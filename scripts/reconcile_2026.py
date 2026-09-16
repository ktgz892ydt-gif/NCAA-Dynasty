"""Recompute audited 2026 fields in the self-contained site (Python standard library).

This is a targeted reconciliation, not a complete photo/ratings ingestion pipeline.
The remaining DATA fields and national leaderboard baselines are preserved.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_site(path):
    html = path.read_text()
    start = html.index('const DATA = ') + len('const DATA = ')
    data, length = json.JSONDecoder().raw_decode(html[start:])
    return html, start, length, data


def reconcile(d, source):
    if str(d['season']) != '2026':
        raise ValueError('This reconciliation applies only to the 2026 source set.')
    values, notes = d['values'], d['avNotes']
    first, rest = source['eastern_first_game'], source['eastern_other_games']
    games = source['season_games']

    def put(team, key, value, **meta):
        values[team][key] = {'v': value, 'rank': None, 'of': None, **meta}

    recovered = ('Includes the retained Sacramento State Game Log entry; '
                 'the lower statistics photo for that game is unavailable.')
    for key, field in [('punts', 'punts'), ('kr', 'kick_return_yards'), ('pr', 'punt_return_yards')]:
        put('E. Michigan', key, first[field] + rest[field], note=recovered)
    top = (first['possession_seconds'] + rest['possession_seconds']) / games
    put('E. Michigan', 'toppg', top, note=recovered)
    emu = values['E. Michigan']
    put('E. Michigan', 'bci', .5 * top / source['regulation_game_seconds']
        + .3 * emu['fd']['v'] / emu['plays']['v'] - .2 * emu['torate']['v'], note=recovered)
    put('E. Michigan', 'puntyds', rest['punt_yards'], partial=rest['games'],
        note='Punt yards cover 11 games; Sacramento State punt yardage is unavailable.')
    put('E. Michigan', 'ypunt', rest['punt_yards'] / rest['punts'], partial=rest['games'],
        note='969 yards / 21 punts over the same 11 games; excludes Sacramento State.')
    for key in ['punts', 'kr', 'pr', 'top']:
        d['boxCoverage']['E. Michigan'].pop(key, None)

    # Eastern's punter is identified by his punt count alone, so the two independent
    # routes to that number - eleven photographed box scores plus the retained Game
    # Log entry, and his own season line - have to agree. If an input edit breaks
    # that equality the identification no longer holds and the build must stop.
    derived_punts = {'E. Michigan': first['punts'] + rest['punts']}
    for team, punter in source['punters'].items():
        if team in derived_punts and derived_punts[team] != punter['punts']:
            raise ValueError(
                f"{team} punt count disagrees: {derived_punts[team]} from the box scores "
                f"and Game Log against {punter['punts']} on {punter['name']}'s season line. "
                'That equality is what assigns the punter to the school.')
        put(team, 'punts', punter['punts'])
        put(team, 'puntyds', punter['yards'])
        put(team, 'ypunt', punter['yards'] / punter['punts'])
        full = d['full'][team]
        notes[full]['punter_adj_ypa'] = ((punter['yards'] - 13 * punter['blocked'])
                                       / (punter['punts'] + punter['blocked']))
        # A named punter's season line covers every game, so the partial-coverage
        # marker set above for Eastern no longer applies.
        d['boxCoverage'][team].pop('puntyds', None)

    # Full-season offensive inputs must have the same game coverage.
    for team in d['teams']:
        v = values[team]
        inp = notes['inputs'][d['full'][team]]
        inp['punts'] = v['punts']['v']
        inp['punts_games'] = games
        n = notes[d['full'][team]]
        # One drive definition, the estimate documented in calculations.md, used for
        # offensive rate, Explosiveness and the defence alike. The earlier AV
        # offensive count omitted failed fourth downs and end-of-half possessions
        # and came out near nine drives a game, well under a real twelve.
        drives = (v['ttd']['v'] + inp['fga'] + inp['punts'] + inp['turnovers']
                  + v['d4a']['v'] - v['d4c']['v'] + 2 * games)
        n['drives'] = drives
        n['off_pts_per_drive'] = (7 * (inp['rtd'] + inp['ptd']) + 3 * inp['fgm']) / drives
        # Possessions alternate, so a defence faces its own offence's drive count to
        # within a possession a game. Deriving it that way removes the opponent
        # field-goal estimate, which ran up to 1.7x the national attempt rate because
        # it charged every non-offensive touchdown allowed to phantom field goals.
        n['def_drives'] = drives
        inp.pop('opp_fga', None)
        inp.pop('opp_fgm_est', None)
        put(team, 'explo', v['ypp']['v'] * v['pts']['v'] / drives, estimate=True,
            note='Uses estimated drives from offensive TDs, FGA, punts, turnovers, '
                 'failed fourth downs and two end-of-half possessions per game.'
                 + (' ' + recovered if team == 'E. Michigan' else ''))

    league = notes['league']
    league['off_ppd'] = sum(notes[d['full'][t]]['off_pts_per_drive'] for t in d['teams']) / len(d['teams'])
    league['def_ppd'] = sum(notes['inputs'][d['full'][t]]['pts_allowed']
                            / notes[d['full'][t]]['def_drives'] for t in d['teams']) / len(d['teams'])
    baseline_note = ('Three-team offensive baseline includes Eastern\u2019s retained '
                     'first-game workbook punts; see source notes.')
    defense_note = ('Defensive drives equal the team\u2019s own estimated drive count, since '
                    'possessions alternate. That removes the earlier opponent field-goal '
                    'estimate, and with it any dependence on opponent punts or takeaways, '
                    'so Eastern\u2019s 11-game opponent-punt total and Central\u2019s '
                    '21-versus-20 takeaway discrepancy no longer reach this figure. The drive '
                    'count itself is still an estimate and the baseline is the three schools.')
    for team in d['teams']:
        n, v = notes[d['full'][team]], values[team]
        offense = 100 * n['off_pts_per_drive'] / league['off_ppd']
        line = offense * 5 / 11
        skill = offense - line
        rush = skill * .22 * v['ryds']['v'] / (v['ryds']['v'] + v['pyds']['v']) / .37
        passing = (skill - rush) * .26
        for key, value in [('av_team_off', offense), ('av_oline_pool', line),
                           ('av_skill_pool', skill), ('av_rush_pool', rush),
                           ('av_pass_pool', passing), ('av_rec_pool', (skill - rush) * .74)]:
            put(team, key, value, note=baseline_note)
        qb = n['qb1']
        delta = qb['aya'] - league['aya']
        adjustment = (delta * (.5 if delta > 0 else 2)) if qb['att'] >= 150 else 0
        put(team, 'av_qb1', passing * qb['yards'] / v['pyds']['v'] + adjustment, note=baseline_note)
        margin = (notes['inputs'][d['full'][team]]['pts_allowed']
                  / n['def_drives']) / league['def_ppd']
        defense = 100 * (1 + 2 * margin - margin ** 2) / (2 * margin)
        for key, value in [('av_team_def', defense), ('av_front7_pool', defense * 2 / 3),
                           ('av_secondary_pool', defense / 3)]:
            put(team, key, value, estimate=True, note=defense_note)
        if team in source['punters']:
            punter = source['punters'][team]
            above = (punter['punts'] + punter['blocked']) * (n['punter_adj_ypa'] - league['punt_adj'])
            put(team, 'av_punter', 2.1875 + 16 * above / (200 * games))

    # Master treats these as user-entered; no screen in the source set records them.
    entered = source.get('user_entered', {})
    for key, by_team in entered.items():
        for team, value in by_team.items():
            put(team, key, value, note=source.get('user_entered_source'))

    # Individual player slots the game never supplies. Apportioning a position pool
    # to one player needs Games Started, which NCAA 26 reports on no screen: the
    # passing, rushing, receiving, blocking, defensive, kicking and punting screens
    # all show games played and snaps only. Drop those rows rather than carry a
    # column of blanks. Anything the source set does identify - the quarterback
    # room, the kicker, the punters - keeps its row.
    unsupported = [m['key'] for m in d['statMeta'] if m['key'].startswith('av_')
                   and all(values[t].get(m['key'], {}).get('v') is None for t in d['teams'])]
    d['statMeta'] = [m for m in d['statMeta'] if m['key'] not in unsupported]
    for team in d['teams']:
        for key in unsupported:
            values[team].pop(key, None)
    # Union, so a rebuild of an already-pruned site keeps the record.
    notes['dropped_player_rows'] = sorted(set(notes.get('dropped_player_rows', [])) | set(unsupported))

    # These four already head every team's summary card, so the stat table does not
    # repeat them. They stay in DATA, in the national tables and in the
    # head-to-head measure picker.
    for meta in d['statMeta']:
        if meta['key'] in ['sos', 'sor', 'srs', 'mov']:
            meta['hide'] = True
        else:
            meta.pop('hide', None)

    values['C. Michigan']['todiff']['note'] = (
        'Uses the season screen\u2019s 21 takeaways minus 19 giveaways. '
        'Its components sum to 20 takeaways; the source discrepancy remains unresolved.')
    d['missingRows'] = [{'group': m['group'], 'name': m['name']} for m in d['statMeta']
                        if not m.get('hide')
                        and all(values[t][m['key']]['v'] is None for t in d['teams'])]
    notes['status'] = 'computed_with_estimates'
    notes['source_review'] = 'See data/verified-inputs-2026.json and data/SOURCE_NOTES.md.'
    return d


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if the site needs regeneration')
    args = parser.parse_args()
    path = ROOT / 'index.html'
    html, start, length, data = read_site(path)
    source = json.loads((ROOT / 'data/verified-inputs-2026.json').read_text())
    updated = reconcile(data, source)
    text = html[:start] + json.dumps(updated, ensure_ascii=False, separators=(',', ':')) + html[start+length:]
    if args.check:
        if text != html:
            raise SystemExit('Audited calculations are stale; run python3 scripts/reconcile_2026.py')
        print('Audited calculations are current.')
    else:
        path.write_text(text)
        print('Updated audited calculations in index.html.')


if __name__ == '__main__':
    main()
