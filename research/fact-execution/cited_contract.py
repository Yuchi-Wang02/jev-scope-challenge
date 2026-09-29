"""Known-grammar citation control, not a model or a language-transfer remedy.

This deliberately strong program control reads the entire visible state. It must
be reported as a pure-code reference, never as free validation for a model path.
"""
from interface import compile_visible
from gap_data import parse_text, sentence

KNOWN_HEADERS = {'Evidence:', 'Available records:', 'Decision notes:', 'Supplied facts:',
                 'Record extract:', 'Case file:', 'Policy evidence:', 'Source lines:',
                 'Audit fragment:', 'Statement log:', 'Input report:', 'Fact register:'}


def _evidence_records(state, policy):
    schema = compile_visible(state, policy)
    parsed = parse_text(state, policy, schema['policy_id'], schema['sites'])
    lines = state.splitlines(keepends=True)
    if (len(lines) < 2 or lines[1].rstrip('\r\n') not in KNOWN_HEADERS or
            len(lines[2:]) != len(parsed['records'])):
        raise ValueError('Incomplete known-grammar evidence block')
    entries = []
    offset = sum(len(line) for line in lines[:2])
    for line, record in zip(lines[2:], parsed['records']):
        content = line.rstrip('\r\n')
        expected = sentence(record, parsed)
        prefix = content[:-len(expected)] if content.endswith(expected) else None
        if prefix is None or (prefix not in ('', '- ') and not (
                prefix.startswith('[') and prefix.endswith('] ') and prefix[1:-2].isdigit())):
            raise ValueError('Evidence line does not match parsed record')
        start = offset + len(content) - len(expected)
        entries.append((record, {'start': start, 'end': start + len(expected), 'text': expected}))
        offset += len(line)
    return schema, entries


def verify_claim(state, policy, claim, *, certify_absence_with_parser=False):
    """Check one claim; unsupported wording and uncertified absence stay explicit.

    Claim keys: field, status, spans, inspected_scope='complete_visible_state'.
    This does not execute policy or supply missing model citations on its behalf.
    """
    if not isinstance(claim, dict) or claim.get('inspected_scope') != 'complete_visible_state':
        return {'gate': 'rejected', 'reason': 'inspection_scope_not_declared'}
    if claim.get('status') not in ('TRUE', 'FALSE', 'MISSING', 'CONFLICT'):
        return {'gate': 'rejected', 'reason': 'invalid_status'}
    if not isinstance(claim.get('spans'), list):
        return {'gate': 'rejected', 'reason': 'spans_not_list'}
    try:
        schema, entries = _evidence_records(state, policy)
    except (ValueError, IndexError):
        return {'gate': 'unsupported_grammar', 'reason': 'visible_state_not_parsed'}
    field = claim.get('field')
    if field not in {item['name'] for item in schema['fields']}:
        return {'gate': 'rejected', 'reason': 'unknown_field'}
    spans = claim['spans']
    if any(not isinstance(span, dict) or set(span) != {'start', 'end', 'text'} or
           not isinstance(span['start'], int) or not isinstance(span['end'], int) or
           not isinstance(span['text'], str) or
           state[span['start']:span['end']] != span['text'] for span in spans):
        return {'gate': 'rejected', 'reason': 'span_not_exact'}
    if len({(span['start'], span['end'], span['text']) for span in spans}) != len(spans):
        return {'gate': 'rejected', 'reason': 'duplicate_span'}
    indexed = {(span['start'], span['end'], span['text']): record for record, span in entries}
    cited = []
    for span in spans:
        record = indexed.get((span['start'], span['end'], span['text']))
        if record is None:
            return {'gate': 'rejected', 'reason': 'span_not_evidence_record'}
        if record['scope'] != schema['target'] or record['field'] != field:
            return {'gate': 'rejected', 'reason': 'wrong_target_or_field'}
        cited.append(record['value'])
    observed = {record['value'] for record, _ in entries
                if record['scope'] == schema['target'] and record['field'] == field}
    expected = {'TRUE': {True}, 'FALSE': {False}, 'MISSING': set(),
                'CONFLICT': {True, False}}[claim['status']]
    if observed != expected:
        return {'gate': 'rejected', 'reason': 'status_contradicts_visible_records'}
    if claim['status'] == 'MISSING':
        if spans:
            return {'gate': 'rejected', 'reason': 'missing_has_no_supporting_quote'}
        if not certify_absence_with_parser:
            return {'gate': 'absence_unverified', 'reason': 'empty_citation_does_not_prove_absence'}
        return {'gate': 'accepted', 'reason': 'absence_certified_by_full_known_grammar_parser',
                'provenance': 'pure_code_reference'}
    if set(cited) != expected:
        return {'gate': 'rejected', 'reason': 'citations_do_not_cover_status'}
    return {'gate': 'accepted', 'reason': 'exact_target_field_values_in_known_grammar',
            'provenance': 'pure_code_reference'}
