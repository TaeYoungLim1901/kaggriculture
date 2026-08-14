# Kaggriculture research ladder

Research-only audit completed 2026-08-14. Inline citations use the requested `file:line` or `notebook cell` form. Calculated values state the input file and formula beside the result.

## Acquisition

The installed Kaggle CLI is 2.2.4 and its `kernels pull` parser takes the kernel ref positionally, not with `-k`; the literal `-k` form failed eight times with `A kernel must be specified`. Retrying with the equivalent `kaggle kernels pull <ref> -p <dir> -m` succeeded for all eight refs. The two Raykkretzschmar kernels share Kaggle's output filename, so both were preserved under distinct filenames in `research/notebooks/raykkretzschmar/`.

Pulled and flattened:

- `raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta` → `research/notebooks/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta.{ipynb,py}`
- `cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta` → `research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.{ipynb,py}`
- `busyaprime/what-actually-wins-on-the-kaggriculture-ladder` → `research/notebooks/busyaprime/what-actually-wins-on-the-kaggriculture-ladder.{ipynb,py}`
- `kaitofukami/25-27-strict-future-v27-midgame-meta-reset` → `research/notebooks/kaitofukami/25-27-strict-future-v27-midgame-meta-reset.{ipynb,py}`
- `tetsutani/adaptive-farming-strategy-for-kaggriculture` → `research/notebooks/tetsutani/adaptive-farming-strategy-for-kaggriculture.{ipynb,py}`
- `flexonafft/kaggriculture-adaptive-replay-agent` → `research/notebooks/flexonafft/kaggriculture-adaptive-replay-agent.{ipynb,py}`
- `raykkretzschmar/kaggriculture-rank-your-agent` → `research/notebooks/raykkretzschmar/kaggriculture-rank-your-agent.{ipynb,py}`
- `ocean240812/kaggriculture-strategy-guide` → `research/notebooks/ocean240812/kaggriculture-strategy-guide.{ipynb,py}`

## 1. What the official episode data gives us

### Refs, layout, and size

`kaggriculture-episodes-index` is the manifest-only index used by the live-meta notebook; the daily replay datasets are named `kaggle/kaggriculture-episodes-YYYY-MM-DD` and are mounted at `/kaggle/input/datasets/organizations/kaggle/kaggriculture-episodes-YYYY-MM-DD`. The notebook looks for `manifest.csv` plus either `<episode_id>.json` or `<episode_id>_summary.json` in that directory (`research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cells 0, 16). The raw `<episode_id>.json` layout is the one that gives the complete `steps` stream needed for state-aware replay mining; the notebook also handles a compact top-level `actions` layout (`research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cell 19; `research/notebooks/busyaprime/what-actually-wins-on-the-kaggriculture-ladder.ipynb`, cell 2).

The local index has 15 daily refs. `total_bytes` is the compressed dump size recorded by the index; GiB is calculated as `total_bytes / 2^30`. No daily dump was downloaded.

| date | dataset ref | episodes | bytes | GiB |
|---|---|---:|---:|---:|
| 2026-07-30 | `kaggle/kaggriculture-episodes-2026-07-30` | 864 | 13,639,221,377 | 12.70 |
| 2026-07-31 | `kaggle/kaggriculture-episodes-2026-07-31` | 928 | 21,452,054,005 | 19.98 |
| 2026-08-01 | `kaggle/kaggriculture-episodes-2026-08-01` | 829 | 21,450,823,404 | 19.98 |
| 2026-08-02 | `kaggle/kaggriculture-episodes-2026-08-02` | 793 | 21,471,097,913 | 20.00 |
| 2026-08-03 | `kaggle/kaggriculture-episodes-2026-08-03` | 787 | 21,469,441,381 | 19.99 |
| 2026-08-04 | `kaggle/kaggriculture-episodes-2026-08-04` | 755 | 21,469,460,776 | 19.99 |
| 2026-08-05 | `kaggle/kaggriculture-episodes-2026-08-05` | 743 | 21,456,733,131 | 19.98 |
| 2026-08-06 | `kaggle/kaggriculture-episodes-2026-08-06` | 683 | 21,455,506,191 | 19.98 |
| 2026-08-07 | `kaggle/kaggriculture-episodes-2026-08-07` | 675 | 21,445,647,958 | 19.97 |
| 2026-08-08 | `kaggle/kaggriculture-episodes-2026-08-08` | 675 | 21,452,045,805 | 19.98 |
| 2026-08-09 | `kaggle/kaggriculture-episodes-2026-08-09` | 687 | 21,451,856,799 | 19.98 |
| 2026-08-10 | `kaggle/kaggriculture-episodes-2026-08-10` | 685 | 21,466,382,494 | 19.99 |
| 2026-08-11 | `kaggle/kaggriculture-episodes-2026-08-11` | 682 | 21,457,049,311 | 19.98 |
| 2026-08-12 | `kaggle/kaggriculture-episodes-2026-08-12` | 684 | 21,466,985,686 | 19.99 |
| 2026-08-13 | `kaggle/kaggriculture-episodes-2026-08-13` | 687 | 21,454,228,762 | 19.98 |

