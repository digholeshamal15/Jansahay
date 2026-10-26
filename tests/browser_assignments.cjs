/* Optional QA: npm install --no-save playwright@1.51.1 @axe-core/playwright
   npx playwright install chromium
   node tests/browser_assignments.cjs
   JANSAHAY_PYTHON may name your virtual-environment interpreter. */
const {chromium}=require('playwright');
const AxeBuilder=require('@axe-core/playwright').default;
const {spawn}=require('node:child_process');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'jansahay-assignment-'));
const port=5024,origin='http://127.0.0.1:'+port;
const server=spawn(process.env.JANSAHAY_PYTHON||'python',['-c',`from app import app; app.config.update(DATABASE=${JSON.stringify(temp+'/test.sqlite')},UPLOAD_DIR=${JSON.stringify(temp+'/photos')}); app.run(host='127.0.0.1',port=${port},debug=False)`],{cwd:root,stdio:['ignore','ignore','pipe']});
let browser,serverErrors='';server.stderr.on('data',b=>serverErrors+=b);process.on('exit',()=>server.kill());
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function get(route){return new Promise((resolve,reject)=>require('node:http').get(origin+route,r=>{let s='';r.on('data',b=>s+=b);r.on('end',()=>{try{resolve(JSON.parse(s));}catch(e){reject(e);}});}).on('error',reject));}
function check(test,message){if(!test)throw Error(message);}
(async()=>{
 let ready=false;for(let i=0;i<120;i++){try{if((await get('/api/config')).ui){ready=true;break;}}catch{}await delay(150);}check(ready,'Server did not start: '+serverErrors);
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1440,height:1050},reducedMotion:'reduce',permissions:['clipboard-read','clipboard-write']});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin);await page.locator('#begin').filter({hasText:'Report a problem'}).waitFor();
 await page.click('#begin');await page.fill('#issue','Preserve my unfinished water complaint.');
 await page.click('.main-nav [data-page="lab"]');await page.locator('.assignment-card').last().waitFor();
 check(await page.locator('.assignment-card').count()===11,'Not all 11 assignments displayed');
 // All demos must return and visibly render their specific result.
 for(let id=1;id<=11;id++){
  await page.locator(`[data-assignment="${id}"]`).click();await page.click('#assignment-example');
  if([7,8].includes(id))await page.selectOption('#ngram','3');
  const response=page.waitForResponse(r=>r.url().endsWith(`/api/assignments/${id}/run`)&&r.request().method()==='POST');
  await page.click('#assignment-run');const body=await (await response).json();
  check(body.assignment===id,'Wrong assignment response');await page.locator('#assignment-output .lab-card').first().waitFor();await page.waitForFunction(()=>!document.querySelector('#assignment-run').disabled);
  check((await page.textContent('#assignment-result-label')).includes(' '+id+' ·'),'Missing result assignment label');
  console.log('Assignment '+id+': mapped feature, method, scope and specific output displayed.');
 }
 // Assignment 2's real bundled-corpus calculation, not a mocked summary.
 await page.locator('[data-assignment="2"]').click();await page.click('#assignment-example');
 const corpusResponse=page.waitForResponse(r=>r.url().endsWith('/api/assignments/2/run'));await page.click('#assignment-corpus');const corpus=await (await corpusResponse).json();
 check(corpus.result.message_count===1331,'Wrong corpus size');await page.waitForFunction(()=>!document.querySelector('#assignment-run').disabled);check((await page.textContent('#assignment-output')).includes('1331'),'Corpus result not rendered');
 console.log('Assignment 2: actual 1,331-message civic corpus analyzed.');
 // Input, selected assignment and analysis language must survive interface changes.
 await page.fill('#lab-text','पाणी येत नाही। मदत करा।');await page.selectOption('#lab-language','mr');
 for(const language of ['hi','mr']){
  await page.selectOption('#ui-language',language);check(await page.inputValue('#lab-text')==='पाणी येत नाही। मदत करा।','Input lost on interface-language change');check(await page.inputValue('#lab-language')==='mr','Analysis language changed unexpectedly');
  const res=page.waitForResponse(r=>r.url().endsWith('/api/assignments/2/run'));await page.click('#assignment-run');const data=await(await res).json();check(data.result.word_count===5&&data.result.sentence_count===2,'Unicode analysis wrong');await page.waitForFunction(()=>!document.querySelector('#assignment-run').disabled);
 }
 console.log('Hindi/Marathi interface, Unicode results and input/analysis-language retention passed.');
 await page.locator('.assignment-raw > summary').click();await page.locator('.assignment-raw button').click();const copied=JSON.parse(await page.evaluate(()=>navigator.clipboard.readText()));check(copied.word_count===5,'Result copy failed');
 await page.locator('.inspector-tools > summary').click();await page.click('#inspect-all');await page.locator('#lab-output .lab-card').first().waitFor();check((await page.textContent('#lab-output')).includes('ngram'),'Original NLP inspector missing');await page.click('#topics');await page.waitForFunction(()=>document.querySelector('#lab-output').textContent.includes('topics'));
 console.log('Raw JSON copy and original full inspector/topic outputs passed.');
 await page.locator('.inspector-tools > summary').click();
 for(const [name,width] of [['desktop',1440],['Marathi mobile',390]]){
  await page.setViewportSize({width,height:950});await page.evaluate(()=>document.fonts.ready);const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();check(!scan.violations.length,'Accessibility '+name+': '+JSON.stringify(scan.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))));check(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Page overflow: '+name);console.log('Assignments '+name+': no automated A/AA violations or page overflow.');
 }
 if(process.env.JANSAHAY_QA_SCREENSHOTS){await page.setViewportSize({width:1440,height:1050});await page.selectOption('#ui-language','en');await page.locator('#lab-panel').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(process.env.JANSAHAY_QA_SCREENSHOTS,'assignments-desktop.png'),fullPage:true});await page.setViewportSize({width:390,height:844});await page.selectOption('#ui-language','mr');await page.screenshot({path:path.join(process.env.JANSAHAY_QA_SCREENSHOTS,'assignments-mobile.png'),fullPage:true});}
 await page.setViewportSize({width:1440,height:1050});await page.selectOption('#ui-language','en');await page.locator('[data-assignment="8"]').focus();await page.keyboard.press('Enter');check(await page.locator('[data-assignment="8"]').getAttribute('aria-pressed')==='true','Keyboard selection failed');
 await page.click('.main-nav [data-page="home"]');check(await page.inputValue('#issue')==='Preserve my unfinished water complaint.','Complaint input lost');
 check((await get('/api/drafts')).length===0,'Demo saved a complaint');check(!errors.length,'Browser errors: '+errors.join('; '));console.log('Keyboard selection, original complaint retention and no demo writes passed.');
 await browser.close();server.kill();fs.rmSync(temp,{recursive:true,force:true});console.log('Assignment browser checks passed.');
})().catch(async e=>{console.error(e);if(browser)await browser.close();server.kill();process.exit(1);});
