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

## What is missing, and why

Only **6 of the 110 team rows** are blank, plus 18 of the 35 Approximate Value slots:

| Group | Attribute | Why |
|---|---|---|
| Results | Conference Champion, Bowl Result, Final CFP Ranking | User-entered in Master; no screen captures them |
| Disruptions | Tackles for Loss, Defensive Touchdowns | Need every defender on a team, and the leaderboards name no team |
| Totals (Special Teams) | TDs | Same: needs the team's returners identified |

Four rows that looked unrecoverable were recovered from the screen recordings instead
(see below): FGA, FGM, FG %, XPA, XPM, XP %, Explosiveness Index, Sacks and Sack Rate.

Two caveats on rows that *are* filled:

- **Total Touchdowns** counts offensive touchdowns only. The kicker identification does
  reveal how many non-offensive touchdowns each school scored — 0 for Western Michigan and
  2 each for Eastern and Central — but it cannot split those between defence and special teams.
- **Eastern Michigan** is missing the lower half of one box score, so their kick return yards,
  punt return yards, punts, punt yards and Explosiveness Index rest on eleven games. Those
  cells carry an `11g` marker on the page.

## Finding players the game will not name

The national leaderboards print no team beside a player, which is what blocked the
kicking, sacks and Approximate Value rows. The way round it is arithmetic: each school's
season totals are already known exactly, so the players can be picked out by identity.

- **Punter** — by exact punt count and yards. `R.Millmore` (26 for 1,121) is Western
  Michigan; `D.Duley` (36 for 1,623) is Central Michigan. Eastern Michigan's punter falls
  below the captured range.
- **Quarterback** — by attempts and passing yards. Touchdowns and interceptions then match
  the team totals too, four confirmations each: `B.Lowry`; `N.Kim` + `J.Stuckey`;
  `A.Flores` + `M.Beamon`.
- **Kicker** — by the only field-goal and extra-point line that reproduces the team's point
  total through `Points = 6*TD + XPM + 3*FGM + 2*TwoPtMade`. `P.Domschke` (368),
  `R.Kessinger` (190), `J.London` (309).

This also corrected a real error: summing completions off the box scores gave Central
Michigan an 85.1% completion rate, higher than any passer in the country, and one box score
printed more completions than attempts. The leaderboard's figures replaced them.

## Approximate Value

`AV_Calculations.md` says AV "cannot be computed from the team Game Log alone". Most of it
now is:

- **Every team-level pool** — offence, O-line, skill, rush, pass, receiving, defence,
  front-7, secondary. These need only team stats plus the team's FGM/FGA, which the kicker
  identification supplies.
- **The five offensive-line slots.** Their formula is `GP + 5*GS*PosMult`, so for a line
  that started all twelve games it reduces to the position multipliers alone — tackles take
  21.88% of the line pool each, interior linemen 18.75%.
- **QB1**, from the passer's share of team passing yards plus the AY/A adjustment against a
  national baseline of 7.54 across 140 qualified passers.
- **K and P**, from the by-distance field-goal buckets and the punting line.

Still blank are RB1/RB2, WR1–3, TE1 and the twelve defensive slots. Those need per-player
production tied to a school, and no arithmetic identity pins them down the way a kicker's
point total or a punter's punt count does. Per-team roster or player-stat screens would
close it.

League baselines use the three schools for the drive rates, which is one of the two options
`AV_Calculations.md` leaves open; the kicking, punting and AY/A baselines are genuine
national averages taken off the leaderboards. Defensive drives rely on an estimate of
opponent field-goal attempts, which the doc explicitly permits approximating.

## Updating

Rebuild the `DATA` object and commit `index.html`. Keep the filename exactly `index.html` at the
repo root so Pages serves it at the root URL; Pages rebuilds on every commit and the shared link
does not change.
