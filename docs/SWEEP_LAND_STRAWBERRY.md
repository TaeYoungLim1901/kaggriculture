# Land + strawberry sweep

## Result

No configuration beat the baseline on the leaderboard metric. Every row was
0W-16L-0T, so there is no winning configuration on this panel. The best
diagnostic margin was the seed-capital fix alone (`H`), at -82,018 versus the
baseline -83,529; that is not a rating improvement because both records are
0W-16L.

## Protocol

- Interpreter: `C:/Users/livde/AppData/Local/Python/pythoncore-3.14-64/python.exe`
- Opponent: `bench/v16_rc5_high_score_8c_4s_premium_market_.py`
- Panel: `--games 8 --seed0 90001 --steps 720`, both seats per seed
- Evaluator: existing `tools/eval.py`; no evaluation logic was reimplemented
- Variants: `C:/Users/livde/AppData/Local/Temp/claude/D--hackathon-KAGGRICULTURE/d866f6e4-1526-4528-9cda-86a8caf2e807/scratchpad`

`A` is an unchanged materialized copy of `main.py`. `C` was the best of the
C/D bracket by W-L first, then mean margin only because all W-L records tied.
`E`, `F`, and `G` inherit that C plan. `H+best` is stored as `H_best.py` in the
scratchpad because the plus sign is sanitized for filenames.

| Config | Change | W-L-T | Win rate | Mean margin | Worst margin |
|---|---|---:|---:|---:|---:|
| A | baseline | 0-16-0 | 0% | -83,529 | -94,996 |
| B | `LAND_TARGET=2` | 0-16-0 | 0% | -96,741 | -128,971 |
| C | land 2; MELON 4, WHEAT 6, STRAWBERRY 20 | 0-16-0 | 0% | -95,145 | -118,197 |
| D12 | C with STRAWBERRY 12 | 0-16-0 | 0% | -104,116 | -124,047 |
| D28 | C with STRAWBERRY 28 | 0-16-0 | 0% | -98,403 | -120,709 |
| E10 | C with `HIRES=10` | 0-16-0 | 0% | -97,628 | -128,213 |
| E12 | C with `HIRES=12` | 0-16-0 | 0% | -97,628 | -128,213 |
| F | C with `LAND_TARGET=3` | 0-16-0 | 0% | -101,125 | -126,650 |
| G10 | C with 10 sheep + 8 cows | 0-16-0 | 0% | -102,762 | -138,295 |
| G14 | C with 14 sheep + 8 cows | 0-16-0 | 0% | -125,392 | -153,609 |
| H | seed target fix only | 0-16-0 | 0% | -82,018 | -92,802 |
| H+best | H plus C | 0-16-0 | 0% | -91,398 | -120,867 |

## What the numbers say

The land-only control is worse than baseline by 13,212 mean coins, confirming
that extra land is cash burn when the existing task zipper does not fill it.
Adding strawberries does not repair that: C sells only 95 strawberries on the
representative seed, versus 274 for the opponent, while milk falls to 72 units
at about $1.5 each. D12 and D28 are both worse than C, so changing strawberry
tile count inside this route is not enough.

Representative sell profile, seed 90001, both seats evaluated by the existing
`tools/sellprofile.py`:

| Variant | Strawberry revenue | Milk revenue | Wool revenue | Melon revenue | Fertilizer revenue |
|---|---:|---:|---:|---:|---:|
| A | $0 | $26,382 | $43,332 | $9,370 | $12,668 |
| C | $11,618 | $106 | $22,302 | $8,392 | $3,666 |
| H | $0 | $25,806 | $45,746 | $8,654 | $13,182 |
| H+best | $11,135 | $116 | $22,961 | $8,208 | $4,364 |
| opponent | $54,900 | $24,939 | $24,763 | $2,268 | $11,011 |

The seed fix removes unnecessary seed inventory without changing the route, so
H preserves the profitable animal mix and improves the mean diagnostic margin
by 1,511. Combining it with C adds some strawberry revenue but recreates the
milk glut and loses 9,380 mean coins versus H. More hires were flat at 10 and
12 and worse than C; both sheep-heavy herd variants were worse, with 14 sheep
collapsing to -125,392.

Idle-PASS diagnostic on representative seed 90001, both seat orders, with an
explicit 720-frame/DONE assertion:

| Variant | PASS unit slots | Total unit slots | Idle-PASS rate |
|---|---:|---:|---:|
| A | 3,784 | 12,462 | 30.4% |
| C | 2,933 | 12,416 | 23.6% |
| H | 3,476 | 12,462 | 27.9% |
| H+best | 2,716 | 12,186 | 22.3% |

The land/strawberry route does reduce idle slots, but the revenue mix shows why
that is not sufficient: the newly occupied work displaces milk/wool production
and pushes milk to the floor. These numbers rule out land alone, strawberry
tile-count bracketing inside the current route, extra hires, and sheep-heavy
scaling as immediate wins. The seed-buying capital defect is real and modestly
helpful alone, but it does not produce a win.

## Errors and artifacts

- `eval.py` configuration runs: no errors. All 12 rows produced 16 game rows and
  a consistent W-L-T summary.
- The environment printed the non-fatal warning
  `Loading environment open_spiel_env failed: No module named 'pyspiel'` during
  sell-profile diagnostics; all diagnostic episodes completed.
- A serial 16-episode idle diagnostic exceeded the outer 300-second shell
  timeout; it was rerun on seed 90001, completed, and asserted 720/DONE. This
  did not affect the `eval.py` table.

`main.py` was not modified and nothing was submitted to Kaggle.
