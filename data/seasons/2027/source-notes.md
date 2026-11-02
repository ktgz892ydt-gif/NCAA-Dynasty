# 2027 source notes

Status: **finalized for local publication, with documented source limits**. Reviewed November 2, 2026. The season label is the in-game year.

The working dataset covers the 12-game regular season. It does not include conference championships or Central Michigan–Tennessee in records, ratings, scoring totals, or statistical totals. The four additional recordings now support individual postseason deductions. The last team box is supplied by two images. Unrecoverable source fields remain explicitly blank or excluded; the user-authorized J. Taylor split is labeled an estimate.

## Source inventory

The original files are in the local `2027` folder. `inputs/video-manifest.json` records their filenames and durations.

| Recording | Content |
| --- | --- |
| IMG_5597 | Brief Western Michigan passing screen |
| IMG_5598–5600 | Western, Central, and Eastern Michigan player statistics |
| IMG_5601–5603 | National team offense, defense, conversions, red-zone efficiency, penalties, and turnovers |
| IMG_5604–5612 | National player passing, rushing, receiving, blocking, defense, kicking, punting, kick returns, and punt returns |
| IMG_5613 | National regular-season results, weeks 0–14 |
| IMG_5614 | Ten conference championship results and nine distinct team box scores |
| IMG_5615 | Central Michigan–Tennessee team box score |
| IMG_5616–5618 | Western, Central, and Eastern Michigan regular-season schedules and team box scores |
| Additional Items/IMG_5620 | Liberty–Western Kentucky individual championship statistics |
| Additional Items/IMG_5621 | Fresno State–Washington State individual championship statistics |
| Additional Items/IMG_5622 | Individual statistics for the other eight championships |
| Additional Items/IMG_5623 | Central Michigan–Tennessee individual statistics |
| Additional Items/IMG_5624–5625.HEIC | Arkansas State–Coastal Carolina upper/lower championship team box |

The two photographs complete the Arkansas State–Coastal Carolina team box omitted from the earlier recordings. Both red-zone lines show 4 TD, 1 FG, and 83%, identifying six attempts. Punting totals match the individual video: Arkansas State 6/215 and Coastal Carolina 6/273. `inputs/photo-manifest.json` retains the image filenames and hashes.

## Regular-season boundary

The scoreboard contains **842 games and 143 rated teams**: 138 real teams with exactly 12 games each, plus five synthetic FCS buckets. Each real team appears at most once per week. The historical `legacy-0-12` policy is retained for synthetic FCS displayed records; their recorded appearances are not 12 individual games each.

| Team | Record | Points scored | Points allowed |
| --- | --- | ---: | ---: |
| Western Michigan | 11–1 | 380 | 193 |
| Eastern Michigan | 4–8 | 202 | 227 |
| Central Michigan | 11–1 | 396 | 142 |

These are regular-season results. In particular, Central's 52–7 regular-season win over Western remains, while its 20–18 championship win is excluded.

The following 11 games are excluded. Their recorded team statistics are subtracted from affected aggregate screens where available.

| Game | Result |
| --- | --- |
| Liberty–Western Kentucky | 31–25 |
| Washington State–Fresno State | 27–24 |
| Air Force–North Dakota State | 25–23, OT |
| Louisville–Miami | 13–49 |
| Kansas State–TCU | 23–25 |
| Western Michigan–Central Michigan | 18–20 |
| Arkansas State–Coastal Carolina | 44–38, OT |
| Memphis–UAB | 35–24 |
| Texas A&M–LSU | 28–35 |
| Michigan–Nebraska | 21–38 |
| Central Michigan–Tennessee | 17–37 |

Western's aggregate screens cover 13 games, Central's 14, and Eastern's 12. The other championship participants and Tennessee have one excluded game each.

## Reconciliation method

