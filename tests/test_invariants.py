import copy
import sys
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as rules

import main as submission


SEED = 4242
EPISODE_STEPS = 720
BOARD_SIZE = 10
TURNS_PER_DAY = 24
MIN_END_MONEY = 60000

PRODUCTS = set(rules.PRODUCTS)
CROPS = set(rules.CROPS)
ANIMALS = set(rules.ANIMALS)
ALL_ITEMS = PRODUCTS | ANIMALS
MOVES = set(rules.FARMER_MOVES)
UNIT_VERBS = (
    "NORTH", "SOUTH", "EAST", "WEST", "PASS", "DROP", "PICKUP", "PLACE",
    "PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG", "BUILD_COOP",
    "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE",
)
MARKET_VERBS = ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "SELL", "HIRE", "BUY_LAND")
ALL_VERBS = UNIT_VERBS + MARKET_VERBS


def _get(value, key, default=None):
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _plain(value):
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _positive_int(value):
    return type(value) is int and value > 0


def _verb(action):
    return action[0] if isinstance(action, list) and action and isinstance(action[0], str) else "<invalid>"


def _pass_action():
    return {"farmer": ["PASS"], "hands": [], "market": []}


def _run_episode(tested_seat):
    caught = []

    def tested_agent(obs):
        try:
            return submission.agent(obs)
        except BaseException as exc:  # Make a swallowed agent exception observable.
            caught.append(repr(exc))
            return _pass_action()

    agents = ["pass", "pass"]
    agents[tested_seat] = tested_agent
    env = None
    error = None
    try:
        env = make("kaggriculture", configuration={"episodeSteps": EPISODE_STEPS, "seed": SEED})
        env.run(agents)
    except BaseException as exc:
        error = repr(exc)
    return {"env": env, "seat": tested_seat, "caught": caught, "error": error}


def _validate_position(position, label):
    assert isinstance(position, (list, tuple)) and len(position) == 2, label
    assert all(type(coord) is int for coord in position), label
    assert all(0 <= coord < BOARD_SIZE for coord in position), label


def _validate_observation_coordinates(obs):
    farms = _get(obs, "farms", [])
    assert isinstance(farms, list) and len(farms) == 2
    for farm in farms:
        tiles = _get(farm, "tiles", [])
        assert isinstance(tiles, list) and len(tiles) == BOARD_SIZE
        assert all(isinstance(row, list) and len(row) == BOARD_SIZE for row in tiles)
        _validate_position(_get(farm, "farmer"), "farmer coordinates")
        for index, hand in enumerate(_get(farm, "hands", []) or []):
            _validate_position(hand, f"hand coordinates {index}")


def _validate_unit_action(action):
    assert isinstance(action, list) and action and isinstance(action[0], str)
    op = action[0]
    assert op in UNIT_VERBS, f"unknown unit verb: {op}"
    if op in MOVES or op in {"PASS", "DROP", "WATER", "HARVEST", "FERTILIZE", "DIG",
                              "BUILD_COOP", "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE"}:
        assert len(action) == 1, f"wrong arity: {action}"
    elif op == "PLANT":
        assert len(action) == 2 and action[1] in CROPS, f"invalid plant: {action}"
    elif op in {"PICKUP", "PLACE"}:
        assert len(action) in (2, 3) and action[1] in ALL_ITEMS, f"invalid shed action: {action}"
        if len(action) == 3:
            assert _positive_int(action[2]), f"invalid quantity: {action}"


def _validate_market_action(order):
    assert isinstance(order, list) and order and isinstance(order[0], str)
    op = order[0]
    assert op in MARKET_VERBS, f"unknown market verb: {op}"
    if op in {"HIRE", "BUY_LAND"}:
        assert len(order) == 1, f"wrong arity: {order}"
        return
    assert len(order) == 3 and _positive_int(order[2]), f"invalid market order: {order}"
    if op == "BUY_SEED":
        assert order[1] in CROPS
    elif op == "BUY_ANIMAL":
        assert order[1] in ANIMALS
    elif op == "BUY_PRODUCT":
        assert order[1] in {"WHEAT", "FERTILIZER"}
    else:
        assert order[1] in PRODUCTS


def _check_determinism(episodes):
    env = episodes[0]["env"]
    assert env is not None
    obs = env.steps[0][0].observation
    first = submission.agent(copy.deepcopy(obs))
    second = submission.agent(copy.deepcopy(obs))
    assert first == second, f"different actions: {first!r} != {second!r}"


