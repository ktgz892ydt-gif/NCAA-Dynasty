"""Season storage and strict, atomic JSON I/O."""
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def season_dir(season, root=ROOT):
    if not re.fullmatch(r'\d{4}', str(season)):
        raise ValueError('Season must be a four-digit year.')
    return Path(root) / 'data/seasons' / str(season)


def read(path):
    def invalid(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    return json.loads(Path(path).read_text(), parse_constant=invalid)


def serialized(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = serialized(value)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def input_digest(folder, root):
    files = [p for p in folder.rglob('*') if p.is_file() and p.name != 'season.json']
    files += list((Path(root)/'config').rglob('*.json'))
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def validate_games(games, synthetic=()):
    seen, appearances = set(), set()
    for g in games:
        for key in ['wk','a','h','as','hs','n']:
            if key not in g: raise ValueError(f'Missing scoreboard field: {key}')
        if not isinstance(g['wk'], int) or isinstance(g['wk'], bool) or g['wk'] < 0:
            raise ValueError('Game week must be a nonnegative integer.')
        if not all(isinstance(g[k], str) and g[k].strip() for k in ['a','h']) or g['a']==g['h']:
            raise ValueError('Games must identify two different teams.')
        if not isinstance(g['n'], bool): raise ValueError('Neutral flag must be boolean.')
        if any(not isinstance(g[k], (int,float)) or isinstance(g[k],bool) or not math.isfinite(g[k]) or g[k]<0 or g[k]!=int(g[k]) for k in ['as','hs']):
            raise ValueError('Scores must be finite, nonnegative integers.')
        if g['as']==g['hs']: raise ValueError('Tied games are not supported.')
        key=(g['wk'],*sorted([g['a'],g['h']]))
        if key in seen: raise ValueError(f'Duplicate or conflicting game: {key}')
        seen.add(key)
        for team in [g['a'],g['h']]:
            mark=(g['wk'],team)
            if mark in appearances and team not in synthetic:
                raise ValueError(f'Multiple games in one week for {team}; verify week identifiers.')
            appearances.add(mark)


def validate_output(d):
    if d.get('schemaVersion') != 1: raise ValueError('Unsupported data schema.')
    if d['metadata']['id'] != str(d['season']): raise ValueError('Season metadata mismatch.')
    validate_games(d['scoreboard'],d['metadata']['syntheticTeams'])
    names=[r['t'] for r in d['ratings']]
    if len(set(names))!=len(names):raise ValueError('Duplicate rated team.')
    if any(g[k] not in names for g in d['scoreboard'] for k in ['a','h']):raise ValueError('Unrated opponent.')
    for t in d['teams']:
        if t not in d['values'] or t not in d['schedules']:raise ValueError('Missing dynasty team data.')
        for m in d['statMeta']:
            cell=d['values'][t].get(m['key'])
            if cell is None:raise ValueError(f'Missing metric cell: {t} {m["key"]}')
            if cell.get('rank') is not None and not (cell.get('of') and 1<=cell['rank']<=cell['of']):
                raise ValueError(f'Invalid rank: {t} {m["key"]}')
    for r in d['ratings']:
        if r['syn']:continue
        gs=[g for g in d['scoreboard'] if r['t'] in (g['a'],g['h'])]
        wins=sum(g['as']>g['hs'] if g['a']==r['t'] else g['hs']>g['as'] for g in gs)
        if (r['g'],r['w'],r['l'])!=(len(gs),wins,len(gs)-wins):raise ValueError(f'Record mismatch: {r["t"]}')
    serialized(d)  # Reject non-finite values anywhere in the payload.
