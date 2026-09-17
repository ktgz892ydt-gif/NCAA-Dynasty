"""Opponent-adjusted offensive and defensive efficiency for every rated team.

The KenPom structure, applied to football. A team's offence is rated by the
points it scored against the defences it actually faced, its defence by the
points it allowed to the offences it actually faced, and the two are solved
together because each depends on the other:

    points scored  =  mu + offence(scoring team) + defence(conceding team)
                          + home field, when the scoring team is at home

Every game supplies two observations, one per side, so the 888-game scoreboard
gives 1,776 equations for 287 free parameters. Home-field advantage is not
re-estimated here: it is taken from the ratings export, so this decomposition
and the SRS already in DATA rest on the same figure and can be compared.

What is deliberately absent is pace. KenPom divides by possessions because
basketball tempo ranges over about a quarter of its own value; football drives
cluster far tighter, and a league-wide drive count cannot be built from the
source set at all, since no national screen carries punts or field-goal
attempts. These ratings are therefore per game, and say so.
"""
import argparse
import json
from season_io import ROOT


def observations(data):
    """Two rows per game: points, the scoring team, the conceding team, home."""
    rows = []
    for game in data['scoreboard']:
        at_home = 0 if game['n'] else 1
        rows.append((game['hs'], game['h'], game['a'], at_home))
        rows.append((game['as'], game['a'], game['h'], 0))
    return rows


def solve(rows, teams, home_field, tolerance=1e-13, limit=1000):
    """Alternating least squares: hold one side fixed, solve the other, repeat.

    Each sweep is exact for the side being updated, so this is Gauss-Seidel on
    the normal equations and converges monotonically. Offence and defence are
    recentred on zero every sweep and the level kept in mu, which fixes the
    two-dimensional null space the model would otherwise have.
    """
    position = {team: i for i, team in enumerate(teams)}
    n = len(teams)
    scored, conceded = [[] for _ in range(n)], [[] for _ in range(n)]
    for k, (_, offence, defence, _) in enumerate(rows):
        scored[position[offence]].append(k)
        conceded[position[defence]].append(k)

    offence, defence = [0.0] * n, [0.0] * n
    mu = sum(r[0] for r in rows) / len(rows)
    for sweep in range(1, limit + 1):
        moved = 0.0
        for i in range(n):
            games = scored[i]
            if not games:
                continue
            value = sum(rows[k][0] - mu - defence[position[rows[k][2]]] - home_field * rows[k][3]
                        for k in games) / len(games)
            moved = max(moved, abs(value - offence[i]))
            offence[i] = value
        for i in range(n):
            games = conceded[i]
            if not games:
                continue
            value = sum(rows[k][0] - mu - offence[position[rows[k][1]]] - home_field * rows[k][3]
                        for k in games) / len(games)
            moved = max(moved, abs(value - defence[i]))
            defence[i] = value
        off_mean, def_mean = sum(offence) / n, sum(defence) / n
        offence = [v - off_mean for v in offence]
        defence = [v - def_mean for v in defence]
        mu += off_mean + def_mean
        if moved < tolerance:
            break
    return mu, offence, defence, sweep


def residual_rmse(rows, teams, mu, offence, defence, home_field):
    position = {team: i for i, team in enumerate(teams)}
    total = 0.0
    for points, off, deff, at_home in rows:
        fitted = mu + offence[position[off]] + defence[position[deff]] + home_field * at_home
        total += (points - fitted) ** 2
    return (total / len(rows)) ** 0.5


def rank_all(values, eligible, higher_is_better):
    """Competition ranks over the real FBS teams, ties sharing a place."""
    ranks = {}
    for team in eligible:
        better = sum((values[o] > values[team]) if higher_is_better else (values[o] < values[team])
                     for o in eligible)
        ranks[team] = 1 + better
    return ranks


STATS = [
    ('adjo', 'AdjO', 'Adjusted Offense', True, 'num1'),
    ('adjd', 'AdjD', 'Adjusted Defense', False, 'num1'),
    ('adjem', 'AdjEM', 'Adjusted Efficiency Margin', True, 'signed2'),
]
SHOWN = [s for s in STATS if s[0] != 'adjem']


def update_efficiency(data):
    teams = [row['t'] for row in data['ratings']]
    home_field = data['params']['estimated_home_field_advantage']
    rows = observations(data)
    mu, offence, defence, sweeps = solve(rows, teams, home_field)
    position = {team: i for i, team in enumerate(teams)}

    value = {'adjo': {}, 'adjd': {}, 'adjem': {}}
    for team in teams:
        i = position[team]
        value['adjo'][team] = mu + offence[i]
        value['adjd'][team] = mu + defence[i]
        value['adjem'][team] = offence[i] - defence[i]

    eligible = [row['t'] for row in data['ratings'] if not row['syn']]
    for row in data['ratings']:
        for key, _, _, _, _ in STATS:
            row[key] = value[key][row['t']]

    for key, _, _, higher, _ in STATS:
        ranks = rank_all(value[key], eligible, higher)
        if key == 'adjem':
            for short in data['teams']:
                data['values'][short][key] = {'v': value[key][data['canon'][short]],
                                              'rank': ranks.get(data['canon'][short]),
                                              'of': len(eligible)}
            continue
        for short in data['teams']:
            full = data['canon'][short]
            data['values'][short][key] = {'v': value[key][full],
                                          'rank': ranks.get(full), 'of': len(eligible)}
        ordered = sorted(eligible, key=lambda t: (-value[key][t] if higher else value[key][t], t))
        data['nationalLeaders'][key] = [{'t': t, 'v': value[key][t]} for t in ordered[:10]]

    # Only the two halves become stat rows. The margin is not surfaced separately
    # because AdjO - AdjD is exactly SRS, which the site already carries: showing
    # both would print one number twice under two names. It stays on the ratings
    # rows, where the agreement with SRS is the check that the solve is right.
    data['statMeta'] = [m for m in data['statMeta'] if m['key'] not in value]
    data['nationalLeaders'].pop('adjem', None)
    at = next(i for i, m in enumerate(data['statMeta']) if m['key'] == 'mov') + 1
    for offset, (key, short, name, higher, fmt) in enumerate(SHOWN):
        data['statMeta'].insert(at + offset, {
            'group': 'Results', 'name': name, 'key': key, 'fmt': fmt,
            'higherBetter': higher, 'pick': f'{short} · {name}'})

    data['effMethod'] = {
        'model': 'points scored = mu + offence + defence + home field',
        'observations': len(rows),
        'teams_rated': len(teams),
        'ranked_teams': len(eligible),
        'league_average_points_per_game': mu,
        'home_field_advantage': home_field,
        'home_field_source': 'Taken from the ratings export, not re-estimated, so this '
                             'decomposition and the published SRS rest on the same figure.',
        'solver': 'Alternating least squares (Gauss-Seidel on the normal equations), '
                  'offence and defence recentred on zero each sweep',
        'sweeps': sweeps,
        'residual_rmse': residual_rmse(rows, teams, mu, offence, defence, home_field),
        'pace': 'Per game, not per drive. No national screen carries punts or field-goal '
                'attempts, so a league-wide drive count cannot be built from the source set. '
                'Football drives also vary far less than basketball possessions: the three '
                'dynasty schools run 10.4 to 11.8 a game.',
    }
    return data


def main():
    from build_season import main as build_main
    build_main()


if __name__ == '__main__':
    main()
