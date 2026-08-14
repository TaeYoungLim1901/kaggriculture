"""Bake a recorded blob and the reactive fallback into one standalone agent."""
import argparse
import ast
import base64
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _strip_demo(source):
    tree = ast.parse(source)
    remove = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "demo":
            remove.append((node.lineno, node.end_lineno))
        elif isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"
            ):
                remove.append((node.lineno, node.end_lineno))
    lines = source.splitlines(keepends=True)
    for start, end in sorted(remove, reverse=True):
        del lines[start - 1:end]
    source = "".join(lines)
    source = source.replace("def agent(obs):", "def _reactive_agent(obs):", 1)
    return source.rstrip() + "\n"


def load_blob(path):
    encoded = Path(path).read_bytes()
    return json.loads(zlib.decompress(base64.b85decode(encoded)))


def bake_blob(blob_path, output=None):
    blob_path = Path(blob_path).resolve()
    if not blob_path.is_file():
        raise FileNotFoundError(blob_path)
    actions = load_blob(blob_path)
    if not isinstance(actions, list):
        raise ValueError("blob must decode to a list")

    main_source = _strip_demo((ROOT / "main.py").read_text(encoding="utf-8"))
    encoded = base64.b85encode(
        zlib.compress(json.dumps(actions, separators=(",", ":"), ensure_ascii=True).encode())
    ).decode("ascii")
    trace_source = f'''\nimport base64
import copy
import json
import zlib

_ACTIONS = json.loads(zlib.decompress(base64.b85decode({encoded!r})))


def _trace_step(obs):
    day = int(_g(obs, "day", 0) or 0)
    hour = int(_g(obs, "hour", 0) or 0)
    return day * 24 + hour


def _trace_pass(obs):
    farms = _g(obs, "farms", []) or []
    seat = int(_g(obs, "player", 0) or 0)
    hands = _g(farms[seat], "hands", []) if seat < len(farms) else []
    return {{"farmer": ["PASS"], "hands": [["PASS"] for _ in (hands or [])], "market": []}}


def agent(obs):
    try:
        step = _trace_step(obs)
        if 0 <= step < len(_ACTIONS):
            return copy.deepcopy(_ACTIONS[step])
        return _reactive_agent(obs)
    except Exception:
        try:
            return _trace_pass(obs)
        except Exception:
            return {{"farmer": ["PASS"], "hands": [], "market": []}}
'''
    output = Path(output) if output is not None else ROOT / "build" / f"trace_{blob_path.stem}.py"
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(main_source + trace_source, encoding="utf-8", newline="\n")
    compile(output.read_bytes(), str(output), "exec")
    print(f"entries: {len(actions)}  agent: {output}  bytes: {output.stat().st_size}")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blob", help="record.py output file")
    args = parser.parse_args()
    bake_blob(args.blob)


if __name__ == "__main__":
    main()
