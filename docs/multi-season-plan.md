# NCAA Dynasty: Multi-Season Website Plan

Prepared: September 17, 2026  
Repository: `https://github.com/ktgz892ydt-gif/NCAA-Dynasty`  
Planning horizon: five to six seasons

## 1. Objective and agreed direction

Extend the existing Dynasty HQ website so it can preserve and display multiple seasons within one repository and one website.

**Each published season will have its own tab at the top of the page.** Initially, only **2026** will appear. Once the next season is completed, verified, and ready to publish, a **2027** tab will be added. Later seasons will follow the same process.

Selecting a season will change all the season-specific content together:

- Team season summaries and records.
- Team statistics, rankings, and coverage notes.
- Head-to-Head comparisons.
- Schedules and game results.
- National team ratings and statistical leaders.
- Individual player leaderboards.
- Season-dependent values inside metric explanations.

The existing navigation will remain beneath the season tabs:

```text
Dynasty HQ

[ 2026 ] [ 2027 ] [ 2028 ]

[ Dynasty ] [ Head-to-Head ] [ Schedules ] [ National ] [ Leaders ]

Content for the selected season and section
```

The years above illustrate the finished design; they are not a proposal to publish empty future-season tabs.

This document is an implementation plan. Creating it does not change the website, its calculations, or its published data.

## 2. Current repository assessment

The repository was reviewed on September 17, 2026. At that review:

- All **43 automated tests passed**.
- All five existing rebuild checks reported current data: reconciliation, SOS, SOR, adjusted efficiency, and player leaders.
- The main HTML file was approximately **607 KB**, including an embedded data object.
- The published data included **2,016 player rows** across the existing categories.
- The site was organized around a single 2026 dataset.

These checks establish a useful migration baseline. They do not prove that every transcription or statistical model is independently correct.

### What already works well

- A static website fits the size and purpose of this project.
- The current interface already provides mobile layouts, sortable tables, comparisons, and explanatory dialogs.
- Verified leaderboard inputs are separated into category files.
- Calculation scripts contain useful integrity checks and regression tests.
- Source notes record known gaps, corrections, and estimates.
- GitHub Desktop provides a familiar commit-and-push workflow.

### What needs to change

| Current structure | Multi-season consequence | Proposed change |
|---|---|---|
| HTML, styles, JavaScript, and data share `index.html` | A content update produces a large mixed-purpose diff | Separate the interface from season data |
| Scripts read existing data out of the HTML before updating it | The website is partly its own source of truth | Read authoritative season inputs and generate display data |
| Script names, paths, and some logic explicitly target 2026 | New seasons require copying and editing scripts | Introduce season-aware build commands |
| Historical corrections mention specific teams, players, and games | A copied correction could affect a later season incorrectly | Keep corrections scoped to the season and source record |
| Summaries are embedded in HTML | A new season could display the old narrative | Store summaries with their season |
| Explanations contain fixed field sizes, game counts, and baselines | A later season could display an incorrect explanation | Insert those facts from the selected season |
| The ratings pipeline is referenced outside the repository | The repository cannot independently rebuild every underlying rating | Bring the required calculation code and configuration into the repository |
| Players are often identified by abbreviated names | Different players could be combined into false career totals | Use verified identities before linking seasons |

## 3. Season-tab behavior

### Published seasons

Maintain a small season manifest that lists the seasons available to visitors. The interface should derive its tabs from this manifest rather than from hardcoded HTML.

Only published seasons appear. Preparing a 2027 data folder must not automatically make 2027 visible on the live site.

Recommended defaults:

- List seasons chronologically from left to right.
- Open the latest published season when the URL does not specify a year.
- Honor an explicit year in a shared URL.
- Visibly distinguish the active season.
- Display the year in the page title and main season description.
- Allow six season tabs to scroll horizontally on small screens without overflowing the page.
- Use accessible tab controls, keyboard navigation, and a visible focus indicator.

### Switching seasons

Preserve the visitor's current section where possible. For example, switching from 2026 to 2027 while viewing Schedules should open the 2027 schedules.

Other state should be handled deliberately:

- Preserve a selected measure when it exists in the new season.
- Select a valid fallback when a measure or player category is unavailable.
- Clear incompatible filters so the new season does not appear empty by accident.
- Close open explanation dialogs and chart tooltips.
- Rebuild explanations, chart data, table rows, labels, and coverage notes from the new dataset.
- Avoid registering duplicate event handlers each time a season changes.

