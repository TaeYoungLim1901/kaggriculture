"""When during the day does each player sell?

Market inventory persists across turns (only prices are recomputed), so the
player who sells at the earlier hour meets an undrained market. This prints the
turn-of-day histogram of SELL orders per product per player.
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

from kaggle_environments import make

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.eval import load


def sell_hours(me, opp, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([me, opp])
    # steps[i].action answers steps[i-1].observation -- see docs/FRAMEWORK.md 5.
    hist = [defaultdict(lambda: [0] * 24) for _ in range(2)]
    for i in range(1, len(env.steps)):
        for p, state in enumerate(env.steps[i]):
            hour = int(env.steps[i - 1][p]["observation"].get("hour", 0) or 0)
            for order in (state.get("action") or {}).get("market", []) or []:
                if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
                    hist[p][order[1]][hour] += int(order[2])
    return env, hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--me", default="main.py")
    ap.add_argument("--opp", default="bench/v16_rc5_high_score_8c_4s_premium_market_.py")
    ap.add_argument("--seed", type=int, default=1000)
    args = ap.parse_args()
    env, hist = sell_hours(load(args.me), load(args.opp), args.seed)

    print(f"seed {args.seed}  units sold by turn-of-day\n")
    for p, label in enumerate(("ME ", "OPP")):
        items = sorted(hist[p], key=lambda k: -sum(hist[p][k]))
        print(f"{label}  {'product':<12} " + " ".join(f"{h:>4}" for h in range(24)))
        for item in items:
            row = hist[p][item]
            print(f"{label}  {item:<12} " + " ".join(f"{n:>4}" if n else "   ." for n in row))
        first = {item: next((h for h, n in enumerate(hist[p][item]) if n), None)
                 for item in items}
        print(f"{label}  earliest sell hour: " +
              ", ".join(f"{i}@{h}" for i, h in first.items() if h is not None) + "\n")

    for p, label in enumerate(("ME ", "OPP")):
        print(f"  {label} final ${env.steps[-1][p]['observation']['farms'][p]['money']:,.0f}")


if __name__ == "__main__":
    main()
