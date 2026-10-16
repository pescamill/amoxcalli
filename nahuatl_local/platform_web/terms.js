'use strict';
// Grupo de término: lo que devuelve la búsqueda única (/api/terms, terms.TermIndex).
// Diccionario, Archivo, Preguntar y Consultar fichas muestran este mismo bloque; solo cambia lo que va debajo.

const termScopes={word:'Palabra completa',component:'Componente',meaning:'Relación de significado',thematic:'Referencia temática'};
const termCache=new Map();
function termSearch(query,limit=5){
 const key=limit+'\u0000'+query;
 if(!termCache.has(key))termCache.set(key,api('/api/terms?'+new URLSearchParams({q:query,limit})).catch(e=>{termCache.delete(key);throw e;}));
 return termCache.get(key);
}
function termVarieties(byVariety){return Object.entries(byVariety||{}).map(([v,n])=>`${esc(v)} ${n.toLocaleString('es-MX')}`).join(' · ');}
function termSpelling(form,total,detail){return `<li><strong lang="nci">${esc(form)}</strong>${total?` <span class="term-count">${total.toLocaleString('es-MX')}</span>`:''}${detail?`<small>${detail}</small>`:''}</li>`;}
function termGlyphLink(g){
 if(g.source==='dictionary')return `<a href="#lexico/${esc(g.sense_id)}" lang="nci">${esc(g.reading)}</a> <small>diccionario</small>`;
 if(g.source==='tlachia_element')return `<a href="#glifos/elemento/${encodeURIComponent(g.id)}" lang="nci">${esc(g.designation)}</a> <small>elemento · ${esc(g.document||'Tlachia')}</small>`;
 return `<a href="#glifos/ficha/${encodeURIComponent(g.id)}" lang="nci">${esc(g.reading)}</a> <small>${g.kind==='personage'?'personaje':'glifo'} · ${esc(g.document||'Tlachia')}${g.locator?' · '+esc(g.locator):''}</small>`;
}
function termGlyphsHTML(g){
 if(!g.glyphs.length&&!g.glyphs_uncertain.length)return '<p class="meta">Sin referencias pictográficas registradas para este término.</p>';
 const groups=Object.keys(termScopes).map(scope=>[scope,g.glyphs.filter(x=>x.scope===scope)]).filter(([,rows])=>rows.length);
 return groups.map(([scope,rows])=>`<div class="term-glyph-scope"><p class="eyebrow">${esc(termScopes[scope])} · ${rows.length}</p><ul>${rows.slice(0,12).map(x=>`<li>${termGlyphLink(x)}</li>`).join('')}</ul>${rows.length>12?`<p class="meta">y ${rows.length-12} más en Glifos.</p>`:''}</div>`).join('')+
  (g.glyphs_uncertain.length?`<details class="term-uncertain"><summary>${g.glyphs_uncertain.length} referencias que solo contienen el término</summary><ul>${g.glyphs_uncertain.map(x=>`<li>${termGlyphLink(x)}</li>`).join('')}</ul><p class="meta">Otra palabra o lectura que incluye el término; no se presentan como el término.</p></details>`:'');
}
// Bloque del grupo. query: la consulta, para enlazar las cuatro vistas con la misma búsqueda.
function termGroupHTML(g,query){
 const q=encodeURIComponent(query||g.lemma),s=g.spellings;
 const senses=g.senses.length?`<p class="term-senses">${g.senses.slice(0,4).map(x=>state.byId?.[x.id]?`<a href="#lexico/${esc(x.id)}">${esc(x.label)}</a>`:esc(x.label)).join(' · ')}${g.senses.length>4?` · y ${g.senses.length-4} acepciones más`:''}</p>`
  :`<p class="term-senses meta">Sin entrada en el diccionario: el grupo reúne las grafías del archivo.${g.gloss_hints?.length?` Las traducciones de sus pasajes dicen ${g.gloss_hints.map(h=>'«'+esc(h.word)+'»').join(', ')} (pista estadística, no definición).`:''}</p>`;
 return `<section class="term-group" data-term-id="${esc(g.id)}" aria-label="Término ${esc(g.lemma)}">
<div class="term-head"><div><p class="eyebrow">${g.source==='dictionary'?'Término del diccionario':'Término del archivo'}${g.match?' · '+esc(g.match.why):''}</p><h2 lang="nci">${esc(g.lemma)}</h2>${senses}</div><p class="term-passages"><strong>${g.passages.total.toLocaleString('es-MX')}</strong> pasajes<small>${termVarieties(g.passages.by_variety)}</small></p></div>
<div class="term-columns"><div><h3>Grafías</h3><ul class="term-spellings">${s.attested.map(v=>termSpelling(v.form,v.total,`${esc(v.orthography)}${v.dictionary?' · diccionario':''}`)).join('')}</ul>
${s.inflected.length?`<h3>Formas flexionadas</h3><ul class="term-spellings">${s.inflected.slice(0,16).map(v=>termSpelling(v.forms.join(' / '),v.total,v.segmentation?esc(v.segmentation):'')).join('')}</ul>${s.inflected.length>16?`<p class="meta">y ${s.inflected.length-16} formas más.</p>`:''}`:''}
${s.uncertain.length?`<details class="term-uncertain"><summary>${s.uncertain.length} grafías inciertas · aparte, no se suman${g.passages.uncertain_total?` (${g.passages.uncertain_total.toLocaleString('es-MX')} pasajes)`:''}</summary><ul class="term-spellings">${s.uncertain.slice(0,30).map(v=>termSpelling(v.forms.join(' / '),v.total,esc(v.why))).join('')}</ul></details>`:''}</div>
<div><h3>Glifos y lecturas</h3>${termGlyphsHTML(g)}</div></div>
<nav class="term-views" aria-label="Ver este término en"><a href="#lexico/buscar/${q}">Diccionario</a><a href="#investigar/${q}">Archivo</a><a href="#preguntar/${q}">Preguntar</a><a href="#consultar/${q}">Consultar fichas</a></nav>
<p class="meta">Las grafías se reúnen por clave laxa y por raíz del analizador; las inciertas quedan aparte.</p></section>`;
}
// Resumen del término dentro de la ayuda de una palabra (Leer y Aprender): grafías, glifos y paso a Preguntar.
function termSummaryHTML(g,query){
 const q=encodeURIComponent(query||g.lemma),spellings=g.spellings.attested.slice(0,5),glyphs=[...g.glyphs].sort((a,b)=>(a.scope!=='word')-(b.scope!=='word')).slice(0,4);
 const inflected=g.spellings.inflected.length;
 return `<section class="term-summary" data-term-id="${esc(g.id)}" aria-label="Grafías y glifos de ${esc(g.lemma)}"><p class="eyebrow">Grafías y glifos</p>
<p>${spellings.map(v=>`<strong lang="nci">${esc(v.form)}</strong> <span class="term-count">${v.total.toLocaleString('es-MX')}</span>`).join(' · ')}${inflected?` · y ${inflected} ${inflected===1?'forma flexionada':'formas flexionadas'}`:''}</p>
${glyphs.length?`<p class="term-summary-glyphs">${glyphs.map(termGlyphLink).join(' · ')}${g.glyphs.length>glyphs.length?` · y ${g.glyphs.length-glyphs.length} más`:''}</p>`:'<p class="meta">Sin glifos registrados para este término.</p>'}
<p class="meta">${g.passages.total.toLocaleString('es-MX')} pasajes en el archivo.</p><div class="entry-actions"><a class="primary" href="#preguntar/${q}">Preguntar sobre ${esc(g.lemma)} →</a><a class="secondary" href="#lexico/buscar/${q}">Ver todas sus grafías</a></div></section>`;
}
