"""Reconcile captured 2027 statistics to the 12-game regular season.

Raw captures remain in inputs/captured-*.json. No per-game or per-player
postseason contributions are guessed. Re-run before build_season.py.
"""
from pathlib import Path
import argparse,copy,collections,json,math
from season_io import ROOT,read,atomic_write,serialized

TEAMS={'Western Michigan':'W. Michigan','Eastern Michigan':'E. Michigan','Central Michigan':'C. Michigan'}

def ratio(n,d):return n/d if n is not None and d else None

def derive(s):
    v=dict(s)
    def div(k,a,b):v[k]=ratio(v.get(a),v.get(b))
    def add(k,*ks):v[k]=sum(v[x] for x in ks) if all(v.get(x) is not None for x in ks) else None
    add('yds','pyds','ryds');add('ttd','ptd','rtd');add('rzs','rztd','rzfg');add('rzsa','rztda','rzfga')
    for k,a,b in [('pcpct','pcomp','patt'),('ypa','pyds','patt'),('ypc_pass','pyds','pcomp'),('ypcar','ryds','car'),('ypcara','rydsa','cara'),('ypp','yds','plays'),('yppa','ydsa','dplays'),('p2r','pyds','ryds'),('balance','car','patt'),('passrate','patt','plays'),('rushshare','car','plays'),('ptdrate','ptd','patt'),('rtdrate','rtd','car'),('pintrate','pint','patt'),('torate','give','plays'),('pctpass','ptd','ttd'),('pctrush','rtd','ttd'),('d3pct','d3c','d3a'),('d4pct','d4c','d4a'),('rzpct','rzs','rza'),('d3pcta','d3ca','d3aa'),('d4pcta','d4ca','d4aa'),('rzpcta','rzsa','rzaa'),('pcpcta','pcompa','patta'),('fgpct','fgm','fga'),('xppct','xpm','xpa'),('ypunt','puntyds','punts')]:div(k,a,b)
    for k,a,b in [('oeff','pts','yds'),('deff','ptsa','ydsa')]:v[k]=100*ratio(v[a],v[b]) if v.get(a) is not None and v.get(b) else None
    for k,a,b in [('sacktakenrate','sackstaken','patt'),('sackrate','sacks','patta')]:v[k]=ratio(v.get(a),v.get(a,0)+v.get(b,0)) if v.get(a) is not None and v.get(b) is not None else None
    if all(v.get(k) is not None for k in ['pyds','ptd','pint','patt']):v['aya']=ratio(v['pyds']+20*v['ptd']-45*v['pint'],v['patt'])
    for suffix in ['', 'a']:
        keys=[k+suffix for k in ['pyds','pcomp','patt']]+(['ptda','dint'] if suffix else ['ptd','pint'])
        if all(v.get(k) is not None for k in keys):
            yards,comp,att,td,ints=[v[k] for k in keys]
            v['ncaa'+suffix]=(8.4*yards+330*td+100*comp-200*ints)/att if att else None
            clip=lambda n:max(0,min(2.375,n))
            v['nfl'+suffix]=100*(clip((comp/att-.3)*5)+clip((yards/att-3)*.25)+clip(td/att*20)+clip(2.375-ints/att*25))/6 if att else None
    if v.get('take') is not None and v.get('give') is not None:v['todiff']=v['take']-v['give']
    if v.get('penyds') is not None:v['penypg']=v['penyds']/12
    if all(v.get(k) is not None for k in ['top','fd','plays','give']):v['bci']=.5*v['top']/(12*2160)+.3*v['fd']/v['plays']-.2*v['give']/v['plays']
    if v.get('top') is not None:v['toppg']=v['top']/12
    if all(v.get(k) is not None for k in ['ptd','rtd','fga','punts','give','d4a','d4c','ypp','pts']):
        drives=v['ptd']+v['rtd']+v['fga']+v['punts']+v['give']+v['d4a']-v['d4c']+24
        v['explo']=v['ypp']*v['pts']/drives
    for dest,src in {'pts2':'pts','ptsa2':'ptsa','fd_so':'fd','d3rate':'d3pct','d4rate':'d4pct','rzrate':'rzpct','sacks_d':'sacks','dint2':'dint'}.items():v[dest]=v.get(src)
    return v