1. Keep captured team/player screens and normalized box scores as separate source inputs. The captured national and postseason player transcriptions are retained alongside the dynasty team captures. OCR observations and enlarged review frames remain in the local Review folder.
2. Subtract additive game counts, yardage, touchdowns, first downs, conversions, red-zone counts, penalties, and turnovers when the relevant box-score field is available. Recompute all percentages and averages from the remaining counts.
3. Use the regular-season scoreboard for wins, losses, points, margins, and all rating systems. Never change a 13- or 14-game total by merely dividing it by 12.
4. Supplement the three dynasty teams with their 12 regular-season box scores for carries, possession time, return yardage, and available opponent statistics.
5. Use the sole active passer's season totals less postseason passing lines for dynasty completions, attempts, and interceptions. Use the sole active punter's totals less postseason punt lines for punt count and yardage. These limited player assignments are supported by the full team player recordings.
6. Leave unrecoverable values null. All 11 excluded games now have team boxes, including Arkansas State–Coastal Carolina. Their team contributions are subtracted before national rankings are calculated. Defensive sacks are reconstructed by subtracting the opposing postseason passers’ recorded sacks taken.
7. Calculate national rankings only among teams with a known regular-season value for that measure. The denominator and coverage note identify that population; it can be less than 138. Rates from the mixed-cutoff screens are not carried into the regular-season rankings.

The adjustment audit is in `inputs/postseason-adjustments.json`. Per-team totals, including competing box-score sums, are in `inputs/dynasty-reconciliation.json`. Manual scoreboard readings and box corrections retain timestamps in `inputs/scoreboard-source-review.json` and `inputs/box-score-corrections.json`.

The player tables contain **a captured regular-season subset**, not a complete national ranking. Repeated season observations are consolidated, arithmetic conflicts are excluded, and national rows are checked against all recorded postseason rosters, including GENERAL participation. A unique roster/category match and matching 13/14-game cutoff support affected national-player deductions. Players with twelve or fewer appearances and possible postseason roster matches are withheld unless independently identified in a dynasty team recording. Abbreviated-name collisions, missing primary counts, and insufficient observations are listed in `inputs/player-withheld-rows.json`.

All three dynasty teams' passing, rushing, and receiving totals are reconstructed, including negative regular-season rushing yardage where subtraction requires it. Player GP remains actual appearances: Western kicker N. Hancock has **11 regular-season appearances**, although his original screen showed 12 including the championship. A postseason zero snap count establishes nonparticipation; a missing name alone does not. The recorded tackle-sorted and sacks-allowed lists reach zero, establishing zero for omitted players in those nonnegative measures. Unknown maxima remain null when a postseason play ties or exceeds the captured season maximum.

`inputs/player-postseason-adjustments.json` retains field-level deductions. `inputs/postseason-player-source-review.json` records manual readings, roster spelling corrections, arithmetic implications, and same-name rows kept separate. `inputs/regular-player-population.json` retains the regular counts before presentation columns are selected.

## Source discrepancies and limits

