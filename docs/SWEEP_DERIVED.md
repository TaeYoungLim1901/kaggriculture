# Sweep: the mined top-ladder plan, re-derived into our constants

Date: 2026-08-14. Opponent `bench/v16_rc5_high_score_8c_4s_premium_market_.py`, 8 seeds × 2 seats,
`--seed0 90001`. Shipped `main.py` reference on this panel: **−83,638**.

## Where the plan came from

`python tools/tracedump.py bench/trace_mined_92791997.py` decodes the winning seat of the
highest-rated public episode of 2026-08-13 (`kaggle/kaggriculture-episodes-2026-08-13`, avg_score
3196.96). Its plan:

| | mined top trace | shipped `main.py` |
| --- | --- | --- |
| hands/day | 5 on d0, ramping to **13** held d19–d27 (283 total) | `HIRES = 8` |
| slots issued/day at peak | **316–318**, of which 292–308 are non-PASS (~95%) | ~208/day, `PASS 3,518` |
| land | `BUY_LAND` d6 and d9 → **3 quadrants** | `LAND_TARGET = 1` |
| herd | **6 COW + 3 SHEEP**, 2C+2S on d0 h1, complete by d7 | 8 COW + 6 SHEEP |
| crops | WHEAT replanted continuously (**126** PLANT requests d0–d27), STRAWBERRY 34, MELON 18 | MELON 6 + WHEAT 5 |
| FERTILIZE | 127, concentrated d12–d27 | 0 |
| selling | WHEAT 40–104 units/day plus a 250-unit d29 dump; premium goods metered (STRAWBERRY 4–35/day) | drip by `DRAIN` |

The economic logic is consistent with `research/datasets/kaggriculture-reference-agents/price_curves.csv`:
only WHEAT and EGG have `units_until_price_floor > 6000`. STRAWBERRY floors at 62 units, WOOL 59,
MILK 76, MELON 158. So the volume goes into the crop that cannot be glutted, and premium goods are
metered rather than scaled.

## Result

| config | levers | W-L-T | mean margin | vs shipped |
| --- | --- | --- | ---: | ---: |
| shipped `main.py` | — | — | −83,638 | — |
| `D-hands` | `HIRES = 13` only | 0W-16L | **−139,995** | −56,357 |
| `D1` | full derived plan: 3 quadrants, 13 hands, 6C+3S, 34 straw / 18 melon / 20 wheat | 0W-16L | **−143,644** | −60,006 |

`python tools/thrash.py .sweep/D1.py`, seed 90001: movement/productive **1.95**, against 1.64 for
the shipped build. The derived plan makes routing *worse*.

## The lever that did pay: a SMALLER herd

Testing the derived plan's parts separately found one gain, and it is the opposite of what we had
been trying all week — fewer animals, not more.

| config | levers | mean margin (8 seeds × 2 seats) | vs shipped −83,638 |
| --- | --- | ---: | ---: |
| `D-herd` | 8C+6S → 6 COW + 3 SHEEP, nothing else | −79,272 | +4,366 |
| `D-wheat` | 15 wheat tiles | −84,770 | −1,132 |
| `D-land` | 3 quadrants, 8 hands | −156,094 | −72,456 |

`price_curves.csv` explains it: MILK floors after 76 units and WOOL after 59. A 14-animal herd
overproduces into a floored market *and* eats the wheat that would otherwise be sold. The mined top
trace runs 6 COW + 3 SHEEP for the same reason.

Combining the small herd with the strawberry mix was superadditive — +4,366 and +5,199 separately,
+12,940 together — because the freed structure tiles go to berries:

