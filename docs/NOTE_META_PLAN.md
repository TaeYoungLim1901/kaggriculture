# V16-RC5 decoded plan

Source: `bench/v16_rc5_high_score_8c_4s_premium_market_.py`, reading its 720-entry `_ACTIONS`. Days and hours below are zero-based. Counts in the action tables are raw trace requests; the agent's weed-repair and premium-sell patches can change the executed action.

## Land and labour

| Action | Count / schedule |
| --- | --- |
| `BUY_LAND` | 2 quadrants: day 6 hour 16, day 10 hour 0 |
| Ownership | Starts with `NW`; ends with `NW`, `NE`, `SW` = 3 quadrants = 75 tiles |

| Day | Hires | Day | Hires | Day | Hires |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 5 | 10 | 14 | 20 | 14 |
| 1 | 1 | 11 | 10 | 21 | 12 |
| 2 | 2 | 12 | 10 | 22 | 10 |
| 3 | 3 | 13 | 8 | 23 | 14 |
| 4 | 4 | 14 | 9 | 24 | 11 |
| 5 | 3 | 15 | 9 | 25 | 12 |
| 6 | 4 | 16 | 13 | 26 | 12 |
| 7 | 7 | 17 | 9 | 27 | 11 |
| 8 | 6 | 18 | 11 | 28 | 10 |
| 9 | 7 | 19 | 13 | 29 | 10 |

Total `HIRE` requests: 264; average 8.8/day; peak 14/day.

## Animals and structures

| Market action | Schedule | Total |
| --- | --- | ---: |
| `BUY_ANIMAL COW` | day 0 hour 0: 1; day 5 hour 0: 1; day 6 hour 17: 2; day 7 hour 0: 2; day 8 hour 0: 2 | 8 |
| `BUY_ANIMAL SHEEP` | day 0 hour 0: 4 | 4 |

| Build action | Requests by day | Total |
| --- | --- | ---: |
| `BUILD_PASTURE` | day 0: 5; day 5: 1; day 6: 2; day 7: 2; day 8: 2; day 21: 1 | 13 |
| `BUILD_COOP` | none | 0 |

The final herd is 4 SHEEP + 8 COW. The replay leaves one additional empty pasture; 12 animal tiles are occupied.

## Crops

`PLANT` requests, including replant requests, are:

| Crop | Requests | Days and number planted |
| --- | ---: | --- |
| `MELON` | 19 | d0: 5; d10: 12; d11: 2 |
| `WHEAT` | 143 | d0: 5; d3: 1; d4: 5; d5: 1; d7: 4; d8: 8; d9: 1; d10: 1; d11: 4; d12: 8; d13: 1; d15: 4; d16: 8; d17: 1; d19: 7; d20: 14; d21: 10; d22: 3; d23: 18; d24: 12; d25: 13; d26: 14 |
| `STRAWBERRY` | 37 | d3: 3; d5: 4; d6: 2; d7: 10; d8: 2; d10: 11; d11: 5 |

The 37 strawberry requests create 35 live STRAWBERRY tiles at once in the seed-90001 episode. There is no strawberry replant wave: the last request is day 11, so replant frequency is zero. The ongoing crop's four-production death is followed by empty/weed space, not a replacement strawberry crop. Peak productive occupancy is 74 of the 75 owned tiles; during the 35-strawberry plateau it is 72 tiles (12 animals + 13 WHEAT + 12 MELON + 35 STRAWBERRY).

## Fertilizer

There are 72 `FERTILIZE` requests: d12: 3; d14: 4; d15: 1; d16: 13; d17: 2; d18: 4; d19: 12; d20: 13; d21: 2; d22: 2; d23: 11; d24: 3; d26: 2.

`FERTILIZE` carries no crop argument. Replaying the trace on seed 90001 maps 70 requests to STRAWBERRY and 2 to WEED/no-op tiles (day 16 and day 20). No fertilizer is spent on MELON or WHEAT. The plan spends fertilizer on ongoing STRAWBERRY rather than selling it.

## Selling

Each cell is `day=units@hours`; `20x2` means two sell orders at hour 20.

