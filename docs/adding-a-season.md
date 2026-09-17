# Adding a season

## 1. Prepare an unpublished draft

Run `python3 -B scripts/init_season.py --season 2027` when ready to begin 2027. It refuses to overwrite an existing year. It does not copy 2026 values, add a tab or edit the manifest.

Fill `metadata.json`: verification date, game length, source coverage, synthetic opponent names and lifecycle status. Keep `inputMode: "standard"`. Start with `status: "draft"`, change to `in-progress` while collecting games, and `finalized` after the season inputs and limitations are reviewed. A finalized season may still have explicitly unavailable statistics.

The `legacy-2026` input mode is a historical compatibility layer and is refused for any other year.

## 2. Enter scores

Add played games to `inputs/scoreboard.json`:

```json
[
  {"wk": 0, "a": "Western Michigan", "h": "Eastern Michigan", "as": 21, "hs": 14, "n": false, "ot": false}
]
```

This example is illustrative, not a real future result. Use the actual week, canonical team names, scores and neutral-site flag. Optional `date` is a consistently formatted chronological string. Preserve chronological input order within each week/date because Elo depends on order. Do not enter unplayed fixtures as 0–0 results.

A real team cannot have two games in one week in this data contract. Synthetic buckets may appear multiple times if named in metadata. Duplicate/conflicting fixtures and tied scores are rejected. All opponents in a national rating need a connected schedule graph; disconnected early-season data requires more games before national ratings are meaningful.

## 3. Enter verified team statistics and players

`inputs/team-stats.json` contains metric cells keyed by the configured short team name and metric ID:

```json
{
  "W. Michigan": {
    "pyds": {"v": 2500, "rank": null, "of": null, "note": "Illustrative only; replace with a verified source and coverage."}
  }
}
```

Use IDs from `config/metrics.json`. Do not invent ranks for fields without national coverage. The build fills unavailable cells automatically. Scoreboard-derived cells are regenerated, so editing their input values does not override the calculated result. The general build does not derive all workbook measures from raw play-by-play; supply verified values for other measures and keep source notes.

Place player categories in `leaders/<CATEGORY>.json` using the existing source shape: `category`, `columns`, `sortedBy`, `complete`, `rows`, optional arithmetic `identities`, and source descriptions. `complete` means the recording reaches the end of that list. An optional `coverage.nationalComplete: true` requires evidence that the list includes every eligible player, not merely the full capped display. Unknown schools must be `null`.

`inputs/player-identities.json` is reserved for verified stable IDs; no name-based automatic matching occurs. Career totals are not yet displayed. Do not label ambiguous abbreviated names as verified identities.

## 4. Document corrections and summaries

Keep raw evidence and describe corrections in source notes. An optional `inputs/corrections.json` patch requires the season, team, metric, exact expected old cell, replacement cell and a `source`. It is applied before calculations and refuses an unexpected old value.

Write reviewed summaries in `summaries.json`:

```json
[
  {"teamId": "wmu", "title": "Western Michigan · actual record", "text": "Reviewed season summary."}
]
```

Include one summary per dynasty team before publication. The example text is a placeholder for editing, never approved content for a live season.

## 5. Build, check and preview

```sh
python3 -B scripts/build_season.py --season 2027
python3 -B scripts/validate_season.py --season 2027
python3 -B -m unittest discover -s scripts -p 'test_*.py'
python3 -B scripts/preview.py --season 2027 --port 8000
```

Open `http://127.0.0.1:8000/`. The preview server temporarily exposes the selected draft in memory and labels its tab “preview”. It never changes the publication manifest on disk and binds only to the local computer. Stop it with Ctrl+C when finished. A normal preview server and the live site still show published seasons only.

A build failure leaves the previous output intact. Correct the reported source issue and rebuild; do not patch generated JSON.

## 6. Register and push

After finalizing metadata, entering settings and verification date, reviewing each summary and rebuilding:

```sh
python3 -B scripts/publish_season.py --season 2027
python3 -B scripts/validate_season.py --all
```

This only registers the season locally, with the latest year as default. Review the entire change set in GitHub Desktop, commit and push. Verify both the new tab and an older season after GitHub Pages updates.

## Correcting an archived season

Change the relevant source input, record why in source notes, rebuild that year and review the diff. The 2026 rating reference deliberately rejects scoreboard changes until its historical reference/order have been explicitly reviewed. Do not casually change global method settings: preserve the existing method and introduce a tested new version for a methodological revision. New versions require an implementation as well as a settings file; unknown versions are rejected.
