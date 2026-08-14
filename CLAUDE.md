# CLAUDE.md

All working rules live in [AGENTS.md](AGENTS.md). Read it first, every session, and again after any
context compaction.

Two things that must never be lost:

1. **Codex CLI subagents always run `-m gpt-5.6-luna -c model_reasoning_effort="xhigh"`.** The slug is
   `gpt-5.6-luna`; plain `luna` 400s. No fallback model.
2. **Opus drives; Codex is the subagent.**
3. **Run the stage checker after every change** — `python tools/check.py edit|logic|strength|ship`
   (AGENTS.md §4). `edit` is 10 s and non-optional. Never claim a change works without its output.
