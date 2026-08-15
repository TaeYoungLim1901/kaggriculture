"""Executed trades, not requested ones.

`tools/bookprobe.py` reads the orders each player PLACED, which overstates
everything: an order is quoted per unit and abandoned the moment one unit fails
(`kaggriculture.py:600-612`), so a 40-unit SELL can fill 3. This wraps the env's
`_commit_unit`, which is the single place a unit of anything changes hands, and
counts what actually settled, per player, per product, at the price paid.

    python tools/fillprobe.py --me main.py --opp bench/ref_broker_bea.py --seed 90001
"""
import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.eval import load  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--me", default="main.py")
    ap.add_argument("--opp", default="bench/ref_broker_bea.py")
    ap.add_argument("--seed", type=int, default=90001)
    ap.add_argument("--steps", type=int, default=720)
    args = ap.parse_args()

    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as K

    units = [collections.Counter(), collections.Counter()]
    cash = [collections.Counter(), collections.Counter()]
    original = K._commit_unit

    # `env.state[...].observation` hands out copies, so a farm dict cannot be matched
    # against it by identity. `_process_market` is the only caller of `_commit_unit`
    # and it holds the real `farms` list, so wrap that instead and register the two
    # dicts by id for the duration of the call.
    owner = {}
    original_market = K._process_market

    def traced_market(state, env_):
        owner.clear()
        # Both real farm dicts hang off player 0's observation -- `farms` is shared
        # state. Player 1's observation is a copy, so mapping from it matches nothing.
        for pid, farm in enumerate((state[0].observation or {}).get("farms") or []):
            owner[id(farm)] = pid
        return original_market(state, env_)

    def traced(op, item, price, farm, private, market, shed_capacity=100):
        ok = original(op, item, price, farm, private, market, shed_capacity)
        if ok:
            pid = owner.get(id(farm))
            if pid is not None:
                key = f"{op}:{item}"
                units[pid][key] += 1
                cash[pid][key] += price if op == "SELL" else -price
        return ok

    env = make("kaggriculture",
               configuration={"episodeSteps": args.steps, "seed": args.seed})
    K._commit_unit = traced
    K._process_market = traced_market
    try:
        env.run([load(args.me), load(args.opp)])
    finally:
        K._commit_unit = original
        K._process_market = original_market

    for pid, name in ((0, args.me), (1, args.opp)):
        total = sum(cash[pid].values())
        print(f"-- p{pid} {name}   net traded ${total:,}   final ${env.steps[-1][pid]['reward']:,.0f}")
        rows = sorted(cash[pid].items(), key=lambda kv: -abs(kv[1]))
        for key, money in rows:
            print(f"   {key:22} {units[pid][key]:6d} units  ${money:>12,}")
        print()


if __name__ == "__main__":
    raise SystemExit(main())
