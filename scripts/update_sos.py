"""Build points-based SOS from the national scoreboard and full-precision SRS."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def scoreboard_hash(games):
    return hashlib.sha256(json.dumps(games, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def opponent_averages(games, ratings):
    opponents = {team: [] for team in ratings}
    for game in games:
        away, home = game['a'], game['h']
        if away not in ratings or home not in ratings:
            raise ValueError('Every opponent must have an SRS rating.')
        opponents[away].append(ratings[home])
        opponents[home].append(ratings[away])
    if any(not values for values in opponents.values()):
        raise ValueError('Every rated team must have at least one game.')
    return {team: math.fsum(values) / len(values) for team, values in opponents.items()}


def update_sos(data, source):
    if str(data['season']) != str(source['season']):
        raise ValueError('SRS input season does not match the site.')
    if scoreboard_hash(data['scoreboard']) != source['scoreboard_sha256']:
        raise ValueError('Scoreboard changed; refresh the full-precision SRS inputs before rebuilding SOS.')
    ratings = source['ratings']
    if set(ratings) != {r['t'] for r in data['ratings']}:
        raise ValueError('SRS inputs must cover the entire rated field.')
    for row in data['ratings']:
        value = ratings[row['t']]
        if not math.isfinite(value) or abs(value - row['srs']) > .005001:
            raise ValueError('Full-precision SRS inputs do not match the displayed ratings.')
    scores = opponent_averages(data['scoreboard'], ratings)
    eligible = {row['t'] for row in data['ratings'] if not row['syn']}
    ranks = {team: 1 + sum(scores[other] > scores[team] for other in eligible) for team in eligible}
    for row in data['ratings']:
        row['sos'] = scores[row['t']]
    for team in data['teams']:
        name = data['canon'][team]
        data['values'][team]['sos'] = {'v': scores[name], 'rank': ranks[name], 'of': len(eligible)}
    for meta in data['statMeta']:
        if meta['key'] == 'sos':
            meta['fmt'] = 'signed2'
    leaders = sorted(eligible, key=lambda team: (-scores[team], team))[:10]
    data['nationalLeaders']['sos'] = [{'t': team, 'v': scores[team]} for team in leaders]
    data['sosMethod'] = {
        'method': 'Mean opponent SRS per scheduled game', 'units': 'points',
        'rated_teams': len(ratings), 'ranked_teams': len(eligible),
        'opponents': 'Includes synthetic FCS buckets using their calculated SRS; repeated opponents count once per game.',
        'source': source.get('source_path', 'data/srs-2026.json'),
    }
    return data


def main():
    from build_season import main as build_main
    build_main()


if __name__ == '__main__':
    main()
