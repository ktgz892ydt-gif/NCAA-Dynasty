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
| Eastern punter D. Hull | IMG_5221.MOV, punt column clipped | 25 punts (1,165 / 46.6), 1,165 yards, 0 blocked |

Eastern's first-game entries are retained workbook transcriptions. The current folder lacks the lower box-score screen for that game, so their provenance is disclosed rather than described as freshly verified photo values. Adding them to the eleven photographed games gives **25 punts, 937 kick-return yards, 269 punt-return yards and 11,715 seconds of possession**. Possession/game is 976.25 seconds. Its punt yardage is now complete. **Eastern's punter is D. Hull.** His punt-count column is clipped off the screen, so the count comes from 1,165 yards / 46.6 average = **25.00** — the only punter in the captured field with 25, and exactly Eastern's total of 21 photographed punts plus the 4 in the Game Log entry. That identification is an equality, not a proximity match, and `reconcile_2026.py` now raises if an input edit breaks it. His 1,165 season yards supply the missing game's punt yardage (1,165 − 969 = 196 over 4 punts, a 49.0 average), so the `11g` markers on Eastern's punt yards and yards/punt are gone.

Under the unified drive definition below, the three schools have **141, 125 and 138 estimated drives** and offensive rates of **2.6241, 1.4080 and 2.1594 points per drive**. The three-team baseline gives offensive AV pools of **127.146854 Western, 68.222191 Eastern and 104.630954 Central**. The dependent line, skill, rushing, passing, receiving and quarterback values are regenerated together. Eastern's Explosiveness Index is **8.512**, using the existing rounded team YPP and the same estimated-drive formula.

The passing footage supports keeping the corrected quarterback-room totals already in the site: Eastern 175 completions on 311 attempts and Central 205 on 302. Passing ratings use those leaderboard season figures, not the inconsistent per-game completion transcriptions. Sacks-taken rates use sacks divided by attempts plus sacks.

## Estimates and unresolved sources

- **Defensive AV no longer estimates opponent field goals.** Defensive drives now equal the team's own estimated drive count, because possessions alternate: over a season a defence faces its offence's drive total to within about a possession a game. This replaced a reconstruction of opponent FGA from the scoring identity, which charged every non-offensive touchdown allowed to phantom field goals and so ran at 1.12x to 1.73x the national attempt rate of 1.46 per team-game. That inflation was largest for Western, whose 248 points allowed on 25 offensive touchdowns works out to 9.9 points per touchdown allowed against a realistic seven. It had lifted Western's defensive pool above Central's, contradicting points allowed per game, defensive efficiency and yards per play allowed, all three of which rank Central's defence first. The corrected order is Central, Western, Eastern. The pools still carry an estimate marker because the drive count is itself the documented estimate and the baseline is only the three schools, but they no longer depend on opponent punts or takeaways at all — so Eastern's 11-game opponent-punt total and Central's 21-versus-20 takeaway discrepancy no longer reach this figure.
- **Central takeaways:** IMG_5191.HEIC reports 21 total but 12 defensive interceptions plus 8 fumble recoveries. The site preserves the reported total, and discloses the inconsistency on the turnover differential and defensive AV estimates.
- **Per-player AV rows removed.** Splitting a position pool among individuals requires Games Started, which NCAA 26 reports on no screen: passing, rushing, receiving, blocking, defensive, kicking and punting all give games played and snaps only. Snaps are not a substitute — a defender with 900 snaps would take five times the pool that his real production supports. The 23 unsupported rows (LT, LG, C, RG, RT, RB1, RB2, WR1–WR3, TE1, DE1/DE2, DT1/DT2, LB1–LB4, CB1/CB2, SS, FS) are dropped from `statMeta` rather than displayed as a column of blanks; the script records them in `avNotes.dropped_player_rows`. Team and position-group pools are unaffected, and the players the screens do name — each quarterback room, kicker and punter — keep their rows.
- **Kicking and punting baselines and qualified-passer AY/A:** the pre-existing saved national baselines remain in DATA. Their complete raw transcriptions and qualification process are not included in this repository, so the reconciliation script does not claim to rebuild them. Player/specialist assignments inherited from the prior build remain inferred except where the footage identifies the school.
- **One drive definition.** Offensive AV, defensive AV and Explosiveness now all use the estimate documented in `calculations.md`: offensive touchdowns, FGA, punts, giveaways, failed fourth downs and two end-of-half possessions per game. The AV offensive rate previously used a shorter count that omitted the last two terms and produced 7.3 to 9.1 drives per game against a realistic twelve; it also disagreed with the defensive count for the same team by 6 to 20 per cent. Unifying them moves the offensive pools by one to six points and leaves the ranking unchanged. Every value using estimated drives is still marked accordingly.
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

## Points-based SOS

