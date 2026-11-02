"""Subtract recorded postseason player lines; never scale totals to twelve games."""
from season_io import ROOT, read, atomic_write
from pathlib import Path
import copy, re, unicodedata, collections, difflib

TEAMS=['Western Michigan','Central Michigan','Eastern Michigan']
COUNT={
 'PASSING':['COMP','ATT','YARDS','TD','INT','SACKS'],
 'RUSHING':['CAR','YARDS','TD','20+','BTK','YAC','FUMB'],
 'RECEIVING':['REC','YARDS','TD','RAC','DROP'],
 'DEFENSE':['SOLO','ASSISTS','TAK','TFL','SACK','INT','INT YDS','TD','DEFL','FFUMB','FUMB','FMBYDS','BLOCK','SFTY'],
 'BLOCKING':['SACK'],'KICKING':['FGM','FGA','XPM','XPA','FG BLK','XPB','KO','TB']+[p+s for p in ['FGM','FGA'] for s in ['29','39','49','50']],
 'PUNTING':['PUNTS','YARDS','NET YDS','IN20','TB','BLOCK'],
 'KICK RETURN':['KR','YARDS','TD'],'PUNT RETURN':['PR','YARDS','TD']}
SORT={'PASSING':'YARDS','RUSHING':'YARDS','RECEIVING':'YARDS','DEFENSE':'TAK','BLOCKING':'SACK','KICKING':'FGM','PUNTING':'PUNTS','KICK RETURN':'YARDS','PUNT RETURN':'YARDS'}
MAXIMA={'PASSING':'LONG','RUSHING':'LONG','RECEIVING':'LONG','DEFENSE':'INT LG','KICKING':'FG LNG','PUNTING':'LONG','KICK RETURN':'LONG','PUNT RETURN':'LONG'}
SIGNED={'YARDS','RAC','INT YDS','FMBYDS','NET YDS'}
COLUMNS={
 'PASSING':['GP','COMP','ATT','COMP%','YARDS','TD','INT','YPA','YPG','RATING','LONG','SACKS'],
 'RUSHING':['GP','CAR','YARDS','AVG','TD','AVG G','20+','BTK','YAC','LONG','FUMB'],
 'RECEIVING':['GP','REC','YARDS','AVG','TD','AVG G','LONG','RAC','RAC AVG','DROP'],
 'DEFENSE':['GP','SOLO','ASSISTS','TAK','TFL','SACK','INT','INT YDS','INT AVG','INT LG','TD','DEFL','FFUMB','FUMB'],
 'BLOCKING':['GP','SACK','SNAPS'],
 'KICKING':['GP','FGM','FGA','FG%','FG LNG','XPM','XPA','XP%','FGM29','FGA29','FGM39','FGA39','FGM49','FGA49','FGM50','FGA50'],
 'PUNTING':['GP','PUNTS','YARDS','AVG','NET YDS','NET AVG','IN20','TB','LONG','BLOCK'],
 'KICK RETURN':['GP','KR','YARDS','AVG','TD','LONG'], 'PUNT RETURN':['GP','PR','YARDS','AVG','TD','LONG']}

def nk(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s.replace('IIl','III')).encode('ascii','ignore').decode().lower())
def matching(rows,name):return [r for r in rows if nk(r['name'])==nk(name)]
def sum_known(rows,k):return sum(r['values'][k] for r in rows if r['values'].get(k) is not None)
def rates(cat,v):
 def div(out,n,d,scale=1):v[out]=round(scale*v[n]/v[d],1) if v.get(n) is not None and v.get(d) else (0 if v.get(n)==0 and v.get(d)==0 else None)
 if cat=='PASSING':
  for o,n,d,s in [('COMP%','COMP','ATT',100),('YPA','YARDS','ATT',1),('YPG','YARDS','GP',1)]:div(o,n,d,s)
  v['RATING']=round((8.4*v['YARDS']+330*v['TD']+100*v['COMP']-200*v['INT'])/v['ATT'],1) if all(v.get(k) is not None for k in ['YARDS','TD','COMP','INT','ATT']) and v['ATT'] else None
 if cat in ['RUSHING','RECEIVING','PUNTING','KICK RETURN','PUNT RETURN']:
  den={'RUSHING':'CAR','RECEIVING':'REC','PUNTING':'PUNTS','KICK RETURN':'KR','PUNT RETURN':'PR'}[cat];div('AVG','YARDS',den)
  if cat in ['RUSHING','RECEIVING']:div('AVG G','YARDS','GP')
  if cat=='RECEIVING':div('RAC AVG','RAC','REC')
  if cat=='PUNTING':div('NET AVG','NET YDS','PUNTS')
 if cat=='DEFENSE':div('INT AVG','INT YDS','INT')
 if cat=='KICKING':div('FG%','FGM','FGA',100);div('XP%','XPM','XPA',100)
 return v

