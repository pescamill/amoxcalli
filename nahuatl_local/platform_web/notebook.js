'use strict';
// Mis palabras: cuaderno de palabras guardadas y repaso espaciado.

function renderSaved(){
 const words=study.saved.map(id=>state.byId[id]).filter(r=>r?.kind==='sense'),now=Date.now(),due=words.filter(r=>!(Number(study.reviews[r.id]?.due)>now));
 $('content').innerHTML=heading('Tu cuaderno','Mis palabras','Reúne las palabras que quieras recordar. Vuelve a sus pasajes y repásalas cuando lo necesites. Tu cuaderno queda en este navegador.',`${words.length} guardadas`)+`<div class="saved-toolbar"><p>${due.length} para repasar hoy</p><button class="primary" id="start-review" ${due.length?'':'disabled'}>Repasar pendientes</button>${words.length?'<button class="secondary" id="review-all">Practicar todas</button>':''}</div><div id="word-review"></div><div class="saved-grid">${words.map(s=>`<div>${wordCard(s,true)}${savedPassageHTML(s.id)}</div>`).join('')||'<div class="empty"><strong>Empieza con una palabra.</strong><p>Abre una ficha y pulsa Guardar palabra.</p><a href="#lexico">Explorar el diccionario →</a></div>'}</div><p class="content-note">${studyStorageAvailable?'Sin cuenta: los datos son locales a este navegador.':'El navegador no permite guardar; el progreso dura esta sesión.'}</p>`;
 $('start-review').onclick=()=>reviewWords(due);if($('review-all'))$('review-all').onclick=()=>reviewWords(words);
 document.querySelectorAll('[data-save-word]').forEach(b=>b.onclick=()=>{toggleSaved(b.dataset.saveWord);renderSaved();});
}
function reviewWords(words){
 let index=0;
 const draw=()=>{
  if(index>=words.length){$('word-review').innerHTML='<section class="review-card"><h2>Repaso terminado</h2><p>Las palabras marcadas para seguir practicando continúan pendientes.</p><button class="secondary" id="finish-review">Volver a mi cuaderno</button></section>';$('finish-review').onclick=renderSaved;return;}
  const s=words[index],g=representativeGlyph(s.id);
  $('word-review').innerHTML=`<section class="review-card"><p class="eyebrow">Repaso ${index+1} de ${words.length}</p>${g?sourceImage(g,'review-glyph'):''}<h2>${esc(s.label)}</h2>${savedPassageHTML(s.id,true)}<p>¿Recuerdas la forma de referencia de esta ficha?</p><button class="secondary" id="show-word">Mostrar palabra</button><div id="review-answer" hidden><p class="review-word" lang="nci">${esc(headword(s.id))}</p>${savedPassage(s.id)?`<p class="review-translation">${esc(savedPassage(s.id).example.passage.es)}</p>`:''}<p class="meta">${esc(g?.context||s.definition)}</p><p class="meta">${esc(g?.evidence?.[0]?.locator||'Consulta la fuente léxica en la ficha.')}</p><a href="#lexico/${esc(s.id)}">Abrir palabra y fuentes</a><div class="entry-actions"><button class="secondary" id="again-word">Seguir practicando</button><button class="primary" id="known-word">La recordé</button></div></div></section>`;
  $('show-word').onclick=()=>{$('review-answer').hidden=false;$('show-word').hidden=true;};
  $('again-word').onclick=()=>{study.reviews[s.id]={streak:0,due:0};writeStudy();index++;draw();};
  $('known-word').onclick=()=>{const old=Number(study.reviews[s.id]?.streak)||0,streak=Math.min(Math.max(old,0)+1,4),days=[1,3,7,14][streak-1];study.reviews[s.id]={streak,due:Date.now()+days*86400000};writeStudy();index++;draw();};
 };
 draw();$('word-review').scrollIntoView({block:'start'});
}
