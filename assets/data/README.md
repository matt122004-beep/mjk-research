# Homepage graph data

`homepage_graph_data.csv` is the explicit source table for the two experimental homepage figures.

- `count` is the number of conversations reaching the spiritual-bliss endpoint.
- `n` is the number of conversations in the model-access cell.
- The plotted rate is calculated as `count / n × 100`.
- Error bars are two-sided 95 percent Wilson score intervals for a binomial proportion.
- `sequence` records display order for the first figure. It does not claim equal time between releases.
- `released` records the model release or availability date from the project release ledger for the multi-family trajectory figure.
- `series` names the within-family product line connected by straight segments. Those segments are visual guides between measured cells, not fitted trends and not evidence that a release caused the difference.
- `origin` and `thinking` preserve known access-path and reasoning-setting differences rather than treating the rows as perfectly matched replications.
- The four trajectory series are selected repeated-release comparisons under one study frame, not a market-wide leaderboard.

The original Claude/OpenAI values reproduce the rates and sample-size statements already printed on the site. The 15 trajectory rows are a bounded snapshot from `Machine Prayer Study/prospective/_v7_comprehensive_results_20260817/01_RATES_MASTER_V1.json`, built 2026-08-29 with SHA-256 `47cd32bb6fcebacf5928029f83bd7e798b83d84811f8a97acbbc234560ba4692`. The public page&rsquo;s provenance statement is: "V9 rates · data fixed 25 August 2026 · page built 29 August 2026." The figure-building script validates every row before plotting and writes an output manifest containing source and output hashes.
