# NCAA Dynasty — Dynasty HQ

Static site for the **2026** season of an NCAA Football 26 online dynasty played by
**Alex (W. Michigan)**, **Blake (E. Michigan)** and **Nick (C. Michigan)**.

Live: https://ktgz892ydt-gif.github.io/NCAA-Dynasty/

Everything is one file, `index.html` — inline CSS and JS, hand-rolled SVG charts, no external
libraries or CDNs, no browser storage. It runs offline and can be hosted anywhere.

## What's on the page

| Tab | What it shows |
|---|---|
| **Dynasty** | The three teams side by side — record, scoring, margin, SRS — then all 70 stats, each with the team's **national rank**. |
| **Head-to-Head** | Any stat as a three-way bar chart, plus a radar "team profile" across eight core measures. |
| **Schedules** | All 12 games per team: site, result, score, and each opponent's final record. |
| **National** | The full **143-team** ratings table (sortable, filterable) and national top tens. |
| **Leaders** | National player leaders by category, read from the screen recordings. |

## Where the data comes from

Every number is the 2026 season, transcribed from **297 photographs** of the in-game screens and
**14 screen recordings**. Nothing is carried over from any earlier snapshot.

```text
in-game photos + screen recordings
  → workbook tabs: League Scores (one row per national game) and Game Log (per-game box scores)
  → Scripts/codex/calculate_ratings.py   → SOS, SRS, Elo, Bradley-Terry, Glicko-2
  → the DATA object baked into index.html
  → commit (GitHub Pages redeploys automatically)
```

The workbook and the instruction docs live outside this repo, in the Dynasty folder;
`Rating_Methodology.md` there is the spec for the ratings.

### Three sources that agree

The season was cross-checked rather than taken on trust. The national scoreboard, the per-game
box scores, and the game's own season Team Stats screens independently produce the **same**
points for and against for all three teams:

| | Alex · W. Michigan | Blake · E. Michigan | Nick · C. Michigan |
|---|---|---|---|
| Record | 9-3 | 4-8 | 10-2 |
| Points for / against | 368 / 248 | 190 / 231 | 309 / 224 |
| Margin of victory | +10.0 | −3.4 | +7.1 |
| Strength of schedule | .475 | .497 | .507 |
| SRS | +5.79 | −7.84 | +1.62 |
| National SRS rank | 46th | 98th | 62nd |

## About the ratings

SOS, SRS, Elo, Bradley-Terry and Glicko-2 are solved over the **entire 143-team national field**
(888 games, weeks 0–13), not just these three teams — which is the whole reason the League Scores
tab captures the full country.

- **SRS** is points-based, uses home-field-adjusted margins, and is centred so the average team
  is 0.0. It is not the win%-based SOS added to margin of victory; that would mix units.
- **Home-field advantage is +0.45 points**, from a team fixed-effect regression. The *raw*
  average home margin is +5.51, but that is badly biased: the FCS buckets play nearly all their
  games on the road and lose heavily. An independent Bradley-Terry fit agreed at roughly zero.
- **There are five FCS buckets, not four** — East, Midwest, Northwest, Southeast and West. All
  five are forced to `0-12` regardless of how many games they actually appear in. They do
  occasionally win (nine times in 2026); those wins are discarded from the bucket's own record
  while the real opponent keeps the loss.

## Not captured this season

These show as "—" rather than zero, because they were never photographed:

**Tackles, tackles for loss, defensive touchdowns, special-teams touchdowns, sacks allowed, and
all kicking (FG attempts/made, XP attempts/made).** Field goals and extra points only appear on
the per-game kicking screens, which weren't shot this season.

Player leaderboards show no team next to each row — the game only prints a team for the
highlighted player — so league leaders cannot be attributed to a school.

## Updating

Rebuild the `DATA` object and commit `index.html`. Keep the filename exactly `index.html` at the
repo root so Pages serves it at the root URL; Pages rebuilds on every commit and the shared link
does not change.