Source for every row and every size: `research/datasets/kaggriculture-episodes-index/manifest.csv:1-16`. The live notebook describes the index as ranked by average agent rating and capped at 20 GiB/day (`research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cell 0).

### Episode JSON schema and action mining

An existing raw replay in the repo has these top-level keys: `configuration`, `description`, `id`, `info`, `module_version`, `name`, `rewards`, `schema_version`, `specification`, `statuses`, `steps`, `title`, and `version`; `info` contains `Agents`, `EpisodeId`, `TeamNames`, and `seed`; it has 720 steps. Each step has two seat frames with `observation`, `action`, `info`, `reward`, and `status`. An observation contains `day`, `hour`, `player`, `step`, `farms`, `private`, `market`, `town`, and `remainingOverageTime`; the action contains `farmer`, `hands`, and `market`. This is a read-only schema probe of `research/replays/episode-91249452-replay.json:1`, corroborated by the repo readers at `tools/replay.py:74-116` and `research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cell 19.

Therefore the answer is yes: winning action sequences can be mined directly without reconstructing policy. For a raw episode, choose the seat with the larger `rewards` value, then read `steps[t][seat]["action"]` for `t=0..719`; `tools/replay.py:74-99` defines the winner/reward read, `tools/replay.py:106-116` reads per-step actions, and `research/notebooks/busyaprime/what-actually-wins-on-the-kaggriculture-ladder.ipynb`, cell 2, explicitly parses `steps[i][seat].action` for 720 turns. The action stream includes farmer, hired-hand, and market orders, so it preserves the exact sequence rather than only final composition. The manifest's `avg_score` is a game-level mean ladder rating, not the seat winner; the winner still comes from `rewards` (`research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cells 15-19).

The practical workflow is: use the daily manifest to select high-`avg_score` episodes, open only the corresponding raw JSONs, select the winning seat by `rewards`, and export its `action` sequence. This is precisely the selection path implemented in `research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cells 16 and 19. It is high-value data, but a replay is one realized trajectory, not a portable policy; Raykkretzschmar explicitly warns that a repeated field schedule must be checked across opponents and that market behavior may be reactive (`research/notebooks/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta.ipynb`, cells 0 and 8).

## 2. What the ten reference agents do differently

### Ranking

The baseline league plays every ordered pair for six games and yields this decisive ranking; the W-L totals below are summed from `research/datasets/kaggriculture-reference-agents/baseline_league.csv`.

| rank | reference | baseline W-L | expected bank |
|---:|---|---:|---:|
| 1 | Closer Cleo | 54-0 | 186,198 |
| 2 | Slotter Silas | 47-7 | 185,853 |
| 3 | Ledger Lena | 43-11 | 186,991 |
| 4 | Broker Bea | 36-18 | 186,766 |
| 5 | Rancher Rita | 30-24 | 53,000 |
| 6 | Melon Mateo | 24-30 | 44,000 |
| 7 | Homestead Hana | 18-36 | 16,700 |
| 8 | Rotation Rosa | 12-42 | 12,300 |
| 9 | Wheat Walter | 6-48 | 7,200 |
| 10 | Fallow Finn | 0-54 | 3,000 |

The pairwise rows are `research/datasets/kaggriculture-reference-agents/baseline_league.csv:2-46`; the expected-bank and design fields are `research/datasets/kaggriculture-reference-agents/agents_manifest.csv:2-11`. The independent head-to-head file confirms the endpoints: Closer Cleo beats Fallow Finn in all six seeds/seats shown at `research/datasets/kaggriculture-reference-agents/head_to_head_games.csv:50-55`.

### Top-versus-bottom diff

Fallow Finn is a useful control, not a weak version of Cleo. Its policy is empty, it never plants, never buys, never hires, never moves, and returns PASS/no market orders for the season (`research/datasets/kaggriculture-reference-agents/fallow_finn.py:3-14`, `research/datasets/kaggriculture-reference-agents/fallow_finn.py:24-27`, `research/datasets/kaggriculture-reference-agents/fallow_finn.py:568-579`). Its day-29 trajectory remains $3,000 with one quadrant and no crop, pasture, or live animal; this is the `fallow_finn` slice of `research/datasets/kaggriculture-reference-agents/season_timeline.csv:1-541`.

Closer Cleo is the opposite shape:

| mechanism | Fallow Finn | Closer Cleo |
|---|---|---|
| crop/animal mix | none | The supplied manifest describes the shared meta field plan as 8 COW, 5 SHEEP, 6 STRAWBERRY tiles across three quadrants with a full crew (`research/datasets/kaggriculture-reference-agents/agents_manifest.csv:11`). The embedded action trace buys 8 COW and 6 SHEEP; that one-animal difference is worth preserving as an observed trace-vs-summary discrepancy, not silently “correcting” (`research/datasets/kaggriculture-reference-agents/closer_cleo.py:46-48`). |
| hiring curve | 0 every day | Decoding the embedded 720-action `_TRACE` gives HIRE counts by day: `5,3,3,4,6,5,4,6,8,9,9,10,10,10,11,9,10,12,12,11,11,13,15,13,12,12,14,13,13,11`. It ramps labor with workload rather than staying at zero (`research/datasets/kaggriculture-reference-agents/closer_cleo.py:18-29`, `research/datasets/kaggriculture-reference-agents/closer_cleo.py:46-48`). |
| market timing | no market | Sells are planned against live inventory and shed stock, premium orders can be moved one turn ahead of a near-clone dump, and sell quantities are ranked by self-induced price impact (`research/datasets/kaggriculture-reference-agents/closer_cleo.py:114-157`, `research/datasets/kaggriculture-reference-agents/closer_cleo.py:476-502`, `research/datasets/kaggriculture-reference-agents/closer_cleo.py:540-569`). |
| queue/capital safety | no buys | Cleo keeps the tape's SELL slots in place instead of hoisting sells over BUY/HIRE slots; the file explains that sells fund later wheat buys and that bad reordering can starve animals (`research/datasets/kaggriculture-reference-agents/closer_cleo.py:8-16`, `research/datasets/kaggriculture-reference-agents/closer_cleo.py:616-634`). |
| movement/routing | no movement | The field route is a replay-derived shared meta schedule, while the terminal controller assigns each actor to the nearest shed or available productive tile and uses Manhattan movement (`research/datasets/kaggriculture-reference-agents/closer_cleo.py:18-29`, `research/datasets/kaggriculture-reference-agents/closer_cleo.py:182-199`, `research/datasets/kaggriculture-reference-agents/closer_cleo.py:202-263`). |

The trajectory ledger shows what adding an authored economy buys before the public meta line: averaged across its three seeds, Rancher Rita reaches day 29 with about $52,645, three quadrants, 16 pasture tiles, and 15.3 live animals, while Finn stays at $3,000; this is a derived average over `research/datasets/kaggriculture-reference-agents/season_timeline.csv:2-541`, with the field definitions at `research/datasets/kaggriculture-reference-agents/season_timeline.csv:1`.

The ten files are deliberately a controlled ladder. Tiers 0-5 share an identical scheduler and vary economic policy; tiers 6-9 share the same meta production plan and vary only market behavior (`research/notebooks/raykkretzschmar/kaggriculture-rank-your-agent.ipynb`, cell 5). That design makes the main causal split unusually clear: production capacity gets an agent from the authored band into the meta band, then market order/timing separates the meta agents (`research/datasets/kaggriculture-reference-agents/agents_manifest.csv:8-11`; `research/datasets/kaggriculture-reference-agents/closer_cleo.py:26-29`).

## 3. Crop economics and price curves

### Per-tile economics

The supplied crop table gives units/cycle, cycle length, base price, gross/day, and seed cost (`research/datasets/kaggriculture-reference-agents/crop_economics.csv:1-6`). The notebook's explicit definition is `profit per tile-day = (units × base price − seed cost) / tile-days occupied` (`research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cell 5). Applying that formula gives the following net-after-seed figures. They exclude labor, land, feed, water, shed overflow, and opponent effects.

