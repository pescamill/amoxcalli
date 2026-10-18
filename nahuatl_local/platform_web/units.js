'use strict';
// Unidades de gramática: borradores generados desde el archivo, el analizador y el índice de términos.
// El progreso vive en el mismo cuaderno local (study.lessons['unidad:ID']) con la edición de práctica de cada unidad:
// si la unidad cambia de practice_version, su progreso empieza de nuevo y el de las lecturas no se toca.

const unitKinds={match:'Emparejar',identify:'Identificar el morfema',build:'Armar la palabra',cloze:'Completar',translate:'Elegir la traducción'};
async function loadUnits(){if(!state.units)state.units=await api('/api/units');return state.units;}
function unitReviewHTML(review){
 return review?.status==='reviewed'
  ?`<span class="unit-review reviewed">Revisada por ${esc(review.reviewer)} · ${esc(review.date)}</span>`
  :`<span class="unit-review automatic" title="Generada automáticamente; ninguna persona la ha revisado todavía.">Borrador automático · sin revisar</span>`;
}
function unitKey(unit){return 'unidad:'+unit.id;}
function unitProgress(unit){
 const edition=(unit.edition_id||state.units.id)+':'+unit.practice_version,old=study.lessons[unitKey(unit)];
 const valid=xs=>Array.isArray(xs)?xs.filter(x=>Number.isInteger(x)&&x>=0&&x<unit.exercises.length):[];
 if(old?.edition===edition)return {edition,passed:valid(old.passed),step:Number.isInteger(old.step)?Math.max(0,Math.min(old.step,unit.exercises.length)):0,done:old.done===true};
 return {edition,passed:[],step:0,done:false};
}
function saveUnitProgress(unit,progress){study.lessons[unitKey(unit)]=progress;writeStudy();}
function unitPassage(unit,id){return unit.passages[id];}
function unitSource(p){return `<p class="meta">${esc(p.document||'Obra no indicada')} · ${esc(p.locator)} · ${esc(p.id)}</p>`;}

async function renderUnits(id){
 let data;
 try{data=await loadUnits();}catch(e){$('content').innerHTML=heading('Unidades','No se pudieron cargar las unidades',e.message);return;}
 if(route().page!=='unidades')return;
 const unit=data.units.find(u=>u.id===id);
 if(unit)return renderUnit(unit);
 $('content').innerHTML=heading('Unidades de gramática','Una regla, palabras conocidas y pasajes reales','Cada unidad toma palabras de las lecturas y una regla del náhuatl clásico. Termina con una lectura breve del archivo.',`${data.units.length} unidades`)
  +`<p class="pilot-note">Estas unidades las propuso un generador automático a partir del archivo, el analizador morfológico y el índice de términos. Cada respuesta se comprueba contra el pasaje y el análisis, pero <strong>ninguna persona las ha revisado todavía</strong> salvo donde se indique.</p>`
  +`<div class="unit-grid">${data.units.map(u=>{const p=unitProgress(u);return `<article class="unit-card" data-unit="${esc(u.id)}"><p class="eyebrow">${esc(u.minutes)} min · ${u.exercises.length} ejercicios</p><h2><a href="#unidades/${esc(u.id)}">${esc(u.title)}</a></h2><p>${esc(u.objective)}</p><p class="unit-words" lang="nci">${u.words.slice(0,4).map(w=>esc(w.segmentation)).join(' · ')}</p>${unitReviewHTML(u.review)}<p class="meta">${p.done?'Completada ✓':p.passed.length?`${p.passed.length} de ${u.exercises.length} ejercicios`:'Sin empezar'}</p></article>`;}).join('')}</div>`
  +(data.proposed_readings.length?`<section class="proposed-readings"><h2>Lecturas propuestas en revisión</h2><p>El generador eligió pasajes breves por cobertura de raíces y redactó sus ayudas. Esperan revisión editorial antes de sumarse a Leer.</p>${data.proposed_readings.map(r=>`<details class="proposed-reading" data-proposed="${esc(r.id)}"><summary>${esc(r.title)} ${unitReviewHTML(r.review)}</summary><p>${esc(r.objective)}</p>${r.passages.map(p=>`<blockquote><p lang="nci">${esc(p.nah)}</p><p>${esc(p.es)}</p>${unitSource(p)}</blockquote>`).join('')}</details>`).join('')}</section>`:'');
}

