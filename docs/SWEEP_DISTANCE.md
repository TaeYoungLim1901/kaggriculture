# SWEEP_DISTANCE — does distance weighting unlock expansion? (2026-08-14)

Panel: `tools/sweep.py`, opponent `bench/v3.py` (a byte copy of the shipped build), 8 seeds × 2
seats, `--seed0 90001`, 720 steps. W-L reads directly as better/worse than what we ship.

`DIST_WEIGHT = 1` is the shipped behavior. One-quadrant configs use the shipped tile plan; XW
configs use M12c: two quadrants, reserve 3, plant cap, 12 melon and 5 wheat tiles.

| config | DIST_WEIGHT | W-L-T | mean margin | worst margin |
| --- | ---: | --- | ---: | ---: |
| W5 | 5 | 1W-3L-12T | -6 | -1,042 |
| W10 | 10 | 0W-16L-0T | -1,151 | -2,622 |
| W20 | 20 | 0W-16L-0T | -1,869 | -4,111 |
| W40 | 40 | 0W-16L-0T | -1,090 | -1,689 |
| XW5 | 5 | 2W-14L-0T | -1,766 | -5,286 |
| XW10 | 10 | 2W-14L-0T | -2,067 | -5,767 |
| XW20 | 20 | 6W-10L-0T | -1,626 | -5,791 |

## Verdict

Distance weighting does not unlock expansion. No one-quadrant config beats the shipped build, so
none required the requested 30-game confirmation. The best expansion variant, XW20, still loses
6W-10L. Keep `DIST_WEIGHT = 1`; no shipped default or submission changes.

The edit and logic checks also preserved the shipped signals: `$343`, BUY_SEED 60, PASS 3518,
and PLANT 104.
