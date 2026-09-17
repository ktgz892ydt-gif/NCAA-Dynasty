"""Write the transcribed national player leaderboards into the self-contained site.

Each category that has been read from its recording or photo set lives in
data/seasons/<year>/leaders/<CATEGORY>.json, carrying its own columns, provenance and the
arithmetic identities the screen itself prints. Categories with no file keep
whatever DATA already holds - the single screenful the first pass captured.
"""
import argparse
import json
from pathlib import Path
from season_io import ROOT

LEADERS = ROOT / 'data/seasons/2026/leaders'


def check_identities(source):
    """Re-derive every relationship the screen prints, on every row.

    Three kinds, because the screens print three kinds: parts that must add up
    to a total, a rounded quotient (an average), and a percentage the game
    truncates rather than rounds.
    """
    rows, sorted_by = source['rows'], source['sortedBy']
    previous = None
    for i, row in enumerate(rows, 1):
        v = row['values']
        where = f'{source["category"]} row {i} ({row["name"]})'
        for rule in source.get('identities', []):
            if 'sum' in rule:
                parts, total = rule['sum']['parts'], rule['sum']['total']
                if sum(v[p] for p in parts) != v[total]:
                    raise ValueError(f'{where}: {" plus ".join(parts)} is not {total}')
            if 'quotient' in rule:
                num, den, quot = rule['quotient']
                scale = rule.get('scale', 1)
                if v[den] and abs(scale * v[num] / v[den] - v[quot]) > rule.get('tolerance', 0.051):
                    raise ValueError(f'{where}: {num} over {den} is not {quot}')
                if not v[den] and v[quot]:
                    raise ValueError(f'{where}: {quot} is set but {den} is zero')
            if 'ratio_min1' in rule:
                # the game divides by one when the denominator is zero, so a
                # quarterback with no interceptions shows his touchdown count
                num, den, quot = rule['ratio_min1']
                if abs(v[num] / max(v[den], 1) - v[quot]) > rule.get('tolerance', 0.051):
                    raise ValueError(f'{where}: {quot} is not {num} over max({den}, 1)')
            if 'floor_percent' in rule:
                # the game truncates these, so the check is exact rather than tolerant
                num, den, pct = rule['floor_percent']
                if v[den] and int(100 * v[num] / v[den]) != v[pct]:
                    raise ValueError(f'{where}: {pct} is not floor(100*{num}/{den})')
        value = v[sorted_by]
        if previous is not None and value > previous:
            raise ValueError(f'{source["category"]} row {i} ({row["name"]}): '
                             f'the list is sorted by {sorted_by} descending')
        previous = value


# Columns the screens do not print, worked out from ones they do. Kept apart from
# the transcribed values so the page can say which is which: air yards is simply
# the receiving yardage that happened before the catch.
DERIVATIONS = {
    'RECEIVING': [
        ('AIR YDS', lambda v: v['YARDS'] - v['RAC']),
        ('AIR/REC', lambda v: round((v['YARDS'] - v['RAC']) / v['REC'], 1) if v['REC'] else 0.0),
    ],
}


def derive(category, rows):
    """Add the derived columns for a category, refusing anything incoherent."""
    recipe = DERIVATIONS.get(category, [])
    for row in rows:
        v = row['values']
        for name, formula in recipe:
            v[name] = formula(v)
        if recipe and category == 'RECEIVING':
            if not 0 <= v['AIR YDS'] <= v['YARDS']:
                raise ValueError(f'{category} {row["name"]}: air yards outside 0..YARDS')
            if v['RAC'] + v['AIR YDS'] != v['YARDS']:
                raise ValueError(f'{category} {row["name"]}: air yards and RAC do not sum to YARDS')
    return [name for name, _ in recipe]


def apply(data, sources):
    leaders = data['playerLeaders']
    for source in sources:
        category = source['category']
        if category not in leaders:
            raise ValueError(f'{category} is not a category in DATA.')
        added = {name for name, _ in DERIVATIONS.get(category, [])}
        transcribed = [c for c in leaders[category]['columns'] if c not in added]
        if transcribed != source['columns']:
            raise ValueError(f'{category} columns no longer match DATA.')
        check_identities(source)
        leaders[category]['rows'] = [
            {'name': r['name'], 'pos': r['pos'], 'team': r['team'], 'values': dict(r['values'])}
            for r in source['rows']]
        derived = derive(category, leaders[category]['rows'])
        leaders[category]['columns'] = list(source['columns']) + derived
        if derived:
            leaders[category]['derived'] = derived
        else:
            leaders[category].pop('derived', None)
    data['leaderDepth'] = {k: len(v['rows']) for k, v in leaders.items()}
    # a category is complete only when its capture reaches the end of the list
    complete = {s['category']: bool(s['complete']) for s in sources}
    data['leaderComplete'] = {k: complete.get(k, False) for k in leaders}
    return data


def load_sources():
    return [json.loads(p.read_text()) for p in sorted(LEADERS.glob('*.json'))]


def main():
    from build_season import main as build_main
    build_main()


if __name__ == '__main__':
    main()
