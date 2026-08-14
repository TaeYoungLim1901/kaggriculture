"""Staged bug checks. Run the stage matching what you just changed.

    python tools/check.py edit      # ~10 s  after ANY main.py edit
    python tools/check.py logic     # ~1 m   after changing decision logic
    python tools/check.py strength  # ~2 m   after a change meant to win more
    python tools/check.py ship      # ~1 m   before packaging / submitting
    python tools/check.py all

Cheapest first: `edit` catches the two failure modes that cost real submissions
(non-last `agent`, per-step timeout) in seconds. Extra args pass through to the
underlying tool, e.g. `check.py strength --games 30 --opp bench/v16.py`.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = [sys.executable]


def edit(_args):
    """Compile + Kaggle's own loader + a short file-path self-play."""
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable

    src = ROOT / "main.py"
    raw = src.read_text(encoding="utf-8")
    compile(raw, "main.py", "exec")

    # Kaggle ignores the name `agent` and runs the LAST callable by position.
    picked = get_last_callable(raw, path=str(src))
    assert picked.__name__ == "agent", \
        f"Kaggle would run {picked.__name__}(), not agent() -- agent must be defined last"

    # By FILE PATH, not the function object: only this path enforces actTimeout.
    env = make("kaggriculture", configuration={"episodeSteps": 60, "seed": 4242})
    env.run([str(src), str(src)])
    statuses = [str(s.status) for s in env.steps[-1]]
    assert statuses == ["DONE", "DONE"], f"{statuses} (TIMEOUT = too slow per step)"
    print(f"OK  edit: 60-step self-play clean, ${env.steps[-1][0].reward:,.0f}")
    return 0


def run(*cmd):
    return subprocess.call(PY + [str(ROOT / cmd[0])] + [str(c) for c in cmd[1:]], cwd=ROOT)


STAGES = {
    "edit": edit,
    "logic": lambda a: run("tests/test_invariants.py", *a),
    "strength": lambda a: run("tools/eval.py", *(a or ["--games", "8"])),
    "ship": lambda a: run("tools/package.py", *a),
}


def main(argv):
    stage, args = (argv[0] if argv else "all"), argv[1:]
    names = list(STAGES) if stage == "all" else [stage]
    if stage not in STAGES and stage != "all":
        sys.exit(f"unknown stage {stage!r}; pick one of {', '.join(STAGES)}, all")
    for name in names:
        print(f"\n=== {name} ===", flush=True)
        try:
            code = STAGES[name](args)
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            return 1
        if code:
            print(f"FAIL {name}: exit {code}")
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
