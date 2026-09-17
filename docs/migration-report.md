# Multi-season migration report

## Implemented

- One shared HTML shell, CSS file and JavaScript application, with separately loaded season JSON.
- Published-season tabs above the existing section navigation; only 2026 is registered.
- Shareable year/section URLs, keyboard season navigation, browser history, retry states and protection against late responses overwriting a newer selection.
- Complete season-view cleanup, including dialogs, tooltips and global event subscriptions.
- Season-owned narratives, provenance, source inputs and coverage notes.
- Dynamic metric explanations for national field sizes, game counts and scoring baselines.
- A deterministic one-season build with atomic output replacement and source checksums.
- Initialization and publication commands that keep unfinished future seasons off the live site.
- The original rating engine copied into the repository and adapted to JSON scoreboards.
- Original 2026 Elo game order extracted read-only from the workbook and preserved as a source input.
- Explicit historical correction handling restricted to 2026.
- Stable dynasty team IDs and a place for verified player identities, without automatic name matching.
- History: program seasons, season comparisons, rivalry results, captured program records and captured player-season records.
- Automated data checks on push/PR, local regression tests and invisible-browser tests.
- Documentation for future capture, input, build, preview and publication.

## Preservation checks

The independent baseline is the complete pre-migration 2026 `DATA` object. The build reproduces **every original field exactly**, including all existing values, schedules, rankings, player data and historical notes. New metadata is additive.

SRS, Elo, Bradley–Terry and Glicko are independently recalculated from the scoreboard and compared to the archived ratings. Small floating-point differences in internal linear algebra are tolerated during this verification; the verified original 2026 full-precision values remain the source for the archived dependent metrics. No spreadsheet was modified.

The old 2026 source-path strings remain in historical metadata where exact preservation requires them. Their relocated equivalents are:

| Historical reference | Current location |
|---|---|
| `data/srs-2026.json` | `data/seasons/2026/inputs/srs-reference.json` |
| `data/verified-inputs-2026.json` | `data/seasons/2026/inputs/verified-corrections.json` |
| `data/leaders-2026/` | `data/seasons/2026/leaders/` |
| `data/SOURCE_NOTES.md` | `data/seasons/2026/source-notes.md` |

## Checks performed

- Existing 43 regression tests preserved and passing.
- Seven additional multi-season tests: baseline equivalence, blank initialization, isolation and reproducibility, invalid inputs, deliberate publication historical-correction scope and unpublished local previews.
- Browser checks at 320, 390, 768 and 1280 pixels across all original views.
- Six synthetic seasons supplied only through test request interception.
- Keyboard season selection, deep links, Back navigation, missing categories, load failure/retry and delayed-response races.
- Existing TFL depth, explanation dialogs, theme controls and History rendering.
- Visual review at phone and desktop sizes.

## Intentional boundaries

No future season is fabricated or published. Actual 2027 inputs and reviewed summaries are still needed before a 2027 tab can appear.

Some 2026 values remain documented imports because the full underlying transcriptions were not originally in the repository. The migration preserves them instead of claiming to reconstruct everything from photos.

Future standard builds compute scoreboard-derived metrics and ingest verified inputs for other measures. The team-specific 2026 AV correction is deliberately not applied to future seasons. Additional raw-stat derivations can be implemented as versioned calculations when their sources are available.

Player-season record lists do not merge careers. Verified cross-season identities are required before career totals can be supported reliably. All captured-list records retain their coverage caveat.

The local preview now uses an HTTP server. An optional single-file offline export was not required for the hosted multi-season workflow and is not included.

Nothing in this migration commits or pushes changes automatically. Publication remains under the owner's GitHub Desktop workflow.