| Product | Total units | Per-day units and hours |
| --- | ---: | --- |
| `FERTILIZER` | 300 | d2=5@0; d3=5@0; d4=5@0; d5=5@0; d6=8@0,16; d7=3@7; d8=10@0,23; d9=10@0; d10=16@1; d11=12@12; d12=10@11; d13=16@4; d14=9@5; d15=4@5; d16=2@0; d17=21@3,14; d19=5@13x2; d21=17@2,23; d22=8@6; d23=6@6,19; d24=22@8,12,17,22; d25=15@0,8,17,20,22; d26=19@2,3,9,22; d27=23@0,1,14,18,21; d28=26@0,5,10,15,18,19,21; d29=18@0,5,18,22 |
| `MELON` | 126 | d10=39@12,15,17,20,22; d20=73@6,8,10,12,13,15,16,22,23; d21=14@0 |
| `MILK` | 320 | d9=3@17; d12=6@14; d13=7@18,23; d14=13@22; d15=21@1,2,17; d16=27@5,22; d17=10@22,23; d18=17@19,23; d19=3@14; d20=22@0,4,22; d21=20@9,15,19; d22=13@23; d23=20@1,3,7; d24=26@11,17,23; d25=12@18,21; d26=10@14; d27=28@0,17,18; d28=8@18; d29=54@6,7,19 |
| `STRAWBERRY` | 300 | d16=24@2,16,21; d17=2@15; d18=28@0; d19=28@16,23; d20=20@0; d21=32@0,18,23; d22=30@0; d23=37@0,23; d24=20@18; d25=30@9,15; d26=16@21; d27=11@3; d29=22@5 |
| `WHEAT` | 479 | d0=9@1; d6=17@6; d8=8@3,19; d9=7@6; d11=11@14; d12=15@15,20,21; d13=24@0; d16=5@21; d17=3@6; d18=4@17; d19=19@11; d20=9@0,11,23; d21=7@18; d22=13@7,15; d24=29@20,21; d25=34@8,9; d26=37@0,8; d27=12@20,23; d28=55@0,17,22; d29=161@0,17,19,20x2,21,22 |
| `WOOL` | 154 | d6=9@16; d7=17@0; d10=18@0; d15=16@1,20; d17=25@11,19; d18=12@21; d23=8@16; d24=8@7; d26=6@10; d27=27@13,21; d28=8@10 |

## Labour conversion

`Issued` counts all farmer/hand action slots, including `PASS`; `work` excludes `PASS`. Market orders are not included.

| Day | Issued | Work | Day | Issued | Work | Day | Issued | Work |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 139 | 91 | 10 | 339 | 318 | 20 | 339 | 334 |
| 1 | 47 | 32 | 11 | 253 | 248 | 21 | 294 | 290 |
| 2 | 70 | 54 | 12 | 252 | 247 | 22 | 251 | 243 |
| 3 | 91 | 73 | 13 | 207 | 199 | 23 | 339 | 325 |
| 4 | 115 | 85 | 14 | 228 | 218 | 24 | 273 | 269 |
| 5 | 93 | 88 | 15 | 230 | 226 | 25 | 293 | 289 |
| 6 | 99 | 99 | 16 | 316 | 305 | 26 | 294 | 285 |
| 7 | 185 | 184 | 17 | 228 | 220 | 27 | 272 | 263 |
| 8 | 162 | 159 | 18 | 272 | 264 | 28 | 249 | 227 |
| 9 | 185 | 171 | 19 | 316 | 311 | 29 | 242 | 232 |

## Episode cross-check

Running the trace agent by file path against `starter` for 720 steps at seed 90001 gives `$155,490` final money, `DONE`, and unlocked quadrants `NW`, `NE`, `SW`. The final herd is 4 SHEEP + 8 COW; the board reaches 74 productive tiles. Thus the two decoded `BUY_LAND` actions match the observed three-quadrant state. The exact money is environment-version/run dependent; this local run is the figure to use here.

## What our constants would have to be

| Constant | Trace mapping |
| --- | --- |
| `ANIMAL_PLAN` | `['SHEEP'] * 4 + ['COW'] * 8`; our shipped plan has 6 SHEEP + 8 COW |
| `CROP_PLAN` | No single static value reproduces the phase changes. Mid-season would be `[('MELON', 12), ('WHEAT', 13), ('STRAWBERRY', 35)]` = 60 crop tiles plus 12 animals; late season shifts to roughly `[('WHEAT', 46), ('STRAWBERRY', 18)]` plus 12 animals. Literal peaks are 12 MELON, 46 WHEAT, and 35 STRAWBERRY, but those peaks are not simultaneous. |
| `LAND_TARGET` | `3` (two purchases beyond the initial quadrant), not our `1` |
| `HIRES` | Not constant: 5--14/day, 264 total. A static approximation is `9`/day; the peak 14 requires phase-aware hiring, and our current `min(HIRES, 10)` cap cannot issue 14 in one hour. |
| fertilizer | Spend it on ongoing STRAWBERRY (`70` effective fertilizations); do not sell the animal fertilizer inventory by default. |

The key land comparison is 75 owned versus 74 productive at peak, not 3 versus 1 quadrants alone.
