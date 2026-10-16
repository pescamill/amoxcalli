'use strict';
// Pasajes: tarjeta de lectura, ayudas, comparación con otros fragmentos y regreso al pasaje
// de origen (Leer y Aprender usan la misma tarjeta).

function annotatedPassage(example,cloze=false){
 const r=example.passage;let end=0,html='';
 // Mismo mecanismo en Leer y en Aprender: cada palabra sin anotación se puede analizar.
 // En un ejercicio de completar solo se oculta la palabra del hueco.
 const blankAnnotated=cloze&&example.annotations.some(a=>a.quote===example.exercise.blank);
 const mask=cloze&&!blankAnnotated?{word:example.exercise.blank,done:false}:null;
 const plain=text=>typeof clickableWords==='function'?clickableWords(text,mask):esc(text);
 for(const [i,a] of example.annotations.entries()){
  html+=plain(r.nah.slice(end,a.start));
  const text=cloze&&a.quote===example.exercise.blank?'_____':a.quote;
  html+=`<button class="annotated-word" data-annotation="${i}" aria-label="${text==='_____'?'Palabra por completar':'Consultar '+esc(a.quote)}">${esc(text)}</button>`;end=a.end;
 }
 html+=plain(r.nah.slice(end));
 if(mask&&!mask.done&&typeof clickableWords!=='function')html=html.replace(esc(example.exercise.blank),'_____');
 return html;
}
function passageSource(example){const r=example.passage;return `<details class="reading-source"><summary>Fuente, contexto y estado de revisión</summary><p><strong>${esc(r.document)}</strong> · ${esc(r.variant_label)}</p><p>${esc(example.context)}</p><p class="meta">${esc(r.locator)} · ${esc(r.id)}</p><p class="meta">${esc(r.verification)}.</p>${link(r.source_url,'Distribución del corpus')}<p><a href="#extraer/${esc(r.id)}">Aportar un cotejo de este pasaje →</a></p><p class="meta">${esc(r.rights_note)}</p></details>`;}
// Resolve navigation IDs only against source-checked public learning data.
// This context neither filters the archive nor changes study storage.
function resolveReadingOrigin(mode,lessonId,passageId){
 if(!['leer','aprender'].includes(mode))return null;
 const lesson=state.learning?.lessons.find(l=>l.id===lessonId),index=lesson?.examples.findIndex(e=>e.archive_id===passageId);
 return index>=0?{mode,lesson,example:lesson.examples[index],index}:null;
}
function routeReadingOrigin(){
 const {page,id,params}=route(),keys=['from','lesson','passage'];
 if(!['leer','aprender','lexico','investigar','consultar'].includes(page)||Array.from(params.keys()).length!==keys.length||keys.some(k=>params.getAll(k).length!==1))return null;
 const origin=resolveReadingOrigin(params.get('from'),params.get('lesson'),params.get('passage'));
 if(origin&&['leer','aprender'].includes(page)&&(origin.mode!==page||origin.lesson.id!==id))return null;
 return origin;
}
function readingOrigin(example){
 const mode=route().page;if(!['leer','aprender'].includes(mode))return null;
 const lesson=state.learning.lessons.find(l=>l.examples.some(e=>e.archive_id===example.archive_id));
 return resolveReadingOrigin(mode,lesson?.id,example.archive_id);
}
function readingLookupHref(hash,origin){
 if(!origin)return hash;
 return hash+'?'+new URLSearchParams({from:origin.mode,lesson:origin.lesson.id,passage:origin.example.archive_id});
}
function preserveReadingLinks(container,origin){
 if(!origin)return;
 container.querySelectorAll('a[href^="#lexico"],a[href^="#investigar"]').forEach(a=>{
  a.setAttribute('href',readingLookupHref(a.getAttribute('href').split('?')[0],origin));
 });
}
function bindReadingQueryLink(link,input,page,origin){
 const update=()=>{const value=input.value;link.setAttribute('href',readingLookupHref('#'+page+(value?(page==='lexico'?'/buscar/':'/')+encodeURIComponent(value):''),origin));};
 const options={signal:pageSignal.signal};// la búsqueda global sobrevive a la página
 input.addEventListener('input',update,options);input.form?.addEventListener('submit',update,options);update();
}
function readingReturnHTML(origin){
 return origin?`<aside class="reading-return"><a class="secondary" data-reading-return href="${esc(readingLookupHref('#'+origin.mode+'/'+encodeURIComponent(origin.lesson.id),origin))}">Volver al pasaje de ${esc(origin.lesson.title)}</a><p class="meta">${esc(origin.example.passage.document)} · ${esc(origin.example.passage.locator)}</p></aside>`:'';
}
function focusReadingOrigin(origin){
 if(!origin)return;
 const card=Array.from($('content').querySelectorAll('[data-archive-id]')).find(c=>c.dataset.archiveId===origin.example.archive_id);
 if(!card)return;
 card.setAttribute('tabindex','-1');card.setAttribute('aria-label',`Pasaje de ${origin.lesson.title} · ${origin.example.passage.locator}`);
 card.focus({preventScroll:true});card.scrollIntoView({block:'start'});
}
function focusReadingReturn(){
 const back=$('content').querySelector('[data-reading-return]');if(back){back.focus({preventScroll:true});back.scrollIntoView({block:'start'});}
}
function readingWordKey(value){return String(value).normalize('NFC').toLowerCase();}
function readingWordMatches(text,query){
 const word=/[\p{L}\p{M}\p{N}_]+(?:['’-][\p{L}\p{M}\p{N}_]+)*/gu;
 const key=readingWordKey(query);
 return (readingWordKey(text).match(word)||[]).includes(key);
}
function readingComparisonPassage(row){
 return `<article class="reading-comparison-passage" data-preview-id="${esc(row.id)}"><p class="meta">${esc(row.document)} · ${esc(row.variant_label)}</p><blockquote lang="nci">${esc(row.nah)}</blockquote><button type="button" class="link-button" data-preview-translation aria-expanded="false">Mostrar traducción</button><p class="preview-translation" hidden>${esc(row.es)}</p><p class="meta">${esc(row.locator)} · ${esc(row.id)}</p><details><summary>Fuente y estado</summary>${link(row.source_url,'Fuente distribuida')}<p class="meta">${esc(row.verification)} · ${esc(row.rights_note)}</p></details></article>`;
}
// Grafías y glifos del término: misma búsqueda única que Diccionario, Archivo y Preguntar.
function fillWordTerm(slot,origin){
 if(!slot)return;
 termSearch(slot.dataset.termQuery,1).then(data=>{const g=data.groups?.[0];if(!g||!slot.isConnected)return;slot.innerHTML=termSummaryHTML(g,slot.dataset.termQuery);preserveReadingLinks(slot,origin);}).catch(()=>{});
}
function bindReading(container,example){
 const origin=readingOrigin(example);
 container.querySelectorAll('[data-annotation]').forEach(b=>b.onclick=()=>{container.querySelectorAll('[data-annotation]').forEach(x=>x.setAttribute('aria-expanded',String(x===b)));const help=container.querySelector('.reading-help');const annotation=example.annotations[Number(b.dataset.annotation)];
  // El hueco de un ejercicio no muestra su ayuda (ni la palabra) hasta responder.
  if(container.dataset.clozeBlank&&annotation.quote===container.dataset.clozeBlank){help.innerHTML=`<div class="word-help blank-help"><p>Esta es la palabra que falta. Elige una opción en el ejercicio; después verás aquí su ayuda, sus grafías y sus glifos.</p><a href="#lexico/${esc(annotation.sense_id)}">Prefiero abrir su entrada en el diccionario</a></div>`;preserveReadingLinks(help,origin);return;}
  help.innerHTML=wordHelpHTML(annotation);preserveReadingLinks(help,origin);bindSaved(help);const slot=help.querySelector('.auto-analysis');if(slot&&typeof showWordAnalysis==='function')showWordAnalysis(slot,annotation.quote,example);fillWordTerm(help.querySelector('.word-term'),origin);});
 if(typeof bindWordStudy==='function')bindWordStudy(container,example);
 const toggle=container.querySelector('[data-toggle-translation]'),translation=container.querySelector('.reading-translation');
 if(toggle)toggle.onclick=()=>{translation.hidden=!translation.hidden;toggle.textContent=translation.hidden?'Mostrar traducción':'Ocultar traducción';toggle.setAttribute('aria-expanded',String(!translation.hidden));};
 const form=container.querySelector('.explore-word-form'),input=form?.querySelector('input');
 if(form){
  const status=container.querySelector('.reading-comparison-status'),results=container.querySelector('.reading-comparison-results'),complete=container.querySelector('[data-comparison-archive]');
  let comparisonRun=0;
  const update=()=>{const q=input.value.trim();comparisonRun++;results.innerHTML='';status.textContent='';form.querySelector('[data-dictionary-lookup]').href=readingLookupHref('#lexico/buscar/'+encodeURIComponent(q),origin);form.querySelector('[data-dictionary-lookup]').hidden=!q;complete.href=readingLookupHref('#investigar/'+encodeURIComponent(q),origin);complete.hidden=!q;};
  input.oninput=update;form.onsubmit=e=>{e.preventDefault();const q=input.value.trim();if(q)location.hash=readingLookupHref('#investigar/'+encodeURIComponent(q),origin);};update();
  container.querySelectorAll('[data-explore-word]').forEach(b=>b.onclick=()=>{input.value=b.dataset.exploreWord;update();form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));});
  const compare=form.querySelector('[data-reading-compare]');
  compare.onclick=async()=>{
   const query=input.value.trim(),run=++comparisonRun,hash=location.hash;
   const current=()=>run===comparisonRun&&container.isConnected&&location.hash===hash&&input.value.trim()===query;
   results.innerHTML='';
   if(!/^[\p{L}\p{M}\p{N}_]+(?:['’-][\p{L}\p{M}\p{N}_]+)*$/u.test(readingWordKey(query))){status.textContent='Copia una sola palabra para compararla aquí. Puedes buscar la frase completa en el Archivo.';return;}
   status.textContent='Buscando otros fragmentos con «'+query+'»…';
   try{
    const data=await api('/api/research?'+new URLSearchParams({query,variant:'nci',period:'historical',offset:'0',limit:'10'}));
    if(!current())return;
    if(!Array.isArray(data.results))throw Error('Respuesta de búsqueda inválida.');
    const seen=new Set(),rows=data.results.slice(0,10).filter(row=>row.id!==example.archive_id&&row.iso==='nci'&&row.period==='historical'&&readingWordMatches(row.nah,query)&&!seen.has(row.id)&&seen.add(row.id)).slice(0,2);
    results.innerHTML=rows.map(readingComparisonPassage).join('');
    status.textContent=rows.length?'Se muestran '+rows.length+' otros fragmentos con la misma escritura. Esta es una selección; puedes ampliar en el Archivo. Compara su contexto; la escritura no decide el sentido.':'No aparecen otros fragmentos con esta escritura exacta en esta muestra. Puedes ampliar la búsqueda en el Archivo.';
    results.querySelectorAll('[data-preview-translation]').forEach(b=>b.onclick=()=>{const es=b.parentElement.querySelector('.preview-translation');es.hidden=!es.hidden;b.textContent=es.hidden?'Mostrar traducción':'Ocultar traducción';b.setAttribute('aria-expanded',String(!es.hidden));});
   }catch(error){if(current())status.textContent='No se pudo cargar la comparación. Puedes volver a intentarlo o abrir el Archivo completo.';}
  };
  container.querySelectorAll('[data-compare-word]').forEach(b=>b.onclick=()=>{input.value=b.dataset.compareWord;update();compare.click();});
 }
}
function readingCard(example,index,hide=false,cloze=false){return `<article class="reading-card" data-example="${index}" data-archive-id="${esc(example.archive_id)}"${cloze?` data-cloze-blank="${esc(example.exercise.blank)}"`:''}><p class="meta">${esc(example.passage.variant_label)} · ${esc(example.passage.document)}</p><p class="guided-passage" lang="nci">${annotatedPassage(example,cloze)}</p><p class="hint">Pulsa las palabras subrayadas para consultar su ayuda y sus fuentes; cualquier otra palabra muestra un análisis automático.</p><div class="reading-toggles"><button class="link-button" data-toggle-translation aria-expanded="${!hide}">${hide?'Mostrar traducción':'Ocultar traducción'}</button><button class="link-button" data-interlinear aria-expanded="false">Mostrar glosa interlineal</button></div><div class="interlinear-box" hidden></div><p class="reading-translation" ${hide?'hidden':''}>${esc(example.passage.es)}</p><div class="reading-help" aria-live="polite"></div><details class="reading-explore"><summary>¿Hay otra palabra que quieras entender?</summary><p>Busca su escritura en otros testimonios y compara las traducciones completas.</p>${example.explore_words?.length?`<div class="entry-actions">${example.explore_words.map(q=>`<span><button class="secondary" data-explore-word="${esc(q)}" lang="nci" aria-label="Buscar ${esc(q)} en el Archivo">${esc(q)}</button><button type="button" class="link-button" data-compare-word="${esc(q)}" aria-label="Comparar aquí ${esc(q)}">Comparar aquí</button></span>`).join('')}</div>`:''}<form class="explore-word-form"><label>Palabra del fragmento<input type="text" maxlength="300" required placeholder="Copia aquí la palabra que te interesa"></label><div class="entry-actions"><button class="secondary" type="submit">Buscar ejemplos en el archivo</button><button class="secondary" type="button" data-reading-compare>Comparar aquí</button><a data-dictionary-lookup>Consultar el diccionario</a></div></form><section class="reading-comparison" aria-label="Otros fragmentos para comparar"><p class="reading-comparison-status" role="status" aria-live="polite"></p><div class="reading-comparison-results"></div><a data-comparison-archive>Abrir búsqueda completa en el Archivo</a></section></details>${passageSource(example)}</article>`;}
// Tras responder, el pasaje recupera la palabra del hueco; la traducción conserva su estado.
function revealCard(example,index){
 const card=$('content').querySelector('.reading-card');if(!card||!card.dataset.clozeBlank)return;
 const hidden=card.querySelector('.reading-translation')?.hidden??true;
 const wrap=document.createElement('div');wrap.innerHTML=readingCard(example,index,hidden,false);
 const fresh=wrap.firstElementChild;card.replaceWith(fresh);bindReading(fresh,example);
}
function renderReader(id){
 const lessons=state.learning.lessons;
 $('content').innerHTML=heading('Lector · Náhuatl clásico','Leer con ayuda','Lee a tu ritmo. Toca una palabra para conocerla; muestra el español cuando lo necesites.')+`<div class="reading-filters"><label>Lectura<select id="reader-lesson"><option value="">Todas las lecturas · ${lessons.reduce((n,l)=>n+l.examples.length,0)} ejemplos</option>${lessons.map(l=>`<option value="${esc(l.id)}">${esc(l.title)}</option>`).join('')}</select></label><div class="entry-actions"><a class="secondary" id="reader-workshop">Preparar ficha para taller</a><a class="secondary" href="#investigar">Buscar en el archivo completo</a></div></div><div id="reader-examples"></div>`;
 const draw=()=>{$('reader-workshop').href='#taller/'+($('reader-lesson').value||lessons[0]?.id||'');const selected=lessons.filter(l=>!$('reader-lesson').value||l.id===$('reader-lesson').value),examples=selected.flatMap(l=>l.examples);$('reader-examples').innerHTML=examples.map((e,i)=>readingCard(e,i)).join('');document.querySelectorAll('[data-example]').forEach(c=>bindReading(c,examples[Number(c.dataset.example)]));};
 $('reader-lesson').value=lessons.some(l=>l.id===id)?id:'';$('reader-lesson').onchange=()=>{history.replaceState(null,'','#leer/'+$('reader-lesson').value);draw();};draw();focusReadingOrigin(routeReadingOrigin());
}
