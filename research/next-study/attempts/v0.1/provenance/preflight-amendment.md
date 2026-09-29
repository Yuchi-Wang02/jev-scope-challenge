# Pre-inference amendment

The initial local preflight manifest is retained here. Before any new-study model
forward pass, the analyzer was tightened to reject incomplete probability vectors
and make `--verify` read-only. The final manifest freezes that version. Data,
gold labels, arm identities, prompts, splits, temperature grid and readout did
not change. This is a local freeze, not an external preregistration.
