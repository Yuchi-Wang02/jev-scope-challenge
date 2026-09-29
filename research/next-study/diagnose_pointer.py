"""Engineering-only kernel diagnosis; never scores the scientific dataset."""
import json
import sys
from pathlib import Path
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from study import HERE,BASE_REV,ADAPTER_REV,write_json
sys.path.insert(0,str(HERE/'vendor'))
from kev.model import DecisionModel,PointerHead,encode

cache=Path('G:/jev-lab/hf-cache')
base=cache/'models--Qwen--Qwen3-4B-Base/snapshots'/BASE_REV
adapter=cache/'models--jaredpalmer--kev-4b/snapshots'/ADAPTER_REV
torch.backends.cuda.matmul.allow_tf32=False
torch.backends.cudnn.allow_tf32=False
tok=AutoTokenizer.from_pretrained(base,local_files_only=True)
lm=AutoModelForCausalLM.from_pretrained(base,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).to('cuda').eval()
lm.model=PeftModel.from_pretrained(lm.model,adapter,is_trainable=False)
meta=torch.load(adapter/'head.pt',map_location='cpu',weights_only=True)
m=DecisionModel.__new__(DecisionModel);torch.nn.Module.__init__(m)
m.lm,m.device,m.pad_id=lm.model,'cuda',tok.pad_token_id
m.head=PointerHead(lm.config.hidden_size,dp=meta.get('head_dim',256)).to('cuda')
m.head.load_state_dict(meta['head']);m.eval()
rec={'state':'Engineering check: account demo has a current enable instruction.',
     'questions':[{'instr':'Does the current instruction enable notifications?','options':['Yes','No'],'label':0}]}
enc=encode(tok,rec,strict=True)
report={'scope':'one engineering input only; no scientific dataset scored','kernels':{}}
for kernel in ('default','math_only'):
    if kernel=='math_only':
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
    with torch.inference_mode():
        packed=m.forward(enc)[0]
        hidden=m.lm(input_ids=torch.tensor([enc['ids']],device='cuda'),position_ids=torch.tensor([enc['pos']],device='cuda')).last_hidden_state[0].float()
        causal=m.head(hidden[enc['decide_idx'][0]],hidden[torch.tensor(enc['opt_idx'][0],device='cuda')])
    report['kernels'][kernel]={'packed_logits':packed.tolist(),'causal_logits':causal.tolist(),
                              'max_probability_delta':(torch.softmax(packed,-1)-torch.softmax(causal,-1)).abs().max().item()}
# Check every adapter tensor was loaded with the expected name and value.
from safetensors.torch import load_file
saved=load_file(adapter/'adapter_model.safetensors')
actual=dict(lm.model.named_parameters())
checked=[]
for name,tensor in saved.items():
    actual_name=name.replace('.lora_A.weight','.lora_A.default.weight').replace('.lora_B.weight','.lora_B.default.weight')
    if actual_name not in actual or not torch.equal(actual[actual_name].detach().cpu().float(),tensor.float()):
        raise ValueError('Loaded adapter tensor mismatch: '+name)
    checked.append(name)
report['adapter_tensor_check']={'status':'passed','tensors':len(checked),'parameters':sum(t.numel() for t in saved.values()),
                                'scope':'expected public LoRA tensors exactly equal loaded tensors; not historical library parity'}
write_json(HERE/'provenance/kernel-diagnosis.json',report)
print(json.dumps(report,indent=2))
