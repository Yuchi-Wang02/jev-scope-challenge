"""Offline, single-pass development calibration with strict budget accounting."""
import argparse
import hashlib
import json
import os
import subprocess
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from interface import GeneratedPresencePenalty, parse_final
from prepare import ROOT, material
from settings import make_config, assert_order, cpu_checks


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8*1024**2), b''): h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--model-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    # Require a clean, committed code/data snapshot before allocating an output.
    assert not subprocess.check_output(['git','status','--porcelain'], cwd=ROOT).strip()
    a.output.mkdir(parents=True, exist_ok=False)
    files = ['run.py','interface.py','prepare.py','settings.py','PROTOCOL.md','plan.json']
    report = {'status': 'preflight', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'source_hashes': {n: file_hash(ROOT/n) for n in files},
              'purpose': 'development interface calibration, not research evaluation',
              'model': 'Qwen/Qwen3.5-4B', 'revision': '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a',
              'calls_started': 0, 'records': [], 'model_downloads': 0, 'paid_api_calls': 0}
    save = lambda: write(a.output/'run.json', report)
    save()
    try:
        plan = json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
        assert plan == material()
        manifest = json.loads((ROOT.parent/'baseline-readiness/qwen35-smoke-repaired/run.json').read_text(encoding='utf-8'))
        report['verified_model_files'] = manifest['model_files']
        for f in report['verified_model_files']:
            assert (a.model_dir/f['name']).stat().st_size == f['bytes']
            assert file_hash(a.model_dir/f['name']) == f['sha256'], f['name']
        for k in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','HF_HUB_DISABLE_PROGRESS_BARS'):
            os.environ[k] = '1'
        import torch
        import transformers
        import peft
        from transformers import (AutoTokenizer, Qwen3_5ForConditionalGeneration,
            StoppingCriteria, StoppingCriteriaList, LogitsProcessorList, set_seed)
        assert transformers.__version__ == '5.3.0' and torch.__version__ == '2.8.0+cu128'
        report['runtime'] = {'transformers': transformers.__version__, 'torch': torch.__version__,
                             'peft': peft.__version__, 'gpu': torch.cuda.get_device_name(0)}
        report['cpu_checks'] = cpu_checks(a.model_dir)
        tokenizer = AutoTokenizer.from_pretrained(a.model_dir, local_files_only=True, trust_remote_code=False)
        rendered = {}
        for c in plan['cases']:
            for thinking in [False, True]:
                text = tokenizer.apply_chat_template([{'role':'user','content':c['prompt']}],
                    tokenize=False, add_generation_prompt=True, enable_thinking=thinking)
                ids = tokenizer(text, add_special_tokens=False)['input_ids']
                rendered[(c['id'],thinking)] = (text,ids)
        report['planned_input_tokens'] = sum(len(rendered[(x['case_id'],x['thinking'])][1]) for x in plan['calls'])
        assert report['planned_input_tokens'] <= plan['max_total_input_tokens']
        report['max_input_tokens_per_call'] = max(len(ids) for _,ids in rendered.values())
        report['status'] = 'loading'; save()
        torch.cuda.reset_peak_memory_stats(); start=time.perf_counter()
        model = Qwen3_5ForConditionalGeneration.from_pretrained(a.model_dir, dtype=torch.bfloat16,
            device_map={'':'cuda:0'}, attn_implementation='sdpa', local_files_only=True, trust_remote_code=False)
        model.eval(); torch.cuda.synchronize()
        report['load_seconds'] = time.perf_counter()-start
        assert {str(p.device) for p in model.parameters()} == {'cuda:0'}
        assert {str(p.dtype) for p in model.parameters()} == {'torch.bfloat16'}
        original = model._get_logits_processor
        record = None

        def audited_processors(*args, **kwargs):
            result = original(*args, **kwargs)
            record['actual_processor_order'] = assert_order(result, record['thinking'])
            save()
            return result

        model._get_logits_processor = audited_processors
        generation_start = None

        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return time.perf_counter()-generation_start >= plan['inference_deadline_seconds']

        cases = {c['id']:c for c in plan['cases']}
        report['status'] = 'generating'; save()
        for call in plan['calls']:
            if generation_start is not None and time.perf_counter()-generation_start >= plan['inference_deadline_seconds']:
                report['status'] = 'deadline'; save(); return
            text, ids = rendered[(call['case_id'],call['thinking'])]
            inputs = {'input_ids': torch.tensor([ids], device='cuda:0'),
                      'attention_mask': torch.ones((1,len(ids)), dtype=torch.long, device='cuda:0')}
            config = make_config(call['thinking'], tokenizer.eos_token_id, tokenizer.pad_token_id)
            effective, unused = model._prepare_generation_config(config)
            assert not unused and effective.do_sample is True and effective.max_new_tokens == call['max_new_tokens']
            record = {**call, 'status':'started', 'rendered_input':text, 'input_ids':ids,
                      'effective_generation_config':effective.to_dict(), 'presence_penalty':1.5}
            report['records'].append(record); report['calls_started'] += 1
            assert report['calls_started'] <= 48
            save(); set_seed(call['seed']); torch.cuda.synchronize(); start=time.perf_counter()
            if generation_start is None: generation_start=start
            with torch.inference_mode():
                out = model.generate(**inputs, generation_config=config,
                    logits_processor=LogitsProcessorList([GeneratedPresencePenalty(len(ids),1.5)]),
                    stopping_criteria=StoppingCriteriaList([Deadline()]))
            torch.cuda.synchronize(); elapsed=time.perf_counter()-start
            generated=out[0,len(ids):].tolist(); decoded=tokenizer.decode(generated,skip_special_tokens=False)
            ended=bool(generated and generated[-1] == tokenizer.eos_token_id)
            parsed=parse_final(decoded,call['thinking'],ended)
            record.update({'status':'completed','output_ids':generated,'decoded_output':decoded,
                'generated_tokens':len(generated),'generation_seconds':elapsed,'ended_with_eos':ended,
                'hit_token_cap':len(generated)==call['max_new_tokens'] and not ended,
                'deadline_reached':time.perf_counter()-generation_start >= plan['inference_deadline_seconds'],
                'parsed':parsed,'content_match':parsed['answer']==cases[call['case_id']]['reference']})
            report['generated_tokens']=sum(r.get('generated_tokens',0) for r in report['records'])
            assert report['generated_tokens'] <= plan['max_generated_tokens']
            report['generation_wall_seconds']=time.perf_counter()-generation_start
            report['peak_allocated_bytes']=torch.cuda.max_memory_allocated()
            report['peak_reserved_bytes']=torch.cuda.max_memory_reserved()
            save(); print(json.dumps({k:record[k] for k in ['id','generated_tokens','generation_seconds','ended_with_eos','parsed']}),flush=True)
        report['status']='completed'; report['finished_at_utc']=datetime.now(timezone.utc).isoformat(); save()
    except BaseException as exc:
        report['status']='failed'; report['error_type']=type(exc).__name__;report['error']=str(exc);save()
        (a.output/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise


if __name__ == '__main__': main()
