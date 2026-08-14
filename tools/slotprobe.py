"""Market order-slot pressure probe.

The env accepts only `maxMarketOrdersPerTurn` (10) orders per turn and `_market`
appends purchases LAST, so a turn that fills up on SELL/HIRE silently buys
nothing. This answers: how often are we at the cap, and how often does that cost
us a purchase we wanted?

    python tools/slotprobe.py [--seed 7] [--opp starter] [--set NAME=VALUE ...]
"""
import argparse
import collections
import importlib
import sys

sys.path.insert(0, ".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--opp", default="starter")
    ap.add_argument("--set", action="append", default=[],
                    metavar="NAME=VALUE", help="override a main.py constant")
    args = ap.parse_args()

    import main as agent_mod
    for pair in args.set:
        name, _, value = pair.partition("=")
        setattr(agent_mod, name, eval(value))

    real_market = agent_mod._market
    log = []

    def spy(*a, **kw):
        orders = real_market(*a, **kw)
        # a = (farm, private, scan, day, hour, prices, todo, build_want[, wheat_pickup])
        log.append((a[3], a[4], [o[0] for o in orders]))
        return orders

    agent_mod._market = spy
    from kaggle_environments import make
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": args.seed}, debug=True)
    env.run([agent_mod.agent, args.opp])
    mine, theirs = (s.reward for s in env.steps[-1])

    cap = 10
    full = [row for row in log if len(row[2]) >= cap]
    starved = [row for row in log if len(row[2]) >= cap
               and not any(t.startswith("BUY") for t in row[2])]
    verbs = collections.Counter(t for _, _, ts in log for t in ts)
    by_day = collections.Counter(d for d, _, ts in starved)

    print(f"seed {args.seed}  us={mine:.0f}  opp={theirs:.0f}")
    print(f"turns logged        {len(log)}")
    print(f"turns at {cap}-order cap {len(full)}  ({100*len(full)/max(1,len(log)):.1f}%)")
    print(f"  of those, zero BUY {len(starved)}")
    print("orders by verb     ", dict(verbs.most_common()))
    if by_day:
        worst = sorted(by_day.items(), key=lambda kv: -kv[1])[:8]
        print("starved turns by day", worst)


if __name__ == "__main__":
    main()
