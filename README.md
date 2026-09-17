# NCAA Dynasty — Dynasty HQ

One static website for the Western Michigan, Eastern Michigan and Central Michigan dynasty, with a top-level tab for each published season. **2026 is the only published season.** Future data folders do not appear until explicitly added to the publication manifest.

Live: https://ktgz892ydt-gif.github.io/NCAA-Dynasty/

## Browse

Choose a year above the existing Dynasty, Head-to-Head, Schedules, National and Leaders navigation. All summaries, ratings, explanations and coverage notes follow that year. Links retain the selected year and section, for example `?season=2026&view=sched`.

History provides program season records, a two-season comparison when available, recorded rivalry games and a program record book. It loads published seasons only. Player career totals remain unavailable because abbreviated names do not establish identity across seasons.

## Files

- `index.html`: shared shell and season-view template.
- `assets/`: shared styles, loader, season views and history.
- `config/teams.json`: stable dynasty team IDs, names and colors.
- `config/metrics.json`: shared metric definitions and display formats.
- `config/methods/v1.json`: versioned model settings.
- `data/seasons.json`: publication manifest and default season.
- `data/seasons/<year>/inputs/`: authoritative input data and documented corrections.
- `data/seasons/<year>/leaders/`: player transcriptions and source coverage.
- `data/seasons/<year>/summaries.json`: reviewed narratives.
- `data/seasons/<year>/season.json`: generated browser dataset. **Do not edit directly.**
- `scripts/`: build, validate, initialize, publish and calculation commands.
- `tests/fixtures/2026-baseline.json`: independent pre-migration statistical baseline.

The site is still static and hosted with GitHub Pages. No database or backend is required.

## Build and check

Python 3.10 or newer is recommended. NumPy is the only runtime dependency for building ratings. Create a virtual environment if needed:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -B scripts/build_season.py --season 2026
python3 -B scripts/build_season.py --season 2026 --check
python3 -B scripts/validate_season.py --all
python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

A build reads season inputs, never existing generated output. It validates and recomputes supported values, then atomically replaces only the selected season file. It does not update the publication manifest, commit, push, or rebuild other seasons. The old `update_*.py` and reconciliation command entrypoints delegate to this unified build for compatibility.

The imported 2026 source contains some legacy transcriptions whose original raw inputs were not exported. They are preserved explicitly in `inputs/legacy-import.json` and `inputs/team-stats.json`. The scoreboard-derived rating engine is now included, and all four published rating systems are independently checked during the archived-season build. Other imported values are not falsely claimed to have been reconstructed from raw photos.

## Preview locally

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/`. JSON loading requires a local HTTP server; opening `index.html` directly with a `file:` URL is no longer the supported preview workflow.

Optional browser regression tests use Playwright and Chromium:

```sh
PREVIEW_URL=http://localhost:8000/ node tests/browser/multiseason.mjs
```

Install Playwright in your development environment first. `PLAYWRIGHT_MODULE` can point to an existing Playwright module, and `CHROME_PATH` can specify an installed Chromium browser. Test-only future seasons are intercepted in memory and never added to the site.

## Add a season

See [Adding a season](docs/adding-a-season.md) for the complete workflow and input examples, and the [capture checklist](docs/data-capture-checklist.md) for what to record.

```sh
python3 -B scripts/init_season.py --season 2027
# Populate inputs, coverage, settings and summaries; review and finalize metadata.
python3 -B scripts/build_season.py --season 2027
python3 -B scripts/validate_season.py --season 2027
python3 -B scripts/publish_season.py --season 2027
```

Initialization creates blank, unpublished inputs. Publishing updates the local manifest only after verification. Review, commit and push the files through GitHub Desktop when ready. No 2027 results or summaries are supplied by this migration.

## Preservation and limitations

- The migration preserves every original 2026 dataset field, including all values and rankings. Additive metadata records provenance and coverage.
- The 2026 scoreboard/statistics cover the regular-season capture. Separately reported championship, bowl and final CFP outcomes do not imply that postseason box scores are included.
- Ratings are season-relative. Method versions, game lengths and coverage should be considered when comparing years.
- Missing values stay `null`, displayed as a dash; absent stats are never copied from the previous season.
- A complete recording can still be a capped player list. The TFL view ranks captured players only.
- For standard seasons, scoreboard-derived records, points, MOV, Pythagorean expectation, SRS, Elo, Bradley–Terry, Glicko, SOS, SOR and adjusted scoring efficiency are generated. Other measures require verified season inputs; missing ones stay blank. The special 2026 AV reconciliation does not run on another year.
- SOR needs at least 25 eligible teams and a valid probability fit. In-progress data can leave it unavailable.

Further details: [Migration report](docs/migration-report.md), [data contract](docs/data-contract.md), [original plan](docs/multi-season-plan.md), [2026 source notes](data/seasons/2026/source-notes.md), and [archived 2026 background](docs/2026-background.md).
