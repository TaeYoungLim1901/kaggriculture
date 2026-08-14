%%writefile submission.py
"""C166 anti-H4 meta counter.

C165 is preserved as the baseline. One addition only: after observing a
high-confidence near-mirror opponent executing the same four-step premium
front-run, the agent gets one step ahead of that policy (H5) on later matching
sales. The escalation is evidence-gated and skipped when town consumption on
the current step would immediately refill that product before the opponent acts.
"""
import base64
import copy
import json
import zlib

_TRACE = json.loads(zlib.decompress(base64.b85decode(
    '<BLOB>'
)).decode("utf-8"))

_SELLABLE = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")

_FRONT_RUN_HORIZON = 4
_FRONT_RUN_ITEMS = ("MELON", "STRAWBERRY", "MILK", "WOOL")
_BASE_PRICE = {"MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200}
_GLUT_WEIGHT = {"MELON": 3.5, "STRAWBERRY": 2.0, "MILK": 2.0, "WOOL": 3.2}
_LAST_STEP = -1
_CLONE_CONFIDENCE = 0

# --- H5 meta layer ---------------------------------------------------------
# Disabled until public flow confirms an H4 mirror.
_H4_META_ACTIVE = False
_H4_META_EVIDENCE = 0
_PREV_MARKET_INV = None
_PREV_TOWN_SHOPS = ()
_PREV_ACTION = None
_PREV_SHED = None
_PREV_PRICES = None
_PREV_STEP = -1

_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}


def _public_signature(farm):
    """Compact public fingerprint for detecting a mirrored build."""
    counts = {item: 0 for item in (
        "COW", "SHEEP", "GOOSE", "WHEAT", "CARROT", "TOMATO",
        "STRAWBERRY", "MELON", "PASTURE", "COOP", "WEED",
    )}
    for row in farm.get("tiles", []) or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            for key in ("animal", "crop", "kind"):
                value = tile.get(key)
                if value in counts:
                    counts[value] += 1
                    break
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands", []) or [])]
    return (
        len(farm.get("hands", []) or []),
        tuple(sorted(farm.get("unlocked_quadrants", []) or [])),
        tuple(sorted(tuple(position) for position in positions)),
        tuple(counts[item] for item in sorted(counts)),
    )


def _signature_distance(left, right):
    distance = abs(left[0] - right[0])
    distance += 3 * abs(len(left[1]) - len(right[1]))
    distance += sum(abs(a - b) for a, b in zip(left[3], right[3]))
    if left[2] != right[2]:
        distance += 2
    return distance


def _update_clone_profile(obs, step):
    global _CLONE_CONFIDENCE
    if step not in (4, 24) and not (step >= 48 and step % 24 == 0):
        return
    farms = obs.get("farms", []) or []
    if len(farms) < 2:
        return
    player = int(obs.get("player", 0) or 0)
    distance = _signature_distance(
        _public_signature(farms[player]),
        _public_signature(farms[1 - player]),
    )
    if distance <= 1:
        _CLONE_CONFIDENCE = min(8, _CLONE_CONFIDENCE + 1)
    elif distance <= 4:
        _CLONE_CONFIDENCE = max(0, _CLONE_CONFIDENCE - 1)
    else:
        _CLONE_CONFIDENCE = max(0, _CLONE_CONFIDENCE - 3)



def _sell_qty(action, item):
    total = 0
    for order in (action or {}).get("market", []) or []:
        if (
            isinstance(order, list) and len(order) >= 3
            and order[0] == "SELL" and order[1] == item
        ):
            total += max(0, int(order[2] or 0))
    return total


def _trace_sell_qty(step, item):
    if not (0 <= step < len(_TRACE)):
        return 0
    total = 0
    for order in _TRACE[step].get("market", []) or []:
        if (
            isinstance(order, list) and len(order) >= 3
            and order[0] == "SELL" and order[1] == item
        ):
            total += max(0, int(order[2] or 0))
    return total


def _town_demand(step, shops, item):
    """Exact default-configuration demand applied AFTER market on `step`."""
    demand = 0
    if step % 4 == 0:
        for shop_name in shops or ():
            products = _SHOP_PRODUCTS.get(shop_name, ())
            if item in products:
                demand += 2 if len(products) == 1 else 1
    if step % 24 == 0 and item != "FERTILIZER":
        demand += 1
    return demand


