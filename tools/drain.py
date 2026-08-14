"""Monte Carlo town-demand and sustainable market sell-rate profile."""
import random

from kaggle_environments.envs.kaggriculture.kaggriculture import (
    MARKET_PARAMS,
    MAX_SHOP_INSTANCES,
    SHOPS,
    TOWN_CENTER_PRODUCTS,
    market_price,
)


DAYS, TURNS, STEPS, RUNS = 30, 24, 720, 10_000
UNLOCK_DAYS, SHOP_TURNS, CENTER_TURNS = 3, 4, 24
PRODUCTS = list(MARKET_PARAMS)
SHOP_NAMES = sorted(SHOPS)


def percentile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo, hi = int(pos), min(len(values) - 1, int(pos) + 1)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


def town_totals(draws):
    total = {p: (DAYS if p in TOWN_CENTER_PRODUCTS else 0) for p in PRODUCTS}
    late = {p: 0 for p in PRODUCTS}
    for unlock_no, shop in enumerate(draws, 1):
        start = unlock_no * UNLOCK_DAYS * TURNS
        multiplier = 2 if len(SHOPS[shop]) == 1 else 1
        for step in range(start, STEPS, SHOP_TURNS):
            for product in SHOPS[shop]:
                total[product] += multiplier
                if step // TURNS >= 20:
                    late[product] += multiplier
    return total, late


def town_schedule(draws, product):
    drain = [0] * STEPS
    if product in TOWN_CENTER_PRODUCTS:
        for step in range(0, STEPS, CENTER_TURNS):
            drain[step] = 1
    for unlock_no, shop in enumerate(draws, 1):
        if product not in SHOPS[shop]:
            continue
        multiplier = 2 if len(SHOPS[shop]) == 1 else 1
        for step in range(unlock_no * UNLOCK_DAYS * TURNS, STEPS, SHOP_TURNS):
            drain[step] += multiplier
    return drain


def final_price(product, rate, drain):
    inventory = MARKET_PARAMS[product]["I0"]
    for step in range(STEPS):
        units = rate / TURNS
        if market_price(product, inventory) > 1:  # _commit_unit: $1 sales add no supply
            inventory += units
        inventory -= drain[step]
    return market_price(product, inventory)


def sustainable_rate(product, drain):
    target = MARKET_PARAMS[product]["base"] * 0.60
    lo, hi = 0.0, 2_000.0
    while final_price(product, hi, drain) >= target:
        hi *= 2
    for _ in range(32):
        mid = (lo + hi) / 2
        if final_price(product, mid, drain) >= target:
            lo = mid
        else:
            hi = mid
    return lo


def main():
    rng = random.Random(20260813)
    totals = {p: [] for p in PRODUCTS}
    late = {p: [] for p in PRODUCTS}
    draws_by_run = []
    for _ in range(RUNS):
        draws = [rng.choice(SHOP_NAMES) for _ in range(MAX_SHOP_INSTANCES)]
        draws_by_run.append(draws)
        total, last = town_totals(draws)
        for p in PRODUCTS:
            totals[p].append(total[p])
            late[p].append(last[p])

    # Use a real unlock path at the sample-median total drain for each product.
    median_draws = {}
    for p in PRODUCTS:
        order = sorted(range(RUNS), key=totals[p].__getitem__)
        median_draws[p] = draws_by_run[order[RUNS // 2]]

    print("product          mean   p10   p50   p90  last10/day  sustainable/day")
    caps = {}
    for p in PRODUCTS:
        drain = town_schedule(median_draws[p], p)
        rate = sustainable_rate(p, drain)
        caps[p] = int(rate)
        target = MARKET_PARAMS[p]["base"] * 0.60
        assert final_price(p, caps[p], drain) >= target
        assert final_price(p, caps[p] + 1, drain) < target
        print(f"{p:<12} {sum(totals[p]) / RUNS:6.1f} "
              f"{percentile(totals[p], .1):5.1f} {percentile(totals[p], .5):5.1f} "
              f"{percentile(totals[p], .9):5.1f} {sum(late[p]) / RUNS / 10:11.2f} "
              f"{rate:16.2f} (cap {caps[p]})")
    print("\nDRAIN = " + repr(caps))


if __name__ == "__main__":
    main()
