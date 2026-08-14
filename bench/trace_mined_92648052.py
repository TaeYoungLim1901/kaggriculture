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
STICKY = False              # keep a moving unit's target until it arrives
# Task value by priority; strictly dominates travel distance (max ~18 tiles).
PRIO_COST = {0: -900, 1: -700, 2: -500, 3: -300, 4: -220, 5: -120, 6: -260}
DIST_WEIGHT = 1
_STICKY_TARGETS = {}
_STICKY_LAST_STEP = None


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
            cost[i][t] = PRIO_COST[prio] + DIST_WEIGHT * _dist(upos, pos)
    return {i: (tasks[t][1], tasks[t][2])
            for i, t in enumerate(min_cost_assignment(cost)) if t is not None}


def _sticky_plan(plan, units, invs, tasks, step):
    global _STICKY_LAST_STEP
    if not STICKY:
        return plan
    if _STICKY_LAST_STEP is not None and step < _STICKY_LAST_STEP:
        _STICKY_TARGETS.clear()
    _STICKY_LAST_STEP = step
    for i in list(_STICKY_TARGETS):
        if i >= len(units):
            _STICKY_TARGETS.pop(i, None)
    for i, old in list(_STICKY_TARGETS.items()):
        if _dist(units[i], old[0]) == 0:
            continue
        closer_feeds = [
            task for task in tasks
            if task[0] == 0
            and (task[3] is None or invs[i].get(task[3], 0) > 0)
            and _dist(units[i], task[1]) < _dist(units[i], old[0])
        ]
        if closer_feeds:
            feed = min(closer_feeds, key=lambda task: _dist(units[i], task[1]))
            for j, assigned in list(plan.items()):
                if j != i and assigned[0] == feed[1]:
                    plan.pop(j)
            plan[i] = (feed[1], feed[2])
            continue
        options = [
            task for task in tasks
            if tuple(task[1]) == old[0]
            and (task[3] is None or invs[i].get(task[3], 0) > 0)
        ]
        if not options:
            continue
        for j, assigned in list(plan.items()):
            if j != i and assigned[0] == old[0]:
                plan.pop(j)
        plan[i] = (old[0], options[0][2])
    return plan


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
        orders += [["HIRE"]] * min(HIRES, 8)   # leave two hour-0 slots for purchases

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

    if hour > 0 and HIRES > 8 and len(orders) < 10:
        hired = int(_g(farm, "hires_today", 8) or 0)
        orders += [["HIRE"]] * min(max(0, HIRES - hired), 10 - len(orders))

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
    tasks = _tasks(scan, day, plant_want, build_want)

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
    plan = _assign([units[i] for i in rest], [invs[i] for i in rest], tasks)
    plan = {rest[k]: v for k, v in plan.items()}
    plan.update(errand)
    _sticky_plan(plan, units, invs, tasks, day * 24 + hour)

    acts = []
    for i, pos in enumerate(units):
        if i not in plan:
            _STICKY_TARGETS.pop(i, None)
            acts.append(["PASS"])
            continue
        goal, action = plan[i]
        if STICKY:
            _STICKY_TARGETS[i] = (goal, action)
        acts.append(action if tuple(pos) == tuple(goal) else _step_toward(pos, goal))

    market = _market(farm, private, scan, day, hour, _g(_g(obs, "market", {}) or {}, "prices", {}) or {},
                     todo, build_want)
    return {"farmer": acts[0] if acts else ["PASS"], "hands": acts[1:], "market": market}




# `agent` MUST be the last callable defined in this file. Kaggle loads a submitted
# .py with `exec(code, {})` and then takes `[v for v in env.values() if callable(v)][-1]`
# -- the last callable defined, by position, ignoring its name. With demo() below
# this, Kaggle ran demo() as the agent: a full 720-step episode per turn, which
# scored "Validation Episode failed" (TIMEOUT at frame ~31). Do not append anything
# callable after this point.
def _reactive_agent(obs):
    try:
        return _act(obs)
    except Exception:
        farms = _g(obs, "farms", []) or []
        seat = int(_g(obs, "player", 0) or 0)
        hands = _g(farms[seat], "hands", []) if seat < len(farms) else []
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in (hands or [])], "market": []}