def _remember_market(obs, step, action):
    global _PREV_MARKET_INV, _PREV_TOWN_SHOPS, _PREV_ACTION
    global _PREV_SHED, _PREV_PRICES, _PREV_STEP
    market = obs.get("market") or {}
    _PREV_MARKET_INV = dict(market.get("inventory") or {})
    _PREV_PRICES = dict(market.get("prices") or {})
    _PREV_TOWN_SHOPS = tuple((obs.get("town") or {}).get("unlocked_shops", []) or [])
    _PREV_ACTION = copy.deepcopy(action)
    _PREV_SHED = dict(((obs.get("private") or {}).get("shed") or {}))
    _PREV_STEP = step


def _observe_h4_meta(obs, step):
    """Confirm that the opponent is itself executing C165-style H4 front-runs.

    Premium products cannot be bought from the market, so their public inventory
    delta decomposes cleanly into our sales + opponent sales - town demand.
    A signal is accepted only when:
      * farms are already strongly near-mirror,
      * our previous action really performed an H4 pre-sale,
      * the opponent supplied a comparable amount on the same turn,
      * no base-tape sale of that item explains the timing.
    """
    global _H4_META_ACTIVE, _H4_META_EVIDENCE
    if (
        _H4_META_ACTIVE
        or _PREV_MARKET_INV is None
        or _PREV_ACTION is None
        or _PREV_SHED is None
        or _PREV_STEP != step - 1
        or _CLONE_CONFIDENCE < 3
    ):
        return

    market = obs.get("market") or {}
    cur_inv = market.get("inventory") or {}
    cur_prices = market.get("prices") or {}

    for item in _FRONT_RUN_ITEMS:
        # $1 floor: inventory no longer identifies sold volume.
        # Ignore that observation.
        if float((_PREV_PRICES or {}).get(item, 2) or 0) <= 1:
            continue
        if float(cur_prices.get(item, 2) or 0) <= 1:
            continue

        target = _PREV_STEP + 4
        target_qty = _trace_sell_qty(target, item)
        if target_qty <= 0:
            continue

        # Accept only a clean H4 timing match.
        # Normal / nearer replay sales are noise here.
        if _trace_sell_qty(_PREV_STEP, item) > 0:
            continue
        if any(_trace_sell_qty(s, item) > 0 for s in range(_PREV_STEP + 1, target)):
            continue

        own_requested = _sell_qty(_PREV_ACTION, item)
        own_supply = min(
            max(0, int((_PREV_SHED or {}).get(item, 0) or 0)),
            own_requested,
        )
        if own_supply < 2:
            continue

        demand = _town_demand(_PREV_STEP, _PREV_TOWN_SHOPS, item)
        observed_delta = int(cur_inv.get(item, 0) or 0) - int(_PREV_MARKET_INV.get(item, 0) or 0)
        opp_supply = observed_delta + demand - own_supply

        # Keep mild quantity drift; reject unrelated dumps.
        if opp_supply >= 2 and 0.40 <= (opp_supply / max(1, own_supply)) <= 2.50:
            _H4_META_EVIDENCE += 1
            _H4_META_ACTIVE = True
            return


def _h5_meta_counter(action, obs, step):
    """One-step second-order preemption against a confirmed H4 opponent.

    If their C165-style policy is expected to move a base sale from t to t-4,
    sell at t-5 instead. Skip the attempt when town demand after our market phase
    would refill the item before the opponent acts on the next step.
    """
    if not _H4_META_ACTIVE:
        return False
    target = step + 5
    if target >= len(_TRACE):
        return False

    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return False

    already = {}
    for order in orders:
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
            already[order[1]] = already.get(order[1], 0) + max(0, int(order[2] or 0))

    shed = (obs.get("private") or {}).get("shed") or {}
    shops = tuple((obs.get("town") or {}).get("unlocked_shops", []) or [])
    prices = ((obs.get("market") or {}).get("prices") or {})

    choices = []
    for item in _FRONT_RUN_ITEMS:
        planned = _trace_sell_qty(target, item)
        if planned <= 0:
            continue
        # Town demand can reset the price edge.
        # Skip H5 when that happens.
        if _town_demand(step, shops, item) > 0:
            continue
        available = max(0, int(shed.get(item, 0) or 0) - already.get(item, 0))
        quantity = min(available, planned)
        if quantity <= 0:
            continue
        price = float(prices.get(item, _BASE_PRICE[item]) or 0)
        priority = price * quantity * _GLUT_WEIGHT[item]
        choices.append((priority, item, quantity))

    if not choices:
        return False

    _, item, quantity = max(choices)
    # Put the pre-sale first in the market queue.
    action["market"] = [["SELL", item, quantity], *orders][:10]
    return True