| crop | units/cycle | cycle days | base | gross/tile-day in CSV | net after seed/tile-day |
|---|---:|---:|---:|---:|---:|
| WHEAT | 4 | 5 | 25 | 20.00 | 18.00 |
| CARROT | 3 | 4 | 35 | 26.25 (CSV rounds 26.2) | 21.25 |
| TOMATO | 4 | 12 | 60 | 20.00 | 15.83 |
| STRAWBERRY | 4 | 17 | 120 | 28.24 (CSV rounds 28.2) | 22.35 |
| MELON | 6 | 13 | 250 | 115.38 (CSV rounds 115.4) | 109.23 |

The ranking is not “melon always wins”: melon has the highest isolated tile economics, but strawberry is an ongoing crop with town demand and melon has a steep glut curve. That exact qualification appears in the live-meta notebook (`research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cells 5 and 20) and is reflected in the price table below.

For context, the same table lists animal output at `research/datasets/kaggriculture-reference-agents/crop_economics.csv:7-9`: GOOSE $100 gross/tile-day, COW $240, SHEEP $266.7, each marked `needs_daily_wheat=True`. Those are product gross values, not crop profit, and should not be compared to the crop net column without subtracting feed and animal-care logistics.

### Price versus cumulative sold volume

`price_curves.csv` reports the price after cumulative sales into an otherwise untouched market (`research/datasets/kaggriculture-reference-agents/price_curves.csv:1-10`). `$0` below means the base price; `+50` means `price_at_50_sold`, etc.

| product | $0 | +50 | +150 | +400 | +1000 | units to $1 floor |
|---|---:|---:|---:|---:|---:|---:|
| WHEAT | 25 | 22 | 21 | 20 | 19 | >6000 |
| CARROT | 35 | 27 | 21 | 12 | 1 | 842 |
| TOMATO | 60 | 42 | 29 | 9 | 1 | 529 |
| STRAWBERRY | 120 | 24 | 1 | 1 | 1 | 62 |
| MELON | 250 | 225 | 25 | 1 | 1 | 158 |
| EGG | 50 | 43 | 41 | 40 | 38 | >6000 |
| MILK | 160 | 55 | 1 | 1 | 1 | 76 |
| WOOL | 200 | 55 | 1 | 1 | 1 | 59 |
| FERTILIZER | 100 | 90 | 70 | 20 | 1 | 493 |

The curve shapes explain the ladder split: STRAWBERRY, MILK, and WOOL are the most fragile; MELON is initially high-value but reaches the floor at 158 units; WHEAT and EGG are the most tolerant (`research/datasets/kaggriculture-reference-agents/price_curves.csv:2-10`; `research/notebooks/raykkretzschmar/kaggriculture-rank-your-agent.ipynb`, cells 8-11).

### What contradicts or corrects `docs/META.md`

- **Supported:** the claim that MELON is the best isolated crop per tile is directionally correct: CSV gross is 115.4 versus WHEAT 20.0 (`research/datasets/kaggriculture-reference-agents/crop_economics.csv:2,6`; `docs/META.md:102-103`).
- **Too broad:** `docs/META.md` says the crash-hard family reaches the floor by roughly 100-200 units (`docs/META.md:61-64`), but the exact thresholds are 59 WOOL, 62 STRAWBERRY, 76 MILK, and 158 MELON (`research/datasets/kaggriculture-reference-agents/price_curves.csv:5-9`). Three of four floor below 100.
- **Needs a FERTILIZER caveat:** `docs/META.md` groups FERTILIZER with essentially flat absorbers (`docs/META.md:63-64`), but the supplied curve falls from 100 to 20 by +400 and floors at 493 (`research/datasets/kaggriculture-reference-agents/price_curves.csv:10`). It is more tolerant than premium goods, not flat at arbitrary volume.
- **Needs CARROT/TOMATO nuance:** both are gentler than premium goods, but their prices are already $12/$9 at +400 and $1 at +1000 (`research/datasets/kaggriculture-reference-agents/price_curves.csv:3-4`); “flat at any realistic volume” is only safe for the smaller volumes used by the ladder.
- **Rough cap, not exact cap:** `docs/META.md` calls ~130 melons the useful cap and gives about $21k as a season ceiling (`docs/META.md:90-91`), while the supplied curve says the floor begins at 158 and `crop_economics.csv` records a 26,485 season ceiling (`research/datasets/kaggriculture-reference-agents/price_curves.csv:6`; `research/datasets/kaggriculture-reference-agents/crop_economics.csv:6`). Treat the doc figure as a conservative strategy heuristic, not the exact economic threshold.
- **Demand figures are consistent:** the doc's +1/day town-center addition and steady-state drains match the live notebook's shop table: WHEAT 30+1, STRAWBERRY 24+1, MILK 18+1, EGG/CARROT/TOMATO/WOOL 12+1, MELON 0+1, FERTILIZER 0 (`docs/META.md:66-85`; `research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cell 17).

