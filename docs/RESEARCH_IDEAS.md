# Kaggriculture strategy research ideas

Research date: 2026-08-14. This is a strategy memo only; `main.py` was not changed and no
evaluation was run while writing it.

## Decision rule

The local baseline is 1,703 productive actions, 2,790 movement actions, 1,739 `PASS`, and
movement/productive `= 1.64`. The comparable opponent is 3,494 productive, 324 movement, and
movement/productive `= 0.99`. Those are the filter: keep an idea only if it can plausibly get
movement/productive below 1.64 or productive actions above 1,703. Money-only ideas are rejected
even when their economics are sound.

The central diagnosis is spatial. A 25-tile plan is asking nine units to service a small set of
targets; buying more land without changing assignment makes the walks longer. The useful outside
ideas therefore have to improve the chain

```text
task value -> worker/zone assignment -> route -> chained action -> shed/market timing
```

## Source table

| Source | URL | Why it is relevant |
| --- | --- | --- |
| Stardew Valley crop growth calendars | [stardewvalleywiki.com/Crop_Growth_Calendars](https://stardewvalleywiki.com/Crop_Growth_Calendars) | Makes growth windows and replant timing explicit; supports scheduling around harvest windows rather than ranking crops only by price. |
| Factorio: What transport for which case? | [wiki.factorio.com/Tutorial:Transport_use_cases](https://wiki.factorio.com/Tutorial:Transport_use_cases) | Separates short, high-throughput local transport from medium/long-haul transport; directly analogous to farm-zone locality. |
| Factorio logistic network | [wiki.factorio.com/Logistic_network](https://wiki.factorio.com/Logistic_network) | Documents nearest-source pickup and distance/range costs, useful for shed staging and route-length accounting. |
| RimWorld stockpile zones | [rimworldwiki.com/wiki/Stockpile_zone](https://rimworldwiki.com/wiki/Stockpile_zone) | Recommends small, high-priority stores beside workbenches while haulers refill them from afar. |
| RimWorld hauling | [rimworldwiki.com/wiki/Hauling](https://rimworldwiki.com/wiki/Hauling) | Covers full-load hauling, one-item-type batching, priority, and why storage should be close to the consumer. |
| Graveyard Keeper automation walkthrough | [blog.edersonfernandes.com.br/graveyard-keeper-walkthrough-part-9-the-zombie-revolution-and-the-golden-kitchen](https://blog.edersonfernandes.com.br/graveyard-keeper-walkthrough-part-9-the-zombie-revolution-and-the-golden-kitchen/) | Uses dedicated workers for production plus automated delivery; relevant to separating productive work from logistics. |
| Agricola strategy guide | [dave-choi.github.io/strategy/agricola](https://dave-choi.github.io/strategy/agricola/index.html) | Shows the worker-placement principle that a maintenance/food engine must be secured before growing the workforce, or future actions are lost to upkeep. |
| Caverna strategy tips | [elusivemeeple.com/2018/02/11/caverna-strategy-tips](https://elusivemeeple.com/2018/02/11/caverna-strategy-tips/) | Supports specialization with enough diversity to avoid a brittle single-engine plan. |
| Lux AI Season 1: Toad Brigade | [github.com/IsaiahPressman/Kaggle_Lux_AI_2021](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021) | A multi-unit competition writeup: one controller coordinates variable fleets and learns when to mine, defend, expand, and finish. |
| Lux AI Season 2 official repository | [github.com/Lux-AI-Challenge/Lux-Design-S2](https://github.com/Lux-AI-Challenge/Lux-Design-S2) | Explicitly frames the competition as resource gathering and allocation with action efficiency and planning. |
| Lux AI Season 2 centralized-control report | [lectures.cgdct.moe/gatech/ml/luxai/egpaper_for_review.pdf](https://lectures.cgdct.moe/gatech/ml/luxai/egpaper_for_review.pdf) | Describes pathfinding and delegated robot responsibilities as the hard part of a variable-sized fleet. |
| Halite III post-mortem | [gist.github.com/nccvector/550800f73f5091382bfd57cdada34a06](https://gist.github.com/nccvector/550800f73f5091382bfd57cdada34a06) | Scores mining by gain per turn and penalizes duplicate destinations and nearby interference. |
| Kore 2022 rules-based writeup | [kaggle.com/competitions/kore-2022/writeups/1-musketeer-1-musketeer-5th-place-solution-rules-b](https://www.kaggle.com/competitions/kore-2022/writeups/1-musketeer-1-musketeer-5th-place-solution-rules-b) | Discusses route generation/selection, distributing fleets, avoiding short routes, and not tying up too many units in one task. |
| CodinGame Spring Challenge 2026 post-mortem | [yannmoisan.com/spring-challenge-2026-postmortem](https://www.yannmoisan.com/spring-challenge-2026-postmortem.html) | Gives the directly useful score `collected / (travel + work + return)` and uses coordinated early/main/end phases. |
| CodinGame Fall Challenge 2024 feedback | [gist.github.com/0x6E0FF/065bfdfca2384549029e18a2e3c4175c](https://gist.github.com/0x6E0FF/065bfdfca2384549029e18a2e3c4175c) | Builds a route graph, computes BFS paths, and measures path overlap before selecting infrastructure. |
| Terminal regional post-mortem | [energy-in-joles.github.io/hackathon/2024-05-26-terminal24](https://energy-in-joles.github.io/hackathon/2024-05-26-terminal24/) | Exploits predictable shortest-path behavior and integrates attack and defense instead of treating them as independent subsystems. |
| Screeps roles | [wiki.screepspl.us/Roles](https://wiki.screepspl.us/Roles/) | Documents role-specific workers versus generic reassignment, including the specialization/idle tradeoff. |
| Screeps remote harvesting | [wiki.screepspl.us/Remote_Harvesting](https://wiki.screepspl.us/Remote_Harvesting/) | Uses static miners plus haulers and explicitly warns that round-trip travel prevents source saturation. |
| Lifelong MAPD: Token Passing and Task Swaps | [publications.ri.cmu.edu/lifelong-multi-agent-path-finding-for-online-pickup-and-delivery-tasks](https://publications.ri.cmu.edu/lifelong-multi-agent-path-finding-for-online-pickup-and-delivery-tasks) | Formalizes recurring pickup/delivery task assignment with online reallocation and collision-free paths. |
| Integrated task assignment and path planning for MAPD | [arxiv.org/abs/2110.14891](https://arxiv.org/abs/2110.14891) | Shows why assignment-first lower-bound costs can be wrong and proposes marginal actual-cost assignment plus large-neighborhood repair. |
| Collision-aware task assignment | [arxiv.org/abs/1904.04374](https://arxiv.org/abs/1904.04374) | Adds collision/deadlock penalties and a receding collision horizon to task bids. |
| Stanford multi-robot task allocation | [robotics.stanford.edu/~gerkey/research/mrta.html](https://robotics.stanford.edu/~gerkey/research/mrta.html) | Connects worker/task allocation to the optimal assignment problem and interference minimization. |
| Cluster-first, route-second / sweep | [metricgate.com/docs/sweep-algorithm-vrp](https://metricgate.com/docs/sweep-algorithm-vrp/) | Names the standard sweep heuristic, its angular clustering step, nearest-neighbor route step, and its non-clustered-demand failure mode. |
| Vehicle routing with time windows review | [sciencedirect.com/science/article/pii/S1018364710000297](https://www.sciencedirect.com/science/article/pii/S1018364710000297) | Places sweep, insertion, local search, and metaheuristics in the standard VRPTW toolbox. |
| Market Impact: A Systematic Study of Limit Orders | [arxiv.org/abs/1802.08502](https://arxiv.org/abs/1802.08502) | Finds temporary price impact for large orders and studies splitting a meta-order into smaller pieces. |
| EVE Online market guide | [thonky.com/eve-online-guide/eve-online-market](https://www.thonky.com/eve-online-guide/eve-online-market) | A competitive-game market guide: do not underprice blindly, use demand/traffic, and avoid sacrificing margin for instant sale. |

## What transfers to this game

### Walking, tool trips, and batching

Experts generally do four things:

1. Score a job by output per complete round trip, not output per action. The Spring Challenge
   post-mortem uses `min(resource, carry remaining) / (travel + work + return)`, while the Halite
   post-mortem uses a gain-per-turn score and penalizes duplicate targets. Those formulas transfer
   directly to `WATER`, `FEED`, `HARVEST`, `CARE`, `FERTILIZE`, and `COLLECT_FERTILIZER`: a nearby
   lower-price task can beat a distant premium task once return travel is included. ([Spring
   Challenge](https://www.yannmoisan.com/spring-challenge-2026-postmortem.html), [Halite
   III](https://gist.github.com/nccvector/550800f73f5091382bfd57cdada34a06))

2. Keep high-frequency work local to its consumer. Factorio favors direct short-range transport for
   high throughput; RimWorld recommends small high-priority stockpiles beside the workbench and
   separate haulers for the long haul. Kaggriculture has no local stockpile tile, so the closest
   equivalent is a worker home range: the same hand should repeatedly service the same animal or
   crop cluster before returning to the shed. ([Factorio transport](https://wiki.factorio.com/Tutorial:Transport_use_cases),
   [RimWorld stockpiles](https://rimworldwiki.com/wiki/Stockpile_zone))

3. Fill the carrier and batch one material. RimWorld haulers take a maximum load of one item type;
   Screeps uses static miners plus dedicated haulers because a generic harvester loses throughput on
   the return trip. In Kaggriculture this means one `PICKUP WHEAT 6` followed by several `FEED`
   actions is useful; six separate one-unit pickups are not. ([RimWorld hauling](https://rimworldwiki.com/wiki/Hauling),
   [Screeps remote harvesting](https://wiki.screepspl.us/Remote_Harvesting/))

4. Use standing orders, but preserve a controlled escape hatch. Screeps role workers are efficient
   when their role matches a stable demand, while generic workers are easier to reassign. The right
   Kaggriculture version is not permanent `STICKY=True`; it is a short chain such as
   `FEED -> HARVEST -> CARE -> COLLECT_FERTILIZER` with preemption only for an expiring `FEED` or
   `WATER` deadline. ([Screeps roles](https://wiki.screepspl.us/Roles/))

5. Batch by spatial sweep, not by arbitrary global priority. The standard sweep heuristic clusters
   customers first and routes each cluster second; nearest-neighbor is a cheap route construction
   method. It is only a baseline because it fails when demand is not angularly clustered or when
   time windows/capacity dominate. ([Sweep](https://metricgate.com/docs/sweep-algorithm-vrp/),
   [VRPTW review](https://www.sciencedirect.com/science/article/pii/S1018364710000297))

### What competition bots did about assignment

- Lux S1 used a single controller for the whole variable-sized fleet; the writeup describes the
  learned policy coordinating mining, defense, resource denial, and end-game construction rather
  than giving every unit an isolated greedy policy. Lux S2 similarly makes allocation and action
  efficiency first-class concerns. The practical translation is a farm-wide task list plus a
  global assignment, which is already the right shape of `tools/assign.py`. ([Lux S1](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021),
  [Lux S2](https://github.com/Lux-AI-Challenge/Lux-Design-S2))

- Halite and Kore both score routes by the opportunity cost of travel and avoid duplicate or
  undersized routes. Halite explicitly reduces the value of cells claimed by another friendly ship;
  the Kore writeup discusses minimum/maximum route and fleet sizes and distributing routes among
  shipyards. For Kaggriculture, a task bid must include the next task and the worker's home/shed
  return, not only current Manhattan distance. ([Halite III](https://gist.github.com/nccvector/550800f73f5091382bfd57cdada34a06),
  [Kore 2022](https://www.kaggle.com/competitions/kore-2022/writeups/1-musketeer-1-musketeer-5th-place-solution-rules-b))

- CodinGame Spring used three phases and a full round-trip throughput score; Fall built a graph,
  computed paths, and measured path overlap. Terminal exploited predictable shortest paths and then
  integrated offense and defense. These are concrete precedents for phase schedules, route
  reservations, and chained tasks rather than a fresh global replan every step. ([Spring](https://www.yannmoisan.com/spring-challenge-2026-postmortem.html),
  [Fall](https://gist.github.com/0x6E0FF/065bfdfca2384549029e18a2e3c4175c),
  [Terminal](https://energy-in-joles.github.io/hackathon/2024-05-26-terminal24/))

## Ranked ideas

The effects below are deliberately stated as falsifiable ranges, not results. The first two
experiments should be measured on the current 25-tile farm before any new land is bought.

| Rank / idea | Mechanism | Which verbs/constants it touches | Expected effect on the measured gap | Cheapest experiment that would falsify it |
| --- | --- | --- | --- | --- |
| 1. Home-range rosters, then cluster-first expansion | Partition owned tiles into compact crop/animal zones. Give each unit a home zone and assign it a local queue; allow cross-zone travel only for urgent `FEED`/`WATER` or shed work. When expanding, buy a quadrant only if it adds a full local workload, not just empty distance. This is the game-fit form of Factorio short-haul flow, RimWorld local stockpiles, Lux cluster operations, and sweep clustering. ([Factorio](https://wiki.factorio.com/Tutorial:Transport_use_cases), [RimWorld](https://rimworldwiki.com/wiki/Stockpile_zone), [Lux S2](https://github.com/Lux-AI-Challenge/Lux-Design-S2), [Sweep](https://metricgate.com/docs/sweep-algorithm-vrp/)) | `_scan`, `_tasks`, `_assign`, `_step_toward`; `CROP_PLAN`, `ANIMAL_PLAN`, `LAND_TARGET`, `LAND_RESERVE`, `STICKY`; `WATER`, `FEED`, `HARVEST`, `CARE`, `FERTILIZE`, `COLLECT_FERTILIZER`. | Highest upside. On the current layout, target movement/productive `<= 1.35` and productive `>= 2,100`; with a proven local planner, target the opponent-like `>= 2,500` productive actions on two/three quadrants. If it only makes workers stay put but does not create enough local tasks, it fails the productive-action bar. | Add one `ZONE_MODE` variant with no crop or animal change. Run `python tools/thrash.py <variant>.py` and reject unless the ratio is `< 1.64` without productive falling below `1,703`; only then run `python tools/eval.py --games 8` against the meta. Use `tools/buildprobe.py` before testing an expanded version. |
| 2. Round-trip marginal-cost bids | Replace `PRIO_COST + distance` with a candidate score using expected output/value, service time, distance to the target, distance to the next compatible target or shed, and deadline slack. Reuse the existing Hungarian solver; only change the cost matrix. This is the direct Spring/Halite heuristic and the MAPD lesson that actual delivery cost beats assignment lower bounds. ([Spring](https://www.yannmoisan.com/spring-challenge-2026-postmortem.html), [Halite III](https://gist.github.com/nccvector/550800f73f5091382bfd57cdada34a06), [integrated MAPD](https://arxiv.org/abs/2110.14891), [MRTA](https://robotics.stanford.edu/~gerkey/research/mrta.html)) | `_tasks`, `_assign`, `PRIO_COST`, `DIST_WEIGHT`; task metadata for yield, deadline, next task; `WATER`, `FEED`, `HARVEST`, `CARE`, `FERTILIZE`, `COLLECT_FERTILIZER`, `PLANT`. | Plausibly cuts movement to `2,100–2,500` and raises productive actions to `1,900–2,300`, which would cross both filters if task density is sufficient. It should beat pure distance weighting because the local sweep already showed that `DIST_WEIGHT > 1` alone does not unlock expansion. | Add one cost-matrix variant only. `python tools/thrash.py <variant>.py` is the cheap screen; require ratio `< 1.64` and productive `> 1,703`. Then use `python tools/eval.py --games 8` on both seats. |
| 3. Chained task bundles with deadline preemption | Persist a short queue per unit: for an animal zone, `PICKUP WHEAT -> FEED all assigned animals -> HARVEST -> CARE -> COLLECT_FERTILIZER`; for a crop zone, `WATER all -> FERTILIZE due ongoing crops -> HARVEST`. Replan only when the queue is empty, a tile disappears, or a higher-deadline task becomes unsafe. This combines Screeps role specialization, Graveyard Keeper production/delivery chains, and MAPD online task reassignment. ([Screeps roles](https://wiki.screepspl.us/Roles/), [Graveyard Keeper](https://blog.edersonfernandes.com.br/graveyard-keeper-walkthrough-part-9-the-zombie-revolution-and-the-golden-kitchen/), [MAPD](https://publications.ri.cmu.edu/lifelong-multi-agent-path-finding-for-online-pickup-and-delivery-tasks)) | `_act`, `_tasks`, `_assign`, `_sticky_plan`; `STICKY` should become a short-lived queue, not a global lock; `FEED`, `WATER`, `CARE`, `HARVEST`, `COLLECT_FERTILIZER`, `FERTILIZE`, `PICKUP`, `DROP`. | Strongest direct PASS lever. Target `PASS < 1,200`, movement/productive `1.20–1.50`, and productive `2,200+`. It can fail if the current 25 tiles do not expose enough simultaneous work; then it should be paired with rank 1 before adding land. | Implement only one animal bundle on the current farm. Run `python tools/thrash.py <variant>.py` and inspect target runs, retargets, PASS, movement, and productive. Falsify if productive does not exceed `1,703` or if movement/productive stays `>= 1.64`; do not infer success from fewer retargets alone. |
| 4. Daily phase scheduler with slack/deadline ordering | Treat the 24-hour day as a small VRPTW: early hours feed/water, middle hours finish harvest/fertilizer work, every hour drains a small sell quota, and late hours repair weeds/return inventory. Rank by deadline slack rather than repeatedly mixing all verbs. Agricola/Caverna's harvest phases and Lux/CodinGame phase policies support this kind of stable cadence. ([Agricola](https://dave-choi.github.io/strategy/agricola/index.html), [Caverna](https://elusivemeeple.com/2018/02/11/caverna-strategy-tips/), [Lux S1](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021), [VRPTW](https://www.sciencedirect.com/science/article/pii/S1018364710000297)) | `day`, `hour`, `_tasks`, `_market`; `SELL_HOURS`, `DRAIN`, `LAST_DAY`; `FEED`, `WATER`, `CARE`, `HARVEST`, `FERTILIZE`, `DIG`, `SELL`. | Medium upside on the current farm: target movement/productive `1.35–1.55` and productive `1,900–2,100`. It should improve reliability and reduce urgent cross-zone rescue trips, but cannot create work by itself. | Add phase weights without changing the crop/animal plan. Use `python tools/thrash.py <variant>.py` plus `python tools/sellhours.py --me <variant>.py`; falsify if the phase scheduler lowers productive actions or leaves any two-day feed/water deadline missed. |
| 5. Sweep each zone, batch full loads, and return once | Once a unit owns a zone, order compatible tasks by a cheap nearest-neighbor/snake sweep, carry full wheat or harvested stacks, and make one shed return after the batch. Do not split an order inside one turn merely to create more market orders: the useful batching is spatial and inventory batching. This is cluster-first/route-second plus RimWorld/Screeps load amortization, with the known sweep failure mode guarded by deadlines. ([Sweep](https://metricgate.com/docs/sweep-algorithm-vrp/), [RimWorld hauling](https://rimworldwiki.com/wiki/Hauling), [Screeps remote harvesting](https://wiki.screepspl.us/Remote_Harvesting/)) | `_step_toward`, `_tasks`; `SEED_BATCH`, `SHED_CAP`; `PICKUP`, `DROP`, `PLACE`, `FEED`, `HARVEST`, `WATER`, `SELL_HOURS`. | Likely movement reduction to `2,200–2,600` and productive increase of `200–500`, enough to cross the ratio bar only if it also reduces PASS. It is weaker without rank 1 because the shed is the only shared staging point. | Add a route-ordering helper and no new tasks. Run `python tools/thrash.py <variant>.py`; use `python tools/shedprobe.py <variant>.py` to catch inventory overflow. Falsify if movement falls but productive does not rise above `1,703`, or if shed overflow increases. |
| 6. Route-aware expansion with staged crop waves | After ranks 1–3 pass on one quadrant, reproduce the opponent's structural idea: land buys create enough targets to keep workers busy, but buy animals first, reserve feed cash, and plant high-drain ongoing crops in compact waves. Use strawberry only when its tiles are near a worker route and fertilizer can be consumed for doubled ongoing yield. The expansion is conditional because Screeps and Factorio both show that a remote source loses throughput to return travel. ([Screeps remote harvesting](https://wiki.screepspl.us/Remote_Harvesting/), [Factorio transport](https://wiki.factorio.com/Tutorial:Transport_use_cases), [Stardew calendars](https://stardewvalleywiki.com/Crop_Growth_Calendars)) | `BUY_LAND`, `BUY_ANIMAL`, `BUILD_PASTURE`, `BUILD_COOP`, `PLANT`, `WATER`, `FERTILIZE`, `HARVEST`, `SELL`; `LAND_TARGET`, `ANIMAL_RESERVE`, `PLANT_CAP`, `CROP_PLAN`, `ANIMAL_PLAN`, `HIRES`. | This is the only idea with a credible path to the full `3,494` productive-action regime, but it must preserve movement/productive `<= 1.64`. Target `2,500–3,400` productive actions with movement/productive `1.20–1.60`; expansion alone is already falsified locally. | Use `tools/buildprobe.py` to verify the first animal remains day 0, then `tools/thrash.py` for routing. Only if both bars pass, run `tools/sweep.py <one-config> --games 8` against both the mirror and meta. |

## Operations-research heuristics and failure modes

| Heuristic | What it buys | Failure mode here | Kaggriculture use |
| --- | --- | --- | --- |
| Greedy nearest task | Very cheap and often locally sensible. | It minimizes one worker's next leg and can strand another worker from an urgent task; it also ignores return and future legs. The MRTA literature frames even homogeneous-worker allocation as an assignment/interference problem. ([MRTA](https://robotics.stanford.edu/~gerkey/research/mrta.html)) | Keep `tools/assign.py`'s Hungarian matching; improve its edge costs instead of replacing it with nearest-first. |
| Hungarian / linear assignment | Globally optimal for the supplied one-step cost matrix. | Static one-step costs do not encode task sequences, deadlines, or route congestion; the MAPD literature explicitly motivates actual marginal delivery cost and coupled repair. ([integrated MAPD](https://arxiv.org/abs/2110.14891)) | Rank 2: retain the solver, change the matrix. |
| Sweep / cluster-first, route-second | Fast, deterministic, transparent baseline. | Angular clustering is poor for scattered or asymmetric demand; nearest-neighbor can make bad within-cluster routes, and time windows can make a cheap route infeasible. ([Sweep](https://metricgate.com/docs/sweep-algorithm-vrp/), [VRPTW](https://www.sciencedirect.com/science/article/pii/S1018364710000297)) | Use only inside a compact farm zone, with feed/water deadlines as hard constraints. |
| Token Passing / task swaps | Online assignment with bounded coordination and a way to swap a task when a better worker appears. ([MAPD](https://publications.ri.cmu.edu/lifelong-multi-agent-path-finding-for-online-pickup-and-delivery-tasks)) | A static token can starve a newly urgent animal; a swap on every observation becomes the same retarget thrash seen locally. | Emulate one daily reservation token and allow swaps only on deadline violation. |
| Auction / dynamic task allocation | Adapts to changing yields, inventory, and opponent state; collision-aware variants reduce overlap/deadlock. ([dynamic allocation review](https://www.sciencedirect.com/org/science/article/pii/S0143991X20000136), [collision-aware allocation](https://arxiv.org/abs/1904.04374)) | Repeated bids add computation and oscillation; Kaggriculture has no unit collision penalty worth optimizing because workers may share a tile. | Use a centralized bid matrix, not per-unit auctions. |
| Hysteresis / sticky targets | Cuts pre-arrival retargets. | The local `STICKY=True` sweep reduced retargets but worsened movement/productive from 1.64 to 1.84 and productive from 1,703 to 1,650; persistence without a useful chain is not enough. | Use bounded bundle persistence only, then measure with `tools/thrash.py`. |

## Shared-market implications

The market analogues are useful but mostly fail the requested movement/productivity filter.

- Market-impact research studies large orders split into smaller pieces and finds temporary impact
  plus partial relaxation afterward. In Kaggriculture, splitting inside one turn is not the same
  experiment: sell orders are repriced unit by unit against the same inventory. The transferable
  move is splitting across *turns* so town consumption can refill the market between sales. ([Market
  Impact](https://arxiv.org/abs/1802.08502))

- EVE's practical advice is to avoid blindly underpricing, watch where demand/traffic is, and accept
  waiting when a stable market can come to your price. Kaggriculture has no player-selected sell
  price, so the equivalent controls are `DRAIN`, `SELL_HOURS`, product order priority, and whether
  to sell before the opponent's likely premium batch. ([EVE market guide](https://www.thonky.com/eve-online-guide/eve-online-market))

- Because both players sell into one inventory, selling a crash-prone product earlier can both
  capture the higher pre-glut units and leave a worse price for the opponent. That is a plausible
  denial/front-run lever for final money, but it does not create a farmer/hand action and cannot by
  itself lower 1.64 or raise 1,703. Treat it as a tie-breaker after routing, not the next mainline
  project. The local `tools/sellhours.py` and `tools/sellprofile.py` are the right probes.

## Rejected

- **`STICKY=True` as the whole fix.** It reduced retargets, but the local sweep measured 3,041
  movement, 1,650 productive, and ratio 1.84. Add only bounded task bundles with deadline
  preemption. (`docs/SWEEP_STICKY.md`, `tools/thrash.py`)

- **Higher `DIST_WEIGHT` as the whole fix.** The local distance sweep did not beat the shipped
  build and did not unlock expansion. A distance term belongs inside a value/return/deadline bid,
  not as a large global multiplier. (`docs/SWEEP_DISTANCE.md`, `tools/sweep.py`)

- **Land expansion without a locality planner.** The measured expansion variants spent money and
  converted new area into walking; more tiles are useful only when they add enough compact tasks
  to keep workers busy. Expand only after rank 1–3 pass. (`docs/META.md`, `tools/buildprobe.py`,
  `tools/thrash.py`)

- **More hired hands or a larger herd by default.** These add slots, but the current farm does not
  provide enough nearby work and larger herds can starve or glut milk/wool. They cannot meet either
  metric filter without a route/workload change. (`docs/META.md`, `tools/sweep.py`)

- **Market-only drip selling, price gates, or front-running.** Drip selling is already the right
  market shape locally; more market timing may improve final coins or deny revenue, but it cannot
  fix PASS, movement, or productive-action counts. Keep it as a later money tie-breaker. (`docs/META.md`,
  `tools/sellhours.py`, `tools/sellprofile.py`)

- **Collision-aware MAPD machinery as the first implementation.** MAPD collision horizons are
  valuable in warehouses, but Kaggriculture permits farmer/hand co-location. The relevant MAPD
  lesson is assignment plus route cost, not a collision simulator. ([CATA](https://arxiv.org/abs/1904.04374))

