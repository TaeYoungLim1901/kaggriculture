"""Simulated annealing over recorded 720-action traces."""
import argparse
import concurrent.futures
import copy
import math
import os
import random
import re
import time
from pathlib import Path

import bake
import plan
import record

ROOT = Path(__file__).resolve().parent.parent
EPISODE_STEPS = 720
DEFAULT_OPP = "bench/v16_rc5_high_score_8c_4s_premium_market_.py"
DEFAULT_SOURCES = ",".join((
    "main.py", ".sweep/B7.py", ".sweep/M12c.py", ".sweep/T10.py",
    ".sweep/W20.py", ".sweep/X3c.py",
))
DEFAULT_PANEL = (90001, 1000, 55555, 8919)
DEFAULT_HOLDOUT = (2222, 31337)


def _path(value):
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.is_file():
        raise SystemExit(f"file not found: {path}")
    return path


def _ints(value, option):
    try:
        values = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise SystemExit(f"{option} must be comma-separated integers") from exc
    if not values:
        raise SystemExit(f"{option} must contain at least one seed")
    return values


def _blob_name(source):
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(source).stem)
    return ROOT / "build" / f"anneal_donor_{stem}.b85"


def _validate_trace(actions, label):
    if not isinstance(actions, list) or len(actions) != EPISODE_STEPS:
        raise SystemExit(f"{label} must decode to {EPISODE_STEPS} actions")
    if any(not isinstance(action, dict) for action in actions):
        raise SystemExit(f"{label} contains a non-action entry")
    return actions


def _record_sources(sources, opponent, seed):
    blobs = []
    for source in sources:
        source_path = _path(source)
        out = _blob_name(source_path)
        record.record_episode(source_path, opponent, seed, out, EPISODE_STEPS)
        blobs.append(out)
    return blobs


def _load_donors(sources, opponent, seed, blobs):
    paths = _record_sources(sources, opponent, seed)
    paths.extend(_path(blob) for blob in blobs)
    donors = []
    seen = set()
    for path in paths:
        actions = _validate_trace(bake.load_blob(path), str(path))
        key = repr(actions)
        if key not in seen:
            seen.add(key)
            donors.append((path, actions))
    if not donors:
        raise SystemExit("no donor traces")
    return donors


def _replay(actions, seed, opponent_path, trace_seat):
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": EPISODE_STEPS, "seed": seed})
    env.reset(2)
    opponent = plan._load(str(opponent_path), f"anneal_opponent_{os.getpid()}_{seed}_{trace_seat}")
    for action in actions:
        if env.done:
            break
        observations = (plan._obs(env, 0), plan._obs(env, 1))
        other = plan._call(opponent, observations[1 - trace_seat])
        pair = [other, copy.deepcopy(action)] if trace_seat else [copy.deepcopy(action), other]
        env.step(pair)
    if not env.done:
        raise RuntimeError(f"replay stopped early at {len(env.steps) - 1} steps")
    raw_margin = plan._margin(env, False)
    return raw_margin if trace_seat == 0 else -raw_margin


def _score_task(task):
    actions, seeds, opponent_path, both_seats = task
    seat0 = tuple(_replay(actions, seed, opponent_path, 0) for seed in seeds)
    seat1 = tuple(_replay(actions, seed, opponent_path, 1) for seed in seeds) if both_seats else None
    objective_values = seat0 if seat1 is None else tuple((a + b) / 2 for a, b in zip(seat0, seat1))
    return {
        "objective": sum(objective_values) / len(objective_values),
        "seat0": seat0,
        "seat1": seat1,
        "values": objective_values,
    }


def _score(actions, seeds, opponent, both_seats, pool):
    return next(iter(pool.map(_score_task, [(actions, seeds, opponent, both_seats)])))


def _segment_length(rng, limit):
    return rng.randint(1, min(limit, 48))