Loading must be consistent: the page must never show a 2027 heading over 2026 statistics. Load and validate the new dataset before activating it. Show a clear loading state and a retryable error if it cannot be loaded. If visitors click several seasons quickly, an earlier request must not overwrite the most recently selected season.

### Shareable URLs

Use a simple URL such as:

```text
?season=2027&view=schedules
```

This avoids requiring separate routes for every season. Browser Back and Forward should restore the selected season and section. An unknown or unpublished year should produce a clear message and a link to an available season.

## 4. Recommended repository structure

```text
index.html
assets/
  styles.css
  app.js
  views/
    dynasty.js
    comparison.js
    schedules.js
    national.js
    leaders.js
config/
  teams.json
  metrics.json
  methods/
    v1.json
data/
  seasons.json
  seasons/
    2026/
      metadata.json
      inputs/
        scoreboard.json
        team-stats.json
        player-identities.json
        corrections.json
        legacy-import.json
      leaders/
        PASSING.json
        RUSHING.json
        RECEIVING.json
        DEFENSE.json
        ...
      summaries.json
      source-notes.md
      season.json
    2027/
      ...
scripts/
  build_season.py
  validate_season.py
  calculations/
    ratings.py
    schedule_strength.py
    strength_of_record.py
    adjusted_efficiency.py
    approximate_value.py
    leaders.py
  migrations/
    import_2026.py
tests/
  fixtures/
    2026-baseline.json
  ...
docs/
  multi-season-plan.md
  adding-a-season.md
  data-capture-checklist.md
```

This is a target structure, not a requirement to create every module immediately. Split code where it creates a clear responsibility; keep the first migration small enough to verify thoroughly.

### Responsibilities

- **Shared interface:** layout, navigation, charts, tables, colors, and dialogs.
- **Team configuration:** stable team identifiers, names, abbreviations, and colors.
- **Metric configuration:** stable metric identifiers, labels, units, display formats, and whether higher or lower is better.
- **Season inputs:** authoritative transcriptions, recorded game results, verified manual entries, and corrections.
- **Season output:** the generated `season.json` used by the browser.
- **Calculation methods:** reusable code and versioned settings.
- **Source notes:** explanations of where evidence came from and what remains incomplete.

`legacy-import.json` is a migration aid for current values whose complete inputs are not yet present in the repository. Such values must retain their provenance and limitations. It should not become the routine input format for future seasons.

## 5. Data contract

### Season manifest

An illustrative manifest for the initial migration:

```json
{
  "schemaVersion": 1,
  "defaultSeason": "2026",
  "seasons": [
    {
      "id": "2026",
      "label": "2026",
      "published": true,
      "dataPath": "data/seasons/2026/season.json"
    }
  ]
}
```

Use paths relative to the project website so they work under the existing GitHub Pages repository URL. Add 2027 only when its publication requirements are met.

### Season metadata

Each season should record:

- Season identifier and display label.
- Data schema version and calculation-method versions.
- Lifecycle status: draft, in progress, or finalized.
- Publication status, separate from completeness.
- Last verified date and source revision or checksums.
- Dynasty teams and the eligible national field.
- Game-length settings and other relevant gameplay rules.
- Coverage cutoff, such as through a particular week or through the postseason.
- Separate coverage descriptions where datasets have different cutoffs.
- Ranking eligibility rules and treatment of synthetic FCS opponents.

A published season can legitimately contain missing data. Publication should mean its limitations have been checked and described, not that every possible statistic is available.

### Coverage and missing values

Continue using `null` for unavailable values. Zero means a measured zero and must not substitute for missing information.

Represent coverage more precisely than a single `complete` flag. Useful distinctions include:

- Entire national field versus the captured leaderboard only.
- Full recorded list versus a partial recording.
- Complete season versus a subset of games.
- Verified school attribution versus unknown school.
- Recorded values versus derived values and estimates.

For example, 400 captured defenders can be a complete recording of a tackle-sorted list while still being insufficient for complete national TFL rankings or team totals.

## 6. Build and validation process

### Proposed commands

```sh
python3 scripts/build_season.py --season 2027
python3 scripts/validate_season.py --season 2027
python3 scripts/build_season.py --season 2027 --check
```

These are proposed interfaces; the current repository does not yet contain them.

