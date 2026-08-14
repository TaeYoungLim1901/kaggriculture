"""Kaggriculture submission — reactive baseline v0.

No hard-coded action trace (unlike the public meta, see docs/META.md). Every turn
we rebuild a task list from the observed farm state, assign each unit its nearest
*doable* task, and drip-sell each product at the rate the town consumes it so
prices never collapse.

Build: 4 SHEEP + 8 COW. CARE banks +1 per fed-and-cared day and pays the whole
bank out on the next scheduled production, so slow animals convert care into more
value per wheat: cow (every 2 days) yields ~1.5 milk/day and sheep ~1.33 wool/day
per 1 wheat/day, against a goose's 2 eggs/day. 12 animals also drop 12 free
fertilizer a day, which nothing in town consumes and which sells for ~$90.
"""
import math

CROPS = {
    "WHEAT":      {"seed": 10, "first": 2, "max_day": 4, "ongoing": False},
    "CARROT":     {"seed": 20, "first": 2, "max_day": 3, "ongoing": False},
    "TOMATO":     {"seed": 50, "first": 8, "max_day": 8, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "ongoing": True},
    "MELON":      {"seed": 80, "first": 10, "max_day": 12, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "product": "WOOL"},
}
BUILD = {"COOP": "BUILD_COOP", "PASTURE": "BUILD_PASTURE"}

# Sustainable units/day: the most we can sell all season with the price staying
# above 60% of base, given town consumption. Calibrated by Monte Carlo over the
# shop-unlock randomness in tools/drain.py -- WHEAT and EGG have log glut curves,
# so their price is effectively volume-independent: sell every unit, always.
DRAIN = {"WHEAT": 9999, "EGG": 9999, "STRAWBERRY": 25, "CARROT": 15,
         "MILK": 14, "WOOL": 11, "TOMATO": 10, "FERTILIZER": 6, "MELON": 4}
BASE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
        "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
# Market inventory persists across turns; only prices are recomputed from it, and
# the only thing that refills it is town consumption. So a day's quota sold in one
# order walks its own price down the curve, while the same quota dripped across the
# day rides the refill. Hour 0 is reserved for HIRE (it needs 8 of the 10 order slots).
SELL_HOURS = tuple(range(1, 24))
LAST_DAY = 29                # unsold stock scores nothing, so liquidate

SHED_CAP = 100
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
CASH_FLOOR = 250            # absolute minimum cash
FEED_DAYS = 3               # days of wheat feed to keep funded before any purchase
SEED_BATCH = 3              # max seeds of one crop bought per turn
ANIMAL_PLAN = ["SHEEP"] * 6 + ["COW"] * 8   # 14 structures + 11 crops = 25 tiles
CROP_PLAN = [("MELON", 6), ("WHEAT", 5)]   # crop -> tiles to keep planted
HIRES = 8                   # per day; cost is fib(n), so 8 hands total $54
LAND_TARGET = 1             # quadrants to own; measured: expansion loses money
                            # at our routing efficiency (see docs/META.md §5)
LAND_RESERVE = 1000         # cash kept back after a land purchase
ANIMAL_RESERVE = 0          # animals ahead to hold cash for before seeds/land
PLANT_CAP = False           # cap PLANT tasks at seeds actually on hand
# Task value by priority; strictly dominates travel distance (max ~18 tiles).
PRIO_COST = {0: -900, 1: -700, 2: -500, 3: -300, 4: -220, 5: -120, 6: -260}


def _g(o, k, d=None):
    if isinstance(o, dict):
        return o.get(k, d)
    get = getattr(o, "get", None)
    return get(k, d) if callable(get) else getattr(o, k, d)