def _mutate(current, donors, rng):
    candidate = copy.deepcopy(current)
    n = len(candidate)
    roll = rng.random()
    if roll < 0.5:
        position = rng.randrange(n)
        donor = donors[rng.randrange(len(donors))]
        candidate[position] = copy.deepcopy(donor[position])
    elif roll < 0.75:
        donor = donors[rng.randrange(len(donors))]
        length = _segment_length(rng, n)
        left = rng.randrange(n - length + 1)
        right = rng.randrange(n - length + 1)
        candidate[left:left + length] = copy.deepcopy(donor[right:right + length])
    else:
        left = rng.randrange(n)
        length = _segment_length(rng, n - left)
        block = candidate[left:left + length]
        rest = candidate[:left] + candidate[left + length:]
        if rng.random() < 0.5:
            right = rng.randrange(len(rest) + 1)
            candidate = rest[:right] + block + rest[right:]
        else:
            right = rng.randrange(len(rest) - length + 1)
            other = rest[right:right + length]
            candidate = rest[:right] + block + rest[right:]
            candidate[left:left + length] = other
    return candidate


def _temperature(t0, t1, iteration, total):
    return t0 * (t1 / t0) ** (iteration / max(1, total - 1))


def _accept(candidate, current, temperature, rng):
    if candidate >= current:
        return True
    return rng.random() < math.exp((candidate - current) / temperature)


def _format_values(values):
    return ", ".join(f"{seed}={value:+.0f}" for seed, value in values)


def _report(label, panel, holdout, seed_score, best_score, holdout_seed_score,
            holdout_best_score, both_seats):
    print("\ntrace                         panel mean   per-seed margin")
    print(f"seed ({label})                 {seed_score['objective']:+10.1f}   "
          f"{_format_values(zip(panel, seed_score['values']))}")
    print(f"best ({label})                 {best_score['objective']:+10.1f}   "
          f"{_format_values(zip(panel, best_score['values']))}")
    print("hold-out seed                 seed trace       best trace")
    for seed, before, after in zip(holdout,
                                   holdout_seed_score["values"], holdout_best_score["values"]):
        print(f"{seed:>12d}                  {before:+10.0f}       {after:+10.0f}")
    if both_seats:
        print("seat-0-only ranking: "
              f"{'best' if best_score['seat0'] and sum(best_score['seat0']) > sum(seed_score['seat0']) else 'seed'}; "
              "both-seat ranking: "
              f"{'best' if best_score['objective'] > seed_score['objective'] else 'seed'}; "
              f"changed={'yes' if (best_score['objective'] > seed_score['objective']) !=
              (sum(best_score['seat0']) > sum(seed_score['seat0'])) else 'no'}")


