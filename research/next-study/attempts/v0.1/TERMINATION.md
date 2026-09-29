# Stopped v0.1 attempt

N0 and N1 each produced 288 real scientific forward records. K1 produced zero
scientific records: its pre-scoring engineering parity check failed, with a
0.0091283 probability delta under default SDPA. Process exited with ValueError.
The original runtime.json and all outputs are preserved, including its incomplete
status. They must not be mixed into v0.2 or presented as a completed three-arm run.

A separate engineering diagnosis found math-only SDPA yields identical packed
and standard probabilities on that one input (delta 0), without changing the
1e-4 acceptance gate. All 504 public adapter tensors (33,030,144 parameters)
exactly matched the tensors loaded by the installed PEFT library. Ignored future
config fields were null/default; historical library output parity is not claimed.

The scientific data, labels, prompts, mappings and split remain fixed. v0.2 uses
math-only SDPA for all arms and reruns all arms. Diagnosis is limited to one
engineering input; it does not establish parity on every possible request.
