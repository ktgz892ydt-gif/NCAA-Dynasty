// History loads only published seasons. Cross-season ratings stay labeled by year.
const cell=(tag,text)=>{const e=document.createElement(tag);e.textContent=text??'—';return e;};
function table(host,headers,rows,caption){
 const sc=document.createElement('div');sc.className='scroll history-block';sc.tabIndex=0;sc.setAttribute('role','region');sc.setAttribute('aria-label',caption);
 const t=document.createElement('table');t.className='history-table';t.append(cell('caption',caption));
 const head=document.createElement('thead'),tr=document.createElement('tr');headers.forEach(x=>tr.append(cell('th',x)));head.append(tr);t.append(head);
 const body=document.createElement('tbody');rows.forEach(row=>{const tr=document.createElement('tr');row.forEach(x=>tr.append(cell('td',x)));body.append(tr);});t.append(body);sc.append(t);host.append(sc);
}
const format=(v,m)=>v==null?'—':m?.fmt==='pct'?(100*v).toFixed(1)+'%':m?.fmt==='rank'?'#'+v:typeof v==='number'?(Number.isInteger(v)?String(v):v.toFixed(2)):String(v);
export function renderHistory(host,seasons){
 host.replaceChildren();host.append(cell('h2','Dynasty history'));
 host.append(cell('p',`${seasons.length} published season${seasons.length===1?'':'s'}. Statistics follow each season’s recorded coverage. Ratings describe standing within that season; they are not a prediction across years.`));
 const controls=document.createElement('div');controls.className='history-controls';host.append(controls);
 const teamLabel=cell('label','Program'),teamSelect=document.createElement('select');teamLabel.append(teamSelect);controls.append(teamLabel);
 const allteams=new Map();seasons.forEach(d=>d.teamConfig.forEach(t=>allteams.set(t.id,t)));
 for(const [id,t] of allteams){const o=cell('option',t.name);o.value=id;teamSelect.append(o);}
 const details=document.createElement('div');host.append(details);
 function draw(){
  details.replaceChildren();const id=teamSelect.value, entries=seasons.flatMap(d=>{const t=d.teamConfig.find(t=>t.id===id);return t?[{d,t,v:d.values[t.short]}]:[];});
  table(details,['Season','Record','Conference champion','Bowl','Final CFP','SRS','SOR','AdjO','AdjD'],entries.map(({d,v})=>[d.season,...['record','confchamp','bowl','cfp','srs','sor','adjo','adjd'].map(k=>format(v[k]?.v,d.statMeta.find(m=>m.key===k)))]),'Program seasons');
  for(const {d} of entries)details.append(cell('p',`${d.season}: ${d.metadata.coverage.statistics} ${d.metadata.coverage.results}`));
  const comparison=document.createElement('div');comparison.className='history-controls';details.append(comparison);
  const selectors=['First season','Second season'].map(label=>{const l=cell('label',label),s=document.createElement('select');entries.forEach(({d})=>{const o=cell('option',d.season);o.value=d.season;s.append(o);});l.append(s);comparison.append(l);return s;});
  if(entries.length>1)selectors[1].selectedIndex=entries.length-1;
  const compare=document.createElement('div');details.append(compare);
  function drawCompare(){
   compare.replaceChildren();if(entries.length<2){compare.append(cell('p','Season-to-season comparison becomes available when a second season is published.'));return;}
   const a=entries.find(e=>e.d.season===selectors[0].value),b=entries.find(e=>e.d.season===selectors[1].value);
   if(a.d.metadata.methodVersion!==b.d.metadata.methodVersion||a.d.metadata.regulationGameSeconds!==b.d.metadata.regulationGameSeconds)compare.append(cell('p','These seasons use different calculation methods or game lengths; interpret the comparison with those differences in mind.'));
   const metrics=a.d.statMeta.filter(m=>m.fmt!=='text'&&b.d.statMeta.some(n=>n.key===m.key));
   table(compare,['Measure',a.d.season,b.d.season],metrics.map(m=>[m.pick||m.name,format(a.v[m.key]?.v,m),format(b.v[m.key]?.v,m)]),'Season comparison');
  }
  selectors.forEach(s=>s.onchange=drawCompare);drawCompare();
  const games=[];
  for(const {d,t} of entries){const names=new Set(d.teamConfig.filter(x=>x.id!==id).map(x=>x.canonical));
   for(const g of d.scoreboard){if((g.a===t.canonical&&names.has(g.h))||(g.h===t.canonical&&names.has(g.a))){const home=g.h===t.canonical;const pf=home?g.hs:g.as,pa=home?g.as:g.hs;games.push([d.season,g.wk,home?g.a:g.h,g.n?'Neutral':home?'Home':'Away',pf>pa?'W':'L',`${pf}–${pa}`]);}}
  }
  table(details,['Season','Week','Opponent','Site','Result','Score'],games,'Recorded dynasty rivalry games');
  const records=[];
  for(const key of ['pts','pyds','ryds','ypp','mov']){
   const available=entries.filter(e=>typeof e.v[key]?.v==='number');if(!available.length)continue;
   const best=Math.max(...available.map(e=>e.v[key].v));const winners=available.filter(e=>e.v[key].v===best);
   records.push([available[0].d.statMeta.find(m=>m.key===key)?.pick||key,format(best,available[0].d.statMeta.find(m=>m.key===key)),winners.map(e=>e.d.season).join(', ')]);
  }
  table(details,['Measure','Best captured value','Season'],records,'Program record book — recorded season values; totals depend on games played');
  details.append(cell('p','Player career totals are unavailable until identities are verified across seasons. Initials and surnames alone are not used to combine players.'));
 }
 teamSelect.onchange=draw;draw();
 // Player seasons remain separate records, even when abbreviated names match.
 const playerHost=document.createElement('div');host.append(playerHost);
 playerHost.append(cell('h2','Captured player season records'));
 playerHost.append(cell('p','Highest recorded values across published seasons. Coverage differs by category and year; these are captured-list records, not complete national or career rankings.'));
 const playerControls=document.createElement('div');playerControls.className='history-controls';playerHost.append(playerControls);
 const categoryLabel=cell('label','Player category'),category=document.createElement('select');categoryLabel.append(category);playerControls.append(categoryLabel);
 const measureLabel=cell('label','Recorded measure'),measure=document.createElement('select');measureLabel.append(measure);playerControls.append(measureLabel);
 const categories=[...new Set(seasons.flatMap(d=>Object.keys(d.playerLeaders||{})))];
 categories.forEach(c=>{const o=cell('option',c);o.value=c;category.append(o);});
 const records=document.createElement('div');playerHost.append(records);
 function showRecords(){
  records.replaceChildren();const k=measure.value;
  const rows=seasons.flatMap(d=>(d.playerLeaders?.[category.value]?.rows||[]).map(r=>({season:d.season,player:r,value:r.values[k]}))).filter(r=>typeof r.value==='number');
  rows.sort((a,b)=>b.value-a.value||a.season.localeCompare(b.season)||a.player.name.localeCompare(b.player.name));
  const shown=rows.slice(0,10);table(records,['Season','Player','School','Position',k||'Value'],shown.map(r=>[r.season,r.player.name,r.player.team||'Unknown',r.player.pos,format(r.value)]),'Top ten captured player-season entries by value (higher first)');
 }
 function changeCategory(){
  const definitions=seasons.map(d=>d.playerLeaders?.[category.value]).filter(Boolean);
  const columns=[...new Set(definitions.flatMap(d=>d.columns))].filter(c=>definitions.some(d=>d.rows.some(r=>typeof r.values[c]==='number')));
  measure.replaceChildren();columns.forEach(c=>{const o=cell('option',c);o.value=c;measure.append(o);});
  const preferred=definitions[0]?.sortedBy;if(columns.includes(preferred))measure.value=preferred;
  showRecords();
 }
 category.onchange=changeCategory;measure.onchange=showRecords;changeCategory();
}
