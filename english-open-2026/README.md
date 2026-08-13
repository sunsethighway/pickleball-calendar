# English Open 2026 — squad fixtures

Fixtures for ten players at the Proflex English Open (Pickleball England / PickleBook),
14–16 August 2026, transcribed from the tournament's Schedule & Results screens.

## Files

| File | What it is |
|---|---|
| `fixtures.csv` | The source data — 64 unique matches, one row each |
| `build_sheet.py` | Builds the workbooks from the CSV |
| `english-open-2026.xlsx` | Compact workbook: Overview + one tab per day |
| `english-open-2026-full.xlsx` | Full workbook: the above plus By Player and a tab per player |

Rebuild both with:

```
pip install openpyxl
python build_sheet.py
```

## The data

`fixtures.csv` is keyed on PickleBook's match ID, so a match involving two tracked
players (James Davey and Daniel Greenhow's Saturday doubles, say) appears once
rather than twice. `our_players` names which of the ten are in that match.

Per-player counts reconcile exactly against the entry totals PickleBook showed on
each player's filtered view:

| Player | Matches | | Player | Matches |
|---|---|---|---|---|
| Ryan Kent | 12 | | Tracey-Anne Greenhow | 9 |
| Daniel Greenhow | 14 | | Holly Davey | 9 |
| James Davey | 14 | | Laura Kent | 8 |
| Will Cheeseman | 9 | | Jack Adams | 8 |
| Sophie Maitland | 8 | | Sonja Talbot | 8 |

Names follow PickleBook's registrations — note **Will** Cheeseman, and
Tracey-Anne under **Greenhow**.

## Caveats

- Transcribed from screenshots, not scraped. The counts above are the check that
  nothing was dropped, but individual court numbers and times are read by eye.
- Every source view had the Status filter set to `A`. If that is a status code
  rather than "All", fixtures in other states are not represented here.
- Match `#15652` (Sunday 14:40, Court 47) shows its opponents withdrawn.
- Times are scheduled starts. Tournament days drift; the venue board wins.
