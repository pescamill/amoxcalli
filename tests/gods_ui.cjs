// Dioses y calendario: índice de fichas, ficha de deidad con fuentes, búsqueda por grafía variante desde Preguntar,
// calendario navegable (trecena → día → día siguiente), veintena sin fuente para el nombre, lecturas y unidad como borradores.
const assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const origin=process.env.CORPUS_QA_ORIGIN,errors=[];
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label='UI'){for(let i=0;i<800;i++){if(fn())return;await pause(25);}throw Error(label+' timeout');}
async function open(hash,width=1200){
 const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
 return JSDOM.fromURL(origin+'/'+hash,{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
  w.fetch=(url,options={})=>fetch(new URL(url,origin),options);Object.defineProperty(w,'innerWidth',{value:width});
  w.matchMedia=()=>({matches:width<700,addEventListener(){},removeEventListener(){}});w.Element.prototype.scrollIntoView=function(){};
  w.URL.createObjectURL=()=>'blob:test';w.URL.revokeObjectURL=()=>{};
 }});
}
(async()=>{
 const catalog=await(await fetch(origin+'/api/entities')).json();
 assert(catalog.entities.filter(e=>e.kind==='deity').length>=12);
 let dom=await open('#dioses'),w=dom.window,d=w.document,$=s=>d.querySelector(s),all=s=>[...d.querySelectorAll(s)];
 await until(()=>$('[data-entity="huitzilopochtli"]'),'índice');
 assert.equal(all('.gods-card').length,catalog.entities.length);
 assert.match($('.pilot-note').textContent,/sin revisar/);
 // Ficha: atributos con fuente, grafías, enlaces al índice de términos, Preguntar y Tlachia.
 w.location.hash='#dioses/quetzalcoatl';await until(()=>$('.gods-attributes'),'ficha');
 assert(all('.gods-attributes > li').every(li=>li.querySelector('.gods-sources')||li.closest('section')),'cada atributo con fuentes');
 assert(all('.gods-source').length>=3);
 assert.match($('.term-spellings').textContent,/quetzalcohuatl/);
 assert($('a[href="#lexico/buscar/Quetzalcoatl"]')&&$('a[href="#preguntar/Quetzalcoatl"]'));
 assert($('a[href^="#glifos/ficha/telleriano"]'),'enlace al folio de Tlachia');
 assert($('a[href="#dioses/calendario/trecena-18"]'),'trecena de su lámina');
 // Preguntar con una grafía variante lleva a la misma ficha.
 w.location.hash='#preguntar/Uitzilopochtli';await until(()=>$('.entity-banner a'),'aviso en Preguntar');
 assert.equal($('.entity-banner a').getAttribute('href'),'#dioses/huitzilopochtli');
 // Calendario: trecena, día, día siguiente; la trecena 19 muestra a Xochiquetzal (f. 25v).
 w.location.hash='#dioses/calendario/trecena-19';await until(()=>all('.gods-days li').length===13,'trecena');
 assert.match($('#gods-trecena').textContent,/Xochiqu/);
 $('.gods-days li a').click();await until(()=>$('.gods-pager')&&/día \d+ de 260/.test($('.intro').textContent),'día');
 assert.match(d.querySelector('h1').textContent,/ce cuauhtli/);
 assert($('.gods-glyphs img'),'glifo del día desde Tlachia');
 all('.gods-pager a')[1].click();await until(()=>/ome cozcacuauhtli/.test(d.querySelector('h1').textContent),'día siguiente');
 // Veintena sin fuente para el nombre: lo dice.
 w.location.hash='#dioses/veintena-teotleco';await until(()=>$('.pilot-note')&&/pendiente de fuente/.test(d.body.textContent),'teotleco');
 w.location.hash='#dioses/veintenas';await until(()=>all('[data-veintena]').length===19,'veintenas');
 // Lecturas y unidad: borradores en la cola.
 w.location.hash='#dioses/lecturas';await until(()=>all('.proposed-reading').length>=3,'lecturas');
 assert.equal(all('.unit-review.reviewed').length,0);
 w.location.hash='#dioses/unidad';await until(()=>$('#unit-start'),'unidad');
 assert.equal($('.back-link').getAttribute('href'),'#dioses/lecturas');
 $('#unit-start').click();await until(()=>$('.unit-exercise'),'ejercicio');
 assert($('.automatic-tag'));
 dom.window.close();
 // Teléfono: el calendario se lee en una columna (sin tablas de 20 columnas).
 dom=await open('#dioses/calendario',375);w=dom.window;d=w.document;
 await until(()=>d.querySelectorAll('.gods-days li').length===13,'teléfono');
 assert(!d.querySelector('table.gods-grid-20'),'sin rejilla de 260 casillas');
 assert.deepEqual(errors,[]);
 console.log(`Dioses y calendario: ${catalog.entities.length} fichas, Preguntar «Uitzilopochtli» → huitzilopochtli, trecena 19 → ce cuauhtli → ome cozcacuauhtli, ${catalog.readings.length} lecturas y la unidad como borradores.`);
 dom.window.close();
})().catch(e=>{console.error(e);process.exit(1);});
