# Animal and fertilizer economics

All source citations below refer to:

`C:/Users/livde/AppData/Roaming/Python/Python314/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`

The measured inputs are the supplied seed-90001 totals: WOOL `200/$15,365`, MILK
`165/$24,076`, FERTILIZER `303/$15,853`, MELON `48/$11,750`, WHEAT `187/$9,769`.

## Q1: GOOSE / EGG

### Source facts

| item | value | source |
|---|---:|---|
| GOOSE purchase | `$300` | `ANIMALS["GOOSE"]["cost"]`, env:20 |
| COW purchase | `$400` | `ANIMALS["COW"]["cost"]`, env:21 |
| SHEEP purchase | `$500` | `ANIMALS["SHEEP"]["cost"]`, env:22 |
| GOOSE structure | `COOP` | env:20 |
| COW/SHEEP structure | `PASTURE` | env:21-22 |
| monetary structure cost | `$0` | `BUILD_COOP` and `BUILD_PASTURE` only assign a tile; no money is debited, env:480-489 |
| action cost to build | `1 BUILD_* action` | one farmer/hand action is applied per turn, env:900-926 |
| structure/animal occupancy | `1 tile/animal` | placement requires one matching unoccupied structure tile, env:368-378 |
| feed | `1 WHEAT/animal/day` | `FEED` takes exactly one WHEAT, env:492-500 |
| GOOSE production | `1 event/day`, first event day `4` | env:20 |
| COW production | `1 event/2 days`, first event day `8` | env:21 |
| SHEEP production | `1 event/3 days`, first event day `6` | env:22 |

With daily FEED and no CARE, the steady rates are:

| animal | no CARE | with CARE | derivation |
|---|---:|---:|---|
| GOOSE | `1.000/day` | `2.000/day` | base `1`; interval `1`; one banked CARE bonus is paid on the next event |
| COW | `0.500/day` | `1.000/day` | `1/2`; CARE gives `2 units/event` |
| SHEEP | `0.333/day` | `1.000/day` | `1/3`; CARE gives `3 units/event` |

The CARE derivation is the source behavior: a fed-and-cared day banks `+1`, and the
whole bank is consumed on the next fed production day, env:812-817. The table assumes
HARVEST keeps `yield_units` below `max_held`; the caps are `4` for GOOSE and `6` for
COW/SHEEP, env:20-22.

### Wheat tiles

WHEAT starts with `1` unit, can add one unit on each watered age `2`, `3`, and `4`,
and is removed by HARVEST, env:12, 202-212, 426-430, 451-455. Therefore, without
fertilizer, one perfectly staggered tile supplies `4 units / 5 days = 0.8 WHEAT/day`.

Required feed tiles for `N` animals:

`wheat_tiles = ceil(N / 0.8) = ceil(1.25N)`

| build | structure tiles | wheat tiles for full self-feed | total tiles |
|---|---:|---:|---:|
| `N` GOOSE | `N` | `ceil(1.25N)` | `N + ceil(1.25N)` |
| `8 COW + 6 SHEEP` | `14` | `ceil(14/0.8) = 18` | `32` |

Thus the current `8 COW + 6 SHEEP` cannot be fully self-fed inside the 25-tile
quadrant. Its `14` structures leave `11` crop tiles; the shipped constants are
`ANIMAL_PLAN` with `14` animals and `CROP_PLAN` with `6 MELON + 5 WHEAT`,
`main.py:50-51`. Five WHEAT tiles supply `4/day` at steady state, so the remaining
`10/day` of the herd's `14/day` feed demand must be bought or supplied from stock.

For GOOSE, the 25-tile maximum is `N=11`:

| N | structure tiles | wheat tiles | total |
|---:|---:|---:|---:|
| `8` | `8` | `10` | `18` |
| `9` | `9` | `12` | `21` |
| `10` | `10` | `13` | `23` |
| `11` | `11` | `14` | `25` |
| `12` | `12` | `15` | `27` |

### EGG price and daily revenue

The market starts at inventory `I0=10,000`, env:38, 165-169. EGG has

`base=50, T=332, above_func=log, above_target=0.20`,

env:47. The exact above-market price is therefore

`p(x) = max(1, round(50 - (10 / ln(333)) * ln(1+x)))`,

where `x = inventory - 10,000`, from env:179-193. Useful points are:

