'use strict';
// Palabras del catálogo: formas, glifos con su procedencia y la ayuda de una palabra anotada.


const glyphTypes={element:'Elemento de un compuesto',simplex:'Glifo simple',compound:'Glifo compuesto',iconography:'Imagen iconográfica',unspecified:'Referencia de catálogo'};
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
function appendSourceCredits(){
 $('content').querySelector('.source-credit-summary')?.remove();
 const visible=new Set(Array.from($('content').querySelectorAll('img[data-source-image]')).map(i=>i.getAttribute('src'))),groups=new Map();
 for(const g of state.records.filter(r=>r.kind==='glyph'&&visible.has(r.image))){const key=g.image_credit||'Consultar derechos en la ficha de la fuente.';if(!groups.has(key))groups.set(key,[]);if(!groups.get(key).some(r=>r.url===g.url))groups.get(key).push(g);}
 if(!groups.size)return;
 const details=document.createElement('details');details.className='source-credit-summary';details.innerHTML='<summary>Créditos y procedencia de las imágenes</summary>'+Array.from(groups,([credit,rows])=>`<p>${esc(credit)}<br>${rows.map(g=>link(g.url,g.reading)).join(' · ')}</p>`).join('');$('content').append(details);
}
function wordHelpHTML(annotation){
 const sense=state.byId[annotation.sense_id],g=annotation.glyph_id?state.byId[annotation.glyph_id]:representativeGlyph(annotation.sense_id);
 const relations={full_word:'Palabra completa',observed_form:'Forma del pasaje · análisis automático abajo',source_variant:'Grafía de la fuente · relación pendiente de cotejo',thematic:'Comparación temática'};
 return `<div class="word-help"><div>${g?sourceImage(g,'help-image'):''}</div><div><p class="eyebrow">Ayuda de lectura${annotation.relation?' · '+esc(relations[annotation.relation]):''}</p><h3 lang="nci">${esc(annotation.quote)}</h3><p class="lookup-reference">Entrada de consulta: <a href="#lexico/${esc(annotation.sense_id)}"><span lang="nci">${esc(headword(annotation.sense_id))}</span> · ${esc(sense?.label)}</a></p><p>${esc(annotation.note)}</p><p class="meta">${g?esc(state.byId[g.evidence?.[0]?.source_id]?.label)+' · '+esc(g.evidence?.[0]?.locator):'Sin referencia glífica específica incorporada.'}</p>${g?'<p class="meta">La referencia visual y este pasaje pertenecen a documentos distintos. Consulta el alcance de la relación.</p>'+associationHTML(g):''}${pictographicLinksHTML(annotation.sense_id)}<div class="word-term" data-term-query="${esc(headword(annotation.sense_id)||annotation.quote)}"></div><div class="entry-actions">${saveWordButton(annotation.sense_id)}<button class="secondary" data-save-context="${esc(annotation.sense_id)}" ${isSaved(annotation.sense_id)?'':'hidden'}>Guardar este fragmento para repaso</button><a class="secondary" href="#lexico/${esc(annotation.sense_id)}">Ver palabra y fuentes</a></div>${/^[\p{L}\p{M}]+$/u.test(annotation.quote)?'<div class="auto-analysis"></div>':''}</div></div>`;
}
