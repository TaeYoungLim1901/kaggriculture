"""Constant-override sweeps: materialise variants of main.py and eval each.

Current panel: the capital question (docs/META.md §6 item 0) -- does an animal
capital reserve unblock expansion when combined with a bigger CROP_PLAN?
Opponent is `bench/v3.py`, a byte copy of the shipped build, so a W-L record
here reads directly as "better or worse than what we ship".
"""
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
SCRATCH = ROOT / ".sweep"
OPP = "bench/v3.py"
GAMES = 8
SEED0 = 90001
STEPS = 720
OVERRIDABLE = {
    "LAND_TARGET", "CROP_PLAN", "ANIMAL_PLAN", "HIRES", "SEED_BATCH", "LAND_RESERVE",
    "ANIMAL_RESERVE", "PLANT_CAP", "DIST_WEIGHT", "STICKY",
}
SUMMARY = re.compile(
    r"(?P<w>\d+)W-(?P<l>\d+)L-(?P<t>\d+)T over (?P<n>\d+) games "
    r"\((?P<rate>\d+)% win rate\), mean margin (?P<mean>[+-][\d,]+), "
    r"worst (?P<worst>[+-][\d,]+)"
)
SEED_LINE = re.compile(r"^  seed \d+ seat [01]:", re.MULTILINE)

BIG_CROPS = [("MELON", 4), ("WHEAT", 6), ("STRAWBERRY", 20)]
EXPAND = {"LAND_TARGET": 2, "CROP_PLAN": BIG_CROPS}
META_ANIMALS = ["SHEEP"] * 4 + ["COW"] * 8
META_CROPS = [("MELON", 12), ("WHEAT", 13), ("STRAWBERRY", 35)]
META_SCALE = {"LAND_TARGET": 3, "ANIMAL_PLAN": META_ANIMALS,
              "CROP_PLAN": META_CROPS, "ANIMAL_RESERVE": 3, "PLANT_CAP": True}
CONFIGS = {
    # expansion alone, re-measured against the shipped build
    "X0": dict(EXPAND),
    # the never-run combination: reserve capital for the herd while expanding
    "X1": dict(EXPAND, ANIMAL_RESERVE=1),
    "X1c": dict(EXPAND, ANIMAL_RESERVE=1, PLANT_CAP=True),
    "X2c": dict(EXPAND, ANIMAL_RESERVE=2, PLANT_CAP=True),
    "X3c": dict(EXPAND, ANIMAL_RESERVE=3, PLANT_CAP=True),
    "X6c": dict(EXPAND, ANIMAL_RESERVE=6, PLANT_CAP=True),
    "X14c": dict(EXPAND, ANIMAL_RESERVE=14, PLANT_CAP=True),   # the whole herd
    "X14": dict(EXPAND, ANIMAL_RESERVE=14),
    # fewer berry tiles, now that the reserve keeps the herd on schedule
    "S12c": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
             "CROP_PLAN": [("MELON", 6), ("WHEAT", 5), ("STRAWBERRY", 12)]},
    "S6c": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
            "CROP_PLAN": [("MELON", 6), ("WHEAT", 5), ("STRAWBERRY", 6)]},
    # more melon on the same 2 quadrants, no berries at all
    "M12c": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
             "CROP_PLAN": [("MELON", 12), ("WHEAT", 5)]},
    # two quadrants doubles travel; pay for more hands to cover it
    "M12c-H10": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
                 "CROP_PLAN": [("MELON", 12), ("WHEAT", 5)], "HIRES": 10},
    "M12c-H12": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
                 "CROP_PLAN": [("MELON", 12), ("WHEAT", 5)], "HIRES": 12},
    "S6c-H12": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
                "CROP_PLAN": [("MELON", 6), ("WHEAT", 5), ("STRAWBERRY", 6)], "HIRES": 12},
    # does the reserve+cap pair pay at the current 25 tiles?
    "R2c": {"ANIMAL_RESERVE": 2, "PLANT_CAP": True},
    "W5": {"DIST_WEIGHT": 5},
    "W10": {"DIST_WEIGHT": 10},
    "W20": {"DIST_WEIGHT": 20},
    "W40": {"DIST_WEIGHT": 40},
    "XW5": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
            "CROP_PLAN": [("MELON", 12), ("WHEAT", 5)], "DIST_WEIGHT": 5},
    "XW10": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
             "CROP_PLAN": [("MELON", 12), ("WHEAT", 5)], "DIST_WEIGHT": 10},
    "XW20": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "PLANT_CAP": True,
             "CROP_PLAN": [("MELON", 12), ("WHEAT", 5)], "DIST_WEIGHT": 20},
    "T14": dict(META_SCALE, HIRES=14),
    "T10": dict(META_SCALE, HIRES=10),
    "S-on": {"STICKY": True},
    "T10-on": dict(META_SCALE, HIRES=10, STICKY=True),
    "T8": dict(META_SCALE, HIRES=8),
    "T14b": dict(META_SCALE, HIRES=14, LAND_TARGET=2,
                 CROP_PLAN=[("MELON", 6), ("WHEAT", 8), ("STRAWBERRY", 20)]),
    "T14c": dict(META_SCALE, HIRES=14,
                  CROP_PLAN=[("MELON", 12), ("WHEAT", 13), ("STRAWBERRY", 20)]),
}


