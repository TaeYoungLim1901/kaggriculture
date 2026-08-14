"""When does each build/buy actually happen? baseline vs expanded config C."""
import importlib.util, sys
from pathlib import Path
from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
WATCH = ("BUILD_PASTURE", "BUY_ANIMAL", "PLACE", "BUY_SEED", "BUY_LAND", "PLANT")


def load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


targets = [(p, p) for p in sys.argv[1:]] or [("main.py", ROOT / "main.py")]
for label, path in targets:
    mod = load(path)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 90001})
    env.run([mod.agent, "starter"])
    first, count, money, work = {}, {}, {}, {}
    for step, frame in enumerate(env.steps[1:], start=1):
        day = (step - 1) // 24
        money[day] = frame[0].observation["farms"][0]["money"]
        act = frame[0].action
        if not act:
            continue
        units = [act.get("farmer")] + (act.get("hands") or [])
        work[day] = work.get(day, 0) + sum(
            bool(u) and u[0] != "PASS" for u in units
        )
        verbs = [o[0] for o in act.get("market", [])]
        verbs += [o[0] for u in [act.get("farmer")] + act.get("hands", []) if u for o in [u]]
        for v in verbs:
            if v in WATCH:
                first.setdefault(v, day)
                count[v] = count.get(v, 0) + 1
    print(f"\n--- {label} ---")
    for v in WATCH:
        print(f"  {v:<14} first day {first.get(v, '--'):>3}   total {count.get(v, 0)}")
    print("  money by day:", " ".join(f"{d}:{money[d]:.0f}" for d in sorted(money) if d < 16))
    print("  work by day:", " ".join(f"{d}:{work[d]}" for d in sorted(work)))
