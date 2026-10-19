'use strict';
// Dioses y calendario: fichas por deidad, tonalpohualli (signo, numeral, trecena), veintenas, lecturas y unidad.
// Todo viene de /api/entities (nahuatl_local.entities): cada dato trae su fuente; lo automático se marca.

async function loadGods(){if(!state.gods)state.gods=await api('/api/entities');return state.gods;}
const godsCards=new Map();
function godsCard(id){if(!godsCards.has(id))godsCards.set(id,api('/api/entities/'+encodeURIComponent(id)).catch(e=>{godsCards.delete(id);throw e;}));return godsCards.get(id);}
const basisLabels={ordinal:'Número dado por la fuente',sequence:'Orden según una secuencia del archivo',gap:'Hueco entre veintenas con fuente'};
const roleLabels={night_lord:'Señor de la Noche',figure:'Figura de la lámina',attire:'Atavío o elemento'};
function godsSign(n){return state.gods.calendar.signs[n];}
function godsNumeral(n){return state.gods.calendar.numerals[n-1];}
function godsDayName(n,s){return `${godsNumeral(n).name} ${godsSign(s).name}`;}
function godsDayHref(n,s){return `#dioses/dia/${n}-${s}`;}
function godsDayAt(index){return {n:index%13+1,s:index%20};}
function godsIndexOf(n,s){for(let d=0;d<260;d++)if(d%13===n-1&&d%20===s)return d;return 0;}
function godsReview(review){return review?.status==='reviewed'?`<span class="unit-review reviewed">Revisado por ${esc(review.reviewer)} · ${esc(review.date)}</span>`:`<span class="unit-review automatic" title="Ninguna persona lo ha revisado todavía.">Borrador · sin revisar</span>`;}
function godsSource(s){
 const quote=s.kind==='passage'?` <q lang="nci">${esc(s.quote)}</q>`:s.gloss?` <q>${esc(String(s.gloss).slice(0,160))}</q>`:s.reading?` <q lang="nci">${esc(s.reading)}</q>`:'';
 const where=s.url?link(s.url,s.label):esc(s.label);
 return `<li class="gods-source">${where}${quote}<small>${esc(s.license||'')}${s.attribution?' · '+esc(s.attribution):''}${s.automatic?' · extracción automática':''}</small></li>`;
}
function godsSources(list,label='Fuentes'){return list?.length?`<details class="gods-sources"><summary>${esc(label)} · ${list.length}</summary><ul>${list.map(godsSource).join('')}</ul></details>`:'';}
function godsPassage(r){return `<article class="research-passage gods-passage"><div class="passage-meta"><span>${esc(r.variant_label)}</span><span>${esc(r.document||'Obra no indicada')}</span><span>${esc(r.id)}</span></div><p class="nah-passage" lang="nci">${r.form?askHighlightSafe(r.nah,r.form):esc(r.nah)}</p><p class="spanish-passage">${esc(r.es)}</p><p class="meta">${esc(r.verification)} · ${reportLink(r.id)}</p></article>`;}
function askHighlightSafe(text,form){const i=text.indexOf(form);return i<0?esc(text):`${esc(text.slice(0,i))}<mark>${esc(form)}</mark>${esc(text.slice(i+form.length))}`;}
function godsImage(row,caption){return row?.image&&typeof pictographicImage==='function'?pictographicImage(row,caption):'';}
function godsNav(view){
 const items=[['','Deidades'],['calendario','Calendario'],['veintenas','Veintenas'],['lecturas','Lecturas y unidad']];
 return `<nav class="pictographic-nav gods-nav" aria-label="Dioses y calendario">${items.map(([v,l])=>`<a href="#dioses${v?'/'+v:''}"${view===v?' aria-current="page"':''}>${l}</a>`).join('')}</nav>`;
}
function godsHeading(view){
 return heading('Dioses y calendario','Dioses, días y veintenas','Fichas de deidades con sus nombres en todas sus grafías, el tonalpohualli de 260 días y las 18 veintenas. Cada dato dice de dónde sale.')+godsNav(view)
  +`<p class="pilot-note">Fichas generadas por el proyecto desde el archivo, el diccionario, Wiktionary y Tlachia. Los atributos los redactó el proyecto con su fuente; ${godsReview(state.gods.review)}. Las imágenes son de Tlachia (UNAM) y se cargan desde su sitio.</p>`;
}
function godsTermLinks(name){const q=encodeURIComponent(name);return `<nav class="term-views" aria-label="Buscar ${esc(name)} en"><a href="#lexico/buscar/${q}">Índice de términos</a><a href="#preguntar/${q}">Preguntar</a><a href="#investigar/${q}">Archivo</a></nav>`;}

