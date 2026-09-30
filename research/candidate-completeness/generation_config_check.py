"""CPU-only reproduction of the recorded Transformers default-merge defect."""
from types import SimpleNamespace
from transformers import GenerationConfig
from transformers.generation.utils import GenerationMixin
from study import ROOT, read
import local_run as L

if __name__=='__main__':
    f=read(ROOT/'reasoning_freeze.json')
    base=GenerationConfig.from_pretrained(str(L.DEFAULT),local_files_only=True)
    stub=SimpleNamespace(generation_config=base)
    cfg=GenerationConfig(do_sample=False,max_new_tokens=512,
        eos_token_id=[f['closing_token_id'],f['model_eos_token_id']],pad_token_id=f['pad_token_id'],use_cache=True)
    old,_=GenerationMixin._prepare_generation_config(stub,cfg)
    new,_=GenerationMixin._prepare_generation_config(stub,cfg,use_model_defaults=False,do_sample=False)
    assert old.do_sample and not new.do_sample
    assert old.get_generation_mode().value=='sample'
    assert new.get_generation_mode().value=='greedy_search'
    audit=read(ROOT/'generation_config_audit.json')
    assert old.to_dict()==audit['original_effective_config']
    assert new.to_dict()==audit['repaired_effective_config']
    print('Recorded sampling override and repaired greedy configuration reproduced, with zero model forwards.')