def deductions(cats,cat,name,field):
 rows=matching(cats.get(cat,[]),name)
 if len(rows)==1 and not rows[0].get('identityAmbiguous'):
  value=rows[0]['values'].get(field)
  if value is not None:return value,'Recorded game player line'
 if len(rows)>1 and all(field in r['values'] for r in rows) and len({r['values'][field] for r in rows})==1:
  return rows[0]['values'][field],'Both same-name game rows show the same value'
 if len(rows)>1 and (cat,nk(name)) in cats.get('_equalShare',set()) and all(field in r['values'] for r in rows):
  return sum(r['values'][field] for r in rows)/len(rows),'User-authorized equal split of same-name game lines; individual estimate'
 # A zero snap count establishes non-participation for every category.
 gen=matching(cats.get('GENERAL',[]),name)
 if len(gen)==1 and gen[0]['values'].get('SNAPS')==0:return 0,'Recorded zero game snaps'
 if not rows:
  if cat=='DEFENSE' and field in ['SOLO','ASSISTS','TAK','TFL','SACK'] and cats.get('_dynastyReviewed'):
   return 0,'Recorded tackle-sorted table reaches zero below all positive-tackle players'
  if cat=='BLOCKING' and field=='SACK' and cats.get('_dynastyReviewed'):
   return 0,'Recorded sacks-allowed table reaches zero'
  if cat=='RUSHING' and cats.get('_rushCountsComplete') and field in ['CAR','YARDS','TD','20+','YAC','LONG']:
   return 0,'Recorded carries exhaust the independently recorded team rush count'
  if cat in ['KICK RETURN','PUNT RETURN'] and cats.get('_zeroReturnYards',{}).get(cat) and field in ['YARDS','TD','LONG']:
   return 0,'Team return yards are zero and the yardage-sorted player table has no positive returns'
 # Nonnegative category totals, verified against the passer/team line, exhaust
 # the game total and therefore establish zero for an unread/missing cell.
 target=None
 if cat=='RECEIVING' and field in ['REC','TD']:target=sum_known(cats['PASSING'],{'REC':'COMP','TD':'TD'}[field])
 if cat=='RECEIVING' and field=='YARDS':
  # The recorded list is ordered by yards and reaches zero; all positive-yard
  # production accounts for the passer total. Unseen rows cannot offset it.
  target=sum_known(cats['PASSING'],'YARDS')
 if target is not None and sum_known(cats.get(cat,[]),field)==target:return 0,'Recorded receiving rows exhaust the passing total'
 if cat=='RECEIVING' and field in ['RAC','LONG']:
  rec,_=deductions(cats,cat,name,'REC')
  if rec==0:return 0,'No game receptions'
 # A defender with no tackles has no solo/assisted tackles, TFL or sacks.
 if len(rows)==1 and rows[0]['values'].get('TAK')==0 and field in ['SOLO','ASSISTS','TFL','SACK']:return 0,'Zero game tackles'
 if len(rows)==1 and cat=='DEFENSE' and field in ['SOLO','ASSISTS','TAK']:
  v=rows[0]['values'];other={'SOLO':('TAK','ASSISTS'),'ASSISTS':('TAK','SOLO'),'TAK':('SOLO','ASSISTS')}[field]
  if all(k in v for k in other):return (v[other[0]]+v[other[1]] if field=='TAK' else v[other[0]]-v[other[1]]),'Tackle identity'
 return None,'No uniquely identified game value'

