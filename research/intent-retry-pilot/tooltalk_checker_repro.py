"""Reproduce one pinned ToolTalk checker defect with controlled similarity.

This isolates a real upstream method via AST; it never imports the upstream
package, initializes an embedding model, calls an API, or sends a message.
Message similarity is an explicit controlled test input, not a model output.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'audit_sources/tooltalk_message.py'
EXPECTED_SHA256 = '8cad12aec95c6befd7aefe0f938918d42a3b2d642eaedd8e142a3993db8118b8'


def extract_checker(source, similarity):
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SendMessage')
    method = copy.deepcopy(next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == 'check_api_call_correctness'))
    method.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    namespace = {'semantic_str_compare': lambda a,b: similarity, '__builtins__': {}}
    exec(compile(module, 'pinned_ToolTalk_SendMessage_checker', 'exec'), namespace)
    return namespace['check_api_call_correctness']


def main():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    text = raw.decode('utf-8')
    old = "if predict_params['receiver'] != predict_params['receiver']:"
    new = "if predict_params['receiver'] != ground_truth_params['receiver']:"
    assert text.count(old) == 1
    patched = text.replace(old,new)
    truth = {'exception':None, 'request':{'parameters':{
        'session_token':'synthetic-session', 'receiver':'alex', 'message':'The report is ready.'}}}
    cases = []
    specs = [
        ('matching_recipient', {}, 1.0, True, True),
        ('wrong_recipient_identical_text', {'receiver':'blair'}, 1.0, True, False),
        ('wrong_session', {'session_token':'different-synthetic-session'}, 1.0, False, False),
        ('dissimilar_message', {'message':'Unrelated text'}, 0.0, False, False),
        ('wrong_recipient_threshold_boundary', {'receiver':'blair'}, 0.8, True, False),
    ]
    for name,changes,similarity,old_expected,new_expected in specs:
        predicted = copy.deepcopy(truth)
        predicted['request']['parameters'].update(changes)
        old_result = extract_checker(text,similarity)(predicted,truth)
        new_result = extract_checker(patched,similarity)(predicted,truth)
        assert old_result is old_expected and new_result is new_expected
        cases.append({'case':name,'controlled_message_similarity':similarity,
                      'original_accepts':old_result,'one_line_fix_accepts':new_result})
    result = {'status':'isolated checker regression reproduced', 'upstream_commit':'e05f4ce6132c80ed33392b81535b077d56ab28fd',
              'source_sha256':EXPECTED_SHA256,'original_method_extracted_without_body_edits':True,
              'controlled_dependency':'semantic_str_compare replaced by explicit scalar test values',
              'full_upstream_runtime_executed':False,'model_calls':0,'real_messages_sent':0,
              'cases':cases,'claim_limit':'Shows receiver validation defect conditional on similarity passing; does not quantify benchmark-score impact.'}
    (ROOT/'results/tooltalk_checker_repro.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':
    main()
