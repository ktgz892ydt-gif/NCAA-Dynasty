import {mountSeason} from './views/season.js';
import {renderHistory} from './views/history.js';
const $=s=>document.querySelector(s);
const panel=$('#season-panel'), tabs=$('#season-tabs'), status=$('#load-status'), historyPanel=$('#history-panel');
let manifest, seasons=[], current=null, activeId=null, generation=0, historyMode=false;
const cache=new Map();
const views=new Set(['dynasty','h2h','sched','national','leaders']);

async function json(path){
  const response=await fetch(new URL(path,document.baseURI),{cache:'no-cache'});
  if(!response.ok)throw new Error(`Could not load ${path} (${response.status}).`);
  return response.json();
}
function message(text,retry){
  status.replaceChildren(document.createTextNode(text));
  if(retry){const b=document.createElement('button');b.className='ghost';b.textContent='Retry';b.onclick=retry;status.append(' ',b);}
}
function address(season,view,mode='push'){
  const url=new URL(location.href);url.searchParams.set('season',season);url.searchParams.set('view',view);
  if(url.href!==location.href)history[mode==='replace'?'replaceState':'pushState']({},'',url);
}
async function dataset(entry){
  if(cache.has(entry.id))return cache.get(entry.id);
  const d=await json(entry.dataPath);
  if(d.schemaVersion!==1||String(d.season)!==entry.id||d.metadata?.id!==entry.id||!Array.isArray(d.teams)||!Array.isArray(d.statMeta)||!Array.isArray(d.ratings)||!Array.isArray(d.teamConfig))throw new Error(`The ${entry.id} season file is invalid.`);
  cache.set(entry.id,d);return d;
}
function mark(){
  [...tabs.children].forEach(b=>{const selected=b.dataset.season===activeId;b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});
  if(!activeId&&tabs.firstChild)tabs.firstChild.tabIndex=0;
  $('#history-button').setAttribute('aria-pressed',String(historyMode));
}
function selectView(view){
  if(!views.has(view))view='dynasty';
  current?.setView(view);address(activeId,view);
}
async function selectSeason(id,view=null,mode='push'){
  const ticket=++generation, entry=seasons.find(s=>s.id===id);
  current?.closeOverlays();
  historyMode=false;historyPanel.hidden=true;
  // Hide the previous season while loading; its heading and values remain together.
  panel.hidden=true;panel.setAttribute('aria-busy','true');
  mark();
  if(!entry){
    message(`Season ${id} is not published. Choose an available season above.`);
    panel.removeAttribute('aria-busy');return;
  }
  message(`Loading ${entry.label}…`);
  const previous=current?.state()||{};
  try{
    const d=await dataset(entry);if(ticket!==generation)return;
    current?.destroy();panel.replaceChildren($('#season-template').content.cloneNode(true));
    const requested=view||previous.view||'dynasty';
    const section=({'schedules':'sched','head-to-head':'h2h'})[requested]||requested;
    current=mountSeason(panel,d,{...previous,view:section},v=>address(id,v));
    activeId=id;panel.hidden=false;panel.removeAttribute('aria-busy');panel.setAttribute('aria-labelledby','season-'+id);
    document.title=`Dynasty HQ — ${entry.label}`;mark();message('');
    if(mode)address(id,current.state().view,mode);
  }catch(error){
    if(ticket!==generation)return;
    panel.hidden=true;panel.removeAttribute('aria-busy');
    message(`Unable to open ${entry.label}. ${error.message}`,()=>selectSeason(id,view,mode));
  }
}
async function showHistory(mode='push'){
  const ticket=++generation;current?.closeOverlays();historyMode=true;panel.hidden=true;historyPanel.hidden=true;mark();message('Loading dynasty history…');
  try{
    const data=await Promise.all(seasons.map(dataset));if(ticket!==generation)return;
    renderHistory(historyPanel,data);historyPanel.hidden=false;message('');document.title='Dynasty HQ — History';
    if(mode)address(activeId||manifest.defaultSeason,'history',mode);
  }catch(error){if(ticket===generation)message(`Unable to open history. ${error.message}`,()=>showHistory(mode));}
}
function fromUrl(mode=null){
  const q=new URLSearchParams(location.search),id=q.get('season')||manifest.defaultSeason;
  if(q.get('view')==='history')return showHistory(mode);
  return selectSeason(id,q.get('view')||'dynasty',mode);
}
tabs.addEventListener('click',e=>{const b=e.target.closest('[data-season]');if(b)selectSeason(b.dataset.season);});
tabs.addEventListener('keydown',e=>{
  const keys=['ArrowLeft','ArrowRight','Home','End'];if(!keys.includes(e.key))return;
  const bs=[...tabs.children];let index=bs.indexOf(document.activeElement);if(index<0)return;e.preventDefault();
  index=e.key==='Home'?0:e.key==='End'?bs.length-1:(index+(e.key==='ArrowRight'?1:-1)+bs.length)%bs.length;
  bs[index].focus();selectSeason(bs[index].dataset.season);
});
$('#history-button').onclick=()=>showHistory();
$('#theme').onclick=()=>{
  document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';current?.render();
};
addEventListener('popstate',()=>{if(manifest)fromUrl();});
async function start(){
  try{
    manifest=await json('data/seasons.json');
    if(manifest.schemaVersion!==1||!Array.isArray(manifest.seasons))throw new Error('Invalid season manifest.');
    seasons=manifest.seasons.filter(s=>s.published===true).sort((a,b)=>a.id.localeCompare(b.id));
    if(!seasons.length||!seasons.some(s=>s.id===manifest.defaultSeason)||new Set(seasons.map(s=>s.id)).size!==seasons.length)throw new Error('No valid default published season.');
    tabs.replaceChildren();
    for(const entry of seasons){
      if(!/^\d{4}$/.test(entry.id)||entry.dataPath!==`data/seasons/${entry.id}/season.json`)throw new Error('Invalid season path.');
      const b=document.createElement('button');b.type='button';b.className='season-tab';b.id='season-'+entry.id;b.dataset.season=entry.id;b.textContent=entry.label;b.setAttribute('role','tab');b.setAttribute('aria-controls','season-panel');tabs.append(b);
    }
    mark();await fromUrl('replace');
  }catch(error){message(`Unable to load seasons. ${error.message}`,start);}
}
start();