def _hungarian(rows, real_cols, tie_costs):
    """Solve rows <= real_cols, allowing rows to use dummy columns."""
    row_count = len(rows)
    column_count = real_cols + row_count
    costs = []
    for row_index, row in enumerate(rows):
        encoded = []
        for column_index, value in enumerate(row):
            encoded.append(
                (math.inf, 0, 0)
                if math.isinf(value)
                else (0, value, tie_costs[row_index][column_index])
            )
        encoded.extend([(1, 0, 0)] * row_count)
        costs.append(encoded)

    # Triples compare lexicographically: first minimize dummy assignments,
    # then actual cost, then the assignment vector encoded in tie_costs.
    zero = (0, 0, 0)
    u = [zero] * (row_count + 1)
    v = [zero] * (column_count + 1)
    matched = [0] * (column_count + 1)
    way = [0] * (column_count + 1)

    for row_number in range(1, row_count + 1):
        matched[0] = row_number
        column = 0
        minimum = [(math.inf, 0, 0)] * (column_count + 1)
        used = [False] * (column_count + 1)

        while True:
            used[column] = True
            row = matched[column]
            delta = (math.inf, 0, 0)
            next_column = 0
            for candidate in range(1, column_count + 1):
                if used[candidate]:
                    continue
                value = costs[row - 1][candidate - 1]
                current = (
                    value[0] - u[row][0] - v[candidate][0],
                    value[1] - u[row][1] - v[candidate][1],
                    value[2] - u[row][2] - v[candidate][2],
                )
                if current < minimum[candidate]:
                    minimum[candidate] = current
                    way[candidate] = column
                if minimum[candidate] < delta:
                    delta = minimum[candidate]
                    next_column = candidate

            for candidate in range(column_count + 1):
                if used[candidate]:
                    matched_row = matched[candidate]
                    u[matched_row] = (
                        u[matched_row][0] + delta[0],
                        u[matched_row][1] + delta[1],
                        u[matched_row][2] + delta[2],
                    )
                    v[candidate] = (
                        v[candidate][0] - delta[0],
                        v[candidate][1] - delta[1],
                        v[candidate][2] - delta[2],
                    )
                else:
                    minimum[candidate] = (
                        minimum[candidate][0] - delta[0],
                        minimum[candidate][1] - delta[1],
                        minimum[candidate][2] - delta[2],
                    )

            column = next_column
            if matched[column] == 0:
                break

        while column:
            previous = way[column]
            matched[column] = matched[previous]
            column = previous

    assignment = [None] * row_count
    for column in range(1, real_cols + 1):
        if matched[column]:
            assignment[matched[column] - 1] = column - 1
    return assignment


def min_cost_assignment(cost) -> list[int | None]:
    """Return each worker's task index, or None when no finite pair is used."""
    worker_count = len(cost)
    if not worker_count:
        return []
    task_count = len(cost[0])
    if any(len(row) != task_count for row in cost):
        raise ValueError("cost must be rectangular")
    if not task_count:
        return [None] * worker_count

    base = task_count + 1
    if worker_count <= task_count:
        weights = [base ** (worker_count - 1 - worker)
                   for worker in range(worker_count)]
        tie_costs = [[task * weights[worker] for task in range(task_count)]
                      for worker in range(worker_count)]
        return _hungarian(cost, task_count, tie_costs)

    # Transpose so the Hungarian core always has no more rows than columns.
    transposed = [[cost[worker][task] for worker in range(worker_count)]
                  for task in range(task_count)]
    weights = [base ** (worker_count - 1 - worker)
               for worker in range(worker_count)]
    tie_costs = [[(task - task_count) * weights[worker]
                  for worker in range(worker_count)]
                 for task in range(task_count)]
    task_to_worker = _hungarian(transposed, worker_count, tie_costs)
    assignment = [None] * worker_count
    for task, worker in enumerate(task_to_worker):
        if worker is not None:
            assignment[worker] = task
    return assignment

def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _step_toward(pos, goal):
    dx, dy = goal[0] - pos[0], goal[1] - pos[1]
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"]
    return ["SOUTH"] if dy > 0 else ["NORTH"]


def _scan(farm):
    """One pass over the board -> everything the planner needs."""
    s = {"empty": [], "weed": [], "plants": [], "animals": [], "structs": []}
    for y, row in enumerate(_g(farm, "tiles", []) or []):
        for x, t in enumerate(row or []):
            if t is None:
                s["empty"].append((x, y))
            elif t == "LOCKED" or not isinstance(t, dict):
                continue
            elif t.get("kind") == "WEED":
                s["weed"].append((x, y))
            elif t.get("kind") == "PLANT":
                s["plants"].append(((x, y), t))
            elif "animal" in t:
                s["animals"].append(((x, y), t))
            else:
                s["structs"].append(((x, y), t))     # built, unoccupied
    return s


