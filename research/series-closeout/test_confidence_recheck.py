"""Synthetic software boundary tests; never added to the research report rows."""
from decimal import Decimal
import unittest
from unittest.mock import patch

import confidence_recheck as audit


def row(text, correct=True):
    value, status = audit.confidence_value(audit.load_json(text))
    return {'confidence': value, 'confidence_status': status, 'correct': correct}


class DecimalBoundaryTests(unittest.TestCase):
    def test_json_parser_preserves_decimal_digits(self):
        value = audit.load_json('{"confidence": 0.9899999999999999999999999}')['confidence']
        self.assertEqual(value, Decimal('0.9899999999999999999999999'))
        self.assertIsInstance(value, Decimal)

    def test_exact_boundary_accepted_including_wrong_prediction(self):
        rows = [row('0.99'), row('0.99', False)]
        counts = audit.threshold_counts(rows, Decimal('0.99'), 'decimal_exact')
        self.assertEqual(counts['accepted'], {'total': 2, 'correct': 1, 'wrong': 1})
        self.assertEqual(counts['exact_decimal_boundary'], {'total': 2, 'correct': 1, 'wrong': 1, 'accepted': 2, 'rejected': 0})

    def test_immediately_below_is_rejected_without_epsilon(self):
        value = row('0.9899999999999999999999999')['confidence']
        self.assertFalse(audit.accepted(value, Decimal('0.99')))

    def test_immediately_above_is_accepted(self):
        value = row('0.9900000000000000000000001')['confidence']
        self.assertTrue(audit.accepted(value, Decimal('0.99')))

    def test_equality_count_does_not_include_above_threshold(self):
        rows = [row('0.9899999999999999999999999'), row('0.9900', False),
                row('0.9900000000000000000000001'), row('1')]
        counts = audit.threshold_counts(rows, Decimal('0.99'), 'decimal_exact')
        self.assertEqual(counts['accepted']['total'], 3)
        self.assertEqual(counts['exact_decimal_boundary']['total'], 1)
        self.assertEqual(counts['exact_decimal_boundary']['wrong'], 1)

    def test_wrong_binary_fraction_rejects_exact_099_and_095(self):
        for text in ('0.99', '0.95'):
            threshold = Decimal(text)
            self.assertTrue(audit.accepted(threshold, threshold, 'decimal_exact'))
            self.assertFalse(audit.accepted(threshold, threshold, 'legacy_fraction_of_binary_float'))

    def test_missing_and_invalid_confidence_are_distinct_and_rejected(self):
        self.assertEqual(audit.confidence_value(), (None, 'missing'))
        for bad in (None, True, False, '0.99', 0.99, [], {}, Decimal('NaN'),
                    Decimal('Infinity'), Decimal('-0.01'), Decimal('1.01')):
            with self.subTest(value=repr(bad)):
                self.assertEqual(audit.confidence_value(bad), (None, 'invalid'))
                self.assertFalse(audit.accepted(None, Decimal('0.99')))

    def test_zero_and_one_json_integers_are_valid(self):
        self.assertEqual(audit.confidence_value(audit.load_json('0')), (Decimal(0), 'valid'))
        self.assertEqual(audit.confidence_value(audit.load_json('1')), (Decimal(1), 'valid'))

    def test_partition_retains_unscored_rows_and_reconciles_errors(self):
        rows = [row('0.99', False), row('1', True), row('0.98', False),
                {'confidence': None, 'correct': True}, {'confidence': None, 'correct': False}]
        for mode in audit.MODES:
            counts = audit.threshold_counts(rows, Decimal('0.99'), mode)
            self.assertEqual(counts['missing_or_invalid_confidence_rejected'], 2)
            self.assertEqual(counts['accepted']['total']+counts['rejected']['total'], 5)
            self.assertEqual(counts['accepted']['wrong']+counts['rejected']['wrong'], 3)
        correct = audit.threshold_counts(rows, Decimal('0.99'), 'decimal_exact')
        self.assertEqual(correct['accepted']['wrong'], 1)
        self.assertEqual(correct['rejected'], {'total': 3, 'correct': 1, 'wrong': 2})

    def test_threshold_and_mode_validation(self):
        with self.assertRaises(ValueError):
            audit.accepted(Decimal('0.99'), 0.99)
        with self.assertRaises(ValueError):
            audit.accepted(Decimal('0.99'), Decimal('NaN'))
        with self.assertRaises(ValueError):
            audit.accepted(Decimal('0.99'), Decimal('0.99'), 'epsilon')


class PriorProvenanceTests(unittest.TestCase):
    def test_verification_without_zip_retains_prior_metadata_without_reopening(self):
        prior = {'sha256': 'synthetic-unit-test-metadata', 'bytes': 10, 'members': []}
        saved = {'provenance': {'external_reference_zip': prior}}
        with patch.object(audit, 'reference_evidence', side_effect=AssertionError('Must not open archive')):
            retained, status = audit.verification_reference(saved)
        self.assertEqual(retained, prior)
        self.assertFalse(status['external_reference_reopened'])
        self.assertIn('not rechecked', status['external_reference_verification'])

    def test_optional_archive_must_match_saved_archive_and_members(self):
        prior = {'sha256': 'synthetic-unit-test-metadata', 'bytes': 10, 'members': [{'sha256': 'member-a'}]}
        saved = {'provenance': {'external_reference_zip': prior}}
        with patch.object(audit, 'reference_evidence', return_value=prior):
            retained, status = audit.verification_reference(saved, 'synthetic-path')
        self.assertEqual(retained, prior)
        self.assertTrue(status['external_reference_reopened'])
        changed = {**prior, 'members': [{'sha256': 'member-b'}]}
        with patch.object(audit, 'reference_evidence', return_value=changed):
            with self.assertRaises(ValueError):
                audit.verification_reference(saved, 'synthetic-path')


if __name__ == '__main__':
    unittest.main()
