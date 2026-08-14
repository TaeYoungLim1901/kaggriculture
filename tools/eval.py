"""Paired local evaluation: both seat orders on the same seeds.

    python tools/eval.py                       # main.py vs starter, 6 seeds
    python tools/eval.py --games 30
    python tools/eval.py --opp bench/v16_rc5_high_score_8c_4s_premium_market_.py

Rating on the leaderboard is win/loss only, so WIN RATE is the number that matters;
money margin is printed only as a diagnostic.
"""
import argparse
import concurrent.futures
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILTINS = ("pass", "random", "starter")


def load(spec):
    if spec in BUILTINS:
        return spec
    path = (ROOT / spec).resolve()
    mod_spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(module)
    return module.agent


def play(a, b, seed, steps):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
    env.run([a, b])
    return [float(s.reward or 0) for s in env.steps[-1]]


def result(me, opp, seed, steps, flip):
    pair = (opp, me) if flip else (me, opp)
    rewards = play(*pair, seed=seed, steps=steps)
    mine, theirs = (rewards[1], rewards[0]) if flip else (rewards[0], rewards[1])
    return seed, flip, mine, theirs


def worker(task):
    me_spec, opp_spec, seed, steps, flip = task
    return result(load(me_spec), load(opp_spec), seed, steps, flip)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--me", default="main.py")
    ap.add_argument("--opp", default="starter")
    ap.add_argument("--games", type=int, default=6, help="seeds; each plays both seats")
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
    ap.add_argument("--seed0", type=int, default=1000,
                    help="first seed; change it to get a holdout panel")
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs must be at least 1")

    tasks = [(args.me, args.opp, args.seed0 + i * 7919, args.steps, flip)
             for i in range(args.games) for flip in (0, 1)]
    if args.jobs == 1:
        me, opp = load(args.me), load(args.opp)
        results = [result(me, opp, seed, args.steps, flip)
                   for _, _, seed, _, flip in tasks]
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(worker, tasks))
    results.sort(key=lambda item: (item[0], item[1]))

    wins = losses = ties = 0
    margins = []
    for seed, flip, mine, theirs in results:
        margins.append(mine - theirs)
        wins += mine > theirs
        losses += mine < theirs
        ties += mine == theirs
        print(f"  seed {seed} seat {flip}: {mine:9.0f} vs {theirs:9.0f}  "
              f"{'WIN ' if mine > theirs else 'loss' if mine < theirs else 'tie '}", flush=True)

    n = len(margins)
    print(f"\n{args.me} vs {args.opp}: {wins}W-{losses}L-{ties}T over {n} games "
          f"({wins / n:.0%} win rate), mean margin {sum(margins) / n:+,.0f}, "
          f"worst {min(margins):+,.0f}")
    return 0 if wins > losses else 1


if __name__ == "__main__":
    sys.exit(main())
