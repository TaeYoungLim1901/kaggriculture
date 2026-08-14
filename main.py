"""Kaggriculture submission — reactive baseline v0.

No hard-coded action trace (unlike the public meta, see docs/META.md). Every turn
we rebuild a task list from the observed farm state, assign each unit its nearest
*doable* task, and sell the whole shed as early in the day and as early in the
order list as the ten market slots allow -- order slots settle by index against
the opponent's, so selling late means selling into a book they already filled.

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
# Throttling the sell rate is a loss, and the loss is monotone in the throttle. DRAIN
# was calibrated against the town's consumption alone, which is the wrong question:
# holding stock back does not protect the price, it just leaves the goods in the shed
# while the town keeps refilling the order book. Measured head-to-head against the
# unscaled build, 8 seeds x 2 seats: 0.60 -5,904 / 0.75 -3,830 / 0.90 -1,422 /
# 1.25 +1,112 / 1.50 +2,920 / 2.0 +3,390 / 5.0 +2,429 / no throttle +7,581 (16W-0L).
# 999 makes every per-hour share exceed the shed, i.e. sell everything, every hour.
# The knob stays because a future opponent may make the throttle worth something.
DRAIN_SCALE = 999.0
# Hour 0 included. The whole gain from dropping the throttle is reaching the top of
# the price curve before the opponent, so the earliest turn of the day is the most
# valuable one to sell in -- the shed is fullest there, holding everything the hands
# dropped at the day rollover. HIRE still takes 8 of the 10 hour-0 slots, leaving one
# sell order, and that one order is worth +4,244 (16W-0L). Do not fund it by hiring
# less: HIRES 6 falls to +1,814 and HIRES 4 to -13,484.
SELL_HOURS = tuple(range(0, 24))
LAST_DAY = 29                # unsold stock scores nothing, so liquidate

SHED_CAP = 100
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
CASH_FLOOR = 250            # absolute minimum cash
FEED_DAYS = 3               # days of wheat feed to keep funded before any purchase
SEED_BATCH = 5
# Found by the Optuna study `v9mirror` (tools/tune.py, 100 trials against a frozen
# main.py) and confirmed at 32 episodes. Cow-heavy, wheat-heavy, and it needs the
# second quadrant: 13 structures + 16 crops = 29 tiles against NW's 25. Under the
# old sell throttle expansion always lost -- part of its cost was flooding a market
# we were simultaneously metering. With the throttle gone it wins.
# 32 paired episodes: vs the 1-quadrant build 26W-6L +2,135, vs the shipped v7
# 28W-4L +3,824, vs bench/v3.py 24W-8L +8,057 (the 1-quadrant build managed only
# 18W-14L there). Against the reference agents the mean is ~2k worse but the WORST
# case improves (-94,870 -> -83,633), and we lose to them 0W-32L either way.
# Do not read Optuna rankings straight off: trial 82 reported +2,112 at 16 episodes
# and measured -373 at 32. Only trials re-confirmed at 32 belong here.
ANIMAL_PLAN = ['SHEEP', 'SHEEP', 'SHEEP', 'SHEEP', 'SHEEP', 'COW', 'COW', 'COW', 'COW', 'COW', 'COW', 'COW', 'COW']
CROP_PLAN = [('STRAWBERRY', 4), ('WHEAT', 12)]
HIRES = 11
HIRE_SLOTS = 2              # market slots a single turn may spend on HIRE past 8
# Of the 10 hour-0 order slots, how many go to HIRE; the rest of the crew is topped
# up from hour 1 at HIRE_SLOTS per turn. Hour 0 sells into the fullest shed of the
# day, so slots spent hiring are expensive there. Measured against the 8/0 split,
# 8 seeds x 2 seats: 7 +4,673 / 6 +5,298 / 5 +4,321 / 4 +6,632 / 2 +4,343, all 16W-0L.
HIRE_HOUR0 = 5
# Rank sell orders by the value of the whole position, not the unit price: an
# early slot is worth more than a late one and hour 0 only has a few. 16W-0L,
# +1,835 against ranking by unit price.
SELL_BY_VALUE = True
FERT_RESERVE = 99           # fertilizer held back from market for the ongoing crops
BUY_SLOTS = 1               # order slots per turn kept back from selling for purchases
LAND_TARGET = 2
                            # at our routing efficiency (see docs/META.md §5)
LAND_RESERVE = 1000         # cash kept back after a land purchase
ANIMAL_RESERVE = 2
ANIMAL_PIPELINE = 5
PLANT_CAP = False           # cap PLANT tasks at seeds actually on hand
STICKY = False              # keep a moving unit's target until it arrives
BUNDLE = False              # persist short local work queues with deadline preemption
# Task value by priority; strictly dominates travel distance (max ~18 tiles).
PRIO_COST = {0: -900, 1: -700, 2: -500, 3: -300, 4: -220, 5: -120, 6: -260}
DIST_WEIGHT = 1
_STICKY_TARGETS = {}
_STICKY_LAST_STEP = None
_BUNDLES = {}
_BUNDLE_LAST_STEP = None


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

def _fib(n):
    """Cost of the n-th hire of the day (kaggriculture.py:685, mult 1)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


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


