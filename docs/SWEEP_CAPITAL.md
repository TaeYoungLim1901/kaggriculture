# SWEEP_CAPITAL — does a capital reserve unblock expansion? (2026-08-14)

Answers the live question left open in `docs/META.md` §6 item 0.

Panel: `tools/sweep.py`, `--opp bench/v3.py` (a byte copy of the shipped build), 8 seeds × 2 seats,
`--seed0 90001`, 720 steps. A W-L record here reads directly as "better or worse than what we ship".

Knobs added to `main.py`, both defaulted to the shipped behaviour:

- `ANIMAL_RESERVE = 0` — hold cash for the next N animals still waiting on a structure, before the
  `BUY_SEED` / `BUY_LAND` branches can spend it.
- `PLANT_CAP = False` — cap PLANT tasks at seeds actually on hand (the companion to the reserve).

`EXPAND` below means `LAND_TARGET = 2` plus `CROP_PLAN = [(MELON,4), (WHEAT,6), (STRAWBERRY,20)]`.

| config | change | W-L-T | mean margin |
| --- | --- | --- | --- |
| X0 | EXPAND only | 0W-16L | −34,179 |
| X1 | EXPAND + reserve 1 | 0W-16L | −19,705 |
| X1c | EXPAND + reserve 1 + plant cap | 0W-16L | −19,762 |
| X2c | EXPAND + reserve 2 + plant cap | 0W-16L | −18,038 |
| **X3c** | EXPAND + reserve 3 + plant cap | 0W-16L | **−13,854** |
| X6c / X14c / X14 | EXPAND + reserve 6 / 14 / 14-no-cap | 0W-16L | −50,804 |
| S12c | 2 quadrants, 12 strawberry, reserve 3 + cap | 0W-16L | −9,455 |
| S6c | 2 quadrants, 6 strawberry, reserve 3 + cap | 0W-16L | −6,943 |
| **M12c** | 2 quadrants, 12 melon, no berries, reserve 3 + cap | **4W-12L** | **−1,956** |
| M12c-H10 / -H12 | M12c + 10 / 12 hands | 0W-16L | −23,250 |
| S6c-H12 | S6c + 12 hands | 0W-16L | −9,530 |
| R2c | current 25 tiles + reserve 2 + cap (no expansion) | 0W-16L | −2,730 |

## 1. The reserve works, and it is not enough

`tools/buildprobe.py`, seed 90001:

| | first `BUY_ANIMAL` | first `BUY_LAND` | money, days 0–9 |
| --- | --- | --- | --- |
| shipped `main.py` | day 0 | never | 116–862 |
| X0 (expansion, no reserve) | **day 10** | day 0 | 124–366 |
| X3c (expansion + reserve 3) | **day 0** | day 15 | 124–967 |

The diagnosed defect is fixed: with a reserve the herd is bought on schedule and land waits until
day 15. Expansion's loss drops from −34k to −14k. It still loses every game.

## 2. What is actually left — labour spent walking, not capital

`tools/sellprofile.py --me .sweep/X3c.py --opp bench/v3.py --seed 90001`:

| product | X3c (expanded) | v3 (shipped) |
| --- | --- | --- |
| STRAWBERRY | 46 @ $238 = $10,966 | 0 |
| MILK | 129 @ $112 = $14,393 | 165 @ $146 = **$24,076** |
| FERTILIZER | 165 = $8,468 | 303 = **$15,853** |
| MELON | 33 = $8,115 | 48 = $11,750 |

The berries earn $11.0k and the herd loses $17.2k of milk and fertilizer. 20 tiles produced only 46
berries in 30 days. Every crop line drops, not just the animals — the second quadrant does not add
work capacity, it adds **distance**. The 58% PASS rate is not free capacity waiting to be used; the
units convert it into travel steps the moment tiles are further apart.

That is why the loss is monotone in tiles added, at fixed capital: berries 20 ⇒ −13.9k, 12 ⇒ −9.5k,
6 ⇒ −6.9k, none (12 melon) ⇒ −2.0k. Zero extra tiles is the optimum of that family, which is the
shipped build.

More hands does not buy the distance back (−1,956 ⇒ −23,250 at 10 hands). Note `main.py` emits
`[["HIRE"]] * min(HIRES, 10)` — the market takes 10 order slots, so `HIRES` above 10 is a no-op and
H10 and H12 are the same agent. The 10-hand run also fills every slot at hour 0, evicting the wheat
and animal purchases that share it.

## 3. Verdict

- Ship nothing from this panel. `main.py` keeps `ANIMAL_RESERVE = 0`, `PLANT_CAP = False`.
- **Do not retry land expansion behind a capital fix.** It has now been measured with the capital
  defect removed, and the answer is still no at every crop size.
- The remaining expansion blocker is **travel cost per task**, not money and not hand count. Only a
  routing change (locality-aware assignment, or units homed per quadrant) can move it. Until such a
  change exists and is measured on one quadrant, more land is a tax.
- The reserve knob stays in the tree at its default so this panel can be re-run in a minute
  (`python tools/sweep.py all`); it was reimplemented from scratch twice before it was measured.