| EGG excess inventory x | `0` | `50` | `100` | `200` | `300` | `1,600` |
|---:|---:|---:|---:|---:|---:|---:|
| price | `$50` | `$43` | `$42` | `$41` | `$40` | `$37` |

EGG town drain is expected `13/day`: EGG appears in `2` of the `8` shop names,
env:90-99 and 103-105; each shop consumes once per `4` turns, so each instance
drains `24/4=6/day`, env:720-730; the town center adds `1/day` because EGG is in
`TOWN_CENTER_PRODUCTS`, env:25 and 101, 732-734. Shop draws are with replacement,
so `13/day` is the eight-shop expectation, not a fixed seed-level value, env:873-878.

Let `R=N` without CARE and `R=2N` with CARE. The net EGG inventory change is

`delta = R - 13` units/day.

Consequences:

| GOOSE count | CARE output | `delta` | conservative daily revenue before glut |
|---:|---:|---:|---:|
| `1-6` | `2-12/day` | `-11` to `-1` | `$100N/day` |
| `7` | `14/day` | `+1` | starts at `$700/day`, then decays |
| `8` | `16/day` | `+3` | starts at `$800/day`, then decays |
| `9` | `18/day` | `+5` | starts at `$900/day`, then decays |
| `10` | `20/day` | `+7` | starts at `$1,000/day`, then decays |
| `11` | `22/day` | `+9` | starts at `$1,100/day`, then decays |

For a concrete 30-day decay calculation, I assumed a fresh market (`x=0`), all `R`
units sold at the start of each day, `13` units drained at day end, and steady
production from day 1. Thus `Rev30 = sum_d sum_j p(x_d+j)` for `d=0..29`,
`j=0..R-1`, with `x_(d+1)=x_d+R-13` until the `$1` no-supply rule applies. Applying
the source's integer rounding gives:

| CARE GOOSE count | output/day | end excess after 30 days | 30-day average EGG revenue/day |
|---:|---:|---:|---:|
| `6` | `12` | `0 or below` | `$600` base-price benchmark |
| `7` | `14` | `30` | `$628.60` |
| `8` | `16` | `90` | `$695.97` |
| `9` | `18` | `150` | `$770.20` |
| `10` | `20` | `210` | `$845.57` |
| `11` | `22` | `270` | `$921.80` |

For `R>13`, the above-I0 inventory grows and the EGG quote decays; EGG's logarithm
makes that decay slow. At the `$1` floor, source sales stop adding inventory while
the town still drains EGG, so the floor is not a permanent monotone state. The table
is a 30-day steady-production calculation, not an eval and not an opening-day
calculation.

For comparison, the current herd's source-base gross revenue is:

| build | output/day with CARE | source price | gross/day |
|---|---:|---:|---:|
| `8 COW` | `8 MILK` | `$160`, env:48 | `$1,280` |
| `6 SHEEP` | `6 WOOL` | `$200`, env:49 | `$1,200` |
| total |  |  | **`$2,480/day`** |

Without CARE, the same calculation is `4 MILK/day * $160 + 2 WOOL/day * $200 =
$1,040/day`. The supplied run actually realized

`($24,076 + $15,365) / 30 = $1,314.70/day`,

with measured means `$145.92/MILK` and `$76.83/WOOL`. Even the 25-tile maximum of
`11 CARE GOOSE` is only about `$921.80/day` under the explicit 30-day decay model,
before WHEAT cost. GOOSE is not the next economics run.

## Q2: FERTILIZER

### Town drain and price behavior

The META claim is **verified**. `SHOPS` contains no FERTILIZER, env:90-99, and
`TOWN_CENTER_PRODUCTS` explicitly excludes it, env:101. `_town_consume` subtracts
only shop products and center products, env:723-736. Therefore:

`FERTILIZER town drain = 0/day`.

FERTILIZER's source market constants are `base=100`, `I0=10,000`, `T=200`, linear
above curve, target `0.40`, env:38, 50. Thus above I0:

`p(x) = max(1, round(100 - 0.2x))`.

From a fresh market, selling `303` units gives

`sum(round(100 - 0.2j), j=0..302) = $21,150`,

