"""Record, bake, and compare a trace with its source agent by file path."""
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEDS = (90001, 1000, 8919)
STEPS = 720


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(path, seed):
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": STEPS, "seed": seed})
    env.run([str(path), "starter"])
    assert [str(s.status) for s in env.steps[-1]] == ["DONE", "DONE"]
    return env


def _first_divergence(left, right):
    for frame_index, (a, b) in enumerate(zip(left.steps[1:], right.steps[1:]), start=1):
        for seat in (0, 1):
            if a[seat].action != b[seat].action:
                return frame_index - 1, seat
    if len(left.steps) != len(right.steps):
        return min(len(left.steps), len(right.steps)) - 1, None
    return None


def _pct(a, b):
    return 100.0 * (b - a) / max(abs(a), 1.0)


def main():
    record = _load("trace_record", ROOT / "tools" / "record.py")
    bake = _load("trace_bake", ROOT / "tools" / "bake.py")
    rows = []
    with tempfile.TemporaryDirectory(prefix="kaggriculture-trace-") as temp:
        temp = Path(temp)
        for seed in SEEDS:
            blob = temp / f"main_{seed}.b85"
            record.record_episode(ROOT / "main.py", "starter", seed, blob, STEPS)
            baked = temp / f"trace_{seed}.py"
            bake.bake_blob(blob, baked)
            source_env = _run(ROOT / "main.py", seed)
            replay_env = _run(baked, seed)
            source = [float(s.reward or 0) for s in source_env.steps[-1]]
            replay = [float(s.reward or 0) for s in replay_env.steps[-1]]
            divergence = _first_divergence(source_env, replay_env)
            rows.append((seed, source, replay, divergence))

        # Leave the acceptance artifact as the documented seed-90001 trace.
        final_blob = ROOT / "build" / "main.b85"
        record.record_episode(ROOT / "main.py", "starter", 90001, final_blob, STEPS)
        bake.bake_blob(final_blob, ROOT / "build" / "trace_main.py")

    print("seed    source seat0  replay seat0  delta     source seat1  replay seat1  delta     divergence")
    failed = False
    for seed, source, replay, divergence in rows:
        d0, d1 = _pct(source[0], replay[0]), _pct(source[1], replay[1])
        label = "none" if divergence is None else f"step {divergence[0]} seat {divergence[1]}"
        print(f"{seed:5d}  {source[0]:13.0f}  {replay[0]:12.0f}  {d0:+6.2f}%  "
              f"{source[1]:13.0f}  {replay[1]:12.0f}  {d1:+6.2f}%  {label}")
        failed |= abs(d0) > 2.0 or abs(d1) > 2.0 or divergence is not None
    if failed:
        print("FAIL: replay diverged; the table gives the first differing effective step.")
        return 1
    print("OK: all final-money pairs are within 2% and action streams match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
