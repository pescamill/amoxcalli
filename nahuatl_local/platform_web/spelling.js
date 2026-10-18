'use strict';
// Grafías (spelling.Search): sugerencias mientras se escribe en la búsqueda global y la vista «Grafías» de una palabra.
// Nada se presenta como «la grafía correcta»: cada fuente conserva la suya y una conjetura nunca se muestra como atestiguada.

const spellingCache=new Map();
function spellingSearch(q,limit=5){
 const key=limit+'\u0000'+q;
 if(!spellingCache.has(key))spellingCache.set(key,api('/api/spellings?'+new URLSearchParams({q,limit})).catch(e=>{spellingCache.delete(key);throw e;}));
 return spellingCache.get(key);
}
const spellingConfidence={alta:'confianza alta',media:'confianza media',baja:'confianza baja'};
function spellingVarieties(by){return Object.entries(by||{}).slice(0,3).map(([v,n])=>`${esc(v.replace(/^Náhuatl (de la |de |)/,''))} ${n.toLocaleString('es-MX')}`).join(' · ');}
function spellingCandidateHTML(c,i){
 const m=c.match;
 return `<li role="option" id="spelling-option-${i}" class="spelling-option" data-id="${esc(c.id)}"><a href="#grafias/${encodeURIComponent(c.id)}">
<span class="spelling-lemma" lang="nci">${esc(c.lemma)}</span>${m.form&&m.form!==c.lemma.toLowerCase()?` <span class="spelling-form">como <strong lang="nci">${esc(m.form)}</strong></span>`:''}
<small>${esc(m.why)} · ${esc(spellingConfidence[m.confidence.label])}${c.total?` · ${c.total.toLocaleString('es-MX')} ${c.total===1?'aparición':'apariciones'} (${spellingVarieties(c.by_variety)})`:''}${c.senses.length?' · '+esc(c.senses.map(s=>s.label).join('; ')):''}</small></a></li>`;
}
function spellingSuggestHTML(r){
 if(!r.candidates.length)return `<p class="spelling-note">Sin grafías parecidas en el archivo ni en el diccionario.</p>`;
 return `${r.note?`<p class="spelling-note">${esc(r.note)}</p>`:''}<ul role="listbox" aria-label="Posibilidades para ${esc(r.word)}">${r.candidates.map(spellingCandidateHTML).join('')}</ul>`;
}
// Sugerencias bajo la caja de búsqueda global. Se suman a lo que cada página hace con la caja (filtros, Preguntar).
(function bindSpellingSuggestions(){
 const input=$('search'),form=$('global-search');if(!input||!form)return;
 const box=document.createElement('div');box.id='spelling-suggest';box.className='spelling-suggest';box.hidden=true;form.appendChild(box);
 input.setAttribute('aria-controls','spelling-suggest');input.setAttribute('aria-autocomplete','list');
 let timer=null,seq=0,active=-1;
 const hide=()=>{box.hidden=true;active=-1;input.removeAttribute('aria-activedescendant');};
 input.addEventListener('input',()=>{
  clearTimeout(timer);const q=input.value.trim();
  if(q.length<2||/\s/.test(q)){hide();return;}
  timer=setTimeout(async()=>{
   const mine=++seq;
   try{const r=await spellingSearch(q);if(mine!==seq||input.value.trim()!==q)return;box.innerHTML=spellingSuggestHTML(r);box.hidden=false;active=-1;}
   catch{if(mine===seq)hide();}
  },120);
 });
 input.addEventListener('keydown',e=>{
  const items=[...box.querySelectorAll('.spelling-option')];
  if(box.hidden||!items.length){return;}
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();active=(active+(e.key==='ArrowDown'?1:-1)+items.length)%items.length;
   items.forEach((x,i)=>x.classList.toggle('active',i===active));input.setAttribute('aria-activedescendant',items[active].id);}
  else if(e.key==='Enter'&&active>=0){e.preventDefault();location.hash='grafias/'+encodeURIComponent(items[active].dataset.id);hide();}
  else if(e.key==='Escape')hide();
 });
 box.addEventListener('click',e=>{if(e.target.closest('a'))hide();});
 document.addEventListener('click',e=>{if(!form.contains(e.target))hide();});
 form.addEventListener('submit',hide);
 window.addEventListener('hashchange',hide);
})();