| config | herd | crops | mean margin | vs shipped |
| --- | --- | --- | ---: | ---: |
| `H9-S7` | 6C+3S | STRAWBERRY 7 / WHEAT 4 | −75,132 | +8,506 |
| `H9-S10` | 6C+3S | STRAWBERRY 10 / WHEAT 6 | −70,698 | +12,940 |
| `H9-S12` | 6C+3S | STRAWBERRY 12 / WHEAT 4 | −76,859 | +6,779 |
| `H9-S14` | 6C+3S | STRAWBERRY 14 / WHEAT 2 | −73,055 | +10,583 |
| `H6-S10` | 4C+2S | STRAWBERRY 12 / WHEAT 7 | −74,063 | +9,575 |
| `H11-S8` | 7C+4S | STRAWBERRY 8 / WHEAT 6 | −70,817 | +12,821 |

S10 → S12 → S14 is not monotone, so the 8-seed panel carries several thousand of noise; do not read
a trend off two points of it.

## Confirmation on a bigger panel and a second opponent

Every row above is an 8-seed panel. Re-measured at 24 seeds × 2 seats (48 episodes), with the
shipped build re-run on the *same* panel — a reference taken at a different panel size is not
comparable, which is why `BASE` now exists in `tools/sweep.py`:

| build | vs meta bench, 48 episodes | vs mined top trace, 16 episodes |
| --- | ---: | ---: |
| shipped (`BASE`) | −86,140 | −42,825 |
| `H9-S10` | −72,821 (**+13,319**) | −40,058 (**+2,767**) |
| `H11-S8` | −72,376 (**+13,764**) | −38,960 (**+3,865**) |

The two candidates are 445 apart on the meta panel and 1,098 apart on the mined panel — inside the
noise individually, but `H11-S8` is ahead on both independent opponents, so it is the pick. Shipped
as `ANIMAL_PLAN = 4 SHEEP + 7 COW`, `CROP_PLAN = [("STRAWBERRY", 8), ("WHEAT", 6)]`.

## The conflict: it loses to its own predecessor

Head to head against `bench/v3.py`, a byte copy of the previously shipped build, the new build goes
**0W-48L, mean margin −8,279**. Against every third party it is ahead. Both numbers are real:

| opponent | new build | shipped v3 | delta |
| --- | ---: | ---: | ---: |
| meta bench, 48 episodes | −72,376 | −86,140 | **+13,764** |
| mined top trace, 16 episodes | −38,960 | −42,825 | **+3,865** |
| `bench/ref_broker_bea.py` (reference tier 6), 16 episodes | −64,923 | −68,330 | **+3,407** |
| `bench/ref_closer_cleo.py` (reference tier 9), 16 episodes | −62,902 | −66,881 | **+3,979** |
| **`bench/v3.py` itself, 48 episodes** | **−8,279** | — | **0W-48L** |

The mirror-panel reading is that vacating melon, milk and wool hands v3 those niches uncontested
while our own strawberry volume — 8 tiles against a 62-unit price floor — crashes the one product we
kept. That is the bias recorded in `docs/META.md` §5c, and the three independent opponents above all
agree with the new build. The reference agents are the cleanest evidence available: they come from
the public reference dataset, share no lineage with either of our builds, and have no reason to
concede the berry niche.

## What this establishes

The plan is not the gap. Handed the top of the ladder's own field plan, our agent loses another
60,000 — because our executor cannot keep 13 hands busy across three quadrants. They issue ~318
slots/day at ~95% non-PASS; we hold 3,518 PASS and spend 1.64–1.95 movement actions per productive
one. More hands without more *local* work is pure wage cost (hire cost is `fib(n)`, so 13 hands is
roughly 609/day against 54/day for 8).

The remaining lever is therefore the assignment/routing engine, not any constant:
`docs/RESEARCH_IDEAS.md` ranks 1–3 (home-range rosters, round-trip marginal-cost bids, chained task
bundles with deadline preemption). Their acceptance bars are already written there: movement per
productive below 1.64 **and** productive above 1,703, measured with `tools/thrash.py`, before any
eval is run.

See also `docs/SWEEP_METASCALE.md`, which reached the same wall from the other direction.
