"""Reproduce the pinned from_pretrained generation-config path without weights."""
from pathlib import Path


def loaded_configurations(model_dir):
    import sys
    from transformers import AutoConfig, GenerationConfig, LogitsProcessorList
    from transformers.generation.utils import GenerationMixin
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'generation-calibration'))
    from settings import make_config, assert_order
    from interface import GeneratedPresencePenalty

    # The pinned 11-file snapshot has no generation_config.json. An unpinned
    # addition would change from_pretrained's path and must not be ignored.
    if (Path(model_dir) / 'generation_config.json').exists():
        raise ValueError('Unexpected unpinned generation_config.json')

    class NoWeights(GenerationMixin):
        @classmethod
        def can_generate(cls):
            return True

    stub = NoWeights()
    stub.config = AutoConfig.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    stub.generation_config = GenerationConfig.from_model_config(stub.config)
    # This is the same library method invoked after model weight loading, not
    # a normalization of null/false flags in previously saved evidence.
    stub.adjust_generation_fn(None, False, None, model_dir, cache_dir=None,
        force_download=False, proxies=None, local_files_only=True, token=None,
        revision='main', subfolder='', trust_remote_code=False)
    configurations = []
    for thinking in (False, True):
        effective, unused = stub._prepare_generation_config(make_config(thinking, 248046, 248044))
        if unused:
            raise ValueError('Unused pinned generation parameters')
        recorded = effective.to_dict()
        stub._prepare_special_tokens(effective, kwargs_has_attention_mask=True, device='cpu')
        processors = stub._get_logits_processor(effective, input_ids_seq_length=2,
            logits_processor=LogitsProcessorList([GeneratedPresencePenalty(2, 1.5)]), device='cpu')
        configurations.append({'thinking': thinking, 'effective_generation_config': recorded,
                               'processor_order': assert_order(processors, thinking)})
    return configurations
