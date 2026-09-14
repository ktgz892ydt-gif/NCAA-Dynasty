# NCAA Dynasty — Dynasty HQ

Static site for the **2026** season of an NCAA Football 26 online dynasty between
**Western Michigan**, **Eastern Michigan** and **Central Michigan**.

Live: https://ktgz892ydt-gif.github.io/NCAA-Dynasty/

Everything is one file, `index.html` — inline CSS and JS, hand-rolled SVG charts, no external
libraries or CDNs, no browser storage. It runs offline and can be hosted anywhere.

## What's on the page

| Tab | What it shows |
|---|---|
| **Dynasty** | The three schools side by side, then the workbook’s **110 stats** plus **estimated SOR**, grouped as on the Master tab, each with its **national rank** where one can be computed. |
| **Head-to-Head** | Any stat as a three-way bar chart, plus a radar profile across eight core measures. |
| **Schedules** | All 12 games per school: site, result, score, and each opponent's final record. |
| **National** | The full **143-team** ratings table (sortable, filterable) and national top tens. |
| **Leaders** | National player leaders in nine categories, from the screen recordings. |

## Mobile layout and measure explanations

Phone layouts use compact team cards, a search/group filter and three-column comparison rows
with the measure name above the school values. Wide national and player tables scroll within
their panels; their team/player column stays visible. Navigation, controls and explanation buttons
support touch and keyboard input.

Tap a measure marked ⓘ for its plain-language definition and interpretation. Explanations cover SRS,
SOS, estimated SOR, MOV, Pythagorean expected wins, Explosiveness Index, Ball Control Index, Pass-to-Run Yard
Ratio and Approximate Value. They are available on team cards, the comparison table and the
selected Head-to-Head measure; national rating headers keep explanation and sorting separate.
AV help appears only on the Approximate Value section header, not individual AV rows or the
Head-to-Head selection. Other data coverage notes open on tap; AV estimate markers remain visible.
Dialogs support Escape, a close button, backdrop dismissal
and focus return.

School accents use the same exact colors in light and dark themes: Western **#512C1D**,
Eastern **#0C5C30**, Central **#670231**. Text stays in the readable theme foreground, and chart
marks have outlines so the dark school colors remain distinguishable. No statistical data or
calculation inputs are changed by this interface update.

## Stat structure

Estimated SOR is added directly below SOS. The remaining Dynasty rows mirror the Master tab: the same 13 group titles, in the same order, with
attribute names copied verbatim — including the ones Master repeats inside a group ("Rate",
"Conversion %", "Yards"), which read unambiguously next to their neighbouring rows. Only the
stat dropdown qualifies them ("Rate (TD)", "Conversion % (3rd Down)"), since a dropdown has no
neighbours to give them context.

```
Results · Core Efficiency · Scoring and Posession · Passing · Rushing · Situational Offense
Scoring Defense · Passing Defense · Rush Defense · Disruptions · Situational Defense
Penalties · Totals (Special Teams)
```

**104 of the 110 rows are populated. 43 carry a national rank** — a rank is only shown where the
stat can be computed for the whole country from the national Team Stats screens; stats that come
from the per-game box scores exist for these three schools alone.

## Where the data comes from

The 2026 source set contains **297 photographs**, **14 screen recordings**, and the local
workbook. Retained workbook entries fill Eastern's missing first-game punts, returns and
possession; their provenance and remaining gaps are recorded in [source notes](data/SOURCE_NOTES.md).

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
| SOS (points) | -4.21 | -4.46 | -5.43 |
| SRS | +5.79 | −7.84 | +1.62 |
| National SRS rank | 46th | 98th | 62nd |

## About the ratings

SRS, Elo, Bradley-Terry and Glicko-2 are solved over the **entire 143-team national field**
(888 games, weeks 0–13), not just these three schools.

- **SOS** is the average opponent SRS, in points above/below the average team. Every scheduled game counts equally, including repeat opponents and synthetic FCS opponents. Positive is tougher and negative is easier. FBS national ranks exclude the five synthetic buckets. Full-precision SRS inputs are stored in `data/srs-2026.json`; `scripts/update_sos.py` updates the values, ranks and top ten together.
- **SRS** is points-based, uses home-field-adjusted margins, and is centred so the average team
  is 0.0.
- **Home-field advantage is +0.45 points**, from a team fixed-effect regression. The *raw*
  average home margin is +5.51, but that is badly biased: the FCS buckets play nearly all their
  games on the road and lose heavily. An independent Bradley-Terry fit agreed at roughly zero.
- **There are five FCS buckets, not four** — East, Midwest, Northwest, Southeast and West — all
  forced to `0-12` regardless of how many games they appear in.

## What is missing, and why

Only **6 of the 110 team rows** are blank, plus 23 of the 35 Approximate Value rows.
Eastern's punter AV is also blank in an otherwise populated row:

| Group | Attribute | Why |
|---|---|---|
| Results | Conference Champion, Bowl Result, Final CFP Ranking | User-entered in Master; no screen captures them |
| Disruptions | Tackles for Loss, Defensive Touchdowns | Need every defender on a team, and the leaderboards name no team |
| Totals (Special Teams) | TDs | Same: needs the team's returners identified |

Nine rows that looked unrecoverable were pulled out of the screen recordings instead (see
below): FGA, FGM, FG %, XPA, XPM, XP %, Explosiveness Index, Sacks and Sack Rate.

Two caveats on rows that *are* filled:

