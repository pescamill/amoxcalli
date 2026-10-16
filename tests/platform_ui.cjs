const assert=require('node:assert/strict');
const {JSDOM,CookieJar,VirtualConsole}=require('jsdom');
const origin=process.env.CORPUS_QA_ORIGIN,cookieJar=new CookieJar(),errors=[];
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){for(let i=0;i<240;i++){if(fn())return;await pause(25);}throw Error('UI timeout');}
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
 dom=await open('/',{version:1,saved:[],lessons:{aves:{edition:'lectura-clasica-v1:2',passed:[0],step:0}},reviews:{'sense-tototl':{streak:2,due:1900000000000}}});w=dom.window;d=w.document;const $=s=>d.querySelector(s);
 await until(()=>$('.learn-hero'));assert.equal(d.querySelectorAll('.lesson-card').length,12);assert(!$('#research-generate'));

 const studyBeforeDocumentary=w.localStorage.getItem('scriptorium-study-v1');
 w.location.hash='#consultar/agua';await until(()=>$('#documentary-results .documentary-hit'));assert.equal(d.title,'Amoxcalli · Consultar fichas');assert($('#documentary-query').labels.length);assert($('#documentary-status').getAttribute('role')==='status');assert($('#documentary-results').textContent.includes('atl'));assert($('#documentary-results').textContent.includes('Escritura original'));assert($('#documentary-results a[href^="https://"]'));assert($('#documentary-results a[href="#lexico/sense-atl"]'));
 const publicFieldHit={id:'synthetic-public-form',kind:'form',label:'Sintético',match:['identifier'],source_ids:[],urls:[],fields:[{field:'definition',value:'Public edit',table:'public_records',record_id:'synthetic-public',url:'https://example.org/'}]};const projected=w.documentaryHit(publicFieldHit);assert(projected.includes('no transcripción de la fuente'));assert(projected.includes('Fuente relacionada'));
 assert.equal($('#documentary-results img'),null);const documentaryPre=$('#documentary-results pre');assert.equal(documentaryPre.getAttribute('style'),null);assert.equal(w.getComputedStyle(documentaryPre).whiteSpace,'pre-wrap');assert.equal(w.getComputedStyle(documentaryPre).overflowWrap,'anywhere');
 $('#documentary-query').value='ic';$('#documentary-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#documentary-status').textContent.includes('fichas mostradas')&&$('#documentary-results').textContent.includes('sense-gdn'));assert(d.querySelectorAll('.documentary-hit').length>=2);assert($('#documentary-results').textContent.includes('Normalización catalogada'));
 $('#documentary-query').value='axolotl-14546';$('#documentary-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#documentary-results').textContent.includes('Original náhuatl'));assert($('#documentary-results').textContent.includes('Español conservado'));assert($('#documentary-results').textContent.includes('Variedad declarada'));
 $('#documentary-query').value='<script>zzzz-no-evidence-7821</script>';$('#documentary-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#documentary-status').textContent.includes('No hay coincidencias'));assert.equal($('#documentary-results script'),null);assert.equal(w.localStorage.getItem('scriptorium-study-v1'),studyBeforeDocumentary);
 console.log('PASS: documentary lookup, distinct senses, original/normalization, cited passages, accessible form, abstention, escaping and study privacy');
 const studyBeforeProject=w.localStorage.getItem('scriptorium-study-v1');
 w.location.hash='#proyecto';await until(()=>$('#project-status'));assert.equal(d.title,'Amoxcalli · Proyecto');assert($('#project-status').textContent.includes('575'));assert($('#project-status').textContent.includes('436'));assert($('#content').textContent.includes('No se declara aval'));assert($('a[href="/project/pilot.md"]'));
 w.location.hash='#taller/aves';await until(()=>$('#workshop-preview .workshop-sheet'));assert.equal(d.title,'Amoxcalli · Ficha para taller');assert(d.body.classList.contains('workshop-view'));assert.equal(d.querySelectorAll('.workshop-passage').length,4);assert.equal($('.workshop-answer-key'),null);assert.equal(d.querySelectorAll('.workshop-translation').length,4);assert($('.workshop-provenance').textContent.includes('axolotl-14546'));assert($('.source-hash').textContent.includes('SHA-256'));
 const publicLearning=await(await w.fetch('/api/learning')).json(),publicBirds=publicLearning.lessons.find(l=>l.id==='aves');
 const packet=w.workshopBundle(publicBirds);assert.deepEqual(JSON.parse(JSON.stringify(packet.lesson)),publicBirds);assert.equal(packet.editorial_status,'pending_linguistic_review');assert.equal(packet.variant,'nci');assert(!Object.hasOwn(packet,'profile'));assert(!Object.hasOwn(packet,'study'));packet.lesson.examples[0].passage.nah='changed in detached export';assert.notEqual(packet.lesson.examples[0].passage.nah,publicBirds.examples[0].passage.nah);
 $('#workshop-key').checked=true;$('#workshop-key').dispatchEvent(new w.Event('change'));assert($('.workshop-answer-key').textContent.includes(publicBirds.examples[0].comprehension.options[publicBirds.examples[0].comprehension.answer]));
 $('#workshop-translations').checked=false;$('#workshop-translations').dispatchEvent(new w.Event('change'));assert.equal($('.workshop-translation'),null);assert.equal(d.querySelectorAll('.workshop-passage').length,4);
 let printed=0;w.print=()=>printed++;$('#print-workshop').click();assert.equal(printed,1);
 let exported;const originalDownload=w.download;w.download=(name,value)=>{exported={name,value};};$('#download-workshop').click();w.download=originalDownload;assert.equal(exported.name,'amoxcalli-lectura-aves-v3.json');// versión de contenido: claves de lectura y práctica v2assert.equal(exported.value.lesson.examples.length,4);assert(exported.value.lesson.examples[0].passage.rights_note);assert.equal(w.localStorage.getItem('scriptorium-study-v1'),studyBeforeProject);
 $('#workshop-lesson').value='flor';$('#workshop-lesson').dispatchEvent(new w.Event('change'));assert.equal(w.location.hash,'#taller/flor');assert($('.workshop-sheet h2').textContent.includes('flor'));
 w.location.hash='#taller/not-a-lesson';await until(()=>$('#content').textContent.includes('Lectura no disponible'));assert.equal($('.workshop-sheet'),null);
 w.location.hash='#leer/aves';await until(()=>$('#reader-workshop'));assert(!d.body.classList.contains('workshop-view'));assert.equal($('#reader-workshop').getAttribute('href'),'#taller/aves');assert($('.reading-source a[href="#extraer/axolotl-14546"]'));
 {
  const studyBeforeComparison=w.localStorage.getItem('scriptorium-study-v1'),writes=[],requests=[];
  const originalSet=w.Storage.prototype.setItem,originalFetch=w.fetch;let controlled;
  w.Storage.prototype.setItem=function(k,v){writes.push(k);return originalSet.call(this,k,v);};
  w.fetch=async(url,options={})=>{
   if(String(url).startsWith('/api/research?')){requests.push(new URL(url,origin));if(controlled)return controlled(url,options);}
   return originalFetch(url,options);
  };
  const firstCard=()=>$('.reading-card'),input=()=>firstCard().querySelector('.explore-word-form input');
  const edit=query=>{input().value=query;input().dispatchEvent(new w.Event('input',{bubbles:true}));};
  const compare=()=>firstCard().querySelector('[data-reading-compare]').click();
  const status=()=>firstCard().querySelector('.reading-comparison-status');
  const previews=()=>[...firstCard().querySelectorAll('.reading-comparison-passage')];
  assert(w.readingWordMatches('In MICHI, cuiatl.','michi'));
  assert(!w.readingWordMatches('totolimpanecas','tototl'));
  assert(!w.readingWordMatches('ichachalaca chachalaca-tlatohua chachálaca','chachalaca'));
  assert(w.readingWordMatches('co\u0301huatl','cóhuatl'));
  assert(!w.readingWordMatches('cohuatl','cóhuatl'));
  assert(firstCard().querySelector('[data-comparison-archive]').hidden);edit('dos palabras');compare();assert.equal(requests.length,0);assert(status().textContent.includes('una sola palabra'));
  firstCard().querySelector('[data-compare-word="chachalaca"]').click();
  assert(status().textContent.startsWith('Buscando'));assert.equal(status().getAttribute('aria-live'),'polite');
  await until(()=>previews().length===2);assert.equal(w.location.hash,'#leer/aves');
  assert.deepEqual(previews().map(p=>p.dataset.previewId),['axolotl-10403','axolotl-14479']);// orden de la búsqueda de términos: grafía consultada, luego orden del archivo
  const response=await(await originalFetch('/api/research?query=chachalaca&variant=nci&period=historical&offset=0&limit=10')).json();
  for(const card of previews()){
   const row=response.results.find(r=>r.id===card.dataset.previewId);assert(row);
   assert.equal(card.querySelector('blockquote').textContent,row.nah);
   assert.equal(card.querySelector('.preview-translation').textContent,row.es);
   assert(card.querySelector('.preview-translation').hidden);
   assert(card.textContent.includes(row.locator));assert(card.textContent.includes(row.document));
   assert.equal(card.querySelector('a[href^="https://"]').getAttribute('href'),row.source_url);
  }
  const translation=previews()[0].querySelector('[data-preview-translation]');translation.click();
  assert(!previews()[0].querySelector('.preview-translation').hidden);assert.equal(translation.getAttribute('aria-expanded'),'true');
  translation.click();assert(previews()[0].querySelector('.preview-translation').hidden);
  assert.equal(firstCard().querySelector('.reading-translation').hidden,false);
  const publicRow=response.results.find(r=>r.id==='axolotl-14479');
  const row=(id,nah,extra={})=>({...publicRow,id,nah,...extra});
  const reply=results=>new Response(JSON.stringify({total:999,results}),{status:200,headers:{'Content-Type':'application/json'}});
  controlled=async()=>reply([
   row('axolotl-14546','chachalaca'),row('wrong-variety','chachalaca',{iso:'azz'}),
   row('compound','ichachalaca chachalaca-tlatohua'),row('accent','chachálaca'),
   row('synthetic-exact-1','CHACHALACA <script>escaped</script>',{es:'<b>translation original</b>',source_url:'javascript:alert(1)'}),
   row('synthetic-exact-1','chachalaca duplicate'),row('synthetic-exact-2','in chachalaca.'),row('synthetic-exact-3','chachalaca')]);
  compare();await until(()=>previews()[0]?.dataset.previewId==='synthetic-exact-1');
  assert.equal(previews().length,2);assert.equal(firstCard().querySelector('script'),null);
  assert.equal(previews()[0].querySelector('a'),null);assert(previews()[0].textContent.includes('<script>escaped</script>'));
  assert(previews()[0].querySelector('.preview-translation').textContent.includes('<b>translation original</b>'));
  assert(!status().textContent.includes('999'));
  controlled=async()=>reply([row('compound','ichachalaca')]);compare();await until(()=>status().textContent.startsWith('No aparecen'));
  assert.equal(previews().length,0);assert(firstCard().querySelector('[data-comparison-archive]').hash.includes('passage=axolotl-14546'));
  controlled=async()=>new Response(JSON.stringify({error:'<script>error</script>'}),{status:503});
  compare();await until(()=>status().textContent.startsWith('No se pudo cargar'));assert.equal(previews().length,0);
  let release;controlled=()=>new Promise(resolve=>{release=()=>resolve(reply([row('late-old','chachalaca OLD_LATE')]));});
  compare();assert(status().textContent.startsWith('Buscando'));const releaseOld=release;
  edit('michi');controlled=async()=>reply([row('latest','MICHI latest')]);compare();await until(()=>previews()[0]?.dataset.previewId==='latest');
  releaseOld();await pause(30);assert.equal(previews()[0].dataset.previewId,'latest');assert(!firstCard().textContent.includes('OLD_LATE'));
  controlled=()=>new Promise(resolve=>{release=()=>resolve(reply([row('stale-input','michi')]));});compare();
  edit('cuiatl');release();await pause(30);assert.equal(previews().length,0);assert.equal(status().textContent,'');
  compare();const detached=firstCard(),releaseRoute=release;w.location.hash='#aprender/aves';await until(()=>$('.lesson-progress')&&$('[data-answer]'));
  releaseRoute();await pause(30);assert(!detached.isConnected);assert.equal(previews().length,0);
  controlled=undefined;firstCard().querySelector('[data-compare-word="chachalaca"]').click();await until(()=>previews().length===2);
  assert(firstCard().querySelector('[data-comparison-archive]').hash.includes('from=aprender&lesson=aves&passage=axolotl-14546'));
  const comparisonRequestCount=requests.length;firstCard().querySelector('[data-comparison-archive]').click();await until(()=>$('[data-reading-return]')&&$('#archive-results'));
  $('[data-reading-return]').click();await until(()=>d.activeElement?.dataset.archiveId==='axolotl-14546');
  assert.equal($('[data-step="0"]').getAttribute('aria-current'),'step');
  for(const url of requests.slice(0,comparisonRequestCount)){assert.equal(url.searchParams.get('variant'),'nci');assert.equal(url.searchParams.get('period'),'historical');assert.equal(url.searchParams.get('limit'),'10');assert.equal(url.searchParams.get('offset'),'0');}
  assert.equal(w.localStorage.getItem('scriptorium-study-v1'),studyBeforeComparison);assert.deepEqual(writes,[]);
  w.fetch=originalFetch;w.Storage.prototype.setItem=originalSet;
  w.location.hash='#leer/aves';await until(()=>$('#reader-workshop'));
  console.log('PASS: comparación inline exacta/acento/NFC, dos fuentes públicas y traducción ocultable, variante, errores/vacíos, carreras/input/ruta, retorno y cero escrituras');
 }
 console.log('PASS: project purpose, live inventory, public workshop packet, optional print keys/translations, provenance, missing lesson and personal storage preserved');
 w.location.hash='#investigar';await until(()=>$('#archive-results .research-passage'));assert($('#archive-count').textContent.includes('16,111'));
 $('#research-query').value='maíz';$('#research-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>!$('#archive-count').textContent.includes('Buscando'));assert($('#archive-results').textContent.toLowerCase().includes('maíz'));
 w.location.hash='#lexico';await until(()=>$('#dictionary-grid .dictionary-card'));assert.equal($('#dictionary-grid').children.length,24);assert.equal(d.querySelectorAll('#dictionary-grid img').length,24);const featured=(await(await w.fetch('/api/corpus')).json()).dictionary_featured_ids;assert.deepEqual(Array.from(d.querySelectorAll('.word-card-link')).map(a=>a.hash.split('/')[1]),featured);const seen=[...featured];assert($('#dictionary-count').textContent.includes('575'));$('#dictionary-next').click();assert($('#dictionary-range').textContent.includes('25–72'));assert.equal($('#dictionary-grid').children.length,48);let alphabetic=[];do{alphabetic.push(...Array.from(d.querySelectorAll('.word-card-link strong')).map(a=>a.textContent));seen.push(...Array.from(d.querySelectorAll('.word-card-link')).map(a=>a.hash.split('/')[1]));if($('#dictionary-next').disabled)break;$('#dictionary-next').click();}while(true);assert.equal(seen.length,575);assert.equal(new Set(seen).size,575);assert.deepEqual(alphabetic,[...alphabetic].sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'})));$('#dictionary-previous').click();assert(!$('#dictionary-next').disabled);$('#dictionary-origin').value='automatic';$('#dictionary-origin').dispatchEvent(new w.Event('change'));assert($('#dictionary-count').textContent.includes('549'));assert($('#dictionary-grid').textContent.includes('extracción automática'));
 w.location.hash='#lexico/sense-mes';await until(()=>$('.dictionary-entry'));assert($('.dictionary-entry').textContent.includes('metztli'));assert($('.dictionary-entry a[href*="metztli-osu14v"]'));assert($('.dictionary-entry img'));
 w.location.hash='#lexico/sense-atl';await until(()=>$('.dictionary-entry h1').textContent==='atl');const fig=$('.source-image img');assert(fig);assert.equal(fig.getAttribute('loading'),'lazy');assert(fig.getAttribute('alt').includes('atl'));assert($('.image-credit').textContent.includes('Bodleian'));
 w.location.hash='#lexico/sense-madera';await until(()=>$('.dictionary-entry h2').textContent==='madera');assert($('.dictionary-entry').textContent.includes('no equivale a escribir únicamente'));assert($('.source-image a[href*=tlecuauh]'));w.location.hash='#lexico/sense-ihuan';await until(()=>$('.dictionary-entry h1').textContent==='ihuan');assert($('.association-note').textContent.includes('No representa ihuan'));assert($('.association-note').textContent.includes('Sol y a la Luna'));
 w.location.hash='#lexico/sense-tletl';await until(()=>$('.dictionary-entry h1').textContent==='tletl');assert($('.dictionary-entry').textContent.includes('Imagen iconográfica'));
 assert($('link[rel=manifest]'));assert($('.app-install'));
 w.location.hash='#lexico';await until(()=>$('#search')&&$('#dictionary-grid .dictionary-card'));// #search es la búsqueda global: espera la lista$('#search').value='arbol';$('#search').dispatchEvent(new w.Event('input'));await until(()=>$('#dictionary-grid').textContent.includes('árbol florido'));assert($('#dictionary-grid').textContent.includes('árbol'));assert($('#dictionary-grid').textContent.includes('árbol florido'));
 $('#period').value='modern';$('#period').dispatchEvent(new w.Event('change'));assert($('#dictionary-grid').textContent.includes('No hay coincidencias.'));
 w.location.hash='#lexico/buscar/tototl';await until(()=>$('#dictionary-grid .word-card-link strong')?.textContent==='tototl');assert($('#dictionary-order').textContent.includes('exactas primero'));
 w.location.hash='#lexico/buscar/chachalaca';await until(()=>$('[data-archive-fallback]'));assert.equal($('[data-archive-fallback]').getAttribute('href'),'#investigar/chachalaca');$('[data-archive-fallback]').click();await until(()=>$('#archive-count')?.textContent==='3 resultados');assert($('#archive-results').textContent.includes('parlotea'));
 w.location.hash='#lexico/buscar/'+encodeURIComponent('<script>missing</script>');await until(()=>$('[data-archive-fallback]')?.textContent.includes('<script>'));assert.equal($('#dictionary-grid script'),null);
 w.location.hash='#aprender/flor';await until(()=>$('[data-answer]'));assert($('.reading-translation').hidden);$('[data-annotation="1"]').click();assert($('.word-help').textContent.includes('flor'));assert($('.word-help').textContent.includes('documentos distintos'));
 $('[data-save-word="sense-xochitl"]').click();assert.equal($('[data-save-word="sense-xochitl"]').getAttribute('aria-pressed'),'true');
 $('[data-answer="0"]').click();assert($('.exercise-feedback').textContent.includes('Vuelve'));assert(!$('.exercise-feedback').textContent.includes('CONTEMPLO'));assert.equal(w.savedPassage('sense-xochitl').example.archive_id,$('.reading-card').dataset.archiveId);assert($('#next-example').disabled);
 $('[data-answer="1"]').click();assert(!$('#next-example').disabled);$('#next-example').click();assert($('.guided-passage').textContent.includes('_____'));
 $('[data-annotation="1"]').click();assert($('.word-help').textContent.includes('canto'));assert($('.word-help img').src.includes('xochitl10r'));assert($('.association-note').textContent.includes('No representa Cuicatl'));assert($('.association-note').textContent.includes('In xochitl, in cuicatl'));assert.equal($('.word-help a[href^="#lexico/sense-cuicatl?"]').getAttribute('href'),'#lexico/sense-cuicatl?'+new w.URLSearchParams({from:'aprender',lesson:'flor',passage:$('.reading-card').dataset.archiveId}));
 $('[data-answer="2"]').click();$('#next-example').click();$('[data-annotation="0"]').click();assert.equal($('.word-help a[href^="#lexico/sense-cacahuaxochitl?"]').getAttribute('href'),'#lexico/sense-cacahuaxochitl?'+new w.URLSearchParams({from:'aprender',lesson:'flor',passage:$('.reading-card').dataset.archiveId}));assert($('.word-help img').src.includes('CacahuaxochitlMH885v'));assert($('.association-note').textContent.includes('nombre personal'));assert($('.word-help').textContent.includes('identificación botánica'));
 $('[data-answer="0"]').click();$('#next-example').click();assert($('.guided-passage').textContent.includes('_____'));$('[data-answer="0"]').click();assert($('#next-example').disabled);$('[data-answer="2"]').click();$('#next-example').click();assert($('.completion-card'));
 assert.equal(w.lessonProgress({id:'cielo',version:2,practice_version:1,examples:[1,2,3,4]}).edition,'lectura-clasica-v1:1');
 // Práctica v2: el progreso de la edición anterior no se aplica a las opciones nuevas (reglas de versión).
 w.eval("study.lessons['synthetic-legacy']={edition:'lectura-clasica-v1:1',passed:[0,1],comprehension:[0],step:1}");
 assert.equal(JSON.stringify(w.lessonProgress({id:'synthetic-legacy',practice_version:1,examples:[1,2,3,4]}).passed),'[0,1]');
 assert.equal(JSON.stringify(w.lessonProgress({id:'synthetic-legacy',practice_version:2,examples:[1,2,3,4]}).passed),'[]');w.eval("delete study.lessons['synthetic-legacy']");
 const saved=JSON.parse(w.localStorage.getItem('scriptorium-study-v1'));assert(saved.saved.includes('sense-xochitl'));assert.equal(saved.lessons.flor.passed.length,4);assert.equal(saved.lessons.flor.edition,'lectura-clasica-v1:3');
 w.location.hash='#aprender/lugares';await until(()=>$('.guided-passage'));$('[data-step="1"]').click();$('[data-annotation="0"]').click();assert($('.word-help h3').textContent==='tlacuilolcalli');assert($('.word-help').textContent.includes('Comparación temática'));assert($('.lookup-reference').textContent.includes('calli'));assert($('.word-help').textContent.includes('no escribe el compuesto completo'));
 for(const lid of ['agua-tierra','flores-cantos','aves']){
  w.location.hash='#aprender/'+lid;
  const lessons=(await(await w.fetch('/api/learning')).json()).lessons,l=lessons.find(l=>l.id===lid);
  await until(()=>$('#content h1')?.textContent===l.title&&d.querySelectorAll('[data-step]').length===4);
  if(lid==='aves'){
   // Un solo aviso de revisión por página (el de la cabecera); sin bloque propio de Aves.
   assert.equal($('.aves-availability'),null);assert.equal(d.querySelectorAll('.review-notice').length,1);
   assert($('#review-notice').textContent.includes('revisión lingüística'));assert(!$('#content').textContent.includes('revisión lingüística'));
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
  if(lid==='aves'){
   assert.equal($('.aves-availability'),null);assert.equal(d.querySelectorAll('.review-notice').length,1);
   const beforeExplanation=w.localStorage.getItem('scriptorium-study-v1');
   const compare=$('.aves-self-explanation');assert(compare);assert(!compare.open);
   const compared=[...compare.querySelectorAll('[data-comparison-archive]')];
   assert.deepEqual(compared.map(a=>a.dataset.comparisonArchive),['axolotl-14546','axolotl-14253']);
   for(const [i,article] of compared.entries()){
    assert.equal(article.querySelector('blockquote [lang="nci"]').textContent,l.examples[i].passage.nah);
    assert.equal(article.querySelector('blockquote p:last-child').textContent,l.examples[i].passage.es);
    assert(article.textContent.includes(l.examples[i].passage.locator));
    assert(article.querySelector('a[href^="https://"]'));
    assert(article.querySelector('a[href^="#leer/aves?"]').hash.includes('passage='+l.examples[i].archive_id));
   }
   compare.open=true;const explanation=compare.querySelector('textarea');assert(explanation.labels.length);
   explanation.value='Explicación sintética <script>no ejecutar</script>';
   explanation.dispatchEvent(new w.Event('input',{bubbles:true}));
   assert.equal(compare.querySelector('script'),null);
   assert.equal(compare.querySelector('button'),null);
   assert.equal(w.localStorage.getItem('scriptorium-study-v1'),beforeExplanation);
   assert(compare.textContent.includes('No se califica automáticamente'));
   console.log('PASS: Aves disponible, cuatro pasajes y ocho ejercicios, autoexplicación opcional con originales/citas/retorno, sin calificación ni nueva escritura');
  }else assert.equal($('.aves-self-explanation'),null);
 }
 const shortLesson=(await(await w.fetch('/api/learning')).json()).lessons.find(l=>l.id==='agua-tierra');w.renderLesson({...shortLesson,id:'synthetic-short',examples:shortLesson.examples.slice(0,2)});assert.equal(d.querySelectorAll('[data-step]').length,2);for(const e of shortLesson.examples.slice(0,2)){$('[data-answer="'+e.exercise.answer+'"]').click();$('#next-example').click();}assert($('.completion-card'));assert($('#content').textContent.includes('los 2 fragmentos'));
 w.location.hash='#leer';await until(()=>$('#reader-examples'));assert.equal(d.querySelectorAll('.reading-card').length,48);assert($('.reading-translation').textContent.includes('CONTEMPLO'));
 w.location.hash='#palabras';await until(()=>$('#start-review'));assert.equal($('.saved-grid').children.length,1);$('#start-review').click();assert($('#review-answer').hidden);assert($('.saved-context blockquote').textContent.toLowerCase().includes('xochitl'));assert($('.saved-context a').getAttribute('href').startsWith('#leer/'));$('#show-word').click();assert(!$('#review-answer').hidden);assert($('.review-translation').textContent.length>0);$('#known-word').click();assert($('#finish-review'));$('#finish-review').click();assert($('#start-review').disabled);
 const migrated=JSON.parse(w.localStorage.getItem('scriptorium-study-v1'));assert.equal(migrated.lessons.aves.edition,'lectura-clasica-v1:2');assert.equal(migrated.lessons.aves.passed.length,4);assert.equal(migrated.lessons.aves.comprehension.length,4);assert.equal(migrated.reviews['sense-tototl'].streak,2);
 console.log('PASS: guided reading, contextual glyph help, incorrect-answer feedback, exact-form exercise, completion, saved words and review');
 w.location.hash='#aprender/aves';await until(()=>$('[data-step="0"]'));$('[data-step="0"]').click();$('[data-annotation="0"]').click();$('[data-save-word="sense-tototl"]').click();
 assert.equal(w.savedPassage('sense-tototl').example.archive_id,'axolotl-14546');
 $('[data-step="1"]').click();$('[data-annotation="0"]').click();$('[data-save-context="sense-tototl"]').click();
 assert.equal(w.savedPassage('sense-tototl').example.archive_id,'axolotl-14253');assert.equal(JSON.parse(w.localStorage.getItem('scriptorium-study-v1')).reviews['sense-tototl'].streak,2);
 $('[data-save-word="sense-tototl"]').click();assert.equal(w.savedPassage('sense-tototl'),undefined);
 console.log('PASS: dictionary-to-archive continuation, exact-first lookup, saved passage context, source-backed comprehension and legacy progress preserved');
 console.log('PASS: accent-insensitive search, separate senses, contextual references and explicit absent variant');
 const studyBeforeGlyphs=w.localStorage.getItem('scriptorium-study-v1');
 const publicPictography=await(await w.fetch('/api/pictography')).json();
 const designationCount=new Set(publicPictography.elements.map(e=>e.designation)).size;
 const calliElementIds=new Set(publicPictography.elements.filter(e=>e.designation==='calli').map(e=>e.id));
 const calliAppearances=publicPictography.occurrences.filter(o=>o.components.some(c=>calliElementIds.has(c.element_id))).length;
 const calliLinkedIds=new Set(publicPictography.elements.filter(e=>e.lexical_links.some(l=>l.sense_id==='sense-calli')).map(e=>e.id));
 const calliLinkedAppearances=publicPictography.occurrences.filter(o=>o.components.some(c=>calliLinkedIds.has(c.element_id))).length;
 w.location.hash='#glifos';await until(()=>$('#pictographic-results .pictographic-card'));
 assert.equal(d.title,'Amoxcalli · Glifos');assert.equal($('#pictographic-results').children.length,24);
 assert($('#pictographic-count').textContent.startsWith(`${designationCount} denominaciones`));assert($('#pictographic-count').textContent.includes(`${publicPictography.elements.length} registros`));assert($('.pictographic-inventory').textContent.includes(`${publicPictography.summary.components} apariciones de componentes`));
 $('#pictographic-next').click();assert($('#pictographic-range').textContent.includes('25–48'));
 $('#pictographic-search').value='calli';$('#pictographic-search').dispatchEvent(new w.Event('input'));
 const calliMatches=publicPictography.elements.filter(e=>[e.designation,e.code,...e.meanings].join(' ').toLowerCase().includes('calli'));
 assert($('#pictographic-count').textContent.startsWith(`${new Set(calliMatches.map(e=>e.designation)).size} denominaciones · ${calliMatches.length} registros`));assert($('.pictographic-card h2').textContent==='calli');
 $('#pictographic-document').value='calpan';$('#pictographic-document').dispatchEvent(new w.Event('change'));
 assert($('#pictographic-count').textContent.startsWith('1 '));
 w.location.hash='#glifos/elemento/'+encodeURIComponent('calpan:element:05.01.01');await until(()=>$('.pictographic-element'));
 assert.equal(d.querySelectorAll('.pictographic-comparison article').length,calliAppearances);
 assert($('.pictographic-element').textContent.includes('tecpan'));assert($('.pictographic-element').textContent.includes('chan'));
 assert($('.pictographic-element a[href="#lexico/sense-calli"]'));
 w.location.hash='#glifos/ficha/'+encodeURIComponent('calpan:073_08_A_01');await until(()=>$('.pictographic-entry'));
 assert.equal($('.pictographic-reading h2').textContent,'tecpan');assert($('.pictographic-components').textContent.includes('calli'));
 assert($('.source-hash').textContent.includes('SHA-256'));assert($('.pictographic-provenance').textContent.includes('Perla Valle'));
 const glyphImage=$('img[data-pictographic-image]');glyphImage.dispatchEvent(new w.Event('error'));assert(glyphImage.hidden);assert(!$('.image-fallback').hidden);
 const severalPageDoc=publicPictography.documents.find(doc=>publicPictography.pages.filter(p=>p.document_id===doc.id).length>1);
 if(severalPageDoc){w.location.hash='#glifos/documento/'+encodeURIComponent(severalPageDoc.id);await until(()=>$('.pictographic-provenance summary')?.textContent==='Alcance del registro inicial');assert($('.pictographic-provenance').textContent.includes(severalPageDoc.scope));}
 w.location.hash='#glifos/observar';await until(()=>$('#glyph-observation-feedback'));
 $('[data-observe-answer="0"]').click();assert($('#glyph-observation-feedback').textContent.includes('Compara'));
 $('[data-observe-answer="1"]').click();assert($('#glyph-observation-feedback').textContent.includes('Sí.'));
 assert.equal(w.localStorage.getItem('scriptorium-study-v1'),studyBeforeGlyphs);
 w.location.hash='#glifos/apariciones';await until(()=>$('#pictographic-type'));
 $('#pictographic-type').value='personage';$('#pictographic-type').dispatchEvent(new w.Event('change'));assert($('#pictographic-count').textContent.startsWith(`${publicPictography.occurrences.filter(o=>o.kind==='personage').length} `));
 let glyphExport;const savedDownload=w.download;w.download=(name,value)=>glyphExport={name,value};$('#pictographic-export').click();w.download=savedDownload;
 assert(glyphExport.name.startsWith('amoxcalli-pictografia-'));assert.equal(glyphExport.value.rights.training,false);assert(!Object.hasOwn(glyphExport.value,'profile'));assert(!Object.hasOwn(glyphExport.value,'study'));
 w.location.hash='#glifos/ficha/missing';await until(()=>$('#pictographic-content').textContent.includes('No se encontró'));
 w.location.hash='#lexico/sense-calli';await until(()=>$('.pictographic-bridge'));assert($('.pictographic-bridge').textContent.includes(`${calliLinkedAppearances} apariciones`));
 assert.equal(w.localStorage.getItem('scriptorium-study-v1'),studyBeforeGlyphs);
 console.log('PASS: documentary elements, pagination, filters, context-specific values, guided observation, source hashes, image fallback, public export and study preserved');
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
 const studyBeforeLab=w.localStorage.getItem('scriptorium-study-v1');
 w.location.hash='#modelos/progreso';await until(()=>$('#lab-progress'));
 const comparison=await(await w.fetch('/api/laboratory')).json(),dc=comparison.documentary;
 await until(()=>$('#lab-visual-case')?.options.length===51);
 const visualStatus=comparison.visual_preparation;
 assert.equal(visualStatus.candidate.status,'not_run');assert.equal(visualStatus.case_count,51);assert(!Object.hasOwn(visualStatus,'cases'));
 assert.equal(visualStatus.candidate.metrics,null);assert.equal(visualStatus.candidate.cost,null);assert.equal(visualStatus.execution_enabled,false);
 const visualReview=await(await w.fetch('/api/laboratory/visual-preparation')).json();
 assert.equal(visualReview.cases.length,51);assert(visualReview.cases.every(c=>c.split==='development'&&c.modality==='visual'));
 assert($('#lab-visual-preparation').textContent.includes('no son un benchmark de reconocimiento de píxeles'));
 assert($('#lab-visual-preparation').textContent.includes('sin revisión humana nueva'));
 assert.equal($('#lab-visual-preparation img'),null);assert.equal($('#lab-visual-preparation button'),null);
 assert($('#lab-visual-case').labels.length);assert($('#lab-visual-work').labels.length);
 assert.equal($('#lab-visual-status').getAttribute('aria-live'),'polite');
 const firstVisual=visualReview.cases[0];assert.equal($('#lab-visual-case').value,firstVisual.id);
 assert.equal($('.lab-visual-question p').textContent,firstVisual.question);
 assert.equal($('.lab-visual-question table'),null);assert(!$('.lab-visual-question').textContent.includes('Campos esperados'));
 assert.equal($('[data-visual-reference]').open,false);assert($('[data-visual-reference]').textContent.includes(firstVisual.reference.fields[0].field));
 assert($('.lab-visual-question a[href^="https://"]'));assert($('.lab-visual-question').textContent.includes('Abrir catálogo del documento'));assert(firstVisual.proposed_input.image_reference_urls.every(url=>$('.lab-visual-question').textContent.includes(url.split('/').at(-1))));assert.equal($('.lab-visual-question img'),null);
 const componentCase=visualReview.cases.find(c=>c.reference.fields.some(f=>f.field==='components'));
 $('#lab-visual-case').value=componentCase.id;$('#lab-visual-case').dispatchEvent(new w.Event('change'));
 assert($('[data-visual-reference]').textContent.includes('components'));
 assert.equal($('.lab-visual-question p').textContent,componentCase.question);
 assert(!Object.hasOwn(componentCase.proposed_input,'reference'));assert(!Object.hasOwn(componentCase.proposed_input,'fields'));
 const work=visualReview.cases[0].document.id;$('#lab-visual-work').value=work;$('#lab-visual-work').dispatchEvent(new w.Event('change'));
 assert.equal($('#lab-visual-case').options.length,visualReview.cases.filter(c=>c.document.id===work).length);
 assert([...$('#lab-visual-case').options].every(o=>visualReview.cases.find(c=>c.id===o.value).document.id===work));
 $('#lab-visual-work').value='';$('#lab-visual-work').dispatchEvent(new w.Event('change'));assert.equal($('#lab-visual-case').options.length,51);
 const fake=JSON.parse(JSON.stringify(firstVisual));fake.reference.fields[0].value='<img src="https://image.invalid" onerror="bad()">';fake.reference.attributed_responsibility=['<script>literal source</script>'];fake.proposed_input.catalog_page_url='javascript:alert(1)';
 const holder=d.createElement('div');holder.innerHTML=w.labVisualCase(fake);assert.equal(holder.querySelector('script'),null);assert.equal(holder.querySelector('img'),null);assert.equal(holder.querySelector('a[href^="javascript:"]'),null);assert(holder.textContent.includes('<script>literal source</script>'));
 for(const query of ['?split=reserve','?path=data/community/private.sqlite3']){const denied=await w.fetch('/api/laboratory/visual-preparation'+query);assert.equal(denied.status,400);assert(!Object.hasOwn(await denied.json(),'cases'));}
 const noExecute=await w.fetch('/api/laboratory/visual-preparation',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});assert.equal(noExecute.status,405);
 const incomplete=w.labVisualPreparation({...visualStatus,available:false,case_count:0});assert(incomplete.includes('no se muestran referencias'));assert(!incomplete.includes('Campos de referencia'));
 const labStorage=w.localStorage.getItem('scriptorium-study-v1');assert.equal(labStorage,studyBeforeLab);
 console.log('PASS: preparación visual not_run, 51 casos documentales de desarrollo, selector/obra, referencias separadas y colapsadas, fuentes escapadas/enlaces sin imágenes, sin ejecución/reserva/progreso');
 assert(dc.available,'Current documentary comparison must have validated source evidence');
 assert.equal(d.querySelectorAll('[data-documentary-method]').length,3);assert.equal(d.querySelectorAll('.lab-tabs a').length,3);
 const retrievalNode=$('[data-documentary-method="retrieval"]');
 assert(retrievalNode.textContent.includes('119/123'));assert(retrievalNode.textContent.includes('121/121'));assert(retrievalNode.textContent.includes('121/123'));assert(retrievalNode.textContent.includes('840/860'));assert(retrievalNode.textContent.includes('2 / 2'));
 assert.equal(dc.runs[0].metrics.complete,119);assert.equal(dc.runs[0].metrics.queries,123);assert.equal(dc.runs[0].metrics.abstained,2);assert.equal(dc.runs[0].failures.length,4);
 assert.equal(d.querySelectorAll('#lab-documentary-failures li').length,4);assert.equal(d.querySelectorAll('#lab-documentary-failures a[href^="#consultar/"]').length,4);assert($('#lab-documentary a[href="#consultar"]'));
 for(const method of ['textual_model','multimodal_candidate']){const node=$(`[data-documentary-method="${method}"]`),run=dc.runs.find(r=>r.method===method);assert(node.textContent.includes('Sin ejecutar'));assert(node.textContent.includes('Puntuación: Sin medir'));assert(node.textContent.includes('Tiempo, memoria y coste monetario: Sin medir'));assert(run.reason.length>30);assert.equal(run.metrics,null);assert.equal(run.cost,null);assert.deepEqual(run.report_hashes,{});}
 assert($('#lab-documentary').textContent.includes('no hay una comparación de rendimiento'));assert($('#lab-documentary').textContent.includes('no mide comprensión general'));assert($('#lab-documentary').textContent.includes('tracemalloc'));assert($('#lab-documentary').textContent.includes('memoria total del proceso'));assert($('#lab-documentary').textContent.includes('training:false'));assert($('#lab-documentary').textContent.includes('image_model_input:false'));assert($('#lab-documentary').textContent.includes('pendientes'));
 assert($('#lab-documentary-sources').textContent.includes(dc.battery.sha256));assert.equal(dc.battery.reserve_used,false);assert.equal(dc.human_review,'pending');assert.equal(dc.rights.training,false);assert.equal(dc.rights.image_model_input,false);
 assert.equal($('#lab-documentary [style]'),null);assert.equal(w.getComputedStyle($('.lab-methods')).display,'grid');
 const rejectKeys=new Set(['reference','expected_fields','expected_target_ids','missing_fields','source_conditions']);
 const assertNoKeys=value=>{if(value&&typeof value==='object'){for(const [key,item] of Object.entries(value)){assert(!rejectKeys.has(key),`Oracle/reserve key exported: ${key}`);if(key==='queries')assert.equal(typeof item,'number','Only aggregate query counts can be exported');assertNoKeys(item);}}};
 for(const id of ['documentary-comparison','documentary-retrieval']){const response=await w.fetch('/api/laboratory/reports/'+id);assert.equal(response.status,200);const exported=await response.json();assertNoKeys(exported);assert.equal(exported.battery.evaluated_split,'development');assert.equal(exported.battery.reserve_used,false);}
 for(const id of ['documentary-battery','documentary-reserve','../../data/community/private']){const response=await w.fetch('/api/laboratory/reports/'+id);assert.equal(response.status,404);}
 assert.equal($('#lab-documentary img'),null);assert($('#lab-progress').textContent.includes('Resultados históricos'));assert($('#lab-progress').textContent.includes('otras muestras'));assert($('#lab-documentary').compareDocumentPosition($('#lab-progress'))&w.Node.DOCUMENT_POSITION_FOLLOWING);
 assert($('#lab-progress').textContent.includes('22.58'));assert($('#lab-progress').textContent.includes('27.96'));assert($('#lab-progress').textContent.includes('Los hashes actuales no coinciden'));assert($('.lab-curve svg'));assert($('#lab-how').textContent.includes('no reconoce imágenes'));$('[data-lab-target="lab-progress"]').click();assert.equal(w.location.hash,'#modelos/progreso');assert.equal(w.localStorage.getItem('scriptorium-study-v1'),studyBeforeLab);

 console.log('PASS: documentary laboratory comparison, measured costs, honest not_run states, failures, fresh source hashes and safe public downloads');
 w.location.hash='#modelos/probar';await until(()=>$('#compose'));assert.equal($('#experiment-mode').value,'corpus');$('#compose-text').value='flor';$('#experiment-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#compose-result h2'));assert($('#compose-result').textContent.includes('sin LLM'));$('#experiment-mode').value='rules';$('#experiment-mode').dispatchEvent(new w.Event('change'));$('#compose-text').value='Veo una flor.';$('#experiment-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#review-export'));assert($('#compose-result').textContent.includes('Niquitta xochitl.'));assert($('#compose-result').textContent.includes('Regla local · sin LLM'));
 w.location.hash='#modelos/datos';await until(()=>$('#training-rows .training-pair'));assert($('#training-count').textContent.includes('650'));assert.equal($('#training-rows').children.length,20);$('#training-next').click();await until(()=>$('#training-range').textContent.includes('21–40'));$('#training-dataset').value='train';$('#training-dataset').dispatchEvent(new w.Event('change'));await until(()=>$('#training-count').textContent.includes('2,161'));
 const pf=$('#training-pair-form');pf.elements.es.value='TEXTO SINTÉTICO UI';pf.elements.nah.value='FORMA SINTÉTICA DE PRUEBA';pf.elements.document.value='Colección de QA UI';pf.elements.locator.value='Registro sintético';pf.elements.source_url.value='https://example.org';pf.elements.license.value='CC-BY-4.0';for(const k of ['authorship','review_consent','training_consent'])pf.elements[k].checked=true;pf.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#pair-message').textContent.includes('Guardado'));await until(()=>$('.withdraw-pair'));assert($('#pair-proposals').textContent.includes('Pendiente de revisión'));
 const exp=await(await w.fetch('/api/training-pairs/export')).text();assert.equal(exp.trim().split('\n').length,1);$('.withdraw-pair').click();await until(()=>$('#pair-proposals').textContent.includes('Retirado'));
 const csvResult=w.pairCSV('es,nah,document,locator,source_url,license,reviewer,iso\n"texto, con coma","forma\nsegunda línea",Obra,Folio,https://example.org,CC-BY-4.0,,nci\n');assert.equal(csvResult[0].es,'texto, con coma');assert.equal(csvResult[0].nah,'forma\nsegunda línea');
 console.log('PASS: laboratory tabs, separate corpus/rules, training pairs, pagination, CSV and private proposals');
 w.location.hash='#aprender/casas-relatos';await until(()=>$('.reading-card [data-interlinear]'));{const card=$('.reading-card');assert.equal(card.dataset.clozeBlank,'calli');assert(card.querySelectorAll('.plain-word').length>5);assert(!card.querySelector('.guided-passage').textContent.includes('calli'));card.querySelector('[data-interlinear]').click();await until(()=>card.querySelector('.interlinear'));assert(card.querySelector('.interlinear').textContent.includes('_____'));assert(!/cal-li/.test(card.querySelector('.interlinear').textContent));
 [...d.querySelectorAll('[data-answer]')].find(b=>b.textContent.trim()==='calli').click();await until(()=>!$('.reading-card').dataset.clozeBlank);assert($('.reading-card .guided-passage').textContent.includes('calli'));$('.reading-card [data-annotation]').click();await until(()=>$('.reading-help .auto-analysis .word-analysis')&&!$('.reading-help .auto-analysis').textContent.includes('Analizando'));assert($('.reading-help .auto-analysis').textContent.includes('cal'));}
 console.log('PASS: Aprender usa el mismo análisis que Leer: palabras analizables y glosa durante el ejercicio con el hueco oculto, pasaje completo al responder y análisis dentro de la ayuda');
 w.location.hash='#preguntar/kuali';await until(()=>$('.ask-understood'));assert($('.ask-understood').textContent.includes('cualli'));assert(d.querySelectorAll('.ask-passage').length>=3);assert($('.ask-passage mark'));assert.equal($('[data-page="preguntar"]').getAttribute('aria-current'),'page');assert($('.ask-note').textContent.includes('Sin llamadas a modelos'));assert($('.ask-explanation').textContent.includes('Sin modelo'));assert(!$('[data-explain-claude]'));{const cite=$('.ask-cite');assert(cite);const target=$(`[data-evidence-id="${cite.dataset.cite}"]`);assert(target);cite.click();assert(target.classList.contains('ask-flash'));}
 w.location.hash='#preguntar/'+encodeURIComponent('¿cómo se dice mujer?');await until(()=>$('.ask-candidates'));assert(/ciuatl|cihuatl/.test($('.ask-candidates').textContent));assert($('.ask-result').textContent.includes('No es una definición'));
 w.location.hash='#preguntar/xyzq';await until(()=>$('.ask-abstained'));assert.equal($('.ask-abstained a').getAttribute('href'),'#investigar/xyzq');
 w.location.hash='#preguntar/'+encodeURIComponent('<b>dos</b> palabras');await until(()=>$('#ask-status')?.textContent.includes('sola palabra'));assert.equal($('#ask-results b'),null);
 // Misma búsqueda de términos en las cuatro vistas: mujer → cihuatl con sus grafías, sin entrada de diccionario.
 for(const [hash,ready] of [['#lexico/buscar/mujer','#dictionary-term .term-group'],['#investigar/mujer','#archive-term .term-group'],['#preguntar/mujer','#ask-results .term-group'],['#consultar/mujer','#documentary-term .term-group']]){w.location.hash=hash;await until(()=>$(ready));assert.equal($(ready).dataset.termId,'term-siwatl');assert($(ready).textContent.includes('ciuatl'));assert($(ready+' a[href="#preguntar/mujer"]'));}
 for(const q of ['kuali','qualli']){w.location.hash='#lexico/buscar/'+q;await until(()=>$('#dictionary-term .term-group')?.dataset.termId==='term-kwali');assert($('#dictionary-term .term-uncertain').textContent.includes('tlacualli'));}
 w.location.hash='#investigar/nocal';await until(()=>$('#archive-term .term-group'));assert.equal($('#archive-term .term-group').dataset.termId,'lemma-kalli');assert($('#archive-term h2').textContent==='calli');assert($('#archive-term a[href^="#glifos/elemento/"]'));
 console.log('PASS: preguntar con evidencia: grafía laxa, pasajes resaltados, español→raíz, abstención, error escapado; un mismo grupo de término en Diccionario, Archivo, Preguntar y Consultar fichas');
 w.location.hash='#fuentes';await until(()=>$('#source-results'));assert($('#source-results').textContent.includes('UNAM'));assert.equal($('#source-results').children.length,20);
 w.location.hash='#textos';await until(()=>$('#text-results'));assert.equal($('#text-results').children.length,3);
 assert.deepEqual(errors,[]);console.log('PASS: sources and texts render with no application JavaScript errors');dom.window.close();
})().catch(e=>{console.error(e);process.exit(1);});
