"""Measure per-unit target churn and action efficiency for one episode.

    python tools/thrash.py main.py
    python tools/thrash.py .sweep/T10.py
"""
import argparse
import importlib.util
import inspect
import statistics
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
META = "bench/v16_rc5_high_score_8c_4s_premium_market_.py"
MOVEMENT = {"NORTH", "SOUTH", "EAST", "WEST"}


def load(path):
    path = (ROOT / path).resolve()
    spec = importlib.util.spec_from_file_location(f"thrash_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def positions(obs):
    farms = obs.get("farms", [])
    seat = int(obs.get("player", 0) or 0)
    farm = farms[seat] if seat < len(farms) else {}
    return [tuple(farm.get("farmer", [4, 4]))] + [tuple(p) for p in farm.get("hands", [])]


def verb(action):
    return action[0] if isinstance(action, list) and action else "PASS"


def environment_make():
    try:
        from kaggle_environments import make
        return make
    except ModuleNotFoundError:
        # This machine has the competition package without its optional pip
        # dependencies. Kaggriculture itself only needs these two import shims.
        if "jsonschema" not in sys.modules:
            jsonschema = types.ModuleType("jsonschema")
            jsonschema.validate = lambda *_args, **_kwargs: None
            sys.modules["jsonschema"] = jsonschema
        if "requests" not in sys.modules:
            requests = types.ModuleType("requests")
            exceptions = types.ModuleType("requests.exceptions")
            exceptions.Timeout = type("Timeout", (Exception,), {})
            exceptions.RequestException = type("RequestException", (Exception,), {})
            requests.exceptions = exceptions
            requests.post = lambda *_args, **_kwargs: None
            sys.modules["requests"] = requests
            sys.modules["requests.exceptions"] = exceptions
        package = Path.home() / "AppData" / "Roaming" / "Python" / "Python314" / "site-packages" / "kaggle_environments"
        init = package / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            "kaggle_environments", init, submodule_search_locations=[str(package)]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["kaggle_environments"] = module
        spec.loader.exec_module(module)
        return module.make


def measure(path, opponent="starter", seed=90001, steps=720):
    module = load(path)
    source_lines, first_line = inspect.getsourcelines(module._act)
    plan_line = next(
        first_line + n for n, line in enumerate(source_lines)
        if "if i not in plan:" in line
    )
    code = module._act.__code__
    target_logs = []
    records = []
    current = {"targets": {}, "seen": set()}
    turn = 0

    def local_trace(frame, event, _arg):
        if event == "line" and frame.f_lineno == plan_line:
            i = frame.f_locals["i"]
            if i not in current["seen"]:
                plan = frame.f_locals["plan"]
                current["targets"][i] = None if i not in plan else tuple(plan[i][0])
                current["seen"].add(i)
        return local_trace

    def global_trace(frame, event, arg):
        if event == "call" and frame.f_code is code:
            return local_trace
        return None

    def traced_agent(obs):
        nonlocal turn, current
        current = {"targets": {}, "seen": set()}
        sys.settrace(global_trace)
        try:
            result = module.agent(obs)
        finally:
            sys.settrace(None)
        current["positions"] = positions(obs)
        current["actions"] = [result.get("farmer", ["PASS"])] + result.get("hands", [])
        target_logs.append(current)
        turn += 1
        return result

    env = environment_make()("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
    env.run([traced_agent, opponent])
    if not target_logs:
        raise RuntimeError("episode produced no agent calls")
    turns = len(target_logs)

    runs = []
    state = {}
    movement = productive = 0
    for t, record in enumerate(target_logs):
        for action in record["actions"]:
            name = verb(action)
            movement += name in MOVEMENT
            productive += name not in MOVEMENT and name != "PASS"
        for i, target in record["targets"].items():
            old = state.get(i)
            if old is not None and target != old["target"]:
                runs.append(t - old["start"])
            if target is None:
                state.pop(i, None)
            elif old is None or target != old["target"]:
                state[i] = {"target": target, "start": t}
            else:
                state[i] = old
    runs.extend(turns - old["start"] for old in state.values())
    # Count directly from logs so an active final run needs no special casing.
    retargets = 0
    previous = {}
    for t, record in enumerate(target_logs):
        for i, target in record["targets"].items():
            old = previous.get(i)
            if old is not None and target != old and tuple(record["positions"][i]) != old:
                retargets += 1
            previous[i] = target
    return {
        "path": str(path),
        "seed": seed,
        "turns": turns,
        "retargets_before_arrival": retargets,
        "target_runs": len(runs),
        "mean_target_survival": statistics.mean(runs) if runs else 0,
        "movement": movement,
        "productive": productive,
        "movement_per_productive": movement / productive if productive else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="main.py")
    parser.add_argument("--opp", default=META)
    parser.add_argument("--seed", type=int, default=90001)
    parser.add_argument("--steps", type=int, default=720)
    args = parser.parse_args()
    result = measure(args.path, args.opp, args.seed, args.steps)
    print(f"{result['path']} seed {result['seed']} ({result['turns']} turns)")
    print(f"retargets before arrival: {result['retargets_before_arrival']}")
    print(f"target runs: {result['target_runs']}, mean survival: {result['mean_target_survival']:.2f} turns")
    print(f"movement: {result['movement']}, productive: {result['productive']}, "
          f"movement/productive: {result['movement_per_productive']:.2f}")


if __name__ == "__main__":
    main()
