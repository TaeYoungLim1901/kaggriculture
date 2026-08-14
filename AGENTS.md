# AGENTS.md — Kaggriculture work rules

> Read this first, every session. Applies to Claude Code, Codex CLI, and every subagent.

## 0. NON-NEGOTIABLE: model routing

**Opus is the primary driver. Codex CLI is the subagent, and Codex ALWAYS runs `luna` at `xhigh` reasoning.**

Every Codex delegation, without exception:

```bash
codex exec -m gpt-5.6-luna -c model_reasoning_effort="xhigh" --skip-git-repo-check "<task>" < /dev/null
```

**`< /dev/null` is mandatory when launching from a tool/background shell.** Without a tty on stdin,
`codex exec` prints `Reading additional input from stdin...` and blocks forever waiting for EOF — the
prompt argument is *appended to*, not replaced by, stdin. It looks exactly like a long-running job:
process alive, no output, near-zero CPU. Three jobs burned 2.4 h this way on 2026-08-13.
(`ERROR rmcp::transport::worker: ... 127.0.0.1:27182/mcp` lines in the output are unrelated noise from
a dead local MCP server; ignore them.)

The model slug is **`gpt-5.6-luna`**, not `luna` — the short name returns
`400 The 'luna' model is not supported when using Codex with a ChatGPT account`, which looks like an
auth problem but is just a bad slug. `xhigh` is a supported reasoning level for it
(see `~/.codex/models_cache.json`). ChatGPT-account auth is fine; no API key needed.

Rules:
- Never drop `-m gpt-5.6-luna`. Never drop `model_reasoning_effort="xhigh"`. Never fall back to
  `gpt-5.6-sol` or the config default silently — if it fails, STOP and report, do not substitute.
- Simple mechanical work (scripts, parsers, sweeps, refactors, test harnesses) goes to Codex by
  default. Opus keeps strategy and the submission.
- Add `--sandbox read-only` for analysis-only tasks; `--sandbox workspace-write` when Codex must edit files.
- Opus keeps the strategy, the final call, and the submission. Codex does bounded work: replay parsing, simulation sweeps, per-crop math, refactors.
- Re-read this section whenever the conversation has been compacted or summarized. If you cannot see this rule in context, re-read `AGENTS.md` before delegating anything.

Verified working 2026-08-13.

## 1. What this repo is

Agent for the Kaggle **Kaggriculture** simulation competition (2-player farming sim, 720 turns).
There is no dataset — the "data" is the environment itself, shipped inside `kaggle-environments`.

| Path | What |
| --- | --- |
| `main.py` | The submission. Must expose `agent(obs)` at module root. |
| `tools/eval.py` | Local paired evaluation (both seats × N seeds). The only source of truth for "is it better". |
| `tools/check.py` | Staged bug checkers, see §4. Run after every change. |
| `tools/sweep.py` | Constant-override sweeps: materialises variants of `main.py` and evals each. |
| `tools/shedprobe.py` | End-of-day shed occupancy + `panic` firings. Answers "are we over capacity". |
| `tools/buildprobe.py` | First day of each BUILD/BUY verb + money by day. Answers "did the engine start late". |
| `bench/` | Public top-scorer agents, extracted from their Kaggle notebooks. Opponents, not templates. |
| `tools/quota.py` | Submissions left today. 5/day, resets 09:00 KST, failures count. Run before submitting. |
| `tools/tracedump.py` | Decodes a bench agent's hard-coded `_ACTIONS` replay into its plan. |
| `tools/record.py` / `bake.py` / `verify_trace.py` | Trace pipeline: record an episode → bake a standalone replay agent into `build/` → prove it reproduces the source. See `docs/TRACE_PIPELINE.md`. |
| `tools/plan.py` | Offline rollout planner: per-step policy-portfolio selection scored by full-episode rollouts. See `docs/TRACE_PLANNER.md`. |
| `tools/thrash.py` | Re-targeting rate and movement per productive action. |
| `docs/GAME_SPEC.md` | Full game rules (competition-provided). |
| `docs/GETTING_STARTED.md` | Kaggle CLI + submission workflow (competition-provided). |
| `docs/META.md` | What the top of the leaderboard actually does + strategy math. |
| `CONTEXT.md` | Condensed competition rules and top-scorer links. |
| `research/notebooks/` | Pulled top-scorer notebooks (`.ipynb` + flattened `.py`). |

## 2. Environment quirks on this machine

- Python 3.14. `pip install kaggle-environments` **fails** (pygame has no 3.14 wheel).
  Install with `pip install --no-deps -U kaggle-environments` — the env itself only needs stdlib.