mean `$69.80`; the last fresh-market quote is about `$40`. The measured
`$15,853 / 303 = $52.32` is consistent with roughly `87` pre-existing excess
fertilizer units before the measured lot. Exact inversion is impossible from the
total because both players share the market and orders commit in lockstep,
env:531-535 and 599-615.

The price reaches the `$1` floor at approximately `x=493` excess units under the
source rounding, and a `$1` sale does **not** add inventory, env:179-193 and 639-648.
That is why the price does not collapse below `$1`; it pins at `$1`. It does not
make a positive non-floor sale rate sustainable:

| target | sustainable sell rate with zero town drain |
|---|---:|
| any non-floor price forever | `0/day` |
| keep price at least `$52` for a fresh 30-day episode | about `243/30 = 8.1/day` |
| current measured rate | `303/30 = 10.1/day` |
| floor-price liquidation | any rate, but only `$1/unit` and no inventory increase |

Every surviving animal makes one fertilizer available at end of day, regardless of
feed or CARE, env:816-819. `COLLECT_FERTILIZER` clears the boolean and adds exactly
one unit, env:502-508; it does not accumulate. Fourteen surviving animals therefore
create `14 fertilizer/day` in steady state, against a `0/day` town sink.

### FERTILIZE instead of selling

The only ongoing crops are TOMATO and STRAWBERRY, env:14-15. FERTILIZE consumes one
fertilizer and is active for the current day plus the next two days, env:462-469.
On a watered ongoing production event, the source adds `2` units instead of `1`,
env:779-787.

The supplied fertilizer sale mean is `$15,853/303 = $52.32`. No realized TOMATO or
STRAWBERRY price was supplied, so the calculation below assumes the source base
prices `$60` and `$120`, env:44-45, with enough drain-rate selling to avoid a glut.
The break-even prices are also shown.

| crop | event interval | extra events from one 3-day FERTILIZE window | extra units | source/base value per fertilizer | break-even crop price |
|---|---:|---:|---:|---:|---:|
| TOMATO | `1 day`, env:14 | `3` | `+3` | `3*$60 = $180` | `$52.32/3 = $17.44` |
| STRAWBERRY | `2 days`, env:15 | `2` | `+2` | `2*$120 = $240` | `$52.32/2 = $26.16` |

Both are marginally better than selling one fertilizer. STRAWBERRY is better:
`$240 - $52.32 = $187.68` incremental value per fertilizer versus
`$180 - $52.32 = $127.68` for TOMATO. Its expected town drain is also higher,
`4*6+1=25/day`, than TOMATO's `2*6+1=13/day`, from the shop table and center rules
above.

To replace the entire measured `$15,853` fertilizer sale using one fertilizer
window per tile:

| crop | tile-windows required |
|---|---:|
| STRAWBERRY | `ceil(15,853/$240) = 67` |
| TOMATO | `ceil(15,853/$180) = 89` |

One STRAWBERRY tile-window already beats selling its one fertilizer:
`2*$120 = $240 > $52.32`. Twenty-five such windows use `25` fertilizer and create
`50` extra STRAWBERRIES worth `$6,000`, versus `$1,308` if those `25` fertilizer
units were sold. The full measured-sale replacement needs `67` tile-windows; it is
not a 25-tile one-wave result. A four-event STRAWBERRY plant can use two such
windows over its life, because its events are two days apart and capped at four,
env:15.

## Ranked recommendation

1. **Run the STRAWBERRY fertilizer test next.** Keep
   `ANIMAL_PLAN = ["SHEEP"] * 6 + ["COW"] * 8`; change only
   `CROP_PLAN` to `[('STRAWBERRY', 6), ('WHEAT', 5)]`. This keeps `14+6+5=25`
   tiles, preserves five WHEAT tiles, and makes each timed STRAWBERRY fertilizer
   window worth about `$240` versus `$52.32` sold.
2. **Do not run the GOOSE build next.** The 25-tile self-fed candidate is
   `ANIMAL_PLAN = ["GOOSE"] * 11`, `CROP_PLAN = [('WHEAT', 14)]`; its modeled
   30-day CARE revenue is about `$921.80/day`, below the current measured animal
   revenue `$1,314.70/day`.
3. **Do not treat FERTILIZER sale as sustainable.** With no town drain, the
   non-floor sustainable rate is `0/day`; use it on ongoing STRAWBERRY first and
   sell only the remainder.
