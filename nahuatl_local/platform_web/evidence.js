'use strict';
// Preguntar: una palabra o pregunta breve → análisis, entradas y pasajes citados.
// Recuperación por raíz y por grafía laxa; no se usa un LLM ni se inventa una traducción.

const askExamples=['nocal','kuali','tlajtoli','¿cómo se dice mujer?','¿Qué significa xochitl?'];
const askCache=new Map();
function askEvidence(query){
 if(!askCache.has(query))askCache.set(query,api('/api/ask?'+new URLSearchParams({q:query})).catch(e=>{askCache.delete(query);throw e;}));
 return askCache.get(query);
}
function askHighlight(text,form){
 if(!form)return esc(text);
 const target=form.toLocaleLowerCase('es');
 return text.split(/([\p{L}\p{M}’']+)/u).map(part=>part.toLocaleLowerCase('es')===target?`<mark>${esc(part)}</mark>`:esc(part)).join('');
}
function askEntryHTML(e){
 const sense=state.byId?.[e.sense_id];
 const title=`<strong lang="nci">${esc(e.written)}</strong> · ${esc(e.label)}`;
 return `<li class="ask-entry">${sense?`<a href="#lexico/${esc(e.sense_id)}">${title}</a>`:title}<span class="ask-why">${esc(e.how)}${e.derivation?' · '+esc(e.derivation):''}</span>${e.automatic?'<span class="pill">Molina / GDN · extracción automática</span>':''}</li>`;
}
function askPassageHTML(p){
 return `<article class="ask-passage"><p class="passage-meta"><span>${esc(p.variety)}</span><span>${esc(p.document||'Obra no indicada')}</span><span>${esc(p.id)}</span></p><p class="nah-passage" lang="nci">${askHighlight(p.nah,p.form)}</p><p class="spanish-passage">${esc(p.es)}</p><p class="ask-why">${esc(p.why)}</p></article>`;
}
function askFormsHTML(forms){
 return forms?.length?`<p class="ask-forms">Formas en el archivo: ${forms.map(f=>`<span lang="nci">${esc(f.form)}</span> (${f.count})`).join(', ')}</p>`:'';
}
function askResultHTML(r){
 if(r.abstained)return `<section class="ask-result ask-abstained"><h2>Sin evidencia suficiente</h2><p>${esc(r.reason)}</p><a href="#investigar/${encodeURIComponent(r.word)}">Buscar «${esc(r.word)}» en el archivo completo →</a></section>`;
 let html='<section class="ask-result">';
 html+=`<p class="ask-understood">${r.language==='es'?`Palabra en español: <strong>${esc(r.word)}</strong>`:`Palabra náhuatl: <strong lang="nci">${esc(r.word)}</strong>`}${r.interpreted_as?` · se leyó como <strong lang="nci">${esc(r.interpreted_as)}</strong>, otra grafía del archivo`:''}</p>`;
 if(r.analysis&&typeof morphemeChips==='function')html+=`<h2>Análisis</h2>${morphemeChips(r.analysis)}<p class="meta">${esc(morphBasis?.[r.analysis.basis]||r.analysis.basis)} · análisis automático</p>`;
 if(r.entries.length)html+=`<h2>En el diccionario</h2><ul class="ask-entries">${r.entries.map(askEntryHTML).join('')}</ul>`;
 else if(r.language==='nah')html+='<p class="meta">Sin entrada en el diccionario; los pasajes muestran cómo se usa.</p>';
 if(r.candidates?.length)html+=`<h2>El corpus paralelo lo traduce así</h2><ul class="ask-candidates">${r.candidates.map(c=>`<li><strong lang="nci">${esc(c.forms[0]?.form||c.stem)}</strong> · raíz ${esc(c.stem)} · ${c.support} pasajes${c.in_dictionary?' · coincide con el diccionario':''}${askFormsHTML(c.forms)}</li>`).join('')}</ul><p class="meta">Asociación estadística entre raíces nahuas y palabras de las traducciones, con sus pasajes de apoyo. No es una definición.</p>`;
 if(r.root)html+=`<h2>Pasajes clásicos con la misma raíz</h2><p class="meta">Raíz <span lang="nci">${esc(r.root.stem)}</span> · ${r.root.total_passages.toLocaleString('es-MX')} pasajes.</p>${askFormsHTML(r.root.forms)}`;
 else if(r.passages.length)html+='<h2>Pasajes</h2>';
 html+=r.passages.map(askPassageHTML).join('');
 if(r.other_varieties.length)html+=`<h2>En otras variedades</h2><p class="meta">Misma palabra con otra ortografía; el analizador solo cubre el náhuatl clásico.</p>${r.other_varieties.map(askPassageHTML).join('')}`;
 if(r.gloss_hints?.length)html+=`<h2>Pistas de las traducciones</h2><p>${r.gloss_hints.map(h=>`≈ ${esc(h.word)} (${h.support} pasajes)`).join(' · ')}</p><p class="meta">Palabras frecuentes en las traducciones de pasajes con esta raíz.</p>`;
 html+=`<p class="ask-note">${esc(r.note)} Sin llamadas a modelos.</p></section>`;
 return html;
}
async function renderAsk(id){
 const query=decodeURIComponent(id||'');
 $('content').innerHTML=heading('Preguntar con evidencia','¿Qué significa? ¿Cómo se dice?','Escribe una palabra náhuatl en cualquier grafía, o una palabra en español. La respuesta reúne entradas del diccionario y pasajes del archivo; cada resultado dice por qué aparece.')+
  `<form id="ask-form" class="ask-form"><label for="ask-input">Palabra o pregunta</label><div class="ask-row"><input id="ask-input" type="search" maxlength="120" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="nocal, kuali, ¿cómo se dice mujer?" value="${esc(query)}"><button class="primary" type="submit">Preguntar</button></div><p class="ask-examples">Ejemplos: ${askExamples.map(q=>`<a href="#preguntar/${encodeURIComponent(q)}">${esc(q)}</a>`).join(' · ')}</p></form><div id="ask-status" role="status" aria-live="polite"></div><div id="ask-results"></div>`;
 $('ask-form').onsubmit=e=>{e.preventDefault();const q=$('ask-input').value.trim();if(q)location.hash='preguntar/'+encodeURIComponent(q);};
 if(!query)return;
 $('ask-status').textContent='Buscando evidencia…';
 try{
  const r=await askEvidence(query);
  if(route().page!=='preguntar'||decodeURIComponent(route().id||'')!==query)return;
  $('ask-status').textContent='';$('ask-results').innerHTML=askResultHTML(r);
 }catch(e){if($('ask-status'))$('ask-status').textContent=e.message;}
}
// Diccionario vacío: resumen breve con enlace a la evidencia completa.
async function askSuggestion(slot,query){
 if(!slot||!query)return;
 try{
  const r=await askEvidence(query);
  if(!slot.isConnected||r.abstained)return;
  const top=r.language==='es'?(r.candidates?.length?`El corpus paralelo traduce «${esc(r.word)}» en pasajes con <strong lang="nci">${esc(r.candidates[0].forms[0]?.form||r.candidates[0].stem)}</strong>.`:`Hay pasajes cuya traducción dice «${esc(r.word)}».`)
   :`${r.analysis&&typeof morphemeChips==='function'?morphemeChips(r.analysis):''}${r.interpreted_as?`<p>Otra grafía de <strong lang="nci">${esc(r.interpreted_as)}</strong>.</p>`:''}${r.entries[0]?`<p>Entrada: <strong lang="nci">${esc(r.entries[0].written)}</strong> · ${esc(r.entries[0].label)}</p>`:''}`;
  slot.innerHTML=`<div class="word-suggestion"><p class="eyebrow">${r.language==='es'?'Palabra en español':'¿Es una forma flexionada o con otra grafía?'}</p>${top}<a class="secondary" href="#preguntar/${encodeURIComponent(query)}">Ver evidencia y pasajes →</a></div>`;
 }catch{/* La sugerencia es opcional. */}
}