async function renderGods(id=''){
 let data;
 try{data=await loadGods();}catch(e){$('content').innerHTML=heading('Dioses y calendario','No se pudieron cargar las fichas',e.message);return;}
 if(route().page!=='dioses')return;
 const [view='',...rest]=id.split('/');
 if(view==='')return renderGodsIndex(data);
 if(view==='calendario')return renderGodsCalendar(data,rest.join('/'));
 if(view==='veintenas')return renderGodsVeintenas(data);
 if(view==='lecturas')return renderGodsReadings(data);
 if(view==='unidad')return renderGodsUnit();
 if(view==='dia'){const [n,s]=rest.join('').split('-').map(Number);if(n>=1&&n<=13&&s>=0&&s<=19)return renderGodsDay(n,s);}
 return renderGodsCard(view);
}

function renderGodsIndex(data){
 const kinds=[['deity','Deidades'],['figure','Figuras de las láminas'],['epithet','Epítetos'],['place','Lugares']];
 $('content').innerHTML=godsHeading('')+kinds.map(([k,label])=>{const rows=data.entities.filter(e=>e.kind===k);return rows.length?`<section class="gods-section"><div class="section-heading"><h2>${label}</h2><span class="meta">${rows.length}</span></div><div class="gods-grid">${rows.map(e=>`<article class="gods-card" data-entity="${esc(e.id)}"><p class="eyebrow">${esc(e.kind_label)}</p><h3><a href="#dioses/${esc(e.id)}" lang="nci">${esc(e.name)}</a></h3>${e.spellings.length>1?`<p class="gods-spellings" lang="nci">${e.spellings.slice(0,4).map(esc).join(' · ')}</p>`:''}<p>${esc(e.summary)}</p><p class="meta">${e.passages} pasajes · ${e.tlachia} registros de Tlachia</p></article>`).join('')}</div></section>`:'';}).join('');
}