def _wanted(scan, seeds):
    """(animals still to buy, structure kinds to build, crop -> tiles to plant)."""
    have = [t.get("animal") for _, t in scan["animals"]]
    todo = list(ANIMAL_PLAN)
    for a in have:
        if a in todo:
            todo.remove(a)
    free = [t.get("kind") for _, t in scan["structs"]]
    build = []
    for a in todo:
        kind = ANIMALS[a]["structure"]
        if kind in free:
            free.remove(kind)
        else:
            build.append(kind)
    planted = {}
    for _, t in scan["plants"]:
        planted[t.get("crop")] = planted.get(t.get("crop"), 0) + 1
    # Uncapped by default: over-requesting sends units to the tiles now and they
    # plant as the 3-per-turn seed drip lands; capping measured 0W-16L on its own.
    # The wasted PLANT no-ops it prevents only appear once ANIMAL_RESERVE starves
    # seeds, so PLANT_CAP is the companion knob to that one.
    plant = {c: min(n - planted.get(c, 0), seeds.get(c, 0)) if PLANT_CAP
             else n - planted.get(c, 0)
             for c, n in CROP_PLAN
             if n - planted.get(c, 0) > 0 and seeds.get(c, 0) > 0}
    return todo, build, plant


def _tasks(scan, day, plant_want, build_want):
    """(priority, pos, action, required_item). Lower priority = more urgent."""
    out = []
    for pos, t in scan["animals"]:
        if not t.get("fed_today"):
            out.append((0, pos, ["FEED"], "WHEAT"))
        if t.get("yield_units", 0) > 0:
            out.append((2, pos, ["HARVEST"], None))
        if not t.get("cared_today"):
            out.append((3, pos, ["CARE"], None))
        if t.get("fertilizer_available"):
            out.append((4, pos, ["COLLECT_FERTILIZER"], None))
    for pos, t in scan["plants"]:
        crop = CROPS.get(t.get("crop"))
        if crop is None:
            continue
        age = day - t.get("planted_day", day)
        if not t.get("watered_today"):
            out.append((1, pos, ["WATER"], None))
        ripe = age >= (crop["first"] if crop["ongoing"] else crop["max_day"])
        if ripe and t.get("yield_units", 0) > 0:
            out.append((2, pos, ["HARVEST"], None))
        # A fertilized+watered production event yields 2 units instead of 1, and
        # only ongoing crops run that code path at all. One FERTILIZER covers 3
        # days; spent on STRAWBERRY it buys ~$200 of fruit, against ~$50 if sold.
        if crop["ongoing"] and t.get("fertilized_until_day", -1) < day:
            out.append((3, pos, ["FERTILIZE"], "FERTILIZER"))
    for pos in scan["weed"]:
        out.append((5, pos, ["DIG"], None))

    jobs = [[BUILD[k]] for k in build_want]
    for crop, n in plant_want.items():
        jobs += [["PLANT", crop]] * n
    for pos, job in zip(scan["empty"], jobs):
        out.append((6, pos, job, None))
    return out


def _assign(units, invs, tasks):
    """Optimal unit->task matching (docs/FRAMEWORK.md §4).

    Greedy nearest-first strands units: one worker standing between two urgent
    tasks takes both away from a worker who could have covered one. This is a
    minimum-cost bipartite matching, so solve it exactly -- Hungarian is O(n^3)
    and costs ~0.5 ms at 12 units x 80 tasks.
    """
    if not units or not tasks:
        return {}
    cost = [[math.inf] * len(tasks) for _ in units]
    for t, (prio, pos, _act, req) in enumerate(tasks):
        for i, upos in enumerate(units):
            if req is not None and invs[i].get(req, 0) <= 0:
                continue                       # precondition fails: no edge
            cost[i][t] = PRIO_COST[prio] + _dist(upos, pos)
    return {i: (tasks[t][1], tasks[t][2])
            for i, t in enumerate(min_cost_assignment(cost)) if t is not None}


def _drip(daily, hour):
    """This turn's share of a daily sell quota, spread evenly over SELL_HOURS.

    Bresenham split: the per-hour shares are integers summing to exactly `daily`,
    so a quota of 4 (MELON) emits four 1-unit orders at evenly spaced hours rather
    than nothing (4 // 23 == 0) or 23 units (max(1, ...)).
    """
    i = hour - SELL_HOURS[0]
    n = len(SELL_HOURS)
    if not 0 <= i < n:
        return 0
    return (i + 1) * daily // n - i * daily // n


