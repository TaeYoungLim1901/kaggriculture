"""Run one candidate against the standard opponent panel."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import sweep

DEFAULT = ["bench/v15.py", "bench/v14.py", "bench/v3.py",
           "bench/ref_broker_bea.py", "bench/ref_closer_cleo.py"]
SETS = {"default": DEFAULT, "mirror": DEFAULT[:3], "refs": DEFAULT[3:]}
BUILTINS = {"pass", "random", "starter"}


def evaluate(me, opp, args):
    runner = (
        "import runpy; runpy.run_path('tools/thrash.py')['environment_make'](); "
        "runpy.run_path('tools/eval.py', run_name='__main__')"
    )
    command = [
        sys.executable, "-c", runner, "--me", str(me), "--opp", opp,
        "--games", str(args.games), "--seed0", str(args.seed0),
        "--steps", str(sweep.STEPS), "--jobs", str(args.jobs),
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8")
    output = completed.stdout + completed.stderr
    if completed.returncode not in (0, 1):
        raise RuntimeError(f"eval.py exit {completed.returncode}\n{output}")
    match = sweep.SUMMARY.search(completed.stdout)
    if not match:
        raise RuntimeError(f"eval.py produced no summary\n{output}")
    expected = args.games * 2
    if len(sweep.SEED_LINE.findall(completed.stdout)) != expected:
        raise RuntimeError(f"expected {expected} completed game rows\n{output}")
    values = {key: int(value.replace(",", "")) for key, value in match.groupdict().items()
              if key != "rate"}
    if values["w"] + values["l"] + values["t"] != values["n"] or values["n"] != expected:
        raise RuntimeError(f"inconsistent W-L-T summary: {match.group(0)}")
    values["rate"] = int(match.group("rate"))
    return values


def present(rows, with_delta):
    rendered = []
    for name, result, baseline in rows:
        fields = [f"{result['w']}W-{result['l']}L-{result['t']}T",
                  f"{result['rate']}%", f"{result['mean']:+,}", f"{result['worst']:+,}"]
        if with_delta:
            fields.append(f"{result['mean'] - baseline['mean']:+,}")
        rendered.append((name, fields))
    widths = [len(header) for header in ("W-L-T", "win%", "mean margin", "worst margin")]
    if with_delta:
        widths.append(len("delta"))
    for _, fields in rendered:
        widths = [max(width, len(field)) for width, field in zip(widths, fields)]
    name_width = max([len("opponent")] + [len(name) for name, _ in rendered])
    headers = ["W-L-T", "win%", "mean margin", "worst margin"] + (["delta"] if with_delta else [])
    print(f"{'opponent':<{name_width}}  " + "  ".join(
        f"{header:>{width}}" for header, width in zip(headers, widths)))
    for name, fields in rendered:
        print(f"{name:<{name_width}}  " + "  ".join(
            f"{field:>{width}}" for field, width in zip(fields, widths)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("me", nargs="?", default="main.py")
    parser.add_argument("--opp-set", choices=SETS, default="default")
    parser.add_argument("--opp", action="append")
    parser.add_argument("--games", type=int, default=8)
    parser.add_argument("--seed0", type=int, default=sweep.SEED0)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--config", choices=tuple(sweep.CONFIGS))
    parser.add_argument("--baseline")
    args = parser.parse_args()
    if args.games < 1 or args.jobs < 1:
        parser.error("--games and --jobs must be at least 1")
    me = (sweep.materialize(args.config, sweep.CONFIGS[args.config])
          if args.config else Path(args.me))
    if not (me if me.is_absolute() else ROOT / me).is_file():
        parser.error(f"missing candidate file: {me}")
    opponents = args.opp if args.opp is not None else SETS[args.opp_set]
    opponents = [opp for opp in opponents
                 if opp in BUILTINS or (ROOT / opp).is_file()
                 or (Path(opp).is_absolute() and Path(opp).is_file())]
    skipped = (args.opp if args.opp is not None else SETS[args.opp_set])
    for opp in skipped:
        if opp not in opponents:
            print(f"warning: skipping missing opponent {opp}", file=sys.stderr)
    if args.baseline and not (ROOT / args.baseline).is_file():
        parser.error(f"missing baseline file: {args.baseline}")
    baseline = args.baseline
    baseline_results = ([evaluate(baseline, opp, args) for opp in opponents]
                        if baseline else [None] * len(opponents))
    rows = [(opp, evaluate(me, opp, args), base)
            for opp, base in zip(opponents, baseline_results)]
    present(rows, baseline is not None)
    mirrors = [(opp, result) for opp, result, _ in rows if opp in SETS["mirror"]]
    selected_mirrors = [opp for opp in (args.opp or SETS[args.opp_set])
                        if opp in SETS["mirror"]]
    if not selected_mirrors:
        verdict = "N/A (no mirror opponents selected)"
    elif len(mirrors) < len(selected_mirrors):
        verdict = "NO (not every mirror opponent was evaluated)"
    else:
        verdict = "YES" if all(result["w"] > result["l"] for _, result in mirrors) else "NO"
    print(f"Verdict: candidate beat every mirror opponent: {verdict}")


if __name__ == "__main__":
    raise SystemExit(main())
