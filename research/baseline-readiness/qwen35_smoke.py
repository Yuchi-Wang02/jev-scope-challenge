"""One bounded, offline technical smoke. Never reads research cases or API keys."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
PROMPTS = [
    'Reply with exactly the word READY.',
    'Return only a JSON object with key color and value blue.',
    'Choose one letter. Which number is even? A: 3. B: 4. C: 5. Reply with only the letter.',
]
FILES = ['LICENSE', 'README.md', 'config.json', 'tokenizer.json',
         'tokenizer_config.json', 'chat_template.jinja', 'merges.txt', 'vocab.json',
         'model.safetensors.index.json',
         'model.safetensors-00001-of-00002.safetensors',
         'model.safetensors-00002-of-00002.safetensors']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model-dir', type=Path, required=True)
    p.add_argument('--hub-metadata', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)  # no replacement or implicit rerun
    report = {'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'purpose': 'technical smoke only; no research scores',
              'model': 'Qwen/Qwen3.5-4B', 'revision': REVISION,
              'freeze_commit': subprocess.check_output(
                  ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'runner_sha256': sha(__file__),
              'protocol_sha256': sha(ROOT/'QWEN35_SMOKE_PROTOCOL.md'),
              'generation_attempts': 0, 'records': [], 'status': 'preflight'}
    save = lambda: write(a.output/'run.json', report)
    save()
    try:
        hub = json.loads(a.hub_metadata.read_text(encoding='utf-8'))
        assert hub['sha'] == REVISION and hub['id'] == report['model']
        upstream = {r['rfilename']: r for r in hub['siblings']}
        manifest = []
        for name in FILES:
            path = a.model_dir/name
            row = {'name': name, 'bytes': path.stat().st_size, 'sha256': sha(path)}
            source = upstream[name]
            assert row['bytes'] == source['size'], name
            if source.get('lfs'):
                row['upstream_lfs_sha256'] = source['lfs']['sha256']
                assert row['sha256'] == row['upstream_lfs_sha256'], name
            manifest.append(row)
        report['model_files'] = manifest
        report['model_file_bytes'] = sum(r['bytes'] for r in manifest)
        assert report['model_file_bytes'] < 15 * 1024**3
        save()

        # All model/tokenizer loading is local. No hidden backend/kernel downloads.
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
        import torch
        import transformers
        import tokenizers
        import huggingface_hub
        from transformers import (AutoTokenizer, GenerationConfig,
                                  Qwen3_5ForConditionalGeneration,
                                  StoppingCriteria, StoppingCriteriaList, set_seed)
        from transformers.models.qwen3_5 import modeling_qwen3_5
        report['runtime'] = {'python': platform.python_version(),
                             'torch': torch.__version__,
                             'transformers': transformers.__version__,
                             'tokenizers': tokenizers.__version__,
                             'huggingface_hub': huggingface_hub.__version__,
                             'cuda': torch.version.cuda,
                             'gpu': torch.cuda.get_device_name(0),
                             'fast_delta_kernels': modeling_qwen3_5.is_fast_path_available}
        assert transformers.__version__ == '5.3.0'
        assert torch.__version__ == '2.8.0+cu128'
        tokenizer = AutoTokenizer.from_pretrained(a.model_dir, local_files_only=True,
                                                 trust_remote_code=False)
        torch.cuda.reset_peak_memory_stats()
        report['status'] = 'loading'
        save()
        start = time.perf_counter()
        model = Qwen3_5ForConditionalGeneration.from_pretrained(
            a.model_dir, dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            attn_implementation='sdpa', local_files_only=True, trust_remote_code=False)
        model.eval()
        torch.cuda.synchronize()
        report['load_seconds'] = time.perf_counter()-start
        report['parameter_devices'] = sorted({str(x.device) for x in model.parameters()})
        report['parameter_dtypes'] = sorted({str(x.dtype) for x in model.parameters()})
        assert report['parameter_devices'] == ['cuda:0']
        report['status'] = 'generating'
        save()
        inference_start = None

        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return time.perf_counter()-inference_start >= 600

        for thinking in (False, True):
            for index, prompt in enumerate(PROMPTS):
                if inference_start is not None and time.perf_counter()-inference_start >= 600:
                    report['status'] = 'deadline'
                    save()
                    return
                messages = [{'role': 'user', 'content': prompt}]
                rendered = tokenizer.apply_chat_template(messages, tokenize=False,
                           add_generation_prompt=True, enable_thinking=thinking)
                inputs = tokenizer(rendered, return_tensors='pt', add_special_tokens=False).to('cuda:0')
                config = GenerationConfig(
                    do_sample=True, temperature=1.0 if thinking else 0.7,
                    top_p=0.95 if thinking else 0.8, top_k=20, min_p=0.0,
                    repetition_penalty=1.0, max_new_tokens=256,
                    eos_token_id=tokenizer.eos_token_id,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    use_cache=True, num_beams=1, num_return_sequences=1)
                effective, unused = model._prepare_generation_config(config)
                assert not unused, unused
                assert effective.do_sample is True and effective.max_new_tokens == 256
                assert effective.temperature == config.temperature and effective.top_p == config.top_p
                record = {'id': f'{"thinking" if thinking else "direct"}_{index+1}',
                          'thinking': thinking, 'messages': messages, 'rendered_input': rendered,
                          'input_ids': inputs['input_ids'][0].tolist(), 'seed': 20260930,
                          'effective_generation_config': effective.to_dict(),
                          'presence_penalty': 0.0, 'status': 'started'}
                report['records'].append(record)
                report['generation_attempts'] += 1
                assert report['generation_attempts'] <= 6
                save()
                set_seed(20260930)
                torch.cuda.synchronize()
                start = time.perf_counter()
                if inference_start is None:
                    inference_start = start
                with torch.inference_mode():
                    output = model.generate(**inputs, generation_config=config,
                             stopping_criteria=StoppingCriteriaList([Deadline()]))
                torch.cuda.synchronize()
                elapsed = time.perf_counter()-start
                ids = output[0, inputs['input_ids'].shape[1]:].tolist()
                eos = bool(ids and ids[-1] == tokenizer.eos_token_id)
                record.update({'status': 'completed', 'output_ids': ids,
                               'decoded_output': tokenizer.decode(ids, skip_special_tokens=False),
                               'generated_tokens': len(ids), 'generation_seconds': elapsed,
                               'ended_with_eos': eos,
                               'hit_token_cap': len(ids) == 256 and not eos,
                               'deadline_reached': time.perf_counter()-inference_start >= 600})
                report['generated_tokens'] = sum(r.get('generated_tokens', 0) for r in report['records'])
                assert report['generated_tokens'] <= 1536
                report['inference_wall_seconds'] = time.perf_counter()-inference_start
                report['peak_allocated_bytes'] = torch.cuda.max_memory_allocated()
                report['peak_reserved_bytes'] = torch.cuda.max_memory_reserved()
                save()
                print(json.dumps({k: record[k] for k in ['id', 'generated_tokens', 'generation_seconds', 'ended_with_eos']}), flush=True)
        report['status'] = 'completed'
        report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        save()
    except BaseException as exc:
        report['status'] = 'failed'
        report['error_type'] = type(exc).__name__
        report['error'] = str(exc)
        save()
        (a.output/'traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
