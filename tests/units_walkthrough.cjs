// Recorrido completo de una unidad: portada de Lecturas → Unidades → regla → nueve ejercicios → lectura de cierre,
// progreso guardado sin tocar el de las lecturas, y repaso de Mis palabras con un ejemplo de concordancia.
const assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const origin=process.env.CORPUS_QA_ORIGIN,errors=[];
const initial={version:1,saved:['sense-calli'],lessons:{aves:{edition:'lectura-clasica-v1:1',passed:[0],comprehension:[],step:1}},reviews:{'sense-calli':{streak:1,due:0}},contexts:{}};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label='UI'){for(let i=0;i<400;i++){if(fn())return;await pause(25);}throw Error(label+' timeout');}
async function open(hash,storage){
 const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
 const dom=await JSDOM.fromURL(origin+'/'+hash,{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
  w.localStorage.setItem('scriptorium-study-v1',storage);
  w.fetch=(url,options={})=>fetch(new URL(url,origin),options);
  w.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});w.Element.prototype.scrollIntoView=function(){};
  w.URL.createObjectURL=()=>'blob:test';w.URL.revokeObjectURL=()=>{};
 }});
 return dom;
}
(async()=>{
 const data=await(await fetch(origin+'/api/units')).json();
 assert(data.units.length>=3,'al menos tres unidades servidas');
 let dom=await open('#aprender',JSON.stringify(initial)),w=dom.window,d=w.document,$=s=>d.querySelector(s);
 // Portada: las unidades aparecen como borradores automáticos.
 await until(()=>$('#units-teaser')&&!$('#units-teaser').hidden,'portada');
 assert.equal(d.querySelectorAll('.unit-chip').length,data.units.length);
 assert.match($('#units-teaser').textContent,/borradores automáticos sin revisar/);
 // Índice de unidades: ninguna se presenta como revisada.
 w.location.hash='#unidades';await until(()=>d.querySelectorAll('.unit-card').length===data.units.length,'índice');
 assert.equal(d.querySelectorAll('.unit-card .unit-review.automatic').length,data.units.length);assert.equal(d.querySelectorAll('.proposed-reading .unit-review.automatic').length,data.proposed_readings.length);
 assert.equal(d.querySelectorAll('.unit-review.reviewed').length,0);
 assert(d.querySelectorAll('.proposed-reading').length>=6,'lecturas propuestas en revisión');
 const unit=data.units.find(u=>u.id==='posesivos')||data.units[0];
 w.location.hash='#unidades/'+unit.id;await until(()=>$('#unit-start'),'regla');
 assert.match($('.unit-rule').textContent,/pendientes de revisión/);
 $('#unit-start').click();
 const kinds=new Set();let triedWrong=false;
 for(const [i,e] of unit.exercises.entries()){
  await until(()=>$('.unit-exercise')?.dataset.exercise===e.id,'ejercicio '+e.id);
  kinds.add(e.kind);
  assert($('.automatic-tag'),'cada ejercicio se marca como automático');
  assert.equal($('#unit-next').disabled,true);
  const feedback=()=>$('.exercise-feedback').textContent;
  if(['identify','cloze','translate'].includes(e.kind)){
   if(!triedWrong){d.querySelector(`[data-choice="${(e.answer+1)%3}"]`).click();assert.doesNotMatch(feedback(),/^Correcto/);assert.equal($('#unit-next').disabled,true);triedWrong=true;}
   d.querySelector(`[data-choice="${e.answer}"]`).click();
   if(e.kind==='cloze')assert($('.unit-blank'));
  }else if(e.kind==='build'){
   for(const t of e.answer){d.querySelector(`[data-tile="${t}"]`).click();}
   $('#unit-check').click();
  }else if(e.kind==='match'){
   for(const [p] of e.pairs.entries()){d.querySelector(`[data-form="${p}"]`).click();d.querySelector(`[data-gloss="${p}"]`).click();}
  }
  assert.match(feedback(),/^Correcto/,e.id);
  assert.equal($('#unit-next').disabled,false);
  $('#unit-next').click();
 }
 assert.deepEqual([...kinds].sort(),['build','cloze','identify','match','translate']);
 // Lectura breve real al cierre.
 await until(()=>$('.unit-closing'),'cierre');
 const passage=unit.passages[unit.closing.archive_id];
 assert.equal($('.unit-closing blockquote p[lang="nci"]').textContent,passage.nah);
 assert.equal($('.unit-translation').hidden,true);$('#unit-translation').click();assert.equal($('.unit-translation').hidden,false);
 $('#unit-finish').click();assert.equal($('#unit-finish').textContent,'Unidad completada ✓');
 const stored=JSON.parse(w.localStorage.getItem('scriptorium-study-v1'));
 assert.deepEqual(stored.lessons['unidad:'+unit.id],{edition:data.id+':'+unit.practice_version,passed:unit.exercises.map((_,i)=>i),step:unit.exercises.length,done:true});
 assert.deepEqual(stored.lessons.aves,initial.lessons.aves,'el progreso de las lecturas se conserva');
 assert.deepEqual(stored.saved,initial.saved);assert.deepEqual(stored.reviews,initial.reviews);
 dom.window.close();
 // Al volver, la unidad figura completada; Mis palabras repasa con un pasaje real.
 dom=await open('#unidades',JSON.stringify(stored));w=dom.window;d=w.document;
 await until(()=>d.querySelector(`[data-unit="${unit.id}"]`),'índice tras recargar');
 assert.match(d.querySelector(`[data-unit="${unit.id}"]`).textContent,/Completada ✓/);
 w.location.hash='#palabras';await until(()=>d.querySelector('#start-review'),'cuaderno');
 d.querySelector('#start-review').click();
 await until(()=>d.querySelector('.concordance-example mark'),'concordancia');
 const examples=(await(await fetch(origin+'/api/units/examples?sense=sense-calli')).json()).examples;
 const shown=examples[1%examples.length];
 assert.equal(d.querySelector('.concordance-example mark').textContent,shown.form);
 assert.match(d.querySelector('.concordance-example').textContent,/ejemplo automático/);
 d.querySelector('#show-word').click();
 assert(d.querySelector('.concordance-answer').textContent.includes(shown.segmentation));
 assert.deepEqual(errors,[]);
 console.log(`Unidad «${unit.title}»: ${unit.exercises.length} ejercicios (${[...kinds].join(', ')}) + lectura de cierre; progreso guardado como ${data.id}:${unit.practice_version}; lecturas intactas; repaso con «${shown.form}».`);
 dom.window.close();
})().catch(e=>{console.error(e);process.exit(1);});
