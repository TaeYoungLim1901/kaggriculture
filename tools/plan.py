"""Choose each action by full-episode offline rollouts."""
import argparse
import base64
import concurrent.futures
import copy
import importlib.util
import json
import os
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODE_STEPS = 720
DEFAULT_PORTFOLIO = ",".join(("main.py", ".sweep/B7.py", ".sweep/M12c.py",
                               ".sweep/T10.py", ".sweep/W20.py", ".sweep/X3c.py"))
DEFAULT_OPP = "bench/v16_rc5_high_score_8c_4s_premium_market_.py"


def _path(value):
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.is_file():
        raise SystemExit(f"agent not found: {path}")
    return str(path)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def _get(value, key, default=None):
    try:
        return value[key]
    except (KeyError, IndexError, TypeError):
        return getattr(value, key, default)


def _obs(env, seat):
    return env._Environment__get_shared_state(seat).observation


def _pass(obs):
    farms = _get(obs, "farms", []) or []
    seat = int(_get(obs, "player", 0) or 0)
    farm = farms[seat] if seat < len(farms) else {}
    hands = _get(farm, "hands", []) or []
    return {"farmer": ["PASS"], "hands": [["PASS"] for _ in hands], "market": []}


def _call(agent, obs):
    try:
        return copy.deepcopy(agent(obs))
    except Exception:
        return _pass(obs)


def _key(action):
    return json.dumps(action, sort_keys=True, separators=(",", ":"), default=str)


def _money(obs):
    farms = _get(obs, "farms", []) or []
    farm = farms[0] if farms else {}
    return float(_get(farm, "money", 0) or 0)


def _partial_score(obs):
    private = _get(obs, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}
    market = _get(obs, "market", {}) or {}
    prices = _get(market, "prices", {}) or {}
    return _money(obs) + sum(float(n or 0) * float(_get(prices, item, 0) or 0)
                             for item, n in shed.items())


def _rollout(task):
    base, action, opponent_action, continuation, opponent, current, horizon = task
    started = time.perf_counter()
    env = copy.deepcopy(base)
    before = len(env.steps)
    env.step([copy.deepcopy(action), copy.deepcopy(opponent_action)])
    truncated = horizon < EPISODE_STEPS - current
    if truncated:
        env.configuration["episodeSteps"] = current + horizon + 1
    if not env.done:
        env.run([continuation, opponent])
    obs = _obs(env, 0)
    score = _partial_score(obs) if truncated else _money(obs)
    return score, time.perf_counter() - started, len(env.steps) - before


def _encode(actions):
    payload = json.dumps(actions, separators=(",", ":"), ensure_ascii=True).encode()
    return base64.b85encode(zlib.compress(payload))


def _estimate(planned, unique, rollout_steps, rollout_cpu, jobs):
    if not planned or not rollout_steps:
        return None
    average_unique = unique / planned
    full_steps = sum(EPISODE_STEPS - step for step in range(EPISODE_STEPS - 1))
    seconds = (rollout_cpu / rollout_steps) * average_unique * full_steps
    return seconds / max(1, jobs)


def plan(args):
    from kaggle_environments import make

    portfolio_paths = [_path(item.strip()) for item in args.portfolio.split(",") if item.strip()]
    if not portfolio_paths:
        raise SystemExit("--portfolio must contain at least one agent path")
    opponent_path = _path(args.opp)
    continuation_path = _path("main.py")
    portfolio = [_load(path, f"portfolio_{i}") for i, path in enumerate(portfolio_paths)]
    opponent = _load(opponent_path, "planner_opponent")

    env = make("kaggriculture", configuration={"episodeSteps": EPISODE_STEPS, "seed": args.seed})
    env.reset(2)
    plan_limit = min(args.horizon, EPISODE_STEPS)
    actions = []
    proposals_seen = unique_seen = rollout_count = zero_rollout_steps = 0
    rollout_steps = rollout_cpu = 0.0
    wall_started = time.perf_counter()
    step_times = []
    pool = (concurrent.futures.ProcessPoolExecutor(max_workers=args.jobs)
            if args.jobs > 1 else None)

    try:
        while not env.done and len(actions) < plan_limit:
            step_started = time.perf_counter()
            current = int(_get(_obs(env, 0), "step", len(actions)) or len(actions))
            proposals = [_call(agent, _obs(env, 0)) for agent in portfolio]
            opponent_action = _call(opponent, _obs(env, 1))
            grouped = {}
            for proposal in proposals:
                grouped.setdefault(_key(proposal), proposal)
            proposals_seen += len(proposals)
            unique_seen += len(grouped)
            if len(grouped) == 1:
                zero_rollout_steps += 1
                winner = next(iter(grouped.values()))
            else:
                rollout_count += len(grouped)
                tasks = [(env, proposal, opponent_action, continuation_path,
                          opponent_path, current, args.horizon)
                         for proposal in grouped.values()]
                results = list(pool.map(_rollout, tasks)) if pool else [_rollout(task) for task in tasks]
                scores = [item[0] for item in results]
                winner = list(grouped.values())[max(range(len(scores)),
                                                    key=lambda i: (scores[i], -i))]
                rollout_cpu += sum(item[1] for item in results)
                rollout_steps += sum(item[2] for item in results)
            env.step([copy.deepcopy(winner), copy.deepcopy(opponent_action)])
            actions.append(copy.deepcopy(winner))
            elapsed = time.perf_counter() - step_started
            step_times.append(elapsed)
            print(f"step {len(actions):3d}/{plan_limit}: proposals={len(proposals)} "
                  f"unique={len(grouped)} time={elapsed:.3f}s", flush=True)

        # Kaggle exposes one final observation that is not executed. Stage 1
        # still records its action so every baked trace has 720 entries.
        if plan_limit == EPISODE_STEPS and len(actions) == EPISODE_STEPS - 1:
            actions.append(_call(portfolio[0], _obs(env, 0)))
    finally:
        if pool:
            pool.shutdown()

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(_encode(actions))

    planned = len(step_times)
    duplicate_rate = (proposals_seen - unique_seen) / proposals_seen if proposals_seen else 0
    zero_rate = zero_rollout_steps / planned if planned else 0
    elapsed = time.perf_counter() - wall_started
    per_step = elapsed / planned if planned else 0
    estimate = _estimate(planned, unique_seen, rollout_steps, rollout_cpu, args.jobs)
    print(f"entries: {len(actions)}  out: {out}")
    print(f"dedup hit rate: {duplicate_rate:.1%} ({proposals_seen - unique_seen}/"
          f"{proposals_seen}); zero-rollout steps: {zero_rollout_steps}/{planned} ({zero_rate:.1%})")
    print(f"rollouts: {rollout_count}  wall: {elapsed:.2f}s  per planned step: {per_step:.3f}s")
    if estimate is not None:
        print(f"estimated full 720-step run: {estimate / 60:.1f} min "
              f"({args.jobs} jobs, observed rollout rate; rough)")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portfolio", default=DEFAULT_PORTFOLIO,
                        help="comma-separated seat-0 agent paths")
    parser.add_argument("--opp", default=DEFAULT_OPP, help="seat-1 agent path")
    parser.add_argument("--seed", type=int, default=90001)
    parser.add_argument("--out", required=True, help="stage-1-compatible .b85 output")
    parser.add_argument("--horizon", type=int, default=EPISODE_STEPS,
                        help="rollout length; values below 720 also plan only that prefix")
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
    args = parser.parse_args()
    if args.horizon < 1:
        parser.error("--horizon must be at least 1")
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    plan(args)


if __name__ == "__main__":
    main()
