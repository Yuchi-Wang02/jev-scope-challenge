"""Audit greedy generation's effective settings without model weights."""
from pathlib import Path


def make_config():
    from transformers import GenerationConfig
    return GenerationConfig(do_sample=False,num_beams=1,num_return_sequences=1,
        max_new_tokens=32,use_cache=True,repetition_penalty=1.0,
        eos_token_id=248046,pad_token_id=248044)


def audit_config(model_dir):
    from transformers import AutoConfig,GenerationConfig,LogitsProcessorList
    from transformers.generation.utils import GenerationMixin
    if (Path(model_dir)/'generation_config.json').exists():raise ValueError('Unpinned generation config')
    class NoWeights(GenerationMixin):
        @classmethod
        def can_generate(cls):return True
    stub=NoWeights()
    stub.config=AutoConfig.from_pretrained(model_dir,local_files_only=True,trust_remote_code=False)
    stub.generation_config=GenerationConfig.from_model_config(stub.config)
    stub.adjust_generation_fn(None,False,None,model_dir,cache_dir=None,force_download=False,
        proxies=None,local_files_only=True,token=None,revision='main',subfolder='',trust_remote_code=False)
    effective,unused=stub._prepare_generation_config(make_config(),return_dict_in_generate=True,output_logits=True)
    # return_dict/output_logits are GenerationConfig fields, not model inputs.
    if unused:raise ValueError('Unused generation kwargs')
    record=effective.to_dict()
    stub._prepare_special_tokens(effective,kwargs_has_attention_mask=True,device='cpu')
    processors=stub._get_logits_processor(effective,input_ids_seq_length=2,
        logits_processor=LogitsProcessorList(),device='cpu')
    names=[type(p).__name__ for p in processors]
    if names:raise ValueError('Unexpected greedy logits processors')
    return {'effective_generation_config':record,'processor_order':names,'model_forwards':0}
