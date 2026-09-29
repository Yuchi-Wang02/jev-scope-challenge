# Every fixed fact/execution and direct control result

Exploratory original development only: 72 texts in 12 parent groups, not 72 independent trials.
Scaffolded direct and extraction receive the same explicit field definitions and policy.
Legacy rows use previous scores without those definitions. No independent labels or rewrite/test results.

|Path|Method|Correct /72|Complete /12|Deletion pair /12|Unsupported /24|False I /48|Wrong supported /48|Actions|Action errors|Calls /72|Input tokens|Corrected vs direct0|Regressed vs direct0|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|N0|direct_0|39|0|3|19|3|11|64|30|72|23523|0|0|
|N0|direct_1|24|0|0|24|1|23|71|47|72|23523|9|24|
|N0|direct_2|35|0|0|24|0|13|72|37|72|23523|5|9|
|N0|direct_two_01|28|0|0|23|6|15|65|38|144|47046|9|20|
|N0|direct_three|35|0|0|23|1|13|70|36|216|70569|8|12|
|N0|facts_0|24|0|0|0|48|0|0|0|168|63467|19|34|
|N0|facts_1|23|0|0|21|7|21|62|42|168|63467|8|24|
|N0|facts_two|23|0|1|3|41|5|10|8|336|126934|18|34|
|N0|legacy_direct_0|34|0|3|18|7|13|59|31|72|13401|7|12|
|N1|direct_0|31|0|0|23|5|13|66|36|72|23523|0|0|
|N1|direct_1|26|0|0|24|5|17|67|41|72|23523|4|9|
|N1|direct_2|35|0|1|21|4|12|65|33|72|23523|5|1|
|N1|direct_two_01|31|0|0|23|5|13|66|36|144|47046|1|1|
|N1|direct_three|31|0|0|23|5|13|66|36|216|70569|1|1|
|N1|facts_0|44|1|1|14|8|6|54|20|168|63467|17|4|
|N1|facts_1|41|0|0|20|5|6|63|26|168|63467|14|4|
|N1|facts_two|43|0|0|17|6|6|59|23|336|126934|14|2|
|N1|legacy_direct_0|33|0|0|24|4|11|68|35|72|13401|3|1|
|K1|direct_0|32|0|0|24|6|10|66|34|72|23595|0|0|
|K1|direct_1|35|0|0|24|2|11|70|35|72|23595|3|0|
|K1|direct_2|32|0|0|21|10|9|59|30|72|23595|3|3|
|K1|direct_two_01|32|0|0|24|5|11|67|35|144|47190|0|0|
|K1|direct_three|33|0|0|23|6|10|65|33|216|70785|1|0|
|K1|facts_0|35|0|0|20|5|12|63|32|168|63635|13|10|
|K1|facts_1|42|0|1|19|4|7|63|26|168|63635|14|4|
|K1|facts_two|40|0|0|20|3|9|65|29|336|127270|15|7|
|K1|legacy_direct_0|35|0|1|23|4|10|67|33|72|13473|3|0|

Known-grammar full solver: 72/72 decisions, zero model calls; exact synthetic grammar only.
Calls and tokens describe each hypothetical deployment method. Shared-grid reuse does not make a deployment call free.
Actual new execution: 1656 scientific forwards, 552 additional pointer parity forwards, six warmups. Legacy rows created no new forwards.
Latency sums are recorded serial forward times, excluding parity/load; they are not a fresh end-to-end deployment benchmark.

## Extraction: correct actions need not mean correct facts

|Path|Method|Correct fields /168|Exact vectors /72|Missing -> value /18|Missing -> conflict /18|Missed conflicts /12|Wrong facts masked|Wrong facts, wrong action|Executor defects|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|N0|facts_0|16|0|0|17|0|24|48|0|
|N0|facts_1|49|4|17|0|12|19|49|0|
|N0|facts_two|25|1|8|9|4|22|49|0|
|N1|facts_0|123|33|14|1|3|11|28|0|
|N1|facts_1|122|30|18|0|9|11|31|0|
|N1|facts_two|123|33|16|0|5|10|29|0|
|K1|facts_0|120|25|16|1|9|10|37|0|
|K1|facts_1|121|31|16|0|9|11|30|0|
|K1|facts_two|122|30|17|0|9|10|32|0|

The extractor chooses four statuses; it does not produce quotes. Every predicted evidence_spans is null.
Construction reference quotes are stored separately and must not be described as model-generated citations.

## Family and view counts

