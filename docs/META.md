# META — what the top of the leaderboard actually does

Derived from the four public notebooks in `CONTEXT.md` §1 (agents extracted to `bench/`) and from
reading the environment source directly. Numbers below were computed against the real
`market_price()` in `kaggle_environments 1.32.6`, not from the docs.

## 1. The public meta is a hard-coded replay trace

Every strong public agent is the same shape:

```
_ACTIONS = <719-step action script, zlib+base85 embedded>   # ~19 KB
agent(obs) = script[step] + small reactive patches
```

- **boatlee V16-RC5** — reconstructed Nikita Lugovoy's submission `55440039` by majority-voting the
  `farmer` / `hands` / `market` action across three *public replay JSONs*. Route: 3 quadrants,
  4 SHEEP immediately, 8 COW by step 192, mixed WHEAT/STRAWBERRY/MELON. Patches: WEED repair
  (`DIG` then replay the intended action) and a one-turn **premium sell front-run**.
- **kaitofukami v25** — same idea off THUNDER THUNDER's replay `91249452`. Explicitly reports that the
  public v23 opening appears in **22 of the Top-30 teams**. Its warning is the important part:
  freezing another top player's adaptive trace scored **0/50** — a replay is behavior under one state
  path, not a portable policy.
- **andrewsokolovsky C166** — trace + mirror detection (public-farm fingerprint distance) + a counter
  to the front-run above.

Consequences for us:

1. **Public replays are the dataset.** `kaggle competitions replay <EPISODE_ID>` yields every action a
   top agent took. That is the entire "no raw data" answer.
2. Copying a trace lands you inside a large mirror cluster where matches are decided by tie-breaking
   overlays, not strategy.
3. Traces are brittle: they desync on weeds, on lost money, on any state drift. Everyone bolts on
   repair logic. A genuinely reactive policy that matches the route's economics should beat them on
   the tail seeds.

## 2. Scoring reality

Rating is **win/loss/tie only — coin margin is ignored**. Winning by $1 equals winning by $20,000.
kaitofukami measured 86% of losses within 4,000 coins. Optimize win *rate* and variance, not mean money.

## 3. Market math (the part the docs do not spell out)

Prices move with market inventory (`I0 = 10,000` for every product). Cumulative revenue for selling
`k` units into an otherwise-untouched market:

| Product | $ at +0 | +50 | +100 | rev(100 units) | rev(300 units) |
| --- | ---: | ---: | ---: | ---: | ---: |
| MELON | 250 | 225 | 150 | **$21,721** | $26,627 |
| FERTILIZER | 100 | 90 | 80 | **$9,010** | **$21,030** |
| EGG | 50 | 43 | 42 | $4,371 | **$12,559** |
| WOOL | 200 | 55 | 1 | $7,969 | $8,169 |
| MILK | 160 | 55 | 1 | $6,205 | $6,405 |
| TOMATO | 60 | 42 | 35 | $4,318 | $9,207 |
| STRAWBERRY | 120 | 24 | 1 | $3,847 | $4,047 |
| CARROT | 35 | 27 | 23 | $2,738 | $6,510 |
| WHEAT | 25 | 22 | 21 | $2,193 | $6,313 |

Read it as two families:

- **Crash-hard (STRAWBERRY, MILK, WOOL, MELON):** at the price floor by 100–200 units. Their whole
  season value is front-loaded. Dumping them is throwing money away; they must be dripped.
- **Absorbers (WHEAT, EGG, FERTILIZER, CARROT, TOMATO):** `log`/`sqrt` glut curves, essentially a flat
  price at any realistic volume. EGG holds ~$37 even 1,600 units deep.

### Town demand is the reset button

Town consumption drains market inventory, which pushes prices back *up*. Shops unlock one per 3 days,
drawn uniformly with replacement, capped at 8 instances (all 8 by day 24). Each instance consumes
1 of each demanded product every 4 turns = **6/day** (single-product shops 2× = 12/day). The town
center consumes 1 of every non-fertilizer product per day, flat.

Expected steady-state drain once all 8 shops are up (8 × P(shop demands product), from the shop table):