def _wanted(scan, seeds, held=None):
    """(animals still to buy, structure kinds to build, crop -> tiles to plant)."""
    have = [t.get("animal") for _, t in scan["animals"]]
    # An animal sitting in the shed or carried by a hand is already owned. Counting
    # only the ones standing on tiles leaves it listed as still-wanted, so we buy it
    # again every few hours while it is in transit -- and BUY_ANIMAL fires whenever
    # any matching structure is vacant, which it is until the animal lands. Measured
    # on seed 7: 3 SHEEP bought on d7 for the plan's 1 remaining slot, ending the
    # season with 13 animals against ANIMAL_PLAN's 11 for 19 of 30 days. That is
    # ~$900 of dead capital, 2 extra wheat/day of feed, MILK/WOOL pushed deeper into
    # their price floor, and -- since 13 structures + 14 crops = 27 tiles against the
    # quadrant's 25 -- two crop tiles lost. v4's whole edge was cutting 14 -> 11.
    for animal, count in (held or {}).items():
        have += [animal] * count
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


def _bundle_refresh(scan, day, invs, shed, step):
    """Drop completed/disappeared queue entries; keep the rest boundedly persistent."""
    global _BUNDLE_LAST_STEP
    if _BUNDLE_LAST_STEP is not None and step <= _BUNDLE_LAST_STEP:
        _BUNDLES.clear()
    _BUNDLE_LAST_STEP = step
    animals = {p: t for p, t in scan["animals"]}
    plants = {p: t for p, t in scan["plants"]}
    for i, queue in list(_BUNDLES.items()):
        inv = invs[i] if i < len(invs) else {}
        wheat = inv.get("WHEAT", 0)
        fertilizer = inv.get("FERTILIZER", 0)
        kept = []
        for goal, action in queue:
            verb = action[0]
            if verb == "PICKUP":
                valid = shed.get(action[1], 0) > 0
                if valid and action[1] == "WHEAT":
                    wheat += min(action[2] if len(action) > 2 else 1, shed["WHEAT"])
            elif goal in animals:
                animal = animals[goal]
                valid = {
                    "FEED": not animal.get("fed_today") and wheat > 0,
                    "HARVEST": animal.get("yield_units", 0) > 0,
                    "CARE": not animal.get("cared_today"),
                    "COLLECT_FERTILIZER": animal.get("fertilizer_available"),
                }.get(verb, False)
                if valid and verb == "FEED":
                    wheat -= 1
            elif goal in plants:
                plant = plants[goal]
                crop = CROPS.get(plant.get("crop"), {})
                age = day - plant.get("planted_day", day)
                ripe = age >= (crop.get("first", 0) if crop.get("ongoing") else
                               crop.get("max_day", 0))
                valid = {
                    "WATER": not plant.get("watered_today"),
                    "FERTILIZE": (crop.get("ongoing") and
                                   plant.get("fertilized_until_day", -1) < day and
                                   fertilizer > 0),
                    "HARVEST": ripe and plant.get("yield_units", 0) > 0,
                }.get(verb, False)
                if valid and verb == "FERTILIZE":
                    fertilizer -= 1
            else:
                valid = False
            if valid:
                kept.append((goal, action))
        if kept:
            _BUNDLES[i] = kept
        else:
            _BUNDLES.pop(i, None)


