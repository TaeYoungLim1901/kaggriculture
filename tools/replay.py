"""Fetch and report public Kaggriculture replay traces."""
import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
REPLAY_DIR = ROOT / "research" / "replays"
KAGGLE = Path(r"C:\Users\livde\AppData\Roaming\Python\Python314\Scripts\kaggle.exe")


def replay_file(episode):
    return REPLAY_DIR / f"episode-{episode}-replay.json"


def fetch_one(episode):
    target = replay_file(episode)
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"{episode}: cached {target}")
        return

    cli_error = "kaggle CLI failed"
    try:
        result = subprocess.run(
            [str(KAGGLE), "competitions", "replay", str(episode), "-p", str(REPLAY_DIR), "-q"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if result.returncode == 0 and target.exists():
            print(f"{episode}: downloaded {target}")
            return
        cli_error = (result.stderr or result.stdout or cli_error).strip().splitlines()[-1]
    except (OSError, subprocess.SubprocessError) as exc:
        cli_error = str(exc)

    url = f"https://www.kaggle.com/api/v1/competitions/episodes/{episode}/replay"
    try:
        request = Request(url, headers={"User-Agent": "kaggriculture-replay.py"})
        with urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8")
        json.loads(raw)
        with target.open("w", encoding="utf-8") as handle:
            handle.write(raw)
        print(f"{episode}: downloaded {target} (public API)")
    except HTTPError as exc:
        if exc.code == 404:
            print(f"{episode}: 404 not found; skipped")
        else:
            print(f"{episode}: download failed (HTTP {exc.code}; {cli_error})")
    except (OSError, URLError, ValueError) as exc:
        print(f"{episode}: download failed ({cli_error}; {exc})")


def load_replay(value):
    path = replay_file(value) if value.isdigit() else Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        raise SystemExit(f"Replay not found: {path}. Run fetch first.")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle), path


def winner_info(data):
    rewards = data.get("rewards") or [0, 0]
    player = 0 if rewards[0] >= rewards[1] else 1
    names = data.get("info", {}).get("TeamNames") or []
    if not names:
        names = [agent.get("Name", f"seat {i}") for i, agent in enumerate(data.get("info", {}).get("Agents", []))]
    name = names[player] if player < len(names) else f"seat {player}"
    return player, name, rewards


def action_items(action):
    yield action.get("farmer", [])
    yield from action.get("hands", []) or []
    yield from action.get("market", []) or []


def action_verb(action):
    return action[0] if isinstance(action, list) and action else None


def build_order(data, player):
    wanted = {"HIRE", "BUY_ANIMAL", "BUY_SEED"}
    timeline = []
    for step, frame in enumerate(data.get("steps", [])[:120]):
        events = Counter()
        for action in action_items(frame[player].get("action", {})):
            verb = action_verb(action)
            if verb and (verb in wanted or verb.startswith("BUILD")):
                text = " ".join(str(part) for part in action)
                if verb == "HIRE":
                    text = verb
                events[text] += 1
        if events:
            timeline.append((step, tuple(sorted(events.items()))))

    runs = []
    for step, events in timeline:
        if runs and runs[-1][2] == events and runs[-1][1] == step - 1:
            runs[-1] = (runs[-1][0], step, events)
        else:
            runs.append((step, step, events))
    return runs


def format_events(events):
    return ", ".join(text + (f" x{count}" if count > 1 else "") for text, count in events)


def final_composition(data, player):
    final = data["steps"][-1][player]["observation"]["farms"][player]
    structures, animals, crops = Counter(), Counter(), Counter()
    for row in final.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT" and tile.get("crop"):
                crops[tile["crop"]] += 1
            elif kind not in (None, "WEED"):
                structures[kind] += 1
                if tile.get("animal"):
                    animals[tile["animal"]] += 1
    return final.get("money", 0), structures, animals, crops


def executed_sell(previous, current, item):
    if previous is None:
        return 0
    old_private = previous.get("private", {})
    new_private = current.get("private", {})
    old = old_private.get("shed", {}).get(item, 0)
    new = new_private.get("shed", {}).get(item, 0)
    dropped = 0
    if current.get("day") != previous.get("day"):
        dropped = sum(inv.get(item, 0) for inv in old_private.get("inventories", []))
    return max(0, old - new + dropped)


def sell_profile(data, player):
    steps = data["steps"]
    prices = steps[0][player]["observation"].get("market", {}).get("prices", {})
    products = list(prices)
    stats = {
        product: {"requested": 0, "sold": 0, "value": 0, "daily": defaultdict(float),
                  "sizes": Counter(), "turns": Counter()}
        for product in products
    }
    for step, frame in enumerate(steps):
        state = frame[player]
        observation = state["observation"]
        orders = Counter()
        for order in state.get("action", {}).get("market", []) or []:
            if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
                item, quantity = order[1], int(order[2])
                stats.setdefault(item, {"requested": 0, "sold": 0, "value": 0,
                                        "daily": defaultdict(float), "sizes": Counter(), "turns": Counter()})
                stats[item]["requested"] += quantity
                stats[item]["sizes"][quantity] += 1
                stats[item]["turns"][step % 24] += 1
                orders[item] += quantity
        previous = steps[step - 1][player]["observation"] if step else None
        for item, requested in orders.items():
            sold = min(requested, executed_sell(previous, observation, item))
            price = observation.get("market", {}).get("prices", {}).get(item, 0)
            revenue = sold * price
            stats[item]["sold"] += sold
            stats[item]["value"] += revenue
            stats[item]["daily"][observation.get("day", step // 24)] += revenue
    return stats, products


def counter_text(counter, turn=False):
    if not counter:
        return "-"
    parts = []
    for key, count in sorted(counter.items()):
        label = f"{key:02d}" if turn else str(key)
        parts.append(f"{label}x{count}")
    return ", ".join(parts)


def print_sell_report(stats, products, label):
    all_products = list(products) + [item for item in stats if item not in products]
    print(f"\n{label}  product          sold  mean price  revenue")
    for item in all_products:
        row = stats[item]
        mean = row["value"] / row["sold"] if row["sold"] else 0
        print(f"{label:3}  {item:<12} {row['sold']:8d}  {mean:10.1f}  ${row['value']:8,.0f}")
    mismatches = [(item, stats[item]["requested"], stats[item]["sold"])
                  for item in all_products if stats[item]["requested"] != stats[item]["sold"]]
    if mismatches:
        print("  requested -> executed: " + ", ".join(
            f"{item} {requested}->{sold}" for item, requested, sold in mismatches))

    daily = defaultdict(float)
    for row in stats.values():
        for day, value in row["daily"].items():
            daily[day] += value
    max_revenue = max(daily.values(), default=0)
    scale = max_revenue or 1
    max_day = max(daily, default=0)
    print("\nDaily revenue (each # is 1/20 of the largest day):")
    print(f"day | {label:<28}")
    for day in range(max_day + 1):
        value = daily[day]
        width = max(1, round(20 * value / scale)) if value else 0
        print(f"{day:02d}  | {'#' * width:<20} ${value:7,.0f}")

    print("\nSell cadence (requested SELL orders):")
    print("product      order sizes                 turn-of-day")
    for item in all_products:
        row = stats[item]
        print(f"{item:<12} {counter_text(row['sizes']):<28} {counter_text(row['turns'], turn=True)}")


def print_action_histogram(data, player):
    daily = defaultdict(Counter)
    for step, frame in enumerate(data["steps"]):
        state = frame[player]
        day = state["observation"].get("day", step // 24)
        for action in action_items(state.get("action", {})):
            verb = action_verb(action)
            if verb:
                daily[day][verb] += 1
    print("\nAction verbs per day (farmer + hands + market):")
    for day in sorted(daily):
        counts = daily[day]
        print(f"day {day:02d} total {sum(counts.values()):3d}: " +
              ", ".join(f"{verb}={count}" for verb, count in sorted(counts.items())))


def report(value):
    data, path = load_replay(value)
    player, name, rewards = winner_info(data)
    episode = data.get("info", {}).get("EpisodeId", value)
    label = "WINNER"
    tie = " (tie; seat 0 used)" if rewards[0] == rewards[1] else ""
    print(f"Replay {episode}: winning seat {player} — {name}{tie}")
    print(f"Scores: seat 0 ${rewards[0]:,.0f}, seat 1 ${rewards[1]:,.0f}  [{path}]")

    print("\nBuild order timeline (first 120 steps; identical runs collapsed):")
    for start, end, events in build_order(data, player):
        span = f"step {start}" if start == end else f"steps {start}-{end}"
        print(f"{span}: {format_events(events)}")

    money, structures, animals, crops = final_composition(data, player)
    print(f"\nFinal composition (money ${money:,.0f}):")
    print("  structures: " + (", ".join(f"{k}={v}" for k, v in sorted(structures.items())) or "none"))
    print("  animals:    " + (", ".join(f"{k}={v}" for k, v in sorted(animals.items())) or "none"))
    print("  crop tiles: " + (", ".join(f"{k}={v}" for k, v in sorted(crops.items())) or "none"))

    stats, products = sell_profile(data, player)
    print_sell_report(stats, products, label)
    print_action_histogram(data, player)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch = subparsers.add_parser("fetch", help="download replay JSONs")
    fetch.add_argument("episode", nargs="+", help="episode IDs")
    report_parser = subparsers.add_parser("report", help="analyze one replay")
    report_parser.add_argument("replay", help="episode ID or replay JSON path")
    args = parser.parse_args()
    if args.command == "fetch":
        for episode in args.episode:
            if not episode.isdigit():
                print(f"{episode}: invalid episode ID; skipped")
                continue
            fetch_one(int(episode))
    else:
        report(args.replay)


if __name__ == "__main__":
    main()