| Product | expected drain/day | note |
| --- | ---: | --- |
| WHEAT | ~31 | in 5 of 8 shops |
| STRAWBERRY | ~25 | in 4 of 8 |
| MILK | ~19 | in 3 of 8 |
| CARROT | ~19 | PET_CAFE is 2× |
| EGG | ~13 | in 2 of 8 |
| TOMATO | ~13 | in 2 of 8 |
| WOOL | ~13 | YARN_STORE only, 2× |
| **MELON** | **1** | **in no shop — town center only** |
| **FERTILIZER** | **0** | **excluded from the town center entirely** |

This is the single most actionable fact in the game: **sell each product at roughly its town drain rate
and the price never falls.** Selling faster than the drain permanently destroys your own price.

MELON and FERTILIZER have no meaningful drain, so their revenue tables above *are* the season cap:
~$21k of melon and ~$21k of fertilizer, and not a coin more. Everything past ~130 melons is worthless.

## 4. Production economics

- **FERTILIZER is free money.** Every surviving animal makes 1 fertilizer available at end of day
  regardless of feeding or care, and it does not accumulate — one `COLLECT_FERTILIZER` per animal per
  day. 12 animals × 25 days = 300 units ≈ **$21k**, one action each, no input cost. This is plausibly
  the real reason the 8C/4S route wins, more than the milk.
- **EGG is the only scalable premium good.** GOOSE: $300, coop, first yield day 4, then 1/day forever.
  With `FEED` + `CARE` every day the banked care bonus pays out on the next day's production, i.e.
  ~2 eggs/day/goose at ~3 actions (FEED, CARE, HARVEST) + 1 wheat. Egg price barely moves with volume.
- **MELON is the best crop per tile** ($250 base, 6 units, no shop demand so drip it) but capped at
  ~130 units for the season.
- **Labour is nearly free.** `HIRE` costs `fib(n)` — hands 1..8 on one day cost 1+1+2+3+5+8+13+21 = **$54
  total**. Nine units × 24 turns = 216 actions/day. Actions are not the bottleneck; tiles, wheat supply,
  and market absorption are.
- **Shed cap is 100 non-seed items** and overflow is silently discarded at the end-of-day drop. Any
  build that stockpiles must sell continuously.

## 5. Where our agent stands (measured 2026-08-14)

`main.py` v2: 6 SHEEP + 8 COW + 6 melon + 5 wheat tiles, NW quadrant only, optimal unit→task
matching, drain-rate drip selling on all 23 non-hire turns.

All numbers below are reproducible: `python tools/eval.py --opp <X> --games 8 --seed0 90001`
(a holdout panel, 8 seeds × both seats).

| Benchmark | Result |
| --- | --- |
| solo economy (vs `pass`), holdout panel | mean margin **+$75,190**, worst +$37,649 |
| vs built-in `starter` | 16W-0L, mean +$86,613 |
| vs `bench/v16_rc5…` (public top trace) | **0W-16L**, mean −$93,870 |
| v2 vs v1 head-to-head, holdout panel | **16W-0L**, worst +$2,881 |

Session progression on the 3-seed tuning panel: $58,032 → $62,129 (price-gated selling) → $72,317
(Hungarian matching, +13%) → $87,644 (capital-allocation fix) → $90,473 (6 sheep instead of 4).
Then v2 on the holdout panel: +$67,336 → **+$75,190** mean, +$28,294 → **+$37,649** worst.

> Earlier drafts quoted "mean $89,008, min $67,406" for the holdout. That was a different, easier
> seed panel and is not comparable to anything else here; `--seed0 90001` is the panel of record.

### What the opponent's sell profile actually showed (`tools/sellprofile.py`, seed 11)

| Product | us | them |
| --- | --- | --- |
| STRAWBERRY | **0** | 268 @ $113 = **$30,387** |
| WOOL | 85 @ $244 = $20,696 | 107 @ $242 = $25,947 |
| WHEAT | 208 @ $44 | 318 @ $43 |
| FERTILIZER | 184 @ $53 | 194 @ $66 |
| MILK | 119 @ **$27** | 144 @ **$81** |
| MELON | 99 @ $117 | 18 @ $64 |

Two real defects came out of this and are now fixed: milk was being dumped in single lots that
crashed its own price mid-order (now chunked to the drain rate across three daily windows), and
capital was being sunk into seeds and empty pastures while zero animals were earning (animals are now
bought the moment any matching structure is vacant, seeds in batches of 3).

### v3 (2026-08-14, not yet submitted) — the seed-capital fix

`_market()` bought seeds toward `n - seeds_in_stock`, ignoring tiles already planted, so it parked
`n` seeds of capital in the shed permanently. Now `n - planted - seeds_in_stock`.

