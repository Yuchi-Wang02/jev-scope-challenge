"""Synthetic mutation tests of the authored gate, not research/model examples.

These fixtures imitate documented response shapes. They are not captured native
tool outputs, upstream benchmark replays, or additional independent samples.
"""

import copy
import unittest

from gate import evaluate_gate


CONTRACT = {
    "full_name": "Theodore Collins", "date_of_birth": "1985-09-14",
    "passport_number_prefix": "US876543", "passport_country": "US",
    "origin": "JFK", "destination": "LAX", "date": "2026-10-15",
}


def event(name, arguments, response, success=True, error=None):
    return {"call": {"name": name, "arguments": arguments},
            "response": response, "success": success, "error": error}


def fixture(with_profile=False):
    events = [
        event("read_reservations", {"traveler_name": CONTRACT["full_name"],
              "route": "JFK-LAX", "date": CONTRACT["date"]},
              {"reservation_id": "res_100", "user_id": "user_100", "status": "confirmed",
               "traveler_ids": ["trav_100"], "flight_ids": ["flt_100"],
               "flights": [{"flight_id": "flt_100", "origin": "JFK", "destination": "LAX",
                            "date": "2026-10-15"}]}),
        event("verify_travel_and_pricing",
              {"check_type": "verify_traveler_information", "traveler_id": "trav_100"},
              {"check_type": "verify_traveler_information", "verified": True,
               "traveler_id": "trav_100", "full_name": "Theodore Collins",
               "passport_country": "US", "passport_expiry": "2031-09-13", "documents_count": 1}),
    ]
    if with_profile:
        events.append(event("read_user_account", {"user_id": "user_100"},
                            {"user_id": "user_100", "traveler_profiles": [
                                {"traveler_id": "trav_100", "user_id": "user_100",
                                 "full_name": "Theodore Collins", "date_of_birth": "1985-09-14",
                                 "passport_number": "US876543210", "passport_country": "US"}]}))
    return {"system_prompt": "synthetic fixture", "user_request": "synthetic fixture",
            "tools": [], "events": events,
            "pending_action": {"name": "manage_booking", "arguments": {
                "action": "cancel_reservation", "reservation_id": "res_100"}}}