@dataclass
class Result:
    name: str
    path: str
    wins: int
    losses: int
    ties: int
    games: int
    rate: int
    mean: int
    worst: int

    def row(self):
        return (f"{self.name:<18} {self.wins}W-{self.losses}L-{self.ties}T "
                f"{self.rate:>3}% {self.mean:+,} {self.worst:+,}")

    def json(self):
        return self.__dict__


def materialize(name, overrides):
    source = MAIN.read_text(encoding="utf-8")
    for key, value in overrides.items():
        if key not in OVERRIDABLE:
            raise ValueError(f"{name}: unknown override {key}")
        pattern = rf"(?m)^{re.escape(key)}\s*=.*$"
        source, matched = re.subn(pattern, f"{key} = {value!r}", source, count=1)
        assert matched == 1, f"{name}: substitution did not match {key!r}"
    SCRATCH.mkdir(exist_ok=True)
    path = SCRATCH / f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', name)}.py"
    path.write_text(source, encoding="utf-8")
    return path


def run_eval(name, overrides, games=GAMES, opp=OPP):
    path = materialize(name, overrides)
    eval_runner = (
        "import runpy; runpy.run_path('tools/thrash.py')['environment_make'](); "
        "runpy.run_path('tools/eval.py', run_name='__main__')"
    )
    command = [
        sys.executable, "-c", eval_runner,
        "--me", str(path), "--opp", opp,
        "--games", str(games), "--seed0", str(SEED0), "--steps", str(STEPS),
        "--jobs", "1",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    output = completed.stdout + completed.stderr
    (SCRATCH / f"{path.stem}.eval.txt").write_text(output, encoding="utf-8")
    if completed.returncode not in (0, 1):
        raise RuntimeError(f"{name}: eval.py exit {completed.returncode}\n{output}")
    match = SUMMARY.search(completed.stdout)
    if not match:
        raise RuntimeError(f"{name}: eval.py produced no summary\n{output}")
    expected = games * 2
    if len(SEED_LINE.findall(completed.stdout)) != expected:
        raise RuntimeError(f"{name}: expected {expected} completed game rows\n{output}")
    values = {k: int(v.replace(",", "")) for k, v in match.groupdict().items() if k != "rate"}
    if values["w"] + values["l"] + values["t"] != values["n"] or values["n"] != expected:
        raise RuntimeError(f"{name}: inconsistent W-L-T summary: {match.group(0)}")
    return Result(name, str(path), values["w"], values["l"], values["t"], values["n"],
                  int(match.group("rate")), values["mean"], values["worst"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", nargs="?", default="all", help="config name, or all")
    ap.add_argument("--opp", default=OPP)
    ap.add_argument("--games", type=int, default=GAMES)
    args = ap.parse_args()
    names = list(CONFIGS) if args.config == "all" else [args.config]
    if any(name not in CONFIGS for name in names):
        raise SystemExit(f"config must be one of {', '.join(CONFIGS)}, or all")

    print(f"vs {args.opp}, {args.games} seeds x 2 seats, seed0 {SEED0}")
    print("config             W-L-T       win%  mean margin  worst margin")
    results = []
    for name in names:
        result = run_eval(name, CONFIGS[name], args.games, args.opp)
        results.append(result)
        print(result.row(), flush=True)
    (SCRATCH / "sweep-results.json").write_text(
        json.dumps([r.json() for r in results], indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