- `kaggle` CLI is not on PATH. Full path:
  `C:/Users/livde/AppData/Roaming/Python/Python314/Scripts/kaggle.exe`
- Kaggle auth already works (`~/.kaggle/access_token`).
- Env source of truth (read this, not the docs, when behavior is unclear):
  `C:/Users/livde/AppData/Roaming/Python/Python314/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`

## 3. Iteration loop

1. Change `main.py`.
2. Run the stage checkers (§4). `python tools/eval.py --games 8` for a fast signal;
   `--games 30` before believing anything.
3. Always evaluate in **both seats** on the **same seeds** (eval.py does this). Single-seat results lie.
4. Leaderboard rating counts **win/loss only** — coin margin is worthless past +1. Optimize win rate, not money.
5. Only then submit (max 5/day), and only when the user asks — it is outward-facing and rate-capped:
   ```bash
   python tools/package.py
   kaggle competitions submit kaggriculture -f submission.tar.gz -m "<version note>"
   ```
   Always the tar.gz, never a bare `main.py`. Submitting requires face verification on the Kaggle
   account; before that is done the file uploads fully and then `CreateSubmission` returns
   `403 Client Error: Forbidden` — a verification issue, never an agent or packaging fault, so do not
   debug `main.py` over it. Credentials are `~/.kaggle/access_token`; there is no `kaggle.json`.
6. Check the result: `kaggle competitions submissions kaggriculture`. The CLI table hides the reason
   for a failure — get it from Python:
   ```python
   import kaggle; api = kaggle.KaggleApi(); api.authenticate()
   [(s.ref, s.status, s.error_description) for s in api.competition_submissions("kaggriculture")]
   ```

## 4. Bug checkers — one per stage, run them in order

Long contexts drift and drop invariants. Do not eyeball a diff; run the stage that matches the
change. Single entry point, `tools/check.py`, wrapping the tools that already exist:

| Stage | Command | Cost | Catches |
| --- | --- | --- | --- |
| after **any** `main.py` edit | `python tools/check.py edit` | ~10 s | syntax, `agent` not last callable, per-step timeout, crash — via 60-step **file-path** self-play |
| after changing decision logic | `python tools/check.py logic` | ~1 m | `tests/test_invariants.py`: determinism, never-raises, action schema, no-op rate, economic floor |
| after a change meant to win more | `python tools/check.py strength` | ~2 m | `tools/eval.py --games 8`, both seats, same seeds. Exit 1 if not a net win. |
| before packaging / submitting | `python tools/check.py ship` | ~1 m | `tools/package.py`: full 720-step self-play as Kaggle loads it + tar integrity |

`python tools/check.py all` runs all four. Extra args pass through
(`check.py strength --games 30 --opp bench/v16_rc5_high_score_8c_4s_premium_market_.py`).

Rules:
- **`edit` is not optional.** It is 10 s and it is the stage that would have caught both wasted
  submissions (refs 55487986, 55488019).
- Never claim "it works" from a stage you did not run. Paste the checker output.
- A red stage stops the pipeline — do not run the next stage, fix first.
- **Every Codex delegation that touches `main.py` must end by running the stages it affects and
  reporting the output**, using the §0 invocation (`-m gpt-5.6-luna`,
  `model_reasoning_effort="xhigh"`, `--sandbox workspace-write`, `< /dev/null`). Opus verifies by
  re-running `check.py`, never by trusting the subagent's summary.
- New invariant discovered? Add it to `tests/test_invariants.py` (logic stage), not to a one-off
  script that gets forgotten.

## 5. Hard constraints

- Submission = single `main.py` (or tar.gz with `main.py` at root). No network at eval time ("no ingress or egress").
- No private code sharing. Public Kaggle notebooks are fair to read and are OSI-licensed by the rules.
- **`agent` must be the LAST callable defined in `main.py`.** Kaggle does not look up the name. It
  runs `exec(code, {})` and takes `[v for v in globals.values() if callable(v)][-1]` — the last
  callable *by position*. A `demo()` defined after `agent()` was submitted **as the agent**, running
  a full 720-step episode every turn; Kaggle reported only `Validation Episode failed` (two wasted
  submissions, refs 55487986 and 55488019). `tools/package.py` now asserts this.
- **Validate the way Kaggle loads it**: `env.run(["main.py", "main.py"])` with the *file path*, not
  `env.run([mod.agent, ...])`. Passing the function object bypasses Kaggle's loader and its per-step
  `actTimeout` (1 s), so a submission-breaking file can pass every function-level check.
- `main.py` must never raise: wrap `agent()` in try/except returning a PASS action. An exception forfeits the episode.
- Agent must be fast — 720 steps × many episodes. No heavy per-step computation.
