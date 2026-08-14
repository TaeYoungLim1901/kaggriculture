# KAGGRICULTURE

Agent for the Kaggle [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) simulation
competition. Two farms, 720 turns, one dynamic market, most coins wins.

There is no dataset to download — the environment ships inside `kaggle-environments`, and the only
external "data" that matters is the public replay of every episode top players have ever run.

## Layout

| Path | What |
| --- | --- |
| `AGENTS.md` | **Working rules — read first.** Model routing, environment quirks, iteration loop. |
| `main.py` | The submission. `agent(obs)` + a `demo()` self-check (`python main.py`). |
| `tools/eval.py` | Paired local evaluation, both seats on the same seeds (`--seed0` picks the panel). |
| `tools/sellhours.py` | Units sold per turn-of-day per player — how the market timing war is going. |
| `tools/replay.py` | `fetch`/`report` on public top-player replays: build order, composition, sell cadence. |
| `tests/test_invariants.py` | Determinism, never-raises, action schema, and the **per-verb no-op table**. |
| `bench/` | Public top-scorer agents extracted from their notebooks — opponents to beat. |
| `docs/META.md` | What the leaderboard actually does, plus the market/production math. |
| `docs/GAME_SPEC.md`, `docs/GETTING_STARTED.md` | Competition-provided rules and Kaggle CLI workflow. |
| `CONTEXT.md` | Condensed competition rules + source links. |
| `research/notebooks/` | Pulled top-scorer notebooks (`.ipynb` and flattened `.py`). |

## Quick start

```bash
pip install --no-deps -U kaggle-environments     # --no-deps: pygame has no Python 3.14 wheel
python main.py                                   # self-check vs the built-in starter agent
python tools/eval.py --games 6                   # vs starter, both seats
python tools/eval.py --opp bench/v16_rc5_high_score_8c_4s_premium_market_.py --games 6
```

## Status

Holdout panel, 8 seeds × both seats: `python tools/eval.py --opp <X> --games 8 --seed0 90001`.

| Matchup | Result |
| --- | --- |
| solo economy vs `pass` | mean margin **+$75,190**, worst +$37,649 |
| vs built-in `starter` | 16W-0L, mean +$86,613 |
| vs `bench/v16_rc5…` (public top trace agent) | **0W-16L**, mean −$93,870 |
| vs the previous version (`bench/prev_v1.py`) | **16W-0L**, worst +$2,881 |

The agent is fully reactive — no hard-coded action trace — and derives its whole plan from the
observed board every turn: build/plant targets by set difference, unit→task assignment by exact
minimum-cost bipartite matching, and price-gated chunked selling calibrated to town demand.
It beats the built-in baselines comfortably and still loses to the public replay-trace meta;
`docs/META.md` §5–6 records every measurement, including the negative results.

## Submission

```bash
python tools/package.py          # validates main.py, then writes submission.tar.gz
```

Then upload `submission.tar.gz` by hand at
<https://www.kaggle.com/competitions/kaggriculture/submissions>.

Upload the **tar.gz**, not a bare `main.py`: an identical-code `main.py` upload scored
`SubmissionStatus.ERROR` where the tar.gz was accepted. Submission requires face verification on the
Kaggle account; before that is done, `kaggle competitions submit` streams the whole file and then
fails with `403 Forbidden` on `CreateSubmission`.

`tools/package.py` refuses to package unless `main.py` compiles, exposes `agent(obs)`, plays a full
720-step episode in **both seats** without raising, and emits structurally valid actions on every
step. It never submits — that stays a human action.

## Method

`docs/FRAMEWORK.md` is the transferable part: how ontology, action logic, set algebra, graph matching,
and loop/control engineering map onto agent competitions in general, with the prior-art writeups
(Lux AI, Kore, Halite) that back each choice.
