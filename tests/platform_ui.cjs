const assert=require('node:assert/strict');
const {JSDOM,CookieJar,VirtualConsole}=require('jsdom');
const origin=process.env.CORPUS_QA_ORIGIN,cookieJar=new CookieJar(),errors=[];
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){for(let i=0;i<120;i++){if(fn())return;await pause(25);}throw Error('UI timeout');}
async function open(path,studyData){
 const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!e.message.includes('HTMLMediaElement'))errors.push(e.message);});
 return JSDOM.fromURL(origin+path,{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,cookieJar,virtualConsole:vc,beforeParse(w){
  if(studyData)w.localStorage.setItem('scriptorium-study-v1',JSON.stringify(studyData));
  w.fetch=async(url,options={})=>{const absolute=new URL(url,origin).href;const headers=new Headers(options.headers);const cookie=cookieJar.getCookieStringSync(absolute);if(cookie)headers.set('Cookie',cookie);if(options.method&&options.method!=='GET')headers.set('Origin',origin);const r=await fetch(absolute,{...options,headers});for(const value of r.headers.getSetCookie())cookieJar.setCookieSync(value,absolute);return r;};
  w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;};
  w.matchMedia=()=>({matches:false});w.Element.prototype.scrollIntoView=function(){};w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 }});
}
(async()=>{
 let dom=await open('/aportar'),w=dom.window,d=w.document;
 await until(()=>d.querySelector('#start-profile'));assert.equal(d.querySelector('.role-nav a').textContent,'Aprender');d.querySelector('#start-profile').click();let p=d.querySelector('#profile-form');assert.equal(p.elements.experience.value,'');
 p.elements.alias.value='Integración sintética';p.elements.variant_id.value='inali-04';p.elements.experience.value='learning';p.elements.participation_consent.checked=true;p.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>d.querySelector('#answer-form'));dom.window.close();
 dom=await open('/',{version:1,saved:[],lessons:{aves:{edition:'lectura-clasica-v1:1',passed:[0],step:0}},reviews:{'sense-tototl':{streak:2,due:1900000000000}}});w=dom.window;d=w.document;const $=s=>d.querySelector(s);
 await until(()=>$('.learn-hero'));assert.equal(d.querySelectorAll('.lesson-card').length,6);assert(!$('#research-generate'));
 w.location.hash='#investigar';await until(()=>$('#archive-results .research-passage'));assert($('#archive-count').textContent.includes('16,111'));
 $('#research-query').value='maíz';$('#research-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>!$('#archive-count').textContent.includes('Buscando'));assert($('#archive-results').textContent.toLowerCase().includes('maíz'));
 w.location.hash='#lexico';await until(()=>$('#dictionary-grid .dictionary-card'));assert.equal($('#dictionary-grid').children.length,24);assert.equal(d.querySelectorAll('#dictionary-grid img').length,24);const featured=(await(await w.fetch('/api/corpus')).json()).dictionary_featured_ids;assert.deepEqual(Array.from(d.querySelectorAll('.word-card-link')).map(a=>a.hash.split('/')[1]),featured);const seen=[...featured];assert($('#dictionary-count').textContent.includes('575'));$('#dictionary-next').click();assert($('#dictionary-range').textContent.includes('25–72'));assert.equal($('#dictionary-grid').children.length,48);let alphabetic=[];do{alphabetic.push(...Array.from(d.querySelectorAll('.word-card-link strong')).map(a=>a.textContent));seen.push(...Array.from(d.querySelectorAll('.word-card-link')).map(a=>a.hash.split('/')[1]));if($('#dictionary-next').disabled)break;$('#dictionary-next').click();}while(true);assert.equal(seen.length,575);assert.equal(new Set(seen).size,575);assert.deepEqual(alphabetic,[...alphabetic].sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'})));$('#dictionary-previous').click();assert(!$('#dictionary-next').disabled);$('#dictionary-origin').value='automatic';$('#dictionary-origin').dispatchEvent(new w.Event('change'));assert($('#dictionary-count').textContent.includes('549'));assert($('#dictionary-grid').textContent.includes('extracción automática'));
 w.location.hash='#lexico/sense-mes';await until(()=>$('.dictionary-entry'));assert($('.dictionary-entry').textContent.includes('metztli'));assert($('.dictionary-entry a[href*="metztli-osu14v"]'));assert($('.dictionary-entry img'));
 w.location.hash='#lexico/sense-atl';await until(()=>$('.dictionary-entry h1').textContent==='atl');const fig=$('.source-image img');assert(fig);assert.equal(fig.getAttribute('loading'),'lazy');assert(fig.getAttribute('alt').includes('atl'));assert($('.image-credit').textContent.includes('Bodleian'));
 w.location.hash='#lexico/sense-madera';await until(()=>$('.dictionary-entry h2').textContent==='madera');assert($('.dictionary-entry').textContent.includes('no equivale a escribir únicamente'));assert($('.source-image a[href*=tlecuauh]'));w.location.hash='#lexico/sense-ihuan';await until(()=>$('.dictionary-entry h1').textContent==='ihuan');assert($('.association-note').textContent.includes('No representa ihuan'));assert($('.association-note').textContent.includes('Sol y a la Luna'));
 w.location.hash='#lexico/sense-tletl';await until(()=>$('.dictionary-entry h1').textContent==='tletl');assert($('.dictionary-entry').textContent.includes('Imagen iconográfica'));
 assert($('link[rel=manifest]'));assert($('.app-install'));
 w.location.hash='#lexico';await until(()=>$('#search'));$('#search').value='arbol';$('#search').dispatchEvent(new w.Event('input'));assert($('#dictionary-grid').textContent.includes('árbol'));assert($('#dictionary-grid').textContent.includes('árbol florido'));
 $('#period').value='modern';$('#period').dispatchEvent(new w.Event('change'));assert($('#dictionary-grid').textContent.includes('No hay coincidencias.'));
 w.location.hash='#lexico/buscar/tototl';await until(()=>$('#dictionary-grid .word-card-link strong')?.textContent==='tototl');assert($('#dictionary-order').textContent.includes('exactas primero'));
 w.location.hash='#lexico/buscar/chachalaca';await until(()=>$('[data-archive-fallback]'));assert.equal($('[data-archive-fallback]').getAttribute('href'),'#investigar/chachalaca');$('[data-archive-fallback]').click();await until(()=>$('#archive-count')?.textContent==='3 resultados');assert($('#archive-results').textContent.includes('parlotea'));
 w.location.hash='#lexico/buscar/'+encodeURIComponent('<script>missing</script>');await until(()=>$('[data-archive-fallback]')?.textContent.includes('<script>'));assert.equal($('#dictionary-grid script'),null);
 w.location.hash='#aprender/flor';await until(()=>$('[data-answer]'));assert($('.reading-translation').hidden);$('[data-annotation="1"]').click();assert($('.word-help').textContent.includes('flor'));assert($('.word-help').textContent.includes('documentos distintos'));
 $('[data-save-word="sense-xochitl"]').click();assert.equal($('[data-save-word="sense-xochitl"]').getAttribute('aria-pressed'),'true');
 $('[data-answer="0"]').click();assert($('.exercise-feedback').textContent.includes('Vuelve'));assert(!$('.exercise-feedback').textContent.includes('CONTEMPLO'));assert.equal(w.savedPassage('sense-xochitl').example.archive_id,$('.reading-card').dataset.archiveId);assert($('#next-example').disabled);
 $('[data-answer="1"]').click();assert(!$('#next-example').disabled);$('#next-example').click();assert($('.guided-passage').textContent.includes('_____'));
 $('[data-annotation="1"]').click();assert($('.word-help').textContent.includes('canto'));assert($('.word-help img').src.includes('xochitl10r'));assert($('.association-note').textContent.includes('No representa Cuicatl'));assert($('.association-note').textContent.includes('In xochitl, in cuicatl'));assert($('.word-help a[href="#lexico/sense-cuicatl"]'));
 $('[data-answer="2"]').click();$('#next-example').click();$('[data-annotation="0"]').click();assert($('.word-help a[href="#lexico/sense-cacahuaxochitl"]'));assert($('.word-help img').src.includes('CacahuaxochitlMH885v'));assert($('.association-note').textContent.includes('nombre personal'));assert($('.word-help').textContent.includes('identificación botánica'));
 $('[data-answer="0"]').click();$('#next-example').click();assert($('.guided-passage').textContent.includes('_____'));$('[data-answer="0"]').click();assert($('#next-example').disabled);$('[data-answer="2"]').click();$('#next-example').click();assert($('.completion-card'));
 assert.equal(w.lessonProgress({id:'cielo',version:2,practice_version:1,examples:[1,2,3,4]}).edition,'lectura-clasica-v1:1');
 const saved=JSON.parse(w.localStorage.getItem('scriptorium-study-v1'));assert(saved.saved.includes('sense-xochitl'));assert.equal(saved.lessons.flor.passed.length,4);assert.equal(saved.lessons.flor.edition,'lectura-clasica-v1:2');
 w.location.hash='#aprender/lugares';await until(()=>$('.guided-passage'));$('[data-step="1"]').click();$('[data-annotation="0"]').click();assert($('.word-help h3').textContent==='tlacuilolcalli');assert($('.word-help').textContent.includes('Comparación temática'));assert($('.lookup-reference').textContent.includes('calli'));assert($('.word-help').textContent.includes('no escribe el compuesto completo'));
 for(const lid of ['agua-tierra','flores-cantos','aves']){
  w.location.hash='#aprender/'+lid;
  const lessons=(await(await w.fetch('/api/learning')).json()).lessons,l=lessons.find(l=>l.id===lid);
  await until(()=>$('#content h1')?.textContent===l.title&&d.querySelectorAll('[data-step]').length===4);
  if(lid==='aves'){
   assert.equal($('#next-example').disabled,true);assert($('[data-answer="0"]').disabled);
   assert($('.hint').textContent||$('.exercise-feedback').textContent);
   $('[data-explore-word="chachalaca"]').click();await until(()=>$('#archive-count')?.textContent==='3 resultados');
   w.location.hash='#aprender/aves';await until(()=>$('#content h1')?.textContent===l.title);
   assert($('[data-answer="0"]').disabled);assert($('#next-example').disabled);
  }
  for(const [i,e] of l.examples.entries()){
   assert($('.lesson-progress').textContent.includes('Ejemplo '+(i+1)+' de 4'));
   assert.equal($('.reading-translation').textContent,e.passage.es);
   $('[data-answer="'+e.exercise.answer+'"]').click();
   if(e.comprehension){
    assert($('#next-example').disabled);
    const bad=(e.comprehension.answer+1)%e.comprehension.options.length;
    $('[data-comprehension="'+bad+'"]').click();assert($('#next-example').disabled);
    assert(!$('.comprehension-feedback').textContent.includes(e.comprehension.options[e.comprehension.answer]));
    $('[data-comprehension="'+e.comprehension.answer+'"]').click();assert(!$('#next-example').disabled);
   }
   $('#next-example').click();
  }
  assert($('.completion-card'));
 }
 const shortLesson=(await(await w.fetch('/api/learning')).json()).lessons.find(l=>l.id==='agua-tierra');w.renderLesson({...shortLesson,id:'synthetic-short',examples:shortLesson.examples.slice(0,2)});assert.equal(d.querySelectorAll('[data-step]').length,2);for(const e of shortLesson.examples.slice(0,2)){$('[data-answer="'+e.exercise.answer+'"]').click();$('#next-example').click();}assert($('.completion-card'));assert($('#content').textContent.includes('los 2 fragmentos'));
 w.location.hash='#leer';await until(()=>$('#reader-examples'));assert.equal(d.querySelectorAll('.reading-card').length,24);assert($('.reading-translation').textContent.includes('CONTEMPLO'));
 w.location.hash='#palabras';await until(()=>$('#start-review'));assert.equal($('.saved-grid').children.length,1);$('#start-review').click();assert($('#review-answer').hidden);assert($('.saved-context blockquote').textContent.toLowerCase().includes('xochitl'));assert($('.saved-context a').getAttribute('href').startsWith('#leer/'));$('#show-word').click();assert(!$('#review-answer').hidden);assert($('.review-translation').textContent.length>0);$('#known-word').click();assert($('#finish-review'));$('#finish-review').click();assert($('#start-review').disabled);
 const migrated=JSON.parse(w.localStorage.getItem('scriptorium-study-v1'));assert.equal(migrated.lessons.aves.edition,'lectura-clasica-v1:1');assert.equal(migrated.lessons.aves.passed.length,4);assert.equal(migrated.lessons.aves.comprehension.length,4);assert.equal(migrated.reviews['sense-tototl'].streak,2);
 console.log('PASS: guided reading, contextual glyph help, incorrect-answer feedback, exact-form exercise, completion, saved words and review');
 w.location.hash='#aprender/aves';await until(()=>$('[data-step="0"]'));$('[data-step="0"]').click();$('[data-annotation="0"]').click();$('[data-save-word="sense-tototl"]').click();
 assert.equal(w.savedPassage('sense-tototl').example.archive_id,'axolotl-14546');
 $('[data-step="1"]').click();$('[data-annotation="0"]').click();$('[data-save-context="sense-tototl"]').click();
 assert.equal(w.savedPassage('sense-tototl').example.archive_id,'axolotl-14253');assert.equal(JSON.parse(w.localStorage.getItem('scriptorium-study-v1')).reviews['sense-tototl'].streak,2);
 $('[data-save-word="sense-tototl"]').click();assert.equal(w.savedPassage('sense-tototl'),undefined);
 console.log('PASS: dictionary-to-archive continuation, exact-first lookup, saved passage context, source-backed comprehension and legacy progress preserved');
 console.log('PASS: accent-insensitive search, separate senses, contextual references and explicit absent variant');
 w.location.hash='#extraer/sense-atl';await until(()=>$('#extract-form'));
 assert($('.profile-note').textContent.includes('Integración sintética'));const f=$('#extract-form');
 f.elements.label.value='QA <script>no ejecutar</script>';f.elements.written.value='FORMA_QA';f.elements.locator.value='sesión sintética';f.elements.review_consent.checked=true;f.elements.authorship.checked=true;f.elements.public_consent.checked=true;
 f.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#extract-message').textContent.includes('Guardada'));await until(()=>$('.withdraw-proposal'));
 assert.equal($('#my-proposals script'),null);assert($('#my-proposals').textContent.includes('<script>no ejecutar</script>'));
 const proposals=await(await w.fetch('/api/proposals')).json();assert.equal(proposals.length,1);assert.equal(proposals[0].payload.consent.training,false);
 console.log('PASS: one Voces session submits a sourced lexical proposal with independent permissions');
 const corpus=await(await w.fetch('/api/corpus')).json();assert(!corpus.records.some(r=>r.id===proposals[0].id));
 $('.withdraw-proposal').click();$('.confirm').click();await until(()=>$('#my-proposals').textContent.includes('Retirada'));
 console.log('PASS: pending contribution remains outside corpus and can be withdrawn');
 w.location.hash='#modelos/progreso';await until(()=>$('#lab-progress'));assert($('#lab-progress').textContent.includes('22.58'));assert($('#lab-progress').textContent.includes('27.96'));assert($('#lab-progress').textContent.includes('Los hashes actuales no coinciden'));assert($('.lab-curve svg'));assert($('#lab-how').textContent.includes('no reconoce imágenes'));$('[data-lab-target="lab-progress"]').click();assert.equal(w.location.hash,'#modelos/progreso');
 w.location.hash='#modelos/probar';await until(()=>$('#compose'));assert.equal($('#experiment-mode').value,'corpus');$('#compose-text').value='flor';$('#experiment-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#compose-result h2'));assert($('#compose-result').textContent.includes('sin LLM'));$('#experiment-mode').value='rules';$('#experiment-mode').dispatchEvent(new w.Event('change'));$('#compose-text').value='Veo una flor.';$('#experiment-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#review-export'));assert($('#compose-result').textContent.includes('Niquitta xochitl.'));assert($('#compose-result').textContent.includes('Regla local · sin LLM'));
 w.location.hash='#modelos/datos';await until(()=>$('#training-rows .training-pair'));assert($('#training-count').textContent.includes('650'));assert.equal($('#training-rows').children.length,20);$('#training-next').click();await until(()=>$('#training-range').textContent.includes('21–40'));$('#training-dataset').value='train';$('#training-dataset').dispatchEvent(new w.Event('change'));await until(()=>$('#training-count').textContent.includes('2,161'));
 const pf=$('#training-pair-form');pf.elements.es.value='TEXTO SINTÉTICO UI';pf.elements.nah.value='FORMA SINTÉTICA DE PRUEBA';pf.elements.document.value='Colección de QA UI';pf.elements.locator.value='Registro sintético';pf.elements.source_url.value='https://example.org';pf.elements.license.value='CC-BY-4.0';for(const k of ['authorship','review_consent','training_consent'])pf.elements[k].checked=true;pf.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#pair-message').textContent.includes('Guardado'));await until(()=>$('.withdraw-pair'));assert($('#pair-proposals').textContent.includes('Pendiente de revisión'));
 const exp=await(await w.fetch('/api/training-pairs/export')).text();assert.equal(exp.trim().split('\n').length,1);$('.withdraw-pair').click();await until(()=>$('#pair-proposals').textContent.includes('Retirado'));
 const csvResult=w.pairCSV('es,nah,document,locator,source_url,license,reviewer,iso\n"texto, con coma","forma\nsegunda línea",Obra,Folio,https://example.org,CC-BY-4.0,,nci\n');assert.equal(csvResult[0].es,'texto, con coma');assert.equal(csvResult[0].nah,'forma\nsegunda línea');
 console.log('PASS: laboratory tabs, separate corpus/rules, training pairs, pagination, CSV and private proposals');
 w.location.hash='#fuentes';await until(()=>$('#source-results'));assert($('#source-results').textContent.includes('UNAM'));assert.equal($('#source-results').children.length,20);
 w.location.hash='#textos';await until(()=>$('#text-results'));assert.equal($('#text-results').children.length,3);
 assert.deepEqual(errors,[]);console.log('PASS: sources and texts render with no application JavaScript errors');dom.window.close();
})().catch(e=>{console.error(e);process.exit(1);});
