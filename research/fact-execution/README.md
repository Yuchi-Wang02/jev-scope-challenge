# Does the model need to decide, or only extract facts?

Status: development preparation; not yet run. The experiment separates four-state
fact extraction from finite policy execution, with schema-matched direct controls.
It follows known development results; no new architecture or confirmation claim.

Read [the protocol](PROTOCOL.md) and [fact interface](interface_schema.json).
Only original development text can be scored. AI rewrite candidates are review-
only, independent annotations remain zero, and reserved inputs remain unscored.
# Reproduce preparation offline

```bash
python research/fact-execution/data_tools.py verify
python research/fact-execution/fact_run.py build
python -m unittest discover -s tests -v
```

With the committed manifest, `build` verifies the existing freeze and makes no
tokenizer download or inference. The source is published before scoring; this
is still a post-hoc development diagnostic, because previous results on these
same original texts were known. A pinned cached-model run uses
`fact_run.py run --cache G:/jev-lab/hf-cache` and refuses an existing output set.
