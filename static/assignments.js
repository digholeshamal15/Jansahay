'use strict';
// Assignment views call the existing algorithms. No complaint is saved by a demo.
const assignmentUI={
 catalog:[], selected:1, initialized:false, result:null, resultLabel:'', sequence:0, busy:false,
 localize(){
  const grid=$('assignment-grid');grid.replaceChildren();
  this.catalog.forEach(a=>{const b=button('', 'assignment-card'+(a.id===this.selected?' selected':''),()=>this.select(a.id,true));b.dataset.assignment=a.id;b.setAttribute('aria-pressed',String(a.id===this.selected));b.append(node('span',tr('assignment_number')+' '+String(a.id).padStart(2,'0'),'assignment-card-number'),node('strong',a.title[lang]),node('span',a.feature[lang],'assignment-card-feature'));grid.append(b);});
  this.renderSelection();
  if(!this.initialized){this.example();this.initialized=true;}
  this.renderResult();
 },
 select(id,focus=false){this.selected=id;this.result=null;this.resultLabel='';this.sequence++;this.busy=false;this.localize();$('assignment-error').classList.add('hidden');if(focus){$('assignment-demo').scrollIntoView({behavior:'smooth',block:'start'});$('assignment-heading').focus({preventScroll:true});}},
 renderSelection(){
  const a=this.catalog.find(a=>a.id===this.selected);if(!a)return;
  $('assignment-badge').textContent=tr('assignment_number')+' '+a.id+' / 11';$('assignment-heading').textContent=a.title[lang];$('assignment-purpose').textContent=a.purpose[lang];$('assignment-feature').textContent=a.feature[lang];$('assignment-method').textContent=a.method;$('assignment-limits').textContent=a.limitation[lang];$('assignment-files').replaceChildren(...a.files.map(f=>node('li',f)));
  const html=this.selected===1;$('assignment-text-fields').classList.toggle('hidden',html);$('lab-text').required=!html;$('lab-html').required=html;$('assignment-html-fields').classList.toggle('hidden',!html);$('assignment-cli').classList.toggle('hidden',!html);$('assignment-ngram-field').classList.toggle('hidden',![7,8].includes(this.selected));$('assignment-location-field').classList.toggle('hidden',this.selected!==11);$('assignment-project-links').classList.toggle('hidden',this.selected!==11);$('assignment-corpus').classList.toggle('hidden',this.selected!==2);
  $('assignment-command').textContent='python scripts/scrape.py "https://YOUR-PERMITTED-PAGE" --lang '+$('lab-language').value;
  $('assignment-run').disabled=this.busy;$('assignment-corpus').disabled=this.busy;$('assignment-run').textContent=tr(this.busy?'assignment_running':'assignment_run');
 },
 example(){
  if(this.selected===1){$('lab-html').value='<html><head><title>Sample civic guidance</title></head><body><nav>Menu to ignore</nav><main><h1>Water supply help</h1><p>Describe the supply issue and provide its location.</p><script>/* excluded from extracted text */</script></main></body></html>';return;}
  if([3,4].includes(this.selected)){$('lab-language').value='en';$('lab-text').value='Residents reported broken pipes. Workers are repairing the roads in Pune.';}
  else if(this.selected===5){$('lab-text').value=({en:'The water supply in Pune 411001 stopped on 22/10/2026.',hi:'पुणे 411001 में 22/10/2026 से पानी नहीं आ रहा है।',mr:'पुणे 411001 येथे 22/10/2026 पासून पाणी येत नाही.'})[$('lab-language').value];}
  else if(this.selected===10){$('lab-text').value=({en:'The water is dirty again. We are angry and frustrated.',hi:'पानी गंदा है। बार बार परेशानी हो रही है।',mr:'पाणी घाण आहे. पुन्हा त्रास होत आहे.'})[$('lab-language').value];}
  else $('lab-text').value=config.samples[$('lab-language').value].water;
 },
 async run(corpus=false){
  if(this.busy)return;const html=this.selected===1;
  if(!(html?$('lab-html').value:$('lab-text').value).trim()){$('assignment-error').textContent=html?tr('assignment_html_note'):tr('empty_issue');$('assignment-error').classList.remove('hidden');return;}
  const id=this.selected,seq=++this.sequence,analysisLanguage=$('lab-language').value;this.busy=true;this.renderSelection();$('assignment-error').classList.add('hidden');
  const input={text:$('lab-text').value,html:$('lab-html').value,lang:analysisLanguage,n:Number($('ngram').value),location:$('lab-location').value,corpus};
  try{const data=await post('/api/assignments/'+id+'/run',input);if(seq!==this.sequence)return;this.result=data.result;this.resultLabel={id,analysisLanguage,corpus};this.renderResult();}
  catch(e){if(seq===this.sequence){$('assignment-error').textContent=tr('error_generic');$('assignment-error').classList.remove('hidden');}}
  finally{if(seq===this.sequence){this.busy=false;this.renderSelection();}}
 },
 renderResult(){
  $('assignment-result-label').textContent=this.resultLabel?tr('assignment_number')+' '+this.resultLabel.id+' · '+config.names[this.resultLabel.analysisLanguage]+(this.resultLabel.corpus?' · data/service_train.json':''):'';$('assignment-output').replaceChildren();if(this.result===null){$('assignment-output').append(node('p',tr('assignment_wait'),'assignment-empty'));return;}
  const values=node('div',undefined,'assignment-results');Object.entries(this.result).forEach(([key,value])=>values.append(this.value(key,value)));$('assignment-output').append(values);
  const raw=node('details',undefined,'assignment-raw');raw.append(node('summary',tr('assignment_raw')),button(tr('assignment_copy'),'text-button',()=>copyText(JSON.stringify(this.result,null,2))),node('pre',JSON.stringify(this.result,null,2)));$('assignment-output').append(raw);
 },
 label(key){
  const names={language:'Language hint',word_count:'Word count',sentence_count:'Sentence count',tokens:'Tokens',english:'English word normalization',stems:'Porter stems',lemmas:'WordNet lemmas',pos:'POS tags',word_embedding:'Dense word embedding',pos_embedding_classifier:'English POS + embedding classification',service_classifier:'Public service classification',items:'Recognized entities',status:'Resource / method status',resource_note:'Resource requirement',tfidf_top_character_features:'TF-IDF features',top_features:'TF-IDF features',input_ngrams:'Your input N-grams',ngram_counts:'Learned N-gram counts',terms:'Conditional probability steps',probability_factors:'Probability product (rounded factors)',related_guidance:'LSA / LSI related guidance',tone_counts:'Tone counts',topics:'LDA topics',draft:'Prepared complaint (not saved)',mode:'Demonstration mode',network_request_made:'Website contacted',training_messages:'Training messages',negative_cues:'Negative cues',positive_cues:'Positive cues',emotions:'Emotion cues',classification:'Guarded service classification',language_hint:'Language hint',examples:'Corpus examples'};
  return names[key]||key.replaceAll('_',' ').replace(/^./,s=>s.toUpperCase());
 },
 compact(v){if(v===null||v===undefined)return '—';if(Array.isArray(v))return v.length?v.map(x=>typeof x==='object'?JSON.stringify(x):String(x)).join(' · '):'—';if(typeof v==='object')return Object.entries(v).map(([k,x])=>this.label(k)+': '+this.compact(x)).join('; ');if(typeof v==='boolean')return tr(v?'yes':'no');return String(v);},
 value(key,value,depth=0){
  const card=node('section',undefined,depth?'assignment-nested':'lab-card assignment-value');card.append(node(depth?'h4':'h3',this.label(key)));
  if(value===null||value===undefined||(Array.isArray(value)&&value.length===0)){card.append(node('p',tr('assignment_no_results'),'field-hint'));return card;}
  if(Array.isArray(value)){
   if(value.every(x=>x&&typeof x==='object'&&!Array.isArray(x))){
    const columns=[...new Set(value.flatMap(x=>Object.keys(x)))];const wrap=node('div',undefined,'assignment-table-wrap');wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',this.label(key));const table=node('table');const cap=node('caption',this.label(key),'sr-only');table.append(cap);const head=node('thead'),trh=node('tr');columns.forEach(k=>{const th=node('th',this.label(k));th.scope='col';trh.append(th);});head.append(trh);const body=node('tbody');value.forEach(row=>{const line=node('tr');columns.forEach(k=>line.append(node('td',this.compact(row[k]))));body.append(line);});table.append(head,body);wrap.append(table);card.append(wrap);
   }else{const list=node('div',undefined,'assignment-tokens');value.forEach(v=>list.append(node('span',this.compact(v),'assignment-token')));card.append(list);}
  }else if(typeof value==='object'){
   const dl=node('dl',undefined,'assignment-metrics');Object.entries(value).forEach(([k,v])=>{if(v!==null&&typeof v==='object')card.append(this.value(k,v,depth+1));else{const pair=node('div');pair.append(node('dt',this.label(k)),node('dd',this.compact(v)));dl.append(pair);}});card.insertBefore(dl,card.children[1]||null);
  }else card.append(node('p',this.compact(value),['draft','extracted_text'].includes(key)?'assignment-text':'assignment-scalar'));
  return card;
 },
 bind(){
  $('lab-form').onsubmit=e=>{e.preventDefault();this.run();};$('assignment-example').onclick=()=>{this.example();this.renderSelection();};$('assignment-corpus').onclick=()=>this.run(true);$('lab-language').onchange=()=>this.renderSelection();
  $('inspect-all').onclick=async()=>{const b=$('inspect-all');b.disabled=true;try{renderLab(await post('/api/lab',{text:$('lab-text').value,lang:$('lab-language').value,n:Number($('ngram').value)}));}catch{toast(tr('empty_issue'));}finally{b.disabled=false;}};
 }
};