def _check_never_raises(episodes):
    for episode in episodes:
        assert episode["error"] is None, episode["error"]
        assert not episode["caught"], episode["caught"]
        env = episode["env"]
        assert env is not None and len(env.steps) == EPISODE_STEPS
        assert all(str(state.status) == "DONE" for state in env.steps[-1])


def _check_schema(episodes):
    for episode in episodes:
        env = episode["env"]
        assert env is not None
        seat = episode["seat"]
        for index in range(1, len(env.steps)):
            previous = env.steps[index - 1][seat].observation
            current = env.steps[index][seat].observation
            _validate_observation_coordinates(previous)
            _validate_observation_coordinates(current)

            action = env.steps[index][seat].action
            assert isinstance(action, Mapping)
            farmer = _get(action, "farmer", ["PASS"])
            _validate_unit_action(farmer)
            hands = _get(action, "hands", [])
            assert isinstance(hands, list)
            for hand_action in hands:
                _validate_unit_action(hand_action)
            market = _get(action, "market", [])
            assert isinstance(market, list) and len(market) <= 10
            for order in market:
                _validate_market_action(order)


def _unit_effects(previous, seat, action):
    farms = _get(previous, "farms", [])
    farm = copy.deepcopy(farms[seat])
    private = copy.deepcopy(_get(previous, "private", {}))
    hands = _get(farm, "hands", []) or []
    actions = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    day = int(_get(previous, "day", 0) or 0)

    demand = {}
    for item in actions:
        if isinstance(item, list) and len(item) >= 2 and item[0] == "PLANT":
            demand[item[1]] = demand.get(item[1], 0) + 1
    seeds = _get(private, "seeds", {}) or {}
    blocked = {crop for crop, count in demand.items() if count > seeds.get(crop, 0)}

    effects = []
    for index, original in enumerate(actions):
        exists = index == 0 or index - 1 < len(hands)
        allowed = ["PASS"] if (
            isinstance(original, list) and len(original) >= 2
            and original[0] == "PLANT" and original[1] in blocked
        ) else original
        before_farm = _plain(farm)
        before_private = _plain(private)
        if exists:
            try:
                rules._apply_unit_action(
                    farm, private, index, allowed, BOARD_SIZE, day, TURNS_PER_DAY
                )
            except BaseException:
                pass
        effects.append(_plain(farm) != before_farm or _plain(private) != before_private)
    return effects, farm, private


def _market_effects(previous, orders, after_units_farm, after_units_private):
    farm = copy.deepcopy(after_units_farm)
    private = copy.deepcopy(after_units_private)
    market = copy.deepcopy(_get(previous, "market", {}))
    effects = []
    for order in orders[:10]:
        parsed = rules._parse_order(order)
        if parsed is None:
            effects.append(False)
            continue
        op = parsed["type"]
        if op == "HIRE":
            before = len(_get(farm, "hands", []) or [])
            rules._do_hire(farm, private, BOARD_SIZE)
            effects.append(len(_get(farm, "hands", []) or []) > before)
        elif op == "BUY_LAND":
            before = len(_get(farm, "unlocked_quadrants", []) or [])
            rules._do_buy_land(farm, BOARD_SIZE)
            effects.append(len(_get(farm, "unlocked_quadrants", []) or []) > before)
        else:
            committed = False
            for _ in range(parsed["remaining"]):
                item = parsed["item"]
                if op == "SELL" and item in PRODUCTS:
                    price = rules.market_price(item, market["inventory"][item], market.get("params"))
                elif op == "BUY_PRODUCT" and item in {"WHEAT", "FERTILIZER"}:
                    price = rules.market_price(item, market["inventory"][item] - 1, market.get("params"))
                elif op == "BUY_SEED" and item in CROPS:
                    price = rules.CROPS[item]["seed"]
                elif op == "BUY_ANIMAL" and item in ANIMALS:
                    price = rules.ANIMALS[item]["cost"]
                else:
                    break
                if not rules._commit_unit(op, item, price, farm, private, market):
                    break
                committed = True
            effects.append(committed)
    return effects


