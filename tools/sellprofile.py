"""Profile executed market sales in one fixed Kaggriculture episode."""
import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.eval import load


def executed_sell(prev, current, item):
    """Estimate actual SELL units from the shed transition.

    End-of-day drops happen in the same transition, so include inventories
    visible in the previous frame when the day rolls over.

    ESTIMATE, NOT A COUNT. The shed delta also moves for BUY_PRODUCT, PICKUP,
    PLACE and FEED in the same turn, so the `requested -> executed` line below
    UNDERSTATES executions whenever we buy or pick up the same item we sell.
    Measured 2026-08-14: this reported `WHEAT 330->198` while the environment's
    own order loop recorded 325 attempts, 324 successes, 1 rejection. Do not
    chase a gap seen here without confirming it by instrumenting `_commit_unit`
    in the environment source. See also: the OPP column is unreliable for the
    same reason.
    """
    if prev is None:
        return 0
    old = prev["private"]["shed"].get(item, 0)
    new = current["private"]["shed"].get(item, 0)
    dropped = 0
    if current.get("day") != prev.get("day"):
        dropped = sum(inv.get(item, 0) for inv in prev["private"].get("inventories", []))
    return max(0, old - new + dropped)


def profile(me, opp, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([me, opp])
    if len(env.steps) != 720 or any(str(s.status) != "DONE" for s in env.steps[-1]):
        raise RuntimeError(f"episode did not complete: {len(env.steps)} frames")

    products = list(env.steps[0][0]["observation"]["market"]["prices"])
    stats = [{"requested": Counter(), "sold": Counter(), "price": Counter(),
              "revenue": Counter(), "daily": defaultdict(float)} for _ in range(2)]
    for i, frame in enumerate(env.steps):
        for p, state in enumerate(frame):
            obs = state["observation"]
            prev = env.steps[i - 1][p]["observation"] if i else None
            orders = Counter()
            for order in (state.get("action") or {}).get("market", []) or []:
                if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
                    orders[order[1]] += int(order[2])
            for item, requested in orders.items():
                executed = min(requested, executed_sell(prev, obs, item))
                price = obs["market"]["prices"][item]
                stats[p]["requested"][item] += requested
                stats[p]["sold"][item] += executed
                stats[p]["price"][item] += executed * price
                stats[p]["revenue"][item] += executed * price
                stats[p]["daily"][obs["day"]] += executed * price
    return env, products, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--me", default="main.py")
    ap.add_argument("--opp", default="bench/v16_rc5_high_score_8c_4s_premium_market_.py")
    ap.add_argument("--seed", type=int, default=1000)
    args = ap.parse_args()
    env, products, stats = profile(load(args.me), load(args.opp), args.seed)

    print(f"seed {args.seed}: {args.me} vs {args.opp}")
    for p, label in enumerate(("ME", "OPP")):
        print(f"\n{label}  product          sold  mean price  revenue")
        for item in products:
            sold = stats[p]["sold"][item]
            mean = stats[p]["price"][item] / sold if sold else 0
            print(f"{label:3}  {item:<12} {sold:8d}  {mean:10.1f}  ${stats[p]['revenue'][item]:8,.0f}")
        mismatches = [(item, stats[p]["requested"][item], stats[p]["sold"][item])
                      for item in products if stats[p]["requested"][item] != stats[p]["sold"][item]]
        if mismatches:
            print("  requested -> executed: " + ", ".join(
                f"{item} {requested}->{sold}" for item, requested, sold in mismatches))

    daily = [stats[p]["daily"] for p in (0, 1)]
    max_revenue = max((max(d.values(), default=0) for d in daily), default=0)
    scale = max_revenue or 1
    print("\nDaily revenue (each # is 1/20 of the largest day):")
    print("day | ME                         | OPP")
    for day in range(max((max(d, default=0) for d in daily), default=0) + 1):
        cells = []
        for d in daily:
            value = d[day]
            width = max(1, round(20 * value / scale)) if value else 0
            cells.append(f"{'#' * width:<20} ${value:7,.0f}")
        print(f"{day:02d}  | {cells[0]} | {cells[1]}")

    print("\nFinal money:")
    for p, label in enumerate(("ME", "OPP")):
        money = env.steps[-1][p]["observation"]["farms"][p]["money"]
        print(f"  {label}: ${money:,.0f}")


if __name__ == "__main__":
    main()