The season timeline is not another price curve; it is a daily state ledger with `bank`, `hands_hired_today`, quadrants, crop/pasture/coop tiles, animals, shed load, and selected prices (`research/datasets/kaggriculture-reference-agents/season_timeline.csv:1`). Its role is to show when capacity and inventory appear, not to replace the crop/price tables.

## 4. Fingerprints: what they measure and what they do not

### Stream fingerprints

The stream dataset stores SHA-256 prefixes over canonicalized action dictionaries at horizons 24, 48, 100, ..., 719 plus `full_sha`; it does not store the actions or per-turn state (`research/datasets/kaggriculture-stream-fingerprints/README.md:68-80`; `research/datasets/kaggriculture-stream-fingerprints/make_fingerprints.py:37-57`). A matching hash proves identical emitted actions for that prefix, and matching full streams for the same team across different episodes/seeds/opponents is the open-loop proof (`research/datasets/kaggriculture-stream-fingerprints/README.md:3-5,70-76`; `research/datasets/kaggriculture-stream-fingerprints/make_fingerprints.py:16-18`).

It is a dated, derived snapshot, not a live leaderboard feed: 2026-07-30 17:29 UTC through 2026-08-11 23:19 UTC, 4,546 of 22,702 public episodes, about 20% (`research/datasets/kaggriculture-stream-fingerprints/README.md:40-50`). The random file has 5,340 seats from 2,670 episodes; the team-stratified file has 4,258 seats from 2,129 episodes; the latter is not a probability sample (`research/datasets/kaggriculture-stream-fingerprints/README.md:58-64,90-110`). It therefore cannot tell us the current Aug-14 top players' verb histogram, and it cannot produce one without returning to the raw replay corpus.