**60W-0L-0T over 60 games** vs the pre-fix version (`--seed0 90001`), mean +3,588, worst +595.
`BUY_SEED` emissions 82 → 60, `PASS` 3,780 → 3,518. Cheap and unambiguous; it does not change the
route, only stops it from idling capital. Still 0W-16L vs `v16_rc5` (mean −82,018, the best of all
12 sweep configs).

### Submitted

`55488191` — `submission.tar.gz`, "v2 drip selling; fix: agent must be last callable",
`SubmissionStatus.COMPLETE`, publicScore 600.0 (the starting rating; it moves as matches play).
Two earlier submissions errored on the entry-point bug, see `AGENTS.md` §4.

### The idle-labour finding — the clearest open lead

`python tests/test_invariants.py` prints a per-verb no-op table. Everything is clean except:

```
  PASS                        3780   3780 100.0%
```

3,780 PASS actions in one episode: **units sit idle ~58% of all unit-slots.** The replay winner runs
270–370 actions/day. Labour is nearly free ($54 for all 8 hands), so this is pure waste, and it has
the same root as the strawberry gap — 25 tiles in one quadrant cannot absorb 9 units of work. Land
expansion and idle labour are one problem, not two, which is why fixing either alone has always lost.

This is the number to drive down. It is measured directly from emitted actions, so it is not a
detection artifact (unlike the first draft of that suite, which reported false no-ops for
HARVEST/BUY_PRODUCT by checking market orders against pre-unit state).

### The sell-timing result (v2, the biggest single win since Hungarian matching)

`tools/sellhours.py` prints units sold per turn-of-day per player. Against `v16_rc5` it showed the
whole story: **they sell on all 24 turns, we dumped into 3 windows.** Market inventory persists
across turns — `_refresh_prices` only recomputes price *from* inventory, and the sole thing that
refills it is town consumption. So a day's quota sold in one order walks its own price down the
curve, while the same quota dripped across the day rides the refill. Splitting a quota *within* one
turn is worthless (price is requoted per unit from live inventory, so one order of 48 == 48 orders
of 1); only spreading across *turns* helps.

The price gate was worse than useless — it was actively causing the glut it existed to prevent:

```
ME   MILK              154         1.0  $     154      <- 154 units at the $1 floor
```

Below 0.6×base the gate `continue`d, so stock accumulated instead of selling, the shed passed
`SHED_CAP - 20`, and `panic` dumped the entire holding at the floor. Selling at the drain rate is
self-stabilising by construction (the town removes as much as we add), so the gate on top of it only
ever converted a good price into a floored one. Removing it outright is what the numbers above buy.

**Order-slot ordering is a real but separate lever.** Orders resolve slot-by-slot (`for i in
range(max_len)`), both players quoted the same pre-commit inventory *within* a slot. So slot 0 meets
an untouched market and slot 3 meets whatever slots 0–2 crashed. Buys and sells share the one
10-slot queue, so any BUY appended before a SELL costs that sell a slot. We already emit sells
first, sorted by descending base price. Do not reorder without re-measuring.

### Measured negative results — do not retry without new evidence

- **Scaling the herd loses money.** 8S/16C ⇒ $27k, 10S/20C ⇒ $120. Milk drain is only ~14/day and
  8 cows with CARE already produce ~12/day, so extra cows earn floor prices while still eating $50/day
  of wheat. Wool had headroom (11/day drain vs 5.3/day from 4 sheep), which is exactly why 6 sheep won.
- **Land expansion loses money** at every size tested ($1k–$7k spent for a strictly worse result).
  Extra tiles only pay if they grow something with drain headroom, and melon has a drain of *one per
  day*, so more melon tiles just deepen the glut.
- **Strawberry did not pay for us** despite being the opponent's biggest line ($30k). It needs ~40+
  tiles to reach their volume, which needs land, which we lose money on. It is the clearest remaining
  lead but only behind a routing/expansion rework, not as a drop-in.
