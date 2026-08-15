"""Optuna search over the agent's tunable constants."""
import argparse
import subprocess
import sys
from pathlib import Path

import optuna

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".sweep"
DB = SCRATCH / "tune.db"
OPP = "bench/v15.py"
STAGES = [4, 12, 32]
# HIRE_HOUR0 and HIRE_SLOTS used to be suggested here and then never written into
# `overrides`, so two of the dimensions were pure noise -- every study before
# 2026-08-15 searched nine knobs, not eleven. STRAWBERRY is out and MELON is in:
# the berry line is closed (docs/SWEEP_DERIVED.md) and melon is what the plan runs.
SEARCH_SPACE = {
    "HIRES": (9, 13),
    "HIRE_HOUR0": (4, 9),
    "HIRE_SLOTS": (1, 4),
    "LAND_TARGET": (2, 3),
    "ANIMAL_RESERVE": (0, 3),
    "ANIMAL_PIPELINE": (3, 7),
    "SEED_BATCH": (3, 8),
    "LAST_DAY": (6, 18),
    "DIST_WEIGHT": (10, 30),
    "n_sheep": (2, 8),
    "n_cow": (5, 11),
    "n_melon": (4, 14),
    "n_wheat": (16, 32),
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
    tiles += params["n_melon"] + params["n_wheat"]
    if tiles > 25 * params["LAND_TARGET"]:
        raise optuna.TrialPruned(f"{tiles} tiles exceed {25 * params['LAND_TARGET']}")
    overrides = {key: params[key] for key in (
        "HIRES", "HIRE_HOUR0", "HIRE_SLOTS", "LAND_TARGET", "ANIMAL_RESERVE",
        "ANIMAL_PIPELINE", "SEED_BATCH", "LAST_DAY", "DIST_WEIGHT",
    )}
    overrides.update({
        "ANIMAL_PLAN": ["SHEEP"] * params["n_sheep"] + ["COW"] * params["n_cow"],
        "CROP_PLAN": [("MELON", params["n_melon"]),
                      ("WHEAT", params["n_wheat"])],
    })
    seed0 = args.seed0
    for step, games in enumerate(args.stages):
        mean, rate = run_eval(
            f"trial-{trial.number}-stage-{step}", overrides, games, args.opp,
            args.jobs, seed0
        )
        trial.set_user_attr(f"stage_{step}_value", mean)
        trial.set_user_attr(f"stage_{step}_win_rate", rate)
        trial.set_user_attr("stage_reached", step)
        trial.report(mean, step=step)
        if step < len(args.stages) - 1 and trial.should_prune():
            raise optuna.TrialPruned(f"pruned after stage {step}")
        seed0 += games
    trial.set_user_attr("win_rate", rate)
    return mean


def parse_stages(raw, games):
    if raw:
        try:
            stages = [int(part) for part in raw.split(",")]
        except ValueError as exc:
            raise ValueError("--stages must be comma-separated positive integers") from exc
    elif games != STAGES[0]:
        stages = [games]
    else:
        stages = STAGES[:]
    if not stages or any(stage < 1 for stage in stages) or stages != sorted(set(stages)):
        raise ValueError("stages must be positive and strictly increasing")
    return stages


def trial_value(trial):
    if trial.value is not None:
        return trial.value
    reached = trial.user_attrs.get("stage_reached", -1)
    return trial.user_attrs.get(f"stage_{reached}_value", float("-inf"))


def print_trial(trial, stages):
    reached = trial.user_attrs.get("stage_reached", -1)
    marker = " UNCONFIRMED" if reached == 0 and len(stages) > 1 else ""
    details = []
    for step in range(reached + 1):
        value = trial.user_attrs.get(f"stage_{step}_value")
        rate = trial.user_attrs.get(f"stage_{step}_win_rate")
        details.append(f"s{step}={value:+,}/{rate}%")
    print(f"  {trial.number}: reached stage {reached}{marker}; "
          f"{', '.join(details)}; params={trial.params}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--games", type=int, default=STAGES[0],
                    help="single-stage budget; the default uses STAGES")
    ap.add_argument("--stages", help="comma-separated games per stage")
    ap.add_argument("--opp", default=OPP)
    ap.add_argument("--study", default="kaggri")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--seed0", type=int, default=sweep.SEED0)
    args = ap.parse_args()
    if args.jobs < 1 or args.games < 1 or args.trials < 1:
        ap.error("--trials, --games, and --jobs must be at least 1")
    try:
        args.stages = parse_stages(args.stages, args.games)
    except ValueError as exc:
        ap.error(str(exc))
    SCRATCH.mkdir(exist_ok=True)
    storage = f"sqlite:///{DB.as_posix()}"
    study = optuna.create_study(storage=storage, study_name=args.study,
                                load_if_exists=True, direction="maximize",
                                pruner=optuna.pruners.SuccessiveHalvingPruner(
                                    min_resource=1, reduction_factor=2))
    study.optimize(lambda trial: objective(trial, args), n_trials=args.trials)

    complete = [t for t in study.trials
                if t.state == optuna.trial.TrialState.COMPLETE]
    print(f"\nStudy {args.study}: {len(study.trials)} trials, {len(complete)} complete")
    attempted = [t for t in study.trials if "stage_reached" in t.user_attrs]
    if complete:
        best = study.best_trial
        print(f"Best trial {best.number}: value={best.value}, "
              f"win_rate={best.user_attrs.get('win_rate')}%")
        print(f"  params={best.params}")
    else:
        print("No completed trials.")
    print("Top 5 trials:")
    for trial in sorted(attempted, key=trial_value, reverse=True)[:5]:
        print_trial(trial, args.stages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