def _front_run(action, obs, step):
    """Sell one premium line immediately before a clone's expected glut."""
    if _h5_meta_counter(action, obs, step):
        return
    if _CLONE_CONFIDENCE < 1 or _FRONT_RUN_HORIZON <= 0:
        return
    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return
    already = {}
    for order in orders:
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
            already[order[1]] = already.get(order[1], 0) + max(0, int(order[2] or 0))
    planned = {}
    end = min(len(_TRACE), step + _FRONT_RUN_HORIZON + 1)
    for future_step in range(step + 1, end):
        distance = future_step - step
        for order in _TRACE[future_step].get("market", []) or []:
            if not (
                isinstance(order, list) and len(order) >= 3
                and order[0] == "SELL" and order[1] in _FRONT_RUN_ITEMS
            ):
                continue
            item = order[1]
            quantity = max(0, int(order[2] or 0))
            if item not in planned:
                planned[item] = [distance, quantity]
            else:
                planned[item][1] += quantity
    shed = (obs.get("private") or {}).get("shed") or {}
    prices = ((obs.get("market") or {}).get("prices") or {})
    choices = []
    for item, (distance, quantity) in planned.items():
        available = max(0, int(shed.get(item, 0) or 0) - already.get(item, 0))
        quantity = min(available, quantity)
        if quantity <= 0:
            continue
        price = float(prices.get(item, _BASE_PRICE[item]) or 0)
        priority = (
            price * quantity * _GLUT_WEIGHT[item]
            + (_FRONT_RUN_HORIZON + 1 - distance) * _BASE_PRICE[item]
        )
        choices.append((priority, item, quantity))
    if choices:
        _, item, quantity = max(choices)
        orders.append(["SELL", item, quantity])
        action["market"] = orders[:10]


def _terminal_liquidation(action, obs, step):
    """Replay-derived safety net: leave no sellable shed inventory at season end."""
    if step < 680:
        return
    shed = (obs.get("private") or {}).get("shed") or {}
    market = action.setdefault("market", [])
    already = {
        order[1]
        for order in market
        if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL"
    }
    for item in _SELLABLE:
        qty = int(shed.get(item, 0) or 0)
        if qty > 0 and item not in already and len(market) < 10:
            market.append(["SELL", item, qty])


def _shed_access(size):
    half = size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _move_toward(pos, target, tiles):
    x, y = pos
    tx, ty = target
    choices = []
    if tx < x:
        choices.append(("WEST", (x - 1, y)))
    if tx > x:
        choices.append(("EAST", (x + 1, y)))
    if ty < y:
        choices.append(("NORTH", (x, y - 1)))
    if ty > y:
        choices.append(("SOUTH", (x, y + 1)))
    size = len(tiles)
    for op, (nx, ny) in choices:
        if 0 <= nx < size and 0 <= ny < size and tiles[ny][nx] != "LOCKED":
            return [op]
    return ["PASS"]