def adjust(row,cat,team,games,cutoff,audit):
 raw=row['values'];v={};postrows=[(game,cats) for game,cats in games];estimated=[]
 for field in COUNT[cat]:
  before=raw.get(field);remaining=before;steps=[]
  for game,cats in postrows:
   deduction,why=deductions(cats,cat,row['name'],field)
   if why.startswith('User-authorized'):estimated.append(field)
   if before==0 and field not in SIGNED and deduction in [None,0]:deduction,why=0,'Nonnegative captured season count is zero'
   if remaining is None or deduction is None:remaining=None
   else:remaining-=deduction
   steps.append({'game':game,'subtract':deduction,'reason':why})
  if remaining is not None and remaining<0 and field not in SIGNED:remaining=None;steps.append({'reason':'Conflicting source counts; withheld'})
  v[field]=remaining
  if postrows:audit.append({'team':team,'category':cat,'name':row['name'],'pos':row['pos'],'field':field,'captured':before,'regular':remaining,'deductions':steps})
 gp=raw.get('GP')
 if gp==cutoff:gp=12
 elif postrows:
  for game,cats in postrows:
   gen=matching(cats.get('GENERAL',[]),row['name'])
   if len(gen)==1 and gen[0]['values'].get('SNAPS') is not None:played=int(gen[0]['values']['SNAPS']>0)
   else:
    rs=matching(cats.get(cat,[]),row['name']);played=1 if len(rs)==1 and any(rs[0]['values'].get(k,0)>0 for k in COUNT[cat]) else None
   gp=gp-played if gp is not None and played is not None else None
 v['GP']=gp
 if raw.get('SNAPS') is not None:
  snaps=raw['SNAPS']
  for game,cats in postrows:
   rs=matching(cats.get('GENERAL',[]),row['name']);sn=rs[0]['values'].get('SNAPS') if len(rs)==1 else None
   snaps=snaps-sn if snaps is not None and sn is not None else None
  v['SNAPS']=snaps if snaps is None or snaps>=0 else None
 if cat in MAXIMA:
  k=MAXIMA[cat];maximum=raw.get(k)
  for game,cats in postrows:
   count,why=deductions(cats,cat,row['name'],k)
   if maximum is not None and maximum!=0 and (count is None or count>=maximum):maximum=None
  v[k]=maximum
 result={'name':row['name'],'pos':row['pos'],'team':team,'values':rates(cat,v)}
 if estimated:result.update(estimate=True,estimatedFields=sorted(set(estimated)),note='Estimated individual split, requested by the user: each J. Taylor receives half of both postseason game lines. Combined team totals remain exact.')
 return result