- **More than 8 hired hands loses.** 9 hands ⇒ $51.8k, 10 ⇒ $55.6k, 8 ⇒ $58.0k on the same panel.
- **The goose/EGG build loses badly**, killing open hypotheses 1 and 3. EGG looked ideal — a log glut
  curve that holds ~$37 at 1,600 units, and *no public agent sells any*, so the whole sink is
  uncontested. Measured against `v16_rc5` on the holdout panel (baseline −$88,096):
  14 GOOSE ⇒ −$123,386, 6 SHEEP + 8 GOOSE ⇒ −$115,321, 10 GOOSE + 4 COW ⇒ −$105,078.
  An uncontested sink is worth nothing if the thing filling it is low-value per action: a goose is
  3 actions/day (FEED, CARE, HARVEST) plus a wheat for ~2 eggs ≈ $80, while the same pasture slot
  carries a sheep whose wool clears far more per action.
- **Strawberry still does not pay, now retested with FERTILIZE.** vs `v16_rc5`, baseline −$88,096:
  6 straw ⇒ −$90,944, 4 straw + 3 melon ⇒ −$90,037, 8 straw ⇒ −$127,794. Fertilizing improved every
  strawberry variant (−$93,952 ⇒ −$90,944 at 6 tiles) but not enough to pass melon. Four strawberry
  tiles produced 20 units against the replay winner's 274 — the constraint is tiles, not the crop.
  Strawberry stays blocked behind land, exactly as recorded above.

### Fertilizer is a crop input, not just a product (found 2026-08-14, in `main.py`, unused in the shipped plan)

```python
fertilized = was_watered and tile.get("fertilized_until_day", -1) >= current_day
tile["yield_units"] = min(cd["max_yield"], tile["yield_units"] + (2 if fertilized else 1))
```