- **National points:** Pittsburgh's scoreboard points allowed are 262 versus 268 on the defense screen. Wisconsin's scoreboard points scored are 294 versus 300 on the offense screen. Kent State's scoreboard points allowed are 252 versus 258 on the defense screen. The scoreboard governs. Wisconsin's 24–17 overtime win at UCLA was checked on readable frames; it is not changed to force agreement.
- **Central postseason passing:** A. Sheppard’s individual championship line is 12/15, whereas the team box shows 14/15. His Tennessee line is 19/26, versus 20/26 in the team box. Receiving totals confirm 12 and 19. Regular-season passing is therefore **181/247**, with 1,891 yards, 23 TD, and 6 INT.
- **Passing counts:** several regular-season boxes show internally impossible completion/attempt relationships. Dynasty passer season totals take precedence for offensive passing counts. Opponent completion-dependent metrics still come from those boxes and are marked provisional estimates.
- **Eastern interceptions:** B. Barnett's passing screen shows 10; team turnovers and the regular boxes indicate 11 interceptions thrown. His individual passing line and passing-efficiency measures use 10; team giveaways retain the displayed total of 13. These sources are not silently forced to reconcile.
- **Eastern plays:** the regular boxes sum to 257 attempts and 520 plays; the passer screen shows 255 attempts. With 263 recorded carries, the team uses 518 plays for derived offensive rates.
- **Eastern receiving:** captured receptions total 150 while the passer screen shows 149 completions; both yield 1,341 yards. The independent captured lines are retained pending resolution.
- **Eastern recoveries:** the team defense screen reports three recoveries but the 12 boxes show five opponent fumbles lost. The team uses five recoveries and ten takeaways, consistent with five interceptions. This does not revise individual defensive player rows.
- **Central punting:** corrected regular boxes sum to 1,054 punt yards. The full punter screen less postseason gives 1,050 (1,312 − 144 − 118), which governs the team and player totals. The four-yard difference remains documented.
- **Missing fields:** Iowa/UNLV penalty fields and UNLV turnover fields are incomplete in the capture. Other unreadable fields stay absent. No unreadable zero is silently filled. Toledo's nine first downs against Western were read manually from the highlighted row at IMG_5616, 112 seconds.
- **Same-name defenders:** Central has J. Taylor at WILL and FS. Championship tackle lines are 6 and 3; Tennessee lines are 8 and 7. The player cards never identify which belongs to which position. At the user’s request, each receives half of each game line: 4.5 championship tackles and 7.5 Tennessee tackles, with the corresponding solo/assisted tackle and TFL splits. Both individual rows are labeled **estimated split**. The team aggregates remain exact. The explicit authorization is retained in `inputs/player-estimate-policy.json`.
- **Arkansas State championship rushing:** the team box shows 30 carries, 110 yards, 4 TD. Captured individual rows total 29 carries, 110 yards, 3 TD; the residual one-carry, zero-yard touchdown is not assigned to a guessed player. Team deductions use the photographed team line. National players without an identifiable individual postseason line remain excluded.
- **Negative postseason rushers:** Fresno State, Washington State, North Dakota State, Kansas State, and TCU rushing screens stop among zero-yard players before the negative-yard rows. Team boxes provide aggregate deductions, but residual negative yardage is never assigned to a guessed player.
- **Central defensive sacks:** individual season half-sacks sum to 33.5; the team screen shows 33. Team rankings use the team source, yielding 31 after two postseason sacks are removed. Individual half-sacks retain their separate source.
- **Memphis/UAB:** a readable team-box frame and the individual lines confirm 59 Memphis kick-return yards and 214 UAB punt yards (5 × 42.8). These correct the initial OCR normalization.
- **Player coverage:** schools are attached only where the captured team evidence and cutoff identify them. National lists are capped/partially captured, and ambiguous records are excluded. Season-long maxima are never subtracted.
- **AV:** 2027 uses the existing estimated-drive method and three-dynasty-team offensive/defensive baselines. AY/A, kicking-distance, and punting baselines are recomputed from the available regular-season player population; their exact members and counts are retained in `inputs/av-baseline-players.json` and `inputs/av-notes.json`. They are explicitly a captured subset, not a complete national population. AV values are marked estimates. Specialist formulas use actual regular-season appearances. Individual lineman/receiver/defender AV is not invented from GP or snaps because starts are unavailable.
- **Model scope:** ratings use the existing v1 methods and a 2,160-second regulation game. They describe this regular-season schedule. The 2026 dataset and publication manifest remain unchanged.

## Rebuild and verify

Use the pinned NumPy version from `requirements.txt` for the archived rating checks.

```sh
python3 -B scripts/prepare_2027_players.py
python3 -B scripts/prepare_2027.py
python3 -B scripts/build_season.py --season 2027
python3 -B scripts/prepare_2027.py --check
python3 -B scripts/build_season.py --season 2027 --check
python3 -B scripts/validate_season.py --season 2027
python3 -B -m unittest discover -s scripts -p 'test_*.py'
python3 -B scripts/preview.py --season 2027 --port 8765
```

2027 is finalized in the local publication manifest and is the default season. Run `python3 -B scripts/preview.py --port 8765` to view the normal two-season site. The rebuild commands do not commit, push, or deploy changes. `pending-capture.md` records the closed capture requests and remaining documented source limitations.