Website SOS now averages the full-precision SRS of each scheduled opponent. The input ratings come from the existing local ratings export and match all 143 displayed national SRS ratings to their display precision. The builder uses all 888 games; a repeated opponent contributes once for each meeting. Synthetic FCS buckets contribute their actual calculated SRS, not a forced zero rating or a forced 12-game divisor. National ranks/top ten include only the 138 real FBS teams. Rankings use unrounded SOS values and competition ranks for exact ties.

`data/srs-2026.json` stores full-precision input ratings and a scoreboard checksum. `scripts/update_sos.py` computes every team’s SOS, the three comparison values, national ranks, top ten and points formatting. `scripts/test_sos.py` verifies repeat-opponent weighting, missing/stale-input rejection, FBS ranking and the identity between SRS, home-adjusted scoring margin and SOS across all 143 teams. The existing SRS, scoreboard, AV inputs and other statistical values are unchanged.

The prior record-based SOS in the local workbook and original ratings export is not used by the website’s new SOS field. These local sources remain untouched.


## Estimated SOR addition

Derived from the existing 888-game national scoreboard, full-precision `srs-2026.json` and the existing home-field estimate. No new photo transcription or workbook values. The shared benchmark is the average SRS of the top 25 FBS teams. All 138 FBS teams receive a résumé rank; synthetic FCS buckets are opponents only. `scripts/update_sor.py` stores model parameters, retrospective fit diagnostics and per-team match-or-exceed probabilities in `DATA.sorMethod`. See README for assumptions and validation limitations.

## Summary-card measures removed from the stat table

SOS, SOR, SRS and MOV appear at the head of every team's summary card, so they no longer repeat as rows in the full stat table. They are flagged `hide` in `statMeta` rather than deleted: the values, ranks and national leader lists are untouched, the Head-to-Head measure picker still offers all four, and the National tab still ranks the whole 143-team field on them. `update_sor.py` rebuilds its own `statMeta` entry, so the flag is set there as well as in `reconcile_2026.py`.

## Offensive v Defensive Balance

The Core Efficiency row named "Offensive v Defensive Balance" is the workbook's `CARRIES / PASSING ATTEMPTS`. Despite the name it compares the offense with itself, not with the defense, and it measures play calls rather than yardage. The page now carries that explanation on the measure itself so the label cannot be read as an offense-versus-defense rating.

## Full national DEFENSE leaderboard

`IMG_5215.MOV` scrolls the national DEFENSE leaderboard from the first row to the last. It is now transcribed in full: **400 players**, from S. Bracey at 124 tackles to M. Malaki-Donaldson at 57. The site previously held the first twelve rows, which was all the earlier pass captured.

The list scrolls continuously at roughly sixteen rows a second, so most video frames are ghosted by the TV's own scroll animation. Frames were sampled at the native rate and the sharpest in each window chosen by bright-pixel fraction, since ghosting halves peak text brightness while *raising* the gradient energy a naive sharpness metric would use. Consecutive pages were then chained by overlapping player names, and every page overlaps its predecessor by at least one row, so no row is interpolated or assumed. Where a page turned over with no overlap, an intermediate frame was pulled until the two chained.

Three arithmetic identities on the screen validate the result, and all three hold on all 400 rows: SOLO + ASSISTS = TAK; TAK never increases down the list; and INT YDS / INT = INT AVG wherever there is an interception. As an independent check, the twelve rows already published were reproduced exactly by this pass without reference to them.

The screen prints no team column. A player's school appears only on the card beside the highlighted row, so only the two players already identified carry a team; the rest are null rather than guessed.

`data/leaders-2026/DEFENSE.json` stores the rows and this provenance, `scripts/update_leaders.py` writes them into DATA and re-checks the identities on every run, and `scripts/test_leaders.py` covers the invariants, the row count, the refusal to guess teams, and the fact that team TFL stays blank regardless. `DATA.leaderDepth` records each category's depth so the Leaders tab can state whether a list is complete or truncated.

**This does not unblock Tackles for Loss.** TFL is a column on this very screen, but a 400-deep national list sorted by tackles is about three players per school, and sorting by tackles systematically excludes the linemen who generate most of a team's TFL. See the README for the full reasoning and for the one setting that would fix it.

## Kick and punt returns

These two categories were photographed rather than recorded. **KICK RETURN** is twenty-nine stills, IMG_5222 through IMG_5250, each one screenful overlapping its predecessor by a single row; the last ends with the highlight on the final row, giving the complete list of **313 players**. YARDS / KR = AVG holds on every row and AVG never increases.

One lesson from it: the stills are 5712 pixels wide, and an early pass read them from a 1600-pixel copy where a 392 came out as 382. The yards-per-return identity caught it. Everything here is read from the full-resolution originals.