class GateTests(unittest.TestCase):
    def assert_decision(self, visible, decision, reason=None, strict=False):
        result = evaluate_gate(visible, CONTRACT, require_profile=strict)
        self.assertEqual(result["decision"], decision, result)
        if reason is not None:
            self.assertEqual(result["reason"], reason)

    def test_prefixes_have_different_requirements(self):
        v = fixture()
        v["events"] = []
        v["pending_action"] = None
        self.assert_decision(v, "NEED_DISCOVERY")
        v = fixture()
        v["events"] = v["events"][:1]
        self.assert_decision(v, "HOLD", "no_identity_verification_after_discovery")
        self.assert_decision(fixture(), "ALLOW")

    def test_strict_profile_is_additional_not_silent_oracle(self):
        self.assert_decision(fixture(), "HOLD", "profile_evidence_required", strict=True)
        self.assert_decision(fixture(True), "ALLOW", strict=True)

    def test_error_or_missing_result_never_becomes_verified(self):
        for response, success, error in [(None, False, "Internal server error"),
                                          (None, True, None), ({"verified": True}, True, "error")]:
            with self.subTest(response=response, success=success, error=error):
                v = fixture(True)
                v["events"][1].update(response=response, success=success, error=error)
                self.assert_decision(v, "HOLD", "identity_verification_failed_or_unstructured", strict=True)

    def test_verified_requires_boolean_true(self):
        for value in [False, "true", 1, None, {}, []]:
            with self.subTest(value=value):
                v = fixture()
                v["events"][1]["response"]["verified"] = value
                self.assert_decision(v, "HOLD", "identity_not_explicitly_verified")

    def test_pending_wrong_reservation(self):
        v = fixture()
        v["pending_action"]["arguments"]["reservation_id"] = "res_101"
        self.assert_decision(v, "HOLD", "pending_target_differs_from_discovery")

    def test_request_and_response_traveler_ids_both_bound(self):
        for section in ["request", "response"]:
            v = fixture()
            if section == "request":
                v["events"][1]["call"]["arguments"]["traveler_id"] = "trav_101"
            else:
                v["events"][1]["response"]["traveler_id"] = "trav_101"
            self.assert_decision(v, "HOLD", "verification_traveler_binding_mismatch")

    def test_other_verification_type_does_not_authorize_cancel(self):
        v = fixture()
        v["events"][1]["call"]["arguments"]["check_type"] = "verify_baggage_allowance"
        self.assert_decision(v, "HOLD", "no_identity_verification_after_discovery")
        v = fixture()
        v["events"][1]["response"]["check_type"] = "verify_baggage_allowance"
        self.assert_decision(v, "HOLD", "verification_type_mismatch")

    def test_name_and_country_are_checked(self):
        for key, value, reason in [("full_name", "Thea Collins", "verification_name_mismatch"),
                                   ("passport_country", "CA", "verification_passport_country_mismatch")]:
            v = fixture()
            v["events"][1]["response"][key] = value
            self.assert_decision(v, "HOLD", reason)

    def test_flight_binding_route_date(self):
        for key, value, reason in [("flight_id", "flt_101", "flight_detail_binding_mismatch"),
                                   ("destination", "SFO", "flight_route_or_date_mismatch"),
                                   ("date", "2026-10-16", "flight_route_or_date_mismatch")]:
            v = fixture()
            v["events"][0]["response"]["flights"][0][key] = value
            self.assert_decision(v, "HOLD", reason)

    def test_completed_status_and_unknown_status(self):
        v = fixture()
        v["events"][0]["response"]["status"] = "cancelled"
        self.assert_decision(v, "ALREADY_DONE")
        for status in [None, "completed", "unknown"]:
            v["events"][0]["response"]["status"] = status
            self.assert_decision(v, "HOLD", "reservation_status_not_supported_as_cancellable")

    def test_verification_before_discovery_does_not_count(self):
        v = fixture()
        v["events"].reverse()
        self.assert_decision(v, "HOLD", "no_identity_verification_after_discovery")

    def test_unrelated_read_preserves_permission(self):
        v = fixture(True)
        v["events"].append(event("search_flights", {}, {"flights": []}))
        self.assert_decision(v, "ALLOW")
        self.assert_decision(v, "ALLOW", strict=True)

    def test_visible_booking_call_requires_refresh_even_after_error(self):
        for success, error in [(True, None), (False, "unknown result")]:
            v = fixture()
            v["events"].append(event("manage_booking", {"action": "change_reservation",
                "reservation_id": "res_100"}, {}, success, error))
            self.assert_decision(v, "HOLD", "booking_call_requires_refreshed_evidence")

    def test_latest_failed_verification_is_not_cherry_picked_away(self):
        v = fixture(True)
        e = copy.deepcopy(v["events"][1])
        e.update(success=False, error="Internal server error", response=None)
        v["events"].append(e)
        self.assert_decision(v, "HOLD", "identity_verification_failed_or_unstructured", strict=True)

    def test_latest_failed_discovery_is_not_cherry_picked_away(self):
        v = fixture()
        v["events"].append(event("read_reservations", {"reservation_id": "res_100"},
                                  None, False, "not found"))
        self.assert_decision(v, "HOLD", "discovery_failed_or_unstructured")

    def test_strict_profile_checks_each_identity_field(self):
        changes = [("user_id", "user_101", "profile_user_binding_mismatch"),
                   ("full_name", "Thea Collins", "profile_name_mismatch"),
                   ("date_of_birth", "1990-04-02", "profile_birth_date_mismatch"),
                   ("passport_number", "US111122223", "profile_passport_prefix_mismatch"),
                   ("passport_country", "CA", "profile_passport_country_mismatch")]
        for key, value, reason in changes:
            with self.subTest(key=key):
                v = fixture(True)
                v["events"][2]["response"]["traveler_profiles"][0][key] = value
                self.assert_decision(v, "HOLD", reason, strict=True)

    def test_profile_account_and_traveler_bindings(self):
        v = fixture(True)
        v["events"][2]["response"]["user_id"] = "user_101"
        self.assert_decision(v, "HOLD", "profile_account_binding_mismatch", strict=True)
        v = fixture(True)
        profile = v["events"][2]["response"]["traveler_profiles"][0]
        profile["traveler_id"] = "trav_101"
        self.assert_decision(v, "HOLD", "profile_traveler_missing_or_duplicated", strict=True)
        v = fixture(True)
        profiles = v["events"][2]["response"]["traveler_profiles"]
        profiles.append(copy.deepcopy(profiles[0]))
        self.assert_decision(v, "HOLD", "profile_traveler_missing_or_duplicated", strict=True)

    def test_requested_identity_values_are_not_profile_evidence(self):
        v = fixture()
        v["events"][1]["call"]["arguments"]["provided_details"] = str(CONTRACT)
        self.assert_decision(v, "ALLOW", "upstream_verification_passed_identity_fields_unchecked")
        self.assert_decision(v, "HOLD", "profile_evidence_required", strict=True)

    def test_discovery_lookup_id_must_match_returned_record(self):
        v = fixture()
        v["events"][0]["call"]["arguments"] = {"reservation_id": "res_101"}
        self.assert_decision(v, "HOLD", "discovery_request_response_id_mismatch")

    def test_unsupported_scope_does_not_become_permission(self):
        v = fixture()
        v["pending_action"]["arguments"]["action"] = "book_flight"
        self.assert_decision(v, "OUT_OF_SCOPE")
        v = fixture()
        v["events"][0]["response"]["traveler_ids"].append("trav_101")
        self.assert_decision(v, "OUT_OF_SCOPE", "requires_single_traveler_single_flight")

    def test_events_require_strict_success_flag_and_do_not_mutate_input(self):
        v = fixture()
        original = copy.deepcopy(v)
        self.assert_decision(v, "ALLOW")
        self.assertEqual(v, original)
        v["events"][1]["success"] = 1
        self.assert_decision(v, "HOLD", "malformed_visible_events")

    def test_malformed_enum_values_fail_closed_without_exception(self):
        v = fixture()
        v["pending_action"]["arguments"]["action"] = ["cancel_reservation"]
        self.assert_decision(v, "OUT_OF_SCOPE", "unsupported_pending_action")
        v = fixture()
        v["events"][1]["call"]["arguments"]["check_type"] = {"type": "verify_traveler_information"}
        self.assert_decision(v, "HOLD", "no_identity_verification_after_discovery")


if __name__ == "__main__":
    unittest.main()
