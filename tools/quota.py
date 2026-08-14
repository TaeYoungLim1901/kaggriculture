"""How many submissions are left today, without spending one to find out.

Kaggle's daily cap is 5 and resets at 00:00 UTC (09:00 KST). Failed submissions
count against it too -- refs 55487986 and 55488019 were both errors and both cost
a slot. The CLI only prints the remaining count as a side effect of submitting,
so count the submission list instead.
"""
from datetime import datetime, timezone, timedelta

LIMIT = 5
KST = timezone(timedelta(hours=9))

import kaggle
api = kaggle.KaggleApi()
api.authenticate()

subs = api.competition_submissions("kaggriculture")
today = datetime.now(timezone.utc).date()
used = [s for s in subs if s.date.replace(tzinfo=timezone.utc).date() == today]

reset = datetime.combine(today + timedelta(days=1), datetime.min.time(), timezone.utc)
print(f"used today (UTC {today}): {len(used)} of {LIMIT}   remaining: {LIMIT - len(used)}")
print(f"resets {reset.astimezone(KST):%Y-%m-%d %H:%M} KST "
      f"(in {str(reset - datetime.now(timezone.utc)).split('.')[0]})")
for s in used:
    print(f"  {s.date.replace(tzinfo=timezone.utc).astimezone(KST):%H:%M KST}  {s.ref}  "
          f"{s.status}  {s.description[:50]}")
