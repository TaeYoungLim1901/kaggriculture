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

## Correction, 2026-08-14: every `HIRES > 8` row above is void

The extra-hire refill loop in `_market` had no slot budget and no affordability check:

```python
if hour > 0 and HIRES > 8 and len(orders) < 10:
    hired = int(_g(farm, "hires_today", 8) or 0)
    orders += [["HIRE"]] * min(max(0, HIRES - hired), 10 - len(orders))
```

`_do_hire` (`kaggriculture.py:689`) returns silently without advancing `hires_today` when
`money < cost`, and the env accepts only `maxMarketOrdersPerTurn = 10` orders. So one broke hour
deadlocks the season: HIRE fills all ten slots, no SELL goes out, no cash arrives, the hires keep
failing, and the request repeats every hour for the rest of the day. Measured on seed 7 at
`HIRES = 13`: **1,516 HIRE orders for the 390 wanted**, SELL 527 -> 336, money $70,267 -> $46,222,
with day 4 hour 0 opening on $1 and 8 of 8 hires failing.

Fixed with two guards — `HIRE_SLOTS = 2` per turn, cumulative `_fib` affordability against
`CASH_FLOOR` — plus a herd gate (`not todo`), because days 1-10 run on $123-$588 and extra wage
there starves `BUY_ANIMAL`/`BUY_SEED`. The mined top-ladder trace independently ramps to 13 hands
only from d19. `HIRES = 8` never enters this branch, so the shipped build is byte-identical in
behaviour (`check.py strength` 16W-0L, +81,856).

The wage arithmetic above was also wrong. Cost is `sum(fib(0..n-1))` with `fib(0) = 0`, so the first
hire is free: **8 hands is $33/day and 13 hands is $376/day**, not $54 and $609.

Re-measured vs `bench/ref_broker_bea.py`, 8 seeds x 2 seats (BASE = -64,804):

| config | mean margin | vs BASE |
| --- | ---: | ---: |
| `H13` (13 hands, 1 quadrant) | -74,850 | -10,046 |
| `E2-H8` (2 quadrants, 8 hands) | -89,818 | -25,014 |
| `E2-H12` (2 quadrants, 12 hands) | -79,011 | -14,207 |

The conclusion of this document survives: expansion still loses. But the *reason* is now narrower.
More hands are no longer pure waste — at two quadrants 12 hands beat 8 by **+10,807**, the first time
crew size has ever paid. NW is exactly full at the shipped plan (11 structures + 14 crops = 25 tiles
= one quadrant), so at one quadrant there is no work for a 9th hand to do and `H13` correctly loses
about its own wage. Land is the thing that does not pay for itself; hands scale with it.

## Correction, 2026-08-14 (2): `ANIMAL_PLAN` was never what stood on the board

