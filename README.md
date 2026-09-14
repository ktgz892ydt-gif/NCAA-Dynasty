# NCAA Dynasty — Dynasty HQ

Static site for an NCAA Football 26 online dynasty played by **Alex**, **Blake** and **Nick**.
Published with GitHub Pages: https://ktgz892ydt-gif.github.io/NCAA-Dynasty/

Everything lives in one file, `index.html` — inline CSS and JS, hand-rolled SVG charts,
no external libraries or CDNs, no browser storage. It runs offline and can be hosted anywhere.

## What the site shows

Three tabs — **Standings**, **Head-to-Head** and **Trends** — over 73 stats grouped into
Overall, Offense, Defense, Special Teams, Red Zone, Turnovers and Post Season, for the
seasons 2024, 2026, 2027 and 2028 plus a Career roll-up. (2025 has no data and is omitted.)

Coaches change schools between seasons, so school names are per-season: `DATA.schoolsBySeason`
maps a season to each player's school, falling back to the flat `DATA.schools` map for seasons
that have not been verified. In **2026** the three are W. Michigan (Alex), E. Michigan (Blake)
and C. Michigan (Nick).

## Where the data comes from

The numbers are a baked-in snapshot in the `const DATA = { … }` object inside `index.html`.
They are not live-linked to anything. The 2026 season was built from in-game screenshots:

```text
photographs of the in-game screens
  → transcribed into the workbook (Game Log + League Scores tabs)
  → Scripts/codex/calculate_ratings.py   (SOS, SRS, Elo, Bradley-Terry, Glicko-2)
  → the DATA object in index.html
  → commit (GitHub Pages redeploys automatically)
```

The workbook and the transcription/instruction docs live outside this repo, in the
Dynasty folder. `Rating_Methodology.md` there is the spec for the ratings; the
**League Scores** tab holds one row per national-scoreboard game for the whole country,
which is what makes strength of schedule computable.

## 2026 at a glance

| | Alex · W. Michigan | Blake · E. Michigan | Nick · C. Michigan |
|---|---|---|---|
| Record | 9-3 | 4-8 | 10-2 |
| Points for / against | 368 / 248 | 190 / 231 | 309 / 224 |
| Margin of victory | +10.0 | −3.4 | +7.1 |
| Strength of schedule | .475 | .497 | .507 |
| SRS (points, field average 0) | +5.79 | −7.84 | +1.62 |

SRS, SOS and margin of victory are computed across the **full 143-team national field**
(888 games, weeks 0–13), not just these three teams.

## Known gaps in 2026

These show as "—" because the screenshot set does not contain them:

- **Tackles, tackles for loss, defensive touchdowns, special-teams touchdowns, sacks allowed.**
- **Kicking — FG attempts/made/%, XP made/%.** Field goals and extra points are only in the
  per-game kicking screens, which were not captured this season.
- **Season Rating** — no formula for it exists in any of the source documents.

Career figures for a few rate stats (yards per play, yards per carry, 3rd/4th down %,
XP %, yards per punt) are carried over from the previous snapshot: their underlying
components are not part of the 73-stat model, so they cannot be recomputed here.

## Updating

Regenerate the `DATA` object and commit `index.html`. Keep the filename exactly
`index.html` at the repo root so Pages serves it at the root URL. Pages rebuilds on
every commit; the shared link does not change.