MAPPING={'OFFENSE':{'GP':'games','PTS':'pts','OFF':'yds','PASS':'pyds','PTD':'ptd','RUSH':'ryds','RTD':'rtd','FDS':'fd'},
'DEFENSE':{'PTS':'ptsa','TOTAL':'ydsa','PASS':'pydsa','RUSH':'rydsa','SACK':'sacks'},
'CONVERSIONS':{'3DC':'d3c','3DA':'d3a','4DC':'d4c','4DA':'d4a','2PC':'twoMade','2PA':'twoAtt'},
'REDZONE EFFICIENCY':{'ATT':'rza','TD':'rztd','FG':'rzfg','DATT':'rzaa','DTD':'rztda','DFG':'rzfga'},
'PENALTIES':{'PEN':'pen','YARDS':'penyds'},
'TURNOVERS':{'GIVE':'give','INT':'pint','FUM LOST':'fumlost','TAKE':'take','DINT':'dint','FUM REC':'fumrec'}}


def box_totals(v):
    result={}
    for field,key in {'Score':'pts','First Downs':'fd','Total Offense':'yds','Total Plays':'plays','Passing Yards':'pyds','Turnovers':'give','Interceptions':'pint','Fumble Lost':'fumlost','PR Yards':'pr','KR Yards':'kr','T.O.P':'top'}.items():
        if field in v:result[key]=v[field]
    for field,keys in {'Rushes - Yards - TDs':['car','ryds','rtd'],'Comp - Att - TDs':['pcomp','patt','ptd'],'3rd Down Conv.':['d3c','d3a'],'4th Down Conv.':['d4c','d4a'],'2-Point Conv.':['twoMade','twoAtt'],'Red Zone TD-FG-%':['rztd','rzfg','rza'],'Punts - Avg':['punts','puntyds'],'Penalties - Yards':['pen','penyds']}.items():
        if field in v:result.update(dict(zip(keys,v[field])))
    return result


