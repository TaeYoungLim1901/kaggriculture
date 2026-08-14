# Chained task bundles

Date: 2026-08-14. This is a constant-gated rank-3 experiment from
`docs/RESEARCH_IDEAS.md`.

## Design

`main.py` adds one module-level switch:

```py
BUNDLE = False
```

The shipped path is unchanged when it is false. `BUNDLE=True` keeps a short
queue in `_BUNDLES`, keyed by unit index. The existing Hungarian solver in
`_assign` still chooses the first task; the queue only changes what that task
expands into.

- Animal work is ordered `FEED -> HARVEST -> CARE -> COLLECT_FERTILIZER` for
  the assigned animal. The existing shed errand supplies `PICKUP WHEAT` before
  feeding when wheat is needed, so pickup is not duplicated by a bundle.
- Crop work is ordered `WATER -> FERTILIZE -> HARVEST` for the assigned crop.
- The final measured variant uses a same-tile local group. A queue is created
  only after the first Hungarian target is reached, avoiding a new travel leg
  while preserving persistence across compatible actions.
- Queue entries are removed when their target/action is complete or the tile
  disappears. Unfed animals and crops with an unsafe watering deadline preempt
  a persistent queue. This is bounded persistence; `STICKY` remains separate
  and is ignored while bundle mode is enabled.

## Required OFF checks

With `BUNDLE=False`:

```text
OK  edit: 60-step self-play clean, $343
PASS determinism
PASS never raises
PASS action schema
BUY_SEED 60
PASS 3518
PLANT 104
PASS no-op rate
PASS economic floor
```

The full no-op table was unchanged across the repeated OFF checks.

## Thrash measurements

Baseline `main.py` at seed 90001:

| turns | retargets before arrival | target runs | mean survival | movement | productive | movement/productive |
|---:|---:|---:|---:|---:|---:|---:|
| 719 | 334 | 1,916 | 2.36 | 2,790 | 1,703 | 1.64 |

The bundle implementation was screened before evaluation. Intermediate
variants are included because they exposed the cost of broad local groups and
duplicate wheat pickups.

| variant | retargets | target runs | mean survival | movement | productive | ratio |
|---|---:|---:|---:|---:|---:|---:|
| radius 4 | 600 | 1,924 | 3.20 | 4,724 | 1,240 | 3.81 |
| radius 2 + inventory validity | 605 | 2,086 | 2.99 | 4,634 | 1,399 | 3.31 |
| same-tile, duplicate pickup path | 534 | 1,965 | 2.87 | 3,676 | 1,829 | 2.01 |
| final: same-tile, create at arrival | 320 | 1,845 | 2.43 | 2,726 | 1,729 | 1.58 |

The final variant crosses both local bars: movement/productive `< 1.64` and
productive `> 1,703`.

## Evaluation

Each sweep used 8 seeds × 2 seats, `seed0 90001`.

| config | opponent | W-L-T | mean margin | worst margin |
|---|---|---:|---:|---:|
| `BUNDLE` | `bench/v16_rc5_high_score_8c_4s_premium_market_.py` | 0W-16L-0T | -84,832 | -97,540 |
| `BUNDLE` | `bench/trace_mined_92791997.py` | 0W-16L-0T | -43,342 | -70,547 |
| `BD1` (bundle + derived plan) | `bench/v16_rc5_high_score_8c_4s_premium_market_.py` | 0W-16L-0T | -143,646 | -168,255 |
| `BD1` (bundle + derived plan) | `bench/trace_mined_92791997.py` | 0W-16L-0T | -100,572 | -133,944 |

`BD1` uses `LAND_TARGET=3`, `HIRES=13`, `6 COW + 3 SHEEP`, and
`34 STRAWBERRY / 18 MELON / 20 WHEAT`, as requested.

## Verdict

The executor passes the cheap movement/productivity acceptance bar, but the
8-seed evaluations are decisively negative. Keep `BUNDLE=False`; the owner
should not enable it or combine it with the derived plan based on this result.