### Top-player opening fingerprints

This dataset does expose action verbs, but only for the first 48 turns of 15 episodes from five teams, snapshot date 2026-08-09 (`research/datasets/kaggriculture-top-player-opening-fingerprints/README.md:3-5,14,36-47`; `research/datasets/kaggriculture-top-player-opening-fingerprints/build_dataset.py:15,46-119`). Its clusters identify the historical top-5 snapshot: Seb rank 1 (3201.1), HealthStone rank 2 (3132.9), then the v23-fork trio tao_wu11, Mohamed, and mrgrishninsb (3117.6-3131.4) (`research/datasets/kaggriculture-top-player-opening-fingerprints/openings_clusters.csv:2-6`; `research/datasets/kaggriculture-top-player-opening-fingerprints/README.md:61-74`). So it is useful for an opening fingerprint, not the current full-season action mix.

The following verb histograms are calculated from all 3,171 rows in `research/datasets/kaggriculture-top-player-opening-fingerprints/openings_actions.csv:1-3172`; the generator records farmer, hand, and market verbs separately (`research/datasets/kaggriculture-top-player-opening-fingerprints/build_dataset.py:68-119`). They are first-48 counts, not 720-turn counts. `productive` means every verb except the four movement verbs and PASS, matching `tools/thrash.py:119-125`.

