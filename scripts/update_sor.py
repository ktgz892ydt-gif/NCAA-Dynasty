"""Build estimated Strength of Record using a shared Top-25 SRS benchmark."""
import argparse
import copy
import json
import math
from reconcile_2026 import read_site
from update_sos import ROOT, update_sos


def logistic(x):
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


def fit_slope(samples):
    """No-intercept logistic MLE: equal ratings at neutral sites imply 50%."""
    def gradient(beta):
        return math.fsum(x * (y - logistic(beta * x)) for x, y in samples)
    if not samples or gradient(0) <= 0:
        raise ValueError('Results do not support a positive SRS probability slope.')
    low, high = 0., 1.
    while gradient(high) > 0 and high < 1024:
        high *= 2
    if gradient(high) > 0:
        raise ValueError('No finite probability fit; inspect separated results.')
    for _ in range(90):
        mid = (low + high) / 2
        if gradient(mid) > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def record_tail(probabilities, wins):
    """Exact Poisson-binomial probability of at least wins; no simulation."""
    if not 0 <= wins <= len(probabilities):
        raise ValueError('Wins must be within the played schedule.')
    if any(not 0 <= p <= 1 for p in probabilities):
        raise ValueError('Invalid game probability.')
    if wins == 0:
        return 1.
    distribution = [1.]
    for p in probabilities:
        nxt = [0.] * (len(distribution) + 1)
        for k, mass in enumerate(distribution):
            nxt[k] += mass * (1-p)
            nxt[k+1] += mass * p
        distribution = nxt
    return min(1., math.fsum(distribution[wins:]))


def update_sor(data, source):
    # Reuse checksum/season/rating validation without changing existing SOS or other fields.
    update_sos(copy.deepcopy(data), source)
    ratings = source['ratings']
    eligible = sorted(r['t'] for r in data['ratings'] if not r['syn'])
    if len(eligible) < 25:
        raise ValueError('At least 25 FBS teams are needed for the benchmark.')
    benchmark = math.fsum(sorted((ratings[t] for t in eligible), reverse=True)[:25]) / 25
    hfa = data['params']['estimated_home_field_advantage']
    samples = []
    for g in data['scoreboard']:
        if g['as'] == g['hs']:
            raise ValueError('Tied games need an explicit SOR policy.')
        samples.append((ratings[g['h']] - ratings[g['a']] + (0 if g['n'] else hfa), int(g['hs'] > g['as'])))
    beta = fit_slope(samples)
    schedules = {t: [] for t in eligible}
    wins = dict.fromkeys(eligible, 0)
    for g in data['scoreboard']:
        for team, opponent, location, won in [(g['h'], g['a'], 1, g['hs'] > g['as']), (g['a'], g['h'], -1, g['as'] > g['hs'])]:
            if team in schedules:
                schedules[team].append(logistic(beta * (benchmark - ratings[opponent] + (0 if g['n'] else location*hfa))))
                wins[team] += int(won)
    for row in data['ratings']:
        t = row['t']
        if t in schedules and (len(schedules[t]) != row['g'] or wins[t] != row['w']):
            raise ValueError('Scoreboard and FBS records disagree: ' + t)
    tails = {t: record_tail(schedules[t], wins[t]) for t in eligible}
    # Round only for tie comparison to avoid numerical noise assigning different ranks.
    keys = {t: round(tails[t], 12) for t in eligible}
    ranks = {t: 1 + sum(keys[o] < keys[t] for o in eligible) for t in eligible}
    for row in data['ratings']:
        row['sor'] = ranks.get(row['t'])
    for team in data['teams']:
        rank = ranks[data['canon'][team]]
        data['values'][team]['sor'] = {'v': rank, 'rank': rank, 'of': len(eligible)}
    data['statMeta'] = [m for m in data['statMeta'] if m['key'] != 'sor']
    position = next(i for i,m in enumerate(data['statMeta']) if m['key']=='sos') + 1
    data['statMeta'].insert(position, {'key':'sor','name':'SOR','group':'Results','fmt':'rank','higherBetter':False,'pick':'SOR · Strength of Record'})
    data['nationalLeaders']['sor'] = [{'t':t,'v':ranks[t]} for t in sorted(eligible,key=lambda t:(keys[t],t))[:10]]
    # Leave-one-week-out slope checks retain final-season ratings: diagnostic, NOT forecast validation.
    checks = []
    for week in sorted(set(g['wk'] for g in data['scoreboard'])):
        slope = fit_slope([s for s,g in zip(samples,data['scoreboard']) if g['wk'] != week])
        checks.extend((logistic(slope*x)-y)**2 for (x,y),g in zip(samples,data['scoreboard']) if g['wk']==week)
    data['sorMethod'] = {
        'method':'Estimated Strength of Record; lower benchmark match-or-exceed probability ranks better',
        'benchmark':'Mean full-precision SRS of the top 25 FBS teams; shared across every schedule',
        'benchmark_srs':benchmark, 'logistic_slope':beta, 'home_field_points':hfa,
        'ranked_teams':len(eligible), 'fit_games':len(samples),
        'brier_score':math.fsum((logistic(beta*x)-y)**2 for x,y in samples)/len(samples),
        'week_held_out_slope_brier':math.fsum(checks)/len(checks),
        'validation_caveat':'Final-season SRS is used throughout; fit diagnostics are not independent predictive validation.',
        'assumptions':'Independent games; fixed team strength; actual played schedules including repeats and synthetic FCS opponents. Synthetic buckets are not ranked. Ties rejected. Zero wins gives probability 1. Competition ranks compare probabilities rounded to 12 decimals.',
        'source':'data/srs-2026.json and DATA.scoreboard',
        'teams':{t:{'games':len(schedules[t]),'wins':wins[t],'match_probability':tails[t],'rank':ranks[t]} for t in eligible},
    }
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'index.html'
    html, start, length, data = read_site(path)
    update_sor(data, json.loads((ROOT / 'data/srs-2026.json').read_text()))
    updated = html[:start] + json.dumps(data,ensure_ascii=False,separators=(',',':')) + html[start+length:]
    if args.check:
        if html != updated:
            raise SystemExit('SOR is stale. Run python3 -B scripts/update_sor.py')
        print('Estimated SOR is current.')
    else:
        path.write_text(updated)
        print(json.dumps({t:data['values'][t]['sor'] for t in data['teams']}))
        print('Model diagnostics:',data['sorMethod']['benchmark_srs'],data['sorMethod']['logistic_slope'],data['sorMethod']['brier_score'],data['sorMethod']['week_held_out_slope_brier'])


if __name__ == '__main__':
    main()
