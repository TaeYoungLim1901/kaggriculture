"""Print aggregate actions from a hard-coded Kaggriculture replay."""
import argparse
import collections
import importlib.util
from pathlib import Path


def load_actions(path):
    spec = importlib.util.spec_from_file_location("replay", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module._ACTIONS)


def units(entry):
    return [entry.get("farmer", ["PASS"]), *(entry.get("hands") or [])]


def verb(action):
    return action[0] if isinstance(action, list) and action else None


def day_text(counter):
    return " ".join(f"d{day}:{count}" for day, count in sorted(counter.items()) if count)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("agent", type=Path, help="bench agent containing _ACTIONS")
    actions = load_actions(parser.parse_args().agent)

    print(f"entries: {len(actions)} ({len(actions) // 24} days, zero-based days/hours)")

    print("\nBUY_LAND")
    for i, entry in enumerate(actions):
        for action in entry.get("market", []):
            if verb(action) == "BUY_LAND":
                print(f"  day {i // 24}, hour {i % 24}")

    print("\nHIRE per day")
    hires = collections.Counter(
        i // 24
        for i, entry in enumerate(actions)
        for action in entry.get("market", [])
        if verb(action) == "HIRE"
    )
    print("  " + day_text(hires) + f"  (total {sum(hires.values())})")

    print("\nBUY_ANIMAL")
    animals = collections.Counter()
    for i, entry in enumerate(actions):
        for action in entry.get("market", []):
            if verb(action) == "BUY_ANIMAL":
                animals[action[1]] += int(action[2])
                print(f"  day {i // 24}, hour {i % 24}: {action[1]} x{action[2]}")
    print("  totals: " + ", ".join(f"{animal} x{n}" for animal, n in sorted(animals.items())))

    print("\nBUILD_PASTURE / BUILD_COOP")
    for op in ("BUILD_PASTURE", "BUILD_COOP"):
        days = collections.Counter(
            i // 24
            for i, entry in enumerate(actions)
            for action in units(entry)
            if verb(action) == op
        )
        print(f"  {op}: {sum(days.values())} requests; {day_text(days) or 'none'}")

    print("\nPLANT requests by crop")
    planted = {}
    for crop in sorted({
        action[1]
        for entry in actions
        for action in units(entry)
        if verb(action) == "PLANT" and len(action) > 1
    }):
        days = collections.Counter(
            i // 24
            for i, entry in enumerate(actions)
            for action in units(entry)
            if verb(action) == "PLANT" and len(action) > 1 and action[1] == crop
        )
        planted[crop] = sum(days.values())
        print(f"  {crop}: {planted[crop]}; {day_text(days)}")

    fert = collections.Counter(
        i // 24
        for i, entry in enumerate(actions)
        for action in units(entry)
        if verb(action) == "FERTILIZE"
    )
    print("\nFERTILIZE")
    print(f"  {sum(fert.values())} requests; {day_text(fert)}")
    print("  crop is not encoded by the FERTILIZE opcode; map it by replaying the actions.")

    print("\nSELL: units and hours")
    sell = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, entry in enumerate(actions):
        for action in entry.get("market", []):
            if verb(action) == "SELL" and len(action) >= 3:
                sell[action[1]][i // 24].append((i % 24, int(action[2])))
    for item in sorted(sell):
        rows = []
        for day, orders in sell[item].items():
            hours = collections.Counter(hour for hour, _ in orders)
            text = ",".join(str(hour) + (f"x{n}" if n > 1 else "") for hour, n in sorted(hours.items()))
            rows.append(f"d{day}={sum(n for _, n in orders)}@{text}")
        print(f"  {item}: " + "; ".join(rows))

    print("\nUNIT ACTIONS per day (issued/non-PASS)")
    for day in range((len(actions) + 23) // 24):
        issued = [action for entry in actions[day * 24:(day + 1) * 24] for action in units(entry)]
        work = sum(verb(action) != "PASS" for action in issued)
        print(f"  d{day}: {len(issued)}/{work}")


if __name__ == "__main__":
    main()
