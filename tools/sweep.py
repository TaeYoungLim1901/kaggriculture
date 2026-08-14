"""Constant-override sweeps: materialise variants of main.py and eval each.

Pass `--opp main.py` to measure a variant against the build in the tree: the
ladder behaves like a mirror, so a W-L record there reads directly as "better or
worse than what we ship". Use bench/ref_broker_bea.py and bench/ref_closer_cleo.py
as the independent check -- we lose to both 0W-32L, so only their margin informs.
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
    "ANIMAL_RESERVE", "ANIMAL_PIPELINE", "DRAIN_SCALE", "PLANT_CAP", "DIST_WEIGHT",
    "STICKY", "BUNDLE", "SELL_HOURS", "LAST_DAY", "HIRE_SLOTS", "HIRE_HOUR0", "SELL_BY_VALUE", "FERT_RESERVE", "PRIO_COST", "CASH_FLOOR", "FEED_DAYS", "SHED_CAP", "BUY_SLOTS",
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
# Derived from decoding the mined top-ladder trace (bench/trace_mined_92791997.py,
# `python tools/tracedump.py`): 13 hands/day held from d19, 3 quadrants bought d6/d9,
# a SMALL herd of 6 COW + 3 SHEEP finished by d7, and wheat replanted continuously
# (126 PLANT requests) because wheat is the only crop besides EGG whose price does not
# floor. Premium goods are metered, not scaled. This is the plan, re-derived for our
# own constants -- not their action stream.
DERIVED = {"LAND_TARGET": 3, "HIRES": 13,
           "ANIMAL_PLAN": ["COW"] * 6 + ["SHEEP"] * 3,
           "CROP_PLAN": [("STRAWBERRY", 34), ("MELON", 18), ("WHEAT", 20)]}

CONFIGS = {
    # the shipped build, unmodified: the baseline every other row is measured
    # against. Re-run it whenever --games or --opp changes; a reference taken at
    # a different panel size is not comparable.
    "BASE": {},
    "BUNDLE": {"BUNDLE": True},
    # Every HIRES > 8 row measured before 2026-08-14 is void: the extra-hire refill
    # loop filled all 10 market slots with HIRE every hour, blocking SELL, so cash
    # never arrived, `_do_hire` kept failing without advancing `hires_today`, and it
    # re-requested forever. Re-measure anything that raises HIRES.
    "H13": {"HIRES": 13},
    # The transit re-buy (fixed 2026-08-14) meant ANIMAL_PLAN was never what stood on
    # the board: v4 declared 11 and ran 6 SHEEP + 7 COW. Re-tune from the real herd.
    # Herd size at a fixed 25-tile budget, now that the ramp is pipelined and the
    # herd honestly matches ANIMAL_PLAN. Every tile freed from a pasture is a berry.
    "A10c": {"ANIMAL_PLAN": ["SHEEP"] * 4 + ["COW"] * 6,
             "CROP_PLAN": [("STRAWBERRY", 9), ("WHEAT", 6)]},
    "A9c": {"ANIMAL_PLAN": ["SHEEP"] * 3 + ["COW"] * 6,
            "CROP_PLAN": [("STRAWBERRY", 10), ("WHEAT", 6)]},
    "A12c": {"ANIMAL_PLAN": ["SHEEP"] * 4 + ["COW"] * 8,
             "CROP_PLAN": [("STRAWBERRY", 7), ("WHEAT", 6)]},
    # Sell rate on the shared market. Judge these head-to-head against main.py, not
    # against the reference agents: the point is what happens when both sides sell the
    # same goods into one order book.
    "D060": {"DRAIN_SCALE": 0.60},
    "D075": {"DRAIN_SCALE": 0.75},
    "D090": {"DRAIN_SCALE": 0.90},
    "D125": {"DRAIN_SCALE": 1.25},
    "D150": {"DRAIN_SCALE": 1.50},
    "D200": {"DRAIN_SCALE": 2.0},
    "D300": {"DRAIN_SCALE": 3.0},
    "D500": {"DRAIN_SCALE": 5.0},
    "D999": {"DRAIN_SCALE": 999.0},   # sell the whole shed every hour
    # No-throttle wins by getting to the top of the price curve first, so try to get
    # there earlier still. Hour 0 is reserved for HIRE, which needs 8 of the 10 slots.
    "SH0": {"SELL_HOURS": tuple(range(0, 24))},
    # How many of the 10 hour-0 slots go to HIRE vs to selling into the fullest shed
    # of the day. The rest of the crew is topped up from hour 1 (HIRE_SLOTS per turn).
    # Optuna study `v9mirror` (clean: frozen main.py, 100 trials, 16 episodes each).
    # All five top trials converge on the same shape -- two quadrants, 13 animals
    # cow-heavy, a wheat-heavy crop plan, 10-11 hands.
    "T82": {"HIRES": 10, "HIRE_HOUR0": 3, "LAND_TARGET": 2, "ANIMAL_RESERVE": 2,
            "ANIMAL_PIPELINE": 5, "SEED_BATCH": 5,
            "ANIMAL_PLAN": ["SHEEP"] * 5 + ["COW"] * 8,
            "CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 12)]},
    "T92": {"HIRES": 11, "HIRE_HOUR0": 5, "LAND_TARGET": 2, "ANIMAL_RESERVE": 2,
            "ANIMAL_PIPELINE": 5, "SEED_BATCH": 5,
            "ANIMAL_PLAN": ["SHEEP"] * 5 + ["COW"] * 8,
            "CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 12)]},
    "T82-F4": {"HIRES": 10, "LAND_TARGET": 2, "ANIMAL_RESERVE": 2,
               "ANIMAL_PIPELINE": 5, "SEED_BATCH": 5,
               "ANIMAL_PLAN": ["SHEEP"] * 5 + ["COW"] * 8,
               "CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 12)]},
    # Single-knob deltas from the shipped two-quadrant plan (main.py = T92).
    "k-H10": {"HIRES": 10},
    "k-H12": {"HIRES": 12},
    "k-F4": {"HIRE_HOUR0": 4},
    "k-F6": {"HIRE_HOUR0": 6},
    "k-cow7": {"ANIMAL_PLAN": ["SHEEP"] * 5 + ["COW"] * 7},
    "k-cow9": {"ANIMAL_PLAN": ["SHEEP"] * 5 + ["COW"] * 9},
    "k-sheep7": {"ANIMAL_PLAN": ["SHEEP"] * 7 + ["COW"] * 8},
    "k-w9": {"CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 9)]},
    "k-w16": {"CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 16)]},
    "k-berry8": {"CROP_PLAN": [("STRAWBERRY", 8), ("WHEAT", 12)]},
    "k-P4": {"ANIMAL_PIPELINE": 4},
    "k-L3": {"LAND_TARGET": 3},
    # Priority bands. With DIST_WEIGHT 20 a 200-point band gap is worth 10 tiles of
    # walking, so the shape of this dict is now a routing knob, not just an ordering.
    # Never swept before 2026-08-14: a constant at its first-commit default is not
    # a tuned constant.
    "STICKY": {"STICKY": True},
    "AR1": {"ANIMAL_RESERVE": 1},
    "AR3": {"ANIMAL_RESERVE": 3},
    "SB3": {"SEED_BATCH": 3},
    "SB8": {"SEED_BATCH": 8},
    "LD27": {"LAST_DAY": 27},
    "LD29x": {"LAST_DAY": 99},
    "CF50": {"CASH_FLOOR": 50},
    "CF1000": {"CASH_FLOOR": 1000},
    "FD1": {"FEED_DAYS": 1},
    "FD2": {"FEED_DAYS": 2},
    "FD5": {"FEED_DAYS": 5},
    "LR0": {"LAND_RESERVE": 0},
    "LR3000": {"LAND_RESERVE": 3000},
    "PC-flat": {"PRIO_COST": {0: -900, 1: -800, 2: -700, 3: -600, 4: -500, 5: -400, 6: -650}},
    "PC-steep": {"PRIO_COST": {0: -1800, 1: -1400, 2: -1000, 3: -600, 4: -440, 5: -240, 6: -520}},
    "PC-feed": {"PRIO_COST": {0: -1400, 1: -700, 2: -500, 3: -300, 4: -220, 5: -120, 6: -260}},
    "PC-harv": {"PRIO_COST": {0: -900, 1: -700, 2: -800, 3: -300, 4: -220, 5: -120, 6: -260}},
    "PC-plant": {"PRIO_COST": {0: -900, 1: -700, 2: -500, 3: -300, 4: -220, 5: -120, 6: -600}},
    "W8": {"DIST_WEIGHT": 8},
    "W12": {"DIST_WEIGHT": 12},
    "W15": {"DIST_WEIGHT": 15},
    "W20": {"DIST_WEIGHT": 20},
    "W30": {"DIST_WEIGHT": 30},
    "W50": {"DIST_WEIGHT": 50},
    "SV": {"SELL_BY_VALUE": True},
    "B0": {"BUY_SLOTS": 0},
    "B2": {"BUY_SLOTS": 2},
    "FR0": {"FERT_RESERVE": 0},
    "FR2": {"FERT_RESERVE": 2},
    "FR4": {"FERT_RESERVE": 4},
    "S3": {"HIRE_SLOTS": 3},
    "S4": {"HIRE_SLOTS": 4},
    "S1": {"HIRE_SLOTS": 1},
    "F2": {"HIRE_HOUR0": 2},
    "F3": {"HIRE_HOUR0": 3},
    "F4": {"HIRE_HOUR0": 4},
    # Optuna study `v6mirror` (tools/tune.py, 60 trials, 8 episodes each -- noisy).
    # Every one of its top five picks LAND_TARGET 2: under the sell throttle part of
    # expansion's cost was flooding a market we were also metering.
    "T33": {"HIRES": 9, "LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "ANIMAL_PIPELINE": 4,
            "SEED_BATCH": 1, "ANIMAL_PLAN": ["SHEEP"] * 7 + ["COW"] * 5,
            "CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 14)]},
    "T46": {"HIRES": 10, "LAND_TARGET": 2, "ANIMAL_RESERVE": 2, "ANIMAL_PIPELINE": 6,
            "SEED_BATCH": 2, "ANIMAL_PLAN": ["SHEEP"] * 8 + ["COW"] * 5,
            "CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 5)]},
    "T33-F4": {"HIRES": 9, "LAND_TARGET": 2, "ANIMAL_RESERVE": 3, "ANIMAL_PIPELINE": 4,
               "SEED_BATCH": 1, "HIRE_HOUR0": 4,
               "ANIMAL_PLAN": ["SHEEP"] * 7 + ["COW"] * 5,
               "CROP_PLAN": [("STRAWBERRY", 4), ("WHEAT", 14)]},
    "F5": {"HIRE_HOUR0": 5},
    "F6": {"HIRE_HOUR0": 6},
    "F7": {"HIRE_HOUR0": 7},
    "SH0-h4": {"SELL_HOURS": tuple(range(0, 24)), "HIRES": 4},
    "SH0-h6": {"SELL_HOURS": tuple(range(0, 24)), "HIRES": 6},
    "P1": {"ANIMAL_PIPELINE": 1},
    "P2": {"ANIMAL_PIPELINE": 2},
    "P4": {"ANIMAL_PIPELINE": 4},
    "P6": {"ANIMAL_PIPELINE": 6},
    "P4-A13": {"ANIMAL_PIPELINE": 4,
               "ANIMAL_PLAN": ["SHEEP"] * 6 + ["COW"] * 7},
    "A13": {"ANIMAL_PLAN": ["SHEEP"] * 6 + ["COW"] * 7},
    "A12": {"ANIMAL_PLAN": ["SHEEP"] * 5 + ["COW"] * 7},
    "A14": {"ANIMAL_PLAN": ["SHEEP"] * 6 + ["COW"] * 8},
    "A13c": {"ANIMAL_PLAN": ["SHEEP"] * 6 + ["COW"] * 7,
             "CROP_PLAN": [("STRAWBERRY", 7), ("WHEAT", 5)]},
    "E2-H12": {"LAND_TARGET": 2, "HIRES": 12, "ANIMAL_RESERVE": 1,
               "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    "E2-H8": {"LAND_TARGET": 2, "ANIMAL_RESERVE": 1,
              "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    # Crew size at two quadrants, now that the hire path works and the herd is honest.
    "E2-H16": {"LAND_TARGET": 2, "HIRES": 16, "ANIMAL_RESERVE": 1,
               "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    "E2-H20": {"LAND_TARGET": 2, "HIRES": 20, "ANIMAL_RESERVE": 1,
               "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    "E2-H24": {"LAND_TARGET": 2, "HIRES": 24, "ANIMAL_RESERVE": 1,
               "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    # How early can the quadrant be afforded?
    "E2-H12-L0": {"LAND_TARGET": 2, "HIRES": 12, "ANIMAL_RESERVE": 1, "LAND_RESERVE": 0,
                  "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    "E2-H12-L500": {"LAND_TARGET": 2, "HIRES": 12, "ANIMAL_RESERVE": 1, "LAND_RESERVE": 500,
                    "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    "E2-H12-R0": {"LAND_TARGET": 2, "HIRES": 12, "ANIMAL_RESERVE": 0, "LAND_RESERVE": 0,
                  "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 26)]},
    # ...and the same crew question on the quadrant we already own.
    "H12": {"HIRES": 12},
    "H16": {"HIRES": 16},
    # the whole derived plan, then each of its three levers alone
    "D1": dict(DERIVED),
    "BD1": dict(DERIVED, BUNDLE=True),
    "D-hands": {"HIRES": 13},
    "D-herd": {"ANIMAL_PLAN": ["COW"] * 6 + ["SHEEP"] * 3},
    "D-land": dict(DERIVED, HIRES=8),
    "D-wheat": {"CROP_PLAN": [("MELON", 6), ("WHEAT", 15)]},
    # the small herd was the one derived lever that gained (-79,272 vs -83,638):
    # MILK floors at 76 units and WOOL at 59, so 14 animals overproduce into a
    # floored market and eat the wheat. Combine it with the strawberry gain and
    # spend the 5 freed tiles.
    "H9-S7": {"ANIMAL_PLAN": ["COW"] * 6 + ["SHEEP"] * 3,
              "CROP_PLAN": [("STRAWBERRY", 7), ("WHEAT", 4)]},
    "H9-S10": {"ANIMAL_PLAN": ["COW"] * 6 + ["SHEEP"] * 3,
               "CROP_PLAN": [("STRAWBERRY", 10), ("WHEAT", 6)]},
    "H6-S10": {"ANIMAL_PLAN": ["COW"] * 4 + ["SHEEP"] * 2,
               "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 7)]},
    # H9-S10 (-70,698) is the best measured build; margin is monotone in berries
    # so far, so push the mix further and bracket the herd size around 9.
    "H9-S14": {"ANIMAL_PLAN": ["COW"] * 6 + ["SHEEP"] * 3,
               "CROP_PLAN": [("STRAWBERRY", 14), ("WHEAT", 2)]},
    "H9-S12": {"ANIMAL_PLAN": ["COW"] * 6 + ["SHEEP"] * 3,
               "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 4)]},
    "H11-S8": {"ANIMAL_PLAN": ["COW"] * 7 + ["SHEEP"] * 4,
               "CROP_PLAN": [("STRAWBERRY", 8), ("WHEAT", 6)]},
    # H11-S8 shipped as v4. It goes 0W-48L against its own predecessor while
    # beating four independent opponents: vacating melon/milk/wool hands those
    # niches to a same-lineage rival. Does keeping a token melon presence deny
    # that, and is 8 berries against a 62-unit price floor already too many?
    "H11-S8M2": {"ANIMAL_PLAN": ["COW"] * 7 + ["SHEEP"] * 4,
                 "CROP_PLAN": [("STRAWBERRY", 8), ("WHEAT", 4), ("MELON", 2)]},
    "H11-S6": {"ANIMAL_PLAN": ["COW"] * 7 + ["SHEEP"] * 4,
               "CROP_PLAN": [("STRAWBERRY", 6), ("WHEAT", 8)]},
    "H13-S6": {"ANIMAL_PLAN": ["COW"] * 8 + ["SHEEP"] * 5,
               "CROP_PLAN": [("STRAWBERRY", 6), ("WHEAT", 6)]},
    # tools/sellprofile.py on the v4 build vs ref_broker_bea, seed 1000:
    #   MILK   147 units @ $35.8  = $5,257   (base $160 -- floored)
    #   WOOL   146 units @ $159.6 = $23,300  (base $200 -- holds)
    #   STRAWBERRY 78 @ $196.7; the opponent sold 215 at $198.9, so berries do NOT
    #   floor in practice and we are simply under-producing them.
    # Cows are therefore near-worthless per structure tile while sheep are not.
    "S6C2-B10": {"ANIMAL_PLAN": ["SHEEP"] * 6 + ["COW"] * 2,
                 "CROP_PLAN": [("STRAWBERRY", 10), ("WHEAT", 7)]},
    "S8C0-B10": {"ANIMAL_PLAN": ["SHEEP"] * 8,
                 "CROP_PLAN": [("STRAWBERRY", 10), ("WHEAT", 7)]},
    "S6C0-B12": {"ANIMAL_PLAN": ["SHEEP"] * 6,
                 "CROP_PLAN": [("STRAWBERRY", 12), ("WHEAT", 7)]},
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
