# Claims and evidence

|Claim|Evidence|Status/boundary|
|---|---|---|
|864 actual forward records in completed v0.2|results/N0.jsonl, N1.jsonl, K1.jsonl; frozen grid and offline checks|Verified local inference, not mock|
|N1 and N0 use identical inputs and candidate slots|analyze_study.py checks prompt, token IDs, candidate IDs and order|One pinned adapter/native prompt|
|N1 test decision accuracy exceeds N0 and K1 here|results/summary.json and REPORT.md|Exploratory synthetic parents; no broad superiority claim|
|Complete correctness remains poor|0/12, 1/12, 0/12 parents|Each parent requires 12 decisions correct|
|Missing evidence is often mishandled|36/36, 29/36, 35/36 false commitments|Explicit construction policies; human audit missing|
|Uniform math SDPA resolved the engineering discrepancy|provenance/kernel-diagnosis.json; results/pointer_parity.json|One engineering input; not all-input parity|
|No new training or paid API|runner/runtime and dependency path|Local download/inference/engineering costs exist|
|A specialized head causes the whole gap|Not isolated: K1 also changes layout/readout|Unsupported|
|Dedicated decision training is unnecessary|Not tested by an initial-training factorial|Unsupported|
|Human-validated benchmark or new architecture|No supporting evidence|Not claimed|
