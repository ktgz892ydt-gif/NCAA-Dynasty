"""JSON scoreboard adapter for the preserved rating engine."""
from . import ratings as engine
from update_sos import scoreboard_hash


def calculate(games, metadata, settings, order=None):
    converted=[engine.Game(i+1,i,g['wk'],g.get('date',''),g['a'],g['h'],g['as'],g['hs'],g['n'],g.get('notes','')) for i,g in enumerate(games)]
    if order is not None:
        if sorted(o['scoreboardIndex'] for o in order)!=list(range(len(games))):raise ValueError('Invalid rating game order.')
        converted=[engine.Game(g.row_number,o['sourceOrder'],g.week,o['date'],g.away_team,g.home_team,g.away_score,g.home_score,g.neutral,g.notes) for o in order for g in [converted[o['scoreboardIndex']]]]
    teams=engine.team_list(converted)
    if not teams:return [],{},None
    # All season ratings require a connected opponent graph to share a baseline.
    reached={teams[0]}
    while True:
        nxt=reached|{g[k] for g in games if g['a'] in reached or g['h'] in reached for k in ['a','h']}
        if nxt==reached:break
        reached=nxt
    if len(reached)!=len(teams):raise ValueError('Opponent graph is disconnected; a shared national rating is not yet identifiable.')
    hfa=engine.estimate_home_field(converted,teams)
    home=hfa['estimated_home_field_advantage'] or 0.
    stats=engine.calculate_records(converted,teams)
    if metadata['syntheticRecordPolicy']=='legacy-0-12':
        # Scope the old synthetic-record convention to this adapter call.
        original=engine.FCS_TEAMS
        try:
            engine.FCS_TEAMS=set(metadata['syntheticTeams'])
            engine.apply_fcs_summary(stats,converted)
        finally:engine.FCS_TEAMS=original
    srs,_,_=engine.calculate_srs(converted,teams,home)
    elo=engine.calculate_elo(converted,teams,home,settings['eloStart'],settings['eloK'])
    bt,_,_=engine.calculate_bradley_terry(converted,teams)
    g2=engine.calculate_glicko2(converted,teams,home,settings['eloStart'],settings['glickoRD'],settings['glickoVolatility'],settings['glickoTau'])
    rows=[{'t':t,'g':int(stats[t]['games']),'w':int(stats[t]['wins']),'l':int(stats[t]['losses']),
           'pf':stats[t]['pf'],'pa':stats[t]['pa'],'mov':round((stats[t]['pf']-stats[t]['pa'])/stats[t]['games'],2),
           'srs':round(srs[t],2),'elo':round(elo[t],1),'bt':round(bt[t],1),'g2':round(g2[t]['rating'],1),
           'syn':t in metadata['syntheticTeams']} for t in teams]
    rows.sort(key=lambda r:-r['srs'])
    source={'season':metadata['id'],'scoreboard_sha256':scoreboard_hash(games),'ratings':srs,'source_path':f'data/seasons/{metadata["id"]}/inputs/scoreboard.json'}
    return rows,{'estimated_home_field_advantage':home,'home_field_estimation_method':hfa['method'],'home_field_estimation_status':hfa['status']},source