### Build responsibilities

The build should:

1. Read the selected season's metadata and inputs.
2. Validate identifiers, duplicate games, records, required fields, and source coverage.
3. Apply only that season's documented corrections.
4. Calculate the underlying ratings from the available scoreboard and configured methods.
5. Calculate dependent statistics, ranks, and leaderboards in an explicit dependency order.
6. Attach coverage, provenance, method versions, and summaries.
7. Validate consistency across the generated results.
8. Write the selected season's output only after the complete build succeeds.

Use a temporary output followed by replacement so a failed build cannot leave a partially updated season file. Building 2027 must never rewrite 2026 as a side effect.

Calculations should use full precision internally. Round for display only. Identical inputs and method versions should produce identical statistical output; avoid volatile build timestamps in content used for reproducibility checks.

### Calculation boundaries

Move the underlying rating generator into the repository before describing the process as fully reproducible. The current update scripts do not collectively reconstruct every published value from raw source files.

Keep one-time 2026 repairs in a migration or correction layer. Do not generalize a player-specific repair into a rule that automatically applies to future seasons.

Season-specific settings must supply game counts, league baselines, ranking denominators, home-field assumptions, and record handling. An in-progress build must handle teams without games and schedules of differing lengths without inventing results or dividing by zero.

## 7. Historical consistency and fair comparisons

### Preserve the initial 2026 migration

The first migration should preserve existing values, ranks, source notes, estimates, and visible content. Structural changes should not silently introduce a new statistical method.

Retain a baseline fixture outside the generated output and compare the migrated season against it. Tests that compare a file only with itself are insufficient protection.

### Version methods

Store a data schema version separately from calculation-method versions. The shape of the data can change without the formula changing, and a formula can change without the data shape changing.

After a season is finalized, updates should be deliberate:

- Correct factual errors with a documented source and revision.
- Record any calculation-method change.
- Do not silently recalculate all archived seasons during a routine new-season build.
- If all seasons are intentionally recalculated under a shared method, identify that revision consistently.

### Across-season statistics

For combined rates, recompute from totals:

- Career yards per attempt uses total yards divided by total attempts.
- Combined completion percentage uses total completions divided by total attempts.
- Combined scoring margin uses total point differential divided by total games.

Do not average percentages, per-game statistics, national ranks, or season ratings indiscriminately.

SRS and SOR describe performance relative to their season's field and assumptions. Displaying them side by side is useful, but their values do not prove the outcome of a hypothetical game between teams from different years. Raw totals also require game-count and gameplay-setting context.

Default to calculating each season independently. Carrying Elo or Glicko into the next year should be a later, explicit modeling decision because roster turnover and offseason changes matter.

## 8. Team and player identities

Assign stable IDs to teams so display-name changes do not break historical links. Keep conference membership and other changing attributes in season data.

Assign stable player IDs only when identity is verified. Initials, surname, and position are not sufficient: current leaderboard data already contain collisions.

Keep a player's season participation separate from identity so transfers can eventually be represented. Unknown school attribution should remain unknown. Career totals should include only confidently linked seasons and clearly describe partial coverage.

Team history can launch before player career tracking; the latter should not block season tabs.

## 9. Future History section

Once a second season is available, useful additions include:

| Feature | Purpose | Dependency |
|---|---|---|
| Team season comparison | Compare Western 2026 with Western 2027 | Consistent metric definitions and coverage |
| Program history | Records, championships, bowls, and annual rankings | Verified season results |
| Rivalry history | Head-to-head results across years | Stable team and game identifiers |
| Team record book | Best recorded totals and rates | Comparable settings and qualification rules |
| Player season record book | Best verified individual seasons | Coverage labels and attribution |
| Player career records | Combine performances across years | Verified player identities |

Keep a future History section distinct from the existing within-season Head-to-Head comparison. Label records as the best among captured data when the underlying national coverage is incomplete.

## 10. Capturing future seasons

Create a repeatable capture checklist before 2027 is archived:

- Preserve the complete national scoreboard, with dates or weeks and postseason identification.
- Capture team offense, defense, situational, turnover, and special-teams totals.
- Record the three dynasty teams' complete individual statistics using team-specific scope.
- Capture the full scrollable list and all relevant horizontal columns.
- Record whether a national leaderboard has a cap or is sorted by a particular measure.
- Preserve enough player identification to verify school attribution and future career links.
- Capture standings, championship results, bowl outcomes, and final rankings separately.
- Record gameplay settings and the date or stage of each capture.
- Retain originals in a season-organized media archive with a backup.

