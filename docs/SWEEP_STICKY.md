# Sticky-target sweep (2026-08-14)

`tools/thrash.py` traced the final per-unit plan inside `_act` for seed `90001`
against the decoded meta agent. The episode ran 719 agent calls for 720 configured
steps. A retarget is counted only when the unit was not standing on its previous
target; productive excludes `PASS` and the four movement verbs.

| config | pre-arrival retargets | target runs | mean target survival | movement | productive | movement / productive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `main.py` (`STICKY=False`) | 334 | 1,916 | 2.36 | 2,790 | 1,703 | 1.64 |
| `.sweep/T10.py` (`STICKY=False`) | 726 | 2,366 | 2.36 | 3,797 | 1,629 | 2.33 |
| `.sweep/S-on.py` (`STICKY=True`) | 93 | 1,729 | 2.74 | 3,041 | 1,650 | 1.84 |
| `.sweep/T10-on.py` (`STICKY=True`) | 176 | 1,785 | 2.87 | 3,585 | 1,387 | 2.58 |

The hypothesis is real: commitment cuts pre-arrival retargets by 72% on the
shipped layout and 76% at T10 scale. It does not improve routing efficiency;
movement per productive action rises in both cases.

## Panel

`tools/sweep.py`, seed0 `90001`, 8 seeds x 2 seats:

| config | mirror (`bench/v3.py`) W-L-T | mirror mean | meta W-L-T | meta mean |
| --- | --- | ---: | --- | ---: |
| S-on | 12W-4L-0T | +110 | 0W-16L-0T | -85,262 |
| T10-on | 0W-16L-0T | -32,475 | 0W-16L-0T | -103,761 |

The primary shipped reference is `-83,638` against the meta; the existing T10
reference is `-92,126`, and the best prior variant was `-78,439`. Sticky therefore
earns no default change. It wins the mirror panel at one quadrant but loses the
meta panel, so it is not a shipping candidate on both panels. `STICKY` remains
`False`.
