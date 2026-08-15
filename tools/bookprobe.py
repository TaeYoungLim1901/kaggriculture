"""Shared order-book probe: price/inventory trajectory and BOTH players' orders.

`tools/slotprobe.py` only sees our own `_market` return value. This reads the
finished episode instead, so it shows what the opponent actually put on the book
turn by turn and what the price did as a result.

    python tools/bookprobe.py [--opp bench/v3.py] [--seed 7] [--item WHEAT]
"""
import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.eval import load  # noqa: E402

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
            "WOOL", "FERTILIZER")


def orders_of(step_state):
    action = step_state.get("action") or {}
    if not isinstance(action, dict):
        return []
    return action.get("market") or []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--me", default="main.py")
    ap.add_argument("--opp", default="starter")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--item", default="WHEAT", help="product to trace per day")
    args = ap.parse_args()

    from kaggle_environments import make
    env = make("kaggriculture",
               configuration={"episodeSteps": args.steps, "seed": args.seed})
    env.run([load(args.me), load(args.opp)])
    turns_per_day = int(env.configuration.get("turnsPerDay", 24))

    sold = [collections.Counter(), collections.Counter()]
    revenue = [collections.Counter(), collections.Counter()]
    verbs = [collections.Counter(), collections.Counter()]
    # price seen at the step the order was placed, as an approximation of fill price
    rows = []

    for i, step in enumerate(env.steps):
        obs = step[0]["observation"]
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inv = market.get("inventory") or {}
        for pid in (0, 1):
            for order in orders_of(step[pid]):
                if not isinstance(order, list) or not order:
                    continue
                verbs[pid][order[0]] += 1
                if order[0] in ("SELL", "BUY_PRODUCT") and len(order) >= 3:
                    qty = int(order[2])
                    sign = 1 if order[0] == "SELL" else -1
                    key = order[1] if sign > 0 else "-" + order[1]
                    sold[pid][key] += qty
                    revenue[pid][key] += sign * qty * prices.get(order[1], 0)
        if i % turns_per_day == 0:
            rows.append((i // turns_per_day,
                         prices.get(args.item, 0), inv.get(args.item, 0),
                         dict(sorted(((k, prices[k]) for k in PRODUCTS if k in prices)))))

    print(f"{args.me} vs {args.opp}  seed {args.seed}")
    print(f"final reward: p0 {env.steps[-1][0]['reward']}  p1 {env.steps[-1][1]['reward']}")
    print()
    print(f"day  {args.item}_price  {args.item}_inv")
    for day, price, inv, _ in rows:
        print(f"{day:3d}  {price:11d}  {inv:9d}")
    print()
    print("price by day (all products)")
    header = "day " + " ".join(f"{p[:4]:>5}" for p in PRODUCTS)
    print(header)
    for day, _, _, allp in rows:
        print(f"{day:3d} " + " ".join(f"{allp.get(p, 0):5d}" for p in PRODUCTS))
    print()
    for pid in (0, 1):
        who = args.me if pid == 0 else args.opp
        print(f"-- p{pid} {who}")
        print("   verbs:", dict(verbs[pid].most_common()))
        print("   sold :", dict(sold[pid].most_common()))
        print("   rev~ :", {k: int(v) for k, v in revenue[pid].most_common()})


if __name__ == "__main__":
    main()