def anneal(args):
    panel = _ints(args.seeds, "--seeds")
    holdout = _ints(args.holdout, "--holdout")
    if len(panel) < 2:
        raise SystemExit("--seeds must contain at least two seeds")
    if set(panel) & set(holdout):
        raise SystemExit("--seeds and --holdout must be disjoint")
    if args.jobs < 1 or args.budget < 1:
        raise SystemExit("--jobs and --budget must be at least 1")
    if args.t0 <= 0 or args.t1 <= 0 or args.t1 > args.t0:
        raise SystemExit("require 0 < --t1 <= --t0")

    opponent = _path(args.opp)
    sources = tuple(item.strip() for item in args.sources.split(",") if item.strip())
    donor_blobs = tuple(item.strip() for item in args.donor_blobs.split(",") if item.strip())
    donors = _load_donors(sources, opponent, args.record_seed, donor_blobs)
    print("donors: " + ", ".join(str(path.relative_to(ROOT)) for path, _ in donors))

    wall_started = time.perf_counter()
    evaluations = 0
    report_reserve = 2
    if args.budget <= len(donors) + report_reserve:
        raise SystemExit(f"--budget must exceed {len(donors) + report_reserve} initial/report evaluations")

    pool = concurrent.futures.ProcessPoolExecutor(
        max_workers=args.jobs,
        mp_context=None,
    )
    try:
        scored = []
        for path, actions in donors:
            result = _score(actions, panel, opponent, args.both_seats, pool)
            scored.append((result["objective"], path, actions, result))
            evaluations += 1
        scored.sort(key=lambda item: item[0], reverse=True)
        _, seed_path, seed_trace, seed_score = scored[0]
        print(f"seed trace: {seed_path.relative_to(ROOT)}  panel={seed_score['objective']:+.1f}")

        candidate_budget = args.budget - evaluations - report_reserve
        chains = min(args.jobs, candidate_budget)
        rng_master = random.Random(args.rng_seed)
        rngs = [random.Random(rng_master.randrange(1 << 63)) for _ in range(chains)]
        currents = [copy.deepcopy(seed_trace) for _ in range(chains)]
        current_scores = [seed_score["objective"] for _ in range(chains)]
        best = copy.deepcopy(seed_trace)
        best_score = seed_score
        last_print = time.perf_counter()
        completed = 0
        while completed < candidate_budget:
            batch = min(chains, candidate_budget - completed)
            tasks = []
            candidates = []
            for chain in range(batch):
                candidate = _mutate(currents[chain], [actions for _, actions in donors], rngs[chain])
                tasks.append((candidate, panel, opponent, args.both_seats))
                candidates.append(candidate)
            results = list(pool.map(_score_task, tasks))
            for chain, result in enumerate(results):
                candidate_score = result["objective"]
                temperature = _temperature(args.t0, args.t1, completed + chain,
                                            candidate_budget)
                if _accept(candidate_score, current_scores[chain], temperature, rngs[chain]):
                    currents[chain] = candidates[chain]
                    current_scores[chain] = candidate_score
                if candidate_score > best_score["objective"]:
                    best = copy.deepcopy(candidates[chain])
                    best_score = result
            completed += batch
            evaluations += batch
            now = time.perf_counter()
            if now - last_print >= 1.0 or completed == candidate_budget:
                rate = evaluations / max(now - wall_started, 1e-9) * 60
                print(f"iter {completed:5d}/{candidate_budget}  best={best_score['objective']:+.1f} "
                      f"T={_temperature(args.t0, args.t1, completed - 1, candidate_budget):.1f} "
                      f"eval/min={rate:.2f}", flush=True)
                last_print = now

        holdout_seed_score = _score(seed_trace, holdout, opponent, args.both_seats, pool)
        holdout_best_score = _score(best, holdout, opponent, args.both_seats, pool)
        evaluations += report_reserve
    finally:
        pool.shutdown()

    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(plan._encode(best))
    elapsed = time.perf_counter() - wall_started
    rate = evaluations / max(elapsed, 1e-9) * 60
    print(f"best blob: {output}  entries: {len(best)}")
    print(f"wall: {elapsed:.2f}s  evaluations: {evaluations}  evaluations/min: {rate:.2f}")
    print(f"holdout means: seed={holdout_seed_score['objective']:+.1f} "
          f"best={holdout_best_score['objective']:+.1f}")
    _report("seat-relative" if args.both_seats else "seat 0", panel, holdout,
            seed_score, best_score, holdout_seed_score, holdout_best_score,
            args.both_seats)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default=",".join(map(str, DEFAULT_PANEL)))
    parser.add_argument("--holdout", default=",".join(map(str, DEFAULT_HOLDOUT)))
    parser.add_argument("--both-seats", action="store_true")
    parser.add_argument("--opp", default=DEFAULT_OPP)
    parser.add_argument("--sources", default=DEFAULT_SOURCES,
                        help="comma-separated agent files to record as donors")
    parser.add_argument("--donor-blobs", default="build/portfolio_margin.b85",
                        help="comma-separated existing trace blobs")
    parser.add_argument("--record-seed", type=int, default=90001,
                        help="seed used when recording source donors")
    parser.add_argument("--out", required=True)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--budget", type=int, default=16000,
                        help="total trace evaluations, including donor and holdout reports")
    parser.add_argument("--t0", type=float, default=10000.0)
    parser.add_argument("--t1", type=float, default=100.0)
    parser.add_argument("--rng-seed", type=int, default=20260814)
    args = parser.parse_args()
    anneal(args)


if __name__ == "__main__":
    main()