**PUNT RETURN is the one category the source set cannot complete.** Only two stills exist, IMG_5251 and IMG_5252, covering **23 players**; the list plainly continues past them, since many players have a single return. This is recorded as `complete: false` and the page says so rather than presenting 23 as the whole leaderboard. Capturing the rest needs new photographs or a recording of that screen.

Each category now carries its own file under `data/leaders-2026/` declaring its columns, its sorted column, and the arithmetic identities the screen prints, so `scripts/update_leaders.py` validates every category by re-deriving them rather than trusting the transcription. `DATA.leaderComplete` drives the wording on the Leaders tab.

## Punting, and the Eastern punter confirmed

The national PUNTING leaderboard is now complete at **138 punters — exactly one per FBS team**. IMG_5220 carries GP through BLOCK and IMG_5221 is the same list scrolled right for SNAPS; because IMG_5221 still shows the NAME column the two were merged by name rather than by row position, and all 138 matched in order.

This settles the Eastern punter question properly. D.Hull was originally identified by dividing his yards by his average, because his punt-count column was clipped: 1,165 / 46.6 = 25.00. That inference rested on the claim that no other punter had a similar count, which at the time was based on a partial transcription and could not actually be checked. **The complete field now confirms it directly.** The last three rows of the national list are D.Duley 36, R.Millmore 26 and D.Hull 25, each count unique among all 138 punters, and each printed on screen rather than derived. All three are now attributed to their schools in the leaderboard, and a test cross-checks their name, punts, yards and blocked against `verified-inputs-2026.json`.

Two identities validate every row — YARDS / PUNTS = AVG and NET YDS / PUNTS = NET AVG — and the first caught a real error: W. McSparron read as 2,482 yards, which gives 43.5 rather than the 43.7 on screen. At full resolution it is 2,492.

D.Hull's SNAPS of 37 also matches the figure recovered in the earlier pass, an independent check on the merge.

## Kicking

The national KICKING leaderboard is complete at **138 kickers**, the same one-per-FBS-team count as punting. Its twenty-two columns span three recordings: IMG_5217 carries GP through XP%, IMG_5218 the four distance buckets plus kickoffs and touchbacks, IMG_5219 from FGA49 rightwards to SNAPS. All three keep the NAME column, so they merge by name rather than by row position, and all 138 names matched in order; the columns that appear on both IMG_5218 and IMG_5219 agree row for row.

This is the best-validated category in the set. Five independent identities hold on every row: the four distance buckets sum to FGM, and separately to FGA; FG% equals floor(100 x FGM / FGA); XP% equals floor(100 x XPM / XPA); and TB% equals touchbacks over kickoffs. The percentages are truncated by the game rather than rounded, which makes those two checks exact rather than tolerant. The FGA bucket sum caught a misread: K. Meester's FGA49 read as 3, giving 14 attempts against the 15 printed, and is 4 at full resolution.

`scripts/update_leaders.py` now understands three kinds of identity, because the screens print three kinds: parts that must add to a total, a rounded quotient such as an average, and a truncated percentage. A quotient rule may carry a `scale` so a percentage can be expressed as one.

## Passing, and three quarterbacks identified

The national PASSING leaderboard is complete at **192 quarterbacks** — every player who attempted a pass, down to T. Ulatowski at 0 for 1. Its nineteen columns span IMG_5208 (GP through TD:INT) and IMG_5209 (YPA through SNAPS); both keep the NAME column, so the two merge by name and all 192 matched in order.

Eight identities hold on every row. Within the first screen: COMP% is floor(100 x completions / attempts), TD% and INT% are per attempt, and TD:INT is touchdowns over interceptions — with the game dividing by one when a quarterback has none, so `update_leaders.py` carries a rule for exactly that. Across the two screens: YPA, YPG, SACK% (sacks over attempts plus sacks) and the passer RATING, which reproduces the NCAA formula (8.4 x yards + 330 x TD + 100 x completions - 200 x INT) / attempts.

Two ratings disagree with that formula by exactly one tenth — W. Wilson shows 99.1 where the formula gives exactly 99.2, and D. Afalava 142.7 against exactly 142.8. Both are cases where the true value lands precisely on a tenth, and the game's single-precision result falls just below it and is truncated. It is the game's arithmetic, not a misreading, so the rating check carries a one-tenth tolerance.

**Three of the dynasty quarterbacks are now identified with certainty.** B. Lowry's national line matches Western Michigan's team passing totals exactly on attempts, yards, touchdowns and interceptions (352, 2,922, 21, 14), so he took every one of Western's attempts. N. Kim and A. Flores leave only 8 and 4 attempts for Eastern's and Central's backups respectively.

