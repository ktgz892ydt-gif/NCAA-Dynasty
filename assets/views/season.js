// Each mount owns its DOM and global event subscriptions. Destroy before switching seasons.
export function mountSeason(root,DATA,initial={},onView=()=>{}){
const events=new AbortController();
const addEventListener=(type,listener,options={})=>window.addEventListener(type,listener,{...options,signal:events.signal});


/* ---------- tiny helpers ---------- */
const $=(s,r=root)=>r.querySelector(s);
const el=(t,a={},kids=[])=>{const e=document.createElement(t);
  for(const k in a){if(a[k]==null)continue;
    if(k==='class')e.className=a[k]; else if(k==='html')e.innerHTML=a[k]; else e.setAttribute(k,a[k]);}
  (Array.isArray(kids)?kids:[kids]).forEach(c=>c!=null&&c!==false&&e.append(c.nodeType?c:document.createTextNode(c)));
  return e;};
const SVNS="http://www.w3.org/2000/svg";
const sv=(t,a={})=>{const e=document.createElementNS(SVNS,t);for(const k in a)if(a[k]!=null)e.setAttribute(k,a[k]);return e;};

const P=DATA.teams, FULL=DATA.full, META=DATA.statMeta;
/* SOS, SOR, SRS and MOV head every summary card, so the stat table skips them.
   They stay in META for the head-to-head picker and the national tables. */
const TABLE=META.filter(m=>!m.hide);
const byKey={}; META.forEach(m=>byKey[m.key]=m);
const teamStyle=p=>DATA.teamConfig.find(t=>t.short===p);
const col=p=>teamStyle(p)?.accent||'#555';
const textCol=p=>teamStyle(p)?.[document.documentElement.dataset.theme==='dark'?'textDark':'textLight']||'var(--ink)';

function fmt(v,f){
  if(v==null||v==='')return '—';
  if(f==='record'||f==='text')return v;
  if(f==='rank')return '#'+Math.round(v);
  if(f==='pct')return (v*100).toFixed(1)+'%';
  if(f==='num0')return Math.round(v).toLocaleString();
  if(f==='num1')return (Math.round(v*10)/10).toFixed(1);
  if(f==='num2')return v.toFixed(2);
  if(f==='signed2')return (v>0?'+':'')+v.toFixed(2);
  if(f==='num3')return v.toFixed(3);
  if(f==='clock'){const s=Math.round(v);const h=Math.floor(s/3600),m=Math.floor(s%3600/60);
    return `${h}:${String(m).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;}
  if(f==='mmss'){const s=Math.round(v);
    return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;}
  if(f==='int')return Math.round(v).toLocaleString();
  return String(v);
}
const ord=n=>{if(n==null)return '';const s=['th','st','nd','rd'],v=n%100;return n+(s[(v-20)%10]||s[v]||s[0]);};
const val=(t,k)=>DATA.values[t]?.[k]||{v:null,rank:null,of:null};

/* ---------- measure explanations: click, tap and keyboard ---------- */
const EXPLANATIONS={
  srs:{title:'SRS · Simple Rating System',summary:'How strong a team has been, in points per game, after accounting for its opponents and home field.',
    detail:`The ratings are solved together across ${DATA.ratings.length} teams and centered at zero. +6 means roughly six points above the average team on this scale. Higher is better. This is a season rating, not a guaranteed margin or a win probability.`},
  sos:{title:'SOS · Strength of Schedule',summary:'How strong a team’s opponents were, measured in points above or below the average team.',
    detail:`This is the average SRS of the opponents on the schedule, counting each game equally. +5 means the opponents averaged five points stronger than an average team; −5 means five points weaker. Higher means a tougher schedule. Repeat opponents count each time they are played. FCS opponents use their synthetic bucket’s calculated SRS. National ranks compare ${DATA.ratings.filter(r=>!r.syn).length} FBS teams. SOS measures opponent strength; home-field adjustments are handled separately in SRS.`},
  sor:{title:'SOR · Strength of Record',summary:'How difficult would it be for a typical Top 25 team to match or exceed your win total against your schedule?',
    detail:`This is our estimated national résumé rank: #1 is strongest, out of ${(DATA.sorMethod?.ranked_teams??0)} FBS teams. Everyone is compared with the same reference team, rated ${(DATA.sorMethod?.benchmark_srs?.toFixed(2)??'unavailable')} SRS points—the average of this season’s top 25 FBS teams by SRS. We estimate its chance in each game using opponent strength and home, away or neutral location, then its chance of matching or exceeding your wins. A smaller chance earns a better rank. All played games count, including repeat opponents and FCS opponents using their synthetic ratings. Your scoring margins are not directly rewarded, but the SRS inputs reflect season scoring margins. This assumes independent games and uses a model fitted to this season’s results; it is a retrospective estimate, not an official ranking or a forecast.`},
  mov:{title:'MOV · Margin of Victory',summary:'Your average scoring margin across every game, including losses.',
    detail:'An MOV of +10 means the team scored ten more points than its opponents per game on average. Negative values mean it was outscored. Higher is better; MOV does not adjust for opponent strength.'},
  adjo:{title:'AdjO \u00b7 Adjusted Offense',summary:'Points a team would be expected to score per game against an average defence, on a neutral field.',
    detail:`This is the football version of what KenPom does for basketball: every team’s offence is rated by the points it scored against the defences it actually faced, its defence by the points it allowed to the offences it faced, and the two are solved together across all ${DATA.scoreboard.length} games because each depends on the other. Higher is better. A team that piles up points against weak defences is marked down, and one that scores steadily against good ones is marked up. The league average is ${DATA.effMethod?.league_average_points_per_game?.toFixed(1)??'unavailable'} points a game, so a figure above that is an above-average offence once the schedule is accounted for. National ranks compare ${DATA.ratings.filter(r=>!r.syn).length} FBS teams.`},
  adjd:{title:'AdjD \u00b7 Adjusted Defense',summary:'Points a team would be expected to allow per game to an average offence, on a neutral field.',
    detail:`Lower is better, and the national rank counts up from the stingiest defence. The league average is ${DATA.effMethod?.league_average_points_per_game?.toFixed(1)??'unavailable'} points a game. Reading AdjO and AdjD together is the point of the pair: a middling SRS can hide a strong defence carrying a poor offence, or the reverse, and the single margin figure cannot tell you which. Their difference is exactly SRS, which is why no separate margin figure is shown — that agreement is a check on the arithmetic rather than a second statistic. One deliberate difference from KenPom: these are per game, not per possession. No national screen carries punts or field-goal attempts, so a league-wide drive count cannot be built, and football drives vary far less than basketball possessions in any case.`},
  pyth:{title:'Pythagorean expected wins',summary:'An estimate of how many games a team would be expected to win from its season scoring totals.',
    detail:'The page shows expected wins, not a percentage. For example, 8.5 means about eight or nine wins from that scoring profile. Compare it with actual wins to spot over- or under-performance in close games. It is not a prediction of the remaining schedule.'},
  explo:{title:'Explosiveness Index',summary:'A dynasty-specific index that combines yards gained per play with points scored per estimated drive.',
    detail:'Higher means more yardage per play combined with more scoring per drive. It is not a count or percentage of long plays. Drives are estimated, including two end-of-half possessions per game, so every value is marked “est.”'},
  bci:{title:'Ball Control Index',summary:'A dynasty-specific blend of possession share, first downs per play and giveaways per play.',
    detail:'Higher rewards holding the ball, moving the chains and avoiding turnovers. A value of 0.30 is an index score, not a 30% win probability.'},
  balance:{title:'Offensive v Defensive Balance',summary:'Rushing carries divided by pass attempts: how the offense splits its play calls.',
    detail:'The name is inherited from the dynasty workbook, but the measure compares the offense with itself rather than with the defense. 1.00 is an even split of play calls; above 1.00 leans run, below 1.00 leans pass. It counts plays called, not how far they went — Pass-to-Run Yard Ratio does the yardage version, and the two can disagree when one phase is far more productive per play. Neither direction is better on its own. Team plays here are carries plus pass attempts, so this is the same split as % Rushing and % Passing expressed as a ratio. It is undefined if a team never attempts a pass.'},
  p2r:{title:'Pass-to-Run Yard Ratio',summary:'How many passing yards the offense gained for each rushing yard.',
    detail:'2.0 means two passing yards for every rushing yard; 1.0 means equal yardage. Higher indicates more passing yardage, not necessarily a better offense. This describes yardage balance, not the ratio of pass calls to run calls. The ratio is undefined when rushing yards are zero.'},
  av:{title:'Approximate Value · AV',summary:'A dynasty adaptation of Approximate Value: team performance creates points pools, then individual players receive shares based on production and participation.',
    detail:'A team or position-group pool is not an individual player’s AV. Quarterbacks include an efficiency adjustment; specialist values can be negative. Drive-rate baselines use the three dynasty teams, and defensive pools stay marked est. because the drive count is estimated. Only the players the source screens actually identify get their own row: the quarterback room, the kicker and the punter. Per-player rows for linemen, backs, receivers and defenders are not listed at all, because splitting a position pool needs Games Started and NCAA 26 reports games played and snaps only.'}
};
const helpKey=key=>key.startsWith('av_')?'av':key;
const dialog=$('#measure-dialog');
let helpOpener=null;
function showExplanation(title,summary,detail){
  helpOpener=document.activeElement;
  $('#measure-title').textContent=title;
  $('#measure-summary').textContent=summary;
  $('#measure-detail').textContent=detail||'';
  document.body.classList.add('dialog-open');
  dialog.showModal();
}
function leagueComparison(key){
  if(key==='bci')return ' A national average is not available from the current source files: possession time and exact offensive play totals are missing for most teams.';
  if(key==='explo')return ' A national average is not available from the current source files: team-level punt totals and field-goal attempts are missing for most teams.';
  return '';
}
function explain(key){
  const info=EXPLANATIONS[key];if(!info)return;
  showExplanation(info.title,info.summary,info.detail+leagueComparison(key));
}
function measureLabel(key,label){
  if(!EXPLANATIONS[key])return label;
  const button=el('button',{class:'measure-help',type:'button','aria-haspopup':'dialog',
    'aria-controls':'measure-dialog','aria-label':`Explain ${label}`},label);
  button.onclick=()=>explain(key);return button;
}
function coverageNote(m,p,s){
  if(m.key.startsWith('av_'))return s.estimate?el('span',{class:'rk',title:s.note},'est.'):null;
  if(!s.note&&!s.partial&&!s.estimate)return null;
  const button=el('button',{class:'rk',type:'button','aria-haspopup':'dialog',
    'aria-label':`${FULL[p]} ${m.name}: data note`},s.partial?`${s.partial}g`:s.estimate?'est.':'ⓘ');
  button.onclick=()=>showExplanation(`${FULL[p]} · ${m.name}`,s.note||`Covers ${s.partial} games.`);
  return button;
}
$('#measure-close').onclick=()=>dialog.close();
dialog.addEventListener('close',()=>{document.body.classList.remove('dialog-open');helpOpener?.focus();});
dialog.addEventListener('click',event=>{
  if(event.target!==dialog)return;
  const r=dialog.getBoundingClientRect();
  if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();
});

/* ---------- theme ---------- */
function toggleTheme(){
  const r=document.documentElement;
  r.dataset.theme = r.dataset.theme==='dark' ? 'light' : 'dark';
  render();
}

/* ---------- tooltip ---------- */
const tt=$('#tt');
function showTT(x,y,html){tt.innerHTML=html;tt.classList.add('on');
  const w=tt.offsetWidth,h=tt.offsetHeight;
  tt.style.left=Math.min(Math.max(8,x+14),innerWidth-w-8)+'px';
  tt.style.top=Math.max(8,y-h-12)+'px';}
function hideTT(){tt.classList.remove('on');}
addEventListener('scroll',hideTT,{passive:true});
addEventListener('touchstart',e=>{if(!e.target.closest('svg'))hideTT();},{passive:true});

/* ---------- header ---------- */
$('#sub').textContent = `${DATA.season} season — `+P.map(p=>FULL[p]).join(' · ');
const cv=DATA.coverage;
$('#prov').textContent =
  `Built from ${cv.photos} in-game photos and ${cv.videos} screen recordings: `+
  `${cv.games} recorded games${cv.weeks.length?' across weeks '+cv.weeks[0]+'–'+cv.weeks[cv.weeks.length-1]:''}, `+
  `${cv.teams} teams rated.`;
$('#coverage-detail').textContent=DATA.seasonNotes.coverage;
$('#nteams').textContent = val(P[0],'srs').of ?? '—';

/* ---------- tabs ---------- */
let view=initial.view||'dynasty';
const views=['dynasty','h2h','sched','national','leaders'];
function setView(next,notify=false){
  view=views.includes(next)?next:'dynasty';
  [...$('#tabs').children].forEach(b=>{b.classList.toggle('on',b.dataset.v===view);b.setAttribute('aria-current',b.dataset.v===view?'page':'false');});
  views.forEach(v=>$('#v-'+v).classList.toggle('hide',v!==view));
  render();if(notify)onView(view);
}
$('#tabs').addEventListener('click',e=>{const b=e.target.closest('.tab');if(b)setView(b.dataset.v,true);});

/* ---------- team cards ---------- */
// The summaries are hand-written but sit in a grid directly above the cards, so
// their column order has to follow DATA.teams. Reordering them from the data
// keeps the two grids aligned instead of relying on the markup staying in sync.
function alignSummaries(){
  const host=$('.season-summaries');host.replaceChildren();
  P.forEach(p=>{
    const team=teamStyle(p), summary=DATA.summaries.find(s=>s.teamId===team?.id);
    if(!summary)return;
    host.append(el('article',{class:'season-summary','data-team':p,style:`--summary-color:${textCol(p)}`},[
      el('h2',{},summary.title),el('p',{},summary.text)]));
  });
  host.hidden=!host.children.length;
}

function renderCards(){
  alignSummaries();
  const host=$('#cards'); host.innerHTML='';
  const order=[...P].sort((a,b)=>(val(b,'winpct').v??0)-(val(a,'winpct').v??0));
  P.forEach(p=>{
    const place=order.indexOf(p)+1;
    const c=el('div',{class:'card'});
    c.append(el('div',{class:'accent',style:`background:${col(p)}`}));
    c.append(el('div',{class:'who'},[
      el('span',{class:'nm'},FULL[p]),
      el('span',{class:'pill'},ord(place)+' of '+P.length)
    ]));
    c.append(el('div',{class:'rec'},fmt(val(p,'record').v,'record')));
    c.append(el('div',{class:'wr'},fmt(val(p,'winpct').v,'pct')+' win rate'));
    const metrics=el('div',{class:'card-metrics'});
    [['pyth','num1','Pythagorean'],['sos','signed2','SOS'],
     ['srs','signed2','SRS'],['sor','rank','SOR'],['mov','num1','MOV'],
     ['adjo','num1','AdjO'],['adjd','num1','AdjD']].forEach(([l,f,short])=>{
      const s=val(p,l);
      metrics.append(el('div',{class:'mini'},[
        el('span',{},measureLabel(l,short)),
        el('b',{},[fmt(s.v,f), s.rank&&l!=='sor'?el('span',{class:'rk'},`${ord(s.rank)} nat`):null])
      ]));
    });
    c.append(metrics);
    host.append(c);
  });
}

/* ---------- full stat table ---------- */
let statQuery='',statGroup='';
[...new Set(TABLE.map(m=>m.group))].forEach(g=>$('#statgroup').append(el('option',{value:g},g)));
$('#statsearch').addEventListener('input',e=>{statQuery=e.target.value.trim().toLowerCase();renderLead();});
$('#statgroup').addEventListener('change',e=>{statGroup=e.target.value;renderLead();});
function renderLead(){
  const t=$('#leadtable'); t.innerHTML='';
  const head=el('tr',{role:'row'},[el('th',{scope:'col',role:'columnheader'},'Stat'),...P.map(p=>el('th',{scope:'col',role:'columnheader'},p))]);
  t.append(el('thead',{role:'rowgroup'},head));
  const body=el('tbody',{role:'rowgroup'});
  let sec=null;
  const shown=TABLE.filter(m=>(!statGroup||m.group===statGroup)&&
    (!statQuery||`${m.name} ${m.pick} ${m.group} ${EXPLANATIONS[helpKey(m.key)]?.title||''}`.toLowerCase().includes(statQuery)));
  $('#statcount').textContent=`${shown.length} of ${TABLE.length} measures`;
  shown.forEach(m=>{
    if(m.group!==sec){sec=m.group;
      body.append(el('tr',{class:'sec'},el('td',{colspan:P.length+1},sec.includes('Approximate Value')?measureLabel('av',sec):sec)));}
    let best=null;
    if(m.higherBetter!=null){
      const nums=P.map(p=>({p,v:val(p,m.key).v})).filter(o=>typeof o.v==='number');
      if(nums.length){nums.sort((a,b)=>m.higherBetter?b.v-a.v:a.v-b.v);best=nums[0].p;}
    }
    const tr=el('tr',{role:'row'},[el('td',{role:'rowheader'},measureLabel(m.key,m.name))]);
    P.forEach(p=>{
      const s=val(p,m.key), isB=best===p;
      tr.append(el('td',{role:'cell',class:isB?'best':null,'data-team':FULL[p].replace(' Michigan','')},[
        isB?el('span',{class:'dot',style:`background:${col(p)}`}):null,
        isB?el('span',{class:'best-value',style:`color:${textCol(p)}`},fmt(s.v,m.fmt)):fmt(s.v,m.fmt),
        s.rank&&m.key!=='sor'?el('span',{class:'rk'},`${ord(s.rank)}`):null,
        coverageNote(m,p,s)
      ]));
    });
    body.append(tr);
  });
  if(!shown.length)body.append(el('tr',{},el('td',{colspan:4,class:'empty-state'},'No matching measures. Try another search or group.')));
  t.append(body);
}

/* ---------- head to head ---------- */
let h2hStat=initial.h2hStat||'pts';
function buildPick(sel,cur,opts,onPick){
  sel.innerHTML='';
  const groups={};
  opts.forEach(m=>{(groups[m.group]=groups[m.group]||[]).push(m);});
  for(const g in groups){
    const og=el('optgroup',{label:g});
    groups[g].forEach(m=>{const o=el('option',{value:m.key},m.pick);
      if(m.key===cur)o.selected=true;og.append(o);});
    sel.append(og);
  }
  sel.onchange=()=>onPick(sel.value);
}
function renderH2H(){
  const numeric=META.filter(m=>m.fmt!=='record'&&m.fmt!=='text');
  if(!numeric.some(m=>m.key===h2hStat))h2hStat=numeric[0].key;
  buildPick($('#h2hpick'),h2hStat,numeric,v=>{h2hStat=v;renderH2H();});
  const m=byKey[h2hStat];
  $('#h2h-help').hidden=!EXPLANATIONS[h2hStat];
  $('#h2h-help').onclick=()=>explain(h2hStat);
  $('#h2h-title').textContent=`${m.group} — ${m.name}`;
  $('#h2h-note').textContent=`${m.higherBetter===false?'Lower is better.':m.higherBetter?'Higher is better.':'Neutral measure.'}`;
  const caveats=P.map(p=>({p,s:val(p,m.key)})).filter(o=>o.s.note||o.s.partial||o.s.estimate);
  if(caveats.length)$('#h2h-note').textContent+=' '+caveats.map(o=>`${FULL[o.p]}: ${o.s.note||`${o.s.partial} games of data.`}`).join(' ');
  const lg=$('#h2h-legend'); lg.innerHTML='';
  P.forEach(p=>lg.append(el('div',{},[
    el('i',{style:`background:${col(p)}`}),FULL[p]])));

  const host=$('#bars'); host.innerHTML='';
  const rows=P.map(p=>({p,v:val(p,m.key).v,r:val(p,m.key).rank,partial:val(p,m.key).partial,estimate:val(p,m.key).estimate}))
              .filter(o=>typeof o.v==='number');
  if(!rows.length){host.append(el('p',{class:'note'},`Not captured for ${DATA.season}.`));}
  else{
    const W=Math.max(260,host.clientWidth),H=rows.length*58+16,padL=64,padR=110;
    const s=sv('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',height:H});
    const lo=Math.min(0,...rows.map(o=>o.v)), hi=Math.max(...rows.map(o=>o.v));
    const span=(hi-lo)||1, zero=padL+(0-lo)/span*(W-padL-padR);
    const lead=[...rows].sort((a,b)=>m.higherBetter===false?a.v-b.v:b.v-a.v)[0].p;
    rows.forEach((o,i)=>{
      const cy=34+i*58;
      const nm=sv('text',{x:padL-10,y:cy+4,'text-anchor':'end',
        fill:'var(--ink2)','font-size':13}); nm.textContent=({'W. Michigan':'WMU','E. Michigan':'EMU','C. Michigan':'CMU'})[o.p]||o.p; s.append(nm);
      const x=padL+(Math.min(0,o.v)-lo)/span*(W-padL-padR);
      const w=Math.max(3,Math.abs(o.v)/span*(W-padL-padR));
      const r=sv('rect',{x,y:cy-13,width:w,height:26,rx:7,fill:col(o.p),stroke:'var(--ink2)','stroke-width':1,
        opacity:o.p===lead?1:.6});
      r.addEventListener('mousemove',ev=>showTT(ev.clientX,ev.clientY,
        `<div class="tt-h">${FULL[o.p]}</div>${m.name}: <b>${fmt(o.v,m.fmt)}</b>`+
        (o.r?`<br><span style="color:var(--muted)">${ord(o.r)} nationally</span>`:'')));
      r.addEventListener('mouseleave',hideTT);
      s.append(r);
      const lab=sv('text',{x:x+w+8,y:cy+4,fill:'var(--ink)','font-size':13,'font-weight':600});
      lab.textContent=fmt(o.v,m.fmt)+(o.partial?` (${o.partial}g)`:o.estimate?' est.':''); s.append(lab);
    });
    if(lo<0)s.append(sv('line',{x1:zero,x2:zero,y1:10,y2:H-6,stroke:'var(--axis)','stroke-width':1}));
    host.append(s);
  }
  renderRadar();
}

const AXES=[['ypp',1,'Yds/Play'],['oeff',1,'Off Eff'],['winpct',1,'Win %'],
            ['d3rate',1,'3rd Down'],['rzrate',1,'Red Zone'],['deff',-1,'Def Eff'],
            ['yppa',-1,'Yds/Play Alw'],['todiff',1,'TO Diff']];
function renderRadar(){
  const host=$('#radar'); host.innerHTML='';
  if(P.some(p=>AXES.some(([k])=>typeof val(p,k).v!=='number'))){host.append(el('p',{class:'note'},'The radar profile needs all eight measures for every team. Some are unavailable for this season.'));return;}
  const S=300,cx=S/2,cy=S/2,R=98;
  // pad the viewBox so the outer axis labels are not clipped at either edge
  const s=sv('svg',{viewBox:`-30 -14 ${S+60} ${S+34}`,width:'100%'});
  const n=AXES.length;
  for(let ring=1;ring<=3;ring++){
    const pts=[...Array(n)].map((_,i)=>{
      const a=-Math.PI/2+i*2*Math.PI/n, r=R*ring/3;
      return `${cx+Math.cos(a)*r},${cy+Math.sin(a)*r}`;}).join(' ');
    s.append(sv('polygon',{points:pts,fill:'none',stroke:'var(--grid)','stroke-width':1}));
  }
  AXES.forEach(([k,dir,lab],i)=>{
    const a=-Math.PI/2+i*2*Math.PI/n;
    s.append(sv('line',{x1:cx,y1:cy,x2:cx+Math.cos(a)*R,y2:cy+Math.sin(a)*R,
      stroke:'var(--grid)','stroke-width':1}));
    const t=sv('text',{x:cx+Math.cos(a)*(R+16),y:cy+Math.sin(a)*(R+16)+3,
      'text-anchor':Math.abs(Math.cos(a))<.3?'middle':(Math.cos(a)>0?'start':'end'),
      fill:'var(--muted)','font-size':8.5});
    t.textContent=lab;
    s.append(t);
  });
  const norm=AXES.map(([k,dir,lab])=>{
    const vs=P.map(p=>val(p,k).v).filter(v=>typeof v==='number');
    if(!vs.length)return null;
    const lo=Math.min(...vs),hi=Math.max(...vs);
    return {k,lab,dir,lo,hi,span:(hi-lo)||1};
  });
  P.forEach(p=>{
    const pts=[];
    norm.forEach((o,i)=>{
      const a=-Math.PI/2+i*2*Math.PI/n;
      let f=.55;
      if(o){const v=val(p,o.k).v;
        if(typeof v==='number'){const t=(v-o.lo)/o.span; f=.2+.8*(o.dir>0?t:1-t);}}
      pts.push([cx+Math.cos(a)*R*f, cy+Math.sin(a)*R*f, i, f]);
    });
    s.append(sv('polygon',{points:pts.map(q=>q[0]+','+q[1]).join(' '),fill:'none',stroke:'var(--ink2)','stroke-width':4}));
    s.append(sv('polygon',{points:pts.map(q=>q[0]+','+q[1]).join(' '),
      fill:col(p),'fill-opacity':.12,stroke:col(p),'stroke-width':2}));
    pts.forEach(([x,y,i])=>{
      const o=norm[i]; if(!o)return;
      const c=sv('circle',{cx:x,cy:y,r:3.6,fill:col(p),stroke:'var(--surface)','stroke-width':1.4});
      c.addEventListener('mousemove',ev=>showTT(ev.clientX,ev.clientY,
        `<div class="tt-h">${FULL[p]}</div>${byKey[o.k].name}: <b>${fmt(val(p,o.k).v,byKey[o.k].fmt)}</b>`));
      c.addEventListener('mouseleave',hideTT);
      s.append(c);
    });
  });
  host.append(s);
}

/* ---------- schedules ---------- */
function renderSched(){
  const host=$('#scheds'); host.innerHTML='';
  P.forEach(p=>{
    const c=el('div',{class:'card'});
    c.append(el('div',{class:'accent',style:`background:${col(p)}`}));
    c.append(el('div',{class:'who'},[el('span',{class:'nm'},FULL[p])]));
    c.append(el('div',{class:'wr'},`${fmt(val(p,'record').v,'record')}  ·  `+
      `${fmt(val(p,'pts').v,'int')} scored / ${fmt(val(p,'ptsa').v,'int')} allowed`));
    (DATA.schedules[p]||[]).forEach(g=>{
      const site=g.site==='H'?'vs':(g.site==='A'?'@':'n');
      const line=el('div',{class:'gm'},[
        el('span',{class:'wk'},'Wk '+g.wk),
        el('span',{class:'st '+(g.w?'W':'L')},g.w?'W':'L'),
        el('span',{class:'op'},[
          el('span',{style:'color:var(--muted)'},site+' '),
          g.opp, g.oppRec?el('span',{class:'rk'},`(${g.oppRec})`):null]),
        el('span',{class:'sc'},`${g.pf}–${g.pa}`+(g.ot?' OT':''))
      ]);
      line.title = g.oppSrs!=null ? `${g.opp}: ${g.oppRec}, SRS ${g.oppSrs>0?'+':''}${g.oppSrs}` : g.opp;
      c.append(line);
    });
    host.append(c);
  });
}

/* ---------- national ---------- */
const NATCOLS=[['t','Team','text'],['w','W','int'],['l','L','int'],['pf','PF','int'],
  ['pa','PA','int'],['mov','MOV','num1'],['sos','SOS','signed2'],['sor','SOR','rank'],['srs','SRS','num2'],
  ['elo','Elo','num0'],['bt','Bradley-Terry','num0'],['g2','Glicko-2','num0']];
let natSort='srs', natDesc=true, natQ='';
function renderNational(){
  const pm=DATA.params;
  $('#nat-note').textContent =
    `${DATA.ratings.length} teams from ${DATA.coverage.games} games. SRS is in points and centred so the average team is 0.0. `+
    `Home-field advantage ${(pm.estimated_home_field_advantage?.toFixed(2)??'unavailable')} pts (${pm.home_field_estimation_method||'not yet estimated'}). `+
    `Rows marked “synthetic” represent FCS buckets; these are excluded from FBS rankings.`;
  const t=$('#nattable'); t.innerHTML='';
  const head=el('tr',{});
  NATCOLS.forEach(([k,lab])=>{
    const th=el('th',{'aria-sort':natSort===k?(natDesc?'descending':'ascending'):'none'});
    const sort=el('button',{class:'sort-button',type:'button','aria-label':`Sort by ${lab}`},
      EXPLANATIONS[k]?(natSort===k?(natDesc?'▾':'▴'):'↕'):lab+(natSort===k?(natDesc?' ▾':' ▴'):''));
    sort.onclick=()=>{if(natSort===k)natDesc=!natDesc;else{natSort=k;natDesc=k!=='sor';}renderNational();};
    th.append(el('span',{class:'sort-help'},[EXPLANATIONS[k]?measureLabel(k,lab):null,sort]));
    head.append(th);
  });
  t.append(el('thead',{},head));
  const mine=new Set(P.map(p=>DATA.canon[p]));
  let rows=DATA.ratings.filter(r=>!natQ||r.t.toLowerCase().includes(natQ));
  rows=[...rows].sort((a,b)=>{
    const x=a[natSort],y=b[natSort];
    if(x==null)return y==null?0:1;
    if(y==null)return -1;
    if(typeof x==='string')return natDesc?y.localeCompare(x):x.localeCompare(y);
    return natDesc?y-x:x-y;});
  const body=el('tbody');
  rows.forEach(r=>{
    const who=P.find(p=>DATA.canon[p]===r.t);
    const tr=el('tr',{class:mine.has(r.t)?'me':null});
    NATCOLS.forEach(([k,lab,f])=>{
      if(k==='t'){
        tr.append(el('td',{},[
          who?el('span',{class:'dot',style:`background:${col(who)}`}):null,
          r.t, r.syn?el('span',{class:'rk'},'synthetic'):null]));
      } else tr.append(el('td',{},fmt(r[k],f)));
    });
    body.append(tr);
  });
  t.append(body);
  $('#natcount').textContent=`${rows.length} shown`;

  const opts=Object.keys(DATA.nationalLeaders).map(k=>byKey[k]).filter(Boolean);
  if(opts.length){
    if(!DATA.nationalLeaders[natStat])natStat=opts[0].key;
    buildPick($('#natpick'),natStat,opts,v=>{natStat=v;renderNatTop();});
    renderNatTop();
  }else $('#nattop').replaceChildren(el('caption',{},'No national leader data for this season.'));
}
let natStat=initial.natStat||'srs';
function renderNatTop(){
  const m=byKey[natStat], list=DATA.nationalLeaders[natStat]||[];
  const t=$('#nattop'); t.innerHTML='';
  t.append(el('thead',{},el('tr',{},[el('th',{},'#'),el('th',{class:'lft'},'Team'),
    el('th',{},`${m.group} — ${m.name}`)])));
  const body=el('tbody'); const mine=new Set(P.map(p=>DATA.canon[p]));
  list.forEach((r,i)=>{
    const who=P.find(p=>DATA.canon[p]===r.t);
    body.append(el('tr',{class:mine.has(r.t)?'me':null},[
      el('td',{},String(i+1)),
      el('td',{class:'lft',style:who?`color:${textCol(who)}`:null},[
        who?el('span',{class:'dot',style:`background:${col(who)}`}):null,r.t]),
      el('td',{},fmt(r.v,m.fmt))]));
  });
  t.append(body);
}
$('#natsearch').addEventListener('input',e=>{natQ=e.target.value.trim().toLowerCase();renderNational();});

/* ---------- player leaders ---------- */
let leadCat=initial.leadCat||null;
function renderLeaders(){
  const L={...(DATA.playerLeaders||{})};
  const tflCategory='TACKLES FOR LOSS';
  if(L.DEFENSE){
    L[tflCategory]={columns:['GP','TFL','TAK','SACK'],
      rows:L.DEFENSE.rows.filter(r=>typeof r.values.TFL==='number')
        .slice().sort((a,b)=>b.values.TFL-a.values.TFL||a.name.localeCompare(b.name))};
  }
  const cats=Object.keys(L);
  const note=$('#lead-note');
  if(!cats.length){
    note.textContent='Not available — the player leaderboards were not transcribed for this build.';
    $('#leadtbl').innerHTML=''; $('#leadrow').classList.add('hide'); return;
  }
  $('#leadrow').classList.remove('hide');
  if(!leadCat||!L[leadCat])leadCat=cats[0];
  const sel=$('#leadpick'); sel.innerHTML='';
  cats.forEach(c=>{const o=el('option',{value:c},c);if(c===leadCat)o.selected=true;sel.append(o);});
  sel.onchange=()=>{leadCat=sel.value;renderLeaders();};
  const d=L[leadCat], t=$('#leadtbl'); t.innerHTML='';
  // Capture completeness describes the recorded list, not every national player.
  const depth=(DATA.leaderDepth||{})[leadCat]||d.rows.length;
  const whole=(DATA.leaderComplete||{})[leadCat];
  const isTfl=leadCat===tflCategory;
  note.textContent=isTfl
    ? `Tackles for loss among ${d.rows.length} captured defensive players, sorted by TFL. Captured rank compares only these players, with ties sharing a rank. The video was sorted by total tackles, so players outside that list may have more TFL. This is not a complete national TFL ranking or a team total. Schools are shown only where verified.`
    : leadCat==='DEFENSE'
    ? `All ${depth} players from the recorded defense list, sorted by total tackles. TFL means tackles for loss. This list does not include every defender nationally, so it cannot establish complete national TFL rankings or team totals. Schools are shown only where verified.`
    : `${depth} captured players in ${leadCat}, sorted by ${DATA.leaderCoverage?.[leadCat]?.sortedBy||d.sortedBy||'the recorded measure'}. `+
      (whole?'The capture reaches the end of the recorded list. ':'The capture covers only part of the recorded list. ')+
      (DATA.leaderCoverage?.[leadCat]?.nationalComplete?'National coverage is verified. ':'This is not verified as a complete list of every eligible player nationally. ')+
      'Schools are shown only where verified.';
  // a derived column is worked out from the printed ones rather than read off the
  // screen, so it is marked instead of being passed off as a transcription
  const derivedCols=new Set(d.derived||[]);
  if(derivedCols.size)note.textContent+=` ${(d.derived||[]).join(' and ')} are derived from the printed columns, not read off the screen.`;
  t.append(el('thead',{},el('tr',{},[el('th',{},isTfl?'Captured rank':'#'),el('th',{class:'lft'},'Player'),
    el('th',{class:'lft'},'Pos'), ...d.columns.map(c=>el('th',
      derivedCols.has(c)?{class:'calc',title:'Derived from the printed columns, not read from the screen'}:{},
      c))])));
  // a column that holds any fractional value (half sacks, averages) is shown
  // with one decimal throughout, so the column reads consistently
  const frac={};
  d.columns.forEach(c=>frac[c]=d.rows.some(r=>typeof r.values[c]==='number'&&!Number.isInteger(r.values[c])));
  const num=(v,c)=>v==null?'—':(typeof v==='number'
    ? (frac[c]?v.toFixed(1):v.toLocaleString()) : String(v));
  // a player whose team we could read, and who plays for one of the three, is
  // tinted in that coach's colour — the payoff for reading the side panel
  const whoOf=t=>t?P.find(p=>DATA.canon[p]===t||p===t||FULL[p]===t):null;
  const body=el('tbody');
  let capturedRank=0;
  d.rows.forEach((r,i)=>{
    if(!i||r.values.TFL!==d.rows[i-1].values.TFL)capturedRank=i+1;
    const who=whoOf(r.team);
    body.append(el('tr',{class:who?'me':null},[
      el('td',{},String(isTfl?capturedRank:i+1)),
      el('td',{class:'lft',style:who?`color:${textCol(who)}`:null},[
        who?el('span',{class:'dot',style:`background:${col(who)}`}):null,
        r.name, r.team?el('span',{class:'rk'},r.team):null]),
      el('td',{class:'lft'},r.pos||'—'),
      ...d.columns.map(c=>el('td',{},num(r.values[c],c)))]));
  });
  t.append(body);
}

/* ---------- footer ---------- */
$('#foot').replaceChildren(
  el('p',{},`Blank measures: ${DATA.missingRows.length}. A dash means unavailable, not zero.`),
  el('p',{},DATA.seasonNotes.coverage),
  el('p',{},DATA.seasonNotes.av));

/* ---------- render ---------- */
function render(){
  if(view==='dynasty'){renderCards();renderLead();}
  else if(view==='h2h')renderH2H();
  else if(view==='sched')renderSched();
  else if(view==='national')renderNational();
  else if(view==='leaders')renderLeaders();
}
let resizeFrame;
addEventListener('resize',()=>{
  cancelAnimationFrame(resizeFrame);
  resizeFrame=requestAnimationFrame(()=>{if(view==='h2h')renderH2H();});
});
setView(view);
return {
  setView, render, toggleTheme,
  closeOverlays:()=>{if(dialog.open)dialog.close();hideTT();},
  state:()=>({view,h2hStat,natStat,leadCat}),
  destroy:()=>{events.abort();cancelAnimationFrame(resizeFrame);if(dialog.open)dialog.close();document.body.classList.remove('dialog-open');root.replaceChildren();}
};
}
