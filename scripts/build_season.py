"""Build one season from inputs; generated files are never used as inputs."""
import argparse
import copy
from pathlib import Path
from season_io import ROOT, read, season_dir, serialized, atomic_write, input_digest, validate_games, validate_output
from calculations.national import calculate
from update_sos import update_sos, scoreboard_hash
from update_sor import update_sor
from update_efficiency import update_efficiency
from update_leaders import apply as update_leaders
from reconcile_2026 import reconcile


def blank():return {'v':None,'rank':None,'of':None}


def new_dataset(meta, teams, metrics, stats, games):
    shorts=[t['short'] for t in teams]
    values={t:{m['key']:blank() for m in metrics} for t in shorts}
    for t,cells in stats.items():
        if t not in values:raise ValueError('Unknown dynasty team in team-stats: '+t)
        for key,cell in cells.items():
            if key not in values[t]:raise ValueError('Unknown metric: '+key)
            if not isinstance(cell,dict) or 'v' not in cell:raise ValueError('Metric input must be a value cell.')
            values[t][key]={**blank(),**cell}
    return {'season':meta['id'],'teams':shorts,'full':{t['short']:t['name'] for t in teams},
            'canon':{t['short']:t['canonical'] for t in teams},'statMeta':metrics,'values':values,
            'scoreboard':games,'schedules':{t:[] for t in shorts},'ratings':[],'nationalLeaders':{},
            'params':{},'avNotes':{'status':'unavailable','dropped_player_rows':[]},'specialists':{},'qbRoom':{},
            'boxCoverage':{t:{} for t in shorts},'coverage':{},'missingRows':[],'playerLeaders':{},
            'sorMethod':{'ranked_teams':0,'benchmark_srs':None},'effMethod':{}}


def fill_scoreboard_metrics(d, source, settings):
    eligible=[r for r in d['ratings'] if not r['syn']]
    for t in d['teams']:
        full=d['canon'][t];row=next((r for r in eligible if r['t']==full),None)
        if row is None:continue  # No played games: retain unavailable values.
        def put(k,v,rank=None):d['values'][t][k]={'v':v,'rank':rank,'of':len(eligible) if rank is not None else None}
        put('record',f"{row['w']}-{row['l']}")
        put('winpct',row['w']/row['g'],1+sum(r['w']/r['g']>row['w']/row['g'] for r in eligible))
        for k,field,high in [('pts','pf',True),('ptsa','pa',False),('srs','srs',True)]:
            v=source['ratings'][full] if k=='srs' else row[field]
            scores=[source['ratings'][r['t']] if k=='srs' else r[field] for r in eligible]
            put(k,v,1+sum(x>v if high else x<v for x in scores))
        mov=(row['pf']-row['pa'])/row['g'];put('mov',mov,1+sum((r['pf']-r['pa'])/r['g']>mov for r in eligible))
        e=settings['pythExponent'];den=row['pf']**e+row['pa']**e
        put('pyth',row['g']*row['pf']**e/den if den else None)
        for g in d['scoreboard']:
            if full not in (g['a'],g['h']):continue
            home=g['h']==full;opp=g['a'] if home else g['h'];other=next(r for r in d['ratings'] if r['t']==opp)
            pf,pa=(g['hs'],g['as']) if home else (g['as'],g['hs'])
            d['schedules'][t].append({'wk':g['wk'],'opp':opp,'site':'N' if g['n'] else 'H' if home else 'A','pf':pf,'pa':pa,'w':pf>pa,'ot':g.get('ot',False),'oppRec':f"{other['w']}-{other['l']}",'oppSrs':source['ratings'][opp]})
    for key,field,reverse in [('srs','srs',True),('mov','mov',True),('pts','pf',True),('ptsa','pa',False)]:
        d['nationalLeaders'][key]=[{'t':r['t'],'v':source['ratings'][r['t']] if key=='srs' else r[field]} for r in sorted(eligible,key=lambda r:r[field],reverse=reverse)[:10]]