def _check_noops(episodes):
    stats = {verb: [0, 0] for verb in ALL_VERBS}
    for episode in episodes:
        env = episode["env"]
        if env is None:
            continue
        seat = episode["seat"]
        for index in range(1, len(env.steps)):
            # Replay trap: action at i answers observation at i-1; observation i is post-action.
            previous = env.steps[index - 1][seat].observation
            action = env.steps[index][seat].action
            if not isinstance(action, Mapping):
                stats["<invalid>"] = [stats.get("<invalid>", [0, 0])[0] + 1,
                                       stats.get("<invalid>", [0, 0])[1] + 1]
                continue

            unit_actions = [action.get("farmer", ["PASS"]), *(action.get("hands", []) or [])]
            unit_effects, after_units_farm, after_units_private = _unit_effects(previous, seat, action)
            for emitted, effective in zip(unit_actions, unit_effects):
                verb = _verb(emitted)
                stats.setdefault(verb, [0, 0])
                stats[verb][0] += 1
                stats[verb][1] += not effective

            market = action.get("market", []) or []
            market_effects = _market_effects(previous, market, after_units_farm, after_units_private)
            for emitted, effective in zip(market, market_effects):
                verb = _verb(emitted)
                stats.setdefault(verb, [0, 0])
                stats[verb][0] += 1
                stats[verb][1] += not effective

    print("No-op table (PASS is intentionally excluded from the threshold):")
    print("  verb                     emitted  no-op  rate")
    bad = []
    for verb in sorted(stats):
        emitted, noops = stats[verb]
        rate = 0.0 if emitted == 0 else 100.0 * noops / emitted
        print(f"  {verb:<24} {emitted:7d} {noops:6d} {rate:5.1f}%")
        if verb != "PASS" and emitted and noops * 100 >= emitted * 5:
            bad.append(f"{verb}={noops}/{emitted}")
    assert not bad, "no-op rate >= 5%: " + ", ".join(bad)


def _check_economics(episodes):
    for episode in episodes:
        env = episode["env"]
        assert env is not None
        seat = episode["seat"]
        for row in env.steps:
            money = _get(_get(row[seat].observation, "farms", [])[seat], "money")
            assert money >= 0, f"negative money: {money}"
        final_money = _get(_get(env.steps[-1][seat].observation, "farms", [])[seat], "money")
        assert final_money >= MIN_END_MONEY, f"final money {final_money} < {MIN_END_MONEY}"


def _check_herd_cap(episodes):
    """Never own more animals than ANIMAL_PLAN asks for.

    `_wanted` derives the still-to-buy list from animals standing on tiles, so an
    animal in the shed or in a hand's inventory used to read as still-wanted and got
    re-bought while in transit -- seed 7 ended with 13 animals against a plan of 11.
    Owned means on a tile, in the shed, or carried.
    """
    cap = len(submission.ANIMAL_PLAN)
    for episode in episodes:
        env = episode["env"]
        assert env is not None
        seat = episode["seat"]
        for row in env.steps:
            obs = row[seat].observation
            farm = _get(_get(obs, "farms", [])[seat], "tiles", []) or []
            owned = sum(
                1
                for tile_row in farm
                for tile in (tile_row or [])
                if isinstance(tile, Mapping) and "animal" in tile
            )
            private = _get(obs, "private", {}) or {}
            holders = [_get(private, "shed", {}) or {}]
            holders += list(_get(private, "inventories", []) or [])
            owned += sum(
                count
                for holder in holders
                for animal, count in (holder or {}).items()
                if animal in ANIMALS and isinstance(count, int)
            )
            day, hour = _get(obs, "day", 0), _get(obs, "hour", 0)
            assert owned <= cap, f"own {owned} animals, plan is {cap} (d{day} h{hour})"


def _check_hire_wage(episodes):
    """_fib must agree with the env: fib(0) = 1, not 0.

    Seeding at (0, 1) priced every hire one place too cheap -- the 9th hire of the
    day at $21 against the $34 the env charges -- so the affordability guard could
    request a hire it could not pay for and burn the order slot.
    """
    expected = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    got = [submission._fib(n) for n in range(len(expected))]
    assert got == expected, f"_fib {got} != env {expected}"


def _run_check(name, check, failures):
    try:
        check()
    except BaseException as exc:
        failures.append(name)
        print(f"FAIL {name}: {exc}")
    else:
        print(f"PASS {name}")


def main():
    episodes = [_run_episode(seat) for seat in (0, 1)]
    failures = []
    _run_check("determinism", lambda: _check_determinism(episodes), failures)
    _run_check("never raises", lambda: _check_never_raises(episodes), failures)
    _run_check("action schema", lambda: _check_schema(episodes), failures)
    _run_check("no-op rate", lambda: _check_noops(episodes), failures)
    _run_check("economic floor", lambda: _check_economics(episodes), failures)
    _run_check("herd cap", lambda: _check_herd_cap(episodes), failures)
    _run_check("hire wage", lambda: _check_hire_wage(episodes), failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
