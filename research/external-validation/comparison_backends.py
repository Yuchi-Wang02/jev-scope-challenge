"""Live backend factories for the separately frozen comparison runner.

Importing this module loads neither credentials nor weights and makes no request.
"""
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from comparison_plan import ROOT, QWEN_REVISION
from adapters import jev_response, qwen_final


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def decode_api_body(text):
    def reject_constant(value):
        raise ValueError('Nonfinite JSON')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Repeated JSON key')
            result[key] = value
        return result
    try:
        return json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique)
    except ValueError:
        return {'invalid_json_body': text}


def adapt_jev(raw, status_code, options, latency):
    detail = {'http_status': status_code, 'raw_response': raw}
    usage = raw.get('usage', {}) if isinstance(raw, dict) else {}
    if not isinstance(usage, dict):
        usage = {}
    result = {'status': 'protocol_error', 'action': None,
              'input_tokens': None, 'output_tokens': None,
              'latency_seconds': latency, 'detail': detail}
    for key in ('input_tokens', 'output_tokens'):
        if type(usage.get(key)) == int and usage[key] >= 0:
            result[key] = usage[key]
    if status_code != 200:
        detail['error'] = 'http_failure'
        return result
    try:
        parsed = jev_response(raw, options)
    except (ValueError, TypeError, KeyError) as error:
        detail['error'] = 'schema_' + type(error).__name__
        return result
    detail['parsed'] = parsed
    result.update(status='ok', action=parsed['action'])
    return result


@contextmanager
def jev_backend():
    import httpx
    sys.path.insert(0, str(ROOT / 'research/payment-ownership'))
    from run_api_v02 import load_key, sanitize
    key = load_key()
    with httpx.Client(timeout=60, follow_redirects=False,
                      transport=httpx.HTTPTransport(retries=0)) as client:
        def call(job, remaining_seconds):
            start = time.monotonic()
            response = client.post('https://api.typesafe.ai/v1/systemone',
                                   json=job['request'], headers={'Authorization': 'Bearer ' + key})
            raw = sanitize(decode_api_body(response.text), key)
            return adapt_jev(raw, response.status_code, job['options'], time.monotonic() - start)
        yield call, {'python': sys.version, 'httpx': httpx.__version__,
                     'transport_retries': 0, 'redirects': False, 'timeout_seconds': 60}