def prepare(root=ROOT):
    folder=Path(root)/'data/seasons/2027';inp=folder/'inputs';captured=read(inp/'captured-team-stats.json');boxes=read(inp/'captured-box-scores.json');players=read(inp/'captured-dynasty-players.json');games=read(inp/'scoreboard.json');post=read(inp/'excluded-postseason-games.json')
    regular_players=read(inp/'regular-dynasty-players.json');postplayers=read(inp/'captured-postseason-players.json')
    assert len(games)==842
    appearances=collections.Counter(g[k] for g in games for k in ['a','h']);assert all(n==12 for t,n in appearances.items() if not t.startswith('FCS'))
    national={t:{new:c.get(cat,{}).get(old) for cat,mapping in MAPPING.items() for old,new in mapping.items()} for t,c in captured.items()}
    adjustments=[];pending=[]
    for a,h,pf,pa in post:
        key=' | '.join(sorted([a,h]));key+=' | Championship' if set([a,h])=={'Western Michigan','Central Michigan'} else ''
        box=boxes.get(key)
        for team,other,pts,ptsa in [(a,h,pf,pa),(h,a,pa,pf)]:
            s=national[team];s['games']-=1
            if box is None:
                for k in s:
                    if k!='games':s[k]=None
                s['sacks']=captured[team]['DEFENSE']['SACK']-sum(r['values']['SACKS'] for r in postplayers[key][other]['PASSING'] if r['values'].get('ATT',0)>0)
                pending.append({'team':team,'game':key,'reason':'Championship team box missing; team-box-dependent fields withheld. Scoreboard scoring and opposing-passer sack deductions remain available.'})
                continue
            own=box_totals(box['values'][team]);opp=box_totals(box['values'][other]);own.update(ptsa=opp.get('pts'),ydsa=opp.get('yds'),pydsa=opp.get('pyds'),rydsa=opp.get('ryds'),rzaa=opp.get('rza'),rztda=opp.get('rztd'),rzfga=opp.get('rzfg'),take=opp.get('give'),dint=opp.get('pint'),fumrec=opp.get('fumlost'))
            own['sacks']=sum(r['values']['SACKS'] for r in postplayers[key][other]['PASSING'] if r['values'].get('ATT',0)>0)
            changes={}
            for k in s:
                if k=='games':continue
                before=s[k];deduction=own.get(k)
                s[k]=before-deduction if before is not None and deduction is not None else None
                changes[k]={'capturedRemaining':before,'subtract':deduction,'regularRemaining':s[k]}
                if s[k] is not None and s[k]<0:raise ValueError(f'Negative adjusted {team} {k}')
            adjustments.append({'team':team,'game':key,'sourceFrames':box['sources'],'changes':changes})
    for t,s in national.items():
        gs=[g for g in games if t in (g['a'],g['h'])];assert len(gs)==s['games']==12
        # Scoreboard scores, not internally inconsistent aggregate point screens, govern ratings and scoring.
        s['pts']=sum(g['as'] if g['a']==t else g['hs'] for g in gs);s['ptsa']=sum(g['hs'] if g['a']==t else g['as'] for g in gs)
    values={};details={};metric_keys=[m['key'] for m in read(Path(root)/'config/metrics.json')]
    for team,short in TEAMS.items():
        s=national[team];regular=[]
        for key,b in boxes.items():
            if team not in b['teams'] or any(n in [5614,5615] for n,ts in b['sources']):continue
            other=next(t for t in b['teams'] if t!=team);regular.append((box_totals(b['values'][team]),box_totals(b['values'][other])))
        assert len(regular)==12
        def total(key,side=0):
            vals=[pair[side].get(key) for pair in regular]
            return sum(vals) if all(v is not None for v in vals) else None
        for k in ['car','plays','top','pr','kr']:s[k]=total(k)
        for own,other in [('pcompa','pcomp'),('patta','patt'),('ptda','ptd'),('rtda','rtd'),('cara','car'),('dplays','plays'),('fda','fd'),('d3ca','d3c'),('d3aa','d3a'),('d4ca','d4c'),('d4aa','d4a')]:s[own]=total(other,1)
        s['tda']=s['ptda']+s['rtda'] if s['ptda'] is not None and s['rtda'] is not None else None
        rp=regular_players[team]
        qb=next(p for p in rp['PASSING'] if p['values'].get('ATT',0)>0);q=qb['values']
        for key,field in [('pcomp','COMP'),('patt','ATT'),('pint','INT'),('sackstaken','SACKS')]:s[key]=q[field]
        s['plays']=s['car']+s['patt']
        punter=next(p for p in rp['PUNTING'] if p['values'].get('PUNTS',0)>0)
        s.update(punts=punter['values']['PUNTS'],puntyds=punter['values']['YARDS'])
        kicker=next(p for p in rp['KICKING'] if p['values'].get('FGA',0)>0)
        for key,field in [('fga','FGA'),('fgm','FGM'),('xpa','XPA'),('xpm','XPM')]:s[key]=kicker['values'][field]
        # All positive-tackle rows were recorded; zero-tackle tails establish
        # zero TFL. Same-name game rows remain separate in this team sum.
        s['tfl']=sum(p['values']['TFL'] for p in players[team]['DEFENSE'])
        for key,tt in postplayers.items():
            if team in tt:s['tfl']-=sum(p['values'].get('TFL',0) for p in tt[team]['DEFENSE'])
        def sum_complete(cat,field):
            vals=[r['values'].get(field) for r in rp[cat]]
            return sum(vals) if all(v is not None for v in vals) else None
        s['deftd']=sum_complete('DEFENSE','TD')
        returns=[sum_complete(cat,'TD') for cat in ['KICK RETURN','PUNT RETURN']]
        s['sttd']=sum(returns) if all(x is not None for x in returns) else None
        if team=='Eastern Michigan':s['fumrec']=total('fumlost',1)
        s['confchamp']=None;s['bowl']=None;s['cfp']=None
        v=derive(s);details[team]={'boxTotals':{k:total(k) for k in ['pcomp','patt','plays','punts','puntyds','pr','kr']},'quarterback':qb['name'],'punter':punter['name'],'regularTotals':s}
        cells={k:{'v':v.get(k),'rank':None,'of':None} for k in metric_keys if v.get(k) is not None}
        generic='12-game regular season. Season totals minus recorded postseason box scores; available regular-season box scores provide additional fields.'
        for k,c in cells.items():c['note']=generic
        passnote='Passing-room season totals minus postseason passing lines. The game contains inconsistent completion/attempt counts in several regular-season box scores; those box-score counts are not used for the quarterback season totals.'
        for k in ['pcomp','patt','pcpct','ypc_pass','ypa','aya','ncaa','nfl','passrate','plays','ypp']:cells[k]['note']=passnote
        for k in ['pcompa','pcpcta','ncaaa','nfla']:
            if k in cells:cells[k]['note']='Sum of 12 opposing box-score passing lines. The game has known passing-count anomalies; opponent completion-dependent measures remain provisional.';cells[k]['estimate']=True
        if team=='Eastern Michigan':
            cells['pint']['note']='Quarterback season screen: 10 interceptions. Team turnover screen and box scores total 11; retained as a documented source discrepancy.'
            for k in ['give','todiff','torate','fumrec']:
                if k in cells:cells[k]['note']='Giveaways/takeaways follow team totals and 12-game box scores. Eastern passing and recovery summaries disagree with these screens; see source notes.'
        if 'explo' in cells:cells['explo'].update(estimate=True,note='Estimated drives from offensive TD + FGA + punts + giveaways + failed fourth downs + 2 per game; all inputs cover 12 games.')
        for k in ['sacks','sacks_d','sackrate','sackstaken','sacktakenrate','tfl','deftd','fga','fgm','fgpct','xpa','xpm','xppct','sttd']:
            if k not in cells:cells[k]={'v':None,'rank':None,'of':None,'note':'Awaiting individual postseason stats or an independently verified regular-season total. Postseason-inclusive values are withheld.'}
        values[short]=cells;national[team]=s
    derived={t:derive(s) for t,s in national.items()};leaders={};coverage={}
    # Only additive totals and rates reconstructable across teams receive a national comparison.
    rankable=['pts2','ptsa2','pyds','ptd','ryds','rtd','ttd','fd','fd_so','ydsa','pydsa','rydsa','oeff','deff','p2r','pctpass','pctrush','d3c','d3a','d3pct','d3rate','d4c','d4a','d4pct','d4rate','rza','rzs','rzpct','rzrate','rzaa','rzsa','rzpcta','pen','penyds','penypg','dint','dint2','todiff','sacks','sacks_d']
    for m in read(Path(root)/'config/metrics.json'):
        k=m['key']
        if k not in rankable:continue
        eligible={t:v[k] for t,v in derived.items() if v.get(k) is not None};higher=m.get('higherBetter') is not False
        coverage[k]={'teams':len(eligible),'field':138,'scope':'12-game regular season; teams without exact postseason deductions excluded.'}
        leaders[k]=[{'t':t,'v':v} for t,v in sorted(eligible.items(),key=lambda kv:((-kv[1] if higher else kv[1]),kv[0]))[:10]]
        for team,short in TEAMS.items():
            if team not in eligible or k not in values[short]:continue
            v=eligible[team];cell=values[short][k];cell.update(rank=1+sum(x>v if higher else x<v for x in eligible.values()),of=len(eligible))
            if len(eligible)<138:cell['note']+=f' Rank among {len(eligible)} teams with verified regular-season coverage, out of 138 real teams.'
    from prepare_2027_av import calculate
    av,av_notes,av_population=calculate(national,regular_players,read(inp/'regular-player-population.json'))
    for team,short in TEAMS.items():values[short].update(av[team])
    outputs={'av-notes.json':av_notes,'av-baseline-players.json':av_population,'team-stats.json':values,'national-regular-stats.json':national,'national-leaders.json':leaders,'national-stat-coverage.json':coverage,'postseason-adjustments.json':adjustments,'pending-source-fields.json':pending,'dynasty-reconciliation.json':details}
    return folder,outputs


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');args=ap.parse_args();folder,outputs=prepare()
    for name,data in outputs.items():
        p=folder/'inputs'/name
        if args.check:
            if not p.exists() or p.read_text()!=serialized(data):raise SystemExit('Stale '+str(p))
        else:atomic_write(p,data)
    print('2027: regular-season inputs '+('current.' if args.check else 'prepared; no manifest or archived season changed.'))
if __name__=='__main__':main()
