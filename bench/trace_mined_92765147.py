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

_ACTIONS = json.loads(zlib.decompress(base64.b85decode('c%1EBU2hyoa{MoR=EI7lzV3}H&7FwjiUdjB;w%V@1$>49<NUDpo8kX%EN9r$(-|2NnbkuIzI)POhU(7B%BsqYjLiD_KPUh8>u-Pm+ixd-_<C}Cd4GTM?eyf|fBnyY{jZZheEoKM^7mhV`;Wi<_wS$o_jLZJKYqEo{`kx7<^98#yG{0gzMg!#di>S<@Z*=i{&M;G>Zi-=lhczAH$R`8o`tXPKW#R*vmfp^n~x`_CqHejZ$6)#zF&O(^QX<_!^!E}Zwu*v-rPUTg`U3odh+?^?%~tpr|GN32ci}0x#Uwv;qfQ*&F$5PKYzJh=ymx=T8cQp&E--{x7U{+HoG?+{IGZ-dCl$h<>!ZKS`Xeg4P<T!NTthXd_B3p`LZ0|)>>}wZa#kb@US<SSHWN|A2xT1Ak+VWFAdt*Jqe2Ao74U=A1-&ZH~qH#rZY^Y_uV+QYCm}2WCCFHK}l@5QORsNfiC{|`?7D1d^ZL@;ORZU=qm$_FWU-^pS&CR_QA<A?GJN$;m#ZnJ~7QMp1d<d^yJAx;gYFrf=_=7SHz~JIsFE3B23e@SJ1*fyRQH*+ndDpWxahfuB4zA@cP<n1#5KDkMaK6PPo_n)@wNsK1|E*WwmLUp1l7MWS@TWXXoiZ(>H<fZ9f#JBn~0@zyx3Tg)2RFxn&p|+C@0A7F)`N=f3V1u=A(EF4lSM(xTUS>eJS}@?+UdE&uf9`g-%>;g>&d?jEkLum0uGAXn1!bI7wiDp%6_$Ge-`H8k?|<bHGgdqgxF*y-7~7f@7X^zD}v)W)J%PisQ)$<E|NxgCFI&_Mzo1=uvvmt9vKxJk;HK#Bma!<c)5`~zP^=7OZ4K~2CkqOsfyCgAksnQuQL;Qldd2^iy9ZS7&_L0&W5avX8N)Az%k9>4fd)Mp&^^g%ukgse}lmm0i$Hu3n9NA8yZ`h!8|avwn+!BzdPp0>BJRUWrHHjh74?_m9&XNN~4aCE0bzCh*_u#hG>yKA5|LfQjTw2Ths_@dka{4E?s-3L(htHc*dgeY!4ag@l}SdORXE`aBmDlH8lh2K-pvUUbW;equHK$LMrOP?ik3FV0%PfP@L!cUv}Va&nK>4>fjfEg7ZfIRVO<Um2<&Z7a|z08YrUCPYU9nQS~Xs#zTIk)y9T80CzbsjF>wAy2jB<?=P^v}nx{aD{gEc-~0-U;0IU)OvjFR#Dcb6?XP`SozV|K*${lUFe84*A0v8xM1ijz1g*x{Z)NhMo(2FKVnyG^*+LqSNiu<=tNv@2Lqse?azmWZ8kd9LaKqA$E~TrK{=l@Zz37wUt06V4kDAF;9{`53nj4&{z5t;Jwz=WD+EXeAPVUaF#<n?2)K5WGP8vH($Y*!_cGGMTgRq`uC6wXRZr$v!24rM;8mYUWX3W0OB)--ZZ?Y&Su$%NJ=X<QtR~DCwH?bp!_f3HA@3J!}zQZyGX@G%9s8xH2-VR%sK{e1UdDA8;>ZT{+e;=R<^swYnEwv=Ph+rHna4`@>If9b61Ns_ofmXpH~9k>&wp{mr?Nj!`<c2KW^^s{tC21LQ@L}PTv%Ej%su&Cn<_P_kP!kpeMg>{_quX_z6{sl-`waO*a1het&awy>kYV34Q&o5_nF-Vxw8S{neP^=J|yry@iJ!QxDF_kwea$el+yMqxW4Z(7Pk*B6)+y$uLJ;bS;|18E~9akzv_~5LulQWH0Tcp-|Go54feUE63U-!tQ_rLjim0_u#CRJbN++2Om6IK9+K%<QxO->~b!W_r5p-W5}B-axT)?cvn`&j;uH72L4uWeQDL5K?jhWjv&yRinF#Xty^TQJwoboYb~Acv1BNtc^qaPY8y^w|DoWE=T`J-TjDl|>{QIN$f1*B%_;vrl>V~VA!UD}5y*@d*D_uOsP*a%gu2y+U)PL73PdTCMH&XVLHGkq!>3J0Ud9g2o^8<!S8Bvr<E&kAf`7dFQ`MPkxLbftRAVY(1v;;5IlE4(W?lcZIKnlw2aJ4`*X<t{0fs~rI(p`hq5lWZuGBDu?Z*QX=Q4s5F;wYz>@3gs?CY8wWRNon=><(bxomp49uB#5(KDxu(GLymk5Cla{s!@BBEA+6Q0Wx2-<wnf=9XBLVB#+SbanmbSy%-@XE@g(yorhhp6>n=@DYH~uFd+MKE%0}bgMy!Qw5fUS53J_A{Km_;MHAw>Qf@9(gcF5MC-!5)s{vEEO_KFb}n<-3IzVw#<YSrMA>kb2XN0!9QvY{sbZ9wrIQ!>Of3EY45<W`0Ew|aYOWt;_SK%&rFqh6h5bS@=e<y+v41J11-W5@RBQfUbR!ZH(2UPFc+^lZr(?tCjPvsH6icw<M41EObtk`2iN&y@)>-|v`Lcc+1ESIz6<mM2sET-wMm$Y|;_?*97=bZ0R1HFRfA`*^96oC}`WQU0L;?j^?M&P5ZRbtK&aO?R<CxI6#o*USuU`6`NsrA^rSK$5Y;=Hq5Rh%<)8si;ugtMn5it3{omv%rRn5>Hl@%4U2zc5H!3tZuWF|(Ng;WI%?F*!#`4+ld4uVDvA~U*{h42yX&DT<jo9zt4$i<>JqdjzgQju!?_@My%srksTVrN2Pqe8jKAb&a9Y|h{5A~vwj0$4Qrk(YyLCzH2@&DyeZUF1P$XxIyXD|(|ejR)sXCMkvRgGe2hBq|h{!cfFRmW>fzLJb}Cr3m2$?d&^bq&fkNd9^@)X1LU>#6$0)%LqhEtk$l@r{ntwHAS|7wdez>Nq&@qS6dWPk<F9=Fp`R57a%O9=fM%?SC<VsKxy0<hO^I;Q-w5wzT5XZ2&@dS*|us$(>7lCE9b*19lU@N3RpuGhA3eUuh(fOasG19!+GY#`-LU7ATZ03p5r8G6K!Bw$}~sX%XtIRpp$X8!{u%I@w}d2em`34gtEUb&7h=98e$Ut?sugQOA<IPz&045(DIGP=^JUZMD547=%7}agDo%;!!*ptNZ-tJzD~CaVgv3uob~^Z9s#RWnhXl-0z!<1Gz%|D1S%jj9`@S3$!!svK$%drKGX@18*c80mZV};J;}NRQc+h}&k+*>8EJU!G-rzs&37iQ@bqv+9?l40Y-V0P78k-|W9_|q8x*iGhHypOF=4wHKE*X9NdkNymYZGFk$fZCV)s6LCu>jVJNVa(F)Zl=l<l`PiX+W3r=Ur#s{qt+b3CZfq*Sd-Ic^1V1&qRLT96bkA1ML@lzWu?MN1uV2(r`WaOmX%LWfis4GUc)g$Bo}1}T=bKaJ31(<Gjibu@-dDPYq}7nd+3ARHPoJD)0Jx)>W%902pM%u%u&Ep*j!Yp7LbDuo&qErI@-hhSEQ^+RRNnJE^&zwbX8J&lLys(?LV>e|eVgZ~+w;7Et5<T&E0Hx<ki{*aapZo=f0^e)C>@Vos5Qs;pb^sfRlYCF?ce$^Y9wI0sEaSb9f%j8DFSfjk!oy*1wjUSR3uo)I|G~oP+T0*O%T*E?>b2U#LWO3;>4@^jg7(BT+ym)C7B57C>RiMf*#EKPYCc5xW8dH=W6WE9hsB2C+b}cyOF>MM2&ewiZtHnHQ2HFxGleBS%oE&@z&t_;C<ncFHhI{$vt;+EHvREw8Y%7`qdB=$Ihc+wB89ko$*9OBh4M;l%&D$u}Nq4U=;p!hGWIa@Qz8=Hh&$m-b_(2AcmF{x#uXo$TP&Cbv82Ba0yjQZF71Dp+oY1NBjK>Qi76=wR*eY;kC`*UzGyb4*qd$ot+V{B4*o}@YJiMNs4SdIHC25i@vV`gaGKhv-o2!V3_?-?Jp@pTg0A>B~ztu?UZ&m|Dqi;MZA=~^4lp+z5cv6!Opn$|)H+s_w@+$5iy&Qz7+#`isSmw@RD!C`iDm*x$(7`eS17O+6nE%jNxsbVYKMI1edAA}P!LLRb$86+HZi{%TkcmGheAi8fd%-ZvfuLu#2+f#k<np>{hIg%69vx{4wP}cC7>?m=aF;MY2ItWLQp_kpI8t<`sWbvpaeRd-Oq&>s-H9XwOrTmG<4{loZ=jNCj6bR{M$|`%^?@#M=!mLe7cGQiO>|%$9KUc&x|9aOxeo{<AbaTm0faFJ%tZM#l-Li@p}4N!*@>}#K}Osnm@Shy>#+fXmqj@aESU(h0LX7Fhh7)0z<u)PK~fz;WCl-|#4VAQ9PVVGh8@MQ5)=I-TcAnGi-35W3c~6J|FcQ6lE!NzX~2*b4VeQx#e0%S4C(C%dHUN3;m7zN%=h-%sB_xNrg=-3^wniX9v(T!>8b-TAou}0&SZlY;Q?4fL5)lzWM?cZ?JBNZpyrf5&EtNKRJi65S%sF5PXk=x#xtEFuP4Jdy1+nO)S{jz!LM=#T~~1ygCN6!YLOMKciKNz@Zi~!@v4yuaU}@gh`-=cjz+abfeUB*=bljZH#IWCB7t2{0JW+DT;WB#h(<6S`cL1)=sV?hJxj$!>8m4z-`gnYdx*cOk+URKAzO8n031fv@AxlX3YGXYMjTL~9ds`JgqcyCa3`ORS%*N)hdG5HMmH+P$1n$DP8ysDnO_6emgfY^Y4{O@B}=5YW2M?&q2LwhW2bpm8B;M^P4SOXZAEE~lMmojmvN#N*FY^;um^st)bOn@qFi`@W=<)cmdFJG-L$orU#u`OS@X!cR4MkJg<-X-d=v{G#!mWs>i)vOe3Y-iRpw18%R~-F(Hy%s6MlL6r56X%xW!Dpk{D??e+^!e1@Uo6$zQf;66UOU(O-|e0W`+8O!}47R*C9DVBj@k<tXb~^azW6L;dGML{9?f^6NbnN}RXb1<y;er@yTk)6YEd?;)a(hT#Onh$)e$;qB%NYt-noO^$Qq;J{x=Ho=in?k0zhA`*MwKg$fSmV9TCy>zJPra-w9HK@V}w_<omCqGWtB9{QMiLt{9Ve-kT$d5Cyia~x`CkW44VK+PYY3zvB!)B#sZ<y%9+%iE5fSD(+!H1?{(1sE9?4_6#TAp+qvIAQCy(B4&5)MtV8KaloY9PSeN<iMcA)gL&6SGcML(a^om8vH(zM>$pYBaW=RgeJ&JT-_MduzZ%b-YC|)Q0}pDWZ@(DLjXa-!4lREFw@gMZJmvc3uinLql5GT7-$n_(*WK;QNqSwYXlP0~4E>O^K;lr#7Tsk@DJvp%}AJLo!VeL_*|PxC)O201{L<#(H2NN$%cvF<`V1viXfv1ASBuqJ}L5qS@Skec)o=`*V9%KVF@+Heq29%n;Q9Igr7QPrE(B>fHqd@0%WQG-!6Xw2dZ;4y=*-hlF$+H(u|uf}s>YyjB>UR}26)Q{TX6Tx}dNM&R5Jk|?KHZ|;4JmPY{lND~2U8XQ!O6L<XRynk*IGuK3x0LxfVk_na;yiMOA3i8sqwX%gNLA)eUWqTEWlvSIQz$`vPJf};Mj6ymxE(L++vYErtapsYAqTrZrmJAWPTo}b6PPRvSU@~H$p`0I2kJ+YJ3JDPShrpo<h;NmV&*EF}H}uJyXCSLWYTe=x^j(fE)no+5Zv%yt+D}VJT2qgn&GO`(E)%VEe;Kvm+J<ORe)<i7%QRET%CM|H8P>f;B+A~u?dhBB?BEF#;ySKISg1h*&q!B@QUAp=MExKV7U8_ZMi78ve^ld?@tlDG!ZN(B^G9f^Emgx0g&~58W3}ld@bThoL;MPtfxs7FI|JYhLoCu^*CJzxN{~>((=iM1jkOXB@kv%J$v?7-7HrT<Z-grKMXy}MOOJaNEvwa`3ay%<Kk`VdhNl_#R6%#dNKxoYA21um)IlDmL+XTR(@OjsPpk90OT&`Nig$C833i^9@H{cv${(3`v&2m(WhK?>i@iz<Yo~17dk9QZt|Pe1?_UC_BAPM7QnZB>9F3~MJNS0PX4ryd>6!tuVmhAKY4*UJn*QkSbQJ2p&t$RC%ym<_JDs_9z?Lv@QPB{aSJ|?`=QUFDJ3cpNHRhp)LueIS$%f%keyKz(1fE($T?lT^uyKa+QLxxRr0v$y=tTu?K;#nylj)%a3p6#k8NkI54xhIEtpZyEf1eomn`gidn8>oZpu_jie7N%6l9!*ae!6^A(WlMkcDMY;u>_SL02GP201!tw(>fvN-6~xI1P`2YK}nW<O$I>)PoRmU*%V!0e%MSi1U78qGgmnUXC*=kN13TOGzVVmR%NwO<Y`cT)IfJI{ACeD=cFEj93+!JR>k4m3t*kqd=YXmXDC_%A*aPv6=_qeCSr(008GIPk(JZu-quH?<v`=~Ve&sxWX6JY@z&g{m$B$B<lc~YEi;Q<XqmT+syuub@~#v^VdnmYQ^c)7sAc0E`xc}Hfg4O9R+zn3PM97}W^FhkCpP;2bP<<mtg7z-kJ3rNwi@Fi2im+;3dgm^n_D{M0|j;gi|#W)0;uF&gGvR=g&yXewb4}<TyaDNsR$ro0bo<0-2U+Zo?YAt)@6u*xlPLk4+9AUI3Rhc`H>aEwuoK;<RL35OVifC!^*Ib^cl`YiVJ?jHf8RNy4=+9@%fJx0V&5~{>E+QeMM*l>@3yR5S?O*-UwnX#hZ2T5#)-XR6YsApuwH<U$R_d3n<|zaQ0dF*e*Fa-`$VdE|MJ^{JIU|yHgVA`jr^Y)tbmWr>#2PEJ>+%35D_KbH#ZDtkMUHp5-WFWG@&2`;B*Vee?Md@;WVy-6?mHM1}chaFsM^3Qm~R4iHKw+=!tG<rF1%a_#^*(uECo7%AY;v$&lq6g10a!j9B*u3a!2?SPDVmtT0(?0G=5&j-M^ao^&hb-*icic21)ph`Ccv)T?_&;Zn}!ioYl1B4FK)6uOQG++Zf{s6l0R5>|lrr9WD?-5%gI8~lqp-;qj5NAlCR*W{MPEZDbFA?LXdq5qIWJjFDyC|sbf@KNnv$W?LqQY|!AZ*7B)Y6CA<|K$A);Z^lkVwoxCLA@GRu<Z^@mz!M!=*2~qFD&UlFWN~cNCx8>g}a(DV$bG>3A3Y(Ik%1X<zj4p$KJv75hwA7IyF>5x;M|D_T6ZDM2z}^CWd40q={zUxv-C-%4b=&t1@}BF-V2e}7P-@-mDez@`azc(SnN$&09spx%b0!yjTXm`D}HL<K-P`uLZ}P%s%MY&T{B7;40@LZ1}3)Ip_4Rmzpl!@77-WDR+AP|w!LL3u>vj$<Bt-Z<=F&wH(Kj9lglf>Gw*+5JpXzms=cDmYl?3h?<zaSE+l3OnvO@`r>h>c8Yk`y#>v#AS<En=FOPFhY_{K*_&FG%b?YvBH~TJrFUL!^m65c#_SI#1|AR8W<Jo9rYnnOJe!gW2T{Yrig?Mo$v%lTXZX`-p8vy)l4o=ZH+cCiYiDn?IbR6utf4Y1Sl!&P8^QsXE53;E#ST0m{i85kT#T>i65=zPVQi#FUM5DdGuuXgc+2bD|Sb6DfOXpK@gOo8HCLS{wVv<Z4yhlv{t7DhX~fIRj26_v5lc6TNFK5Un!AAFVr=PywVj2z*Ly$8YpJl<2g_7^18`Re-5%!$v!px<+DLY2YC1#5C@HF<^kRz&hqxfip&V9DsY9YaOr?5HfOC(>vA0=X??a;;)pubd;<qyd)1?MSHPG&q^L-P&6{>SM?sqJ{=3_+$N8sYJFkFCBIr@9C`RZfNMh+|<af}R$2-g2sbDWo?O@2J%*MEuC?5oM2RiyMVv`!+s9?0>Z)>~`O0-h(u}xiB%kHDySUaM|!s*rXKr>Fn=I$|Bj6e)p5+!62U55j-kCs3}pB3D=)Zild$F~xS8j=XC7y$)KDFG=0Qci0?2-D4qDF@4)Xl!1&nV#^gJ*hp82m^iWYuhQD#>9?u*HS+-Oj^H_z8^y7ULx$Uyydjvy-aULaqy({jN_~N0>^QI4U81@9JU@QWR()8S=`v;Pb8;Mh0OyoLZl0v?pG{V$y#wG6s#hnvSWo8#;Cv&_OCf4v#Qvd(Nc?eBuH2(4*@_=T=((rW`+t;?@m~x-_$66kmL3hqdF#`KP>qvBVCcchpV5#$uA20z#f*<oswVbMS+pWG}??9;QJ1x(&j+8w-Sxhgpl*<U7-}^k9b?X2glji#L$4m^ELHtKp9AKM3xY_O9}KlM(W2HM4YlJv}1G@q(mBl9C!pF;PUG0jo#MS<91vd7e)qN0Z&PkskLx4+8)Dz#vHi0*~nMKyfkjl^V!ZWP|_-h7dj{tVu8k4inSucEN~9;q5A-$DqTVZ5BVDo;aPW`=21H*2qi&^#4_UJM?vNCaR%&a=Gj{J=T`FGa3(NP%{gT}*Oe^!O5I2kr={z_ypoFYB6@rSp?8W{H;x7hbvh(s&H5qT_1JMlFqQrCcg$q*#Bx77Yq^m@+SQ9J`C{d?wn5}sve~{X!6YV*%VQ&f4Q1d-4IzQE2K+CVb4Keq(V||gv~J@j1$0oUsUuz#+G}n^$!C=Plx_MPq@siH*ip!TQs59}FB!8YO8XN8Tql{<W=BDC`MTKC@hDMe{NVLK<+Up5-n|?xD&jSj(68o56`4-ZH)O=7j+j=_oL{@ZNJ$1Cs-smHvQfnXgNe?_6OlSGpoJ2e4QOoZ<dJ8s!O`;ZgLjZk+Vqf8(O-%g7csa&N<<`cILHc;$GD}6)3i&oLEuHYEttd}Nni9~Bmq+xG&eV93l$J?C3grZKzHFyYB|$YnL{vziX^r_G9!h61hZwI@5%D=1)3Fq300cIio`h0;|!0Mq{^F`Eu@x3FcdKID?Mp+%cCSlfl!1ZqnlQ>Yz<cziP|j(E0xG@+#Ypk@hA_^#zc(B1POWe(U=rgcO@4z5!>uVjV+(Dy1<W(GE^cu%d~MG|FSR++bLOeMBw7hac+&ZJtrArr7~iw04sY#L_5*`0nn=5sT~(Lwav~leqZoBB?brxMtExjm=f@pVlkQ987MZva7*aq?n!t>010}UN!f;d)ox3)k<yk+bL89DR%RsSq@%@&c$^O8tM$PVsWw6)jUPNDyN9dbwMv*P#4!OZsU=sq7A>Gt3lNe?8HG`{n;xKpbzfdPdf?3QQyb2l2bpe@`L8vK0^b2!k}7UT>iOfvP-8ebwS#ujky8<9_8#U4XyoSL5scrKoXThh7(`OP=$w*7j8+Ws5(Xlh7z7Wh3k5$*)8zCbyzgWa!4XEh`{L%m>++54Mlhbb`7m={VC_6eaGns`r>laE1t4>Wi@Ik){5a=`5?LE^{v2Gr+JP7t6rSd&OMLbMI8ZJBQidjmI4037U)rE)x?f3$J|)?n(n^O12m>5~)l&ijZN_8ONc*@SnKA&c5U*nHZ1L;zo^+6B2CHXx6j^MCG(|{Z*QImGK$*vJqT)W*eFHe$Oh)VxassAw9MtLSa$F_*WM&P;lIQteI==xd^HqIpK5na=97;=CP)(_y(P8z50O=uS$}4YkFvYEQE#pG7EirV@1}r1LSgngL87KBAe6)4k9|<q(^kABUHbqj7jHfC60AfijjDH+?MzuUYR{0+AX+@m{%VmLx!RvI5wlPG6^5;ZTdUL$PqXZBqsz`jI+yZ+1#wlR>t{lydYLiBWq)A3Gh-(rjQl^)BG159HdrLK2YWv4HUPku9Q5?1ElD`v={HK3u7gX+zc?e7K^zU)%Z9E6vjgi-Obo>`{igVoE*!}2SbvB2*v8oE6L&DLc6b^=PkVYOr0H9+#+Rmuxta_zG=a@8a)l$$h20CXX+tn%|XF>`H7;Mf&tChTz^2se_GeUsIxyiOtA^t>@k4tk_E3h+o5LzdvJ!8PIyp`9gIshQ#AlG+4ahevNh<eb&LQ;W6n2Z_Z5~j<!+pEi~x1>LE0C-r|2tL4E7ZBEGSJ4<x3eBN7c)XE8(b7twU9?~;>9T;%c~qeE2#;NXa#TfO6z$a+I|QN25CG5;WVL(#WFMZJck?pse=a0K5(=+a{1zWSz`Fr-o3|BC4G0Sq^P5sq$Z<EssR8Z>-NKQ$G|VW7NhuNLdl`(M#k~1<C7rU~y}I#mbiEjsQ^9M9zvm(aFdgjkkiGIF=Y#~DwT$&ieB|ImdVYB;2qSTbA|x?~pF;t)+O<w)V{}Fsj+XE>RArLXcSNJ0=j7l$z*^ae*o+*SS2IOL*QiDc+^$@Xc1qlNGq=YNK)UV62v9?;B6x?Tuv|ytcp+ScW??DyT^TG30j(Yus!QzfSH3~Tfy{T2u=%@)Xfc7KEsABwOwWjsCJ|nnWE<)bO4)~_3)3RY+9DHY1<*WXr)}k<a2_xrYj=VBdWW7!JrGGD6@r_@kTNR)rpVmkvH~gU-IIh$ck7gX%MeyQ4+@rP(V;{fP6lR}8>QrD^uI`!skTW=wj_Y6Bp}K@xoEV`S!N`&Iwxz(Zz3;mDiu%jo3jG=@obn(QWS^&bh-bmQR+k+-n8oW=>bNagA|Z19>i%#1*mPA6RNWP6=G%+hA~LBEP}@9FDC|ugSi4!JIEIe<(_5-OcQg4)sQ=^5MbAWT!{>aXL6(KY*jZItr;^z#y#+?m^WpG(mZv|@)e!j&v)=rIW>A=JfH)5p}>Z)@418QWw!0=zrsf3mfJ_BEQf%>|16M6qK?5<0#;zbb*2Q26tQBq5{fKi3<e@^-|$O#f?d2=BFrATQgXPxHXkMeA!vN`eRQ~$uI><lrC+K@4(cI^VY|G&kP2s%H%h-TBDmU;i7THXDjru)9uJP}g&uCT`dWjD8dEL|-`3G%6rS*h(N?0|YSU;8Nuxm!h8WsS;@VlNu-=Jgux$_Hn`mf8P*+spITLVyR!4+_dkR6RGd^d;B!JK27O2)*Vw27+^p-n;^@peGI3!Sg*yGX{Bz<TC3gZxB$b}DE#N`~d-Z7nlW?fQt>%?2DEa_b$-J2n>C+6msgL|DUT=;j$16h$S1k?SXF%@&Dr7P-l77A3pPOoW1`cbT39?q+>Q|3S>L3}hIa8ZKA8v%G!(oRC)OSNc`gJe?SlvXRUMC_zUcPZyG7av07<!c`EXISy*7%JU6tzpqL#;Unz`lY_=i=X;cY;Y^^u~qbIUbQvQ0L9uaSU!wflw+n)lWNzbuqs2D@b;kXl1Rv@7VJk%Cl7l$+q0(At01rh7xdyH0do-%HBc@utvllzrnf0NVizkK$gSGm85}>1b>e+GvwkREtOkx(0~AmLuAnzjWWqXuxeDQwDS$u6q1uh$c?f7$<#155j*3x!W1iqE>CG8Ox6ny}TEK#1nC=yJb@@bV<Y&+`cwRq^eGl5G#(>sp`-XCV5!R6$Ft$hRKV`&`*8Odhn6O}|-dsg_#1=@BRj&lIqUZjcn35q~^O>I48_nXKDk^{o_4Wmt8VirsM}sD|7O0sEFP?;D^>^`fmI$Yq4V(=uYVD7(H)r^mr{~P$Y*hDF<sp8BS;;Pv{DdvGSbV(>#zh)PCeXPSNQ7q|k#r^D-Wb{<cZPbp${^_rEe>P*XL&Fx%d5U>ELk|{b}Z3oaf+8jYl&veV5~J3n2sUOYu4PXDo$X`(&T4fl=oVcw6Wex$`X^DdYS#>Nn#vg|L;Y)&pDdUFH8(iNdw20B;WoIn$$`O')))


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
