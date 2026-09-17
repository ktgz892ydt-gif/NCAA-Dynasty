// Run against a local preview server. Synthetic seasons exist only in intercepted test responses.
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.PREVIEW_URL||'http://127.0.0.1:8765/';
const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
const errors=[];
try{
 const page=await browser.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base);await page.locator('#cards .card').first().waitFor();
 assert.equal(await page.getByRole('tab').count(),1);
 assert.equal(await page.title(),'Dynasty HQ — 2026');
 for(const width of [320,390,768,1280]){
  await page.setViewportSize({width,height:900});
  for(const view of ['dynasty','h2h','sched','national','leaders']){
   await page.locator(`[data-v="${view}"]`).click();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${view} overflow at ${width}`);
  }
  await page.locator('#leadpick').selectOption('TACKLES FOR LOSS');assert.equal(await page.locator('#leadtbl tbody tr').count(),400);
  await page.locator('[data-v="dynasty"]').click();assert.equal(await page.locator('.season-summary').count(),3);
  await page.getByRole('button',{name:'Explain SOR',exact:true}).first().click();
  assert.ok((await page.locator('#measure-detail').innerText()).includes('18.89'));
  await page.keyboard.press('Escape');await page.locator('#theme').click();
 }
 await page.locator('#history-button').click();await page.locator('#history-panel table').first().waitFor();
 assert.ok((await page.locator('#history-panel').innerText()).includes('second season'));
 await page.goBack();await page.locator('#cards .card').first().waitFor();
 await page.goto(base+'?season=2099');await page.getByText('Season 2099 is not published.',{exact:false}).waitFor();
 await page.getByRole('tab',{name:'2026'}).click();await page.locator('#cards .card').first().waitFor();
 const real=await (await page.request.get(base+'data/seasons/2026/season.json')).json();
 const manifest={schemaVersion:1,defaultSeason:'2026',seasons:Array.from({length:6},(_,i)=>({id:String(2026+i),label:String(2026+i),published:true,dataPath:`data/seasons/${2026+i}/season.json`}))};
 const fixture=year=>{
  const d=structuredClone(real);d.season=year;d.metadata.id=year;d.metadata.label=year;d.metadata.coverage.statistics=`Synthetic ${year} fixture only.`;d.metadata.coverage.results='';
  d.seasonNotes.coverage=`Synthetic ${year} fixture only.`;
  d.summaries=d.summaries.map(s=>({...s,title:`Synthetic ${year} ${s.teamId}`,text:`Test-only summary for ${year}.`}));
  d.values['W. Michigan'].record.v=year==='2027'?'1-0':'2-0';
  if(year==='2027')d.playerLeaders={};
  return d;
 };
 await page.route('**/data/seasons.json',r=>r.fulfill({json:manifest}));
 let fail2027=true;
 await page.route(/\/data\/seasons\/20(27|28|29|30|31)\/season.json/,async r=>{
  const year=r.request().url().match(/seasons\/(\d+)\//)[1];
  if(year==='2027'&&fail2027){fail2027=false;await r.fulfill({status:503,body:'temporary test failure'});return;}
  if(year==='2027')await new Promise(ok=>setTimeout(ok,300));
  await r.fulfill({json:fixture(year)});
 });
 await page.goto(base+'?season=2026&view=schedules');
 // Readable section aliases preserve shared links from the plan.
 await page.locator('#v-sched').waitFor();
 await page.locator('[data-v="sched"]').click();
 await page.getByRole('tab',{name:'2027'}).click();await page.getByRole('button',{name:'Retry',exact:true}).waitFor();
 assert.equal(await page.locator('#season-panel').isVisible(),false);
 await page.getByRole('button',{name:'Retry',exact:true}).click();await page.waitForURL('**season=2027**');
 assert.equal(await page.locator('#v-sched').isVisible(),true);
 await page.locator('[data-v="leaders"]').click();assert.ok((await page.locator('#lead-note').innerText()).includes('Not available'));
 await page.getByRole('tab',{name:'2026'}).click();await page.waitForURL('**season=2026**');assert.equal(await page.locator('#leadtbl tbody tr').count()>0,true);
 await page.locator('[data-v="dynasty"]').click();
 await page.getByRole('button',{name:'Explain SOR',exact:true}).first().click();
 // Season tabs are outside the modal; Escape first, then switching must dispose the modal.
 await page.keyboard.press('Escape');
 for(const year of ['2028','2026','2027','2026']){await page.getByRole('tab',{name:year}).click();await page.waitForURL(`**season=${year}**`);assert.equal(await page.locator('#measure-dialog').count(),1);}
 await page.getByRole('tab',{name:'2026'}).focus();await page.keyboard.press('ArrowRight');await page.waitForURL('**season=2027**');
 await page.locator('#history-button').click();await page.locator('#history-panel table').first().waitFor();
 assert.ok((await page.locator('#history-panel').innerText()).includes('6 published seasons'));
 assert.equal(await page.locator('#history-panel select').count(),5);
 assert.ok((await page.locator('#history-panel').innerText()).includes('Captured player season records'));
 await page.goBack();await page.locator('#cards .card').first().waitFor();assert.equal(await page.title(),'Dynasty HQ — 2027');
 // Fresh page checks delayed response races (no populated dataset cache).
 const race=await browser.newPage({viewport:{width:320,height:900}});race.on('pageerror',e=>errors.push(e.message));
 await race.route('**/data/seasons.json',r=>r.fulfill({json:manifest}));
 await race.route(/\/data\/seasons\/20(27|28)\/season.json/,async r=>{const y=r.request().url().match(/seasons\/(\d+)\//)[1];if(y==='2027')await new Promise(ok=>setTimeout(ok,500));await r.fulfill({json:fixture(y)});});
 await race.goto(base);await race.locator('#cards .card').first().waitFor();
 await race.getByRole('tab',{name:'2027'}).click();await race.getByRole('tab',{name:'2028'}).click();await race.waitForURL('**season=2028**');
 await race.waitForTimeout(650);assert.equal(await race.title(),'Dynasty HQ — 2028');assert.ok((await race.locator('.season-summaries').innerText()).includes('2028'));
 assert.equal(await race.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);
 console.log('PASS: real 2026 views, phone layouts, TFL, dialog, history, six synthetic tabs, keyboard, links, back navigation, missing categories, retry and race protection.');
}finally{await browser.close();}
