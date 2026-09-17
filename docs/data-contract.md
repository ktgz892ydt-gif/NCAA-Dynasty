# Season data contract, version 1

The publication manifest (`data/seasons.json`) is the only source of public tabs. IDs are four-digit years. Each published entry points to exactly `data/seasons/<id>/season.json`. `defaultSeason` must name a published entry; initialization never edits the manifest.

Each season's `metadata.json` defines its ID, schema version, lifecycle, verification date, method version, input mode, dynasty team IDs, game duration, synthetic opponents and separate statistics/results coverage. Publication and dataset completeness are separate concerns.

Stable IDs `wmu`, `emu`, `cmu` map to names and colors in `config/teams.json`. The existing season object retains short/canonical names for compatibility with the rendered tables and original tests. Cross-season history joins dynasty teams by stable ID, not screen order. Other national teams currently use canonical names in scoreboards; verify naming consistently when transcribing.

A metric cell is `{ "v": number|string|null, "rank": number|null, "of": number|null }`, with optional `note`, `partial` and `estimate`. Blank is not zero. Rank needs an eligible population. Full-precision calculation inputs are retained; the browser applies display formatting.

`config/metrics.json` defines IDs, units through display formats, labels, grouping and favorable direction. A model/schema change must be deliberate and covered by tests. Initial migration uses the existing definitions rather than renaming metrics.

The generated dataset contains the existing browser-compatible fields, plus:

- `schemaVersion` and complete `metadata`.
- `teamConfig` and `summaries`.
- `sourceChecksums` for season inputs and shared configuration.
- `seasonNotes` for visible coverage.
- `leaderCoverage`, distinguishing recorded depth, capture completeness and verified national completeness.
- `playerIdentities`, currently with no verified cross-season links.

The browser loads the selected year and remounts all season views. Shared configuration is included in generated data so a published file has everything needed to render that season. History loads published datasets on demand and never averages national ranks or season ratings.

The original 2026 snapshot is stored independently under `tests/fixtures`. Every original field must match after the first migration. Imported historical values without reconstructable raw sources remain explicitly identified in the season's legacy inputs. Numerical rating calculations are verified from the national scoreboard on every 2026 build; original floating-point exports are retained only after the independent result agrees.

For future seasons, use `inputMode: standard`. General rating calculations start fresh each season and do not carry Elo/Glicko state forward. SOR requires 25 eligible teams. Empty drafts keep statistics unavailable; unidentifiable disconnected national schedules are rejected. Missing non-scoreboard measures are not filled from another year or treated as zero.

Source paths in retained historical notes may reflect their original location. New sources should use archive-relative paths and dates, preserving original videos in a backed-up season archive.