def _bundle_deadlines(scan, day):
    urgent = []
    for pos, animal in scan["animals"]:
        if not animal.get("fed_today"):
            urgent.append((0, pos, "FEED"))
    for pos, plant in scan["plants"]:
        crop = CROPS.get(plant.get("crop"))
        if crop is None or plant.get("watered_today"):
            continue
        age = day - plant.get("planted_day", day)
        if plant.get("consecutive_unwatered", 0) >= 1 or age >= crop["max_day"] // 2:
            urgent.append((1, pos, "WATER"))
    return urgent


def _bundle_preempt(scan, day, units, excluded):
    """Free only enough persistent workers to cover missing hard-deadline work."""
    urgent = _bundle_deadlines(scan, day)
    covered = {
        (goal, action[0])
        for queue in _BUNDLES.values()
        for goal, action in queue
        if action[0] in {"FEED", "WATER"}
    }
    for _, goal, verb in urgent:
        if (goal, verb) in covered:
            continue
        candidates = [
            i for i in _BUNDLES
            if i not in excluded and i < len(units)
        ]
        if not candidates:
            break
        i = min(candidates, key=lambda j: _dist(units[j], goal))
        _BUNDLES.pop(i, None)


def _bundle_make(primary, unit, unit_pos, owners, scan, day, inv, shed, claimed):
    """Turn one Hungarian assignment into a local animal or crop queue."""
    goal, first_action = primary
    if tuple(unit_pos) != tuple(goal):
        return None
    animals = {p: t for p, t in scan["animals"]}
    plants = {p: t for p, t in scan["plants"]}
    if goal in animals:
        local = [(p, t) for p, t in scan["animals"]
                 if p[0] // 5 == goal[0] // 5 and p[1] // 5 == goal[1] // 5
                 and _dist(p, goal) == 0]
        groups = {"FEED": [], "HARVEST": [], "CARE": [], "COLLECT_FERTILIZER": []}
        for pos, animal in local:
            if not animal.get("fed_today"):
                groups["FEED"].append((pos, ["FEED"]))
            if animal.get("yield_units", 0) > 0:
                groups["HARVEST"].append((pos, ["HARVEST"]))
            if not animal.get("cared_today"):
                groups["CARE"].append((pos, ["CARE"]))
            if animal.get("fertilizer_available"):
                groups["COLLECT_FERTILIZER"].append((pos, ["COLLECT_FERTILIZER"]))
        order = ["FEED", "HARVEST", "CARE", "COLLECT_FERTILIZER"]
        queue = []
        feed = []
        for verb in order:
            for pos, action in groups[verb]:
                key = (pos, verb)
                if owners.get(key) not in (None, unit):
                    continue
                if key in claimed:
                    continue
                if verb == "FEED":
                    feed.append((pos, action, key))
                else:
                    queue.append((pos, action))
                    claimed.add(key)
        wheat = inv.get("WHEAT", 0)
        pickup = (min(6, shed.get("WHEAT", 0), max(0, len(feed) - wheat))
                  if first_action[0] == "FEED" else 0)
        if pickup:
            queue.insert(0, (min(SHED_TILES, key=lambda p: _dist(goal, p)),
                             ["PICKUP", "WHEAT", pickup]))
            wheat += pickup
        feed = feed[:wheat]
        claimed.update(item[2] for item in feed)
        queue[1 if pickup else 0:1 if pickup else 0] = [
            (pos, action) for pos, action, _ in feed
        ]
        return queue if first_action[0] in {"FEED", "HARVEST", "CARE", "COLLECT_FERTILIZER"} else None
    if goal in plants:
        local = [(p, t) for p, t in scan["plants"]
                 if p[0] // 5 == goal[0] // 5 and p[1] // 5 == goal[1] // 5
                 and _dist(p, goal) == 0]
        groups = {"WATER": [], "FERTILIZE": [], "HARVEST": []}
        for pos, plant in local:
            crop = CROPS.get(plant.get("crop"))
            if crop is None:
                continue
            age = day - plant.get("planted_day", day)
            if not plant.get("watered_today"):
                groups["WATER"].append((pos, ["WATER"]))
            if (crop["ongoing"] and plant.get("fertilized_until_day", -1) < day
                    and inv.get("FERTILIZER", 0) > 0):
                groups["FERTILIZE"].append((pos, ["FERTILIZE"]))
            ripe = age >= (crop["first"] if crop["ongoing"] else crop["max_day"])
            if ripe and plant.get("yield_units", 0) > 0:
                groups["HARVEST"].append((pos, ["HARVEST"]))
        queue = []
        for verb in ("WATER", "FERTILIZE", "HARVEST"):
            for pos, action in groups[verb]:
                key = (pos, verb)
                if owners.get(key) not in (None, unit):
                    continue
                if key not in claimed:
                    queue.append((pos, action)); claimed.add(key)
        return queue if first_action[0] in {"WATER", "FERTILIZE", "HARVEST"} else None
    return None


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


