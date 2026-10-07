const assert=require('node:assert/strict');const {chromium}=require('playwright');
(async()=>{
 let browser;
 try{
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader']});
 const context=await browser.newContext({viewport:{width:1360,height:960}});const p=await context.newPage(),errors=[];
 p.on('pageerror',e=>errors.push(e.message));const origin=process.env.CORPUS_QA_ORIGIN;
 await p.goto(origin);await p.waitForSelector('.lesson-card');assert.equal(await p.locator('.lesson-card').count(),3);await p.goto(origin+'/#investigar');await p.waitForSelector('.research-passage');assert.equal(await p.locator('#archive-results .research-passage').count(),20);
 assert((await p.locator('#archive-count').textContent()).includes('16,111'));
 await p.screenshot({path:'docs/research-desktop.png'});
 await p.locator('#research-query').fill('maíz');await Promise.all([p.waitForResponse(r=>r.url().includes('/api/research?')),p.getByRole('button',{name:'Buscar en el corpus',exact:true}).click()]);
 assert((await p.locator('#archive-results').textContent()).toLowerCase().includes('maíz'));
 await Promise.all([p.waitForResponse(r=>r.url().includes('/api/research?')),p.locator('#research-variant').selectOption('nci')]);
  await p.setViewportSize({width:390,height:844});await p.screenshot({path:'docs/research-mobile.png'});
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert(!(await p.locator('#research-generate').count()));
 await p.goto(origin+'/aportar');await p.locator('#start-profile').click();
 await p.locator('#profile-form [name=alias]').fill('Prueba de navegador');await p.locator('#variant-select').selectOption('inali-04');await p.locator('[name=participation_consent]').check();await p.locator('#profile-form button[type=submit]').click();
 await p.waitForSelector('#audio-file');assert((await p.locator('.prompt blockquote').textContent()).length>40);
 await p.screenshot({path:'docs/contribute-mobile.png'});assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await p.locator('#answer-form [name=text]').fill('PRUEBA SINTÉTICA DE INTERFAZ');await p.locator('[name=review_consent]').check();await p.locator('[name=rights_confirm]').check();await p.locator('#submit-answer').click();await p.waitForSelector('#next-task');
 await p.goto(origin+'/#extraer/axolotl-00001');await p.waitForSelector('#extract-form [name=nah]');
 assert((await p.locator('#extract-form [name=nah]').inputValue()).length>30);
 await p.locator('#extract-form [name=review_consent]').check();await p.locator('#extract-form [name=authorship]').check();await p.locator('#send-extraction').click();await p.waitForFunction(()=>document.getElementById('extract-message').textContent.includes('Guardada'));
 assert.deepEqual(errors,[]);console.log('PASS: Chromium desktop/mobile, full corpus search, variant filter, no horizontal overflow, real corpus voice/text prompt and sourced correction submission.');
 }finally{await browser?.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
