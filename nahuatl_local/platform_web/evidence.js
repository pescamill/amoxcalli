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
function askExplanationHTML(x){
 if(!x||!x.sentences?.length)return '';
 const label={extractive:'Sin modelo · armada con la evidencia',claude:'Redactada por Claude con la evidencia mostrada'}[x.method]||x.method;
 return `<div class="ask-explanation-body"><p class="eyebrow">${esc(label)}</p>${x.sentences.map(s=>`<p>${esc(s.text)} ${s.citations.map(id=>`<button type="button" class="ask-cite" data-cite="${esc(id)}" aria-label="Ver evidencia ${esc(id)}">${esc(id.replace(/^axolotl-/,'#').replace(/^sense-/,''))}</button>`).join('')}</p>`).join('')}${x.fallback_reason?`<p class="meta">${esc(x.fallback_reason)}</p>`:''}<p class="meta">${esc(x.note)}</p></div>`;
}
function askEntryHTML(e){
 const sense=state.byId?.[e.sense_id];
 const title=`<strong lang="nci">${esc(e.written)}</strong> · ${esc(e.label)}`;
 return `<li class="ask-entry" data-evidence-id="${esc(e.sense_id)}">${sense?`<a href="#lexico/${esc(e.sense_id)}">${title}</a>`:title}<span class="ask-why">${esc(e.how)}${e.derivation?' · '+esc(e.derivation):''}</span>${e.automatic?'<span class="pill">Molina / GDN · extracción automática</span>':''}</li>`;
}
function askPassageHTML(p){
 return `<article class="ask-passage" data-evidence-id="${esc(p.id)}"><p class="passage-meta"><span>${esc(p.variety)}</span><span>${esc(p.document||'Obra no indicada')}</span><span>${esc(p.id)}</span></p><p class="nah-passage" lang="nci">${askHighlight(p.nah,p.form)}</p><p class="spanish-passage">${esc(p.es)}</p><p class="ask-why">${esc(p.why)}</p></article>`;
}
function askFormsHTML(forms){
 return forms?.length?`<p class="ask-forms">Formas en el archivo: ${forms.map(f=>`<span lang="nci">${esc(f.form)}</span> (${f.count})`).join(', ')}</p>`:'';
}
function askResultHTML(r){
 if(r.abstained)return `<section class="ask-result ask-abstained"><h2>Sin evidencia suficiente</h2><p>${esc(r.reason)}</p><a href="#investigar/${encodeURIComponent(r.word)}">Buscar «${esc(r.word)}» en el archivo completo →</a></section>`;
 let html='<section class="ask-result">';
 html+=`<p class="ask-understood">${r.language==='es'?`Palabra en español: <strong>${esc(r.word)}</strong>`:`Palabra náhuatl: <strong lang="nci">${esc(r.word)}</strong>`}${r.interpreted_as?` · se leyó como <strong lang="nci">${esc(r.interpreted_as)}</strong>, otra grafía del archivo`:''}</p>`;
 if(r.terms?.[0])html+=termGroupHTML(r.terms[0],r.query);
 if(r.explanation?.sentences?.length)html+=`<section class="ask-explanation" aria-label="Explicación"><h2>Explicación</h2><div class="ask-explanation-slot">${askExplanationHTML(r.explanation)}</div>${r.explain_models?.includes('claude')?'<button type="button" class="secondary" data-explain-claude>Redactar con Claude</button><p class="meta">Envía la pregunta y los pasajes mostrados a la API de Anthropic. Cada frase debe citar esta evidencia o se descarta.</p>':''}</section>`;
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
 $('content').innerHTML=heading('Preguntar con evidencia','¿Qué significa? ¿Cómo se dice?','Una palabra náhuatl en cualquier grafía, o una palabra en español. La respuesta reúne sus grafías, glifos, entradas del diccionario y pasajes del archivo; cada resultado dice por qué aparece.')+
  `<p class="ask-examples">Escribe en la búsqueda de arriba o prueba: ${askExamples.map(q=>`<a href="#preguntar/${encodeURIComponent(q)}">${esc(q)}</a>`).join(' · ')}</p><div id="ask-status" role="status" aria-live="polite"></div><div id="ask-results"></div>`;
 if(!query)return;
 $('ask-status').textContent='Buscando evidencia…';
 try{
  const r=await askEvidence(query);
  if(route().page!=='preguntar'||decodeURIComponent(route().id||'')!==query)return;
  $('ask-status').textContent='';$('ask-results').innerHTML=askResultHTML(r);bindAskResult($('ask-results'),query);
 }catch(e){if($('ask-status'))$('ask-status').textContent=e.message;}
}
function bindAskResult(root,query){
 const cites=()=>root.querySelectorAll('[data-cite]').forEach(b=>b.onclick=()=>{const target=[...root.querySelectorAll('[data-evidence-id]')].find(el=>el.dataset.evidenceId===b.dataset.cite);if(!target)return;target.scrollIntoView({block:'center'});target.classList.add('ask-flash');setTimeout(()=>target.classList.remove('ask-flash'),1600);});
 cites();
 const claude=root.querySelector('[data-explain-claude]');
 if(claude)claude.onclick=async()=>{
  const slot=root.querySelector('.ask-explanation-slot');claude.disabled=true;claude.textContent='Redactando…';
  try{slot.innerHTML=askExplanationHTML(await api('/api/explain?'+new URLSearchParams({q:query,model:'claude'})));cites();claude.hidden=true;}
  catch(e){slot.insertAdjacentHTML('beforeend',`<p class="meta">${esc(e.message)}</p>`);claude.disabled=false;claude.textContent='Redactar con Claude';}
 };
}