`_wanted` derived the still-to-buy list from animals *standing on tiles*. An animal in the shed or
carried by a hand therefore still read as wanted and got re-bought every few hours while in transit
(seed 7: three SHEEP bought on d7 for the plan's one remaining slot). v4 declares 11 animals and runs
**13 for 19 of 30 days** — and 13 structures + 14 crops = 27 tiles against a 25-tile quadrant, so two
crop tiles silently never existed. Every herd-size row in this document compared two *requests*, not
two boards.

Fixed by passing `held` (shed + inventories) into `_wanted`. New invariant `_check_herd_cap` in
`tests/test_invariants.py`, verified to FAIL on the pre-fix `main.py`
(`own 12 animals, plan is 11 (d11 h4)`).

**The fix alone cost −8,500**, because the bug had been *pipelining* acquisition: buying one animal
and waiting for it to be picked up and placed serialises the ramp at hours per animal. `ANIMAL_PIPELINE`
(default 3) restores it by ordering every animal whose structure is already vacant, bounded by the
number already in flight. Depth is flat past 2 (`P2` −64,968, `P4` = `P6` −65,438).

With the ramp restored the herd knob finally measures the herd, vs `ref_broker_bea`, 8 seeds x 2 seats:

| config | herd | mean margin |
| --- | ---: | ---: |
| `BASE` (4 SHEEP + 7 COW) | 11 | **-65,370** |
| `A10c` | 10 | -67,390 |
| `A12c` | 12 | -68,273 |
| `A13` (6 SHEEP + 7 COW, what v4 really ran) | 13 | -69,638 |
| `A9c` | 9 | -85,760 |

v4's plan was right all along; it was simply never executed. 11 beats the 13 it actually ran by 4,268.

## Reversal, 2026-08-14 (3): drip selling is a loss

v2's headline feature was drip selling — spreading a daily `DRAIN` quota across the 23 sell hours so
prices "never collapse". It is wrong, and wrong monotonically. `DRAIN_SCALE` multiplies the quota;
head-to-head against the unscaled build, 8 seeds x 2 seats:

| DRAIN_SCALE | W-L | mean margin |
| ---: | --- | ---: |
| 0.60 | 0W-16L | -5,904 |
| 0.75 | 0W-16L | -3,830 |
| 0.90 | 0W-16L | -1,422 |
| 1.25 | 14W-2L | +1,112 |
| 1.50 | 14W-2L | +2,920 |
| 2.0 | 16W-0L | +3,390 |
| 3.0 | 14W-2L | +3,045 |
| 5.0 | 16W-0L | +2,429 |
| **999 (no throttle)** | **16W-0L** | **+7,581** |

Holding stock back does not protect the price. The town refills the order book every turn, so an
unsold unit is not a defended price — it is a unit sitting in the shed while the refill it was
waiting for is consumed by someone else. The original calibration (`tools/drain.py`) measured the
town's consumption **alone**, with no opponent competing for the same refill.

This is the first change where the mirror panel and the independent references agree, 32 episodes each:

| opponent | v5 | v6 (no throttle) |
| --- | ---: | ---: |
| `main.py` (v5) | — | **16W-0L, +7,581** |
| `bench/v4.py` | 22W-10L | **28W-4L (88%)** |
| `bench/v3.py` | 10W-22L (31%) | **18W-14L (56%), +401** |
| `ref_broker_bea` | -69,705 | **-63,807** |
| `ref_closer_cleo` | -67,690 | **-63,672** |

First build in the lineage to win the v3 matchup. Submitted as v6.

**Everything tuned under the throttle is now suspect** — herd size, crop mix, `HIRES`, and especially
the expansion verdict, since part of expansion's cost was flooding a market we were also throttling.
Re-tune from scratch with `tools/tune.py` (Optuna, resumable SQLite study in `.sweep/tune.db`).

## 2026-08-14 (4): the order slot is a price race, and we were in last place

`_process_market` walks the two players' order lists **by index in lockstep**, committing every unit
of slot `i` before touching slot `i+1` (`kaggriculture.py:542-615`). A SELL in a late slot therefore
prices against an order book the opponent's early-slot SELL has already filled. `HIRE` and `BUY_LAND`
are atomic and settle regardless of position, so putting them first costs real money.

We were emitting 8 `HIRE` orders at hour 0 and selling from slot 8. Two changes:

- **Sell first.** Sells are now built before hires and purchases, at every hour. Worth **+2,794**
  (16W-0L) on its own.
- **`HIRE_HOUR0`** splits the crew: how many hires go in hour 0's ten slots, the rest topped up from
  hour 1 at `HIRE_SLOTS` per turn. Hour 0 sells into the fullest shed of the day (everything the hands
  dropped at the rollover), so slots spent hiring there are expensive. Against the 8/0 split, 8 seeds
  x 2 seats: 7 +4,673 / 6 +5,298 / 5 +4,321 / **4 +6,632** / 2 +4,343, all 16W-0L. Do not cut the
  crew itself to buy the slots — `HIRES` 6 falls to +1,814 and `HIRES` 4 to -13,484.

Shipped as v7. 32 episodes each: vs v6 **32W-0L +5,952**, vs `bench/v4.py` **30W-2L (94%)**, vs
`bench/v3.py` 18W-14L (56%), `ref_broker_bea` **-62,684** (v6 -63,807), `ref_closer_cleo` **-61,811**
(v6 -63,672). Every panel at least matches v6.

Also established, from the env source, and NOT exploitable: `BUY_PRODUCT` quotes at post-buy
inventory `P(I-1)` and selling back quotes the same `P(I-1)`, so a wheat/fertilizer round trip nets
exactly zero — there is no arbitrage. `shedCapacity` gates buying and depositing but never SELL, so
dumping early frees shed room but carries no price advantage of its own.

Optuna (`tools/tune.py`, study `v6mirror`) put `LAND_TARGET = 2` in all five of its top trials, but at
8 episodes per trial its winners collapse when re-measured at 32 (`T33-F4` 2W-14L, `T46` worst
-13,909). Re-run the study at a larger `--games` before believing any row of it.

## 2026-08-14 (5): expansion wins once the throttle is gone

Every earlier test said two quadrants lose. They were all run under the sell throttle, and part of
expansion's cost was flooding a market we were simultaneously metering. With `DRAIN_SCALE = 999` the
answer flips. Found by the Optuna study `v9mirror` (`tools/tune.py`, 100 trials against a frozen
`main.py`, all five top trials converging on the same shape) and confirmed at 32 episodes.

v10: `LAND_TARGET = 2`, `ANIMAL_PLAN` 5 SHEEP + 8 COW, `CROP_PLAN` 4 STRAWBERRY + 12 WHEAT,
`HIRES = 10`, `HIRE_HOUR0 = 5`, `ANIMAL_RESERVE = 2`, `ANIMAL_PIPELINE = 5`, `SEED_BATCH = 5`.
The plan needs the second quadrant outright: 13 structures + 16 crops = 29 tiles against NW's 25.

| opponent | v10 | v7 (shipped) |
| --- | ---: | ---: |
| `bench/v3.py` | **24W-8L, +7,563** | 18W-14L, -1,499 |
| shipped v7 | **30W-2L, +4,601** | — |
| `ref_broker_bea` | -64,111 (worst -85,425) | -62,684 (worst -94,870) |
| `ref_closer_cleo` | -64,246 (worst -82,057) | -61,811 (worst -91,481) |

The references cost ~2k of mean margin and return a much better worst case; we lose to both 0W-32L
either way, so only the same-lineage columns carry information about the ladder. v7 scored **737.9**,
the best reading any build in this lineage has had, which is the evidence for trusting them.

**It is a local optimum in every direction tested**, 32 episodes each, one knob at a time against the
build in the tree: `HIRES` 11 (24W-8L against it) and 12 (0W-32L), `HIRE_HOUR0` 4 (6W-26L), herd
5S+7C (10W-22L) / 5S+9C (7W-25L) / 7S+8C (6W-26L), wheat 9 (0W-32L) / 16 (4W-28L), strawberry 8
(0W-32L), `LAND_TARGET` 3 (0W-32L), `ANIMAL_PIPELINE` 4 (13W-19L).

### Why FERT_RESERVE works, and it is not fertilizer

Reserving fertilizer does not raise the FERTILIZE count (162 -> 156) because the berries were already
at full coverage, and `_act` runs its unit actions before `_market` anyway. The reserve is applied
*after* the sell list is sorted, so zeroing fertilizer's quantity drops its order entirely and
**shifts every later SELL one slot earlier** — the same order-slot race as above. Also worth
recording: the "reverse test agrees" argument is not independent evidence, it relabels the same
paired games. A 27-5 split with a +35 mean is consistent with many tiny wins and a few larger losses.

## 2026-08-14 (6): distance was worth nothing in the assignment cost

`_assign` scores a unit/task pair as `PRIO_COST[prio] + DIST_WEIGHT * dist`. `PRIO_COST` spans 780
and a board crossing is about 18 tiles, so at `DIST_WEIGHT = 1` priority strictly dominated: a unit
would cross the whole farm past equivalent work to reach a task one band higher.

That is affordable on one quadrant and not on two. Expansion pushed movement/productive from 1.64 to
**2.13** — 68% of active slots were commute. Raising the weight so a 10-tile detour costs a whole
priority band fixes it with no code change at all.

32 paired episodes against `DIST_WEIGHT = 1`:

| weight | W-L | mean margin |
| ---: | --- | ---: |
| 5 | 10W-22L | -352 |
| 8 | 27W-5L | +1,380 |
| 10 | 31W-1L | +1,799 |
| 12 | 31W-1L | +1,860 |
| 15 | 28W-4L | +2,311 |
| **20** | **30W-2L** | **+2,367** |
| 30 | 14W-18L | +537 |
| 50 | 14W-18L | -830 |

Non-monotone, and 5 is worse than 1 — the curve is not a simple tradeoff. 20 beats 10 head to head
(21W-11L) and 12 (18W-14L), so it is the pick. Result: movement/productive **2.13 -> 1.97**,
productive actions 1,863 -> 1,907 on seed 90001.

This is the first routing-layer gain in the project, and it came from a constant that had been sitting
at its default the whole time. `PRIO_COST`'s band shape is now a routing knob too, not just an
ordering, since a 200-point gap buys 10 tiles of walking.

New tool: `tools/panel.py` — one command, one table, the candidate against `main.py`, `bench/v3.py`,
`bench/v4.py` and both reference agents, with `--baseline` for a delta column.

## Reading the sweep table: what "no effect" looks like

`tools/eval.py` plays each seed in both seats, and the seats are mirror images of one episode, so a
seat-0 win is the same game's seat-1 loss. An identical build against itself scores **balanced W-L
plus ties with mean margin exactly +0** — not all ties, because the episode is slightly seat
asymmetric (atomic market orders resolve in player order, `kaggriculture.py:558`). Measured:
`main.py` vs `main.py` is `2W-2L-4T, +0, worst -209`.

The summary line's win rate is `W / (W + L + T)`, so a no-effect variant reports something like
"34% win rate" and reads as a mild loss. `ANIMAL_RESERVE` 3 and `SEED_BATCH` 3 and 8 each reported
`11W-11L-10T, +0, worst -1,280` with byte-identical per-seed money: all three are simply no-ops at
the shipped plan. Read the mean margin first; a real effect looks like 30W-2L well clear of zero.

## Routing: retargeting is not waste

Units re-target 836 times before arrival per episode with a mean target survival of 2.36 turns, which
looks like thrash. It is not. Three attempts to keep a unit on its target all lose, 32 paired episodes
each against the shipped build:

| variant | W-L | mean margin |
| --- | --- | ---: |
| `STICKY` (hard lock until arrival) | 0W-32L | -15,861 |
| `BUNDLE` (persistent local queues) | 5W-27L | -963 |
| soft hysteresis, bonus 50 to the current target | 5W-27L | -1,647 |
| soft hysteresis, bonus 100 | 0W-32L | -3,362 |
| soft hysteresis, bonus 200 | 0W-32L | -2,814 |

Consistent with `DIST_WEIGHT = 20` being the thing that worked: once distance is priced properly,
re-targeting to a nearer task is the *correct* move, and any term that resists it is a cost. The
hysteresis code was reverted rather than left behind a zero default.

`ANIMAL_RESERVE` 2 also holds (1 is 0W-32L, 3 is a no-op) and `SEED_BATCH` no longer binds at all.

## 2026-08-14 (7): LAST_DAY is not about liquidation

`dump = day >= LAST_DAY` no longer means "sell the stock before the season ends" — `DRAIN_SCALE`
already sells everything sellable every hour. All the flag still switches off is the **wheat feed
reserve and `FERT_RESERVE`**. Pouring wheat into a shared order book depresses it for the opponent,
who also grows wheat, while we buy ours back at the price our own sale created: roughly neutral for
us, expensive for them. That is why the margin gain is modest and the W-L is not.

32 paired episodes against `LAST_DAY = 29`:

| LAST_DAY | W-L | mean margin | worst |
| ---: | --- | ---: | ---: |
| 27 | 31W-1L | +967 | -57 |
| 24 | 32W-0L | +1,439 | +70 |
| 20 | 32W-0L | +2,384 | +460 |
| 17 | 30W-2L | +2,158 | -336 |
| **15** | **32W-0L** | **+5,037** | **+1,875** |
| 12 | 32W-0L | +4,601 | +794 |
| 10 | 32W-0L | +4,347 | +523 |

### The bug it exposed

Dropping the feed reserve turned the `logic` stage red: `PICKUP` no-ops went to 12 of 176. The
`wheat_pickup` reservation in `_market` summed the *actions being emitted this turn*, so it saw only
units already standing at the shed door. A unit walking there emits a movement action, so its pickup
was invisible and `_market` sold the wheat out from under it before it arrived. Summing the committed
`errand` entries instead fixes it: 12/176 -> 2/166. The reservation had been under-counting since it
was written; `LAST_DAY` only made it cross the 5% threshold.

v13 = LAST_DAY 15 + that fix. 32 paired episodes: vs v12 **32W-0L +4,879 worst +1,780**,
`bench/v4.py` **32W-0L +17,111**, `bench/v3.py` 26W-6L +9,619, `ref_broker_bea` -61,768.

## Routing, closed: constraining the matching always loses

Four independent attempts to stop units roaming, each 32 paired episodes against the shipped build:

| variant | W-L | mean margin |
| --- | --- | ---: |
| `STICKY` — hard target lock until arrival | 0W-32L | -15,861 |
| `BUNDLE` — persistent local work queues | 5W-27L | -963 |
| soft hysteresis on the current target, 50 / 100 / 200 | 5W-27L / 0W-32L / 0W-32L | -1,647 / -3,362 / -2,814 |
| home-zone rosters, 2 / 3 / 4 zones at penalty 300 | 5W-27L / 0W-32L / 0W-32L | -1,184 / -3,324 / -5,111 |
| home-zone rosters, 3 zones at penalty 100 | 1W-31L | -930 |

The zone variant exempted FEED and WATER from the penalty and still lost. `docs/RESEARCH_IDEAS.md`
ranks these ideas 1-3; they are answered. The exact min-cost matching with `DIST_WEIGHT = 20` is
already the right policy, and every spatial or temporal constraint on it costs more than it saves.
The remaining `movement/productive` of 1.97 is the cost of a genuinely distributed task set, not
thrash — the code was reverted rather than left behind a zero default.

## 2026-08-15: the crop plan wants wheat, and the limit is total tiles

`LAST_DAY = 15` changed the economics enough that the crop plan needed re-tuning — the same rule that
caught the herd after the sell throttle came off. Under `LAST_DAY = 29`, 16 wheat tiles lost 4W-28L.
Under 15 it wins 32W-0L. Wheat is the price weapon, so the plan wants as much of it as the board
carries.

32 paired episodes, against 4 strawberry + 12 wheat:

| crop plan | tiles | W-L | mean margin |
| --- | ---: | --- | ---: |
| 4 berry + 9 wheat | 13 | 0W-32L | -3,367 |
| 4 + 16 | 20 | 32W-0L | +1,613 |
| 4 + 20 | 24 | 32W-0L | +2,474 |
| 4 + 24 | 28 | 32W-0L | +2,991 |
| 4 + 26 | 30 | 0W-32L | **-15,208** |
| 8 + 20 | 28 | 0W-32L | -4,653 |

The cliff is not the wheat count: **28 total crop tiles works and 30 does not**, whatever the mix.
Ten hands cannot water and harvest more than about 28 tiles on top of 13 animals. Within that budget,
against 4 + 24: 0 berry + 28 wheat +800, 1 + 27 +904, **2 + 26 +2,735**, and 2 + 28 (30 tiles) loses
again. Shipped: **2 STRAWBERRY + 26 WHEAT**.

Re-checked under the new plan and unchanged: `HIRES` 12 is 0W-32L, 5S+9C is 7W-25L, `LAST_DAY` 10 is
5W-27L and 20 is 0W-32L.

v14 vs v13 **32W-0L +5,735 worst +4,365**. vs `bench/v3.py` **32W-0L +14,993**, the first clean sweep
of it. `ref_broker_bea` **-58,898**, the best margin the lineage has recorded (v7 -62,684).
Against the two strongest benches it is mixed: meta bench -60,454 against v13's -53,629, mined trace
92791997 -31,664 against v13's -38,133. All four stages green.

Trading animals for crop tiles at a constant labour cost does not pay: 11 animals + 31 crops is
14W-18L -179 (neutral but with a -8,056 worst case) and 15 animals + 25 crops is 6W-26L -4,501.
13 animals + 28 crops stands.

## Session 8 — read the shared order book, not our own order list

`tools/bookprobe.py` (new) replays a finished episode and prints the per-day price and inventory of
every product plus **both** players' order streams. `tools/slotprobe.py` only ever saw the list we
returned from `_market`, so it could not show what the opponent was doing to the prices we sell into.

### What the book looks like against `ref_broker_bea` (seed 7)

| product | day 0 | day 29 | we sold | bea sold | our revenue | bea revenue |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| WHEAT | 25 | 51 | 4,804 | 1,143 | 220,872 | 48,909 |
| STRAWBERRY | 120 | **243** | 20 | **651** | 4,382 | **154,626** |
| MELON | 250 | 167 | 0 | **236** | 0 | **52,533** |
| MILK | 160 | **1** | 201 | 691 | **1,881** | 14,498 |
| WOOL | 200 | **1** | 155 | 390 | 6,567 | 3,703 |
| FERTILIZER | 100 | 16 | 245 | 445 | 12,993 | 22,313 |

Three facts fall out of that table.

**1. Our wheat revenue is mostly churn.** We also *buy* 4,632 WHEAT (`BUY_PRODUCT`, 374 orders) for
-213,880 against the 220,872 we sell. Net production is ~950 units — 40 per tile from 24 tiles, which
is what `max_yield 6` over six replant cycles predicts. The feed loop buys wheat up to
`n_animals * 2` and the sell loop dumps everything above that same threshold in the *same* turn, so
half of every day's order slots go to a round trip worth about $1.5 a unit. The 24 wheat tiles are a
~$43k business, not a $220k one.

**2. Strawberry and melon are an untouched book.** STRAWBERRY *rises* from 120 to 243 while bea takes
651 units out of it, because the town drains it faster than one player can supply it (below-I0 branch,
`sqrt`, `below_target 0.70`). MELON is in no shop at all — town-centre demand only — and still pays
bea $222 a unit. We sell 20 strawberries and zero melon all season.

**3. The animals are being priced out from under us.** MILK goes to $1 by day 17 because bea sells 691
of it; our 201 milk earns $1,881, against $38,520 in the same matchup versus `bench/v3.py`. WOOL is
even more brittle: `above_func sq`, `above_target 3.20`, `T 105` means ~59 units above I0 takes the
price from 200 to the floor. Milk and wool revenue is a function of what the *opponent* does, not of
our herd.

### The board that beats us

`ref_broker_bea` at day 20 (seed 7): **40 STRAWBERRY, 9 MELON, 3 WHEAT**, 8 COW, 5 SHEEP, three
quadrants (`BUY_LAND` × 2). Ours: 24 WHEAT, 2 STRAWBERRY, 10 WEED, one extra quadrant. Money is level
at day 20 (19,801 vs 20,899) and then splits — day 25 21,829 vs 54,154, day 29 24,872 vs 78,221.
Strawberry pays from `first_yield_day 10` onward and compounds; wheat is flat.

Every berry row in this file caps at 10 strawberry tiles, and the 28-tile labour ceiling above was
measured on a wheat-heavy mix — wheat needs a replant every cycle, an ongoing crop does not. The
ceiling has never been measured for a field that is mostly strawberry.

### Melon is the win; the strawberry field is not (yet)

Mirror panel, 12 seeds × 2 seats, seed0 90001, against the shipped v14:

| crop plan | tiles | W-L | mean | worst |
| --- | ---: | --- | ---: | ---: |
| 20 / 30 / 40 STRAWBERRY (`LAND_TARGET` 3) | 30-44 | 0W-24L | -47k to -50k | -73,831 |
| 40 STRAWBERRY + 9 MELON | 53 | 0W-24L | -38,487 | -56,678 |
| `LAND_TARGET` 3 alone | 28 | 0W-24L | -2,676 | -3,910 |
| 2 berry + 9 MELON + 17 wheat | 28 | 24W-0L | +4,245 | +582 |
| 9 MELON + 19 wheat | 28 | 24W-0L | +7,053 | +4,086 |
| 8 MELON + 20 wheat | 28 | 24W-0L | +7,946 | +6,286 |
| 8 MELON + 24 wheat | 32 | 24W-0L | +7,982 | +6,508 |
| **8 MELON + 26 wheat** | **34** | **24W-0L** | **+8,037** | **+6,351** |
| 8 MELON + 28 / 30 wheat | 36 / 38 | 24W-0L | +7,552 / +7,529 | |
| 10 / 12 MELON + 26 wheat | 36 / 38 | 24W-0L / 6W-18L | +6,367 / -433 | |
| 8 MELON + 26 or 32 wheat, `LAND_TARGET` 3 | | 24W-0L | +4,926 / +5,353 | |

**The 28-tile labour ceiling was a wheat artifact.** 34 tiles works as soon as 8 of them are melon:
a melon tile is planted once and then only watered until day 13, where a wheat tile needs a replant
every cycle. Melon past 10 tiles loses — its glut curve is `sq` (amp `3.6·250/300² = 0.01`), so
`p(x) = 250 - 0.01x²` and the first floor quote is 158 units above I0. Eight tiles yield 12 units each
over two plantings, ~96 units, which sits on the flat part of that shelf.

`CROP_PLAN` order is load-bearing: the seed-buy loop in `_market` spends its budget in list order, so
a $100 STRAWBERRY seed listed ahead of the $10 WHEAT seed starves the cash engine — the 20-berry
variant holds $118 on day 10 where the shipped build holds $7,552. Putting WHEAT first halves the
berry loss (-47,004 → -18,972) but it still loses 0W-24L, and for melon it *costs* +6,703
(8 melon + 20 wheat is +7,946 melon-first and +1,243 wheat-first — melon seed has to be in the ground
early or the tile never reaches its day-10 first yield). The berry field is a real strategy that our
opening cannot finance; melon is the part of it we can reach today.

**v15 = `CROP_PLAN = [("MELON", 8), ("WHEAT", 26)]`, everything else unchanged.**
vs `bench/v14.py` **64W-0L +8,105 worst +5,420** (32 seeds × 2 seats). Panel at 32 episodes:
`v3` 32W-0L **+25,387** (v14 +14,993), `v4` 32W-0L +29,402, `ref_broker_bea` **2W-30L -47,700**
(v14 -58,898 — the first wins the lineage has ever taken off a reference agent),
`ref_closer_cleo` 0W-32L -55,168. All four stages green.
