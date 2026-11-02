"""2027 AV using the existing drive method and explicitly bounded baselines."""
from prepare_2027_players import TEAMS

def calculate(national,players,population):
    def eligible(cat,fields):
        return [r for r in population[cat] if all(isinstance(r['values'].get(k),(int,float)) for k in fields)]
    qbs=[r for r in eligible('PASSING',['YARDS','TD','INT','ATT']) if r['values']['ATT']>=150]
    kickfields=['XPM','XPA','FGM','FGA']+[p+s for p in ['FGM','FGA'] for s in ['29','39','49','50']]
    kickers=[r for r in eligible('KICKING',kickfields) if all(sum(r['values'][p+s] for s in ['29','39','49','50'])==r['values'][p] for p in ['FGM','FGA']) and all(r['values']['FGM'+s]<=r['values']['FGA'+s] for s in ['29','39','49','50'])]
    punters=[r for r in eligible('PUNTING',['PUNTS','YARDS','BLOCK']) if r['values']['PUNTS']>0]
    total=lambda rows,k:sum(r['values'][k] for r in rows)
    league={'aya':(total(qbs,'YARDS')+20*total(qbs,'TD')-45*total(qbs,'INT'))/total(qbs,'ATT'),
            'xp':total(kickers,'XPM')/total(kickers,'XPA'),
            'fg':{s:total(kickers,'FGM'+s)/total(kickers,'FGA'+s) for s in ['29','39','49','50']},
            'punt_adj':(total(punters,'YARDS')-13*total(punters,'BLOCK'))/(total(punters,'PUNTS')+total(punters,'BLOCK')),
            'population':{'qualifiedPassers':len(qbs),'kickers':len(kickers),'punters':len(punters)}}
    notes={'status':'computed_with_estimates','league':league,'inputs':{},'dropped_player_rows':[],
      'source_review':'AV uses the established three-team drive baselines. Passing/kicking/punting baselines use the available regular-season captured player subset, not a complete national population. See av-baseline-players.json.'}
    out={t:{} for t in TEAMS}
    for t in TEAMS:
        s=national[t]
        drives=s['ptd']+s['rtd']+s['fga']+s['punts']+s['give']+s['d4a']-s['d4c']+24
        notes[t]={'drives':drives,'def_drives':drives,'off_pts_per_drive':(7*(s['ptd']+s['rtd'])+3*s['fgm'])/drives}
        notes['inputs'][t]={'pts_allowed':s['ptsa'],'ptd':s['ptd'],'rtd':s['rtd'],'fga':s['fga'],'fgm':s['fgm'],'punts':s['punts'],'turnovers':s['give'],'games':12}
    league['off_ppd']=sum(notes[t]['off_pts_per_drive'] for t in TEAMS)/3
    league['def_ppd']=sum(national[t]['ptsa']/notes[t]['drives'] for t in TEAMS)/3
    scope=f"Baseline: captured regular-season subset ({len(qbs)} passers with 150+ attempts, {len(kickers)} kickers with complete distance splits, {len(punters)} punters with blocked-punt counts). Not a complete national baseline."
    for t in TEAMS:
        n=notes[t];s=national[t];o=out[t]
        def put(k,v,note,estimate=True):o[k]={'v':v,'rank':None,'of':None,'estimate':estimate,'note':note}
        offense=100*n['off_pts_per_drive']/league['off_ppd'];line=offense*5/11;skill=offense-line
        rush=skill*.22*s['ryds']/(s['ryds']+s['pyds'])/.37;passing=(skill-rush)*.26
        for k,v in [('av_team_off',offense),('av_oline_pool',line),('av_skill_pool',skill),('av_rush_pool',rush),('av_pass_pool',passing),('av_rec_pool',(skill-rush)*.74)]:
            put(k,v,'Estimated drives = offensive TD + FGA + punts + giveaways + failed fourth downs + 24. Offensive points/drive use 7 per offensive TD plus 3 per FG. Baseline is the three dynasty teams.')
        qb=next(r for r in players[t]['PASSING'] if r['values'].get('ATT',0)>0);q=qb['values'];aya=(q['YARDS']+20*q['TD']-45*q['INT'])/q['ATT'];delta=aya-league['aya']
        adjustment=delta*(.5 if delta>0 else 2) if q['ATT']>=150 else 0
        put('av_qb1',passing*q['YARDS']/s['pyds']+adjustment,'Passing pool share plus AY/A adjustment. '+scope)
        n['qb1']={'name':qb['name'],'yards':q['YARDS'],'att':q['ATT'],'aya':aya}
        margin=(s['ptsa']/n['def_drives'])/league['def_ppd'];defense=100*(1+2*margin-margin**2)/(2*margin)
        for k,v in [('av_team_def',defense),('av_front7_pool',defense*2/3),('av_secondary_pool',defense/3)]:put(k,v,'Defensive drives equal the team’s estimated offensive drive count. Baseline is the three dynasty teams; position pools are not individual player AV.')
        kicker=next(r for r in players[t]['KICKING'] if r['values'].get('FGA',0)>0);k=kicker['values']
        paa=k['XPM']-k['XPA']*league['xp']+3*sum(k['FGM'+b]-k['FGA'+b]*league['fg'][b] for b in ['29','39','49','50'])
        put('av_kicker',3.125+16*paa/(5*k['GP']),f"{kicker['name']}: {k['GP']} regular-season appearances; sole placekicker. Buckets ≤29, 30–39, 40–49, 50+. "+scope)
        n['kicker_paa']=paa
        punter=next(r for r in players[t]['PUNTING'] if r['values'].get('PUNTS',0)>0);p=punter['values'];adj=(p['YARDS']-13*p['BLOCK'])/(p['PUNTS']+p['BLOCK']);above=(p['PUNTS']+p['BLOCK'])*(adj-league['punt_adj'])
        put('av_punter',2.1875+16*above/(200*p['GP']),'Adjusted punt average = (yards − 13 × blocked)/(punts + blocked); actual regular-season appearances. '+scope)
        n['punter_adj_ypa']=adj
    baseline={'PASSING':qbs,'KICKING':kickers,'PUNTING':punters}
    return out,notes,baseline
