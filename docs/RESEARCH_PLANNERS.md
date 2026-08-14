# Planning algorithms for Kaggriculture

Research date: 2026-08-14

## Bottom line

Build finished-trace simulated annealing first, seeded from several recorded traces and run as eight independent chains. It matches the artifact the leaderboard actually consumes, needs only the exact terminal margin, parallelises cleanly, and can spend roughly 16,000–20,064 complete-trace evaluations inside the current 58.52-minute budget on eight cores under the supplied 1.4-second episode measurement. This is the same family of offline local-search methods used in the cited Kaggle and AtCoder optimization write-ups. ([Santa's stolen sleigh](https://deepsense.ai/blog/santas-stolen-sleigh-kaggles-optimization-competition/), [AHC059 editorial](https://atcoder.jp/contests/ahc059/editorial/15045))

Beam search is the best second experiment if a useful intermediate state evaluator can be written. Open-loop MCTS is credible, but its main advantage is avoiding a hand-built evaluator; with a deterministic simulator and a fixed opponent script, that advantage is smaller than the cost of repeatedly relearning the same action prefixes. IW/BFWS is worth borrowing for novelty features, not implementing as the next full planner.

## Budget and comparison convention

The repo-measured baseline is the current `tools/plan.py` run: 2,376 scored rollouts and 58.52 minutes at four jobs. The supplied simulator measurement is 1.4 seconds for one complete 720-step episode, or about 1.9 ms per simulator step on one core.

For comparable arithmetic below:

* One **full-episode equivalent (FEE)** is 720 simulator steps, priced at 1.4 seconds of single-core work.
* Ideal eight-core wall time is `FEE × 1.4 / 8 = FEE × 0.175` seconds.
* A 58.52-minute wall budget therefore buys at most `58.52 × 60 × 8 / 1.4 = 20,064 FEE`.
* Node-based methods may be cheaper than a terminal rollout. Their one-step node budget is shown as `FEE × 720`; 20,064 FEE is 14,446,080 one-step successor evaluations.

These are ideal lower bounds, not promises. The current planner's observed wall time is much worse than the 1.4-second arithmetic because it repeatedly deep-copies environments, loads continuation agents, and schedules many short rollouts. Any implementation should measure both simulator steps and wall time. The current objective is terminal **margin**, not our own money.

## Source table

| Title | URL | Relevance |
|---|---|---|
| Open Loop Search for General Video Game Playing | [GECCO 2015 paper](https://www.cmap.polytechnique.fr/~nikolaus.hansen/proceedings/2015/GECCO/proceedings/p337.pdf) | Defines open-loop search, compares OLETS/RHEA-style planning, discusses forward models, and names macro-actions as a way to reduce search space. |
| Rolling Horizon Evolutionary Algorithms for General Video Game Playing | [arXiv:2003.12331](https://arxiv.org/abs/2003.12331) | Gives the RHEA loop, population/individual parameters, heuristic fitness, parallelisation argument, and failure sensitivity to parameter choices. |
| Population Seeding Techniques for Rolling Horizon Evolution | [arXiv:1704.06942](https://arxiv.org/abs/1704.06942) | Tests one-step-lookahead and MCTS population seeding against vanilla RHEA on 20 GVGAI games. |
| Statistical Tree-based Population Seeding for Rolling Horizon EAs | [arXiv:2008.13253](https://arxiv.org/abs/2008.13253) | Documents the waste of creating/evolving a population in a short budget and a tree-seeded RHEA variant. |
| Enhancements for Real-Time MCTS in GVGP | [arXiv:2407.03049](https://arxiv.org/abs/2407.03049) | Covers open-loop MCTS, terminal/non-terminal evaluation, tree reuse, novelty pruning, deterministic-game detection, and rollout failure modes. |
| Parallelizing Monte Carlo Tree Search | [Steinmetz & Gini, ResearchGate full text](https://www.researchgate.net/publication/348085756_More_Trees_or_Larger_Trees_Parallelizing_Monte_Carlo_Tree_Search) | Describes root-parallel independent trees and why MCTS is a natural multi-core workload. |
| Width-Based Planning for General Video-Game Playing | [AAAI PDF](https://cdn.aaai.org/ojs/12786/12786-52-16303-1-2-20201228.pdf) | Defines IW(1)/IW(2) novelty pruning and reports GVGAI results against sample MCTS/OLMCTS. |
| VGDL and the GVGAI Framework, chapter 2 | [GVGAI book PDF](https://gaigresearch.github.io/gvgaibook/PDF/chapters/ch02.pdf) | Records actual GVGAI contest winners, including YBCriber's Iterative Widening and the two-player planning track. |
| Width Based Planning | [Nir Lipovetzky project page](https://nirlipo.github.io/project/width-based-planning/) | Connects novelty search and BFWS to simulator domains including GVGAI and states the exploration/exploitation combination. |
| Best-First Width Search in the IPC 2018 | [project page](https://nirlipo.github.io/publication/frances-2018-best/) | Describes BFWS as novelty exploration plus goal-directed heuristic exploitation, including black-box simulators. |
| Introduction to Heuristics Contest editorial | [AtCoder PDF](https://img.atcoder.jp/intro-heuristics/editorial.pdf) | Practical beam-search, local-search, neighborhood-design, local-optimum, and score-shaping advice from AtCoder. |
| AHC042 editorial | [AtCoder editorial](https://atcoder.jp/contests/ahc042/editorial/12153) | Concrete beam-search progression: beam width, board evaluation, then Zobrist-hash deduplication. |
| Beam search / chokudai search memo | [AtCoder Heuristic Contest Memo](https://jetbead.github.io/AtCoderHeuristicContestMemo/Library/beam_search.html) | Explains top-K beam retention, duplicate/diversity control, Chokudai's per-depth heaps, and inserting longer transitions. |
| AHC059 editorial | [AtCoder editorial](https://atcoder.jp/contests/ahc059/editorial/15045) | Concrete SA neighborhoods—2-opt/reverse, insert/block move, swap, flip—and fast delta/recalculation practice. |
| Santa's stolen sleigh | [deepsense.ai Kaggle write-up](https://deepsense.ai/blog/santas-stolen-sleigh-kaggles-optimization-competition/) | Third-place Kaggle optimization write-up covering hill climbing, SA acceptance, neighborhood design, multi-threading, and long runs. |
| Source code of the prize winners | [Kaggle Traveling Santa write-up](https://www.kaggle.com/competitions/traveling-santa-problem/writeups/wleite-source-code-of-the-prize-winners) | Kaggle winner write-up with segment moves, reconnection, SA tuning, and independent runs with different parameters. |
| Santa 2018 / Prime Travelling Santa | [Kha Vo write-up](https://khavo.ai/kaggle/2019/01/11/santa2018.html) | Shows a high-ranked Kaggle solver starting from a strong route and applying a custom optimizer to the finished solution. |
| Hash Code 2018 local search handout | [PDF](https://upinfo.univ-cotedazur.fr/assets/s1/problem-solving/2-Recherche-Locale_HashCode2018_handout.pdf) | Lists local-search neighborhoods, restarts, local-optimum failure, and the need for a score function. |
| Efficient Black-Box Planning Using Macro-Actions | [IJCAI 2021](https://www.ijcai.org/proceedings/2021/554) | Formal macro-action motivation: depth is exponential, and focused macros can improve black-box planning. |
| Macro-Actions in Planning | [CMU/JAIR background](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume28/coles07a-html/node8.html) | Defines a macro as a sequence of primitive actions and explicitly warns that poor macros increase branching and hurt performance. |

## Method survey

### Beam search with a state hash

Beam search expands action sequences breadth-first, scores the children at each depth, and retains only the best `B`; a state hash prevents the same simulator state from consuming the beam twice. The AtCoder memo gives exactly this definition and recommends hash-based duplicate removal and diversity control. An AHC042 solution improved its result by moving from ordinary beam search to Zobrist-hash deduplication, while the introductory AtCoder material motivates beam search as a way to retain several promising partial solutions instead of committing to one greedy prefix. ([AtCoder memo](https://jetbead.github.io/AtCoderHeuristicContestMemo/Library/beam_search.html), [AHC042 editorial](https://atcoder.jp/contests/ahc042/editorial/12153), [Introduction to Heuristics](https://img.atcoder.jp/intro-heuristics/editorial.pdf))

For this game, beam search has two distinct cost regimes:

1. With an intermediate state evaluator, one successor expansion costs about one simulator step plus feature extraction. For an illustrative branching factor `b=8`, width `B=4`, and depth 720, the search touches `8 × 4 × 720 = 23,040` successor states, only 32 FEE of simulator-step work before Python copying/hash overhead.
2. With terminal margin only, every partial child must be continued to the end to be ranked. The same search becomes 23,040 full-tail evaluations, which is 67.2 minutes ideal on eight cores—over the 58.52-minute budget. A terminal-only beam must stay at roughly `B≤3` for `b=8` (`17,280` children, 50.4 minutes ideal), or use macros.

The required state evaluator is the central risk. Terminal margin is exact but too sparse for ordinary beam ranking; a prefix evaluator could combine current margin, liquidated shed value, cash, capacity pressure, and a continuation-value estimate, but its weights are an additional optimization problem. AtCoder's introductory material makes the same point in a different contest: an intermediate score must correlate with the final objective, and changing the evaluation can matter more than adding raw repetitions. ([Introduction to Heuristics](https://img.atcoder.jp/intro-heuristics/editorial.pdf))

The failure mode is beam collapse: hash deduplication removes exact duplicates but not near-duplicates, so a badly shaped evaluator can fill all `B` slots with variants of the same bad plan. The AtCoder memo explicitly warns about loss of diversity and suggests multiple small beams or partitioned beams. A fixed width also wastes budget late in the episode and underspends it early; dynamic width or Chokudai-style anytime scheduling is a better fit. ([AtCoder memo](https://jetbead.github.io/AtCoderHeuristicContestMemo/Library/beam_search.html))

### Rolling-Horizon Evolutionary Algorithm (RHEA)

RHEA encodes a candidate action sequence of length `L`, simulates it with a forward model, scores the reached state, evolves a population, and executes the first action of the best sequence before replanning at the next game step. The published baseline uses population size `P`, individual length `L`, elitism, parent selection, crossover, and mutation; it also calls out that each individual is independent and therefore easy to parallelise. ([RHEA paper](https://arxiv.org/pdf/2003.12331))

RHEA can use terminal margin if `L` reaches the end of the episode. For shorter `L`, it needs a state evaluator at the horizon; the GVGAI literature uses a heuristic for non-terminal states because terminal states are often unreachable within the simulation depth. ([Open-loop search paper](https://www.cmap.polytechnique.fr/~nikolaus.hansen/proceedings/2015/GECCO/proceedings/p337.pdf), [MCTS enhancements paper](https://arxiv.org/abs/2407.03049))

The budget problem is severe for a literal 720-step rolling RHEA. With `P=32` and `G=8` generations, it evaluates `P × G × 720 = 184,320` candidate sequences before accounting for the fact that early candidates have long tails. Pricing each conservatively as one FEE gives 8.96 hours ideal on eight cores. To stay inside 58.52 minutes, a literal rolling implementation must keep `P×G≤27` at every step—for example `P=9,G=3`, only 19,440 candidate evaluations. That is a tiny evolutionary population for a 720-decision problem. A one-shot 20,000-candidate evolutionary search is affordable, but it is better described and engineered as whole-trace evolutionary local search, not standard RHEA.

Useful variants are seeded RHEA and shift-buffer RHEA. The seeding paper reports that one-step-lookahead and MCTS seeds can improve over random initialization, while the later tree-seeding paper identifies population creation/evolution itself as wasteful and uses a statistical tree to seed part of the population. ([Population seeding](https://arxiv.org/abs/1704.06942), [Statistical tree seeding](https://arxiv.org/abs/2008.13253))

Failure modes are premature convergence, mutation destroying an early action that changes the meaning of all later genes, and a misleading short-horizon evaluator. The RHEA paper reports strong dependence on configuration and notes that different parameter combinations can perform very differently. In our deterministic setting, RHEA also repeatedly re-solves prefixes that a finished-trace optimizer could keep and mutate directly. ([RHEA paper](https://arxiv.org/pdf/2003.12331))

Parallelism is good: evaluate individuals in a process pool, or run independent populations and keep the best. The evolutionary selection step is small and serial; the expensive forward-model evaluations are independent. ([RHEA paper](https://arxiv.org/pdf/2003.12331))

### MCTS with a scripted rollout; open-loop MCTS

MCTS repeatedly selects a tree edge, expands it, rolls out a continuation policy, and backs up the result. Open-loop MCTS stores action-path statistics rather than a full state at every node; the forward model is replayed while traversing the tree. The open-loop GVGP paper describes this representation, and the newer GVGP paper notes that deterministic games have a single successor for each action while nondeterministic games can have several. ([Open-loop search paper](https://www.cmap.polytechnique.fr/~nikolaus.hansen/proceedings/2015/GECCO/proceedings/p337.pdf), [MCTS enhancements paper](https://arxiv.org/abs/2407.03049))

This game can use the current opponent agent and `main.py`/portfolio policy as a scripted rollout. If each simulation continues to terminal, MCTS needs no state evaluation function: one simulation returns exact terminal margin for the fixed opponent/seed. A practical initial budget is 8,000–12,000 terminal simulations (23.3–35.0 minutes ideal); the hard ceiling is 20,064 simulations (58.52 minutes ideal). MCTS becomes more attractive if a short rollout horizon plus a good evaluator makes each simulation much cheaper.

Eight-core root parallelisation is straightforward: build eight independent trees from the same root, then sum root-action visit/value statistics. The parallel MCTS literature distinguishes root, leaf, and shared-tree parallelisation; shared trees need synchronization/virtual-loss machinery, while independent roots have low coordination overhead. ([Parallel MCTS paper](https://www.researchgate.net/publication/348085756_More_Trees_or_Larger_Trees_Parallelizing_Monte_Carlo_Tree_Search))

Failure modes are rollout-policy bias, high variance when promising actions differ only late in the episode, and open-loop prefix duplication. A deterministic game removes stochastic outcome variance, but not the bias from a fixed continuation policy: MCTS may learn which action best helps the script rather than which action best completes a trace. The GVGAI MCTS literature also documents a more basic failure: if terminal states or score changes are not reached, all leaves can receive the same value and search behaves randomly. ([MCTS enhancements paper](https://arxiv.org/abs/2407.03049))

### Iterated Width (IW), novelty search, and BFWS

IW(1) is breadth-first search with a novelty test: discard a newly generated state unless it makes a new atom/feature true. IW(2) keeps a state only when it makes a new pair of atoms true. The GVGAI paper reports that IW(1) beat the sample MCTS and OLMCTS controllers across its tested time windows, with puzzle-like games as the important exception where IW(2) helped. ([Width-Based Planning for GVGAI](https://cdn.aaai.org/ojs/12786/12786-52-16303-1-2-20201228.pdf))

This is not just academic: the GVGAI competition chapter lists YBCriber, a CEEC-2015 winner, as using Iterative Widening with danger avoidance. The same chapter lists OLETS, MCTS, genetic algorithms, BFS, and enhanced MCTS among other winners, so the competition evidence supports width search as one strong component rather than a universal winner. ([GVGAI book chapter](https://gaigresearch.github.io/gvgaibook/PDF/chapters/ch02.pdf))

BFWS adds exploitation: it orders novel states with a goal-directed heuristic. The BFWS literature explicitly frames this as novelty exploration plus heuristic exploitation and includes black-box simulator variants. ([BFWS project](https://nirlipo.github.io/project/width-based-planning/), [BFWS paper page](https://nirlipo.github.io/publication/frances-2018-best/))

IW/BFWS does not require a terminal value function to perform novelty pruning, but it does require a feature/atom representation and a novelty table. BFWS also benefits from a domain heuristic. For Kaggriculture, candidate atoms could be discretized facts such as phase/day, cash bands, shed occupancy bands, crop counts, construction flags, market-price bands, and opponent-visible inventory. The discretization is the hard part: too coarse and all useful states look identical; too fine and nearly every state is novel, so pruning disappears.

The honest budget is node-based: cap the search at 14,446,080 one-step successor evaluations, equivalent to 20,064 FEE and 58.52 minutes ideal. A 1,000,000-node pilot is about 1,389 FEE, or 4.05 minutes ideal before feature/hash overhead. Parallel expansion of one BFS layer is possible, but a novelty table and ordered frontier need synchronization; eight independent roots are simpler but lose sharing. The main failure mode is representation misspecification, followed by novelty exhaustion and little objective exploitation. It is a promising feature-selection experiment, not the next end-to-end planner.

### Finished-trace local search: hill climbing, SA, segment moves, and Chokudai search

Finished-trace local search treats the 720-action trace as the solution vector. One neighbor mutates one action, replaces a segment, swaps two segments, or applies a larger kick. Hill climbing accepts only a higher terminal margin; simulated annealing always accepts improvements and sometimes accepts a worse margin according to a cooling temperature. AtCoder's introductory material explicitly describes hill climbing's local-optimum problem and recommends mixing one-point and two-point moves; its AHC059 editorial uses reverse/2-opt, block insertion, swap, and flip neighborhoods with fast delta or near-linear rescoring. ([Introduction to Heuristics](https://img.atcoder.jp/intro-heuristics/editorial.pdf), [AHC059 editorial](https://atcoder.jp/contests/ahc059/editorial/15045))

This matches the Kaggriculture artifact exactly. Start with a trace produced by `record.py` or `tools/plan.py`, mutate it, replay all 720 actions against the same deterministic opponent, and score terminal margin. No intermediate evaluator is required. A 16,000-evaluation run costs 46.7 minutes ideal; a 20,064-evaluation run consumes the full 58.52-minute ideal budget. Eight independent chains with 2,000–2,508 evaluations each avoid synchronization and preserve multiple basins; keep the best trace across chains.

The Kaggle Santa write-ups are unusually relevant evidence for this shape of offline optimization. A third-place Santa solution describes SA over a finished schedule, explicitly warns that hill climbing gets trapped, and uses non-greedy route moves plus multiple threads; a Santa 2018 gold write-up starts from a strong route and applies a custom optimizer; another Kaggle winner lists segment movement, reconnection, SA tuning, and independent parameterized runs. ([Santa's stolen sleigh](https://deepsense.ai/blog/santas-stolen-sleigh-kaggles-optimization-competition/), [Santa 2018](https://khavo.ai/kaggle/2019/01/11/santa2018.html), [Kaggle winner source](https://www.kaggle.com/competitions/traveling-santa-problem/writeups/wleite-source-code-of-the-prize-winners))

The failure modes are a weak neighborhood, a temperature schedule that either random-walks or freezes, and overfitting one seed/opponent. A single-action replacement is especially weak when setup decisions have delayed effects. Use donor actions from several recorded policies, contiguous segment replacement, short segment swaps, and occasional large kicks. Preserve the best-so-far trace even when the current annealed state is worse. The Hash Code local-search material makes the same operational points: neighborhood choice, restarts, and score computation determine whether local search moves beyond a local optimum. ([Hash Code local search](https://upinfo.univ-cotedazur.fr/assets/s1/problem-solving/2-Recherche-Locale_HashCode2018_handout.pdf))

Chokudai search is an anytime beam variant: keep heaps keyed by depth (or another axis), repeatedly expand whatever heap has time, and allow a node to reach deeper heaps without waiting for an entire layer to finish. The AtCoder memo describes this as the distinction from ordinary beam search and notes that the key can be a multi-step transition, which is useful for macro-actions. It needs a state evaluator to prioritize nodes; terminal margin alone turns it into an expensive delayed-ranking search. ([AtCoder beam/chokudai memo](https://jetbead.github.io/AtCoderHeuristicContestMemo/Library/beam_search.html))

### Macro-actions / options

A macro-action is a sequence of primitive actions treated as one planning transition. Applying it advances the simulator through the whole sequence, reducing effective depth; options are the broader reinforcement-learning term for temporally extended behavior. The planning literature warns that good macros expose useful deeper states, while poor macros increase branching and reduce performance. ([Macro-Actions in Planning](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume28/coles07a-html/node8.html), [Efficient Black-Box Planning Using Macro-Actions](https://www.ijcai.org/proceedings/2021/554), [Option-Critic](https://arxiv.org/abs/1609.05140))

Kaggriculture has natural macro candidates: repeat a harvest/sell cycle, execute a known build/buy sequence, run a crop-management policy for one day, or hand control back to a portfolio policy until a phase boundary. If 24 primitive turns become one macro, the 720-step horizon becomes 30 macro decisions. An illustrative beam with six macros and width 32 expands `6 × 32 × 30 = 5,760` macro successors. With an intermediate macro-boundary evaluator, that is 138,240 primitive steps, or 192 FEE (33.6 seconds ideal); with terminal-only scoring it is 5,760 FEE (16.8 minutes ideal).

The macro library is the risk. A macro that crosses a market or capacity threshold can commit the trace to a bad state, and a fixed-length repeat macro may miss a one-turn intervention. Use interruptible macros with explicit termination conditions and always retain primitive `PASS`/portfolio actions as escape edges. Macro-actions are a later multiplier for beam, MCTS, or RHEA—not a standalone answer until the useful repeatable phase routines are measured.

## Method comparison

The numbers below are planning budgets, not claimed win-rate requirements. “Evaluations needed” means the amount of search work to run a meaningful first experiment and the maximum that fits the old wall budget. For terminal methods, one evaluation is one complete candidate trace. For node methods, one evaluation is one successor plus feature/score calculation unless stated otherwise.

| Method | Evaluations needed | Needs state eval fn? | Parallelism | Wall-time estimate at 1.4 s/episode on 8 cores | Failure modes |
|---|---:|---|---|---:|---|
| Beam + state hash, `b=8,B=4,D=720` | 23,040 successor nodes = 32 FEE; terminal-only version = 23,040 FEE | Yes for the cheap version; no only if every child gets a terminal continuation | Expand children per layer; hash/frontier merge is the synchronization point | ~5.6 s ideal for 32 FEE of step work; 67.2 min terminal-only | Bad evaluator, beam collapse, near-duplicate states, fixed-width waste |
| RHEA, literal rolling `P=32,G=8,D=720` | 184,320 candidate evaluations; ≤20,064 FEE budget means `P×G≤27` | Yes for short `L`; terminal margin works for full tail | Individuals/populations are independent; selection is serial and cheap | 8.96 h conservative at 184,320 FEE; `P=9,G=3` is 19,440 FEE = 56.7 min | Premature convergence, short-horizon deception, parameter sensitivity, repeated prefix work |
| Open-loop MCTS with scripted rollout | 8,000–12,000 terminal simulations for pilot; 20,064 max | No with full terminal rollout; yes for truncated rollout | Root-parallel: 8 independent trees, aggregate root stats; shared tree needs locks/virtual loss | 23.3–35.0 min pilot; 58.52 min at 20,064 | Script bias, high variance/late rewards, repeated deterministic prefixes, weak value ties |
| IW(1)/IW(2) novelty search | Budget in nodes: 1,000,000-node pilot; 14,446,080-node ceiling = 20,064 FEE | No terminal value fn for novelty; yes feature/atom representation; BFWS also wants heuristic | Parallel frontier expansion is possible; independent roots are simpler but duplicate work | ~4.05 min pilot; 58.52 min at ceiling, ideal | Wrong features, novelty exhaustion, no objective exploitation, memory/frontier growth |
| BFWS | Same 1,000,000–14,446,080 node budget, ordered by novelty plus heuristic | Needs novelty representation and a state heuristic for exploitation | Same as IW, with more ordering/synchronization | Same node-based estimate: ~4.05 min pilot to 58.52 min ceiling | Heuristic plateaus, over-aggressive novelty pruning, feature discretization |
| Finished-trace hill climb / SA | 16,000–20,064 complete trace evaluations | No; exact terminal margin is sufficient | 8 independent chains, 2,000–2,508 evaluations each; reduce to best trace at end | 46.7–58.52 min ideal | Local optima, weak mutations, frozen/random temperature, seed/opponent overfit |
| Chokudai search | Budget by node expansions; cap at 14,446,080 one-step nodes or 20,064 terminal candidates | Yes to prioritize heaps; terminal-only is inefficient | Independent heaps/roots or coarse-grained worker batches; merge periodically | Up to 58.52 min at the cap | Heap starvation, evaluator bias, duplicate work, insufficient diversity |
| Macro-action planner, 24-step macros, 6 choices, `B=32` | 5,760 macro successors; 192 FEE with boundary eval, or 5,760 FEE terminal-only | Usually yes at macro boundaries; terminal-only is possible | Macro successors and independent roots parallelise well | 33.6 s ideal with boundary eval; 16.8 min terminal-only | Bad macro library, missed interrupts, threshold-crossing commitments, branching inflation |

## Recommendation

Implement **finished-trace simulated annealing with portfolio-seeded segment mutations** next.

It is the only surveyed method that directly optimizes the object we submit, uses the corrected terminal margin without inventing a surrogate, and turns all eight cores into independent search rather than serial action commitments. It also follows the pattern repeatedly described by AtCoder and Kaggle optimization practitioners: start from a strong feasible solution, use several neighborhood scales, accept occasional regressions, and keep the best solution. ([AtCoder SA editorial](https://atcoder.jp/contests/ahc059/editorial/15045), [Santa Kaggle write-up](https://deepsense.ai/blog/santas-stolen-sleigh-kaggles-optimization-competition/))

### Minimal implementation sketch

Create a new `tools/trace_sa.py`; leave `main.py` and `tools/plan.py` unchanged.

Suggested functions and existing helpers:

```text
decode_blob(path)              # reuse the zlib/base85 format from bake.py
encode_blob(actions, path)     # same compact JSON -> zlib -> base85 format
record_seed_traces(seed, opp)  # call record.record_episode for main.py and portfolio files
score_trace(actions, seed, opp) # deepcopy env; replay 720 actions; return terminal margin
mutate_trace(actions, donors, rng)
anneal_chain(seed_trace, donor_traces, seed, opp, budget, rng_seed)
```

Use `record.record_episode()` to create donor blobs, `bake.load_blob()` to decode them, `plan._load()` and `plan._call()` to load/call the fixed opponent, and `plan._margin(env, False)` for the exact terminal margin. Finish with `bake.bake_blob()`; do not call `plan.plan()` because it is the action-by-action planner being replaced for this experiment.

The loop should be:

```text
current = strong recorded trace
best = current
current_score = score_trace(current)
best_score = current_score
for i in range(budget):
    candidate = mutate_trace(current, donors, rng)
    candidate_score = score_trace(candidate)
    temperature = T0 * (T1 / T0) ** (i / max(1, budget - 1))
    if candidate_score >= current_score or random() < exp((candidate_score-current_score)/temperature):
        current, current_score = candidate, candidate_score
    if candidate_score > best_score:
        best, best_score = candidate, candidate_score
return best
```

Use eight processes with independent RNG seeds. Start with 8 × 2,000 = 16,000 evaluations; expand to 8 × 2,508 = 20,064 only if measured throughput is close to the supplied 1.4-second figure. Mutation mix: roughly half one-step donor replacement, one quarter contiguous donor-segment replacement, and one quarter segment swap/block move or a larger kick. Donor traces should be recorded with `tools/record.py` from `main.py` and the existing `.sweep` policies; the baseline output from `tools/plan.py` can be another donor. Keep action schemas from real recorded traces so mutations remain loader-safe.

After selecting `best`, write the blob, call `tools/bake.py`/`bake_blob()` to produce the standalone replay agent, and run the existing trace verification. The acceptance test is: exact terminal margin is strictly better than the input trace on the planning seed; the baked trace reproduces the chosen action stream and score; then the normal gate evaluates both seat orders on held-out seeds. Do not submit from a single-seed improvement.

### Why not the others first?

Beam and Chokudai need a trustworthy prefix evaluator. RHEA spends its budget replanning 720 prefixes. MCTS avoids the evaluator but spends the budget estimating action values that the deterministic trace can instead optimize directly. IW/BFWS needs a nontrivial feature abstraction and is best treated as a later novelty component. Macro-actions can multiply whichever planner wins, but their library should be learned from measured day/phase traces first.
