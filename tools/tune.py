"""Optuna search over the agent's tunable constants."""
import argparse
import subprocess
import sys
from pathlib import Path

import optuna

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".sweep"
DB = SCRATCH / "tune.db"
OPP = "bench/ref_broker_bea.py"
SEARCH_SPACE = {
    "HIRES": (8, 14),
    "LAND_TARGET": (1, 2),
    "ANIMAL_RESERVE": (0, 3),
    "ANIMAL_PIPELINE": (1, 6),
    "SEED_BATCH": (1, 6),
    "n_sheep": (2, 8),
    "n_cow": (4, 10),
    "n_strawberry": (4, 14),
    "n_wheat": (4, 28),
}

sys.path.insert(0, str(ROOT))
from tools import sweep


def run_eval(name, overrides, games, opp, jobs, seed0):
    path = sweep.materialize(name, overrides)
    eval_runner = (
        "import runpy; runpy.run_path('tools/thrash.py')['environment_make'](); "
        "runpy.run_path('tools/eval.py', run_name='__main__')"
    )
    command = [
        sys.executable, "-c", eval_runner,
        "--me", str(path), "--opp", opp, "--games", str(games),
        "--seed0", str(seed0), "--steps", str(sweep.STEPS), "--jobs", str(jobs),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    output = completed.stdout + completed.stderr
    path.with_suffix(".eval.txt").write_text(output, encoding="utf-8")
    if completed.returncode not in (0, 1):
        raise RuntimeError(f"{name}: eval.py exit {completed.returncode}\n{output}")
    match = sweep.SUMMARY.search(completed.stdout)
    if not match:
        raise RuntimeError(f"{name}: eval.py produced no summary\n{output}")
    expected = games * 2
    if len(sweep.SEED_LINE.findall(completed.stdout)) != expected:
        raise RuntimeError(f"{name}: expected {expected} completed game rows\n{output}")
    values = {k: int(v.replace(",", "")) for k, v in match.groupdict().items()
              if k != "rate"}
    if values["w"] + values["l"] + values["t"] != values["n"] or values["n"] != expected:
        raise RuntimeError(f"{name}: inconsistent W-L-T summary: {match.group(0)}")
    return values["mean"], int(match.group("rate"))


def objective(trial, args):
    params = {key: trial.suggest_int(key, *bounds)
              for key, bounds in SEARCH_SPACE.items()}
    tiles = params["n_sheep"] + params["n_cow"]
    tiles += params["n_strawberry"] + params["n_wheat"]
    if tiles > 25 * params["LAND_TARGET"]:
        raise optuna.TrialPruned(f"{tiles} tiles exceed {25 * params['LAND_TARGET']}")
    overrides = {key: params[key] for key in (
        "HIRES", "LAND_TARGET", "ANIMAL_RESERVE", "ANIMAL_PIPELINE", "SEED_BATCH"
    )}
    overrides.update({
        "ANIMAL_PLAN": ["SHEEP"] * params["n_sheep"] + ["COW"] * params["n_cow"],
        "CROP_PLAN": [("STRAWBERRY", params["n_strawberry"]),
                      ("WHEAT", params["n_wheat"])],
    })
    mean, rate = run_eval(f"trial-{trial.number}", overrides, args.games, args.opp,
                          args.jobs, args.seed0)
    trial.set_user_attr("win_rate", rate)
    return mean


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--games", type=int, default=6)
    ap.add_argument("--opp", default=OPP)
    ap.add_argument("--study", default="kaggri")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--seed0", type=int, default=sweep.SEED0)
    args = ap.parse_args()
    if args.jobs < 1 or args.games < 1 or args.trials < 1:
        ap.error("--trials, --games, and --jobs must be at least 1")
    SCRATCH.mkdir(exist_ok=True)
    storage = f"sqlite:///{DB.as_posix()}"
    study = optuna.create_study(storage=storage, study_name=args.study,
                                load_if_exists=True, direction="maximize")
    study.optimize(lambda trial: objective(trial, args), n_trials=args.trials)

    complete = [t for t in study.trials
                if t.state == optuna.trial.TrialState.COMPLETE]
    print(f"\nStudy {args.study}: {len(study.trials)} trials, {len(complete)} complete")
    if not complete:
        print("No completed trials.")
        return 0
    best = study.best_trial
    print(f"Best trial {best.number}: value={best.value}, win_rate={best.user_attrs.get('win_rate')}%")
    print(f"  params={best.params}")
    print("Top 5 trials:")
    for trial in sorted(complete, key=lambda item: item.value, reverse=True)[:5]:
        print(f"  {trial.number}: value={trial.value}, "
              f"win_rate={trial.user_attrs.get('win_rate')}%, params={trial.params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