def _market(farm, private, scan, day, hour, market_prices, todo, build_want):
    money = _g(farm, "money", 0)
    shed = _g(private, "shed", {}) or {}
    seeds = _g(private, "seeds", {}) or {}
    n_animals = len(scan["animals"])
    orders = []

    if hour == 0:
        orders += [["HIRE"]] * min(HIRES, 10)   # fib pricing: 8 hands = $54 total

    # Price-gated selling (closed loop, docs/FRAMEWORK.md §5). The town drains the
    # market faster than we produce, so prices sit ABOVE base most of the season:
    # a fixed daily cap would leave premium goods rotting in the shed.
    if hour in SELL_HOURS or day >= LAST_DAY:
        panic = sum(shed.values()) > SHED_CAP - 20   # overflow is discarded
        dump = day >= LAST_DAY
        overflow = max(0, sum(shed.values()) - (SHED_CAP - 20)) if panic else 0
        items = (sorted(DRAIN, key=lambda k: BASE[k]) if panic and not dump
                 else sorted(DRAIN, key=lambda k: -BASE[k]))
        for item in items:
            have = shed.get(item, 0)
            if item == "WHEAT" and not dump:
                have -= n_animals * 2      # keep feed in reserve
            if have <= 0 or len(orders) >= 9:
                continue
            price = market_prices.get(item, BASE[item])
            if dump:
                qty = have
            elif panic:
                qty = min(have, overflow)
                overflow -= qty
            else:
                # No price gate. DRAIN is the town's consumption rate, so selling
                # at it is self-stabilising: the town removes what we add. Gating
                # on a low price instead *causes* the glut it means to avoid --
                # stock piles up, the shed passes SHED_CAP, and panic dumps the
                # whole holding at the $1 floor (measured: 154 MILK for $154).
                qty = min(have, _drip(DRAIN[item], hour))
                if qty <= 0:
                    continue
            if qty > 0:
                orders.append(["SELL", item, qty])

    if len(orders) >= 10:
        return orders[:10]

    # Keep enough cash to feed every animal for FEED_DAYS days. Running dry starves
    # the herd (2 unfed days = escape), which is unrecoverable, so this floor is a
    # hard constraint, not a preference.
    wheat_price = market_prices.get("WHEAT", BASE["WHEAT"])
    spend = money - max(CASH_FLOOR, n_animals * wheat_price * FEED_DAYS)
    need_wheat = n_animals * 2 - shed.get("WHEAT", 0)
    if need_wheat > 0 and spend > 0:
        orders.append(["BUY_PRODUCT", "WHEAT", min(need_wheat, 20)])
        spend -= need_wheat * 40

    # Buy an animal as soon as ANY matching structure is vacant. Waiting for the
    # whole build plan to finish starves the herd of capital: seeds and pastures
    # eat the bank while zero animals are earning.
    vacant = {t.get("kind") for _, t in scan["structs"]}
    next_animal = todo[0] if todo else None
    pending = todo
    if next_animal and shed.get(next_animal, 0) == 0             and ANIMALS[next_animal]["structure"] in vacant             and spend >= ANIMALS[next_animal]["cost"]:
        orders.append(["BUY_ANIMAL", next_animal, 1])
        spend -= ANIMALS[next_animal]["cost"]
        pending = todo[1:]
    # Hold cash for the next ANIMAL_RESERVE animals whose structures are still being
    # built, so seeds and land cannot eat the herd's capital. Off by default: at 25
    # tiles it measured 12W-4L against no reserve (the engine is not starved there).
    # It is the EXPANSION fix -- at 2 quadrants the first BUY_ANIMAL slips day 0 ->
    # day 10 -- so it only pays with a larger CROP_PLAN. See docs/META.md §6.
    spend -= sum(ANIMALS[a]["cost"] for a in pending[:ANIMAL_RESERVE])

    # Buy seeds toward the tiles still UNPLANTED. Topping the seed inventory up to
    # `n` ignores what is already in the ground, so it parks n seeds of capital in
    # the shed forever -- $2,000 at 20 STRAWBERRY tiles.
    planted = {}
    for _, t in scan["plants"]:
        planted[t.get("crop")] = planted.get(t.get("crop"), 0) + 1
    for crop, n in CROP_PLAN:
        want = min(n - planted.get(crop, 0) - seeds.get(crop, 0), SEED_BATCH)
        cost = CROPS[crop]["seed"]
        if want > 0 and spend > cost * want:
            orders.append(["BUY_SEED", crop, want])
            spend -= cost * want

    unlocked = len(_g(farm, "unlocked_quadrants", ["NW"]) or ["NW"])
    land = [1000, 2000, 4000]
    if unlocked < LAND_TARGET and unlocked < 4 and spend > land[unlocked - 1] + LAND_RESERVE:
        orders.append(["BUY_LAND"])

    return orders[:10]