// Modo editor (solo en este navegador): muestra los botones de revisión. La decisión se guarda en el servidor con la sesión.
function spellingEditor(){try{return localStorage.getItem('amoxcalli-spelling-editor')==='1';}catch{return false;}}
function spellingEdgeHTML(e,editor){
 const kinds=e.types.join(' + ');
 const rules=e.rules.map(r=>`${esc(r.label)}${r.active?'':' (regla en revisión)'}`).join('; ');
 const tr=e.translations?.shared?.length?` · traducciones: ${e.translations.shared.map(w=>'«'+esc(w)+'»').join(', ')}`:'';
 return `<li class="spelling-edge ${esc(e.status)}"><span lang="nci"><strong>${esc(e.a)}</strong> ↔ <strong>${esc(e.b)}</strong></span>
<small>${esc(kinds)} · ${esc(e.why)}${rules&&!e.why.includes(rules)?' · '+rules:''}${tr}</small>
${editor?`<span class="spelling-review" data-a="${esc(e.a)}" data-b="${esc(e.b)}"><button class="link-button" data-decision="accept">Confirmar</button> <button class="link-button" data-decision="reject">Separar</button> <button class="link-button" data-decision="clear">Deshacer</button></span>`:''}</li>`;
}
function spellingProfilesHTML(profiles){
 return `<table class="spelling-profiles"><thead><tr><th>Perfil</th><th>Forma</th><th>Nota</th></tr></thead><tbody>${profiles.map(p=>`<tr><td>${esc(p.label)}</td><td lang="nci"><strong>${esc(p.form)}</strong></td><td>${esc(p.note||'')}</td></tr>`).join('')}</tbody></table>`;
}
async function renderSpellings(id){
 const gid=decodeHash(id||'');
 if(!gid){$('content').innerHTML=`<section class="page-heading"><div><p class="eyebrow">Grafías</p><h1>Escribe una palabra como la escribes</h1><p>Usa la búsqueda de arriba: <em>kuali</em>, <em>qualli</em>, <em>cuali</em>… Verás las posibilidades con sus fuentes.</p></div></section>`;return;}
 const d=await api('/api/spellings/word?'+new URLSearchParams({id:gid}));
 const editor=spellingEditor();
 const spellings=d.spellings.map(v=>`<tr><td lang="nci"><strong>${esc(v.form)}</strong>${d.dictionary_spellings.some(s=>s.toLowerCase()===v.form)?' <small>diccionario</small>':''}</td><td>${v.total.toLocaleString('es-MX')}</td><td>${spellingVarieties(v.by_variety)||'—'}</td><td>${v.example?`<span lang="nci">${esc(v.example.nah)}</span><small>${esc(v.example.es)} · <a href="#investigar/${encodeURIComponent(v.form)}">${esc(v.example.id)}</a></small>`:'<small>solo en el diccionario</small>'}</td></tr>`).join('');
 $('content').innerHTML=`<section class="page-heading"><div><p class="eyebrow">Grafías · ${d.source==='dictionary'?'término del diccionario':'término del archivo'}</p><h1 lang="nci">${esc(d.lemma)}</h1>
${d.senses.length?`<p>${d.senses.map(s=>`<a href="#lexico/${esc(s.id)}">${esc(s.label)}</a>`).join(' · ')}</p>`:''}<p class="meta">Ninguna grafía es «la correcta»: cada fuente conserva la suya. ${d.total.toLocaleString('es-MX')} apariciones · ${spellingVarieties(d.by_variety)}${d.glyphs?` · ${d.glyphs} referencias pictográficas`:''}</p></div>
<nav class="term-views"><a href="#preguntar/${encodeURIComponent(d.lemma)}">Preguntar</a><a href="#investigar/${encodeURIComponent(d.lemma)}">Archivo</a></nav></section>
<section class="spelling-section"><h2>En cada perfil</h2>${spellingProfilesHTML(d.profiles)}<p class="spelling-limit">${esc(d.limit_note)}</p>
<form id="spelling-convert" class="spelling-convert"><label for="spelling-convert-input">Ver otra forma en cada perfil</label><input id="spelling-convert-input" autocomplete="off" spellcheck="false" placeholder="p. ej. kwawtli"><div id="spelling-convert-out"></div></form></section>
<section class="spelling-section"><h2>Grafías atestiguadas</h2><table class="spelling-table"><thead><tr><th>Grafía</th><th>Apariciones</th><th>Variedades</th><th>Pasaje de ejemplo</th></tr></thead><tbody>${spellings}</tbody></table></section>
<section class="spelling-section"><h2>Por qué se asocian</h2>${d.edges.length?`<ul class="spelling-edges">${d.edges.map(e=>spellingEdgeHTML(e,editor)).join('')}</ul>`:'<p class="meta">Las grafías de arriba comparten la misma forma pivote: solo cambia la convención ortográfica.</p>'}
${d.uncertain.length?`<details class="term-uncertain"><summary>${d.uncertain.length} asociaciones inciertas · aparte, no se suman</summary><ul class="spelling-edges">${d.uncertain.map(e=>spellingEdgeHTML(e,editor)).join('')}</ul></details>`:''}
<p class="meta"><label><input type="checkbox" id="spelling-editor" ${editor?'checked':''}> Modo editor (botones de revisión; requiere sesión)</label> <span id="spelling-review-status" role="status"></span></p></section>`;
 $('spelling-editor').onchange=e=>{try{localStorage.setItem('amoxcalli-spelling-editor',e.target.checked?'1':'0');}catch{}renderSpellings(id);};
 $('spelling-convert').onsubmit=async e=>{e.preventDefault();const q=$('spelling-convert-input').value.trim();if(!q)return;
  try{const r=await spellingSearch(q,1);$('spelling-convert-out').innerHTML=spellingProfilesHTML(r.profiles);}catch(err){$('spelling-convert-out').textContent=err.message;}};
 document.querySelectorAll('.spelling-review button').forEach(b=>b.onclick=async()=>{
  const box=b.parentElement,status=$('spelling-review-status');
  try{await api('/api/spellings/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({a:box.dataset.a,b:box.dataset.b,decision:b.dataset.decision})});
   spellingCache.clear();status.textContent='Decisión guardada.';renderSpellings(id);}
  catch(err){status.textContent=err.message;}
 });
}