- **Total Touchdowns** counts offensive touchdowns only. The kicker identification does
  reveal how many non-offensive touchdowns each school scored — 0 for Western Michigan and
  2 each for Eastern and Central — but it cannot split those between defence and special teams.
- **Eastern Michigan** is missing the lower half of one box score. Season punts, return yards
  and possession now include the retained first-game workbook entries. Punt yards and yards/punt
  still cover eleven matching games and carry an `11g` marker. Explosiveness uses season inputs
  and estimated drives, marked `est.`. Qualifications also appear in Head-to-Head.

## Finding players the game will not name

The national leaderboards print no team beside a player, which is what blocked the
kicking, sacks and Approximate Value rows. The way round it is arithmetic: each school's
season totals are already known exactly, so the players can be picked out by identity.

- **Punter** — by exact punt count and yards. `R.Millmore` (26 for 1,121) is Western
  Michigan; `D.Duley` (36 for 1,623) is Central Michigan. Eastern Michigan's punter is not
  established by the available count-and-yardage evidence.
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

The local `AV_Calculations.md` defines the dynasty's model. The website computes the
following supported results and explicitly labels incomplete estimates:

- **Every team-level pool** — offence, O-line, skill, rush, pass, receiving, defence,
  front-7, secondary. These need only team stats plus the team's FGM/FGA, which the kicker
  identification supplies.
- **The offensive-line pool** is computed, but individual LT/LG/C/RG/RT slots remain blank
  until actual games played and starts for all participating linemen are available.
- **QB1**, from the passer's share of team passing yards plus the AY/A adjustment against a
  national baseline of 7.54 across 140 qualified passers.
- **K and P**, from the by-distance field-goal buckets and the punting line.

Still blank are the five linemen, RB1/RB2, WR1–3, TE1 and the twelve defensive slots. Those need per-player
production tied to a school, and no arithmetic identity pins them down the way a kicker's
point total or a punter's punt count does. Per-team roster or player-stat screens would
close it.

League baselines use the three schools for drive rates. Eastern's full-season punt count now
feeds the offensive baseline and every dependent offensive allocation. Defensive drives retain
estimated opponent field-goal attempts and incomplete Eastern opponent-punt coverage; Central's
takeaway screen also contains an unresolved discrepancy. Because that baseline is shared,
all three defensive pools and their front-seven/secondary allocations are marked `est.`.

The existing national kicking, punting and qualified-passer AY/A baselines are preserved.
Their full raw transcriptions are not included in the repository. See [source notes](data/SOURCE_NOTES.md)
for the distinction between verified corrections, retained transcriptions and estimates.

## Updating

For this source set, edit `data/verified-inputs-2026.json` when evidence changes, then run:

```sh
python3 -B scripts/update_sos.py
python3 -B scripts/update_sos.py --check
python3 -B scripts/test_sos.py
python3 -B scripts/update_sor.py
python3 -B scripts/update_sor.py --check
python3 -B scripts/test_sor.py
python3 scripts/reconcile_2026.py
python3 scripts/reconcile_2026.py --check
python3 -B scripts/test_reconciliation.py
```

This regenerates the audited fields in `DATA`, preserving unrelated data and ratings. It is a
targeted reconciliation, not a complete photo-import pipeline. Other new stats still require
updating the DATA object and recording their sources. Commit the changed files together.
Keep `index.html` at the repo root; the page remains self-contained and Pages serves the same URL.

When the scoreboard or SRS ratings change, refresh `data/srs-2026.json` from the ratings pipeline, including its scoreboard checksum, before rebuilding SOS. The SOS builder rejects stale or mismatched inputs. The local workbook/pipeline’s older record-based SOS is superseded on this website by the points-based calculation. Home-field adjustment is not added to SOS; it remains part of SRS.


## Estimated Strength of Record

SOR ranks all 138 FBS teams by how unlikely a shared reference team would be to match or exceed their actual win total on their actual played schedule. #1 is best. The benchmark is the mean full-precision SRS of the top 25 FBS teams (currently +18.8945), held constant across all schedules in this season snapshot. It is recalculated when the inputs change. Five synthetic FCS buckets supply opponent ratings but receive no SOR rank.

`scripts/update_sor.py` fits a no-intercept logistic win-probability curve to all 888 national results using the home-minus-away SRS difference plus the existing home-field adjustment (zero at neutral sites). The fitted slope is about 0.12863 per point. It substitutes the benchmark strength for each assessed team and combines that schedule’s win probabilities with an exact Poisson-binomial calculation, counting the probability of at least the actual number of wins. No random simulation is used. The [Poisson-binomial distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.poisson_binom.html) models sums of independent games with differing win probabilities.

All games count, including repeat opponents and synthetic FCS opponents. Actual played game counts handle 11-game schedules. Winless teams receive probability 1; tied probabilities share competition ranks (comparison rounded to 12 decimal places). Tied games are rejected pending a policy. Winning margins do not directly score résumé points, but final-season SRS inputs do reflect margins. The model assumes independent games and constant team strength.

The current in-sample Brier score is 0.16237; leaving each week out when fitting the slope gives 0.16273, versus 0.25 for a 50% baseline. These are fit diagnostics only: final-season SRS still includes every game, so this is **not independent forecast validation**. No historical seasons are available to assess predictive calibration. SOR is our retrospective estimate, not an official ranking. Exact parameters, probabilities and ranks for every eligible team are stored in `DATA.sorMethod` for reproducibility. Rebuild SOR after changing the scoreboard, SRS source or home-field parameter; stale source checks are reused from the SOS builder.
