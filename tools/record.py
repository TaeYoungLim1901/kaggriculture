"""Record one seat-0 episode as a compact zlib/base85 action blob."""
import argparse
import base64
import copy
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILTINS = {"pass", "random", "starter"}


def _spec(value, must_exist=False):
    if value in BUILTINS:
        return value
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if must_exist and not path.is_file():
        raise SystemExit(f"agent not found: {path}")
    return str(path)


def record_episode(me, opp, seed, out, steps=720):
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable

    me_path = Path(me).resolve()
    if not me_path.is_file():
        raise FileNotFoundError(me_path)
    opp_spec = _spec(str(opp))
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
    env.run([str(me_path), opp_spec])

    # Frame 0 is the framework's pre-initialization call. Frame 1 contains the
    # action emitted for observation step 0; the final observation is not acted
    # on by a 720-step episode, so emit it once directly to complete the blob.
    actions = [copy.deepcopy(frame[0].action) for frame in env.steps[1:]]
    if len(actions) < steps:
        raw = me_path.read_text(encoding="utf-8")
        agent = get_last_callable(raw, path=str(me_path))
        final_obs = copy.deepcopy(env.steps[-1][0].observation)
        while len(actions) < steps:
            actions.append(copy.deepcopy(agent(final_obs)))
    if len(actions) != steps:
        raise RuntimeError(f"expected {steps} actions, captured {len(actions)}")

    payload = json.dumps(actions, separators=(",", ":"), ensure_ascii=True).encode()
    blob = zlib.compress(payload)
    encoded = base64.b85encode(blob)
    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(encoded)
    print(f"entries: {len(actions)}  blob: {len(encoded)} bytes  out: {out_path}")
    return out_path, len(actions), len(encoded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--me", required=True, help="seat-0 agent file")
    parser.add_argument("--opp", required=True, help="seat-1 agent file or builtin")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--out", required=True, help="blob output file")
    args = parser.parse_args()
    record_episode(_spec(args.me, must_exist=True), _spec(args.opp), args.seed, args.out)


if __name__ == "__main__":
    main()