def _terminal_action(obs):
    """Observation-driven final-eight-turn harvest/drop/sell controller."""
    player = int(obs.get("player", 0) or 0)
    farm = (obs.get("farms") or [])[player]
    private = obs.get("private") or {}
    tiles = farm.get("tiles") or []
    size = len(tiles)
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands") or [])]
    inventories = list(private.get("inventories") or [])
    inventories.extend({} for _ in range(len(positions) - len(inventories)))
    sheds = set(_shed_access(size))

    available = {
        (x, y)
        for y, row in enumerate(tiles)
        for x, tile in enumerate(row)
        if isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0
    }
    actions = []
    pending = {}
    for pos_raw, inventory in zip(positions, inventories):
        pos = tuple(pos_raw)
        inventory = inventory or {}
        load = sum(max(0, int(v or 0)) for v in inventory.values())
        x, y = pos
        tile = tiles[y][x] if 0 <= y < size and 0 <= x < size else None
        if load > 0 and pos in sheds:
            action = ["DROP"]
            for item, count in inventory.items():
                if item in _SELLABLE:
                    pending[item] = pending.get(item, 0) + max(0, int(count or 0))
        elif isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0:
            action = ["HARVEST"]
            available.discard(pos)
        elif load > 0:
            target = min(sheds, key=lambda q: abs(q[0] - x) + abs(q[1] - y))
            action = _move_toward(pos, target, tiles)
        elif available:
            target = min(available, key=lambda q: (abs(q[0] - x) + abs(q[1] - y), q[1], q[0]))
            available.discard(target)
            action = _move_toward(pos, target, tiles)
        elif isinstance(tile, dict) and tile.get("fertilizer_available", False):
            action = ["COLLECT_FERTILIZER"]
        else:
            action = ["PASS"]
        actions.append(action)

    shed = dict(private.get("shed") or {})
    for item, count in pending.items():
        shed[item] = int(shed.get(item, 0) or 0) + count
    prices = ((obs.get("market") or {}).get("prices") or {})
    sells = [
        (int(shed.get(item, 0) or 0) * int(prices.get(item, 1) or 1), item, int(shed.get(item, 0) or 0))
        for item in _SELLABLE
    ]
    sells = [row for row in sells if row[2] > 0]
    sells.sort(reverse=True)
    market = [["SELL", item, qty] for _, item, qty in sells[:10]]
    if int(obs.get("hour", 0) or 0) <= 1:
        already = int(farm.get("hires_today", 0) or 0)
        for _ in range(min(10 - len(market), max(0, 8 - already))):
            market.append(["HIRE"])
    return {"farmer": actions[0], "hands": actions[1:], "market": market[:10]}


def agent(obs, config=None):
    global _LAST_STEP, _CLONE_CONFIDENCE
    global _H4_META_ACTIVE, _H4_META_EVIDENCE
    global _PREV_MARKET_INV, _PREV_TOWN_SHOPS, _PREV_ACTION
    global _PREV_SHED, _PREV_PRICES, _PREV_STEP

    step = min(int(obs.get("step", 0) or 0), len(_TRACE) - 1)
    if step == 0 or step <= _LAST_STEP:
        _CLONE_CONFIDENCE = 0
        _H4_META_ACTIVE = False
        _H4_META_EVIDENCE = 0
        _PREV_MARKET_INV = None
        _PREV_TOWN_SHOPS = ()
        _PREV_ACTION = None
        _PREV_SHED = None
        _PREV_PRICES = None
        _PREV_STEP = -1

    _update_clone_profile(obs, step)
    _observe_h4_meta(obs, step)
    _LAST_STEP = step

    if step >= 717:
        action = _terminal_action(obs)
        _remember_market(obs, step, action)
        return action

    action = copy.deepcopy(_TRACE[step])
    _front_run(action, obs, step)
    _terminal_liquidation(action, obs, step)
    _remember_market(obs, step, action)
    return action


# ---- cell ----

from pathlib import Path
import hashlib
import shutil
import tarfile

ROOT = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd()
submission = ROOT / "submission.py"

# Kaggle обычно запускает ноутбук из /kaggle/working.
# Если cwd другой, переносим готовый файл туда.
local_submission = Path("submission.py").resolve()
if local_submission != submission.resolve():
    shutil.copy2(local_submission, submission)

main = ROOT / "main.py"
shutil.copy2(submission, main)

archive = ROOT / "submission.tar.gz"
with tarfile.open(archive, "w:gz") as tf:
    tf.add(submission, arcname="submission.py")

data = submission.read_bytes()
compile(data, "submission.py", "exec")

print("build ok")
print("submission.py:", submission)
print("bytes:", len(data))
print("sha256:", hashlib.sha256(data).hexdigest())
print("archive:", archive)


# ---- cell ----

# اختبار الدخان الاختياري في وقت التشغيل
try:
    import importlib.util
    from kaggle_environments import make

    spec = importlib.util.spec_from_file_location("c166_submission", submission)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 96, "seed": 166},
        debug=True,
    )
    env.run([mod.agent, mod.agent])

    final = env.steps[-1]
    status = [x.status for x in final]
    reward = [x.reward for x in final]

    print("smoke:", status)
    print("reward:", reward)
    assert all(s == "DONE" for s in status), status
except ModuleNotFoundError:
    print("kaggle_environments is unavailable here; build checks already passed.")
