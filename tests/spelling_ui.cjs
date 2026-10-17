// Grafías: sugerencias mientras se escribe en la búsqueda global y vista «Grafías» de una palabra.
const assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const origin=process.env.CORPUS_QA_ORIGIN,errors=[];
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label='UI'){for(let i=0;i<800;i++){if(fn())return;await pause(25);}throw Error(label+' timeout');}
(async()=>{
 const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
 const dom=await JSDOM.fromURL(origin+'/#lexico',{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
  w.fetch=(url,options={})=>fetch(new URL(url,origin),options);
  w.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});w.Element.prototype.scrollIntoView=function(){};
 }});
 const w=dom.window,d=w.document,$=s=>d.querySelector(s);
 await until(()=>$('#spelling-suggest')&&$('#content').textContent.length>50,'carga');
 // Escribir una grafía moderna no atestiguada: la sugerencia lleva a la palabra con sus fuentes, sin presentarla como atestiguada.
 const input=$('#search');input.value='kuautli';input.dispatchEvent(new w.Event('input'));
 await until(()=>!$('#spelling-suggest').hidden&&$('.spelling-option'),'sugerencias');
 assert.match($('.spelling-note').textContent,/no aparece tal cual/);
 const first=$('.spelling-option');
 assert.match(first.textContent,/cuauhtli/);assert.match(first.textContent,/confianza alta/);assert.match(first.textContent,/apariciones/);
 // Las cuatro grafías de cualli llevan a cualli.
 for(const q of ['kuali','kualli','qualli','cuali']){
  input.value=q;input.dispatchEvent(new w.Event('input'));
  await until(()=>$('.spelling-option .spelling-lemma')?.textContent==='cualli'&&$('#spelling-suggest ul')?.getAttribute('aria-label')?.includes(q),'sugerencia '+q);
 }
 // Teclado: flecha y Enter abren la vista Grafías.
 input.dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}));
 input.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
 await until(()=>$('.spelling-profiles'),'vista Grafías');
 assert.match(w.location.hash,/^#grafias\//);
 assert.match($('h1').textContent,/cualli/);
 const profiles=[...d.querySelectorAll('.spelling-profiles tbody tr')].map(r=>r.textContent);
 assert(profiles.some(t=>/SEP/.test(t)&&/kwalli/.test(t)),'perfil SEP');
 assert(profiles.some(t=>/Sierra de Puebla/.test(t)&&/kuali/.test(t)),'rasgos de la Sierra de Puebla');
 assert.match($('.spelling-limit').textContent,/vocales largas/);
 const forms=[...d.querySelectorAll('.spelling-table tbody tr td:first-child strong')].map(x=>x.textContent);
 for(const f of ['cualli','kuali','cuali','qualli'])assert(forms.includes(f),'grafía '+f);
 assert(!forms.includes('calli'),'calli no es otra grafía de cualli');
 // El conversor muestra otra forma en cada perfil.
 $('#spelling-convert-input').value='kwawtli';$('#spelling-convert').dispatchEvent(new w.Event('submit',{cancelable:true}));
 await until(()=>$('#spelling-convert-out table'),'conversor');
 assert.match($('#spelling-convert-out').textContent,/quauhtli/);
 // Sin modo editor no hay botones de revisión; con él, sí (la decisión exige sesión en el servidor).
 assert.equal(d.querySelectorAll('.spelling-review').length,0);
 w.location.hash='#grafias/lemma-metztli';
 await until(()=>$('h1')?.textContent==='metztli'&&$('.spelling-edges'),'metztli');
 $('#spelling-editor').checked=true;$('#spelling-editor').dispatchEvent(new w.Event('change'));
 await until(()=>d.querySelectorAll('.spelling-review button').length>0,'botones de revisión');
 assert.deepEqual(errors,[]);
 console.log('PASS grafías: sugerencias, teclado, perfiles, grafías por variedad, conversor, revisión');
 w.close();
})().catch(e=>{console.error(e);process.exit(1);});
