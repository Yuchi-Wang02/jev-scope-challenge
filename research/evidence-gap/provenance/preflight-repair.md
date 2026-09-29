# Pre-freeze program-semantics repair (no model inference)

The first development preflight found 14 composed-policy partial states where
the direct three-valued checker returned INSUFFICIENT but exhaustive legal worlds
all yielded DENY: selected-site permission after exception was known blocked,
while reviewer A was absent. Denial does not require proving reviewer approval.

The possible-world labels were unaffected. The independent direct checker lacked
this short-circuit; it was repaired, and the composed policy wording now explicitly
states the denial condition. Full exhaustive checking now precedes writing the
candidate corpus. The initial generated text is archived as preflight-v0.jsonl.

No model was loaded/scored, no human annotations existed, and no corpus/protocol
had been publicly frozen at this point. This is a program-truth/rendering repair,
not post-model relabeling or a model result.
