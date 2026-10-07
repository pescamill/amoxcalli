'use strict';

const glyphTypes={element:'Elemento de un compuesto',simplex:'Glifo simple',compound:'Glifo compuesto',iconography:'Imagen iconográfica',unspecified:'Referencia de catálogo'};
let studyStorageAvailable=true;
function readStudy(){
 try{
  const value=JSON.parse(localStorage.getItem('scriptorium-study-v1')||'null');
  if(value?.version===1)return {version:1,saved:Array.isArray(value.saved)?value.saved.filter(x=>typeof x==='string'):[],lessons:value.lessons&&typeof value.lessons==='object'?value.lessons:{},reviews:value.reviews&&typeof value.reviews==='object'?value.reviews:{}};
 }catch{/* Un almacenamiento vacío o corrupto no impide estudiar. */}
 return {version:1,saved:[],lessons:{},reviews:{}};
}
const study=readStudy();
function writeStudy(){try{localStorage.setItem('scriptorium-study-v1',JSON.stringify(study));return true;}catch{studyStorageAvailable=false;toast('Tu navegador no permite guardar el progreso. Puedes seguir estudiando durante esta sesión.');return false;}}
function isSaved(id){return study.saved.includes(id);}
function toggleSaved(id){
 if(!state.byId[id]||state.byId[id].kind!=='sense')return;
 study.saved=isSaved(id)?study.saved.filter(x=>x!==id):[...study.saved,id];writeStudy();
 document.querySelectorAll('[data-save-word]').forEach(b=>{b.textContent=isSaved(b.dataset.saveWord)?'Guardada ✓':'Guardar palabra';b.setAttribute('aria-pressed',String(isSaved(b.dataset.saveWord)));});
}
function bindSaved(container){container.querySelectorAll('[data-save-word]').forEach(b=>b.onclick=()=>toggleSaved(b.dataset.saveWord));appendSourceCredits();}
function appendSourceCredits(){
 $('content').querySelector('.source-credit-summary')?.remove();
 const visible=new Set(Array.from($('content').querySelectorAll('img[data-source-image]')).map(i=>i.getAttribute('src'))),groups=new Map();
 for(const g of state.records.filter(r=>r.kind==='glyph'&&visible.has(r.image))){const key=g.image_credit||'Consultar derechos en la ficha de la fuente.';if(!groups.has(key))groups.set(key,[]);if(!groups.get(key).some(r=>r.url===g.url))groups.get(key).push(g);}
 if(!groups.size)return;
 const details=document.createElement('details');details.className='source-credit-summary';details.innerHTML='<summary>Créditos y procedencia de las imágenes</summary>'+Array.from(groups,([credit,rows])=>`<p>${esc(credit)}<br>${rows.map(g=>link(g.url,g.reading)).join(' · ')}</p>`).join('');$('content').append(details);
}
function saveWordButton(id){return `<button class="secondary" data-save-word="${esc(id)}" aria-pressed="${isSaved(id)}">${isSaved(id)?'Guardada ✓':'Guardar palabra'}</button>`;}
let dictionaryIndex;
function dictionaryRecords(kind,id){
 if(dictionaryIndex?.records!==state.records){
  dictionaryIndex={records:state.records,form:new Map(),glyph:new Map()};
  for(const r of state.records){if(!dictionaryIndex[r.kind]||!r.sense_id)continue;const rows=dictionaryIndex[r.kind].get(r.sense_id)||[];rows.push(r);dictionaryIndex[r.kind].set(r.sense_id,rows);}
 }
 return dictionaryIndex[kind].get(id)||[];
}
function formsFor(id){return dictionaryRecords('form',id);}
function glyphsFor(id){return dictionaryRecords('glyph',id);}
function representativeGlyph(id){const rows=glyphsFor(id);return rows.find(g=>g.image)||rows[0];}
function headword(id){const rows=formsFor(id);return rows.find(f=>f.id.startsWith('lex-'))?.written||rows[0]?.written||'';}
const associationNames={related_meaning:'Relación de significado',definition_reference:'Referencia de la definición',passage_reference:'Referencia del ejemplo'};
function associationHTML(g){
 const a=g.association;if(!a)return '';
 const p=a.passage;
 return `<div class="association-note"><p><strong>${esc(associationNames[a.type])} · ${esc(g.reading)}</strong></p><p>${esc(a.note)}</p>${a.definition_quote?`<blockquote>${esc(a.definition_quote)}</blockquote>`:''}${p?`<blockquote><p lang="nci">${esc(p.nah)}</p><p>${esc(p.es)}</p><small>${esc(p.document)} · Axolotl, registro ${esc(p.line)}</small></blockquote>`:''}${link(a.evidence_url,'Ver evidencia de la relación')}</div>`;
}
function sourceImage(g,css=''){
 if(!g?.image)return '';
 try{const u=new URL(g.image);if(!['http:','https:'].includes(u.protocol))return '';}catch{return '';}
 const img=`<img src="${esc(g.image)}" alt="${esc(associationNames[g.association?.type]||glyphTypes[g.glyph_type]||'Referencia glífica')}: ${esc(g.reading)}" loading="lazy" decoding="async" data-source-image>`;
 let clickable=img;try{const u=new URL(g.url);if(['http:','https:'].includes(u.protocol))clickable=`<a href="${esc(g.url)}" target="_blank" rel="noopener noreferrer" aria-label="Abrir ficha de la fuente: ${esc(g.reading)}">${img}</a>`;}catch{}
 return `<figure class="source-image ${esc(css)}">${clickable}<p class="image-fallback meta" hidden>La imagen no está disponible. ${link(g.url,'Abrir ficha de la fuente')}</p></figure>`;
}
document.addEventListener('error',e=>{if(e.target.matches?.('img[data-source-image]')){e.target.hidden=true;const fallback=e.target.closest('figure')?.querySelector('.image-fallback');if(fallback)fallback.hidden=false;}},true);
function glyphContext(g){
 const source=state.byId[g.evidence?.[0]?.source_id];
 return `${associationHTML(g)}<p class="eyebrow">${esc(glyphTypes[g.glyph_type]||'Referencia glífica')}</p>${g.context===g.association?.note?'':`<p>${esc(g.context)}</p>`}<p class="meta">${esc(source?.label||'Fuente por consultar')} · ${esc(g.evidence?.[0]?.locator)}</p><div class="card-actions">${link(g.url,'Ficha del catálogo')}${g.manuscript_url?link(g.manuscript_url,'Abrir el folio'):''}</div><p class="image-credit">${esc(g.image_credit||'Imagen no incorporada en esta ficha.')}</p>`;
}
function wordHelpHTML(annotation){
 const sense=state.byId[annotation.sense_id],g=annotation.glyph_id?state.byId[annotation.glyph_id]:representativeGlyph(annotation.sense_id);
 const relations={full_word:'Palabra completa',observed_form:'Forma del pasaje · análisis pendiente',source_variant:'Grafía de la fuente · relación pendiente de cotejo',thematic:'Comparación temática'};
 return `<div class="word-help"><div>${g?sourceImage(g,'help-image'):''}</div><div><p class="eyebrow">Ayuda de lectura${annotation.relation?' · '+esc(relations[annotation.relation]):''}</p><h3 lang="nci">${esc(annotation.quote)}</h3><p class="lookup-reference">Entrada de consulta: <a href="#lexico/${esc(annotation.sense_id)}"><span lang="nci">${esc(headword(annotation.sense_id))}</span> · ${esc(sense?.label)}</a></p><p>${esc(annotation.note)}</p><p class="meta">${g?esc(state.byId[g.evidence?.[0]?.source_id]?.label)+' · '+esc(g.evidence?.[0]?.locator):'Sin referencia glífica específica incorporada.'}</p>${g?'<p class="meta">La referencia visual y este pasaje pertenecen a documentos distintos. Consulta el alcance de la relación.</p>'+associationHTML(g):''}<div class="entry-actions">${saveWordButton(annotation.sense_id)}<a class="secondary" href="#lexico/${esc(annotation.sense_id)}">Ver palabra y fuentes</a></div></div></div>`;
}
function annotatedPassage(example,cloze=false){
 const r=example.passage;let end=0,html='';
 for(const [i,a] of example.annotations.entries()){
  html+=esc(r.nah.slice(end,a.start));
  const text=cloze&&a.quote===example.exercise.blank?'_____':a.quote;
  html+=`<button class="annotated-word" data-annotation="${i}" aria-label="Consultar ${esc(a.quote)}">${esc(text)}</button>`;end=a.end;
 }
 html+=esc(r.nah.slice(end));
 if(cloze&&!example.annotations.some(a=>a.quote===example.exercise.blank))html=html.replace(esc(example.exercise.blank),'_____');
 return html;
}
function passageSource(example){const r=example.passage;return `<details class="reading-source"><summary>Fuente, contexto y estado de revisión</summary><p><strong>${esc(r.document)}</strong> · ${esc(r.variant_label)}</p><p>${esc(example.context)}</p><p class="meta">${esc(r.locator)} · ${esc(r.id)}</p><p class="meta">${esc(r.verification)}. Las ayudas de lectura son un borrador editorial.</p>${link(r.source_url,'Distribución del corpus')}<p class="meta">${esc(r.rights_note)}</p></details>`;}
function bindReading(container,example){
 container.querySelectorAll('[data-annotation]').forEach(b=>b.onclick=()=>{container.querySelectorAll('[data-annotation]').forEach(x=>x.setAttribute('aria-expanded',String(x===b)));const help=container.querySelector('.reading-help');help.innerHTML=wordHelpHTML(example.annotations[Number(b.dataset.annotation)]);bindSaved(help);});
 const toggle=container.querySelector('[data-toggle-translation]'),translation=container.querySelector('.reading-translation');
 if(toggle)toggle.onclick=()=>{translation.hidden=!translation.hidden;toggle.textContent=translation.hidden?'Mostrar traducción':'Ocultar traducción';toggle.setAttribute('aria-expanded',String(!translation.hidden));};
}
function readingCard(example,index,hide=false,cloze=false){return `<article class="reading-card" data-example="${index}"><p class="meta">${esc(example.passage.variant_label)} · ${esc(example.passage.document)}</p><p class="guided-passage" lang="nci">${annotatedPassage(example,cloze)}</p><p class="hint">Pulsa las palabras subrayadas para consultar su ayuda y sus fuentes.</p><button class="link-button" data-toggle-translation aria-expanded="${!hide}">${hide?'Mostrar traducción':'Ocultar traducción'}</button><p class="reading-translation" ${hide?'hidden':''}>${esc(example.passage.es)}</p><div class="reading-help" aria-live="polite"></div>${passageSource(example)}</article>`;}
function lessonProgress(lesson){
 const edition=state.learning.id+':'+(lesson.practice_version||lesson.version||state.learning.version);
 const old=study.lessons[lesson.id];
 if(old?.edition===edition)return {edition,passed:Array.isArray(old.passed)?old.passed.filter(x=>Number.isInteger(x)&&x>=0&&x<lesson.examples.length):[],step:Number.isInteger(old.step)?Math.max(0,Math.min(old.step,lesson.examples.length-1)):0};
 return {edition,passed:[],step:0};
}
function pilotNote(){return `<p class="pilot-note">Lectura clásica · Piloto editorial · Revisión lingüística pendiente. Las traducciones proceden del corpus.</p>`;}
function renderLearn(id){
 const lessons=state.learning.lessons,lesson=lessons.find(l=>l.id===id);
 if(lesson){renderLesson(lesson);return;}
 const complete=lessons.filter(l=>lessonProgress(l).passed.length===l.examples.length).length;
 $('content').innerHTML=`<section class="learn-hero"><div><p class="eyebrow">APRENDER CON LAS FUENTES</p><h1>Leer palabras<br>en su contexto.</h1><p>Empieza a reconocer palabras del náhuatl clásico en fragmentos breves. Compara el original y su traducción, consulta las referencias visuales en sus documentos y guarda lo que quieras recordar.</p><div class="entry-actions"><a class="primary" href="#aprender/${esc(lessons.find(l=>lessonProgress(l).passed.length<l.examples.length)?.id||lessons[0]?.id||'')}">${complete?'Continuar aprendiendo':'Comenzar la primera lectura'}</a><a class="secondary" href="#lexico">Explorar el diccionario</a></div></div><div class="hero-glyph">${sourceImage(state.byId['glyph-xochitl'])}<p>xochitl · flor</p><small>Códice Mendoza, f. 10r · ${link(state.byId['glyph-xochitl']?.url,'Ver fuente')}</small></div></section>${pilotNote()}<div class="section-heading"><h2>Tus primeras lecturas</h2><span class="meta">${complete} de ${lessons.length} recorridos completados</span></div><div class="lesson-grid">${lessons.map((l,i)=>{const p=lessonProgress(l);return `<article class="lesson-card">${sourceImage(state.byId[l.cover_glyph],'lesson-cover')}<div><p class="eyebrow">Lectura ${i+1} · ${l.minutes} min</p><h3>${esc(l.title)}</h3><p>${esc(l.objective)}</p><p class="meta">${l.examples.length} ejemplos · ${p.passed.length} de ${l.examples.length} practicados</p><a class="secondary" href="#aprender/${esc(l.id)}">${p.passed.length===l.examples.length?'Volver a practicar':p.passed.length?'Continuar':'Abrir lectura'}</a></div></article>`;}).join('')}</div><section class="learn-next"><div><h2>De las palabras al documento</h2><p>El diccionario conserva la forma, el significado y el contexto de cada vínculo glífico. Un mismo signo puede tener funciones distintas según el documento.</p></div><div class="entry-actions"><a class="secondary" href="#leer">Leer los ${lessons.reduce((n,l)=>n+l.examples.length,0)} ejemplos</a><a class="secondary" href="#palabras">Mis palabras · ${study.saved.filter(x=>state.byId[x]?.kind==='sense').length}</a></div></section>`;
}
function renderLesson(lesson){
 let progress=lessonProgress(lesson),step=progress.step,answered=progress.passed.includes(step);
 const draw=()=>{
  const example=lesson.examples[step],exercise=example.exercise;
  $('content').innerHTML=`<a class="back-link" href="#aprender">← Todas las lecturas</a>${heading('Lectura guiada · '+(step===lesson.examples.length-1?'Ejemplo nuevo':'Náhuatl clásico'),lesson.title,lesson.objective)}<div class="lesson-progress" role="group" aria-label="Ejemplos de la lectura">${lesson.examples.map((e,i)=>`<button class="step-button ${i===step?'current':''}" data-step="${i}" aria-current="${i===step?'step':'false'}">${i+1}${progress.passed.includes(i)?' ✓':''}</button>`).join('')}<span>Ejemplo ${step+1} de ${lesson.examples.length}${step===lesson.examples.length-1?' · prueba lo que reconoces':''}</span></div>${pilotNote()}${lesson.reading_tips?.length?`<aside class="reading-tips"><h2>Claves para esta lectura</h2><ul>${lesson.reading_tips.map(t=>`<li>${esc(t)}</li>`).join('')}</ul></aside>`:''}<div class="lesson-layout"><section>${readingCard(example,step,true,exercise.kind==='cloze')}<div class="exercise-card"><p class="eyebrow">${exercise.kind==='cloze'?'Recuperar la forma de la fuente':'Comprender el fragmento'}</p><h2>${esc(exercise.question)}</h2><div class="answer-options">${exercise.options.map((o,i)=>`<button class="answer-option" data-answer="${i}" ${answered?'disabled':''}>${esc(o)}</button>`).join('')}</div><p class="exercise-feedback" role="status">${answered?'Respuesta correcta. '+esc(exercise.explanation):''}</p><div class="entry-actions"><button class="primary" id="next-example" ${answered?'':'disabled'}>${step===lesson.examples.length-1?'Terminar lectura':'Siguiente ejemplo →'}</button><button class="link-button" id="retry-example">Practicar este ejemplo otra vez</button></div></div></section><aside class="lesson-words"><h3>Palabras de esta lectura</h3>${lesson.sense_ids.map(id=>`<div class="lesson-word">${sourceImage(representativeGlyph(id),'small-glyph')}<div><a href="#lexico/${esc(id)}">${esc(headword(id))}</a><p>${esc(state.byId[id]?.label)}</p>${saveWordButton(id)}</div></div>`).join('')}<p class="meta">Glifos e imágenes de las fuentes. Abre cada ficha para ver el contexto y el folio.</p></aside></div>`;
  bindReading($('content').querySelector('.reading-card'),example);bindSaved($('content'));
  document.querySelectorAll('[data-step]').forEach(b=>b.onclick=()=>{step=Number(b.dataset.step);answered=progress.passed.includes(step);progress.step=step;study.lessons[lesson.id]=progress;writeStudy();draw();});
  document.querySelectorAll('[data-answer]').forEach(b=>b.onclick=()=>{
   const correct=Number(b.dataset.answer)===exercise.answer;
   b.classList.add(correct?'correct':'incorrect');
   document.querySelector('.exercise-feedback').textContent=(correct?'Respuesta correcta. ':'Revisa el fragmento. ')+exercise.explanation;
   if(correct){answered=true;if(!progress.passed.includes(step))progress.passed.push(step);progress.step=step;study.lessons[lesson.id]=progress;writeStudy();document.querySelectorAll('[data-answer]').forEach(x=>x.disabled=true);$('next-example').disabled=false;}
  });
  $('retry-example').onclick=()=>{progress.passed=progress.passed.filter(x=>x!==step);study.lessons[lesson.id]=progress;answered=false;writeStudy();draw();};
  $('next-example').onclick=()=>{
   if(!answered)return;
   if(step<lesson.examples.length-1){step++;progress.step=step;answered=progress.passed.includes(step);study.lessons[lesson.id]=progress;writeStudy();draw();$('content').scrollIntoView({block:'start'});}
   else if(progress.passed.length<lesson.examples.length){step=lesson.examples.findIndex((_,i)=>!progress.passed.includes(i));progress.step=step;answered=false;draw();}
   else renderLessonComplete(lesson);
  };
 };
 draw();
}
function renderLessonComplete(lesson){
 $('content').innerHTML=heading('Recorrido completado',lesson.title,`Has practicado los ${lesson.examples.length} fragmentos. Guarda las palabras que quieras repasar.`)+`<div class="completion-card"><h2>¿Qué quieres recordar?</h2><div class="saved-grid">${lesson.sense_ids.map(id=>wordCard(state.byId[id],true)).join('')}</div><div class="entry-actions"><a class="primary" href="#palabras">Repasar mis palabras</a><a class="secondary" href="#aprender">Elegir otra lectura</a><a class="secondary" href="#leer/${esc(lesson.id)}">Volver a los ejemplos</a></div><p class="meta">Completar el recorrido registra tu práctica; no certifica dominio de la lengua.</p></div>`;bindSaved($('content'));
}
function renderReader(id){
 const lessons=state.learning.lessons;
 $('content').innerHTML=heading('Lector · Náhuatl clásico','Leer con ayuda','Fragmentos seleccionados. Pulsa las palabras, oculta el español y consulta la fuente.')+pilotNote()+`<div class="reading-filters"><label>Lectura<select id="reader-lesson"><option value="">Todas las lecturas · ${lessons.reduce((n,l)=>n+l.examples.length,0)} ejemplos</option>${lessons.map(l=>`<option value="${esc(l.id)}">${esc(l.title)}</option>`).join('')}</select></label><a class="secondary" href="#investigar">Buscar en el archivo completo</a></div><div id="reader-examples"></div>`;
 const draw=()=>{const selected=lessons.filter(l=>!$('reader-lesson').value||l.id===$('reader-lesson').value),examples=selected.flatMap(l=>l.examples);$('reader-examples').innerHTML=examples.map((e,i)=>readingCard(e,i)).join('');document.querySelectorAll('[data-example]').forEach(c=>bindReading(c,examples[Number(c.dataset.example)]));};
 $('reader-lesson').value=lessons.some(l=>l.id===id)?id:'';$('reader-lesson').onchange=()=>{history.replaceState(null,'','#leer/'+$('reader-lesson').value);draw();};draw();
}
function wordCard(sense,save=false){const g=representativeGlyph(sense.id);return `<article class="dictionary-card">${g?.image?sourceImage(g,'word-thumbnail'):'<div class="word-thumbnail no-image">Referencia glífica pendiente</div>'}<div><a class="word-card-link" href="#lexico/${esc(sense.id)}"><strong lang="nci">${esc(headword(sense.id))}</strong><span>${esc(sense.label)}</span></a><p class="meta">${g?esc(state.byId[g.evidence?.[0]?.source_id]?.label):'Sin vínculo glífico específico'}</p>${g?.association?`<p class="association-caption">${esc(associationNames[g.association.type])}: ${esc(g.reading)}<br>Imagen relacionada; no equivale a esta palabra.</p>`:''}${sense.import_status==='automatic_transcription'?'<span class="pill proposed">Molina / GDN · extracción automática</span>':''}${g?.glyph_type==='iconography'?'<span class="pill">Iconografía de la fuente</span>':''}${save?saveWordButton(sense.id):''}</div></article>`;}
function dictionaryEntryHTML(sense){
 const forms=formsFor(sense.id).filter(filterRecord),glyphs=glyphsFor(sense.id),texts=state.records.filter(r=>r.kind==='text'&&r.sense_ids?.includes(sense.id));
 return `<article class="dictionary-entry"><a class="back-link" href="#lexico">← Diccionario</a><div class="dictionary-entry-head"><div><p class="eyebrow">${esc(sense.pos==='noun'?'Sustantivo':sense.pos==='verb'?'Verbo':'Otra categoría')} · Forma de referencia</p><h1 lang="nci">${esc(headword(sense.id))}</h1><h2>${esc(sense.label)}</h2><p>${esc(sense.definition)}</p></div>${saveWordButton(sense.id)}</div>${sense.import_status==='automatic_transcription'?'<p class="pilot-note">Entrada histórica extraída automáticamente de Molina/GDN. Se conserva su traducción original, sin modernizar ni segmentar acepciones. Cotejo primario y revisión lingüística pendientes.</p>':''}<section><h2>Palabra y referencia visual</h2>${glyphs.length?glyphs.map(g=>`<article class="glyph-evidence"><div>${sourceImage(g)||'<p class="empty">Imagen pendiente de incorporar. La ficha de la fuente sigue disponible.</p>'}</div><div>${glyphContext(g)}<details><summary>Evidencia de la asociación</summary>${badge(g)}${sourceCitations(g)}<p class="meta">${esc(g.notes)}</p></details></div></article>`).join(''):'<p class="empty">Esta acepción aún no tiene un vínculo glífico específico documentado en el índice. Puedes aportar una referencia con fuente y folio.</p>'}</section><section class="dictionary-forms"><h2>Formas y fuentes léxicas</h2>${forms.map(f=>`<details><summary><strong lang="nci">${esc(f.written)}</strong> · ${esc(f.variant_label||f.variant)} · ${esc(periods[f.period])}</summary><p class="meta">${esc(f.orthography)}</p>${f.catalog_normalized?`<p class="meta">Grafía normalizada por GDN, separada de la paleografía: <strong lang="nci">${esc(f.catalog_normalized)}</strong></p>`:''}${badge(f)}${sourceCitations(f)}${link(f.url,'Consultar entrada léxica')}<p class="meta">${esc(f.notes)}</p></details>`).join('')||'<p class="empty">Sin formas para estos filtros.</p>'}</section><section><h2>Ejemplos para leer</h2>${state.learning.lessons.filter(l=>l.examples.some(e=>e.annotations.some(a=>a.sense_id===sense.id))).map(l=>`<p><a href="#leer/${esc(l.id)}">${esc(l.title)} →</a></p>`).join('')||'<p class="meta">Aún no hay una lectura guiada para esta entrada.</p>'}${texts.map(t=>`<p><a href="#textos/${esc(t.id)}">${esc(t.label)}</a></p>`).join('')}<a class="secondary" href="#investigar/${encodeURIComponent(headword(sense.id))}">Buscar esta forma en el corpus</a></section><div class="entry-actions"><a class="secondary" href="#extraer/${esc(sense.id)}">Aportar forma o evidencia</a><button id="export-entry" class="link-button">Descargar ficha con fuentes</button></div><p class="content-note">${esc(sense.id)} · Las asociaciones conservan la época, la acepción y el contexto de la fuente.</p></article>`;
}
function renderDictionary(id){
 const sense=state.byId[id];
 if(sense?.kind==='sense'){
  $('content').innerHTML=dictionaryEntryHTML(sense);bindSaved($('content'));$('content').scrollIntoView({block:'start'});
  $('export-entry').onclick=()=>{const related=state.records.filter(r=>r.sense_id===sense.id||r.sense_ids?.includes(sense.id)),sourceIds=new Set(related.flatMap(r=>(r.evidence||[]).flatMap(e=>[e.source_id,e.via_source_id]).filter(Boolean)));const selected=new Map([sense,...related,...state.records.filter(r=>sourceIds.has(r.id))].map(r=>[r.id,r]));for(const r of selected.values()){const ids=[r.sense_id,r.association?.reference_form_id,r.association?.reference_glyph_id,...(r.evidence||[]).flatMap(e=>[e.source_id,e.via_source_id])];for(const ref of ids){if(state.byId[ref])selected.set(ref,state.byId[ref]);}}download(sense.id+'.json',{schema_version:1,records:[...selected.values()]});};return;
 }
 $('content').innerHTML=heading('Diccionario con fuentes','Palabras, glifos y contextos','Busca en español o náhuatl. Las entradas de Molina/GDN conservan la traducción histórica; las asociaciones glíficas mantienen su contexto.')+toolbar('lexico')+`<div class="dictionary-extra"><label class="dictionary-toggle"><input type="checkbox" id="with-glyph"> Solo palabras con imagen de fuente</label><label>Origen<select id="dictionary-origin"><option value="">Todas las entradas</option><option value="curated">Índice editorial con contextos</option><option value="automatic">Molina / GDN · extracción automática</option></select></label></div><p id="dictionary-count" class="results-count" role="status"></p><p id="dictionary-order" class="meta"></p><div id="dictionary-grid" class="dictionary-grid"></div><div class="pagination"><button id="dictionary-previous" class="secondary">Anterior</button><span id="dictionary-range"></span><button id="dictionary-next" class="secondary">Siguiente</button></div>`;
 let page=0;
 const draw=(reset=true)=>{
  if(reset)page=0;
  const rows=state.records.filter(s=>s.kind==='sense').filter(s=>{const forms=formsFor(s.id),origin=$('dictionary-origin').value;return (!origin||(origin==='automatic')===(s.import_status==='automatic_transcription'))&&includes([s.label,s.definition,...(s.aliases||[]),...forms.flatMap(f=>[f.written,f.catalog_normalized||''])].join(' '))&&(!state.filter.period&&!state.filter.variant||forms.some(filterRecord))&&(!$('with-glyph').checked||glyphsFor(s.id).some(g=>g.image));});
  const compare=(a,b)=>headword(a.id).localeCompare(headword(b.id),'es',{sensitivity:'base'})||a.label.localeCompare(b.label,'es',{sensitivity:'base'})||a.id.localeCompare(b.id);
  const defaultView=!state.filter.q.trim()&&!state.filter.period&&!state.filter.variant&&!$('dictionary-origin').value&&!$('with-glyph').checked;
  const priority=new Map((state.dictionaryFeatured||[]).map((id,i)=>[id,i]));
  const featured=defaultView?rows.filter(s=>priority.has(s.id)).sort((a,b)=>priority.get(a.id)-priority.get(b.id)):[];
  const alphabetic=rows.filter(s=>!featured.some(f=>f.id===s.id)).sort(compare);
  const ordered=[...featured,...alphabetic],firstSize=featured.length||48;
  const offset=page===0?0:firstSize+(page-1)*48,limit=page===0?firstSize:48;
  $('dictionary-count').textContent=`${rows.length} acepciones / entradas · ${rows.filter(s=>glyphsFor(s.id).some(g=>g.image)).length} con imagen de fuente`;
  $('dictionary-order').textContent=featured.length&&page===0?'Palabras representativas · selección inicial. Las siguientes páginas siguen el orden alfabético del náhuatl.':'Orden alfabético por palabra en náhuatl.';
  $('dictionary-grid').innerHTML=ordered.slice(offset,offset+limit).map(s=>wordCard(s,true)).join('')||'<p class="empty">No hay coincidencias. Prueba otra palabra o quita un filtro.</p>';
  $('dictionary-range').textContent=rows.length?`${offset+1}–${Math.min(offset+limit,rows.length)} de ${rows.length}`:'0';
  $('dictionary-previous').disabled=page===0;$('dictionary-next').disabled=offset+limit>=rows.length;bindSaved($('dictionary-grid'));
 };bindToolbar(draw);$('with-glyph').onchange=()=>draw();$('dictionary-origin').onchange=()=>draw();$('dictionary-previous').onclick=()=>{page--;draw(false);};$('dictionary-next').onclick=()=>{page++;draw(false);};draw();
}
function renderSaved(){
 const words=study.saved.map(id=>state.byId[id]).filter(r=>r?.kind==='sense'),now=Date.now(),due=words.filter(r=>!(Number(study.reviews[r.id]?.due)>now));
 $('content').innerHTML=heading('Tu cuaderno','Mis palabras','Guarda palabras desde el diccionario o mientras lees. El repaso y el progreso se conservan en este navegador.',`${words.length} guardadas`)+`<div class="saved-toolbar"><p>${due.length} para repasar hoy</p><button class="primary" id="start-review" ${due.length?'':'disabled'}>Repasar pendientes</button>${words.length?'<button class="secondary" id="review-all">Practicar todas</button>':''}</div><div id="word-review"></div><div class="saved-grid">${words.map(s=>wordCard(s,true)).join('')||'<div class="empty"><strong>Empieza con una palabra.</strong><p>Abre una ficha y pulsa Guardar palabra.</p><a href="#lexico">Explorar el diccionario →</a></div>'}</div><p class="content-note">${studyStorageAvailable?'Sin cuenta: los datos son locales a este navegador.':'El navegador no permite guardar; el progreso dura esta sesión.'}</p>`;
 $('start-review').onclick=()=>reviewWords(due);if($('review-all'))$('review-all').onclick=()=>reviewWords(words);
 document.querySelectorAll('[data-save-word]').forEach(b=>b.onclick=()=>{toggleSaved(b.dataset.saveWord);renderSaved();});
}
function reviewWords(words){
 let index=0;
 const draw=()=>{
  if(index>=words.length){$('word-review').innerHTML='<section class="review-card"><h2>Repaso terminado</h2><p>Las palabras marcadas para seguir practicando continúan pendientes.</p><button class="secondary" id="finish-review">Volver a mi cuaderno</button></section>';$('finish-review').onclick=renderSaved;return;}
  const s=words[index],g=representativeGlyph(s.id);
  $('word-review').innerHTML=`<section class="review-card"><p class="eyebrow">Repaso ${index+1} de ${words.length}</p>${g?sourceImage(g,'review-glyph'):''}<h2>${esc(s.label)}</h2><p>¿Recuerdas la forma de referencia de esta ficha?</p><button class="secondary" id="show-word">Mostrar palabra</button><div id="review-answer" hidden><p class="review-word" lang="nci">${esc(headword(s.id))}</p><p class="meta">${esc(g?.context||s.definition)}</p><p class="meta">${esc(g?.evidence?.[0]?.locator||'Consulta la fuente léxica en la ficha.')}</p><a href="#lexico/${esc(s.id)}">Abrir palabra y fuentes</a><div class="entry-actions"><button class="secondary" id="again-word">Seguir practicando</button><button class="primary" id="known-word">La recordé</button></div></div></section>`;
  $('show-word').onclick=()=>{$('review-answer').hidden=false;$('show-word').hidden=true;};
  $('again-word').onclick=()=>{study.reviews[s.id]={streak:0,due:0};writeStudy();index++;draw();};
  $('known-word').onclick=()=>{const old=Number(study.reviews[s.id]?.streak)||0,streak=Math.min(Math.max(old,0)+1,4),days=[1,3,7,14][streak-1];study.reviews[s.id]={streak,due:Date.now()+days*86400000};writeStudy();index++;draw();};
 };
 draw();$('word-review').scrollIntoView({block:'start'});
}
function renderArchive(query=''){
 const a=state.archive;
 $('content').innerHTML=heading('Archivo completo','Buscar testimonios','Elige una variedad y una obra para explorar los pasajes. Las etiquetas y traducciones se conservan como aparecen en el corpus.')+`<form id="research-form" class="research-search"><label for="research-query">Palabra o expresión en español o náhuatl</label><input type="search" id="research-query" maxlength="300" value="${esc(decodeURIComponent(query))}" placeholder="flor, xochitl, agua…"><div class="entry-actions"><button class="primary">Buscar en el corpus</button></div></form><div class="research-filters"><label>Variedad<select id="research-variant"><option value="">Todas las variedades</option>${a.variants.map(v=>`<option value="${esc(v.id)}">${esc(v.label)} · ${v.count.toLocaleString('es-MX')}</option>`).join('')}</select></label><label>Obra<select id="research-work"><option value="">Todas las obras</option>${a.documents.map(v=>`<option value="${esc(v.id)}">${esc(v.label)}</option>`).join('')}</select></label><a href="#leer">Abrir lecturas guiadas</a></div><div class="results-heading"><p id="archive-count" role="status"></p><button class="link-button" id="export-results">Descargar esta página</button></div><div id="archive-results"></div><div class="pagination"><button class="secondary" id="previous">Anterior</button><span id="page-number"></span><button class="secondary" id="next">Siguiente</button></div>`;
 if(query)$('research-variant').value='nci';let offset=0,version=0,rows=[];
 const draw=async()=>{const request=++version;$('archive-count').textContent='Buscando…';const params=new URLSearchParams({query:$('research-query').value,variant:$('research-variant').value,document:$('research-work').value,offset,limit:20});try{const d=await api('/api/research?'+params);if(request!==version||!$('archive-results'))return;rows=d.results;$('archive-count').textContent=`${d.total.toLocaleString('es-MX')} resultados`;$('archive-results').innerHTML=rows.map(passageHTML).join('')||'<p class="empty">Sin coincidencias. Cambia la palabra o los filtros.</p>';$('previous').disabled=!offset;$('next').disabled=offset+20>=d.total;$('page-number').textContent=d.total?`${offset+1}–${Math.min(offset+20,d.total)}`:'0';bindPassageDownloads($('archive-results'),rows);}catch(e){if($('archive-count'))$('archive-count').textContent=e.message;}};
 $('research-form').onsubmit=e=>{e.preventDefault();offset=0;draw();};for(const id of ['research-variant','research-work'])$(id).onchange=()=>{offset=0;draw();};$('previous').onclick=()=>{offset=Math.max(0,offset-20);draw();};$('next').onclick=()=>{offset+=20;draw();};$('export-results').onclick=()=>download('pasajes-axolotl.json',{citation:a.citation,revision:a.revision,records:rows});draw();
}
