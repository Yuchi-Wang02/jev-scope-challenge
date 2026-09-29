# Upstream source

`model.py` and the empty package initializer are from Jared Palmer's Kev,
commit `29d71c78368657b3a522729a01c748ea15272abc`, the checkpoint's recorded
historical training source. Apache-2.0; see LICENSE. model.py is byte-for-byte
unchanged and its SHA-256 matches the published checkpoint provenance:
`839dd7632ec291ac4740035c86f780f8f13da2b74b54a146ce90ff0ce8de527b`.

This minimal vendoring avoids installing today's incompatible full Kev stack.
The study loader attaches the original historical pointer implementation to the
same adapted backbone used for the native arm. It evaluates an unmerged BF16
path and does not claim to reproduce upstream historical FP32 benchmark scores.
No architecture novelty is claimed. Model and data licenses remain separate.