def _act(obs):
    seat = int(_g(obs, "player", 0) or 0)
    farms = _g(obs, "farms", []) or []
    farm = farms[seat] if seat < len(farms) else {}
    private = _g(obs, "private", {}) or {}
    day, hour = int(_g(obs, "day", 0) or 0), int(_g(obs, "hour", 0) or 0)
    seeds = dict(_g(private, "seeds", {}) or {})
    shed = _g(private, "shed", {}) or {}
    raw_inv = _g(private, "inventories", [{}]) or [{}]

    scan = _scan(farm)
    units = [tuple(_g(farm, "farmer", [4, 4]))] + [tuple(p) for p in (_g(farm, "hands", []) or [])]
    invs = [dict(raw_inv[i] or {}) if i < len(raw_inv) else {} for i in range(len(units))]
    todo, build_want, plant_want = _wanted(scan, seeds)

    # Errands first: an animal in the shed and wheat in the shed both earn nothing.
    errand = {}
    open_struct = [(p, t.get("kind")) for p, t in scan["structs"]]
    for i, pos in enumerate(units):
        held = next((a for a in ANIMALS if invs[i].get(a, 0) > 0), None)
        if not held:
            continue
        slots = [p for p, k in open_struct if k == ANIMALS[held]["structure"]]
        if slots:
            goal = min(slots, key=lambda p: _dist(pos, p))
            open_struct = [(p, k) for p, k in open_struct if p != goal]
            errand[i] = (goal, ["PLACE", held])

    unfed = sum(1 for _, t in scan["animals"] if not t.get("fed_today"))
    to_carry = max(0, unfed - sum(inv.get("WHEAT", 0) for inv in invs))
    shed_animal = next((a for a in ANIMALS if shed.get(a, 0) > 0), None)
    for i, pos in enumerate(units):
        if i in errand or invs[i]:
            continue
        door = min(SHED_TILES, key=lambda p: _dist(pos, p))
        if shed_animal and any(k == ANIMALS[shed_animal]["structure"] for _, k in open_struct):
            errand[i] = (door, ["PICKUP", shed_animal, shed.get(shed_animal, 0)])
            shed_animal = None
        elif to_carry > 0 and shed.get("WHEAT", 0) > 0:
            n = min(6, shed.get("WHEAT", 0), to_carry)
            errand[i] = (door, ["PICKUP", "WHEAT", n])
            to_carry -= n

    rest = [i for i in range(len(units)) if i not in errand]
    plan = _assign([units[i] for i in rest], [invs[i] for i in rest],
                   _tasks(scan, day, plant_want, build_want))
    plan = {rest[k]: v for k, v in plan.items()}
    plan.update(errand)

    acts = []
    for i, pos in enumerate(units):
        if i not in plan:
            acts.append(["PASS"])
            continue
        goal, action = plan[i]
        acts.append(action if tuple(pos) == tuple(goal) else _step_toward(pos, goal))

    market = _market(farm, private, scan, day, hour, _g(_g(obs, "market", {}) or {}, "prices", {}) or {},
                     todo, build_want)
    return {"farmer": acts[0] if acts else ["PASS"], "hands": acts[1:], "market": market}


def demo():
    """Self-check: survives a full episode and outearns the built-in starter."""
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 7}, debug=True)
    env.run([agent, "starter"])
    mine, theirs = (s.reward for s in env.steps[-1])
    assert [str(s.status) for s in env.steps[-1]] == ["DONE", "DONE"]
    assert mine > 3000, f"lost money: {mine}"
    assert mine > theirs, f"lost to starter: {mine} vs {theirs}"
    print(f"ok  us={mine:.0f}  starter={theirs:.0f}")


# `agent` MUST be the last callable defined in this file. Kaggle loads a submitted
# .py with `exec(code, {})` and then takes `[v for v in env.values() if callable(v)][-1]`
# -- the last callable defined, by position, ignoring its name. With demo() below
# this, Kaggle ran demo() as the agent: a full 720-step episode per turn, which
# scored "Validation Episode failed" (TIMEOUT at frame ~31). Do not append anything
# callable after this point.
def agent(obs):
    try:
        return _act(obs)
    except Exception:
        farms = _g(obs, "farms", []) or []
        seat = int(_g(obs, "player", 0) or 0)
        hands = _g(farms[seat], "hands", []) if seat < len(farms) else []
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in (hands or [])], "market": []}


if __name__ == "__main__":
    demo()
