const assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const origin=process.env.CORPUS_QA_ORIGIN;
const initialRaw=JSON.stringify({version:1,saved:['sense-tototl'],lessons:{aves:{edition:'lectura-clasica-v1:2',passed:[0],comprehension:[],step:2}},reviews:{},contexts:{}});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){for(let i=0;i<240;i++){if(fn())return;await pause(25);}throw Error('UI timeout');}
(async()=>{for(const width of [360,390]){
 const errors=[],requests=[],writes=[],scrolls=[];const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
 const dom=await JSDOM.fromURL(origin+'/#leer/aves',{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
  Object.defineProperty(w,'innerWidth',{value:width});w.matchMedia=q=>({matches:/max-width:\s*(\d+)px/.test(q)&&width<=Number(q.match(/max-width:\s*(\d+)px/)[1]),media:q});
  w.localStorage.setItem('scriptorium-study-v1',initialRaw);const set=w.Storage.prototype.setItem;w.Storage.prototype.setItem=function(k,v){writes.push(k);return set.call(this,k,v);};
  w.fetch=async(url,options={})=>{requests.push({url:String(url),method:options.method||'GET'});return fetch(new URL(url,origin),options);};
  w.Element.prototype.scrollIntoView=function(){scrolls.push(this.dataset.archiveId);};w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 }});
 const w=dom.window,d=w.document,$=s=>d.querySelector(s);const suffix='?from=leer&lesson=aves&passage=axolotl-14546';
 const navigate=async(hash,ready)=>{const old=$('#content').firstElementChild;w.location.hash=hash;await until(()=>$('#content').firstElementChild!==old&&ready());};
 const edit=(input,value)=>{input.value=value;input.dispatchEvent(new w.Event('input',{bubbles:true}));};
 const submit=form=>form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 await until(()=>$('.reading-card'));$('[data-explore-word="chachalaca"]').click();await until(()=>$('#archive-count')?.textContent==='3 resultados');
 const compare=$('#archive-compare');
 // Las fichas y originales viven en Preguntar: el cotejo conserva la consulta y el retorno al pasaje.
 assert.equal(compare.hash,'#preguntar/chachalaca'+suffix);compare.click();await until(()=>$('.ask-result'));
 assert.equal($('#search').value,'chachalaca');assert.equal(d.activeElement,$('[data-reading-return]'));
 const cards=await(await fetch(origin+'/api/ask/cards?q=chachalaca')).json();await until(()=>d.querySelectorAll('[data-card-id]').length===cards.results.length);assert.deepEqual([...d.querySelectorAll('[data-card-id]')].map(x=>x.dataset.cardId),cards.results.map(x=>x.id));
 $('[data-reading-return]').click();await until(()=>d.activeElement?.dataset.archiveId==='axolotl-14546');assert.equal(scrolls.at(-1),'axolotl-14546');
 await navigate('#lexico/buscar/atl'+suffix,()=>$('#dictionary-grid .dictionary-card'));edit($('#search'),'cuicatl');assert.equal($('#dictionary-compare').hash,'#preguntar/cuicatl'+suffix);$('#dictionary-compare').click();await until(()=>$('#ask-cards .documentary-hit'));
 const word=$('#ask-cards .documentary-hit a[href^="#lexico/"]');assert(word);assert(word.hash.endsWith(suffix));word.click();await until(()=>$('.dictionary-entry'));assert($('[data-reading-return]'));
 const guide='?from=aprender&lesson=aves&passage=axolotl-08856';await navigate('#preguntar/atl'+guide,()=>$('#ask-cards .documentary-hit'));$('[data-reading-return]').click();await until(()=>d.activeElement?.dataset.archiveId==='axolotl-08856');assert.equal($('[data-step="2"]').getAttribute('aria-current'),'step');assert.equal($('.reading-translation').hidden,true);assert.equal($('.exercise-feedback').textContent,'');assert.equal($('.comprehension-feedback').textContent,'');
 for(const invalid of ['from=leer&lesson=flor&passage=axolotl-14546','from=https%3A%2F%2Fevil.invalid&lesson=aves&passage=axolotl-14546','from=leer&lesson=aves&passage=%ZZ','from=leer&lesson=aves&passage=axolotl-14546&extra=x','from=leer&lesson=aves&passage=axolotl-14546&passage=axolotl-14546']){await navigate('#preguntar/atl?'+invalid,()=>$('#ask-cards .documentary-hit'));assert.equal($('[data-reading-return]'),null);assert(!$('#ask-cards .documentary-hit a[href^="#lexico/"]').hash.includes('?'));}
 await navigate('#consultar/atl'+suffix,()=>$('#ask-cards .documentary-hit'));assert.equal(w.location.hash,'#preguntar/atl'+suffix);assert($('[data-reading-return]'));// enlace antiguo
 assert.equal(w.localStorage.getItem('scriptorium-study-v1'),initialRaw);assert.deepEqual(writes,[]);assert(requests.every(r=>r.method==='GET'));assert(!requests.some(r=>/proposals|bootstrap|community|voice|training-pairs/.test(r.url)));assert.deepEqual(errors,[]);
 console.log(`PASS DOM ${width}: fichas en Preguntar desde Archivo y Diccionario, IDs iguales al endpoint, retorno exacto lector/guiado y foco; enlace antiguo a Consultar; orígenes inválidos; cero escrituras. No mide geometría.`);dom.window.close();
}})().catch(e=>{console.error(e);process.exit(1);});
