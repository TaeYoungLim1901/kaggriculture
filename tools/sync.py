"""Credential-gated git upload helper."""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    ("KG" + "AT_", re.compile("KG" + "AT_")),
    ("gh" + "o_", re.compile("gh" + "o_")),
    ("gh" + "p_", re.compile("gh" + "p_")),
    ("github" + "_pat_", re.compile("github" + "_pat_")),
    ("-" * 5 + "BEGIN", re.compile("-" * 5 + "BEGIN")),
    ("api" + "_key", re.compile("api" + "_key")),
    ("api" + "Key", re.compile("api" + "Key")),
    ("access" + "_token", re.compile("access" + "_token")),
    ("pass" + "word", re.compile("pass" + "word")),
    ("sec" + "ret", re.compile("sec" + "ret")),
)
SECRET_PREFIXES = tuple(re.compile(pattern + r"[A-Za-z0-9_-]{8,}") for pattern in (
    "KG" + "AT_", "gh" + "o_", "gh" + "p_", "github" + "_pat_",
))
ASSIGNMENT = re.compile(
    r"(?:api" + "_key|api" + "Key|access" + "_token|pass" + "word|sec" + "ret)"
    r"\s*[:=]\s*[\"']?([^\"'\s,`]+)"
)


def credential_scan():
    files = [p for p in subprocess.check_output(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0") if p]
    matches = []
    for name in files:
        try:
            lines = (ROOT / name).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            for label, pattern in PATTERNS:
                if not pattern.search(line):
                    continue
                actual = any(prefix.search(line) for prefix in SECRET_PREFIXES)
                actual |= "PRIVATE KEY" in line
                match = ASSIGNMENT.search(line)
                actual |= bool(match and match.group(1) not in {"...", "TOKEN", "token", "value"})
                matches.append((name, number, label, actual, line))
    for name, number, label, actual, line in matches:
        print(f"{name}:{number}:{label}:{'SECRET' if actual else 'prose/path'}:{line}")
    bad = [match for match in matches if match[3]]
    print(f"Credential scan: {len(matches)} matches; actual secrets: {len(bad)}")
    if bad:
        print("Credential gate failed; refusing to push.", file=sys.stderr)
        return False
    return True


def main():
    if not credential_scan():
        return 1
    subprocess.run(
        ["git", "-c", "core.excludesfile=.git/info/exclude", "add", "-A"],
        cwd=ROOT,
        check=True,
    )
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        print("Nothing to commit.")
        changed = []
    else:
        message = sys.argv[1] if len(sys.argv) > 1 else datetime.now().astimezone().strftime(
            "Sync %Y-%m-%d %H:%M:%S %z"
        )
        message += "\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
        subprocess.run(["git", "commit", "-m", message], cwd=ROOT, check=True)
        changed = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=ROOT
        ).decode().splitlines()
        subprocess.run(["git", "push"], cwd=ROOT, check=True)
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode()
    print(f"Changed files: {len(changed)}")
    print("git status --short:")
    print(status, end="" if status else "(clean)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
