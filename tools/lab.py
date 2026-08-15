"""Experiment ledger: queue commands, run them, keep one line per result.

The point is token cost. A training run or an eval prints hundreds of lines; the
agent driving the work only needs the verdict. `lab.py` swallows the output into
a log file and appends ONE json line per experiment, so a session reads
`lab.py tail` (20 short lines) instead of 20 raw logs.

    python tools/lab.py add "python tools/eval.py --me x.py --opp y.py" -n wheat30
    python tools/lab.py run --jobs 2
    python tools/lab.py tail

The command owns its own metric: whatever it prints LAST on stdout becomes the
summary. Print one decisive line (`RESULT auc=0.913 fold=5`) and nothing else
matters. Logs stay in .lab/logs/<id>.log for when something actually breaks.
"""
import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / ".lab"
LEDGER = LAB / "experiments.jsonl"
LOGS = LAB / "logs"


def _rows():
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append(row):
    LAB.mkdir(exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _rewrite(rows):
    LEDGER.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def add(args):
    row = {"id": f"{int(time.time())}{len(_rows()):03d}", "name": args.name or args.command[:40],
           "command": args.command, "note": args.note, "state": "queued",
           "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _append(row)
    print(row["id"], row["name"])


def _run_one(row):
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{row['id']}.log"
    started = time.time()
    completed = subprocess.run(row["command"], shell=True, cwd=ROOT,
                               capture_output=True, text=True)
    output = completed.stdout + completed.stderr
    log.write_text(output, encoding="utf-8")
    lines = [ln.strip() for ln in completed.stdout.splitlines() if ln.strip()]
    row.update(state="done" if completed.returncode == 0 else "failed",
               exit=completed.returncode, seconds=round(time.time() - started, 1),
               summary=lines[-1][:300] if lines else "(no stdout)",
               log=str(log if not log.is_relative_to(ROOT) else log.relative_to(ROOT)))
    return row


def run(args):
    rows = _rows()
    todo = [r for r in rows if r["state"] == "queued"][:args.limit]
    if not todo:
        print("nothing queued")
        return
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        done = list(pool.map(_run_one, todo))
    by_id = {r["id"]: r for r in done}
    _rewrite([by_id.get(r["id"], r) for r in rows])
    for r in done:
        print(f"{r['state']:6} {r['seconds']:7.1f}s  {r['name'][:28]:28} {r['summary'][:90]}")


def tail(args):
    for r in _rows()[-args.n:]:
        state = r["state"]
        extra = r.get("summary", "") if state != "queued" else r["command"][:90]
        print(f"{r['id']}  {state:6} {r['name'][:28]:28} {extra[:100]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="queue a command")
    a.add_argument("command")
    a.add_argument("-n", "--name", help="short label")
    a.add_argument("--note", default="", help="hypothesis being tested")
    a.set_defaults(func=add)
    r = sub.add_parser("run", help="run queued commands")
    r.add_argument("--jobs", type=int, default=1)
    r.add_argument("--limit", type=int, default=99)
    r.set_defaults(func=run)
    t = sub.add_parser("tail", help="last N ledger rows")
    t.add_argument("n", nargs="?", type=int, default=20)
    t.set_defaults(func=tail)
    args = ap.parse_args()
    return args.func(args) or 0


def demo():
    """Self-check: queue two commands, run them, and read the ledger back."""
    global LAB, LEDGER, LOGS
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        LAB, LEDGER, LOGS = Path(tmp), Path(tmp) / "e.jsonl", Path(tmp) / "logs"
        add(argparse.Namespace(command=f'{sys.executable} -c "print(1); print(\'RESULT ok=1\')"',
                               name="good", note=""))
        add(argparse.Namespace(command=f'{sys.executable} -c "raise SystemExit(3)"',
                               name="bad", note=""))
        run(argparse.Namespace(jobs=2, limit=99))
        rows = _rows()
        assert [r["state"] for r in rows] == ["done", "failed"], rows
        assert rows[0]["summary"] == "RESULT ok=1", rows[0]
        assert rows[1]["exit"] == 3, rows[1]
        assert (LOGS / f"{rows[0]['id']}.log").exists()
        assert not [r for r in rows if r["state"] == "queued"]
        print("demo ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        raise SystemExit(main())