@contextmanager
def qwen_backend(model_dir, jobs):
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY',
                'HF_HUB_DISABLE_PROGRESS_BARS'):
        os.environ[key] = '1'
    import torch
    import transformers
    import peft
    from transformers import (AutoTokenizer, Qwen3_5ForConditionalGeneration,
        StoppingCriteria, StoppingCriteriaList, LogitsProcessorList, set_seed)
    if (transformers.__version__ != '5.3.0' or torch.__version__ != '2.8.0+cu128' or
            peft.__version__ != '0.18.1'):
        raise ValueError('Pinned runtime version mismatch')
    sys.path.insert(0, str(ROOT / 'research/generation-calibration'))
    from settings import make_config, assert_order, cpu_checks
    from qwen_configuration import loaded_configurations
    from interface import GeneratedPresencePenalty
    files = json.loads((ROOT / 'research/baseline-readiness/qwen35-smoke-repaired/run.json').read_text())['model_files']
    setup_start = time.monotonic()
    for record in files:
        path = Path(model_dir) / record['name']
        if path.stat().st_size != record['bytes'] or file_hash(path) != record['sha256']:
            raise ValueError('Pinned model file mismatch')
    config_checks = cpu_checks(model_dir)
    loaded_configs = {row['thinking']: row for row in loaded_configurations(model_dir)}
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    for job in jobs:
        rendered = tokenizer.apply_chat_template([{'role': 'user', 'content': job['prompt']}],
                    tokenize=False, add_generation_prompt=True, enable_thinking=job['thinking'])
        ids = tokenizer(rendered, add_special_tokens=False)['input_ids']
        if rendered != job['rendered_input'] or ids != job['input_ids']:
            raise ValueError('Saved prompt/tokenization drift')
        qwen_final(tokenizer, [], thinking=job['thinking'], rendered_prompt=rendered,
                   max_new_tokens=job['max_new_tokens'])
    verification_seconds = time.monotonic() - setup_start
    load_start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    model = Qwen3_5ForConditionalGeneration.from_pretrained(model_dir, dtype=torch.bfloat16,
        device_map={'': 'cuda:0'}, attn_implementation='sdpa', local_files_only=True, trust_remote_code=False)
    model.eval(); torch.cuda.synchronize()
    if ({str(p.device) for p in model.parameters()} != {'cuda:0'} or
            {str(p.dtype) for p in model.parameters()} != {'torch.bfloat16'}):
        raise ValueError('Model placement or precision mismatch')
    metadata = {'python': sys.version, 'transformers': transformers.__version__,
                'torch': torch.__version__, 'peft': peft.__version__,
                'gpu': torch.cuda.get_device_name(0), 'model': 'Qwen/Qwen3.5-4B',
                'revision': QWEN_REVISION, 'files': files, 'cpu_checks': config_checks,
                'loaded_configuration_checks': list(loaded_configs.values()),
                'verification_seconds': verification_seconds,
                'load_seconds': time.monotonic() - load_start, 'warmup_forwards': 0}
    trace = {}
    original = model._get_logits_processor
    def audited(*args, **kwargs):
        processors = original(*args, **kwargs)
        trace['processor_order'] = assert_order(processors, trace['thinking'])
        return processors
    model._get_logits_processor = audited
    def call(job, remaining_seconds):
        start = time.monotonic()
        trace.clear(); trace['thinking'] = job['thinking']
        ids = job['input_ids']
        config = make_config(job['thinking'], tokenizer.eos_token_id, tokenizer.pad_token_id)
        config.max_new_tokens = job['max_new_tokens']
        effective, unused = model._prepare_generation_config(config)
        if unused:
            raise ValueError('Unused generation parameters')
        effective_record = effective.to_dict()
        expected_config = dict(loaded_configs[job['thinking']]['effective_generation_config'])
        expected_config['max_new_tokens'] = job['max_new_tokens']
        if effective_record != expected_config:
            raise ValueError('Actual loaded generation configuration differs from its no-weight audit')
        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return time.monotonic() - start >= remaining_seconds
        set_seed(job['seed'])
        inputs = {'input_ids': torch.tensor([ids], device='cuda:0'),
                  'attention_mask': torch.ones((1, len(ids)), device='cuda:0', dtype=torch.long)}
        torch.cuda.synchronize()
        with torch.inference_mode():
            out = model.generate(**inputs, generation_config=config,
                logits_processor=LogitsProcessorList([GeneratedPresencePenalty(len(ids), 1.5)]),
                stopping_criteria=StoppingCriteriaList([Deadline()]))
        torch.cuda.synchronize()
        output_ids = out[0, len(ids):].tolist()
        detail = {'output_ids': output_ids, 'effective_generation_config': effective_record,
                  'processor_order': trace['processor_order'], 'presence_penalty': 1.5,
                  'stage_peak_allocated_bytes': torch.cuda.max_memory_allocated(),
                  'stage_peak_reserved_bytes': torch.cuda.max_memory_reserved()}
        try:
            adapted = qwen_final(tokenizer, output_ids, thinking=job['thinking'],
                                rendered_prompt=job['rendered_input'], max_new_tokens=job['max_new_tokens'])
            detail['adapted'] = adapted
            status, action = 'ok', adapted['parsed']['action']
        except (ValueError, TypeError, KeyError) as error:
            detail['adapter_error'] = type(error).__name__
            status, action = 'protocol_error', None
        return {'status': status, 'action': action,
                'input_tokens': len(ids), 'output_tokens': len(output_ids),
                'latency_seconds': time.monotonic() - start,
                'detail': detail}
    try:
        yield call, metadata
    finally:
        model._get_logits_processor = original
        del model
        torch.cuda.empty_cache()
