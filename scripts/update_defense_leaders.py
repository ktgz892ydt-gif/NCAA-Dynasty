"""Write the full national DEFENSE leaderboard into the self-contained site.

The other player-leader categories in DATA hold a single screenful, because that
is all the earlier pass transcribed. This one is the complete list: IMG_5215.MOV
scrolls the national DEFENSE leaderboard from the first row to the last, and the
400 players it shows are stored in data/defense-leaders-2026.json.
"""
import argparse
import json
from reconcile_2026 import ROOT, read_site


def check_invariants(rows):
    """The screen gives three independent arithmetic identities; use all of them."""
    previous = None
    for i, row in enumerate(rows, 1):
        v = row['values']
        if v['SOLO'] + v['ASSISTS'] != v['TAK']:
            raise ValueError(f'row {i} ({row["name"]}): solo plus assists is not total tackles')
        if previous is not None and v['TAK'] > previous:
            raise ValueError(f'row {i} ({row["name"]}): the list is sorted by tackles descending')
        previous = v['TAK']
        if v['INT'] and abs(v['INT YDS'] / v['INT'] - v['INT AVG']) > 0.06:
            raise ValueError(f'row {i} ({row["name"]}): interception yards do not match the average')


def apply(data, source):
    leaders = data['playerLeaders']['DEFENSE']
    if leaders['columns'] != source['columns']:
        raise ValueError('The stored columns no longer match the leaderboard in DATA.')
    rows = [{'name': r['name'], 'pos': r['pos'], 'team': r['team'], 'values': r['values']}
            for r in source['rows']]
    check_invariants(rows)
    leaders['rows'] = rows
    data['leaderDepth'] = {k: len(v['rows']) for k, v in data['playerLeaders'].items()}
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if the site needs regeneration')
    args = parser.parse_args()
    path = ROOT / 'index.html'
    html, start, length, data = read_site(path)
    source = json.loads((ROOT / 'data/defense-leaders-2026.json').read_text())
    updated = apply(data, source)
    text = html[:start] + json.dumps(updated, ensure_ascii=False, separators=(',', ':')) + html[start+length:]
    if args.check:
        if text != html:
            raise SystemExit('Defense leaderboard is stale; run python3 scripts/update_defense_leaders.py')
        print('Defense leaderboard is current.')
    else:
        path.write_text(text)
        print(f'Wrote {len(updated["playerLeaders"]["DEFENSE"]["rows"])} DEFENSE rows into index.html.')


if __name__ == '__main__':
    main()