// En la portada de Lecturas: las unidades como siguiente paso, con su estado de revisión visible.
async function fillUnitsTeaser(slot){
 if(!slot)return;
 let data;try{data=await loadUnits();}catch{return;}
 if(!slot.isConnected||!data.units.length)return;
 slot.innerHTML=`<div class="section-heading"><h2>Unidades de gramática</h2><span class="meta">${data.units.length} unidades · borradores automáticos sin revisar</span></div><p>Una regla por unidad con palabras de las lecturas: emparejar, armar la palabra con sus piezas, completar pasajes reales y una lectura breve al final.</p><div class="unit-grid">${data.units.map(u=>`<a class="unit-chip" href="#unidades/${esc(u.id)}"><strong>${esc(u.title)}</strong><span>${esc(u.minutes)} min${unitProgress(u).done?' · completada ✓':''}</span></a>`).join('')}</div>`;
 slot.hidden=false;
}

// opts.back / backLabel / others: enlaces de vuelta de una unidad servida desde otra sección (Dioses y calendario).
function renderUnit(unit,opts={}){
 const back=opts.back||'#unidades',others=opts.others||'#unidades';
 const progress=unitProgress(unit);
 let step=progress.step,onRule=false;
 const record=()=>{progress.step=step;saveUnitProgress(unit,progress);};
 const frame=body=>`<a class="back-link" href="${back}">${esc(opts.backLabel||'← Todas las unidades')}</a>${heading('Unidad · Náhuatl clásico',unit.title,unit.objective)}${unitReviewHTML(unit.review)}<div class="lesson-progress unit-progress" role="group" aria-label="Pasos de la unidad"><button class="step-button ${onRule?'current':''}" data-unit-step="rule">Regla</button>${unit.exercises.map((e,i)=>`<button class="step-button ${i===step&&!onRule?'current':''}" data-unit-step="${i}" aria-current="${i===step&&!onRule?'step':'false'}">${i+1}${progress.passed.includes(i)?' ✓':''}</button>`).join('')}<button class="step-button ${step===unit.exercises.length&&!onRule?'current':''}" data-unit-step="${unit.exercises.length}">Lectura</button></div>${body}`;
 const bindSteps=()=>document.querySelectorAll('[data-unit-step]').forEach(b=>b.onclick=()=>{if(b.dataset.unitStep==='rule'){showRule();return;}step=Number(b.dataset.unitStep);record();draw();});
 const showRule=()=>{
  onRule=true;
  $('content').innerHTML=frame(`<section class="unit-rule"><p class="eyebrow">La regla</p><p>${esc(unit.rule.summary)}</p><ul>${unit.rule.points.map(p=>`<li>${esc(p)}</li>`).join('')}</ul><table class="unit-morphemes"><thead><tr><th>Morfema</th><th>Glosa del analizador</th></tr></thead><tbody>${unit.rule.morphemes.map(m=>`<tr><td lang="nci">${m.surfaces.map(esc).join(', ')}</td><td>${esc(m.gloss)}</td></tr>`).join('')}</tbody></table><p class="meta">Regla y glosas: plantilla del proyecto y analizador morfológico, pendientes de revisión especializada.</p><button class="primary" id="unit-start">${progress.passed.length?'Seguir practicando':'Empezar los ejercicios'}</button></section>`);
  bindSteps();$('unit-start').onclick=()=>{draw();};
 };
 const next=()=>{step=Math.min(step+1,unit.exercises.length);record();draw();$('content').scrollIntoView({block:'start'});};
 const pass=(i,feedback,text)=>{if(!progress.passed.includes(i))progress.passed.push(i);record();feedback.textContent='Correcto. '+text;feedback.className='exercise-feedback correct';$('unit-next').disabled=false;
  const b=document.querySelector(`[data-unit-step="${i}"]`);if(b&&!b.textContent.includes('✓'))b.textContent+=' ✓';};
 const draw=()=>{
  onRule=false;
  if(step>=unit.exercises.length)return drawClosing();
  const e=unit.exercises[step],done=progress.passed.includes(step);
  $('content').innerHTML=frame(`<section class="exercise-card unit-exercise" data-kind="${esc(e.kind)}" data-exercise="${esc(e.id)}"><p class="eyebrow">${esc(unitKinds[e.kind])} · ${step+1} de ${unit.exercises.length} <span class="automatic-tag">Automático</span></p><h2>${esc(e.prompt)}</h2><div class="unit-body"></div><p class="exercise-feedback" role="status"></p><details class="unit-evidence"><summary>De dónde sale la respuesta</summary>${e.evidence.map(ev=>{if(ev.source==='tlachia')return `<p><span lang="nci">${esc(ev.form)}</span> = ${esc(ev.segmentation)} (${esc(ev.support)}) · Tlachia, Telleriano-Remensis f. ${esc(ev.folio)}</p>`;const p=unitPassage(unit,ev.archive_id);return `<p><span lang="nci">${esc(ev.form)}</span> = ${esc(ev.segmentation)} · la traducción dice «${esc(ev.support)}»${p?' · '+esc(p.document||''):''} · ${esc(ev.archive_id)}</p>`;}).join('')}<p class="meta">Comprobado automáticamente contra el pasaje y el análisis actual. No es una revisión humana.</p></details><div class="entry-actions"><button class="primary" id="unit-next" ${done?'':'disabled'}>${step===unit.exercises.length-1?'Ir a la lectura':'Siguiente'}</button></div></section>`);
  bindSteps();$('unit-next').onclick=next;
  const body=$('content').querySelector('.unit-body'),feedback=$('content').querySelector('.exercise-feedback');
  if(done){feedback.textContent='Ya resuelto. '+e.explanation;feedback.className='exercise-feedback correct';}
  const choose=(options,answer,render=o=>esc(o))=>{
   body.innerHTML=`<div class="answer-options">${options.map((o,i)=>`<button class="answer-option" data-choice="${i}" ${done?'disabled':''}>${render(o)}</button>`).join('')}</div>`;
   body.querySelectorAll('[data-choice]').forEach(b=>b.onclick=()=>{const ok=Number(b.dataset.choice)===answer;b.classList.add(ok?'correct':'incorrect');
    if(ok){body.querySelectorAll('[data-choice]').forEach(x=>x.disabled=true);pass(step,feedback,e.explanation);}else{feedback.textContent='Todavía no. Mira de nuevo las piezas de la palabra.';feedback.className='exercise-feedback';}});
  };
  if(e.kind==='identify'){choose(e.options,e.answer);body.insertAdjacentHTML('afterbegin',`<p class="unit-form" lang="nci">${esc(e.form)}</p>`);}
  else if(e.kind==='cloze'){
   const p=unitPassage(unit,e.archive_id),i=p.nah.search(new RegExp('(?<![\\p{L}\\p{M}\\p{N}_])'+e.blank.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'(?![\\p{L}\\p{M}\\p{N}_])','u'));
   choose(e.options,e.answer);
   body.insertAdjacentHTML('afterbegin',`<blockquote class="unit-passage"><p lang="nci">${esc(p.nah.slice(0,i))}<span class="unit-blank">_____</span>${esc(p.nah.slice(i+e.blank.length))}</p><p>${esc(p.es)}</p>${unitSource(p)}</blockquote>`);
  }else if(e.kind==='translate'){
   const p=unitPassage(unit,e.archive_id);
   choose(e.option_ids,e.answer,id=>esc(unitPassage(unit,id).es));
   body.insertAdjacentHTML('afterbegin',`<blockquote class="unit-passage"><p lang="nci">${esc(p.nah)}</p>${unitSource(p)}</blockquote>`);
  }else if(e.kind==='build'){
   let built=done,picked=built?[...e.answer]:[];
   const drawBuild=()=>{
    body.innerHTML=`<p class="unit-built" lang="nci" aria-live="polite">${picked.map(i=>`<span class="tile placed">${esc(e.tiles[i])}</span>`).join('')||'<span class="meta">Toca las fichas en orden</span>'}</p><div class="unit-tiles">${e.tiles.map((t,i)=>`<button class="tile" data-tile="${i}" ${picked.includes(i)||built?'disabled':''} lang="nci">${esc(t)}</button>`).join('')}</div><div class="entry-actions"><button class="secondary" id="unit-clear" ${built?'disabled':''}>Borrar</button><button class="primary" id="unit-check" ${built||!picked.length?'disabled':''}>Comprobar</button></div>`;
    body.querySelectorAll('[data-tile]').forEach(b=>b.onclick=()=>{picked.push(Number(b.dataset.tile));drawBuild();});
    $('unit-clear').onclick=()=>{picked=[];drawBuild();};
    $('unit-check').onclick=()=>{
     if(picked.length===e.answer.length&&picked.every((x,i)=>e.tiles[x]===e.tiles[e.answer[i]])){built=true;drawBuild();pass(step,feedback,e.explanation);}
     else{feedback.textContent='Todavía no. Piensa en el orden: prefijos, raíz y sufijos.';feedback.className='exercise-feedback';}
    };
   };
   drawBuild();
  }else if(e.kind==='match'){
   const glosses=[...e.pairs.keys()].sort((a,b)=>e.pairs[a].gloss.localeCompare(e.pairs[b].gloss,'es'));
   let selected=null;const matched=new Set(done?e.pairs.map((_,i)=>i):[]);
   const drawMatch=()=>{
    body.innerHTML=`<div class="unit-match"><div>${e.pairs.map((p,i)=>`<button class="tile ${selected===i?'selected':''} ${matched.has(i)?'matched':''}" data-form="${i}" ${matched.has(i)?'disabled':''} lang="nci">${esc(p.form)}</button>`).join('')}</div><div>${glosses.map(i=>`<button class="tile ${matched.has(i)?'matched':''}" data-gloss="${i}" ${matched.has(i)?'disabled':''}>${esc(e.pairs[i].gloss)}</button>`).join('')}</div></div>`;
    body.querySelectorAll('[data-form]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.form);drawMatch();});
    body.querySelectorAll('[data-gloss]').forEach(b=>b.onclick=()=>{
     if(selected===null){feedback.textContent='Elige primero una forma.';return;}
     if(Number(b.dataset.gloss)===selected){matched.add(selected);selected=null;feedback.textContent='';drawMatch();if(matched.size===e.pairs.length)pass(step,feedback,e.explanation);}
     else{feedback.textContent='Esa glosa no corresponde. Compara las piezas de la palabra.';feedback.className='exercise-feedback';selected=null;drawMatch();}
    });
   };
   drawMatch();
  }
 };
 const drawClosing=()=>{
  const c=unit.closing,p=unitPassage(unit,c.archive_id);
  $('content').innerHTML=frame(`<section class="unit-closing"><p class="eyebrow">Lectura breve · un pasaje real del archivo</p><blockquote class="unit-passage"><p lang="nci">${esc(p.nah)}</p><button class="link-button" id="unit-translation" aria-expanded="false">Mostrar traducción</button><p class="unit-translation" hidden>${esc(p.es)}</p>${unitSource(p)}</blockquote><h3>Palabras de esta unidad en el pasaje</h3><ul class="unit-closing-forms">${c.forms.map(f=>`<li><span lang="nci">${esc(f.form)}</span> · ${esc(f.segmentation)} · ${esc(f.gloss)}</li>`).join('')}</ul><p class="meta">Glosas por partes del analizador, no traducciones. ${esc(p.verification)}.</p><div class="entry-actions"><button class="primary" id="unit-finish">${progress.done?'Unidad completada ✓':'Terminar la unidad'}</button><a class="secondary" href="${others}">Otras unidades</a><a class="secondary" href="#palabras">Repasar mis palabras</a></div></section>`);
  bindSteps();
  $('unit-translation').onclick=()=>{const t=$('content').querySelector('.unit-translation');t.hidden=!t.hidden;$('unit-translation').textContent=t.hidden?'Mostrar traducción':'Ocultar traducción';$('unit-translation').setAttribute('aria-expanded',String(!t.hidden));};
  $('unit-finish').onclick=()=>{
   const missing=unit.exercises.findIndex((_,i)=>!progress.passed.includes(i));
   if(missing>=0){step=missing;record();draw();toast('Falta el ejercicio '+(missing+1)+'.');return;}
   progress.done=true;record();$('unit-finish').textContent='Unidad completada ✓';
  };
 };
 if(!progress.passed.length&&step===0)showRule();else draw();
}

// Repaso de Mis palabras con concordancia: la palabra aparece flexionada en un pasaje real, no suelta.
// El ejemplo rota con la racha de repasos, así cada vuelta muestra otra forma de la misma raíz.
const unitExamples=new Map();
async function concordanceExamples(senseId){
 if(!unitExamples.has(senseId))unitExamples.set(senseId,api('/api/units/examples?'+new URLSearchParams({sense:senseId})).catch(()=>({examples:[]})));
 return unitExamples.get(senseId);
}
function concordanceExampleHTML(example){
 const i=example.nah.indexOf(example.form);
 const nah=i<0?esc(example.nah):`${esc(example.nah.slice(0,i))}<mark>${esc(example.form)}</mark>${esc(example.nah.slice(i+example.form.length))}`;
 return `<div class="concordance-example" data-concordance="${esc(example.archive_id)}"><p class="eyebrow">En un pasaje real · ejemplo automático</p><blockquote lang="nci">${nah}</blockquote><p>¿Qué significa <strong lang="nci">${esc(example.form)}</strong> aquí?</p></div>`;
}
function concordanceAnswerHTML(example){
 return `<div class="concordance-answer"><p><span lang="nci">${esc(example.segmentation)}</span> · ${esc(example.gloss)}</p><p class="review-translation">${esc(example.es)}</p><p class="meta">${esc(example.document||'')} · ${esc(example.locator)} · glosa por partes del analizador, pendiente de revisión</p></div>`;
}
