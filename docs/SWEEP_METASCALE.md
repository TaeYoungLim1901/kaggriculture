# Meta-scale sweep (2026-08-14)

The panel used `tools/sweep.py`, seed0 `90001`, 8 seeds × 2 seats, and 720 steps. The
new `--opp` flag was run against both the mirror (`bench/v3.py`) and the decoded meta
agent (`bench/v16_rc5_high_score_8c_4s_premium_market_.py`). Defaults in `main.py`
were unchanged.

T14 smoke test, 2 seeds × 2 seats:

| opponent | result | mean margin |
| --- | --- | ---: |
| mirror | 0W-4L-0T | -77,032 |
| meta | 0W-4L-0T | -135,802 |

Full panel, 8 seeds × 2 seats:

| config | mirror W-L-T | mirror mean | meta W-L-T | meta mean |
| --- | ---: | ---: | ---: | ---: |
| T14 | 0W-16L-0T | -82,218 | 0W-16L-0T | -123,189 |
| T10 | 0W-16L-0T | -22,618 | 0W-16L-0T | **-92,126** |
| T8 | 4W-12L-0T | **-7,909** | 0W-16L-0T | -98,567 |
| T14b | 0W-16L-0T | -80,983 | 0W-16L-0T | -123,189 |
| T14c | 0W-16L-0T | -81,590 | 0W-16L-0T | -123,189 |

The primary result is T10: it is the best of this panel against the meta, but its
`-92,126` mean margin is worse than the shipped-build reference `-83,638`. The mirror
panel selects T8 instead, confirming the expected niche-inheritance bias.

Best-config work count

`tools/buildprobe.py .sweep/T10.py` counts every farmer/hand action whose verb is not
`PASS`. T10 issued:

```text
d0:139 d1:80 d2:71 d3:71 d4:97 d5:71 d6:76 d7:123 d8:140 d9:105
d10:129 d11:151 d12:132 d13:130 d14:213 d15:165 d16:252 d17:252
d18:252 d19:252 d20:252 d21:252 d22:252 d23:252 d24:252 d25:252
d26:252 d27:252 d28:252 d29:241
```

Verdict

Scale alone does not change the answer. Even after making 10/14 hires reachable and
testing the decoded 75-tile/72-occupied layout, every expansion variant loses to the
meta. T10 reaches 252 work actions/day late in the episode, near the meta's 250–340
range, but remains below the shipped reference. The remaining gap is routing/locality,
not merely land, crop count, or the HIRE cap.

Required final checks

```text
python tools/check.py edit

=== edit ===
Loading environment open_spiel_env failed: No module named 'pyspiel'
OK  edit: 60-step self-play clean, $343
```

```text
python tools/check.py logic

=== logic ===
Loading environment open_spiel_env failed: No module named 'pyspiel'
PASS determinism
PASS never raises
PASS action schema
No-op table (PASS is intentionally excluded from the threshold):
  verb                     emitted  no-op  rate
  BUILD_COOP                     0      0   0.0%
  BUILD_PASTURE                 30      0   0.0%
  BUY_ANIMAL                    30      0   0.0%
  BUY_LAND                       0      0   0.0%
  BUY_PRODUCT                  148      0   0.0%
  BUY_SEED                      60      0   0.0%
  CARE                         718      0   0.0%
  COLLECT_FERTILIZER           656      0   0.0%
  DIG                            0      0   0.0%
  DROP                           0      0   0.0%
  EAST                         634      0   0.0%
  FEED                         708      0   0.0%
  FERTILIZE                      0      0   0.0%
  HARVEST                      298      0   0.0%
  HIRE                         480      0   0.0%
  NORTH                       2164      0   0.0%
  PASS                        3518   3518 100.0%
  PICKUP                       184      0   0.0%
  PLACE                         30      0   0.0%
  PLANT                        104      0   0.0%
  SELL                        1150      0   0.0%
  SOUTH                        714      0   0.0%
  WATER                        700      0   0.0%
  WEST                        2004      0   0.0%
PASS no-op rate
PASS economic floor
```