def build(season, root=ROOT):
    root=Path(root);folder=season_dir(season,root);inp=folder/'inputs'
    meta=read(folder/'metadata.json')
    if meta['id']!=str(season) or meta['schemaVersion']!=1:raise ValueError('Season metadata mismatch.')
    if meta['status'] not in ['draft','in-progress','finalized']:raise ValueError('Invalid season status.')
    if meta['methodVersion']!='v1':raise ValueError('Unknown calculation version; implement and test it before use.')
    settings=read(root/'config/methods/v1.json')
    if settings['id']!='v1' or settings['sorBenchmarkSize']!=25 or settings['seasonCarryover']:
        raise ValueError('Unsupported method settings; use an explicitly versioned implementation.')
    allteams=read(root/'config/teams.json')['teams'];lookup={t['id']:t for t in allteams}
    if len(lookup)!=len(allteams) or len(set(meta['teamIds']))!=len(meta['teamIds']):raise ValueError('Duplicate team identifier.')
    teams=[lookup[i] for i in meta['teamIds']]
    if not teams:raise ValueError('Season must have at least one dynasty team.')
    metrics=read(root/'config/metrics.json');games=read(inp/'scoreboard.json');validate_games(games,meta['syntheticTeams'])
    stats=read(inp/'team-stats.json')
    corrections=read(inp/'corrections.json')
    if corrections['season']!=str(season):raise ValueError('Corrections belong to another season.')
    for patch in corrections['patches']:
        if not patch.get('source'):raise ValueError('Correction requires a source.')
        old=stats[patch['team']][patch['metric']]
        if old!=patch['expected']:raise ValueError('Correction precondition failed.')
        stats[patch['team']][patch['metric']]=patch['replacement']
    legacy=meta['inputMode']=='legacy-2026'
    if meta['inputMode'] not in ['legacy-2026','standard']:raise ValueError('Unknown input mode.')
    if legacy and str(season)!='2026':raise ValueError('Historical corrections are restricted to 2026.')
    if legacy:
        d=read(inp/'legacy-import.json')
        d.update(season=str(season),statMeta=metrics,scoreboard=games,values=stats,playerLeaders=read(inp/'retained-leaders.json'))
        catalog=read(inp/'leader-catalog.json')
        for k,v in catalog.items():d['playerLeaders'].setdefault(k,{**v,'rows':[]})
    else:d=new_dataset(meta,teams,metrics,stats,games)
    reference=read(inp/'srs-reference.json') if legacy else None
    if legacy and reference['scoreboard_sha256']!=scoreboard_hash(games):
        raise ValueError('2026 scoreboard changed: explicitly migrate the archived ratings references before rebuilding.')
    order=read(inp/'rating-game-order.json') if legacy else None
    ratings,params,source=calculate(games,meta,settings,order)
    if legacy:
        byname={r['t']:r for r in ratings}
        for row in d['ratings']:
            for k in ['srs','elo','bt','g2']:
                if row[k]!=byname[row['t']][k]:raise ValueError(f'Archived rating mismatch: {row["t"]} {k}')
        for t,v in reference['ratings'].items():
            if abs(v-source['ratings'][t])>1e-8:raise ValueError('Full precision SRS mismatch.')
        # Preserve historical floating-point values exactly after independently verifying them.
        source=reference
    else:
        d['ratings']=ratings;d['params']=params
        if source:fill_scoreboard_metrics(d,source,settings)
    d['coverage']={**d.get('coverage',{}),'photos':meta['coverage'].get('photos',0),'videos':meta['coverage'].get('videos',0),
                   'games':len(games),'teams':len(ratings),'weeks':sorted({g['wk'] for g in games})}
    if source:
        # Only dynasty teams with games are passed through the existing rating calculators.
        active=[t for t in d['teams'] if d['canon'][t] in source['ratings']]
        allshort=d['teams'];d['teams']=active
        update_sos(d,source)
        eligible=[r for r in ratings if not r['syn']]
        if len(eligible)>=25:
            try:update_sor(d,source)
            except ValueError:
                if meta['status']=='finalized':raise
                d['sorMethod']={'ranked_teams':len(eligible),'benchmark_srs':None,'unavailable':'Insufficient results for a stable probability fit.'}
        update_efficiency(d)
        d['teams']=allshort
    sources=[read(p) for p in sorted((folder/'leaders').glob('*.json'))]
    for s in sources:
        d['playerLeaders'].setdefault(s['category'],{'columns':s['columns'],'sortedBy':s['sortedBy'],'rows':[]})
    update_leaders(d,sources)
    source_by_category={s['category']:s for s in sources}
    d['leaderCoverage']={k:{'recordedRows':len(v['rows']),
        'captureComplete':d['leaderComplete'].get(k,False),
        'nationalComplete':source_by_category.get(k,{}).get('coverage',{}).get('nationalComplete',False),
        'sortedBy':source_by_category.get(k,{}).get('sortedBy',v.get('sortedBy')),
        'scope':source_by_category.get(k,{}).get('screen','Recorded player list'),
        'teams':'Only verified schools are attributed.'} for k,v in d['playerLeaders'].items()}
    if legacy:reconcile(d,read(inp/'verified-corrections.json'))
    else:
        for m in d['statMeta']:m['hide']=m['key'] in ['srs','sos','sor','mov']
    d['missingRows']=[{'group':m['group'],'name':m['name']} for m in d['statMeta'] if not m.get('hide') and all(d['values'][t].get(m['key'],{}).get('v') is None for t in d['teams'])]
    d.update(schemaVersion=1,metadata=meta,summaries=read(folder/'summaries.json'),teamConfig=teams,
             sourceChecksums=input_digest(folder,root))
    identities=read(inp/'player-identities.json')
    if len({p['id'] for p in identities['players']})!=len(identities['players']):raise ValueError('Duplicate player identity.')
    d['playerIdentities']=identities
    # Shared definitions may carry season-owned explanatory notes, never another season's repairs.
    d['seasonNotes']={'coverage':meta['coverage']['statistics']+' '+meta['coverage']['results'],
                       'av': 'See value-level notes for the source and coverage of Approximate Value.'}
    validate_output(d)
    return d


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--season',default='2026')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    d=build(args.season);path=season_dir(args.season)/'season.json'
    if args.check:
        if not path.exists() or path.read_text()!=serialized(d):raise SystemExit(f'{args.season} is stale; run scripts/build_season.py --season {args.season}')
        print(f'{args.season}: generated season is current.')
    else:
        atomic_write(path,d);print(f'Built {args.season}; other seasons and publication manifest unchanged.')


if __name__=='__main__':main()
