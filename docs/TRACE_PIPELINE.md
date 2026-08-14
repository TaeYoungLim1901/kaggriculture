# Trace pipeline

Stage 1 records the current reactive agent exactly as a 720-entry plan. It does
not optimize the plan.

## Use

```powershell
python tools/record.py --me main.py --opp starter --seed 90001 --out build/main.b85
python tools/bake.py build/main.b85
python tools/verify_trace.py
```

`record.py` runs the supplied agent by file path, stores seat 0's action dicts as
compact JSON → zlib → base85, and prints the entry count and encoded blob size.
The environment makes one pre-initialization call before the first effective
action. The recorder takes effective actions from `env.steps[1:]` and directly
emits the final observation's action, producing exactly 720 entries. The baked
agent indexes those entries with `day * 24 + hour`, so it has no episode-local
counter to desynchronize.

`bake.py` embeds the blob and a demo-free copy of `main.py`'s reactive policy in
`build/trace_<blob stem>.py`. The generated `agent` is the last callable in the
file, and exceptions fall back to a PASS action.

## Measured equivalence

The acceptance artifact is `build/trace_main.py`, recorded against `starter` at
seed 90001. Its blob is **5,860 bytes** and contains **720 entries**.

| Seed | Source seat 0 | Replay seat 0 | Δ | Source seat 1 | Replay seat 1 | Δ | First divergence |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 90001 | 69,409 | 69,409 | 0.00% | 3,494 | 3,494 | 0.00% | none |
| 1000 | 98,731 | 98,731 | 0.00% | 3,500 | 3,500 | 0.00% | none |
| 8919 | 72,711 | 72,711 | 0.00% | 3,504 | 3,504 | 0.00% | none |

`verify_trace.py` runs both agents through file paths, compares both final money
values, and reports the first differing effective step if action streams differ.
All three pairs matched exactly; no divergence was found.

The requested v3 probe was also near even:

```text
build/trace_main.py vs bench/v3.py: 4W-4L-0T over 8 games
mean margin +112, worst -1,550
```
