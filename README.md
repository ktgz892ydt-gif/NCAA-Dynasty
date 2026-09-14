# NCAA Dynasty — Dynasty HQ

Static site for the **2026** season of an NCAA Football 26 online dynasty between
**Western Michigan**, **Eastern Michigan** and **Central Michigan**.

Live: https://ktgz892ydt-gif.github.io/NCAA-Dynasty/

Everything is one file, `index.html` — inline CSS and JS, hand-rolled SVG charts, no external
libraries or CDNs, no browser storage. It runs offline and can be hosted anywhere.

## What's on the page

| Tab | What it shows |
|---|---|
| **Dynasty** | The three schools side by side, then all **110 stats** grouped and named exactly as on the workbook's Master tab, each with its **national rank** where one can be computed. |
| **Head-to-Head** | Any stat as a three-way bar chart, plus a radar profile across eight core measures. |
| **Schedules** | All 12 games per school: site, result, score, and each opponent's final record. |
| **National** | The full **143-team** ratings table (sortable, filterable) and national top tens. |
| **Leaders** | National player leaders in nine categories, from the screen recordings. |

## Stat structure

The Dynasty tab mirrors the Master tab: the same 13 group titles, in the same order, with
attribute names copied verbatim — including the ones Master repeats inside a group ("Rate",
"Conversion %", "Yards"), which read unambiguously next to their neighbouring rows. Only the
stat dropdown qualifies them ("Rate (TD)", "Conversion % (3rd Down)"), since a dropdown has no
neighbours to give them context.

```
Results · Core Efficiency · Scoring and Posession · Passing · Rushing · Situational Offense
Scoring Defense · Passing Defense · Rush Defense · Disruptions · Situational Defense
Penalties · Totals (Special Teams)
```

**95 of the 110 rows are populated. 42 carry a national rank** — a rank is only shown where the
stat can be computed for the whole country from the national Team Stats screens; stats that come
from the per-game box scores exist for these three schools alone.

## Where the data comes from

Every number is the 2026 season, transcribed from **297 photographs** of the in-game screens and
**14 screen recordings**.

```text
in-game photos + screen recordings
  → workbook tabs: League Scores (one row per national game) and Game Log (per-game box scores)
  → Scripts/codex/calculate_ratings.py   → SOS, SRS, Elo, Bradley-Terry, Glicko-2
  → the DATA object baked into index.html
  → commit (GitHub Pages redeploys automatically)
```

### Three sources that agree

The national scoreboard, the per-game box scores, and the game's own season Team Stats screens
independently produce the **same** points for and against:

| | Western Michigan | Eastern Michigan | Central Michigan |
|---|---|---|---|
| Record | 9-3 | 4-8 | 10-2 |
| Points for / against | 368 / 248 | 190 / 231 | 309 / 224 |
| MOV | +10.0 | −3.4 | +7.1 |
| SOS | .475 | .497 | .507 |
| SRS | +5.79 | −7.84 | +1.62 |
| National SRS rank | 46th | 98th | 62nd |

## About the ratings

SOS, SRS, Elo, Bradley-Terry and Glicko-2 are solved over the **entire 143-team national field**
(888 games, weeks 0–13), not just these three schools.

- **SRS** is points-based, uses home-field-adjusted margins, and is centred so the average team
  is 0.0.
- **Home-field advantage is +0.45 points**, from a team fixed-effect regression. The *raw*
  average home margin is +5.51, but that is badly biased: the FCS buckets play nearly all their
  games on the road and lose heavily. An independent Bradley-Terry fit agreed at roughly zero.
- **There are five FCS buckets, not four** — East, Midwest, Northwest, Southeast and West — all
  forced to `0-12` regardless of how many games they appear in.

## The 15 blank rows

These show as "—" because the screenshots do not contain them, not because they are zero:

| Group | Attribute | Why |
|---|---|---|
| Results | Conference Champion, Bowl Result, Final CFP Ranking | User-entered in Master; no screen captures them |
| Core Efficiency | Explosiveness Index | Its drive estimate needs FGA, which was never captured |
| Passing | Sacks, Sack Rate | Sacks *taken* appear on no captured screen |
| Disruptions | Tackles for Loss, Defensive Touchdowns | Only on per-game defensive player screens, not shot this season |
| Totals (Special Teams) | FGA, FGM, FG %, XPA, XPM, XP %, TDs | Kicking is only on the per-game kicking screen, not shot this season |

Two caveats on rows that *are* filled:

- **Total Touchdowns** counts offensive touchdowns only (passing + rushing), because defensive
  and special-teams touchdowns were never captured.
- **Totals (Special Teams) → Yards** is punts × the displayed average, summed per game, so it
  carries a little rounding from the one-decimal average on screen.

## Not built: Position Breakdown / Approximate Value

Master rows 113–147 (the per-position AV model — LT through P) are not on the site. They need
per-player stats attributed to a school, and the player leaderboards in the recordings are
national: the game prints a team only for the one highlighted row. Capturing per-team roster or
player-stat screens would make this possible.

## Updating

Rebuild the `DATA` object and commit `index.html`. Keep the filename exactly `index.html` at the
repo root so Pages serves it at the root URL; Pages rebuilds on every commit and the shared link
does not change.