|Path|Method|Family|Correct /24|Full /4|Reorder /4|Flip /4|Decisive missing /4|Nondecisive missing /4|Conflict /4|Calls /24|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|N0|direct_0|joint_approval|17|2|2|4|3|4|2|24|
|N0|direct_0|reversal_exception|10|3|2|3|0|2|0|24|
|N0|direct_0|route_lookup|12|3|1|4|0|4|0|24|
|N0|direct_1|joint_approval|8|2|2|2|0|2|0|24|
|N0|direct_1|reversal_exception|8|2|2|2|0|2|0|24|
|N0|direct_1|route_lookup|8|2|2|2|0|2|0|24|
|N0|direct_2|joint_approval|14|3|3|4|0|4|0|24|
|N0|direct_2|reversal_exception|10|3|2|2|0|3|0|24|
|N0|direct_2|route_lookup|11|3|1|3|0|4|0|24|
|N0|direct_two_01|joint_approval|9|2|2|2|0|2|1|48|
|N0|direct_two_01|reversal_exception|8|2|2|2|0|2|0|48|
|N0|direct_two_01|route_lookup|11|2|2|3|0|4|0|48|
|N0|direct_three|joint_approval|13|2|3|3|0|4|1|72|
|N0|direct_three|reversal_exception|10|3|3|1|0|3|0|72|
|N0|direct_three|route_lookup|12|4|1|3|0|4|0|72|
|N0|facts_0|joint_approval|8|0|0|0|4|0|4|48|
|N0|facts_0|reversal_exception|8|0|0|0|4|0|4|48|
|N0|facts_0|route_lookup|8|0|0|0|4|0|4|72|
|N0|facts_1|joint_approval|8|2|2|2|0|2|0|48|
|N0|facts_1|reversal_exception|8|2|2|2|0|2|0|48|
|N0|facts_1|route_lookup|7|1|1|2|2|0|1|72|
|N0|facts_two|joint_approval|7|0|0|0|2|1|4|96|
|N0|facts_two|reversal_exception|8|0|0|1|4|0|3|96|
|N0|facts_two|route_lookup|8|0|0|0|4|0|4|144|
|N0|legacy_direct_0|joint_approval|16|3|3|1|3|4|2|24|
|N0|legacy_direct_0|reversal_exception|7|2|1|2|0|2|0|24|
|N0|legacy_direct_0|route_lookup|11|3|1|2|0|4|1|24|
|N1|direct_0|joint_approval|12|2|3|2|0|4|1|24|
|N1|direct_0|reversal_exception|7|2|1|2|0|2|0|24|
|N1|direct_0|route_lookup|12|3|2|3|0|4|0|24|
|N1|direct_1|joint_approval|9|2|2|2|0|3|0|24|
|N1|direct_1|reversal_exception|9|2|2|3|0|2|0|24|
|N1|direct_1|route_lookup|8|2|2|2|0|2|0|24|
|N1|direct_2|joint_approval|11|2|2|2|0|4|1|24|
|N1|direct_2|reversal_exception|11|2|2|2|1|3|1|24|
|N1|direct_2|route_lookup|13|3|2|4|0|4|0|24|
|N1|direct_two_01|joint_approval|11|2|2|2|0|4|1|48|
|N1|direct_two_01|reversal_exception|8|2|1|2|0|3|0|48|
|N1|direct_two_01|route_lookup|12|3|2|3|0|4|0|48|
|N1|direct_three|joint_approval|11|2|2|2|0|4|1|72|
|N1|direct_three|reversal_exception|8|2|1|2|0|3|0|72|
|N1|direct_three|route_lookup|12|3|2|3|0|4|0|72|
|N1|facts_0|joint_approval|14|2|2|2|0|4|4|48|
|N1|facts_0|reversal_exception|12|2|3|3|0|3|1|48|
|N1|facts_0|route_lookup|18|4|2|3|1|4|4|72|
|N1|facts_1|joint_approval|15|2|4|2|0|3|4|48|
|N1|facts_1|reversal_exception|11|2|3|3|0|3|0|48|
|N1|facts_1|route_lookup|15|4|3|4|0|4|0|72|
|N1|facts_two|joint_approval|15|2|3|2|0|4|4|96|
|N1|facts_two|reversal_exception|11|2|3|3|0|3|0|96|
|N1|facts_two|route_lookup|17|4|2|4|0|4|3|144|
|N1|legacy_direct_0|joint_approval|11|2|3|2|0|4|0|24|
|N1|legacy_direct_0|reversal_exception|8|2|2|2|0|2|0|24|
|N1|legacy_direct_0|route_lookup|14|4|2|4|0|4|0|24|
|K1|direct_0|joint_approval|11|2|3|2|0|4|0|24|
|K1|direct_0|reversal_exception|10|3|2|2|0|3|0|24|
|K1|direct_0|route_lookup|11|3|2|2|0|4|0|24|
|K1|direct_1|joint_approval|14|4|3|3|0|4|0|24|
|K1|direct_1|reversal_exception|10|3|2|2|0|3|0|24|
|K1|direct_1|route_lookup|11|3|2|2|0|4|0|24|
|K1|direct_2|joint_approval|10|2|2|2|0|3|1|24|
|K1|direct_2|reversal_exception|11|3|2|2|1|2|1|24|
|K1|direct_2|route_lookup|11|3|2|2|0|4|0|24|
|K1|direct_two_01|joint_approval|11|2|3|2|0|4|0|48|
|K1|direct_two_01|reversal_exception|10|3|2|2|0|3|0|48|
|K1|direct_two_01|route_lookup|11|3|2|2|0|4|0|48|
|K1|direct_three|joint_approval|12|2|3|2|0|4|1|72|
|K1|direct_three|reversal_exception|10|3|2|2|0|3|0|72|
|K1|direct_three|route_lookup|11|3|2|2|0|4|0|72|
|K1|facts_0|joint_approval|15|2|4|2|0|4|3|48|
|K1|facts_0|reversal_exception|10|2|3|3|0|2|0|48|
|K1|facts_0|route_lookup|10|1|2|3|1|3|0|72|
|K1|facts_1|joint_approval|17|2|3|3|1|4|4|48|
|K1|facts_1|reversal_exception|10|2|1|3|0|4|0|48|
|K1|facts_1|route_lookup|15|4|3|4|0|4|0|72|
|K1|facts_two|joint_approval|17|2|4|3|0|4|4|96|
|K1|facts_two|reversal_exception|10|2|3|3|0|2|0|96|
|K1|facts_two|route_lookup|13|3|3|3|0|4|0|144|
|K1|legacy_direct_0|joint_approval|11|2|3|2|0|4|0|24|
|K1|legacy_direct_0|reversal_exception|11|3|2|2|1|3|0|24|
|K1|legacy_direct_0|route_lookup|13|4|2|3|0|4|0|24|

Full four-state confusion matrices and field/family/view extraction counts are in summary.json.
All per-input regressions, fact vectors and attributions are in decisions.jsonl. All status probabilities are in fact_claims.jsonl.
