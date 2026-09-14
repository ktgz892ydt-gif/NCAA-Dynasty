# 2026 source reconciliation

Reviewed against the local Dynasty Folder photographs, recordings and workbook. The original media remain local; this repository records the numeric corrections and their provenance.

## Corrections

| Field | Source | Reconciled value |
| --- | --- | --- |
| Eastern Sacramento State punts | Game Log!BK17 | 4 |
| Eastern Sacramento State kick-return yards | Game Log!BJ17 | 58 |
| Eastern Sacramento State punt-return yards | Game Log!BM17 | 11 |
| Eastern Sacramento State possession | Game Log!Q17 | 15:05 |
| Western punter R. Millmore | IMG_5220.MOV, about 33.5 s | 26 punts, 1,121 yards, 0 blocked |
| Central punter D. Duley | IMG_5220.MOV, about 33.5 s | 36 punts, 1,623 yards, 0 blocked |

Eastern's first-game entries are retained workbook transcriptions. The current folder lacks the lower box-score screen for that game, so their provenance is disclosed rather than described as freshly verified photo values. Adding them to the eleven photographed games gives **25 punts, 937 kick-return yards, 269 punt-return yards and 11,715 seconds of possession**. Possession/game is 976.25 seconds. Its punt yardage remains **969 yards over 21 punts in 11 games**; 969 must not be divided by the full-season 25 punts.

The full-season punt count gives Eastern offensive points/drive of **176/88 = 2**. Recomputing the three-team baseline gives offensive AV pools of **125.282167 Western, 73.814898 Eastern and 100.902935 Central**. The dependent line, skill, rushing, passing, receiving and quarterback values are regenerated together. Eastern's Explosiveness Index becomes **8.512**, using the existing rounded team YPP and the documented estimated-drive formula.

The passing footage supports keeping the corrected quarterback-room totals already in the site: Eastern 175 completions on 311 attempts and Central 205 on 302. Passing ratings use those leaderboard season figures, not the inconsistent per-game completion transcriptions. Sacks-taken rates use sacks divided by attempts plus sacks.

## Estimates and unresolved sources

- **Defensive AV is provisional.** Opponent FGA is estimated. Eastern's opponent punts cover only 11 games, and Central's takeaway screen is internally inconsistent. These affect the shared defensive baseline, so all three teams' defensive pools and their front-seven/secondary allocations carry an estimate marker. Existing defensive estimates are retained; no missing opponent punts are invented.
- **Central takeaways:** IMG_5191.HEIC reports 21 total but 12 defensive interceptions plus 8 fumble recoveries. The site preserves the reported total, and discloses the inconsistency on the turnover differential and defensive AV estimates.
- **Offensive-line AV:** actual GP/GS for all participating linemen are unavailable. Individual slots remain blank rather than assuming five players started every game. The team's line pool is still computed.
- **Eastern punter:** a matching or nearby punt count on a national leaderboard alone does not establish a player's school. No new assignment or missing punt yardage is inferred.
- **Kicking and punting baselines and qualified-passer AY/A:** the pre-existing saved national baselines remain in DATA. Their complete raw transcriptions and qualification process are not included in this repository, so the reconciliation script does not claim to rebuild them. Player/specialist assignments inherited from the prior build remain inferred except where the footage identifies the school.
- **Explosiveness:** every value uses estimated drives and is marked accordingly. Offensive drive-rate AV uses the dynasty's separate AV formula; the two drive definitions are intentionally different in the local calculation references.
- **Total Touchdowns:** this existing row and its national comparison count offensive touchdowns. The footer now explicitly states that definition.

## Local workbook issues

These source issues remain recorded for the next workbook maintenance pass. This change updates the website checkout; it does not overwrite the open local Excel workbook.

- Game Log!X35/BO35 have Central's Western-game turnover types reversed. IMG_5290.HEIC supports **2 interceptions and 0 fumbles lost**. The website already uses the corrected season split, 14 interceptions and 5 fumbles lost.
- IMG_5299.HEIC itself prints 23 completions on 21 attempts. Preserve it as a raw source anomaly; use leaderboard season totals for the website.
- Western fumble recoveries sum to one in Game Log but the season screens report two. The season value is preserved.
- Game Log Week is game sequence, not calendar week. Join scores using team/opponent/game identity rather than that field.
- Master contains reference text rather than executable season-summary formulas.

## Rebuild and validation

`python3 scripts/reconcile_2026.py` reads `data/verified-inputs-2026.json` and updates the affected fields in the embedded DATA object. It preserves all unrelated data, scoreboard rows and ratings. It is a targeted reconciliation, not a complete OCR/import pipeline.

Run `python3 scripts/reconcile_2026.py --check` and `python3 scripts/test_reconciliation.py` before committing. The site remains a self-contained HTML file and needs no runtime fetches or dependencies.

## National Ball Control and Explosiveness benchmarks

The three-team averages have been removed from the explanation notes. A full national mean must use each of the 138 real FBS teams, with the same definition as the displayed index; the five synthetic FCS buckets are not covered by the national stat screens.

The reviewed source set has 105 national team-stat photographs (27 offense, 26 defense, and 13 each for conversions, red zone, penalties and turnovers). None of those tables provides possession time, punts or field-goal attempts. Game Log covers 36 games for Western, Eastern and Central only. League Scores provides game results, not these box-score inputs. The player kicking/punting recordings do not establish complete team assignments and totals for all 138 teams.

Ball Control still requires each team's possession share and offensive play count, alongside first downs and giveaways. The rounded yards/play column cannot recover exact play counts. Explosiveness requires each team's punts and FGA, alongside the captured yardage, scoring, touchdown, giveaway and fourth-down inputs. These missing quantities cannot be uniquely inferred from the available scoring and yardage totals. No national average has been guessed or substituted, and no per-team national index has been added to the page.

To complete the requested averages, supply a team-season export or additional source screens with those missing inputs for the national field. Compute each team's index first and then take the equal-team mean; averaging raw totals or assuming half of possession for every team is a different calculation.
