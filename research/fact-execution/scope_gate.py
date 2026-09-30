"""Request-ID equality for the declared single-record sentence grammar.

This is ordinary parsing, not a language resolver. Unsupported text is UNKNOWN;
it must not silently become a certified foreign record or a missing fact.
"""
import re

IDENTIFIER = r'[A-Za-z][A-Za-z0-9_-]*'
HEADER = re.compile(rf'Request: allow action for request ({IDENTIFIER})\.')
OWNER = rf'(?P<owner>{IDENTIFIER})'
RECORDS = (
    re.compile(rf'Reviewer [AB] (?:approves|rejects) request {OWNER}\.'),
    re.compile(rf'Base decision for request {OWNER}: (?:ALLOW|DENY)\.'),
    re.compile(rf'Reversal exception for request {OWNER}: (?:active|inactive)\.'),
    re.compile(rf'Route for request {OWNER}: {IDENTIFIER}\.'),
    re.compile(rf'Permission for site {IDENTIFIER} in request {OWNER}: (?:allowed|blocked)\.'),
)


def gate_line(header, line):
    """Read visible strings only; return identity equality, never field/polarity."""
    target = HEADER.fullmatch(header)
    if target is None:
        return dict(status='UNKNOWN', target_id=None, owner_id=None,
                    reason='unsupported_header')
    matches = [match for pattern in RECORDS if (match := pattern.fullmatch(line))]
    if len(matches) != 1:
        return dict(status='UNKNOWN', target_id=target.group(1), owner_id=None,
                    reason='unsupported_single_record')
    owner = matches[0].group('owner')
    return dict(status='KEEP' if owner == target.group(1) else 'DROP',
                target_id=target.group(1), owner_id=owner,
                reason='exact_visible_identifier_equality')
