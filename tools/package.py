import gzip, hashlib, importlib.util, inspect, io, sys, tarfile
from pathlib import Path
ROOT = Path(r"D:/hackathon/KAGGRICULTURE")
src = ROOT / "main.py"
raw = src.read_text(encoding="utf-8")
src.write_text(raw, encoding="utf-8", newline="\n")
data = src.read_bytes()
compile(data, "main.py", "exec")

spec = importlib.util.spec_from_file_location("sub_main", src)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
assert len(inspect.signature(mod.agent).parameters) == 1, "agent must take exactly one arg"

# Kaggle does NOT look up the name `agent`. It execs the file and takes
# `[v for v in globals.values() if callable(v)][-1]` -- the last callable defined,
# by position. Defining anything callable after agent() silently submits that
# instead; a demo() there once scored "Validation Episode failed" (TIMEOUT).
from kaggle_environments.agent import get_last_callable
picked = get_last_callable(raw, path=str(src))
assert picked.__name__ == "agent", (
    f"Kaggle would run {picked.__name__}(), not agent() -- "
    "`agent` must be the LAST callable defined in main.py")

from kaggle_environments import make
bad = []
for seat in (0, 1):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 4242})
    env.run([mod.agent, "starter"] if seat == 0 else ["starter", mod.agent])
    assert [str(s.status) for s in env.steps[-1]] == ["DONE", "DONE"], "episode did not finish"
    # state.action at index i is the reply to the observation at index i-1.
    for step, frame in enumerate(env.steps[1:], start=1):
        a = frame[seat].action
        if a is None:
            continue
        hands = env.steps[step - 1][seat].observation["farms"][seat]["hands"]
        if not (isinstance(a.get("farmer"), list) and a["farmer"]):
            bad.append((step, "farmer"))
        if len(a.get("hands", [])) != len(hands):
            bad.append((step, f"hands {len(a.get('hands', []))}!={len(hands)}"))
        if len(a.get("market", [])) > 10:
            bad.append((step, "market>10"))
        if any(not (isinstance(o, list) and o) for o in a.get("hands", []) + a.get("market", [])):
            bad.append((step, "empty order"))
    print(f"  seat {seat}: reward ${env.steps[-1][seat].reward:,.0f}")
assert not bad, f"invalid actions: {bad[:5]}"

# The validation episode Kaggle actually runs: the submitted FILE against itself.
# Passing mod.agent above bypasses Kaggle's loader and its per-step actTimeout,
# so every check up to here can pass on a file that fails validation.
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 4242})
env.run([str(src), str(src)])
assert len(env.steps) == 720, f"self-play stopped at frame {len(env.steps)}"
assert [str(s.status) for s in env.steps[-1]] == ["DONE", "DONE"], \
    f"self-play statuses {[str(s.status) for s in env.steps[-1]]} (TIMEOUT = too slow per step)"
print(f"  self-play (as Kaggle loads it): 720 frames, ${env.steps[-1][0].reward:,.0f}")

out = ROOT / "submission.tar.gz"
with out.open("wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz, \
        tarfile.open(fileobj=gz, mode="w") as tar:
    info = tarfile.TarInfo("main.py"); info.size = len(data); info.mtime = 0; info.mode = 0o644
    tar.addfile(info, io.BytesIO(data))
with tarfile.open(out, "r:gz") as tar:
    assert tar.getnames() == ["main.py"], tar.getnames()
    assert hashlib.sha256(tar.extractfile("main.py").read()).hexdigest() == hashlib.sha256(data).hexdigest()
print(f"OK  main.py {len(data)} bytes  sha256 {hashlib.sha256(data).hexdigest()[:16]}…")
print(f"    {out.name} {out.stat().st_size} bytes, root member main.py")