The website repository should contain the transcriptions and source references needed to understand and rebuild the displayed data. Large original recordings can remain in the separate backed-up archive; use archive-relative references rather than paths tied to one Mac account.

## 11. Testing and acceptance criteria

### Data and calculations

- Existing 2026 regression checks continue to pass after adapting file paths.
- Migrated 2026 values and ranks match the preserved baseline.
- Rebuilding a season is repeatable and detects stale output.
- Building one year does not modify another year's files.
- Missing values remain distinguishable from zero.
- Records agree with the relevant scoreboard coverage.
- Ranking denominators match eligible teams for that season and metric.
- Duplicate or conflicting source records are rejected.
- Coverage limitations survive generation and appear in the interface.

### Interface

- Every section updates to the selected season.
- Summary text, page title, dialogs, ranks, and baseline values use the active season.
- Shared season URLs and browser history work.
- Unpublished seasons do not appear as tabs.
- Rapid switching cannot mix datasets.
- Missing categories and failed loads produce useful messages.
- Six season tabs remain usable on a narrow phone screen.
- Existing table heights, team colors, dialog controls, and mobile layouts remain usable.

Use a clearly marked synthetic second-season fixture to test switching before real 2027 data exists. It must stay out of the published manifest and must never be presented as actual dynasty results.

## 12. Hosting and local previews

Keep GitHub Pages and the existing GitHub Desktop workflow. Static HTML, CSS, JavaScript, and JSON are sufficient for the planned scope; no server-side application is required for season browsing.

Loading separate JSON files changes local preview behavior. Opening the HTML directly from the filesystem can fail because browsers restrict local-file requests. Provide a documented local preview command, for example:

```sh
python3 -m http.server 8000
```

Run it from the repository folder and visit the local address in a browser. If a double-clickable offline copy remains important, add a separate generated standalone export later. That export should use the same inputs and templates as the hosted site.

References:

- [GitHub Pages: static site hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [MDN: restrictions on local-file requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSRequestNotHttp)

## 13. Implementation sequence

### Phase 1 — Preserve and extract 2026

- Save a verified baseline of the current dataset.
- Extract season data, summaries, and source notes.
- Separate shared styles and application code.
- Preserve unsupported or legacy inputs with explicit provenance.
- Verify that the reorganized 2026 site shows the same results.

**Completion condition:** 2026 works from the new structure without statistical changes.

### Phase 2 — Add season tabs

- Add the manifest and loader.
- Introduce the season-tab row above the existing section navigation.
- Implement URL state, loading states, error handling, and complete rerendering.
- Test switching with an unpublished synthetic fixture.

**Completion condition:** the live manifest exposes 2026 only, while the application is capable of loading additional seasons correctly.

### Phase 3 — Make builds reusable

- Include the required underlying rating calculations in the repository.
- Replace hardcoded 2026 paths with season-aware inputs.
- Separate historical corrections from general calculation rules.
- Add the unified build command, validation, and method versions.
- Document the source-capture and update workflow.

**Completion condition:** a new season can be prepared without copying the application or changing general calculation code solely to change the year.

### Phase 4 — Publish 2027 when ready

- Populate and verify 2027 inputs.
- Build its statistics and rankings.
- Draft and review its team summaries.
- Confirm coverage, metadata, and final results.
- Add it to the published manifest and select the intended default season.
- Review the changes, commit, and push through GitHub Desktop.

**Completion condition:** both 2026 and 2027 are independently browsable through their tabs.

### Phase 5 — Add historical features

Start with team season comparisons, program records, and rivalry history. Add player career features only when verified identities make them reliable.

## 14. Publication workflow after migration

For each completed season:

1. Organize and back up the original captures.
2. Transcribe and verify the season inputs.
3. Record unresolved gaps and dataset coverage.
4. Build and validate the season output.
5. Review the summaries and preview each section.
6. Publish the season in the manifest.
7. Review the complete change set in GitHub Desktop.
8. Commit and push using the existing workflow.
9. Check the published season and an older season after deployment.

The foundation is one shared website with independently preserved season datasets. Adding a year should become a controlled data-publication task, while interface improvements remain shared across all years.
