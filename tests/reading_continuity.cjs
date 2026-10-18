const assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const origin=process.env.CORPUS_QA_ORIGIN,errors=[],requests=[],writes=[],scrolls=[];
const initial={version:1,saved:['sense-tototl'],lessons:{aves:{edition:'lectura-clasica-v1:2',passed:[0],comprehension:[],step:2}},reviews:{'sense-tototl':{streak:2,due:1900000000000}},contexts:{'sense-tototl':{archive_id:'axolotl-14546'}}};
const initialRaw=JSON.stringify(initial,null,1);
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,tries=240){for(let i=0;i<tries;i++){if(fn())return;await pause(25);}throw Error('UI timeout');}
(async()=>{
 const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
 const dom=await JSDOM.fromURL(origin+'/#leer/aves',{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
  w.localStorage.setItem('scriptorium-study-v1',initialRaw);
  const originalSet=w.Storage.prototype.setItem;w.Storage.prototype.setItem=function(k,v){writes.push(k);return originalSet.call(this,k,v);};
  w.fetch=async(url,options={})=>{requests.push({url:String(url),method:options.method||'GET'});return fetch(new URL(url,origin),options);};
  w.matchMedia=()=>({matches:false});w.Element.prototype.scrollIntoView=function(){scrolls.push(this.dataset.archiveId);};
  w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 }});
 const w=dom.window,d=w.document,$=s=>d.querySelector(s);
 const navigate=async(hash,ready)=>{const old=$('#content').firstElementChild;w.location.hash=hash;await until(()=>$('#content').firstElementChild!==old&&ready());};
 await until(()=>$('.reading-card'));
 assert.equal($('#reader-lesson').value,'aves');
 const first=$('.reading-card'),archiveId=first.dataset.archiveId;
 assert.equal(archiveId,'axolotl-14546');
 first.querySelector('[data-explore-word="chachalaca"]').click();
 // Primera búsqueda del servidor: construye el índice de términos (~4 s en frío con el catálogo ampliado).
 await until(()=>$('#archive-count')?.textContent==='3 resultados',800);
 if(process.env.READING_CONTINUITY_BASELINE){
  assert.equal(w.location.hash,'#investigar/chachalaca');assert.equal($('[data-reading-return]'),null);
  assert($('a[href="#leer"]'));assert.equal(w.localStorage.getItem('scriptorium-study-v1'),initialRaw);assert.equal(writes.length,0);
  console.log('BASELINE: Aves → chachalaca → 3 resultados; sin origen/retorno al pasaje axolotl-14546. Almacenamiento intacto.');dom.window.close();return;
 }
 const publicLearning=await(await w.fetch('/api/learning')).json(),birds=publicLearning.lessons.find(l=>l.id==='aves');
 assert.equal(w.location.hash,'#investigar/chachalaca?from=leer&lesson=aves&passage=axolotl-14546');
 const back=$('[data-reading-return]');assert.equal(back.textContent,'Volver al pasaje de '+birds.title);assert(back.parentElement.textContent.includes('Axolotl'));
 assert.equal(d.activeElement,back);assert.equal(w.getComputedStyle(back).whiteSpace,'normal');
 assert.equal($('#research-work').value,'');assert.equal($('#research-variant').value,'nci');
 back.focus();assert.equal(d.activeElement,back);back.click();await until(()=>d.activeElement?.dataset.archiveId===archiveId);
 assert.equal($('#reader-lesson').value,'aves');assert.equal(d.querySelectorAll('.reading-card').length,4);assert.equal(scrolls.at(-1),archiveId);
 assert.equal(d.activeElement.getAttribute('tabindex'),'-1');assert(d.activeElement.getAttribute('aria-label').includes(birds.title));
 console.log('PASS: reader Aves → chachalaca archive → exact passage, keyboard focus, scroll and unfiltered results');

 // Choose a different published passage; no exercise answers are clicked.
 const other=publicLearning.lessons.find(l=>l.id!=='aves'),otherId=other.examples[1].archive_id;
 await navigate('#leer/'+other.id,()=>$('#reader-lesson')?.value===other.id);
 const card=d.querySelectorAll('.reading-card')[1],input=card.querySelector('input');input.value='zzzzsinentrada011';input.dispatchEvent(new w.Event('input'));
 card.querySelector('[data-dictionary-lookup]').click();await until(()=>$('#dictionary-grid .empty'));
 assert.equal($('#search').value,'zzzzsinentrada011');assert($('[data-reading-return]').textContent.includes(other.title));
 $('[data-archive-fallback]').click();await until(()=>$('#archive-count')?.textContent==='0 resultados');
 assert.equal(new w.URLSearchParams(w.location.hash.split('?')[1]).get('passage'),otherId);
 $('[data-reading-return]').click();await until(()=>d.activeElement?.dataset.archiveId===otherId);assert.equal($('#reader-lesson').value,other.id);
 // Annotation help and dictionary result/detail links retain the same origin.
 d.activeElement.querySelector('[data-annotation]').click();const help=$('.reading-help a[href^="#lexico/"]');assert(help.hash.includes('passage='+otherId));
 help.click();await until(()=>$('.dictionary-entry'));assert($('[data-reading-return]'));
 $('.dictionary-entry a[href^="#investigar/"]').click();await until(()=>$('#research-form'));assert($('[data-reading-return]'));
 $('[data-reading-return]').click();await until(()=>d.activeElement?.dataset.archiveId===otherId);
 const active=d.activeElement,lookup=active.querySelector('input');lookup.value='atl';lookup.dispatchEvent(new w.Event('input'));
 active.querySelector('[data-dictionary-lookup]').click();await until(()=>$('#dictionary-grid .dictionary-card'));
 const result=$('.word-card-link');assert(result.hash.includes('passage='+otherId));result.click();await until(()=>$('.dictionary-entry'));
 assert($('[data-reading-return]').hash.includes('passage='+otherId));$('[data-reading-return]').click();await until(()=>d.activeElement?.dataset.archiveId===otherId);
 console.log('PASS: another source → empty dictionary → archive fallback → same passage; annotation detail → archive preserves origin');

 // Guided return overrides the visible step without writing the persisted step.
 const guideId=publicLearning.lessons.find(l=>l.id==='aves').examples[1].archive_id;
 await navigate('#aprender/aves?from=aprender&lesson=aves&passage='+guideId,()=>d.activeElement?.dataset.archiveId===guideId);
 assert.equal($('[data-step="1"]').getAttribute('aria-current'),'step');
 const guided=$('.reading-card');guided.querySelector('[data-annotation]').click();$('.reading-help a[href^="#lexico/"]').click();await until(()=>$('.dictionary-entry'));
 assert($('[data-reading-return]').hash.startsWith('#aprender/aves?'));$('[data-reading-return]').click();await until(()=>d.activeElement?.dataset.archiveId===guideId);
 assert.equal($('.reading-translation').hidden,true);assert.equal($('.exercise-feedback').textContent,'');assert.equal($('.comprehension-feedback').textContent,'');
 assert.equal($('#next-example').disabled,true);
 console.log('PASS: guided return selects exact step, leaves answers blank and preserves persisted progress');

 // Legacy/direct routes and untrusted origins: unknown, cross-lesson, duplicate,
 // external, malformed escape and mode mismatch must never produce a return.
 const invalid=['from=leer&lesson=aves&passage='+otherId,'from=https%3A%2F%2Fevil.invalid&lesson=aves&passage='+archiveId,
  'from=leer&lesson=missing&passage='+archiveId,'from=leer&lesson=aves&passage=%ZZ','from=leer&lesson=aves&passage='+archiveId+'&passage='+archiveId,
  'from=leer&lesson=aves&passage='+archiveId+'&extra=%3Cscript%3E','from=leer&lesson=%3Cimg%20onerror%3Dalert(1)%3E&passage='+archiveId];
 for(const query of invalid){await navigate('#investigar/chachalaca?'+query,()=>$('#research-query')?.value==='chachalaca'&&!$('[data-reading-return]'));await until(()=>$('#archive-count')?.textContent==='3 resultados');assert.equal($('#content script'),null);assert.equal($('#content img[onerror]'),null);}
 await navigate('#lexico/buscar/zzzzsinentrada011?'+invalid[0],()=>$('#dictionary-grid .empty'));assert.equal($('[data-reading-return]'),null);assert(!$('[data-archive-fallback]').hash.includes('?'));
 for(const hash of ['#lexico/buscar/atl','#investigar/chachalaca']){await navigate(hash,()=>hash.startsWith('#lexico')?$('#dictionary-grid .dictionary-card'):$('#research-query')?.value==='chachalaca');assert.equal($('[data-reading-return]'),null);}
 const punctuated='¿chachalaca?/atl & "<forma>"';
 await navigate('#investigar/'+encodeURIComponent(punctuated),()=>$('#research-query')?.value===punctuated);assert.equal($('[data-reading-return]'),null);assert.equal($('#research-query').value,punctuated);
 await navigate('#lexico/buscar/'+encodeURIComponent(punctuated),()=>$('#search')?.value===punctuated);assert.equal($('[data-reading-return]'),null);assert.equal($('#dictionary-grid script'),null);
 await navigate('#leer/aves?from=aprender&lesson=aves&passage='+archiveId,()=>$('#reader-lesson')?.value==='aves');assert.notEqual(d.activeElement?.dataset.archiveId,archiveId);
 await navigate('#leer/aves',()=>$('#reader-lesson')?.value==='aves');assert.equal(d.querySelectorAll('.reading-card').length,4);
 console.log('PASS: legacy/direct routes, malformed/external/duplicate/cross-lesson origins and HTML escaping');
 assert.equal(w.localStorage.getItem('scriptorium-study-v1'),initialRaw);assert.deepEqual(writes,[]);
 assert(requests.every(r=>r.method==='GET'));assert(!requests.some(r=>/proposals|bootstrap|community|voice|training-pairs/.test(r.url)));
 assert.deepEqual(errors,[]);console.log('PASS: study bytes unchanged, zero storage writes, public GET only, no application errors');dom.window.close();
})().catch(e=>{console.error(e);process.exit(1);});