import base64
import copy
import json
import zlib

_ACTIONS = json.loads(zlib.decompress(base64.b85decode('c%1EB+iqOP5&RcE^TE97k~f-KTZCy*AgKtBAQ%SXAVA<eIC%^5?}7JrE?r$+-7{yGa{Q#lYI)9FdS<$+t9w5E=j3lc{rbz#zn=W*)5-hm$H$Y;rzd~^>7Rf7*U6tgeLg+;<)>f&@$<ib`~2V2@lU`0aC`UW$M@HdPahsu-rsyWd3(G5U+u%!AAb1p`rYmK*LNqUCpY&WPfpLx*N<;ktM{Y-cwDXCoSdF~e7m}SIyrqg`}+IU-Tk|h)3g20-#^^H`Ec_z{KbpUvyQ#Lz4`9L`{7MzqrQDQ`M7#~TDSGx{lnAS^{4$;vk%jOcwF7x4R5`ezjgPx(W^j1#;+Yd&8Gr2K%G6<!+lHEbFyy7{8!{%@9(Z}R^E7`{_Oq$ylvKQ^49I2jK|ZoWBuK`!5Aie-OiNrvv7o0*Yo!e=5hVBdYBv0{JW|3K+`>+8`0zahq)11<NW5gl`;8d);l(pc5tQxJR7B<e>c}#)7<@Nvoc3rPtD~pT=u2AQ5gR!oG!5b(By!XU@VxtWjpp@%tpguX3YLZpRw(@)1jL@cfRt5A+*!v*yWk9xq-#tZmoQ8nRG!LS+wcIlecTBK9=$~@jQYd-0m=7j-q+f2XX(7{fDiKU_RsqZW#BL2hZIVG{k+MPba)f2X=oudQ;cuh98db*x9Lap?RS5%`|a<^m*!hZ_O;<gSTMrkC2}lH=<7qZtm~yRyR*SezSUby1l#o%XClZG<fBgBuu3Ij)mr6cWRH?<F27S5SjhhIm)j-Cp^GsZU2e+o%ivwj&4K$uhAy~?wxTTM@~2}+zQSB&Inu+xK~@#PPxgv598iOeGCT>0Q-bP%AgAT6g`lQ1^N^|kRbxme{8^`ev^v;${$q8_f-}U#pdz+6Qt7yeHG#<d>ll}3Ge`%`{9w+8H^XdB~FNM8MiO>xX@K4yxD;r>pz~>|7r5M4}7RgOkkfiIR%JF7F`W?u(cg=jLmUQ=g>PS9D|V~&`8xu2SXPJ0r8CPp;0^=8M!`e*KMN$UY2<@br!%|y!j7L1kHyixhG_JxYrgxniAB2PD>Ghgy*6o(q)5&R@!yvpL1!yALi_j$NuryBq!y2FX>o42&Owx`M}e<s_dB+ES@AsijXfshO|WwBfqQSpyVi}O#4YlycLDAGu;`Rx7QDU_Bz%|7>&B4Lwzv>jfQI9m*NnO$D&0aU<bzr5cf)eCKiMb`o3eEw<f_1@JIH8G9Iaz%K+ra#Owwe-3`hRu9OFTcp^Gf#_yZ^SE=amPGCV#F7Sr%=mLXeAN=O_+XW6<tDHLeLH@^M4;N^@%D6~Z>m@%?@x9VHAJ>Q4dP<K^57!^RUOhbg0K|b(*od8BZo|Rbjd~}=gv24HX-m4qmgYx5S073bpM~R=@C)bcRXd}U2x739)5oQJrm?#*W~g$M5szgx*~k9F{)~<vr?IfRBX+b5CpIwX>iPv9o8ZQL1d3MR^*i<TrkPb24}ID+v=Z>N=N6Hl3Ciir<0>@YV&b@?hjRXZo;KSgUZj1R19>Vwd0<!C_Ek664-fY!TO!G`EAW`2?}%QhoGXlf7@dM2@9*!{St`(p+WzNuhVHK4{k9d#m^>G)E31c2;iMXA8Pg_o5{t|S)jI%WCw4bE@{re<GvMfeq@UiWeD4q#$$P0Bwh}4S6hGC0N1M>dhJ8ccO5#$@r!xBpnp#laAQE%<RN?9n=Qolc0gthHDI`X~&N<rA=6geBEwHghpOPa3_8&{^&O^^N85MvQGcR>1XXr&G1vMQrgNzG|nq9`u6-*ILdtA#XiXxwBFc+iP+4m;58K4BuY+$S=tF$u%B0!-#>3kizYn&!fcMyQi<E-D@NT%2eAr&!Fr_54bbDknf1E%)QvwCGtL7-pv!6?`s>rAM$W9lp)!gwk1RMI=O@3q^8I2Ub^_LRGgTgT3M-C1;xTc;t3QyDBmy9JPQAGB!pf4TkKJ{b4};fE4H1pRe8RqQaC<4QO4P92%<@ur7db(ei4>}}+`F&}gPnvk%}sr~E_?Dy9F<5;f?d>!cKP#ZyxOV{2F>|K5={7?yiEdI)t;BobpVpgP&JKD8(uQ7^9Rhk*g`0R-Tf0jZNg<J^g?Ck%uMR8XX#qAgEn8)=T``vGaFe-POWpAF!L9u_Zdn;B9m7?Q0>JV&=!*;wqn7_Zh`)+G_9vrg2j8o=XSnutU-n?&9X(~kgXW0n@CX@#M9I8<HNR^RgZZKHcLNS;WtW3s<7$Y0F`w2_~HsC>XId-EAnPH`wIiOV=vi*dOH-=cw>3vFs0gc5OO3dOztEw2)_QI|yLQ=Mscw1~E#KF7+D8UvHs7z)bP>g?CQ7Ql?BLCr|l~~}KV~eft%wSpu)zx?kFlJyL3m<ZlT12Pg<*<0`*aql}xQmp7(jYhxXd!?jE80^QpIEySJ57=XRPIg_cbAy96v<GgLddWJ%7HN)@GqK(q7<G*8myqX;6stZX+++!ek{lCv_}Iaxpy)Sn1|z+-q}xnr`3E~0;dCSC4%WhVw($H>Zm;q#u?{F1Mgj7JWTDuE~yM?<sVAqNfFLl8y*;UYf1fjQcm)mD#yl^K}Mzmd@KNutl(V=w9+szQK#(-lT`5g_&}ZZzbqr<u{kBGMmwAEHLchZl?tK2TG|{c>8oI)V($v*O#z4Z(F{<1lRGky_yCK+r9E0fw?)ywRV7QZ6TKlNLz#0)gRsahl%KicY)`Mil7}P&3|u|XMgLcg`N@hcShrLOOj?JvF7M;ZeCZaaO+eHrw1R^W5-8zFs3dKRAcpO-6WnJg`Uk7Kyz-Evb+A@F)4}Q<^zYKD?z(_ltK`H!nMx=_>R66*ys$jc$yCDfqT5RPp!?66@H}<#gf<J7WlA9>3lJ;akq3PdVJNVSwyKa-C|Qwt0#$1qfQF$q=NZj41fWbKz|_9v-bFCg__hBkHPO!Lgyp(g@iZ8q@k_*bZw~0w)lMJHngRp!lzs$+@awE31=d8;ATbRn6H9cMdR?pzUL4IcZ6f&Nu)S9NQ;d}1W}ub>Wid>=M6G>g10g1Lmz)Aj%gpW8egh`0)c$>@m(9Kqu&gADU`h!vFD$H@=vIQCO9t8pvU(@48{e$h%f2QL4LV2l;$kD=a0sWojoH#JL=)%VPI-0}+au$JX9Mvfm|SpJ(;Q-XMnN?7s>UXR(<C{I*f@x}hEsahh?fASLv0MbCGVO_)ndb5prkK0AJl6>PAd_Gxqu4F-p!N{Z3135Ry#<x6n6Ec>k7xl*4D2ab66x;Q6n4Z6Mx$n>A6Xg_ND|%r^M{@a`FVHZk|gbg?Djq3Y#x3)fjRB+T-LxmbE0{NR%Q0$WtJ380!%A5R6l$K#{D&Xig2uJ$F*yV-_mb?}t_lE*)M6Mih3U5W%+U65g!Ts?8PP6He$?8BK;x`2iSALbqI<-lWh#+GPhZMDb6T_(_LgnKKRaN>UmDwRqzSC5=aC6pWLMN<=Jd9mOy>82O~pZ~))mYW7V4RxT&lgoy@R>CwfYm>N-6&WlAK2rg(hD+0^7K`X6e60I43B5nPr#V+k%W={r6Z~_9(?|12Z3%UXhH?Z?Y`3q>7vza9KXH?UKC_xBbtQeF1O{PR0u@Z4x<mKYf|8_JL<$6?JyUzcbo+tFHZk9s>eLzVi(y_H_hID8tT~EjlUJ0ekDV1V#8b4&_J5S&YY)yN~i=HIR{>yQDUIm=Z@}vx4XR_JeKGmy3Uz8t{QPRlVN>T?AB*N5$G9(aUBa^i%Lix<6_L|I@ToE0y0L!RUUx~P@ShPbh3OIsTd4dEJ=(*~k3Qt8KMcEi8nxB6a2IsCaDF(Wfi{lL+G!<)VQkfQnm5NX+WptK~5WyFNy5b}X`2iLZvUXCUlVu9&!D-}Y%A2B-CxoGOZ5nCNG7?>R(dHiLk;PmYN@rLrs}0Lk`k@2qUyR6{njXVQ;Rd+XFTlM9+7!W3i033`RzY||MtBUOI0++uCqg>M5;aDNw!Mx#T`SKoA=bhS%Gcz6i?p{q&Am)kxPXZs#sJzQcnrucpo5Uwm&MVWwC1(Q#YNV`ZH7JWc0MB5K9~f;LTe~yrWzi0gk~iU7NrdTRSd4nzEy>Hm2x657Dv7ScFLo;xHP}}MI3?EY7v8ycA=4+u~vdcm4C;@Xj&kjC=-~4BodHfte|8IY&Ox25JvEOm_8wF1}f=CTwQm-Vwr85Qr-SvM295OcEYtQYJHhjBArbVqC-V<;6FJ0Bu#Z;PBT^|FpZS;D%4Y;d1w?d_&;l$M9M2rh$CrvD>7=tHPA5$r3#sF84X%flUI%wH$kcW!h)T%K7PIs>4L^6R)@_y{d9C0O=ElF%dHSUF#EGS1E7U@N%;=Cti0~^2&7wxm-;}u6o-Qt-BSzMTA@|GSr!^gLGNNVL72$VGp#}SFjBXA9mzMc78PIL)ZpF5JH_;8$HVS}&7%KBE43poA50TfYjatJM5sc-SvHIaQ&yu`b1SwkW)74?tjY{ESDB!GXgBo&gJb3KA-Fe;<I4p|djNEXWW`YPPGmiSo?mT-cKc1_VvKHER@@~;YOiBevRTX=m?B)2s>f)Wf{wLSNZ2=;x3*duqNctu<RbJ2z$G*2M9hP?;gn{Vby&RtM$I5`K~D|{ItGRj9gR`T%r5hwCF)s>Bp1OOREa6ANlXMqUMskg$&1s`zl%h`KQZV1#(?q;M2hYL@1l=3c2vic!LxI+IUow+E!2RiX{$SHfiIjw`(H%FG6RDS8n8sGB7jYu(zO?eWybru<hH9KV)7vxY~ipZV!wi}7zCc`I&FBKRr2W@CC1irrkDC{ien_kf8?!enqRVy`DI|fN~BY^>cPkJj-7xwD%2<BORw>h0%%x$Cqlf?m3f)bSjIb)gng(4nRYDfj+qgrlcs?-3J62*R$4LH<q<$FwEasOO`_y2v|CYIt9jZCIcc~VH(Fp-#I{l!!cM1n+=(sMMBB{3VS7^Pv~ja1g1jx^r3Zoog(Q<AlI)5AZsCpy(2wh3wZ`I2pX@oETdv8xgWZP;1H@K?dVrbyc)C!TzZ~JkG-rT%Vx|Q8;371Yd>fL~*Rvn?3=o&5L{>3jKaH$byQ2mAnI4vKF620<?X|3gX1&rxkU_@gl9m6fXWih^yXE|cH@Dxe-@f~oMZ~Ede)j-RB(Z46nl5!bpOhvwwA8rvA86w1=NgQ!>E`={<?AS+Pe48b(t5;vnJ7K@VY_^`M}R(TMQ7qincop4o%0556$cuF`2hciv6uO&nTxs=BE1|4&||g`foGxZYH|v!>Rt)Oqo#<may=}hD2>4jriLTA8p~9k(-POEQUlGrC(X3d^9~dPBGbk|6?9^?h+c&TU|^2HpGt&Za%0m$kvP07g_Lbyp~pdG(2ZJDEt}kq3mr~(TGO#$Elf@$@gX`*j~SC>(?;1J#f1!Vg~0eE*wJC8#YvLdIFUM~S>kQ}t1i<>HCN?NhZ0|Vc<+c=(m>gKRE+^p&&nbLauD^<6wp8%a8>l`>KS!J1s%duOaGEb<q9HB88AlwF92-J`nM-y_pfmm`Ke$7mLvIU0Bl>xzE)hU;68hRB<dJ6$+-usaDgQ>Ok?e$q+UW}k>S-zcLioo+oz)^o<-Vu#x!|6jZShL%u#%~-MNHsYWEtLPVWVR+Cwb<Z4oV>2CDDw6V)U%fm#i~k*+Y3qf1;fu}8D*Ow@*`kty^zS)McLr74)<U0+PJFf<Xvp~I+nz%IqnAIBYh*)(TCR5xDi!Uo(rYtBuHYRsKd1g0|#po1T!rb-G~n=Vn!0FP6-R!G-Yj}4?AujV*`ahX_Euol>kA@TIK$Vz9;(;}UVrLvfLdJ+$1TOq?3_wllInj}34>7J*yP;_dUF_$uFQe9|~rZuc1QcqyS^qIQ}$TvVf;hzFx-<G4j&e!~w3pc&>`izor&Yw?>{?RVum*}S%Y67R%CF3SV&Ljf3=BFLfZsc+bftLkgSx4zd|Kk49|I1k;OXlJfa_^&dYyB!FiAOXexfmeGKA>dyVs`|fPab<!TFE>R362g0Hjzs;!NB8@O-zD#+NP3dL{&+^YW47c3<grJCBSJ}fp;8F#Q1Xx+m$Xa@U0YD6rT&}<^YdF(9>!}gBTB_ZJDql(q^PynV!ziLOn)q5aCn{`B{)G(0a%=EWWaF%8ELFzR+qZZbT&xg$pZ_RSz2awZ<$(fevFmXzmZqH-WxoEh9rAe=Ia-aR!a`rYu<?%jgWs?aohAVE6=bZA|YDW^^*ND<+xZz%vzhgvJzw8$BahUls**>{DPs4Z@})EhTpG1--zM_Z88?o9b_T6e^oOcn6=?&I+(Ik0Lu_-p_ExJdgV_kW<8!(W=zyqB|QFY1U+_0OC)XvT#TMTULNMZ6O3sAZJ<EQ&PSNg$Du@QLkB3yb8sQFvt7X>x5xeuFI6?3VG=X6GamVw&0f;cY!f%Ldg-kJQ0*^36$^Qg|Ik@6@#;%P75s>z&OZ?hT}?@M7Eh0Zg%C;GmUIYU?@9z!fl1fXOZNQs`!IDSS?oj(#-LzHe;pIFx64aWb~C)h3G0w+jw=&(PwmsNH@uM(Owsd@HNEAa$_5;P^nQVW!ibCghx8jiL7p(v#JttVKgb_(jE}h965{HhPL#>05R_I+My*r9J5VKmM`WzQ|LjOZ%QHzEXdg;^A#4DQSK~|%BiUr?aAFme9bv((&`<DM#Bjm=A<F4z%m#}&xrnt&Zizb(YG;XQjy5b&LYrJ&HAxqAPck+T(aX|yQ2ui00Gydc2iwBs$GnwUGEciyBr0%=tT2feC6?cUIEvu=UU(A;2EGex>>n_C-gTvsNN#NBP7ofD0kk!Vp=E_hIF~1w)(g^+tQd+8cq)KXG2)2tGxPWjRJ3eibs+ud!a0o`}rb&rN#AP?obrc$6~dXlx61nc<)Q(xcQ!9f$R<Vt{_t-YO7N4hOu9aqxDj>jFSyn+dM^U@C~s536!Wylwxol;$(PLS~NX2VJt|29al$R$m|2mzABlexqwV_q$kan*e7fC9?K*|EE>ss6<rdDM&k&aL*n^yg@B96ky6Ckyv&8S94Kpwwz0VNSAu)5Zh%xA;%u(&x>nJZ!WM;gz+^jF9bsCeE#<b_!!1g(MW4L$AVFyynouGX5u1gbpl3rVUS_7$kD(N~^*PR;HCAT^!_C{yC=xck3I(u*nGR|SJ8X_r<Si?zQ)*hYq%f`tm&WV5MP;WeJ2oBixh|zctyI*6cjCpT4VCh2?nHZL<kZLrKy@-7fJ6*)U&R^AVL_jWxCOR1mt?8rfhL$S&pS~*hh4EpI&s`}QB{rx1G{EJ(PE|26EvPg`d)^`VbdFKi^er(<$f(P!CN@*M<%6LJgt2FP^L^2JemyigMDg%TI8i!$W&vwPTpFzo0$C&<`U|u*LB~K<!@4zzK|11D9=tZ69Fp2Z6csrfT;mLFWdk-Nb&^blievar50XW=rrwWhvrIqPftS<L<6_QSz(%V2mtyvgc@&?#AvlSjn|^YEq0RI2v<JA{ge886lXEjN|zj>%DSYQ8uf(Zv%QR5DpN{poXUyIU@^8jC+TU-3kynWDFm4%b<tOPhynbyT@VW8>Tfm8#nSA|@UBF0C6{~Yqrzl_ADA{HfKxuea|kbht|t0Y;I?=M;w!A&y19OMxYzqn-HO%(##)xXO1P)&)|KSsLsHuju3q;L1itxKOv|tLXMt*JF2^?wuRc@y?(jLJ*d8XEkX!$a?B~Z)mxcH#!@X%jGu0z6E6~7ye&I5+1?u@9LvjZ8K95JEP=g%>jmohg>5pSM9~N~}iY0W243MdG>$38(oc5JwEQZ6J)R9RjgNh__GPj~yjD8i39)~%d<X{eCj%9*q7{T9@X6AHXflei?iN$$V8>mgFywIS;cZtO;BgtkHRCdi8uc#@M|HXg2gO7R6S4HNE_De$qJT)0WL1>|c*gr5eE=!5jRX)qdsq6%kQh;rc%A{1mNJ<1Y+E9{HQnx9ED2DOf*|(D7MIv2bgHWE>66m@TxRTkN2<7{LlW4a9g}f~%d0p1BLCNG$IkCogcE}UYU#AGyo9)7$;bZO!SNJxRJ#8phNcT2ih@e=Ruhj!Nr1Qb(O5r*4e10sQ7%G!?{#==+XC@Tmax7X2WFe&(jRaD1CL+v=S&CKFSg2y>GXEC9pI3+po$UUX3lIfdw$rR~^XZXrgB1elie3zz8p6Z?H>MDrTyJ0+=?ZpGNiL@8+DLjBnxbx(S5^@!G)o5w#5t#F3PwZ^>;g+A0U{9a2s~mR-560Sx|5>oN<G61Ky50N+FWdjM2G?v3d($dX11_mER`om$!c9x+ov>Lr&}@c_D$HiU=oqpr;-6{<(aH!#XLQP-B4FEw0a+HEdX`Ue+xz&{*CkZw%^J53a7&E&93x|@{&GM4>W<L)VZ{>hA2#c<w0-U(_%8JiLBrQ*F0i7CX1D@kkLZ9tyk@xj3{Rs>|idpufi(yHy~N$aVW{gplN3GbHI?)K^Pwz(}w9XT>By5e}ygympF8}*NL~CD&5#xCCSQ4nSzBVy+|qcyWsQ$c5Er}7@>UJgip#swu!?K_?0z9A)^t}c*ARP2!*b^f+`I=Zb@Fto@7kf#TI_^09RyaOsFN_4a#H4k^ftOj=*NATL2Iy*tIM2M8a0MG=fqEh6luAQ3=bG1a`@2p3H7wf19#KCdP{Q7YeEcS6<HrLk7>&;IWe+jAFc~;X`=Ed9cPki=>FQ(ISHcNU*k}0i}?E?c&xCry4A`_7SteP?Z~wAv_@gBSXB&SV`sba;Z}=T%^L`%|I%Zh_NBn>H)x!rbHLlnou?=9gb493}DU0%oPz0@qVwyNVJg1!pEG*oS1F~o?cwMTc~iYmx1Cuua(H?$4ZoC)|KFRAr`&{8!L+a>k_nhO8p>$LIAYi`kB?Q0lg=U(iOU;5(Kte_+;j4lbCU%f1m4>XRc5>D&9lc_fE#wqwjZ38JBM#CkTUX9+5X0_TJ}_bvF*)mdj>2b>BO&DS1&;rr>)wB^2jUYS@o)$p!J#G}5`0{)x-H8ud(GQ&ee_uD&m6WHNVo**3Faw#WrKN5pwLy&LSh=e^ZV?$vtaQXInj6;*XT%S-XnFJSiyHrpk{7$uRDCcF!QIePRlq)v=TggH}mPpblgP#>dQIBID<oy^0os00gJX3eT(GHRzttxe!9FkWUAMU$-J9eZH&C;*!=G%)VLP?}5g6tzOw>+%4>-F1iW@utaXWs)A*$*@)QyXggu(8MLEsbs<3%iB_$VqbtTH%Ju4I2^K~Bl5cMw93jO%hf2kg$jAY_5sLy)Rec4t6GtN*mDV_wXx)|NW9w6;dn&{RLDiR(xsCNOryUjg1AJ>Qn={4?r9{9EP84d2IAExzE*)>S>ZzdWfW?fKda4KDKBVL<BM$Jc4_mRiet^|!AgLgxn!nJ{I%fnFE)=8MBGQdE}|qa#PG&}Wnjg;n<nP6r2IPMRg>K+e_4PJMnNn`woDx_oAj69QL3X1OkJlg%c?OUb)_O1V{{{<di3&dn9rj`OXI~4Oi8AjE6MswSuK;1G4E!o<pJVcRy(AYLQ7SW&QAkoR*7CPc_3Cf*{zCtvjW|dlVj19iX>24)H)~!)0WCYJz^yjm8Js5M=Bk~bo!_h74%{psk0soS;U;yb4LiGbb*s;u~g<NxPencQ=wA1M(G0U5YtjcaVSBSLN`>>3LrW(H9<VZ+jQwTP@Pz}8DJ3t;y3b2bny~U$KN_$>K>Cg@eHkOIm7hmOBy}A3TYl@m<~37xZ85K<Q<}Mc4ee++A36jPqrdkvWk3ShNIpG+Eia^Ok9{6Co@BSwuxsV)4LwfFZeb>y`(_;5<<MIgRL)iIqf(tcJpB1win!asGRO{<6x%it&)}vDVe#msN2PZQZWeHXrPczB*5fqPjhuR=VS2JJp_w_Y7DtL<vK@%JW0B`*%2gMq{OH$L1RdiogA|j=4KWOsN^Kl<Q~Q`W26U(;nKXAyc?wgdI0zcYlkJU+#yR>IwBWNiU3Q@Vu2@v7(x<g3~=5e>xr|k@Y$`}i&B|8$be)TO%dy{xfIZpP}K%RVxYyxLTyf{lC#WfEI7F$AB<WGGZ1U(xp8Hf8Y)$A!K8c=pOl0a0-IVzBux&=DJ!0~v#IDYAB(sS@K;^M3dpjJh>SADc9XJ}*Sa<cZ$YZlsL?-<;!L%gksrYEgeN~dlZ+t7N+?>6tyEz*Fb~x0VKSFkx76bx17s%HNNt^ay2J_f)YACnMJQuDVzV@7EYFqkEnk(TD&c;sGeAJ(G2p{vWX=U=mkT=uW(TqmoZO+@QVbQRj}e0LmzlHF4n<Ww!Uj65t)R?r^xkU2dqw1}6#!R}dof@ai!n4bf{QGEi1P4)OpPdUKePZ%OHe5*6FKN{;SYQMvPx1=bV2Xb%xEs)1_Tqn3`8GRl7(R`M>aQW!8QyU$f*m{x7<uIcpEg3%B9MbHJx~8I|@~b&9fH5@IYdco3=0ql1?OeM>MFj3PxlvOEoi`U~;xdV@;(Zxe*nd06~f)5jB+=7gg(l#(`-I7oY6lxQy*`1kQG$>dl8#JGXy}0_Q=3&g`vI!o>XFLQV5tH2%OF-M3-!5TrizYF6J5saDNnFBDkomt=XhWhO{?xWjOUdM_)mGH|A_f8atz{k^QTlD3z5=WUBO60`12?^opOoNr_5h-}AsEYmuTep$Gj2sDWN1}<sSyY={qNP&{K+ntN@cOwdEzwf#}RO@T;$lDjst)TYafz&oH0D`ofBTvo;;7hQ+&TXysQg|+d1C**)Yr_mWXI%=i&!pZ80;+7_?LG$r!--rmsjsdIg1i(t;l@G`tpaR}385=-c@)GZZL9Q^<;`eXlDMx-xFVhSmA*2-|K{QTeXqWX)dE3m!$exP&EnZH`?ix0k3&pp{S|5NG{CY`9x?B8+N*Hi0F5H2!v4el&xo^5HF}@_2XpRMuK')))


def _trace_step(obs):
    day = int(_g(obs, "day", 0) or 0)
    hour = int(_g(obs, "hour", 0) or 0)
    return day * 24 + hour


def _trace_pass(obs):
    farms = _g(obs, "farms", []) or []
    seat = int(_g(obs, "player", 0) or 0)
    hands = _g(farms[seat], "hands", []) if seat < len(farms) else []
    return {"farmer": ["PASS"], "hands": [["PASS"] for _ in (hands or [])], "market": []}


def agent(obs):
    try:
        step = _trace_step(obs)
        if 0 <= step < len(_ACTIONS):
            return copy.deepcopy(_ACTIONS[step])
        return _reactive_agent(obs)
    except Exception:
        try:
            return _trace_pass(obs)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}