def prepare(root=ROOT):
 folder=Path(root)/'data/seasons/2027';inp=folder/'inputs';raw=read(inp/'captured-dynasty-players.json');post=read(inp/'captured-postseason-players.json');boxes=read(inp/'captured-box-scores.json');audit=[];dynasty={};out={c:[] for c in COUNT};excluded=[]
 for policy in read(inp/'player-estimate-policy.json')['equalShare']:
  for game in policy['games']:post[game][policy['team']].setdefault('_equalShare',set()).add((policy['category'],nk(policy['name'])))
 for team,cs in raw.items():
  games=[(g,teams[team]) for g,teams in post.items() if team in teams];cutoff=12+len(games);dynasty[team]={}
  for game,cats in games:
   box=boxes[game]['values'][team];cats['_dynastyReviewed']=True
   cats['_rushCountsComplete']=sum_known(cats['RUSHING'],'CAR')==box['Rushes - Yards - TDs'][0]
   cats['_zeroReturnYards']={cat:box.get(field)==0 and all(r['values'].get('YARDS',0)<=0 for r in cats[cat]) for cat,field in [('KICK RETURN','KR Yards'),('PUNT RETURN','PR Yards')]}
  for cat,rows in cs.items():
   dynasty[team][cat]=[]
   for row in rows:
    r=adjust(row,cat,team,games,cutoff,audit);dynasty[team][cat].append(r)
    if r['values'].get(SORT[cat]) is None:excluded.append({'team':team,'category':cat,'name':row['name'],'pos':row['pos'],'reason':'Primary total cannot be attributed/subtracted exactly.'});continue
    if cat!='BLOCKING' and not any(r['values'].get(k,0) for k in [SORT[cat],'TD']):continue
    out[cat].append(r)
 # National screen rows are screened against every recorded postseason roster,
 # including GENERAL participation. GP alone is never the cutoff test.
 national=read(inp/'captured-national-players.json')
 roster=collections.defaultdict(set)
 for game,teams in post.items():
  for team,cats in teams.items():
   for cat,rows in cats.items():
    if cat.startswith('_'):continue
    for row in rows:roster[nk(row['name'])].add(team)
 for cat,rows in national.items():
  name_counts=collections.Counter((nk(r['name']),r['pos']) for r in rows)
  for row in rows:
   name=nk(row['name']);v=row['values'];gp=v.get('GP');reason=None
   known=[(team,r) for team,cs in raw.items() for r in cs[cat] if nk(r['name'])==name and r['pos']==row['pos']]
   if known:continue  # The independently recorded team row governs.
   if row.get('review'):reason='Source arithmetic or name collision needs review'
   elif row.get('observations',0)<3:reason='Too few stable observations'
   elif name_counts[(name,row['pos'])]>1:reason='Duplicate abbreviated name and position'
   elif gp is None or not 1<=gp<=14:reason='Captured games played unavailable'
   matches=roster.get(name,set())
   similar={t for candidate,ts in roster.items() if candidate[:1]==name[:1] and difflib.SequenceMatcher(None,name,candidate).ratio()>.8 for t in ts}
   team=None;games=[]
   if reason is None and gp>12:
    if len(matches)!=1:reason='Postseason team/name cannot be resolved uniquely'
    else:
     team=next(iter(matches));games=[(g,tt[team]) for g,tt in post.items() if team in tt]
     if gp!=12+len(games):reason='Player cutoff does not match the identified postseason cohort'
     elif any(len(matching(cs.get(cat,[]),row['name']))!=1 for _,cs in games):reason='Individual postseason category line missing or ambiguous'
   elif reason is None and similar:reason='Possible postseason roster match with fewer than thirteen appearances'
   if reason:
    excluded.append({'category':cat,'name':row['name'],'pos':row['pos'],'reason':reason,'scope':'national'});continue
   r=adjust(row,cat,team,games,gp if games else 12,audit)
   if r['values'].get(SORT[cat]) is None:
    excluded.append({'category':cat,'name':row['name'],'pos':row['pos'],'reason':'Exact primary postseason deduction unavailable','scope':'national'});continue
   # Rows outside the recorded postseason rosters keep their season counts;
   # those matched to a 13/14-game cohort have exact game lines removed.
   if cat!='BLOCKING' and not any(r['values'].get(k,0) for k in [SORT[cat],'TD']):continue
   out[cat].append(r)
 return folder,dynasty,out,audit,excluded

def main():
 folder,dynasty,out,audit,excluded=prepare()
 atomic_write(folder/'inputs/regular-dynasty-players.json',dynasty)
 atomic_write(folder/'inputs/player-postseason-adjustments.json',audit)
 atomic_write(folder/'inputs/player-withheld-rows.json',excluded)
 atomic_write(folder/'inputs/regular-player-population.json',out)
 for cat,rows in out.items():
  rows.sort(key=lambda r:(-r['values'][SORT[cat]],r['name'],r['pos']))
  source={'category':cat,'columns':COLUMNS[cat],'sortedBy':SORT[cat],'complete':False,'coverage':{'nationalComplete':False},'rows':[{**r,'values':{k:r['values'].get(k) for k in COLUMNS[cat]}} for r in rows],
   'screen':'12-game regular-season window; captured player subset. National rows are screened against recorded postseason rosters. Identified 13/14-game cohorts have individual postseason counts removed; ambiguous matches are withheld. Rates are recomputed. Dashes mark unreadable deductions or unrecoverable season maxima.','sources':['2027/IMG_5598.MOV','2027/IMG_5599.MOV','2027/IMG_5600.MOV']+[f'2027/IMG_{n}.MOV' for n in range(5604,5613)]+[f'2027/Additional Items/IMG_{n}.MOV' for n in range(5620,5624)]}
  atomic_write(folder/'leaders'/f'{cat.replace(" ","_")}.json',source)
 print('Prepared regular-season dynasty rows:',{c:len(r) for c,r in out.items()})
 print('Withheld rows:',len(excluded))
if __name__=='__main__':main()