def _market(farm, private, scan, day, hour, market_prices, todo, build_want, wheat_pickup=0):
    money = _g(farm, "money", 0)
    shed = _g(private, "shed", {}) or {}
    seeds = _g(private, "seeds", {}) or {}
    n_animals = len(scan["animals"])
    unfertilized = sum(1 for _, t in scan["plants"]
                       if CROPS.get(t.get("crop"), {}).get("ongoing")
                       and t.get("fertilized_until_day", -1) < day)
    orders = []

    # Order slots are processed by index, in lockstep with the opponent's list of the
    # same turn: every unit of the order in slot i is committed before slot i+1
    # (kaggriculture.py:542-615). So a SELL in a late slot prices against an order
    # book the opponent's early-slot SELL has already filled. HIRE and BUY_LAND are
    # atomic and settle regardless of position, so selling first costs nothing.
    hire_now = min(HIRES, HIRE_HOUR0) if hour == 0 else 0
    sell_budget = 10 - hire_now - BUY_SLOTS

    # Price-gated selling (closed loop, docs/FRAMEWORK.md §5). The town drains the
    # market faster than we produce, so prices sit ABOVE base most of the season:
    # a fixed daily cap would leave premium goods rotting in the shed.
    if hour in SELL_HOURS or day >= LAST_DAY:
        panic = sum(shed.values()) > SHED_CAP - 20   # overflow is discarded
        dump = day >= LAST_DAY
        overflow = max(0, sum(shed.values()) - (SHED_CAP - 20)) if panic else 0
        # Slots are scarce at hour 0 (HIRE takes HIRE_HOUR0 of the ten), and an early
        # slot is worth more than a late one, so the order here decides which goods
        # win the price race. Unit price ignores how much we are holding: 40 WHEAT at
        # $25 is worth more than 2 MELON at $250. SELL_BY_VALUE ranks by the whole
        # position instead of by the unit.
        items = (sorted(DRAIN, key=lambda k: BASE[k]) if panic and not dump
                 else sorted(DRAIN, key=lambda k: -BASE[k] * (shed.get(k, 0) if SELL_BY_VALUE else 1)))
        for item in items:
            have = shed.get(item, 0)
            if item == "WHEAT":
                have -= wheat_pickup + (n_animals * 2 if not dump else 0)  # keep pickup and feed in reserve
            elif item == "FERTILIZER" and not dump:
                # A fertilized+watered ongoing crop yields 2 units instead of 1 and one
                # FERTILIZER covers 3 days, so on STRAWBERRY it is worth ~$200 of fruit
                # against ~$50 sold. Nothing reserved it before, so with the throttle
                # gone the whole day's collection went straight to market.
                have -= min(FERT_RESERVE, unfertilized)
            if have <= 0 or len(orders) >= sell_budget:
                continue
            price = market_prices.get(item, BASE[item])
            if dump:
                qty = have
            elif panic:
                qty = min(have, overflow)
                overflow -= qty
            else:
                # No price gate, and at DRAIN_SCALE 999 no rate gate either --
                # see the DRAIN_SCALE note. Gating on a low price *causes* the
                # glut it means to avoid: stock piles up, the shed passes
                # SHED_CAP, and panic dumps the holding at the $1 floor
                # (measured: 154 MILK for $154).
                qty = min(have, _drip(max(1, round(DRAIN[item] * DRAIN_SCALE)), hour))
                if qty <= 0:
                    continue
            if qty > 0:
                orders.append(["SELL", item, qty])

    orders += [["HIRE"]] * hire_now

    # Hires past the 8 that fit in hour 0 have to share later turns with selling.
    # Unguarded this deadlocks: HIRE filled all 10 slots every hour, so no SELL
    # went out, so no cash arrived, so `_do_hire` kept failing without advancing
    # `hires_today`, so we re-requested forever (measured at HIRES=13: 1,516 HIRE
    # orders for 390 wanted, SELL 527 -> 336, $70,267 -> $46,222 on seed 7).
    # Two guards: never spend more than HIRE_SLOTS of a turn on hiring, and only
    # ask for hires we can actually pay for -- a failed HIRE burns the slot.
    # ...and not before the herd is bought. Days 1-10 run on $123-$588, so 13
    # hands/day ($232 vs $33) starves BUY_ANIMAL/BUY_SEED and the engine starts
    # late. Idle hands are worthless before there is anything to tend anyway.
    if hour > 0 and HIRES > HIRE_HOUR0:
        hired = int(_g(farm, "hires_today", HIRE_HOUR0) or 0)
        # Completing the crew up to 8 is cheap and urgent. Only the hands past 8 --
        # where the fib wage starts to bite -- wait for the herd to be bought.
        target = HIRES if not todo else min(HIRES, 8)
        room = min(HIRE_SLOTS, max(0, 9 - len(orders)), max(0, target - hired))
        cash, n = money - CASH_FLOOR, 0
        while n < room and _fib(hired + n) <= cash:
            cash -= _fib(hired + n)
            n += 1
        orders += [["HIRE"]] * n

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
    # Buy every animal we can pay for whose structure is already standing empty,
    # instead of one per turn. Ordering one and waiting for it to be picked up and
    # placed serialises the ramp at hours per animal; ANIMAL_PIPELINE bounds how
    # many may be in the shed or in transit at once so we do not park capital in
    # animals the hands cannot place. `todo` counts in-transit animals (see
    # _wanted), so this can never exceed ANIMAL_PLAN.
    vacant = {}
    for _, t in scan["structs"]:
        vacant[t.get("kind")] = vacant.get(t.get("kind"), 0) + 1
    in_flight = sum(count
                    for holder in [shed] + list(_g(private, "inventories", []) or [])
                    for a, count in (holder or {}).items()
                    if a in ANIMALS and count > 0)
    room = ANIMAL_PIPELINE - in_flight
    bought = 0
    for animal in todo:
        kind = ANIMALS[animal]["structure"]
        if (bought >= room or vacant.get(kind, 0) <= 0
                or spend < ANIMALS[animal]["cost"] or len(orders) >= 10):
            break
        orders.append(["BUY_ANIMAL", animal, 1])
        spend -= ANIMALS[animal]["cost"]
        vacant[kind] -= 1
        bought += 1
    pending = todo[bought:]
    # Hold cash for the next ANIMAL_RESERVE animals whose structures are still being
    # built, so seeds and land cannot eat the herd's capital. Off by default: at 25
    # tiles it measured 12W-4L against no reserve (the engine is not starved there).
    # It is the EXPANSION fix -- at 2 quadrants the first BUY_ANIMAL slips day 0 ->
    # day 10 -- so it only pays with a larger CROP_PLAN. See docs/META.md §6.
    spend -= sum(ANIMALS[a]["cost"] for a in pending[:ANIMAL_RESERVE])

    # Land before seeds. The seed drip takes SEED_BATCH of `spend` every turn, so at a
    # 38-tile CROP_PLAN it holds the balance under the land price for days: BUY_LAND
    # landed on d13 of 30, and the quadrant only reaches full throughput (294 of 312
    # unit-slots/day, ~94% non-PASS) around d19. The mined top-ladder trace buys its
    # quadrants on d6 and d9. A tile bought late earns for the rest of the season; a
    # seed bought late costs one crop cycle. No effect at LAND_TARGET = 1, which never
    # reaches this branch.
    unlocked = len(_g(farm, "unlocked_quadrants", ["NW"]) or ["NW"])
    land = [1000, 2000, 4000]
    if unlocked < LAND_TARGET and unlocked < 4 and spend > land[unlocked - 1] + LAND_RESERVE:
        orders.append(["BUY_LAND"])
        spend -= land[unlocked - 1]

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
    held = {}
    for holder in [shed] + invs:
        for item, count in (holder or {}).items():
            if item in ANIMALS and count > 0:
                held[item] = held.get(item, 0) + count
    todo, build_want, plant_want = _wanted(scan, seeds, held)
    tasks = _tasks(scan, day, plant_want, build_want)

    if BUNDLE:
        _bundle_refresh(scan, day, invs, shed, day * 24 + hour)

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

    if BUNDLE:
        for i in errand:
            _BUNDLES.pop(i, None)
        _bundle_preempt(scan, day, units, set(errand))

    rest = [i for i in range(len(units))
            if i not in errand and (not BUNDLE or i not in _BUNDLES)]
    plan = _assign([units[i] for i in rest], [invs[i] for i in rest], tasks)
    plan = {rest[k]: v for k, v in plan.items()}
    if BUNDLE:
        owners = {(tuple(goal), action[0]): i for i, (goal, action) in plan.items()}
        claimed = set()
        for i in sorted(plan):
            queue = _bundle_make((plan[i][0], plan[i][1]), i, units[i], owners, scan, day,
                                 invs[i], shed, claimed)
            if queue:
                _BUNDLES[i] = queue
                plan[i] = queue[0]
        for i, queue in _BUNDLES.items():
            if i not in errand and queue:
                plan[i] = queue[0]
    plan.update(errand)
    if not BUNDLE:
        _sticky_plan(plan, units, invs, tasks, day * 24 + hour)

    acts = []
    for i, pos in enumerate(units):
        if i not in plan:
            _STICKY_TARGETS.pop(i, None)
            acts.append(["PASS"])
            continue
        goal, action = plan[i]
        if STICKY and not BUNDLE:
            _STICKY_TARGETS[i] = (goal, action)
        if tuple(pos) == tuple(goal):
            acts.append(action)
            if BUNDLE and i in _BUNDLES and _BUNDLES[i] and _BUNDLES[i][0] == (goal, action):
                _BUNDLES[i].pop(0)
                if not _BUNDLES[i]:
                    _BUNDLES.pop(i)
        else:
            acts.append(_step_toward(pos, goal))

    wheat_pickup = sum(a[2] for a in acts if len(a) >= 3 and a[:2] == ["PICKUP", "WHEAT"])
    market = _market(farm, private, scan, day, hour, _g(_g(obs, "market", {}) or {}, "prices", {}) or {},
                     todo, build_want, wheat_pickup)
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
