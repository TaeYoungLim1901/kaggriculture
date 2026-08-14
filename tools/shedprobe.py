"""Is the shed structurally over capacity? Print daily shed totals + panic firings.

    python tools/shedprobe.py [agent.py]     # defaults to main.py
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
target = sys.argv[1] if len(sys.argv) > 1 else ROOT / "main.py"
spec = importlib.util.spec_from_file_location("m", target)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

from kaggle_environments import make
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 90001})
env.run([m.agent, "starter"])

SHED_CAP, PANIC_AT = m.SHED_CAP, m.SHED_CAP - 20
print(f"{'day':>4} {'shed':>5} {'panic?':>6}  composition")
panic_days = 0
for step, frame in enumerate(env.steps):
    if step % 24 != 23:                      # end of day
        continue
    shed = frame[0].observation["private"]["shed"] or {}
    total = sum(shed.values())
    hot = total > PANIC_AT
    panic_days += hot
    top = sorted(shed.items(), key=lambda kv: -kv[1])[:4]
    print(f"{step // 24:>4} {total:>5} {'PANIC' if hot else '':>6}  "
          + " ".join(f"{k}={v}" for k, v in top if v))
print(f"\ncap {SHED_CAP}, panic threshold {PANIC_AT}; days over threshold: {panic_days}/30")
