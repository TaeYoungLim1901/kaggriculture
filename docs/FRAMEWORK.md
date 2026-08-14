# FRAMEWORK — a reusable method for agent competitions

Written while building the Kaggriculture agent, but deliberately competition-agnostic: the point is
that the *next* simulation competition should reuse this file and swap only the domain layer.

Five lenses, each with a concrete artifact in this repo. None of them are decoration — every one of
them caught a real bug or bought real score here, and that is the bar for keeping them.

---

## 0. What the strong agents in this genre actually look like

Before theorising, the empirical record from prior Kaggle simulation competitions:

- **Lux AI S2, 1st place ([ry_andy_](https://github.com/ryandy/Lux-S2-public))** — hand-written Python
  agent, not RL. Its central tunable is `FUTURE_LEN`: how many turns of forward simulation each unit
  plans over. Lookahead depth *is* the strategy knob.
- **Lux AI S2, top 25 ([AdamSlay](https://github.com/AdamSlay/LuxAI-competition-agent))** — explicit
  **GOAP** (Goal-Oriented Action Planning): each unit descends a decision tree to pick a *goal*, then
  emits a *queue* of actions realising it. Queues are made as long as possible to avoid re-planning
  cost, and are torn down and rebuilt from scratch when reality interrupts them.
- **Lux AI S1, 1st place ([Toad Brigade / IsaiahPressman](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021))**
  — deep RL, the counter-example. Worth knowing where the crossover is: RL wins when the action space
  is small and self-play is cheap; hand-written planning wins when the rules are rich, the episode is
  long, and a season has hard combinatorial structure.
- **Kaggriculture's own current meta** (see `docs/META.md`) — hard-coded 719-step traces harvested
  from public replays. Cheap, high-scoring, brittle, and self-mirroring.

The common thread in the hand-written winners: **units are assigned to goals, goals compile to action
queues, and the whole thing is re-derived from observed state every turn.** That is the shape we build.

---

## 1. Ontology — name the world before you reason about it

An ontology is a typed vocabulary: entity classes, their attributes, and the relations between them.
It sounds academic; in practice it is the thing that makes your state parser **total** — every value
the environment can hand you falls into exactly one class.

Kaggriculture's tile ontology (`_scan()` in `main.py`):

```
Tile = Empty | Locked | Weed | Plant | Structure
Structure = (Coop | Pasture) × (Occupied Animal | Vacant)
Plant  attributes: crop, planted_day, watered_today, yield_units, fertilized_until_day
Animal attributes: animal, fed_today, cared_today, pending_care_bonus, fertilizer_available
```

Relations that matter (these are what a bare attribute dump does *not* give you):

```
requires(GOOSE, COOP)        requires(COW|SHEEP, PASTURE)
produces(GOOSE, EGG)         consumes(Animal, WHEAT, 1/day)
enables(FERTILIZER, yield_bonus(Plant))
demands(Shop, Product)       drains(Town, Product, rate)
```

**Why it paid here.** The env represents a *vacant* coop and an *occupied* coop as the same dict shape,
distinguished only by the presence of an `"animal"` key. Splitting `structs` (vacant) from `animals`
(occupied) in the ontology is what makes "how many pastures still need a cow" a one-line set
difference instead of a bug farm. The first version of the agent lacked the `Occupied | Vacant`
distinction and happily bought 15 geese for 7 coops — $2,400 burned.

**Transfer rule.** For a new competition, write the ontology *first*, from the environment source, not
from the prose docs. It is 30 lines and it is the only part that must change.

---

## 2. Logic — actions as ⟨precondition, effect⟩, invariants as assertions

Model every operation the way classical planning (STRIPS/PDDL) does:

```
FEED:  pre  = on(unit, tile) ∧ occupied(tile) ∧ ¬fed_today(tile) ∧ WHEAT ∈ inv(unit)
       eff  = fed_today(tile) ∧ inv(unit)[WHEAT] -= 1
PLANT: pre  = on(unit, tile) ∧ empty(tile) ∧ seeds[crop] > 0
       eff  = plant(tile, crop)
```

Two hard-won rules:

**(a) Check preconditions client-side.** The environment silently no-ops illegal actions, so a missing
precondition costs you a whole unit-turn with *no error*. Our worst bug was exactly this: `FEED` was
assigned to whichever unit was nearest, ignoring `WHEAT ∈ inv(unit)`. Result: **456 no-op FEEDs** in 12
days, animals starved, escaped, and got re-bought in a loop. The fix was to attach a required-item
predicate to each task and filter candidates by it — three lines, and it turned a losing agent into one
that makes $58k. **In a silent-failure environment, a no-op is a bug that does not raise.**

**(b) Encode global invariants as runnable assertions,** not comments (`tests/test_invariants.py`):

```
|market orders| ≤ 10                     (extras silently dropped)
|action.hands| = |farm.hands|             (misalignment shifts every order)
Σ count(PLANT, crop) ≤ seeds[crop]        (over-demand drops ALL plants of that crop)
Σ shed ≤ 100                              (overflow silently discarded)
money ≥ 0 ∧ agent never raises
```

**(c) Respect partial observability.** The opponent's shed and seeds are hidden. Absence of evidence is
not evidence of absence: never let an unknown default to zero inside a comparison that drives a
decision. Model the opponent over what *is* public (tiles, money, hands, quadrants) — which is exactly
what the public `Breaking the Tie` agent does with its farm-fingerprint mirror detector.

---

## 3. Set theory — planning as set algebra

Most "what should I do next" logic is a set expression, and writing it as one removes whole classes of
counting bugs:

```
todo      = multiset(ANIMAL_PLAN) − multiset(animals on board)     # what to still buy
to_build  = todo − multiset(vacant structures)                     # what to still build
to_plant  = {crop ↦ target(crop) − |plants of crop|}               # what to still plant
feasible  ⊆ Units × Tasks                                          # the precondition relation
assignment: a matching M ⊆ feasible, injective in both coordinates
```

`_wanted()` in `main.py` is literally these four lines. The payoff is that "we already have 3 of the 4
sheep and one vacant pasture" needs no bookkeeping state — it is recomputed from the board every turn,
so it is *self-healing*. A trace-based agent has to bolt on repair logic for exactly this (the public
V16-RC5 carries a whole `_weed_repair_action` state machine); a set-derived agent gets repair for free.

**Inventories are multisets, not sets** — respect that and `shed`, `seeds`, and per-unit inventories
all obey the same three operations (add, take, cap).

**Cardinality constraints are first-class.** `|market orders| ≤ 10` per turn is a *budget*: it forces
you to rank orders by value, not to emit them opportunistically. Treat every hard cap in the rules as
a knapsack, not as a nuisance.

---

## 4. Graph engineering — matching, distance, and the production DAG

Three graphs, three different jobs.

**(a) The assignment bipartite graph.** Units on one side, tasks on the other, edge weight = cost
(distance + priority penalty), non-edges = infeasible (`math.inf`). Greedy nearest-first is
`O(n·m)` and *locally* fine but globally wrong: one unit standing between two urgent tasks can strand
a second unit across the board. The optimum is a **minimum-cost bipartite matching** — the Hungarian /
Jonker–Volgenant algorithm, `O(n³)`, which at our sizes (≤12 units × ~80 tasks) is microseconds.
This is a textbook result and it is the single highest-leverage import from graph theory into this
genre: goal assignment is a matching problem, and matching problems have exact polynomial solutions,
so there is no excuse for a greedy heuristic. (`tools/assign.py`)

**(b) The movement graph.** A grid where locked tiles are *passable* — so no edges are removed and
shortest path collapses to Manhattan distance, computable in O(1). Establish this before writing a
BFS you do not need. In competitions where obstacles do exist, this is where BFS/A* and, critically,
*reservation tables* (time-expanded graphs to avoid two units claiming a tile at the same step) go.

**(c) The production DAG.** Nodes = resources, edges = conversions with a time and a yield:

```
$ → seed → (water ×n days) → crop → $
$ → structure + animal → (wheat/day, care/day) → product → $
                        ↘ fertilizer (free, 1/animal/day) → $  and → yield bonus
```

Reading the DAG answers questions no local heuristic can: *what is the bottleneck?* Here it is neither
land nor actions — 8 hired hands cost $54/day total, so labour is nearly free — it is **market
absorption**, a sink capacity on the last edge. That reframing is what produced the drip-selling
controller below. Do this analysis on paper (or in `tools/drain.py`) before writing policy code.

---

## 5. Loop engineering — four nested loops, each with its own invariant

```
L0  turn      sense → derive → plan → act      720× per episode. Must never raise. Must be fast.
L1  day       hire → work → drop → refresh     24 turns. Owns the sell window and the feed budget.
L2  season    build-out → steady state → liquidate
L3  dev       edit → paired eval → accept/reject
```

**L0 must be pure.** Recompute everything from `obs`; keep no cross-turn mutable state you cannot
rebuild. Module-level state is a trap in this genre: the same process plays *both seats* and *many
episodes*, so any global must be keyed by seat and reset on `step == 0` (every public trace agent does
this — see their `_FR_STATE[seat]` / `_WEED_STATE[seat]` dictionaries — and it is a classic source of
cross-episode contamination bugs).

**Replay indexing is off by one.** In `kaggle-environments`, `env.steps[i][seat].action` is the reply
to `env.steps[i-1][seat].observation`, not to the observation stored beside it. Any checker or replay
parser that pairs them naively will report a wall of false violations — ours did, on the very first
run of `tools/package.py`, claiming the hand count was wrong on every single step. Verify your
harness against a known-good agent before you trust it to accuse your own.

**L1 owns the phase-sensitive actions.** Harvest lands in a unit's inventory and only reaches the shed
at end-of-day, so sells must be scheduled *after* the drop, not before. Getting the phase wrong makes
an agent that produces perfectly and sells nothing.

**L2 is a feedback controller, not a schedule.** This is the deepest borrowing from control theory and
the biggest departure from the trace-based meta. Instead of "sell 20 melons on day 17", run

```
sell_rate(product) ← f(price(product) vs target, stock, town drain estimate)
```

Open-loop schedules (the public traces) desync the moment reality drifts. A closed loop cannot desync
because it has no plan to desync from — it only has a setpoint. Our v0 already uses a crude version
(a constant per-product daily cap derived from town drain); `tools/drain.py` calibrates the setpoints
by Monte Carlo over the shop-unlock randomness.

**L3 is the loop that actually determines your ranking, so instrument it hardest:**

- Always evaluate **both seats on the same seeds**. Single-seat results are worthless — seat asymmetry
  in market order resolution is real.
- Score on the metric the leaderboard uses. Here that is **win rate, not money**: the rating system
  ignores margin entirely, so a +$1 win equals a +$20,000 win. Optimising mean money is optimising the
  wrong objective and will happily trade three narrow wins for one blowout.
- Parallelise it (`tools/eval.py --jobs`). A 30-seed paired panel is 60 × 720-step simulations; if that
  takes ten minutes you will stop running it, and an unmeasured change is a coin flip.
- Fix the seeds. Reproducibility beats sample size when you are debugging.

---

### 5.x The harness is part of the system under test

Two failures on this project came from testing a *different object* than the one submitted, and
neither produced a useful error message.

**Position-dependent entry points.** Kaggle selects the submitted agent with
`[v for v in exec_globals.values() if callable(v)][-1]` — the last callable defined in the file, by
position, ignoring its name. A `demo()` self-check placed after `agent()` therefore *becomes* the
agent. The remote error was the entire text `Validation Episode failed.` Before trusting any
convention about entry points ("it looks for `agent`"), read the loader.

**Bypassed sandboxes.** Local harnesses take a function object; the real one takes a file path and
wraps it in timeouts. Every function-level test passed — determinism, both seats, full episodes,
action schema — while the file failed validation, because passing `mod.agent` skipped the loader and
the 1 s per-step `actTimeout` entirely.

The rule: **the last validation gate must consume the exact artifact you ship, through the exact
loader the grader uses.** Convenience wrappers are fine everywhere upstream of that gate. A checker
that cannot fail on a broken submission is not a checker.

## 6. Checklist for the next agent competition

1. Read the **environment source**, not the docs. Table the constants yourself. (Docs lie; the
   interpreter does not.)
2. Write the **ontology** (30 lines) and a total `scan()` from observation to typed state.
3. Write the **precondition table**. Every action you can emit, and what must hold for it to not no-op.
4. Find the **cardinality caps** (orders/turn, inventory, hires) and treat each as a budget.
5. Draw the **production DAG**; find the sink with the smallest capacity. That is your real objective.
6. Build the **paired evaluation harness** before the second version of the agent. Parallel, seeded,
   both seats, scored on the leaderboard's actual metric.
7. Encode **invariants as tests** and run them on a real episode plus a fuzz corpus.
8. Only now write policy: units → goals via **min-cost matching**, goals → action queues, replan on
   interruption.
9. Prefer a **closed-loop controller** over a schedule wherever the environment has feedback (prices,
   supply, opponent pressure).
10. Mine the **public replays**. In simulation competitions every episode is public: the strongest
    opponents' full action traces are a free dataset, and reconstructing them tells you the meta.

## References

- ry_andy_ — [Lux AI S2 1st place agent](https://github.com/ryandy/Lux-S2-public) (writeup: Kaggle discussion 407982)
- AdamSlay — [Lux AI S2 GOAP rule-based agent, top 25](https://github.com/AdamSlay/LuxAI-competition-agent)
- Isaiah Pressman — [Lux AI S1 1st place, deep RL](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021)
- tonghuikang — [published Lux AI benchmark agent](https://github.com/tonghuikang/lux-ai-2021)
- Kaggle — [simulation competitions CLI guide](https://github.com/Kaggle/kaggle-cli/blob/main/docs/simulation_competitions.md)
- nagiss — [trends in Kaggle simulation competitions](https://speakerdeck.com/nagiss/kagglesimiyuresiyonkonpenodong-xiang)