That settles an earlier correction that had rested on inference. The site's quarterback-room completion figures of **175 for Eastern and 205 for Central** are corroborated: N. Kim alone has 172 and A. Flores 204, leaving 3 completions on 8 attempts and 1 on 4. The original screen readings of 185 and 257 are now ruled out arithmetically — 257 completions is impossible when Central's starter has 204 and only four other attempts exist all season. The sack figures agree too: Western's 29 taken at 7.6% is B. Lowry's line exactly, while Eastern's 38 and Central's 35 exceed their starters' 37 and 33 by the one and two sacks their backups took.

## Final CFP rankings

Reported by the dynasty owner: **Central Michigan 22nd, Western Michigan 23rd, Eastern Michigan unranked.** Master treats Conference Champion, Bowl Result and Final CFP Ranking as user-entered, and no screen in the source set records any of them. With these three the Results group is complete, and the only blank rows left on the page are Tackles for Loss, Defensive Touchdowns and special-teams TDs.

## Rushing

The national RUSHING leaderboard is complete at **400 players**, the same cap the defensive list hits, ending at F. Meadows on 145 yards. Thirteen columns span IMG_5210 (GP through LONG) and IMG_5211 (TD rightwards to SNAPS); the six columns they share agree row for row and both keep the NAME column, so all 400 merged by name in order.

Three identities hold on every row: AVG is yards per carry, AVG G yards per game, FUM% fumbles per carry.

Two things are worth recording about method. Frames were read in **stitched pairs** — two consecutive screenfuls side by side in one image — which roughly halves the number of reads without losing legibility. And for the columns the screen derives nothing from (SNAPS, BTK, YAC, 20+, LONG) the overlap between frames is the *only* check; it earned its place by catching J. White's snap count, read once as 870 and confirmed at full resolution as 670.

The strongest validation is external: **87 players appear in both this list and the passing list, and their snap counts agree on all 87.** Two independently transcribed datasets, 592 rows between them, with no disagreement. Note that the check must key on name *and* position — three abbreviated names (J. Lewis, B. Brown, C. Brown) belong to a quarterback and a separate running back, and keying on name alone makes them look like errors.

## Receiving, and a cross-category check on snaps

The national RECEIVING leaderboard is complete at **400 players**, the same cap the defensive and rushing lists hit, ending at K. Reynolds on 482 yards. Eleven columns span IMG_5212 (GP through DROPS) and IMG_5213 (YARDS rightwards, plus SNAPS). Because the second screen repeats the yardage, the merge is pinned on name *and* receiving yards at every row rather than on name alone.

Three identities hold on all 400: AVG is yards per reception, AVG G yards per game, RAC AVG yards after the catch per reception.

With eight categories transcribed there is now a check that spans them. A player's snap count is one number however many leaderboards he reaches, and the categories were read independently. **177 name-and-position keys appear in more than one list, and 161 carry the same snap count in every one.** The sixteen that differ are not errors: the game prints an initial and a surname, so a key like "T.Brown WR" covers three different players, and "M.James HB" is a running back in one list and the dual returner — consistent at 89 snaps across both return screens — in the others. `scripts/test_leaders.py` asserts the consistent share stays above ninety per cent and, separately, that every player appearing on both return lists carries an identical snap count.

**BLOCKING remains untranscribed on purpose.** Its three columns are GP, SACK and SNAPS; nothing is derived from anything, so a misreading could not be caught by any of the methods used everywhere else. It is also sorted ascending with hundreds of ties on zero sacks, which makes even the ordering check close to worthless. Capturing it usefully needs a different approach, not more reading.

## Opponent-adjusted efficiency

`scripts/update_efficiency.py` decomposes scoring into an offensive and a defensive rating for all 143 teams, solved together across the 888-game scoreboard. It adds no new source material: the scoreboard, the team list and the home-field estimate were all already in DATA.

The solve is alternating least squares, each sweep exact for the side being updated, with offence and defence recentred on zero so the model's two-dimensional null space is fixed and the level stays in the league mean. It converges in 80 sweeps; residual RMSE is 8.83 points per team-game, which is about what a points model should leave once schedule is removed.

**The check that matters:** AdjO − AdjD is algebraically SRS, and SRS was computed independently by the dynasty owner's own ratings script using a direct least-squares solve. The two agree to **5 × 10⁻¹³ points** for every one of the 143 teams against the full-precision export in `data/srs-2026.json`, and exactly at the two decimals DATA stores. Two different methods, two different code paths, same answer.

Because of that identity the margin is deliberately **not** published as its own statistic — it would be SRS under a second name. Only AdjO and AdjD reach the page, on each summary card and in the Results group after MOV. `adjem` stays on the ratings rows purely so the agreement can be asserted in `scripts/test_efficiency.py`.

Pace is not normalised, and cannot be: no national screen carries punts or field-goal attempts, so league-wide drives are unavailable — the same limitation already recorded for Explosiveness. The ratings are per game and say so in `DATA.effMethod`.
