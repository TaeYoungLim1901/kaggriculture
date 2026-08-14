# Finished-trace simulated annealing

`tools/anneal.py` optimizes the 720 recorded actions that the baked artifact
actually executes. It never changes `main.py`, `tools/plan.py`,
`tools/record.py`, or `tools/bake.py`.

## Objective

The default panel is `90001,1000,55555,8919`. A trace score is the mean of the
exact terminal margin `seat0 money - seat1 money` over every panel seed. The
fixed opponent defaults to
`bench/v16_rc5_high_score_8c_4s_premium_market_.py`.

`--holdout` defaults to `2222,31337`. Hold-outs are replayed only after the
search for reporting; they never affect acceptance.

`--both-seats` also replays the trace in seat 1. In that mode the seat-1 result
is represented from the trace's perspective (`seat1 money - seat0 money`) and
averaged with the seat-0 result. The final report compares the seat-0-only and
both-seat rankings. Without the flag, only seat 0 is optimized.

## Donors and mutations

Each run records the default sources with `tools/record.py` at
`--record-seed 90001`:

```text
main.py, .sweep/B7.py, .sweep/M12c.py, .sweep/T10.py, .sweep/W20.py, .sweep/X3c.py
```

`build/portfolio_margin.b85` is loaded as an additional donor. All donor blobs
are decoded with `bake.load_blob()` and validated as 720 action dictionaries.
The strongest donor on the panel becomes the initial `current` and `best`.

Each candidate is made from real donor/current actions:

- 1/2: replace one position from a donor;
- 1/4: replace a contiguous segment from a donor;
- 1/4: move or swap a contiguous block.

Candidates are scored by replaying all panel episodes with the opponent loaded
through `plan._load()` and called through `plan._call()`. Improvements and ties
are accepted. A worse candidate is accepted with
`exp((candidate-current)/T)`, where `T` cools geometrically from `--t0` to
`--t1`. `best` is tracked independently of the annealed `current` state.

The process pool runs independent RNG chains. `--budget` counts donor scoring,
candidate scoring, and the two final hold-out score calls. One trace evaluation
means one complete replay for every panel seed (twice per seed with
`--both-seats`). Progress is throttled to at most one line per second, and the
final rate is printed as evaluations per minute.

## CLI

Typical long run:

```powershell
python tools/anneal.py --out build/anneal_best.b85 --budget 16000 --jobs 8
```

Useful controls are `--seeds`, `--holdout`, `--both-seats`, `--opp`,
`--sources`, `--donor-blobs`, `--record-seed`, `--t0`, `--t1`, and
`--rng-seed`. The output is a compact blob suitable for `tools/bake.py`.

On this machine's Python 3.14 installation, the local Kaggle package is in the
user site directory. The measured invocation set it explicitly before running
the CLI:

```powershell
$env:PYTHONPATH='C:\Users\livde\AppData\Roaming\Python\Python314\site-packages'
python tools/anneal.py --budget 120 --jobs 8 --out build/anneal_smoke.b85
```

## Smoke run

Command: `--budget 120 --jobs 8`, default panel/hold-outs, seat 0 only.

The run recorded six source donors, loaded `build/portfolio_margin.b85`, and
used 120 total trace evaluations. The strongest initial donor was
`build/anneal_donor_B7.b85`.

```text
seed trace: build\anneal_donor_B7.b85  panel=-86565.0
iter   111/111  best=-86473.2 T=100.0 eval/min=27.45
best blob: D:\hackathon\KAGGRICULTURE\build\anneal_smoke.b85  entries: 720
wall: 266.41s  evaluations: 120  evaluations/min: 27.03
holdout means: seed=-83753.5 best=-83683.0

trace                         panel mean   per-seed margin
seed (seat 0)                   -86565.0   90001=-79936, 1000=-59908, 55555=-102085, 8919=-104331
best (seat 0)                   -86473.2   90001=-79936, 1000=-59812, 55555=-101955, 8919=-104190
hold-out seed                 seed trace       best trace
        2222                      -85411           -85270
       31337                      -82096           -82096
```

The smoke best is the best found in 111 candidate iterations after the donor
and reporting evaluations. It is a small experiment, not evidence of robust
generalization: it used one fixed opponent, one 4-seed acceptance panel, no
seat-1 optimization, and no leaderboard submission. The hold-out result is
reported separately and was not used to accept any move. A longer run should
be judged by its held-out panel and both-seat checks, not by this smoke result.

## Bake and loader check

The smoke result was baked with:

```text
entries: 720  agent: D:\hackathon\KAGGRICULTURE\build\trace_anneal_smoke.py  bytes: 31137
```

The baked source was then loaded by file path against the fixed opponent:

```text
last callable: agent (agent)
file-path run: configured_steps=720 frames=720 statuses=['DONE', 'DONE']
```
