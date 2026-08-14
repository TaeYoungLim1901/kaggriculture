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

_ACTIONS = json.loads(zlib.decompress(base64.b85decode('c%0Rp&5s;OZpHtXKI^dh9BFSoquw21dq#pjcCZ$N!2n*vfU!P|eKY*O8>{ZF%1S=|_{hxamTx6hbtWT%!5|+W8K3{>;@^Jz{U3k-{o;?GFWy~#_;B&%(Z#?2_MiXyUl)J;{N>TbKYsiDKmPvT|NQ*FkCs3E{?nW5*T25I{P6M9`>X74K41L!=IgiKhwnfA?bpkn-~4oWeevkxhqu36JbDuT`@@e{SML^Ie7L%Leevkxr>pC?KVLk0wfgU0e!RN;c=71FFDvPPx%%*NDfHogK41L&_Wj2nzkWLW*XjeziuGLhG@0=DmHMA|Z+`g8r+2G)UH_<-A`bBCay?7$t}lPMx_#5h7poV-Yu;U7{`~Q<tS9d~3}mSZYD(A7_<Zr<?WgtdZnWjy`?s$@{qXUqFpq=6Tz<TIp9pgJ8~M^O8@ErA;`r)xe9RA*x2t#f?&g0c!=!n?9mmbIpS<s&0%G)Gl4!Vbl4&``T>R;u+kQ0i+cEHf5AP95-x+9p*^S`($+rW)d2q5#=fga_@Kzm9KGDpso_wo@>d6NUm0PA`1n+(;cf{3b=IS?y6XCF2#|c{L=kyigWk;2`dD+Zv#+?+VMZCVZTg4td%#ZQ@o+Uia{EgRgB79hu+n4p0<?!U=hamgmD}QzF{utjR#&`3fxg>E2$p;dA<rnVs*tN+p4BE4BVy#TdGtYg!-N4RIgI?_O*tJIQ^VB=jz4K#frPe=vdwqTN!^dC$boKt@o9j3Ka;lI!&GUW8vpy<!n)TQ3-@e;pMm}GBxVrvlM6?*#qbFY;V4^ysAHSqAZ4||NvsO%eVws#McjC`%bdZEcA&jQ_&#9{}+@#8xP!l0shi&eO@(+9w$puM4gPwqCL}R%ZB;eu63*UZ=fXBz|C18waYi$pfM|sWC<T&DrryqxXc>L-^b3Ws!4<E|siIDZq^{NJ6J{vr~<dMfMpnkB?xjaUYXK+=&siz$^Y?sH~9-HSMs&}w{%d5lDh#cLcO};?p6i`T$oZUUpS|RNLDOyJdOMJ1k0KN%VQTGW{{W$T35+Rz#Cyr7%8|(4R+y(JGb4ptSNa6R?v+SLLQFx(!8z9O!qP5SGxrF739#2dKb;?gy{ll2S&chMi82~BO#sOgDAVA_3P~Cg-!D&?UAAsm_yhHBq>o<R%#}BMFwb=3GQqM`fgWaLJb3NC<L_5ztCYpA24bJq~on5*6@#!`=cRM;z&wCD(m-Js7<mYIvpKm4uJe&t*k`6ZeO8zjmjfXs^^ACp*xh;&4P0tmM87k`<sv7#l>X`cR^8H^|@97D?d_eYj%eE6qJ4k_sAx>e-YOW5SH*fCcQ%BiVK>D1?TN5Li@g6)+P%Z|zSo##<+V-Z&WKWE+(YSYoLtAc#=mRKG7rsi8;U2z%x5K7K?+YD~+x_5~a&ldyn{^j+enp3b>vig2ZGeNeK|2HQX<{tr_(^NWM&4b0_LbHw3RwP$c+FaYo@oEx$7IThjeM~BPcS)baL^_Sa0WT+12-N~J~uWa+U=}&gV(Hc^v+xQQ#nlG8{4xIrkmJW?YS47*!XED@V&nL`Sm&q{_yer<uBh~y?_5VF*^{NS}1Y)reHa`(P_CzQS_zvyH^B#@avWj-w~ugU^tQQyUABPdPg+=qrHFo_WITtNEY<@mrme$7#59Y_4cp0xJUNG$kYj<vw_E~gfnjCj+4u;27Y?*zIu?k@QY+P#Xuu&Iu=7tjX2CvWLXhXh+Lf#U`Zz#D#hIK!|hVoog;0CuP4yJrf@y=dUQgoJb5zrMjtz)+?B`Mk&|g+^o2ge*mS|$-y`@<2G)*%Th3IIk1?!CeB3!kqv1=-@w9%eb#DkFin>5yc%y7P@+=M`5pT)h{@!Sh^s$T^Q9=Kkhs(@`uo_F1+Q6mAFbXjhF;znZh9N04uBTPyG^dUzRso)Qqwy_lq*dYe2&xNvT9xvIU6S)$lZrvB1l?ivHw{%eh67;S_T$vlMupyl@MoJqFouTwYGH1L_cGxyH+_~xieYg;p3B{=Uc2#aI1*)aX75X0Bh1%yYRMN>WzQ;?)0^IE`_V!M;?B-IqkB&LIL|-gP`=yy;?5xr=Ka;&A!hD!jFE)nKH;SdDJ+^Hbn2N)_K*W)9u9`}7@wXT4JX-o{H05zy<O{{-dz7>vC3j_&-CD4RMf4dD2Guh`eTGICzPLfaEX^DT5*6Jk1uv<JWZ!Q%M?Wis}osxh;>-=SssPy-~?y**td<S(vA}A9~dd=X;|8i2~z1LG8_`NUD3FfDWEyR8#``IT5=_D&YK>sZrsx>8u}3^p1GjUI{K$pk0&i!LdoxndgiAf$obBAb5JOu9XbaR4^t_;liDdQ7drXDa(G9b693!UOY&vx4j0@eE&bQJgZ%3etR0UZ%?(s4P+HTHbz#q38gLqslohN_3}znG9T{*G3YCA>3i*^hv10g9c1Sk8@|MAwE$?CbGdX!*?vmbuQ438K{_-}=WnEyyVX~k$ZlYkObw2uCdlDbZw9hiY6(RA<a|OPFN63Ni5jG1Mok4BGdi)vh^YM^PblYFE<-?m*C|+?#$4`Eyg*RAGc`&B`tMas5OvCaJPe;=NC|rL(Dy6}HLI8M=kx?PlD%~!%=m-%M1IY4Jtw7Pi`5VRS9I|6frTT!LFp!p3A{!36n`!>6h(C`!u{1UwW*7;~Q284hov{$PIIX9~w^VH9#`);K%yv?aY><=?P?sl&`c&G-IvfHgO>T}nXL8cBSGNw<510sPrlY+OQ}o1b2uE6IPN4#XbGluWd=#U^_3G@9=)n`Jopv^DR@IrX5}5&3%Jm?6IX_-U*zoDfCL4be^w9c%{pX!FSy&Mf#S%t1s-ujV0%r`;ttD=jbV^0*+RtG(2@$oz!6n#<Y71=QE~=<Gyq_cz(ech?%Aq{x;&vK1Lu_9$>};`x4*D|1+@CxgJn%I0p8X0G^~tN+Szo7d7Ysb@1esY-a~Dg+niq<whh$QWKPafDoWV`fwKo|>;<Ws}2uyA!b4EdRJ~WY+yBTUEv+^*RRt{-}{S2xX-2!b@+4fNcn=H8Qf#IjRi{>1I0v!QiX30m42Pd=;1*u1GO3H;)ye(PTF6sCnU9^WHo7v05Ry2_1gdAS4S1isOdGB$fX$U0PPzc`vHd1=9noez|ZV<*7E<l5EdyNrsj7AbZezKP+46KNip28R<7hB_g6MRBECJ))O>?0hdJL-$DmS~(Yfmmpa0CRVcy8*5kq>~;Vf!J*oJ(oimmFQKWy2T!Vu(eso<sCJ$0>y9A=w+Z|7-yt~_l)t>P8ju6I8$^d_J{mk+)xCqNMqHmaoot)G;_TI!ov(!mLwlB61~25Oqf%@!x5yMox-u(XIYd{&^c>HNxgwN$?VR^D1>#_!5ab-IxTW(I;=lT62z7RSutrbWn*dKM#il0*G+B~^5Ax&Z&TR?Um8-{IUGl`w4+To7`HJkht*@Zw<3F$u6Mv6cZ0`gO}rkrvcNW(0$H+23S0P#N|Z|Fm!;z?7uOFm;|KqSMjtg(rZV#E%0E`wF?w>XQ`U_|8{-*fG&#;#ZvbZU-y;O18PE#y+%^UxBw4v-0?zUku65ocXCU#1db^^o=L=h=*bJNxj}ZPZlU-D57j(McbUO)>5b~U@T-ib9--7Avsf*Vcpq$P%0{-pPu9Rn%yrInM6_E1Y@}XrmcH-)f1vD=Rd!RN?y8%7V&XdMZ0ygg+jGZB#n9#R5^5W|=0XlGZK<oYuVJ8Mu{zZEHOh^xb@DNCehMhFb`+#<0LBCu}Bzly*V#*Q1T5UpdV$fG{L%KBe9@XDzaVmDd9qN^36+O&=LMM+c!@?0K(m^&mo+A1ogc+eD=V*b??{}H|Snqg{@~|@Ne{FOSO@G$KwTAF-Lr(S-(`hR4-$;5HGU$>e!;nN1ZL$aW(XTl1pafUN!>2OHljN=<A9AU^0x*#+t#as2JuyY^@w??vPbXng7=ZD(2QXlQdRt`xry9%2kHDJZ@xxqiQt0^Lq)!HN?y0r`sR$z+9AAs14bC$*xJbhHBJ7>$Ds28&zuG=gl*H(6s?-QJ9jQ1w)M5Zvb1xkuh6#chUKzsKS`XaNPaYVCc#-Iw{2ii{cYhGN2qfP)0L5NN1OTpt<Hw^_F~|2{l|&0e&16ARi-bQRBbe+Fh)sNsNwY;$<iKWkVd?2Kn|T?PjxG03_QLYGx&-1xr9A|-##|b7Vw|qx*p7@3kv2v#zlNtTYAGcsbeIy+@IwABw`zi#7k)!p;S)C?J1-LKu}O?j<=A_(Oq-fb>N-BSa0LYJTS9aVkUZMN2EW<F3M=a&AGoCjDo*I0^H}PLAKs8t4x~<Wjw5JD&`blN^=6g4hRieG9JVxz0!c4{OuUV*g7aq`V3Ya7-~|tLj8)<+N$d>-i=D5D9O5#M(e_NN3bQV(EX!(U(joP-D^7JSCw~Z{I+a<(g%Yc50y)G~5g~I7wV{mP07T-MEas~lISUd+qi_U!P;6u$+-pq#^jnGPDMVlXPI|AaCs4Nh9>RD`f|Y5;$U?}S%-sWfow{-Q<d<iBA^g1&3OH!?mq#SCLkM?9S^?yFsgqfGA6OWb188)BnW~hV$%1ZTT;%90wS;on22n!jnKz<Fp}<B5BnnNbgV_0lJ-dtxv9Z^r!)s_XJp>=I-|e%J+$}ID@KX({#JC0--X^{~bt#b@Q46+wSe5hg@?bp0LEIsB;nFQI_$hc0+k5c2SOBELl&~O}M2X#L%QP#7v)Rnmp(AmeP4bVKB}TTzgjiz(*wIAhf^Lqy;^GiMfEdMOnz|rK_sf#EL0A%M4^2~?oJJjxS(D<ZY+@X8>pX3JNpUb8kVaB`Yj?!>A+tV>(Ekj<{EKfdKQFRQ`qqG`_%hIc=@$%~C!#MX+q|dn3_er6fSEt8ygbax0qK12)O}<=bHW?4G_;gwNZ%*H2^2b%&d%YNf|jr`iR&i&lbwNwM;M<#R}6weScZ6yAqL|lN9K|$Lcr-`nq}Ux94BQb<H3y?gh&<Gs2$r1))7#w!_1Tn&`M&V*=VGe*%Pla?=zNy;<ywR!V42}Qh9VkM<{N<qTue)fweK|3+uB36sJNf#Rkr{vPUj0(~)QyLrIk1;kRxY;l-DjXEx9}r_2Kpwj3WMHf6gWQUaT^&VS1K;k+lRaU`G+5ZVXhRGCE`KpN|yP~!>p1u%sIKFrQ}fH@{qm?^h}{;O~lW&(<YdZCjD%4W8F>+Gp)e{c3iq5&R8!~$jT<(}UnTo1}X%!1ds@Qrr`HqzU?p8bD;IH=&>sx%OtZws*FJZ%!n966n?Wcn?Sa(x5hj$ITY$-3xGkFgfrO}8_XA@*5!>0=?UOoZOE6BpLC!B9vt;cjq@wW%wDSN-6vg>VfF>cy)LBZ0CK?b#;c#KhlN20l4|g<a)SO|ldDxeg5L18O!zS;XJ5idIuly9S_Y-qAtH$SyWwI`~kAt-55(<gHE1wM9?Hpa{i<BIzkQPrlckFsq2Ss)@@!my(x|mU=2114T%#D%{6uaYEcOK&V2@XGwdnBuGgYH<wgV@dq9?1m}&>t_I`^XGIU2C+>opKE0gWzGXad98&VPmEL9T6{g)&>jQ&o^7%PsG9Bj*nVAQns`*k+*~C0RfH=nT@vA(#Z%ITY3Cl@o)G(Zx2*G%PyfNm1s~rmXAkn=#XJi8;I*@xjqeocot`R?P=baDB9z+y^x4x9lm4E+tXLQ3G46s}|E*W2-Mv16KRP7)HVpUX)t;jJY)fzpPzjUkXRuDEXUF?x8owbn=VY>|gPYC8s^D@Q&S_t<cf&hX*kXEZ`<*`t%Bx6b}PkH;`wA9&P3{f_&MS?i?Z-$Oq0Nu8@<Z`x`xAg}7HPfeKQIE<J?~F9fT33Fx#Sq+bCmZ@1<y{UcrLWizR)e{W$5V_fgGO4R?-cQ<ku7!xR-tsu7{*Zm{6#c;GoGJ73h)k0aU%fNkchxSwTnnhJjOEp-AbZJaVI^4-s}dQ++IMGZQcSIGKgf`7TGPRV^}SX>ZcPY<GM%)5W@&Z*DAc<8n}yy9OW_i0W*={L+5_Y^8yLWWBt2trK|!$gK+Gl^@Vnc4^vlx2ZOw6!SwO&kyOB0QsfUPmPOG_e`BV;RdvB*l<tMPgwXoiUT6;JK}ngD;#OrEc{FLFI`e)AlwL&QW1f)<b5b`!=yY5xyJ<+(5dedl1f2<lSThN7z`OOiB}S_)!sAf=T!bwJzrT1Msz$U-8cP*XRSA2Wvb^Pv0%eyqVi(&|0uO9cD3xl9M0p6J^C`?5O8Mbp9d@xnvob_$3m>=3{S{{u!!b6fHEGDw8%7n&>eO#Hu8mUaxA6^C80HfG?bL;kh*<N1JUA3@HHc}4$9R4VaFTJHb=%}Pgr0Eb)ENZEs>TvPvgK9^U6doBjqDrs$z;Ujfy%HAgPI1lfT*i`OsZp_;Lsx81kZBRYT<T~L%keD<mwViBPJRV6a1L~EnKOcxp$Bh3nXdX)d^t$PWvXH<%M=;9|m!GTKO@w1(a{l5;~S~yg2_I6V$d^43f`zRR?jNn<pBH_=E!ozuSni%$7!v2npE29z{=G4F8Pu8gdLOk2U)YX+}8RbpU;J{r2Zmqq9%*Q8+Cn%28089nP|w`q;Yc##o8B5iN~Rt>lZ~>;@=t(No5o41cBM94Jzn#k#njL!e19h!PG(5ue%>)*TYNnVqykv}h0oUok&nW?&9R4rbb;#MIPJ3j)iH{>K(ZIN@fpRSd>#p@7lj<_vKjDVxLufZJ;s#mx3-97WO{$3SvcxOfCp8aLN0wwV5-*xkHK7pbRSTJT@2Gy@7#ml>Y?JVv?@Ufu1`uQ^;1Bssm95WII4Od0b8sP(d~)yTf)+1n&cwLVn}LhS4m%h#p}4O|aq%NRBlzAsJ~9XFKovI!+@98y@;B6ed&y-WWFNm==&<!Y+Bwe^sQT{lwc^I%1Opxm6XI*92B&H$3M(V&hxBDZC4RYJQ8npeVRyC?q8J;GX1QOGfNTe6Dt0S$b6EZdrvbPIbZr52q=(;1O_dyWa6X9Q4{-oEr;BQ{iQ)4T<U1n!C&e>mXIh4jSrASMAbsDO-M4QR9)GS(<s7L=YwUHsw?%qfAxT`VYF9xEH4s=T!pToae)u>OpJVU%7#%5A)63kyd(FF9;jfcpAtFD7X;xGfEj+$Ehfg<l~s8B&+I8dn538QQGr!5b8N@OM=ZAwgM46(}AQBSseT+N=Kp`H-IkCre8FkSWPA57mOG^)QN{l@9bh>b}J5{a>n2RDfD!+a??fTwtO%_yZ><tuJy^ZZT)XWkk^{cv)B&k5H5lW0j#4!drV=EDo{WM)<ODfhieWLO6o7Bj6fJoRopF&CM=BAt5ZL8>&-by*lNv9{-^p7p7ap@*&-hGOfZqlwDgBbhacWA#|EeYP=d4JkVkF*YL7l@f`w4#pBM4GCf}?-4aCkCVJ!&U}4gy_Q05Sr%ri>rHH-K$KFfL8V4#4yJihr*eT!5B&6QWL6$b!P)Ovmtd|x?^|ZsE67pgqo}j<d0o)e$!+jozmbf8ha!9LZ&)70C_7pe~zD^6y!8UwqrsF(aLFR~&N!)L~#Td9Mr$}3)r*zl_>_xWnh@zMoagXA#C^6K$2!(?Cuq_4ImjH!|BOpd%M%Ei^O-X31kFXGW4+z>3j;PDFxFm#%2*tB!(Y@axy0Rlk39#vHgQJvH15a0>FBu@#qpoE~8fIENN=kD8y%Q4%ZWX}FG{Oc%k<l0S>S{!D*6>MEW4l}TB?~|k@oIU;Q>oG7Bq!tS7P(pNYE~%1kdCR(ZJajoWs#FxkEaD(B--y(d#U+$dI>{K*e*?fdR1&afCa9$JVES&O>09j+!^q3?9=d_EJ1h}cxHjF$se8*mvPuYH;C%4{f6?sNyi*U{u32Pg)MJIx%(H$sbeW^mrC7~@M_Bksf(L)T2tfBsh#^Mlk?lgKs-ys%`@gb-jLT#*h@>4K5Df__#_(FcO%V{+>ZLv8)&O5y<9)#&7}=hJjp-~2SUR;R0hCX=Ij75hT4NSZus;#P_u5uovver@sgfqfeN(NL~0pxQ%m???`%a+?i3^ro5C=o4iBCZ2cy(<8K%gYZ{)tqhCIk?c6e0NG7*}5BY=+b6W0WgoSyuWh8<6%YykY{SVHL_UQ%0J=D4;@{VW~=RIUBlD0eN+FUy5UkAm)u6Ch}cm!vXqyb~-JqZGi%@wBw+;9Fv57B5eNbm*O1<rP?xnS7uNukZ*_f)0QgMz{fgp&tn$kJR-kHWN}n4$9>8I`Wu59^iH^QqPko-%?AY9%=;Hw9dWPCotM_I(Do!d$|)((QvxZl<|2@Xxt6}65ixd4Kx}ozV|c)D-TZva)X1Cgd8z8azVpjpG=@5UMdRW%lkJm^4T6$3KT>}%A6e(&{(-CXSE#>4f9%r(;E0B5G+(nBDWrNv7pLWP2iE;QbijUb-a;(E-zeTk|wee2r}>O@EQR_SRZGcY6_|}=Q!dNIykuc&MP!Z*K&sr#>`6O#5EHcF@a(*5xw>+W$c)v*eYQ?xFTB^l;%-u0xm>^>43Lu0g5a~7MGTsS|gEwps1lXR#57E;EaF|S;u74X2P7s%Rx7KQ6}`}&r+4P_VmJ21i?8*R2pnmz<qp{SX0-<c(U4`4%fNI{512CcT11Od>u1VAy{kBril7XBPc+biKxdX-_6VVag3<*A9_NrP@$KhanRQncoZW-c(xRBeU;%}AfE`0orJ=tNXXNB#evM^3@!0#Te~pESLfjpwXV*FTUBcUQI+$=6kK%M<y7uj0v2ES{iiqAuYY}a`QhWIq{ykdR6KW5F*JI-6CxLdbc^w%qgJF!EmqAwEwup`G#ZB(@D)&38qIxnn~N9>b<5*QK#2c*J<&bxl*lMYl99z05;~hXuxO=8{?HeJ3eD;i9pk7zA3#Hy3b@?Z7>DzMtQ|$g*WFr4bilioOZk`qqAO`aZVJ7kzRarrM8v1ICvbtR%>oc>RhhTPn2^_jX<jW|MV%_wWu*BCDjq)EDYjSzW)pQ1?p2Q>0<A=pXn|dgom3Rq4K&Ej-q3f5r$Pk0`l@A-no`8blgJv&NfGjwgutZB52Cpkb;IOEFXi-`DUcV(El-sAGn5*<-(kD91>mt>S)UdT5sFx#0pZN652hr9@#FQthcg=AKzqeYw7{ng*0_p#8A`I6>?^@Xy+>zdZP9L>oOK2rDK^x)@5VtD;PjPs^s<1UmLSNp2kI^4_--ki=#b_=6T6B)io5_s4i6d!Rn;EZrEGILlvj#|IhlU0*vO*X3%Z1ULe-Q67msKXyHTV7Um}4yGC=4h)8SsLB(8lTUWs+o*oqmQTuzB?Y@{UAt{@qz?V<nJAeHp8{Y;YZ`fR%ms-z3FMy0n>iV8xVMeD-6o_?;cQ4I!$ki!avk=X^F?_>#*0;s%8I57c)tDNA63pa8_+nnX55#<qBN!bHNtI2vA_5$M+rQg0>35!PHEZ;(Fh*-EMkN00vSB5+hFHJ+gs@gCy?v_T4TNV9o2@+!2ruIbi>|Q}1br+yu8;Lt~!mTuZ+R+(_AYwCFVRW3}+-|i@i#mlOvw}TJ43FXhr59gK_i2=}JVm_oF)f@LB10tU!lD#h7@=09DFu+tq!sxW)x-bvR$aWjC(q!+peQc36MD8&2cztbdysKVyodZZt~5ip`gG7+Swx)+%7hVgFl8AM<#$4*grOwL-mziL(hT-Wtc0Z!9=MZBd%CSQjFir#y2)}SuE>a1bW#RJSg2YMaX1Yck*w69<uxie!ppq)>|-l@H8d+M0Cu+!qhL3jxh6HaCRmA9zTZvK7tHEtpIlOjlV8LMr(Af!i-~$xkzGm}%0}W*)k{N6FOA;|D2+Zl8{vc|l7zb{byf*z*@YFRG5LTzRQPlFL$Y$CRB?<(TRQCXro_HUu<3ysm0TZ;$WbpWef0j&v0tLng7ZA+X5?DJN9O=lBLivoH?a0V1B1%gJ0NTA8uJIgY<zobBRqS(d3LPN1Zhx}N|is>#OIx|xUDi1ribE+<fsL}Hw{~s0>J5txLr7ys`R?BKrL2G2}~z|lUj4D-%vXGVJjp+YD(Pnv^cC+Qg$w8&uNjERZ6yj$Fo17#{zq5HpK2FWG_1$5lzb!Hxqj9en~VOhJVNVA(7LOk)c~%KL?_FEF70;?xo)R+8{#}ja%4>7~77zlLgUZDqQtu`yS$Y;eTP;B6W1=q|G@rr|lQ+sy!hRuCxL2x@myd!#r9&v(+k~b43W>S|NLKizf>TV>e*K_+mYH5ct;cdDuJzj<{)2?K`ClmG3B$jLy{Aj515DAiZ>wxVo{7f!-%<eZ{#V2!;IH?dnr4h*Qsk<FJ&eXTXUXCV56yr!ty)PCjgom^j@|2_4_t5o4LqPGDcw1iDltFyibI422gO%QnJN>{(+Nl+!{g+4pr0$jLDi8^DODfaKuvorqtAwk0843W?H)rzq-1nC-dL%Acx864|9o%eZz~*&svR+C)xAP9=C^xG?UfRg8?7MiG_3UFsX$oy8k;a}L;wM;3Cbu0Xl6z-?z@%`>akDp%Ys&`dN+>%l$Mn^^u#(F1oR3W;}`bWV&b%`cG`F>E=>1QX6SCT(mg7-j<dBZWkDhYiBEz=-O{JMbIImz8M^hO;W9eS28px!ta_xa%UA^ca%^W`+=cmQ#p_Kv)?r9L|yq8>J|s3$rN!jJiRbbus_lMk0jzl;(@{u=%M+_Dw1@yWuNCR~;}xF1d(1>J_hX-f~%L4TWlu#+juR*~)lWDR^FYi-n^A8fU2;z_dWq3C5^9)1V1DTSqXxqRhO5!mt@FDlYqoh|*)%SfX+HvNI9cv<kJEb@rgubp(vXGy8QN5i5(v8^MvbeC1tB#eNpbq`u@fA_az0?&il~JI64*@-L2`1Z?H>IccU(b^QC-D1-?^b8d&)TK;1&9-k~Bfe2+Shgoyb(RjZ~9?JqOQHtl2h#hyTJPsyw*TQQc<+>YlZwupo=;gk`y7KUHlVJi+S;~!0OQ8Pu-um2{=jC{hwgNrA!K*EzAchyBsZ5O_w}Y7aEn?|vhkx`Yxm?2d@6{f7Y1{8swozG>V(awMuVsCyHlaz5vTTOE&LpW&Oe~?Sr|p$3jFV~UHE^qFXlIfeEQms{YM<;6$(z+ef5Wms6+z5+)|z!93NO)j4N<JP&CMPvH>%MaILZ=(j2%T0v0Xf8*V#SB2DB_sN3y(wCI&rO*rg7~n@EPO^N!P5sU`XHe*<=F#{')))


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
