# MISTAKES.md — every mistake that cost us, and the guard that now stops it

One row per incident. **A row without a guard is not finished.** If a new mistake cannot be turned
into a check, write down the rule and put it in `AGENTS.md`, not here.

Read this file before a submission and after any context compaction.

## Cost incurred

| # | Mistake | What it cost | Guard that now prevents it |
| --- | --- | --- | --- |
| 1 | `demo()` defined after `agent()` in `main.py`. Kaggle takes the LAST callable by position, not the name, so it submitted `demo` as the agent | **2 wasted submissions** (refs 55487986, 55488019), a whole day of ladder time | `tools/package.py` asserts `agent` is last; `check.py edit` runs a **file-path** self-play, which is how Kaggle loads it |
| 2 | `codex exec` launched from a tool shell without `< /dev/null` — it blocks forever reading stdin and looks like a slow job | **2.4 h across three jobs** (2026-08-13) | `AGENTS.md` §0 mandates `< /dev/null`; never launch Codex any other way |
| 3 | Read Optuna's ranking at 12 episodes as a result. Its unanimous top three (`HIRES` 12 + `HIRE_SLOTS` 4 + 6S+6C) measured **12W-52L** at 32 | ~200 trials of compute, one session's main lead | Nothing enters `main.py` without a **32-seed, both-seat** confirmation. `check.py strength` exists for exactly this |
| 4 | Read `tools/bookprobe.py`'s numbers as executed trades. They are order quantities as *placed*; an order is abandoned the moment one unit fails, so it overstates everything | A whole session reasoning about a "$217k wheat business" that nets $5k | `tools/fillprobe.py` wraps the env's `_commit_unit` and counts only settled units. `bookprobe`'s docstring now says it is requests |
| 5 | Pushed a generated Kaggle kernel whose script had a syntax error. The kernel reported `COMPLETE` with an empty output list — identical to a job that simply produced nothing | One kernel run, plus the time spent debugging the wrong layer | `tools/kjob.py` runs `compile()` on the generated script before pushing, and the script writes a traceback into `result.txt` on any failure |
| 6 | Piped a long background job through `\| Select-Object -Last 3` in PowerShell. The output file came back empty with exit 0, twice | A 32-seed eval re-run (~10 min) | Background runs redirect to a file (`> "$env:TEMP\x.txt" 2>&1`) and the file is read afterwards. Never judge a run by a pipeline's tail |
| 7 | Added a second `"H12"` key to `sweep.CONFIGS`; a duplicate is silently shadowed, so a sweep can print a row it never ran | Nothing yet — caught the same day | `tests/test_invariants.py::_check_sweep_configs` (logic stage) fails on duplicate keys. It immediately found two older duplicates, `W20` and `v-H11F7` |
| 8 | Left `s-*` and `f-*` sweep rows behind after reverting `CROP_PLAN2` / `PLAN_DAY` / `SELL_FLOOR` from `main.py`. An override naming a constant that no longer exists is dropped silently and the row measures the baseline | Would have produced fake "no effect" rows | Same check: every override key must be in `OVERRIDABLE` **and** exist in `main.py`. The 5 dead rows are deleted |
| 9 | `tools/fillprobe.py` v1 matched farms by identity against `env.state[...].observation`, which hands out copies. It reported the opponent's entire economy as `$0` | Nearly published a false table | The probe resolves ownership inside `_process_market`, where the real `farms` list lives. **Any probe that can report a zero must be checked against a known-nonzero case before its output is used** |
| 10 | Judged berry builds on the mirror panel alone. In a mirror both sides sell the same goods, so MILK settles at $49/unit against $234 vs an opponent who sells berries instead | Three sessions of "berries lose" rows that were partly a panel artifact | Every accept decision needs the mirror **and** at least one independent opponent (`bench/ref_broker_bea.py`, `bench/ref_closer_cleo.py`), and they must agree in sign — see `AGENTS.md` §5 |

| 11 | Read a Kaggle-kernel sweep as a result without checking that the remote environment matches this one. The panel reported `BASE` beating `ref_broker_bea` 11W-3L **+62**, where the same pairing locally is 0W-16L **-47,463**, and v15 as 6W-10L -89 against a local 8W-0L +6,770 | One panel run, and it would have reversed a strategic call if believed | `tools/kjob.py` prints the remote `kaggle-environments` version and an env fingerprint (`ANIMALS["COW"]`, `PRICE_FLOOR`) in every run. **A remote number is not evidence until a known local pairing reproduces there** |

## Rules that are not checkable by code

- **Never edit `main.py` while a sweep is running.** `tools/sweep.py` materialises each variant from
  `main.py` at the moment it runs that row, so an edit mid-sweep silently changes every later row.
  Queue the edit, or run the sweep against a snapshot in `bench/`.
- **Snapshot before shipping.** `bench/vN.py` is the previous build. Without it, tomorrow's "is this
  better" question has no opponent.
- **Report the panel with the number.** "+997" means nothing without "vs `bench/v16.py`, 32 seeds ×
  2 seats, seed0 90001".
- **A ladder score read the same day is not settled.** One submission read 650.6 / 712.8 / 660.5 in
  a single day.
