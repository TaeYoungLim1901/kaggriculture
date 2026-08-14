# Trace planner

Stage 2 selects a trace action-by-action with offline lookahead. At each
effective environment step, every portfolio member proposes seat 0's action.
Equivalent proposals are canonical-JSON deduplicated. For each distinct action,
the planner deep-copies the current environment, applies that action alongside
the opponent's current action, and advances the copy with a fresh file-loaded
`main.py` continuation for seat 0 and the opponent path for seat 1. The action
whose rollout ends with the most seat-0 money is applied to the real environment.

The default portfolio was:

```text
main.py,.sweep/B7.py,.sweep/M12c.py,.sweep/T10.py,.sweep/W20.py,.sweep/X3c.py
```

`--horizon 720` plans the full 720-entry trace. A shorter horizon is also a
planning-prefix cap for smoke runs; truncated rollouts score current money plus
the current market value of priced goods in the seat's shed. `--jobs` uses a
process pool because candidate rollouts are independent. The final framework
observation is not executed, but its action is appended so the stage-1 format
still contains exactly 720 entries.

## Run measurements

Smoke run: `--horizon 48 --jobs 4`, planning the first 48 steps.

| metric | result |
| --- | ---: |
| proposals | 288 |
| distinct proposals | 135 |
| dedup hit rate | **53.1%** (153/288) |
| zero-rollout steps | 0/48 (0.0%) |
| rollouts | 135 |
| wall time | 34.93 s |
| time per planned step | 0.728 s |
| rough full-run estimate | 31.3 min at 4 jobs |

Full run: seed `90001`, meta opponent, `--horizon 720 --jobs 4`.

| metric | result |
| --- | ---: |
| trace entries | 720 |
| proposals | 4,314 |
| distinct proposals | 2,411 |
| dedup hit rate | **44.1%** (1,903/4,314) |
| zero-rollout steps | 35/719 (4.9%) |
| scored rollouts | 2,376 |
| wall time | **3,511.32 s (58.52 min)** |
| time per planned step | 4.884 s |

The trace was encoded as `build/portfolio.b85` and baked as
`build/trace_portfolio.py` (720 entries, 31,838 bytes). `tools/verify_trace.py`
passed its stage-1 file-path replay check with matching action streams and final
money on seeds 90001, 1000, and 8919. A separate file-path run of the new baked
trace completed 720 frames with both agents `DONE`; AST inspection confirmed
`agent` is the last callable.

## Evaluation

`tools/eval.py --games 8` reports 8 seeds in both seat orders, hence 16 games
per panel. Margins are seat-0 trace money minus opponent money.

| panel | meta `v16_rc5` | mirror `bench/v3.py` |
| --- | --- | --- |
| planning panel, `--seed0 90001` | **0W-16L**, mean **−97,871**, worst −119,711 | 4W-12L, mean −1,757, worst −7,333 |
| held out, `--seed0 1000` | **0W-16L**, mean **−109,089**, worst −134,901 | 2W-14L, mean −2,034, worst −5,774 |
| held out, `--seed0 55555` | **0W-16L**, mean **−101,267**, worst −124,056 | 2W-14L, mean −1,966, worst −4,234 |

## Verdict

This planner run does **not** beat the shipped policy. Against the meta on the
planning panel it is 14,233 money worse than the shipped reference margin of
−83,638, and it loses every meta game on both held-out panels. The one-seed
generalisation test therefore fails plainly; this trace should not be shipped.