| historical top team | first-48 nonzero verb histogram | productive / movement / PASS | movement per productive |
|---|---|---:|---:|
| HealthStone | BUILD_PASTURE 15; BUY_ANIMAL 6; BUY_PRODUCT 6; BUY_SEED 9; CARE 12; COLLECT_FERTILIZER 12; EAST 30; FEED 12; HIRE 9; NORTH 48; PASS 45; PICKUP 21; PLACE 15; PLANT 30; SOUTH 21; WATER 30; WEST 60 | 177 / 159 / 45 | 0.90 |
| Mohamed = mrgrishninsb = tao_wu11 | BUILD_PASTURE 18; BUY_ANIMAL 6; BUY_PRODUCT 9; BUY_SEED 6; CARE 24; COLLECT_FERTILIZER 12; EAST 24; FEED 15; HIRE 15; NORTH 57; PASS 99; PICKUP 18; PLACE 12; PLANT 57; SELL 6; SOUTH 18; WATER 57; WEST 78 | 255 / 177 / 99 | 0.69 |
| Seb | BUILD_PASTURE 24; BUY_ANIMAL 9; BUY_PRODUCT 39; BUY_SEED 9; CARE 27; COLLECT_FERTILIZER 12; DROP 21; EAST 24; FEED 27; HIRE 42; NORTH 102; PASS 564; PICKUP 27; PLACE 15; PLANT 51; SELL 9; SOUTH 60; WATER 51; WEST 84 | 363 / 270 / 564 | 0.74 |

Our supplied full-episode reference is 1,703 productive actions, 2,790 movement actions, and 1,739 PASS, movement/productive 1.64 (`docs/RESEARCH_IDEAS.md:8-12`). The comparison is deliberately asymmetric: our numbers cover 720 turns, while the table covers 48. Even so, the early top-player slices show much tighter movement/productive ratios (0.69-0.90 versus our full-season 1.64), while Seb's 564 opening PASS is a warning that PASS alone is not a sufficient strength metric when a 14-hire opening creates many actor slots (`research/datasets/kaggriculture-top-player-opening-fingerprints/openings_clusters.csv:2`; `research/datasets/kaggriculture-top-player-opening-fingerprints/README.md:68-74`). The safe conclusion is “measure route efficiency over the same horizon”; it is not “copy the first-48 counts.”

## 5. What the meta notebooks say separates top from mid ladder

All eight requested notebooks were read. Their evidence is not one homogeneous experiment: some are teaching guides, some replay mining, and some local counterfactuals. The scope warnings matter: Busyaprime samples at most 300 games and calls its result a one-day snapshot (`research/notebooks/busyaprime/what-actually-wins-on-the-kaggriculture-ladder.ipynb`, cells 0 and 21); Kaito labels 25/27 local strict-future results, not an official public score (`research/notebooks/kaitofukami/25-27-strict-future-v27-midgame-meta-reset.ipynb`, cell 0); Tetsutani calls runtime validation a contract test, not a leaderboard estimate (`research/notebooks/tetsutani/adaptive-farming-strategy-for-kaggriculture.ipynb`, cell 18).

The ranked synthesis is:

