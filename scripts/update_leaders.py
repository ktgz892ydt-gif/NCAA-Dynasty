"""Write the transcribed national player leaderboards into the self-contained site.

Each category that has been read from its recording or photo set lives in
data/leaders-2026/<CATEGORY>.json, carrying its own columns, provenance and the
arithmetic identities the screen itself prints. Categories with no file keep
whatever DATA already holds - the single screenful the first pass captured.
"""
import argparse
import json
from pathlib import Path
from reconcile_2026 import ROOT, read_site

LEADERS = ROOT / 'data/leaders-2026'


def check_identities(source):
    """Re-derive every relationship the screen prints, on every row."""
    rows, sorted_by = source['rows'], source['sortedBy']
    previous = None
    for i, row in enumerate(rows, 1):
        v = row['values']
        for rule in source.get('identities', []):
            if 'sum' in rule:
                a, b, total = rule['sum']
                if v[a] + v[b] != v[total]:
                    raise ValueError(f'{source["category"]} row {i} ({row["name"]}): '
                                     f'{a} plus {b} is not {total}')
            if 'quotient' in rule:
                num, den, quot = rule['quotient']
                if v[den] and abs(v[num] / v[den] - v[quot]) > rule.get('tolerance', 0.051):
                    raise ValueError(f'{source["category"]} row {i} ({row["name"]}): '
                                     f'{num} over {den} is not {quot}')
        value = v[sorted_by]
        if previous is not None and value > previous:
            raise ValueError(f'{source["category"]} row {i} ({row["name"]}): '
                             f'the list is sorted by {sorted_by} descending')
        previous = value


def apply(data, sources):
    leaders = data['playerLeaders']
    for source in sources:
        category = source['category']
        if category not in leaders:
            raise ValueError(f'{category} is not a category in DATA.')
        if leaders[category]['columns'] != source['columns']:
            raise ValueError(f'{category} columns no longer match DATA.')
        check_identities(source)
        leaders[category]['rows'] = [
            {'name': r['name'], 'pos': r['pos'], 'team': r['team'], 'values': r['values']}
            for r in source['rows']]
    data['leaderDepth'] = {k: len(v['rows']) for k, v in leaders.items()}
    # a category is complete only when its capture reaches the end of the list
    complete = {s['category']: bool(s['complete']) for s in sources}
    data['leaderComplete'] = {k: complete.get(k, False) for k in leaders}
    return data


def load_sources():
    return [json.loads(p.read_text()) for p in sorted(LEADERS.glob('*.json'))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if the site needs regeneration')
    args = parser.parse_args()
    path = ROOT / 'index.html'
    html, start, length, data = read_site(path)
    updated = apply(data, load_sources())
    text = html[:start] + json.dumps(updated, ensure_ascii=False, separators=(',', ':')) + html[start+length:]
    if args.check:
        if text != html:
            raise SystemExit('Player leaderboards are stale; run python3 scripts/update_leaders.py')
        print('Player leaderboards are current.')
    else:
        path.write_text(text)
        depth = updated['leaderDepth']
        print('Wrote ' + ', '.join(f'{k} {depth[k]}' for k in sorted(depth)) + ' into index.html.')


if __name__ == '__main__':
    main()
