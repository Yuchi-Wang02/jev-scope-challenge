"""Pinned sampling settings; imports runtime dependencies only when called."""
from interface import GeneratedPresencePenalty


def make_config(thinking, eos, pad):
    from transformers import GenerationConfig
    return GenerationConfig(do_sample=True, temperature=1.0 if thinking else 0.7,
        top_p=0.95 if thinking else 0.8, top_k=20, min_p=0.0,
        repetition_penalty=1.0, max_new_tokens=2048 if thinking else 256,
        eos_token_id=eos, pad_token_id=pad, num_beams=1,
        num_return_sequences=1, use_cache=True)


def assert_order(processors, thinking):
    names = [type(p).__name__ for p in processors]
    expected = ['GeneratedPresencePenalty']
    if not thinking:
        expected += ['TemperatureLogitsWarper']
    expected += ['TopKLogitsWarper', 'TopPLogitsWarper', 'MinPLogitsWarper']
    assert names == expected, (names, expected)
    return names


def cpu_checks(model_dir):
    import torch
    from transformers import AutoConfig, GenerationConfig, LogitsProcessorList
    from transformers.generation.utils import GenerationMixin
    logits = torch.tensor([[1., -2., 3., 0.], [0., 1., 2., 3.]])
    ids = torch.tensor([[3, 3, 0, 0, 2], [2, 2, 1, 1, 1]])
    penalty = GeneratedPresencePenalty(2, 1.5)
    actual = penalty(ids, logits)
    expected = torch.tensor([[-0.5, -2., 1.5, 0.], [0., -0.5, 2., 3.]])
    assert torch.equal(actual, expected)
    assert torch.equal(penalty(ids[:, :2], logits), logits)
    assert torch.equal(logits, torch.tensor([[1., -2., 3., 0.], [0., 1., 2., 3.]]))

    class NoWeights(GenerationMixin):
        pass
    stub = NoWeights()
    stub.config = AutoConfig.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    stub.generation_config = GenerationConfig.from_model_config(stub.config)
    configs = []
    for thinking in [False, True]:
        effective, unused = stub._prepare_generation_config(make_config(thinking, 248046, 248044))
        assert not unused and effective.do_sample is True
        serializable_config = effective.to_dict()
        stub._prepare_special_tokens(effective, kwargs_has_attention_mask=True, device='cpu')
        procs = stub._get_logits_processor(effective, input_ids_seq_length=2,
            logits_processor=LogitsProcessorList([penalty]), device='cpu')
        configs.append({'thinking': thinking, 'processor_order': assert_order(procs, thinking),
                        'effective_generation_config': serializable_config})
    return {'model_forwards': 0, 'tensor_penalty_checks_passed': True, 'configurations': configs}