1. **Market timing and order-queue control.** The reference ladder holds production fixed across tiers 6-9 and changes the market layer; Raykkretzschmar's ladder says that difference alone separates the high band (`research/notebooks/raykkretzschmar/kaggriculture-rank-your-agent.ipynb`, cell 5). The notebooks repeatedly identify metered premium sales, sell-slot ordering, one-turn front-runs, and preserving SELL-before-BUY cash flow as the decisive close-match lever (`research/notebooks/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta.ipynb`, cells 9, 18, 40, 47-50; `research/notebooks/kaitofukami/25-27-strict-future-v27-midgame-meta-reset.ipynb`, cell 7; `research/notebooks/flexonafft/kaggriculture-adaptive-replay-agent.ipynb`, cells 1-2).
2. **A coherent high-throughput production route.** Top farms converge on animals plus a small feed crop and a demand-compatible premium crop, while the private top-2 opening snapshot diverges into a sheep-first hybrid and an aggressive counter-meta rather than blindly following the public v23 fork (`research/notebooks/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb`, cells 20 and 29; `research/datasets/kaggriculture-top-player-opening-fingerprints/openings_clusters.csv:2-6`; `research/notebooks/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta.ipynb`, cells 7, 13, 16, 40). The reference ladder's concrete contrast is no production at tier 0, staples/land at tiers 1-4, and cared livestock plus feed at tier 5 (`research/datasets/kaggriculture-reference-agents/agents_manifest.csv:2-7`).
3. **Labor utilization plus locality-aware routing.** Strong strategies spend cheap labor on real work, but they do not confuse “more hands” with “more throughput”: Tetsutani keeps a common opening, then uses one public-demand checkpoint and coherent routes with worker-count, feed, room, weed, and market guards (`research/notebooks/tetsutani/adaptive-farming-strategy-for-kaggriculture.ipynb`, cells 1, 8, 10-12, 25). Ocean's STRONG STATR breakdown identifies job values, travel penalties, shared logistics slots, and a 10-12-hand cap as the scheduling core (`research/notebooks/ocean240812/kaggriculture-strategy-guide.ipynb`, cells 4-5 and 11). This directly matches our 1.64 movement/productive diagnosis (`docs/RESEARCH_IDEAS.md:8-20`).
4. **Opening capital sequencing and feed safety.** The notebooks repeatedly put feed before expansion, sell before same-turn buys, and reserve working capital before buying livestock; the reference implementation explicitly warns that losing the feed chain kills the herd (`research/notebooks/raykkretzschmar/kaggriculture-rank-your-agent.ipynb`, cell 36; `research/notebooks/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta.ipynb`, cells 47-50; `research/notebooks/ocean240812/kaggriculture-strategy-guide.ipynb`, cell 11). This is why the same animal/crop plan can win or collapse depending on market-slot order.
5. **Bounded adaptation to public demand/opponent state.** The useful adaptive designs do not replan everything every turn. Tetsutani reads the ordered `town.unlocked_shops` during the shared opening and commits once at turn 168 to one of two complete economies (`research/notebooks/tetsutani/adaptive-farming-strategy-for-kaggriculture.ipynb`, cells 8-12 and 25). Raykkretzschmar's later controller gates horizon inference on near-clone evidence, and Kaito rejects a seat router that improved an inner screen but did not solve real losses (`research/notebooks/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta.ipynb`, cells 24, 28, 40; `research/notebooks/kaitofukami/25-27-strict-future-v27-midgame-meta-reset.ipynb`, cells 3-7).
6. **Robustness and future-window validation.** Top-vs-mid separation is not established by a single high bank or a frozen replay. The notebooks insist on both seats, an untouched seed block, previous-best veto opponents, and current-future episodes; Kaito's protocol explicitly separates route selection from the strict-future gate (`research/notebooks/raykkretzschmar/kaggriculture-rank-your-agent.ipynb`, cells 28, 36-38; `research/notebooks/kaitofukami/25-27-strict-future-v27-midgame-meta-reset.ipynb`, cells 6-10; `research/notebooks/busyaprime/what-actually-wins-on-the-kaggriculture-ladder.ipynb`, cell 21). This is an experimental separator rather than an in-game verb, but it is the difference between a transferable mechanism and a lucky tape.

Ocean240812's guide adds useful baseline hypotheses—opponent-aware market prediction, Hungarian assignment, dynamic crop mix, marginal hand count, faster early cash, and endgame clearance—but labels them as directions with expected gains, not evidence from this repo (`research/notebooks/ocean240812/kaggriculture-strategy-guide.ipynb`, cell 12). They should be tested, not promoted to facts.

## ACTIONABLE

- Use `tools/thrash.py` to compare a locality/zone assignment variant against the current 1,703 productive / 2,790 movement / 1,739 PASS baseline; promote only if movement/productive falls below 1.64 or productive work rises.
- Use `tools/plan.py` to roll out the two complete demand-conditioned economies from the Tetsutani idea, with the commitment point and route coherence held fixed.
- Use `tools/sweep.py` to sweep the specific 8C/4S, 8C/5S, 9C/4S, and 8C/6S mixes with wheat/strawberry/melon seed counts, always reporting both seats.
- Use `tools/sellhours.py` plus `tools/sellprofile.py` to test one-turn premium front-runs and SELL-slot impact ordering without moving SELLs across feed/BUY slots.
- Use `tools/buildprobe.py` and `tools/shedprobe.py` to test expansion timing against first-animal timing, feed cash, shed occupancy, and overflow before any land experiment.
- Use `tools/tracedump.py` and `tools/verify_trace.py` to decode a newly selected official winning trace, then test only bounded repairs (weed, feed, terminal banking) against the frozen parent.