`FERTILIZE` costs 1 FERTILIZER from the acting unit's inventory and sets `fertilized_until_day =
day + 2`, i.e. 3 days of cover. On a watered production day the tile yields **2 units instead of 1**.
One fertilizer sells for ~$50; spent on a strawberry tile it buys ~$200 of fruit. That is very
likely why the replay winner sold only 192 fertilizer while we sold 288.

Two traps: the doubling lives inside `if not cd["ongoing"]: continue`, so it does **nothing** for
WHEAT, CARROT or MELON — only TOMATO and STRAWBERRY. And `production_count > cd["max_yield"]` ends
the plant, so a strawberry gets exactly 4 production events (days 10, 12, 14, 16 after planting)
whatever you do; fertilizer changes their size, not their number.

`main.py` emits FERTILIZE tasks (priority 3, requires the unit carry FERTILIZER). With the shipped
MELON/WHEAT plan no tile is `ongoing`, so it never fires — it is there for whenever land unlocks
strawberry. Verified inert: vs `pass` the holdout result is byte-identical before and after.

## 5b. Upstream evidence (web search, 2026-08-14) — the town is UNDER-supplied

Searched GitHub/web with Codex luna xhigh. Public competitor code is essentially nonexistent: the
only competitor repo is [`deepeshumrao/kaggriculture-agent`](https://github.com/deepeshumrao/kaggriculture-agent)
(1 star, wheat-only rule-based agent, its `MECHANICS_CALIBRATION.md` labels the economy constants as
*assumptions*) — nothing to learn from. No replay dumps, no leaderboard scrapers, no economy
writeups. The value is all upstream, in `Kaggle/kaggle-environments`:

- **[PR #1394 "Kaggriculture town rebalance"](https://github.com/Kaggle/kaggle-environments/pull/1394),
  merged 2026-08-07 — the single most actionable public fact found.** The PR's own justification is
  an analysis of **62 top-leaderboard episodes**: town demand exceeded farm supply by ~**930 units**,
  a **0.71 coverage ratio**, and players out-supplied the town on only **6 of 30 days**.
  So at the *top of the leaderboard* the market is not the constraint — **production is**. Glut is a
  self-inflicted wound from concentrating on one product (our 99 melons against a drain of 4/day),
  not a ceiling on total volume. This is the strongest argument for expansion we have.
  The PR also flattened town-center demand (no more ramp) and set its interval to 24 turns.
- Balance history worth not re-deriving: [#1199](https://github.com/Kaggle/kaggle-environments/commit/8452d21e61874b1c2390a96cc9f972da1)
  quadrupled the glut-crash slope for STRAWBERRY/MELON/MILK/WOOL (why premium oversupply is punished
  so hard); [#1135](https://github.com/Kaggle/kaggle-environments/commit/1aaf9aa4db0ef3c43732bc5e7d2a734a630f95d2)
  limited market *buys* to WHEAT and FERTILIZER and killed round-trip arbitrage (buys quote post-buy
  inventory, sells quote pre-sell); [#1386](https://github.com/Kaggle/kaggle-environments/commit/5cef41db5085eff6061ec3801a4a1ce9183485e8)
  made buys partial-fill against shed capacity; [#1381/#1392] made LOCKED tiles traversable and shed
  actions legal from locked shed-access tiles.
- **Our installed `kaggle-environments 1.32.6` already contains #1394** (verified in the source:
  `townCenterSellInterval` 24, `townShopSellInterval` 4, shops drawn with replacement,
  `MAX_SHOP_INSTANCES = 8`). Every number in §3–§4 is therefore on the current balance.
- Upstream ships `tests/envs/kaggriculture/test_kaggriculture.py` (price at baseline/glut/scarcity/
  floor, shed capacity, duplicate shops, flat daily demand) — a ready-made oracle if our model of the
  economy ever needs re-verifying.
- Anecdote only, from the [designer's Reddit thread](https://www.reddit.com/r/reinforcementlearning/comments/1vgvuti/kaggriculture_farming_markets_rl_50k_prizes/):
  "melon rush" named as an early meta and "Headstart" as a strong strategy, unexplained. Hypotheses,
  not facts.

### Drain-rate revenue ceilings, computed against the real `market_price`

Selling exactly at the town drain rate for 20 days, price ends **unchanged**:

| Product | drain/day | 20-day volume | revenue | end price | we currently sell |
| --- | ---: | ---: | ---: | ---: | --- |
| WOOL | 13 | 260 | **$51,240** | $200 | 85 ($20,696) |
| STRAWBERRY | 25 | 500 | **$48,480** | $120 | **0** |
| MELON | 1 | 20 | $5,000 | $250 | 99 ($11,617, self-glutted) |

Strawberry headroom alone is larger than the entire margin gap to `v16_rc5`.

## 5c. The measured gap, and the panel bias that hid part of it (2026-08-14)

Every public agent beats the shipped build by 75–85k, not by a little:

| opponent | v3 margin, 8 seeds × 2 seats, seed0 90001 |
| --- | --- |
| `bench/v16_rc5…` (the meta trace) | −83,638 |
| `bench/kaggriculture_breaking_the_tie.py` | −77,624 |

`docs/NOTE_META_PLAN.md` decodes what the meta trace actually does, and one row explains the rest:
it issues **250–340 work actions/day against our ~99**. It converts 93% of its unit-slots into work;
we convert 46%. Our PASS 3518 is not units walking, it is units with **nothing assigned** — 9 units
against 25 tiles. It runs 75 owned tiles (3 quadrants, bought day 6 and day 10), ~60 crop tiles
(12 MELON, 13 WHEAT, **35 STRAWBERRY**), only 12 animals, 5–14 hands/day, and spends fertilizer on
strawberry instead of selling it.

**Structural cap found:** `_market()` emits `[["HIRE"]] * min(HIRES, 10)` and the market takes 10
order slots per turn, so **more than 10 hands is currently impossible**; the meta peaks at 14.

**Panel bias — read this before trusting any crop-mix result.** `tools/sweep.py` evals against
`bench/v3.py`, a copy of our own build. In a two-player market, when a variant stops selling a
product the mirror opponent inherits that niche alone, so deviations are punished twice. Strawberry
is the case where the two panels disagree:

| build | vs mirror (`bench/v3.py`) | vs meta (`v16_rc5`) |
| --- | --- | --- |
| shipped `[(MELON,6),(WHEAT,5)]` | — | −83,638 |
| `[(STRAWBERRY,6),(WHEAT,5)]` | −7,032 | −80,500 |
| `[(STRAWBERRY,7),(WHEAT,4)]` | −9,201 | **−78,439** |

The berry swap also gains +4,083 against `breaking_the_tie`, so the meta column is corroborated by a
second real opponent. Expansion, re-checked the same way, does **not** flip (M12c −87,486, X3c
−85,736, XW20 −83,877 vs meta, all worse than shipped). Always report both columns; the meta column
is the primary signal.

## 6. Open hypotheses to test with `tools/eval.py`

0. **SOLVED (diagnosis) — why every expansion on record lost money: opening capital allocation.**
   The land+strawberry sweep (`docs/SWEEP_LAND_STRAWBERRY.md`, all 12 configs 0W-16L) mattered for its
   diagnostic, not its headline. Config C (2 quadrants + 20 STRAWBERRY) earned $11,618 of berries and
   destroyed $56k of animal revenue: milk $26,382 → **$106** (72 units at ~$1.47, the $1 floor).
   Instrumented both candidate causes (probes in the scratchpad, `shedprobe.py` / `buildprobe.py`):

   - **Panic dump: ruled out.** End-of-day shed occupancy peaks at 68/100 baseline, 56/100 in config
     C; `panic` (shed > 80) fires on **0 of 30 days in both**. Not a floor dump.
   - **Capital allocation: confirmed.** First-action probe, seed 90001:

     | | first `BUY_ANIMAL` | money, days 0–9 | `BUY_LAND` | `BUY_SEED` |
     | --- | --- | --- | --- | --- |
     | baseline | **day 0** | 116–862 | never | 30 |
     | config C | **day 10** | 124–366 | day 0 | 41 |

     `_market()` gates `BUY_ANIMAL` on `ANIMALS[next]["structure"] in vacant`, but the pasture is
     built by a *unit action later the same day*, so at purchase time the gate is shut, the branch is
     skipped, and the `BUY_SEED`/`BUY_LAND` branches below it eat the whole $3,000 opening bank.
     20 STRAWBERRY tiles at $100/seed plus $1,000 of land ⇒ the herd arrives 10 days late and earns
     nothing all season. **The cows didn't get dumped, they barely existed.** More tiles = more seed
     spend = the engine starves. That is the shape of every expansion loss in §5.

   **The fix is an expansion fix and must never be shipped alone** (both measured vs `A.py`,
   `--games 8 --seed0 90001`):

   | change | result |
   | --- | --- |
   | current `main.py` (seed fix only) | 16W-0L, +3,588 |
   | \+ capital reserve for the next animal | 12W-4L, +1,130 |
   | \+ plant capped at seeds on hand | 0W-16L, −2,203 |

   At 25 tiles the engine isn't starved, so reserving money only delays seeds; and capping PLANT at
   seeds on hand throttles the 3-per-turn seed drip (units otherwise walk to the tile and plant as
   seeds land). The two interact: the reserve alone makes PLANT no-op 126 of 222 times, which is
   exactly what the cap fixes. Both now live in `main.py` behind `ANIMAL_RESERVE = 0` and
   `PLANT_CAP = False` (shipped defaults = off), so `tools/sweep.py` can flip them.

   **ANSWERED 2026-08-14, and the answer is no — see `docs/SWEEP_CAPITAL.md`.** The reserve does fix
   the diagnosed defect: at 2 quadrants the first `BUY_ANIMAL` goes back from day 10 to **day 0** and
   the loss shrinks from −34,179 to −13,854. Expansion still loses **every** game at every crop size,
   and the loss is monotone in tiles added (20 berries −13.9k, 12 −9.5k, 6 −6.9k, melon-only −2.0k,
   none = shipped). The sell profile says why: berries earn $11.0k while milk and fertilizer lose
   $17.2k. The second quadrant adds **distance, not capacity** — the 58% PASS rate is not idle labour
   waiting for work, it converts straight into travel steps. More hands makes it worse (−23.3k at 10),
   and `HIRES > 10` is a no-op anyway (`min(HIRES, 10)` against the 10 order slots).
   **Land expansion is closed until a routing/locality change exists.** Capital and hand count are
   both ruled out.

   Still unexamined and cheap: `DRAIN["FERTILIZER"] = 6`/day against 14 animals producing 14/day,
   where §3 says fertilizer's real town drain is **zero**. And priority inversion (`WATER` prio 1 at
   −700 outranks animal `HARVEST` prio 2 at −500) is untested, though now a much weaker suspect.

1. **Goose-heavy build.** 15–20 geese ≈ 30–40 eggs/day at ~$40 = $1.2–1.6k/day, against an egg curve
   that does not crash. Beats milk/wool, which are floored after ~50 units.
2. ~~**Drain-rate selling.**~~ **Done in v2 — confirmed, 16W-0L over the previous version.**
3. **Fertilizer maximization.** Animals purely as fertilizer engines; is 20 cheap geese better than
   8 cows + 4 sheep for the same tile count?
4. **Front-run everyone.** Orders resolve one unit at a time, both players quoted the same pre-sell
   inventory, so selling on turn *t* instead of *t+1* beats an opponent selling at *t+1*. The public
   agents already do this on MELON/MILK/STRAWBERRY/WOOL, and one of them counters the counter.
