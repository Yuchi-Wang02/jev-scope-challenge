"""Proposed future four-action interface. No model calls or historical rescoring.

Input must be the backend-extracted FINAL channel, not a reasoning transcript.
Callers derive completion from the backend's termination metadata/token trace.
"""
import json
import re
from dataclasses import dataclass

ACTIONS = ('Yes', 'No', 'Irrelevant', 'ASK')
CONTRACT = 'sharc-action-json-v1'


@dataclass(frozen=True)
class ActionResult:
    accepted: bool
    action: str | None
    wrapper: str | None
    strict_json: bool
    error: str | None


def reject(error, wrapper=None):
    return ActionResult(False, None, wrapper, False, error)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite_json_constant')


def parse_final(final_text, *, completion):
    """Accept complete exact JSON or one json fence; never extract a substring.

    completion is normalized by a backend adapter to 'natural_eos', 'length',
    'error', or 'unknown'. Only natural_eos is eligible. Unknown/raw provider
    finish reasons cannot silently pass. This function does not authenticate
    completion or infer it from a closing brace; adapters must retain evidence.
    """
    if completion != 'natural_eos':
        return reject('incomplete_or_unverified_termination')
    if not isinstance(final_text, str):
        return reject('final_not_text')
    text = final_text.strip()
    wrapper = 'bare_json'
    if text.startswith('```'):
        match = re.fullmatch(r'```json[ \t]*\r?\n(.*?)\r?\n```', text, re.S)
        if not match:
            return reject('invalid_fence', 'fenced_json')
        text, wrapper = match[1].strip(), 'fenced_json'
    try:
        value = json.loads(text, object_pairs_hook=unique_object,
                           parse_constant=reject_constant)
    except (ValueError, RecursionError):
        return reject('invalid_json', wrapper)
    if not isinstance(value, dict) or set(value) != {'action'}:
        return reject('wrong_object_schema', wrapper)
    action = value['action']
    if not isinstance(action, str) or action not in ACTIONS:
        return reject('invalid_action', wrapper)
    return ActionResult(True, action, wrapper, wrapper == 'bare_json', None)


def validate_option_order(options):
    """Require one occurrence of each semantic action, in the declared order."""
    if not isinstance(options, (list, tuple)) or len(options) != len(ACTIONS):
        raise ValueError('Four declared options required')
    if any(not isinstance(x, str) for x in options) or set(options) != set(ACTIONS):
        raise ValueError('Options must be a permutation of the semantic actions')
    return tuple(options)
