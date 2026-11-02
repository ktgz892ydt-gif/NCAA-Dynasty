// Run against: python3 -B scripts/preview.py --port 8765
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.PREVIEW_URL||'http://127.0.0.1:8765/';
const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
const errors=[];
try{
  const page=await browser.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);
  const manifest=await (await page.request.get(base+'data/seasons.json')).json();
  assert.equal(manifest.defaultSeason,'2027');
  assert.deepEqual(manifest.seasons.filter(s=>s.published).map(s=>s.id),['2026','2027']);
  await page.locator('#cards .card').first().waitFor();
  assert.equal(await page.title(),'Dynasty HQ — 2027');
  assert.equal(await page.getByRole('tab').count(),2);
  assert.deepEqual(await page.locator('#cards .rec').allTextContents(),['11-1','4-8','11-1']);
  assert.deepEqual(await page.locator('#cards .pill').allTextContents(),['Tied 1st of 3','3rd of 3','Tied 1st of 3']);
  assert.ok((await page.locator('#coverage-detail').textContent()).includes('12-game regular season'));
  assert.equal(await page.locator('.season-summary').count(),3);
  for(const width of [320,390,768,1280]){
    await page.setViewportSize({width,height:900});
    for(const view of ['dynasty','h2h','sched','national','leaders']){
      await page.locator(`[data-v="${view}"]`).click();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${view} overflows at ${width}`);
    }
    for(const category of ['PASSING','DEFENSE','TACKLES FOR LOSS','KICKING']){
      await page.locator('#leadpick').selectOption(category);
      assert.ok((await page.locator('#lead-note').innerText()).includes('12-game regular-season window'));
      assert.ok((await page.locator('#lead-note').innerText()).includes('ambiguous matches are withheld'));
    }
    await page.locator('#leadpick').selectOption('DEFENSE');
    assert.equal(await page.locator('#leadtbl').getByText('estimated split',{exact:true}).count(),2);
    await page.locator('#leadpick').selectOption('KICKING');
    assert.ok(await page.locator('#leadtbl tbody tr').count()>100);
    assert.ok((await page.locator('#leadtbl').innerText()).includes('N.Hancock'));
    await page.locator('[data-v="national"]').click();
    await page.locator('#natpick').selectOption('pyds');
    assert.ok((await page.locator('#nattop-note').innerText()).includes('138 of 138'));
    await page.locator('#natpick').selectOption('sacks');
    assert.ok((await page.locator('#nattop-note').innerText()).includes('138 of 138'));
    await page.locator('[data-v="dynasty"]').click();
    if(process.env.SCREENSHOT_DIR&&(width===390||width===1280)){
      await page.screenshot({path:`${process.env.SCREENSHOT_DIR}/2027-${width}.png`});
    }
    await page.locator('#theme').click();
  }
  await page.locator('[data-v="sched"]').click();
  assert.equal(await page.locator('#scheds .gm').count(),36);
  await page.getByRole('tab',{name:'2026',exact:true}).click();
  await page.waitForURL('**season=2026**');
  await page.locator('[data-v="dynasty"]').click();
  assert.deepEqual(await page.locator('#cards .rec').allTextContents(),['9-3','4-8','10-2']);
  await page.getByRole('tab',{name:'2027',exact:true}).click();
  await page.waitForURL('**season=2027**');
  assert.deepEqual(await page.locator('#cards .rec').allTextContents(),['11-1','4-8','11-1']);
  await page.locator('#history-button').click();
  await page.locator('#history-panel table').first().waitFor();
  assert.ok((await page.locator('#history-panel').innerText()).includes('2 published seasons'));
  assert.deepEqual(errors,[]);
  console.log('PASS: 2027 records, 36 regular-season schedule rows, partial player and national-rank labels, four viewport sizes, theme changes, and 2026/2027 switching.');
}finally{await browser.close();}