function renderGodsCalendar(data,trecenaId){
 const c=data.calendar,k=Math.max(1,Math.min(20,Number((trecenaId||'').replace('trecena-',''))||1)),t=c.trecenas[k-1];
 const days=[...Array(13).keys()].map(i=>({n:i+1,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godsHeading('calendario')
  +`<section class="gods-section"><h2>Tonalpohualli · 260 días</h2><p>Cada día se nombra con un numeral del 1 al 13 y uno de los 20 signos; los dos avanzan juntos. Trece días forman una trecena.</p><ul class="gods-structure">${c.structure.map(s=>`<li>${esc(s.text)}${godsSources(s.sources,'Fuente')}</li>`).join('')}</ul><p class="meta">${esc(c.check.note)}</p></section>`
  +`<section class="gods-section" id="gods-trecena"><div class="section-heading"><h2>Trecena ${k} · <span lang="nci">${esc(t.name)}</span></h2><span class="meta">${t.pages.length?'Telleriano-Remensis f. '+t.pages.map(p=>esc(p.folio)).join(', '):'Sin lámina en el catálogo incorporado'}</span></div>
<div class="gods-pager"><a class="secondary" href="#dioses/calendario/trecena-${k===1?20:k-1}">← Trecena ${k===1?20:k-1}</a><label>Trecena <select id="gods-trecena-select">${c.trecenas.map(x=>`<option value="${x.n}"${x.n===k?' selected':''}>${x.n} · ${esc(x.name)}</option>`).join('')}</select></label><a class="secondary" href="#dioses/calendario/trecena-${k===20?1:k+1}">Trecena ${k===20?1:k+1} →</a></div>
<ol class="gods-days">${days.map(d=>{const info=c.days[`${d.n}-${d.s}`];return `<li><a href="${godsDayHref(d.n,d.s)}"><span class="gods-day-n">${d.n}</span> <strong lang="nci">${esc(godsDayName(d.n,d.s))}</strong> <small>${esc(godsSign(d.s).es)}</small>${info?`<small class="gods-day-data">${info.glyphs.length?'glifo':''}${info.glyphs.length&&info.passages_total?' · ':''}${info.passages_total?info.passages_total+' pasajes':''}</small>`:''}</a></li>`;}).join('')}</ol>
${t.figures.length?`<p>Figuras de sus láminas según Tlachia: ${t.figures.map(f=>`<a href="#dioses/${esc(f)}">${esc(data.entities.find(e=>e.id===f)?.name||f)}</a>`).join(' · ')}</p>`:'<p class="meta">El catálogo incorporado de Tlachia no tiene láminas de esta trecena.</p>'}
${t.night_lords.length?`<p class="meta">Señores de la Noche en sus láminas: ${t.night_lords.map(f=>`<a href="#dioses/${esc(f)}">${esc(data.entities.find(e=>e.id===f)?.name||f)}</a>`).join(' · ')}</p>`:''}</section>`
  +`<section class="gods-section"><h2>Los 20 signos</h2><div class="gods-signs">${c.signs.map((s,i)=>`<a class="gods-sign" href="#dioses/${esc(s.id)}"><span class="gods-day-n">${s.n}</span><strong lang="nci">${esc(s.name)}</strong><small>${esc(s.es)}</small></a>`).join('')}</div></section>`
  +`<section class="gods-section"><h2>Numerales del 1 al 13</h2><table class="unit-morphemes gods-numerals"><thead><tr><th>Número</th><th>Numeral</th><th>Otras grafías</th></tr></thead><tbody>${c.numerals.map(n=>`<tr><td>${n.n}</td><td lang="nci"><a href="#dioses/${esc(n.id)}">${esc(n.name)}</a></td><td lang="nci">${n.spellings.filter(x=>x!==n.name).slice(0,3).map(esc).join(', ')}</td></tr>`).join('')}</tbody></table></section>`;
 $('gods-trecena-select').onchange=e=>{location.hash='#dioses/calendario/trecena-'+e.target.value;};
}

function renderGodsVeintenas(data){
 $('content').innerHTML=godsHeading('veintenas')+`<section class="gods-section"><h2>Xiuhpohualli · 18 veintenas y nemontemi</h2><p>La cuenta del año: 18 veintenas de 20 días y unos días al final. Cada ficha dice de dónde sale su lugar en la serie y su nombre.</p><ol class="gods-veintenas">${data.calendar.veintenas.map(v=>`<li data-veintena="${esc(v.id)}"><a href="#dioses/${esc(v.id)}"><span class="gods-day-n">${v.kind==='nemontemi'?'+':v.n}</span> <strong lang="nci">${esc(v.name)}</strong></a> <small>${esc(basisLabels[v.position.basis])}${v.name_pending?' · nombre sin fuente todavía':''}${v.dedication?' · '+esc(v.dedication.label):''}</small></li>`).join('')}</ol></section>`;
}

function renderGodsReadings(data){
 $('content').innerHTML=godsHeading('lecturas')+`<section class="gods-section"><h2>Unidad · ${esc(data.unit.title)}</h2><p>${esc(data.unit.objective)}</p>${godsReview(data.unit.review)}<div class="entry-actions"><a class="primary" href="#dioses/unidad">Abrir la unidad</a></div></section>`
  +`<section class="proposed-readings"><h2>Lecturas de mitología en revisión</h2><p>Pasajes reales del archivo, elegidos por el proyecto, con ayudas generadas. Esperan revisión editorial antes de sumarse a Lecturas.</p>${data.readings.map(r=>`<details class="proposed-reading" data-proposed="${esc(r.id)}"><summary>${esc(r.title)} ${godsReview(r.review)}</summary><p>${esc(r.objective)}</p>${r.passages.map(p=>`<blockquote><p lang="nci">${esc(p.nah)}</p><p>${esc(p.es)}</p><p class="meta">${esc(p.document||'')} · ${esc(p.id)}</p></blockquote>`).join('')}</details>`).join('')}</section>`;
}

async function renderGodsUnit(){
 let data;try{data=await api('/api/calendar/unit');}catch(e){$('content').innerHTML=heading('Unidad','No se pudo cargar la unidad',e.message);return;}
 if(route().page!=='dioses')return;
 renderUnit(data.units[0],{back:'#dioses/lecturas',backLabel:'← Dioses y calendario',others:'#dioses/lecturas'});
}

async function renderGodsDay(n,s){
 let d;try{d=await api('/api/calendar/day?'+new URLSearchParams({n,sign:s}));}catch(e){$('content').innerHTML=heading('Día','No se pudo cargar el día',e.message);return;}
 if(route().page!=='dioses')return;
 const index=godsIndexOf(n,s),prev=godsDayAt((index+259)%260),next=godsDayAt((index+1)%260),sign=godsSign(s),t=state.gods.calendar.trecenas[d.trecena-1];
 $('content').innerHTML=`<a class="back-link" href="#dioses/calendario/trecena-${d.trecena}">← Trecena ${d.trecena}</a>`+heading('Día del tonalpohualli',godsDayName(n,s),`${n} ${sign.es} · día ${index+1} de 260 · trecena ${d.trecena} (${t.name}).`)
  +`<div class="gods-pager"><a class="secondary" href="${godsDayHref(prev.n,prev.s)}">← ${esc(godsDayName(prev.n,prev.s))}</a><a class="secondary" href="${godsDayHref(next.n,next.s)}">${esc(godsDayName(next.n,next.s))} →</a></div>`
  +`<p>Numeral: <a href="#dioses/numeral-${n}" lang="nci">${esc(godsNumeral(n).name)}</a> · Signo: <a href="#dioses/${esc(sign.id)}" lang="nci">${esc(sign.name)}</a></p>`
  +(d.glyph_rows.length?`<section class="gods-section"><h2>Glifo en el Telleriano-Remensis</h2><div class="gods-glyphs">${d.glyph_rows.map(g=>`<div>${godsImage(g,'Tlachia · '+g.reading+' · f. '+g.folio)}<p><a href="#glifos/ficha/${encodeURIComponent(g.id)}" lang="nci">${esc(g.reading)}</a> · f. ${esc(g.folio)}</p></div>`).join('')}</div></section>`:'<p class="meta">Sin glifo de este día en las láminas incorporadas de Tlachia.</p>')
  +`<section class="gods-section"><h2>En el archivo</h2>${d.rows.length?d.rows.map(r=>`${godsPassage(dict(r))}<p class="meta">${r.certain?'La traducción da el número':'Posible: la traducción no da el número'}${r.year?' · nombre de año':''}</p>`).join(''):'<p class="meta">Ningún pasaje clásico nombra este día.</p>'}${d.passages_total>d.rows.length?`<p class="meta">y ${d.passages_total-d.rows.length} pasajes más.</p>`:''}</section>`
  +godsTermLinks(godsDayName(n,s));
}
function dict(r){return {...r,form:r.text};}

async function renderGodsCard(eid){
 let e;try{e=await godsCard(eid);}catch(err){$('content').innerHTML=heading('Dioses y calendario','Ficha no encontrada',err.message)+'<a href="#dioses">Volver →</a>';return;}
 if(route().page!=='dioses')return;
 const back=`<a class="back-link" href="#dioses${e.id.startsWith('signo-')||e.id.startsWith('numeral-')||e.id.startsWith('trecena-')?'/calendario':e.id.startsWith('veintena-')?'/veintenas':''}">← Dioses y calendario</a>`;
 if(e.id.startsWith('signo-'))return godsSignCard(e,back);
 if(e.id.startsWith('veintena-'))return godsVeintenaCard(e,back);
 if(e.id.startsWith('numeral-'))return godsNumeralCard(e,back);
 if(e.id.startsWith('trecena-')){location.hash='#dioses/calendario/'+e.id;return;}
 const g=state.gods,figurePages=e.tlachia.filter(t=>t.role==='figure'),lords=e.tlachia.filter(t=>t.role==='night_lord'),attire=e.tlachia.filter(t=>t.role==='attire');
 const trecenas=g.calendar.trecenas.filter(t=>t.figures.includes(e.id)),veintenas=g.calendar.veintenas.filter(v=>v.dedication?.target===e.id);
 $('content').innerHTML=back+heading(e.kind_label,e.name,(o=>o.length?'También: '+o.join(', '):'')(e.names.filter(x=>norm(x)!==norm(e.name))))+godsReview(e.review)+` <span class="gods-report">${reportLink(e.id)}</span>`
  +`<div class="gods-columns"><section class="gods-section"><h2>Qué dicen las fuentes</h2>${e.attributes.length?`<ul class="gods-attributes">${e.attributes.map(a=>`<li><p>${esc(a.text)} ${a.written_by==='template'?'<span class="automatic-tag">Automático</span>':''}</p>${godsSources(a.sources)}</li>`).join('')}</ul>`:''}
${e.senses.length?`<h3>En el diccionario</h3><ul class="gods-attributes">${e.senses.map(s=>`<li>${esc(s.gloss)}${godsSources([s],'Fuente')}</li>`).join('')}</ul>`:''}
${e.epithets.length?`<h3>Otros nombres</h3><ul class="gods-attributes">${e.epithets.map(x=>`<li lang="nci">${esc(x.name)}${godsSources(x.sources,'Fuente')}</li>`).join('')}</ul>`:''}
${e.relations.length?`<h3>Relaciones</h3><ul class="gods-attributes">${e.relations.map(r=>`<li><a href="#dioses/${esc(r.target)}">${esc(g.entities.find(x=>x.id===r.target)?.name||r.target)}</a> · ${esc(r.text)}${godsSources(r.sources,'Fuente')}</li>`).join('')}</ul>`:''}
${trecenas.length||veintenas.length?`<h3>En el calendario</h3><ul class="gods-attributes">${trecenas.map(t=>`<li>Figura de las láminas de la <a href="#dioses/calendario/${esc(t.id)}">trecena ${t.n} · ${esc(t.name)}</a> (Tlachia)</li>`).join('')}${veintenas.map(v=>`<li>Veintena dedicada: <a href="#dioses/${esc(v.id)}" lang="nci">${esc(v.name)}</a>${godsSources(v.dedication.sources,'Fuente')}</li>`).join('')}</ul>`:''}
${e.note?`<p class="pilot-note">${esc(e.note)}</p>`:''}</section>
<section class="gods-section"><h2>Nombres y grafías</h2>${e.spellings.length?`<ul class="term-spellings">${e.spellings.map(s=>`<li><strong lang="nci">${esc(s.form)}</strong> <span class="term-count">${s.total}</span></li>`).join('')}</ul>`:'<p class="meta">El archivo no tiene este nombre.</p>'}<p class="meta">Grafías con la misma clave del índice de términos; las búsquedas de cualquiera de ellas llevan a esta ficha.</p>${godsTermLinks(e.names[0])}
${figurePages.length||attire.length||lords.length?`<h2>En el Telleriano-Remensis (Tlachia)</h2>${figurePages.map(t=>`<div>${godsImage(t,'Tlachia · '+t.reading+' · f. '+t.folio)}<p><a href="#glifos/ficha/${encodeURIComponent(t.id)}" lang="nci">${esc(t.reading)}</a> · f. ${esc(t.folio)}</p></div>`).join('')}${lords.length?`<p>${esc(roleLabels.night_lord)}: ${[...new Set(lords.map(t=>t.folio))].map(f=>{const t=lords.find(x=>x.folio===f);return `<a href="#glifos/ficha/${encodeURIComponent(t.id)}">f. ${esc(f)}</a>`;}).join(' · ')}</p>`:''}${attire.length?`<details><summary>${attire.length} atavíos o elementos registrados</summary><ul>${attire.map(t=>`<li><a href="#glifos/ficha/${encodeURIComponent(t.id)}" lang="nci">${esc(t.item)}</a> · f. ${esc(t.folio)}</li>`).join('')}</ul><p class="meta">Lecturas de Tlachia, sin traducir.</p></details>`:''}`:''}</section></div>`
  +`<section class="gods-section"><h2>Pasajes del archivo</h2><p class="meta">${e.passages.total} pasajes nombran a ${esc(e.name)}${e.passages.restricted?` · ${e.passages.restricted} de una obra que espera permiso no se muestran`:''}.</p>${(e.passages.rows||[]).map(godsPassage).join('')}</section>`;
}

function godsSignCard(e,back){
 $('content').innerHTML=back+heading('Signo del tonalpohualli',`${e.n} · ${e.name}`,`«${e.es}»`)+godsReview(e.review)
  +`<section class="gods-section"><h2>Glosa</h2><ul class="gods-attributes">${e.gloss_sources.map(s=>`<li>${esc(s.gloss)}${godsSources([s],'Fuente')}</li>`).join('')}</ul><p class="meta">Grafías: <span lang="nci">${e.spellings.map(esc).join(', ')}</span></p>${godsTermLinks(e.name)}</section>`
  +`<section class="gods-section"><h2>Glifos en el Telleriano-Remensis</h2><div class="gods-glyphs">${e.glyphs.map(g=>`<div>${godsImage(g,'Tlachia · '+g.reading+' · f. '+g.folio)}<p><a href="${godsDayHref(g.n,g.sign)}" lang="nci">${esc(g.reading)}</a> · f. ${esc(g.folio)}</p></div>`).join('')}</div></section>`
  +`<section class="gods-section"><h2>Días con este signo</h2><div class="gods-signs">${[...Array(13).keys()].map(i=>`<a class="gods-sign" href="${godsDayHref(i+1,e.n-1)}"><span class="gods-day-n">${i+1}</span><strong lang="nci">${esc(godsDayName(i+1,e.n-1))}</strong></a>`).join('')}</div><p class="meta">${e.archive_names.total} nombres calendáricos en el archivo (${e.archive_names.certain} con el número en la traducción).</p></section>`;
}
function godsNumeralCard(e,back){
 $('content').innerHTML=back+heading('Numeral',`${e.n} · ${e.name}`,`Grafías: ${e.spellings.join(', ')}`)+godsReview(e.review)+godsSources(e.sources)
  +`<p class="meta">${e.archive_names} nombres calendáricos del archivo usan este numeral.</p><div class="gods-signs">${[...Array(20).keys()].map(s=>`<a class="gods-sign" href="${godsDayHref(e.n,s)}"><strong lang="nci">${esc(godsDayName(e.n,s))}</strong></a>`).join('')}</div>`;
}
function godsVeintenaCard(e,back){
 const p=e.passages;
 $('content').innerHTML=back+heading(e.kind==='nemontemi'?'Días finales del año':'Veintena '+e.n,e.name,e.spellings.length>1?'Grafías: '+e.spellings.join(', '):'')+godsReview(e.review)
  +`<section class="gods-section"><h2>Lugar en la serie</h2><p>${esc(basisLabels[e.position.basis])}${e.position.text?': '+esc(e.position.text):''}</p>${godsSources(e.position.sources)}
<h2>Nombre</h2>${e.name_pending?'<p class="pilot-note">Ninguna fuente abierta incorporada da este nombre todavía: queda pendiente de fuente.</p>':godsSources(e.name_sources,'Dónde aparece el nombre')}
${e.dedication?`<h2>Dedicada a</h2><p>${e.dedication.target?`<a href="#dioses/${esc(e.dedication.target)}">${esc(e.dedication.label)}</a>`:esc(e.dedication.label)}</p>${godsSources(e.dedication.sources,'Fuente')}`:''}
${e.note?`<p class="pilot-note">${esc(e.note)}</p>`:''}${e.tlachia.length?`<p>Tlachia: ${e.tlachia.map(t=>`<a href="#glifos/ficha/${encodeURIComponent(t.id)}" lang="nci">${esc(t.reading)}</a> · f. ${esc(t.folio)}`).join(' · ')}</p>`:''}${godsTermLinks(e.name)}</section>`
  +`<section class="gods-section"><h2>Pasajes del archivo</h2>${p.certain_rows.map(godsPassage).join('')||'<p class="meta">Ningún pasaje clásico la nombra.</p>'}${p.uncertain_rows.length?`<details class="term-uncertain"><summary>${p.uncertain_total} pasajes donde la palabra puede ser otra cosa</summary>${p.uncertain_rows.map(godsPassage).join('')}</details>`:''}</section>`;
}

// En Preguntar: si la consulta nombra una deidad, un signo, una veintena o un día, enlaza su ficha.
async function fillEntityBanner(slot,query){
 if(!slot||!query)return;
 let r;try{r=await api('/api/entity-search?'+new URLSearchParams({q:query}));}catch{return;}
 if(!slot.isConnected||!r.matches.length)return;
 slot.innerHTML=`<aside class="entity-banner"><p class="eyebrow">Dioses y calendario</p>${r.matches.map(m=>`<a href="#dioses/${esc(m.id)}" lang="nci">${esc(m.name)}</a> <small>${esc(m.why)}</small>`).join('<br>')}</aside>`;
 slot.hidden=false;
}
// En la portada de Lecturas: el paso a la sección.
async function fillGodsTeaser(slot){
 if(!slot)return;let data;try{data=await loadGods();}catch{return;}
 if(!slot.isConnected)return;
 slot.innerHTML=`<div class="section-heading"><h2>Dioses y calendario</h2><span class="meta">${data.entities.filter(e=>e.kind==='deity').length} deidades · 20 signos · 18 veintenas · borradores sin revisar</span></div><p>Huitzilopochtli, Quetzalcóatl, Tláloc y los demás en sus pasajes y en las láminas del Telleriano-Remensis; el tonalpohualli día por día.</p><div class="entry-actions"><a class="primary" href="#dioses">Ver las fichas</a><a class="secondary" href="#dioses/calendario">Abrir el calendario</a></div>`;
 slot.hidden=false;
}

