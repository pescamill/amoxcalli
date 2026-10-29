'use strict';
// Aclarar: un toque para decir qué no cuadra; el contexto lo pone la app. Se guarda aquí y solo sale si la persona lo comparte.
const ACLARAR={categories:{
 traduccion:'La traducción no corresponde',analisis:'La división o el análisis de la palabra',grafia:'Una palabra está mal escrita',
 fuente:'La obra, la página o la fuente no coincide',uso:'En mi variante o comunidad se dice distinto',duda:'No lo entiendo: tengo una duda'},
 bases:{intuicion:'No estoy seguro; me llamó la atención',fuente:'Lo leí en una fuente',hablante:'Hablo una variante actual',estudio:'Estudio o enseño náhuatl clásico'}};
const ACLARACION_MARK='<!-- amoxcalli:aclaracion -->';

// El texto que la persona veía: el pasaje más cercano al botón.
function aclararContext(button){
 let node=button;for(let i=0;i<6&&node;i++,node=node.parentElement){
  const nah=node.querySelector?.('.nah-passage,.guided-passage,h1[lang="nci"]');
  if(nah){const es=node.querySelector('.spanish-passage,.reading-translation,.dictionary-entry-head h2');return {nah:nah.textContent.trim().slice(0,600),es:(es?.textContent||'').trim().slice(0,600)};}}
 return {nah:'',es:''};
}

function aclaracionIssue(a){
 const body=[`**${ACLARAR.categories[a.category]}** en \`${a.target}\``,a.note,a.proposal?`Propone: ${a.proposal}`:'',
  `Cómo lo sabe: ${ACLARAR.bases[a.basis]}${a.variant?' ('+a.variant+')':''}${a.citation?' · '+a.citation:''}`,
  '',ACLARACION_MARK,'```json',JSON.stringify({target:a.target,category:a.category,basis:a.basis,note:a.note,proposal:a.proposal,citation:a.citation,variant:a.variant,context:a.context}),'```'].filter((l,i)=>l||i>=4).join('\n');
 return REPORT_URL+'?'+new URLSearchParams({title:`[Aclaración] ${a.target} · ${ACLARAR.categories[a.category]}`,body,labels:'aclaración'});
}
function aclaracionText(a){return `Aclaración para Amoxcalli\n${ACLARAR.categories[a.category]} · ${a.target}\n${a.note||''}\n${a.proposal?'Propone: '+a.proposal+'\n':''}\n${ACLARACION_MARK}\n\`\`\`json\n${JSON.stringify(a)}\n\`\`\``;}

function aclararShare(a,saved){
 return `<p class="aclarar-done">${saved?'<strong>Guardado en esta computadora.</strong> ':''}¿Lo compartes con el proyecto? Llega ordenado: con el pasaje, lo que viste y tu propuesta.</p>
 <div class="entry-actions"><a class="primary" href="${esc(aclaracionIssue(a))}" target="_blank" rel="noopener noreferrer">Enviar por GitHub ↗</a><button type="button" class="secondary" data-aclarar-copy>Copiar para enviarlo por otro medio</button></div>
 <p class="meta">GitHub pide una cuenta gratuita; tu usuario quedará en el historial de la corrección. Si prefieres no usarla, copia el texto y envíalo por correo o mensaje a quien coordine tu grupo.</p>`;
}

function openAclarar(target,context){
 let dialog=$('aclarar-dialog');
 if(!dialog){dialog=document.createElement('dialog');dialog.id='aclarar-dialog';dialog.className='aclarar-dialog';document.body.append(dialog);}
 dialog.innerHTML=`<form method="dialog" class="aclarar-form"><header><p class="eyebrow">Aclarar · ${esc(target)}</p><h2>¿Qué no cuadra?</h2>${context.nah?`<p class="aclarar-quote" lang="nci">${esc(context.nah.slice(0,160))}${context.nah.length>160?'…':''}</p>`:''}</header>
 <fieldset class="aclarar-chips"><legend class="sr-only">Qué pasa</legend>${Object.entries(ACLARAR.categories).map(([k,l])=>`<label><input type="radio" name="category" value="${k}" required><span>${esc(l)}</span></label>`).join('')}</fieldset>
 <div class="aclarar-more" hidden>
  <label><span>En una frase, qué observas <small>(opcional)</small></span><textarea name="note" maxlength="1000" rows="2"></textarea></label>
  <label><span>Qué propones <small>(opcional)</small></span><input name="proposal" maxlength="600"></label>
  <fieldset class="aclarar-basis"><legend>Cómo lo sabes</legend>${Object.entries(ACLARAR.bases).map(([k,l],i)=>`<label><input type="radio" name="basis" value="${k}" ${i?'':'checked'}><span>${esc(l)}</span></label>`).join('')}</fieldset>
  <label data-when="fuente" hidden><span>Obra y página</span><input name="citation" maxlength="300" placeholder="Molina 1571, f. 23v"></label>
  <label data-when="hablante" hidden><span>Tu variante, como tú la nombras</span><input name="variant" maxlength="120" placeholder="Náhuatl de la Huasteca, mexicano de Milpa Alta…"></label>
 </div>
 <p class="meta">Se guarda solo en esta computadora; tú decides si lo compartes. No pedimos nombre, correo ni ubicación. <a href="#cuidado" data-close>Cómo cuidamos la lengua</a></p>
 <div class="entry-actions"><button type="button" class="primary" data-save disabled>Guardar aclaración</button><button type="button" class="link-button" data-close>Cancelar</button></div></form>`;
 const form=dialog.querySelector('form'),more=dialog.querySelector('.aclarar-more'),save=form.querySelector('[data-save]');
 const close=()=>dialog.open&&(dialog.close?dialog.close():dialog.removeAttribute('open'));
 dialog.onclick=e=>{if(e.target.closest('[data-close]'))close();};
 form.onsubmit=e=>e.preventDefault();
 form.onchange=()=>{const f=new FormData(form);more.hidden=!f.get('category');save.disabled=!f.get('category');
  form.querySelectorAll('[data-when]').forEach(l=>l.hidden=l.dataset.when!==f.get('basis'));};
 save.onclick=async()=>{
  const f=Object.fromEntries(new FormData(form));
  const a={target,category:f.category,basis:f.basis,note:f.note||'',proposal:f.proposal||'',citation:f.basis==='fuente'?f.citation||'':'',variant:f.basis==='hablante'?f.variant||'':'',context:{...context,route:location.hash}};
  let saved=null;try{saved=await api('/api/aclaraciones',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(a)});}catch(error){toast(error.message);}
  form.innerHTML=`<header><p class="eyebrow">Aclarar · ${esc(target)}</p><h2>Gracias por mirar con cuidado</h2></header>${aclararShare(saved||a,!!saved)}<div class="entry-actions"><a href="#aclaraciones" data-close>Ver mis aclaraciones</a><button type="button" class="link-button" data-close>Listo</button></div>`;
  bindAclararCopy(form,saved||a);};
 if(dialog.showModal)dialog.showModal();else dialog.setAttribute('open','');
 dialog.querySelector('input[name=category]').focus();
}
function bindAclararCopy(root,a){root.querySelectorAll('[data-aclarar-copy]').forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(aclaracionText(a));toast('Copiado. Pégalo en un correo o mensaje.');}catch{toast('Tu navegador no permitió copiar.');}});}

document.addEventListener('click',e=>{const b=e.target.closest?.('[data-aclarar]');if(!b)return;e.preventDefault();openAclarar(b.dataset.aclarar,aclararContext(b));});

async function renderAclaraciones(){
 const head=heading('Mis aclaraciones','Lo que has señalado','Se guardan en esta computadora. Compártelas cuando quieras; nada se corrige solo: una persona coteja cada una con su fuente.');
 let items=[];try{items=(await api('/api/aclaraciones')).items.reverse();}catch(e){$('content').innerHTML=head+`<p class="empty">${esc(e.message)}</p>`;return;}
 $('content').innerHTML=head+(items.length?`<div class="entry-actions"><button class="secondary" id="aclaraciones-download">Descargar todas (.json)</button></div><div class="aclaraciones-list">${items.map(a=>`<article class="card aclaracion-item" data-id="${esc(a.id)}"><p class="eyebrow">${esc(ACLARAR.categories[a.category]||a.category)} · ${esc(a.created.slice(0,10))}</p>${a.context?.nah?`<p lang="nci">${esc(a.context.nah.slice(0,200))}</p>`:''}${a.note?`<p>${esc(a.note)}</p>`:''}${a.proposal?`<p><strong>Propones:</strong> ${esc(a.proposal)}</p>`:''}<p class="meta"><code>${esc(a.target)}</code> · ${esc(ACLARAR.bases[a.basis]||'')}${a.variant?' · '+esc(a.variant):''}${a.citation?' · '+esc(a.citation):''}</p>${aclararShare(a,false)}<button class="link-button" data-remove>Borrar</button></article>`).join('')}</div>`
  :`<p class="empty">Aún no hay aclaraciones. En cualquier pasaje, palabra o ficha toca <strong>Aclarar</strong>.</p>`);
 $('aclaraciones-download')?.addEventListener('click',()=>download('mis-aclaraciones.json',{schema:'amoxcalli.aclaracion/1',items}));
 $('content').querySelectorAll('.aclaracion-item').forEach(card=>{const a=items.find(i=>i.id===card.dataset.id);bindAclararCopy(card,a);
  card.querySelector('[data-remove]').onclick=async()=>{try{await api('/api/aclaraciones/'+encodeURIComponent(a.id),{method:'DELETE'});card.remove();toast('Aclaración borrada de esta computadora.');}catch(e){toast(e.message);}};});
}

function renderCuidado(){
 $('content').innerHTML=heading('Cómo cuidamos la lengua','No rescatamos: acompañamos.','El náhuatl está vivo: lo hablan más de 1.6 millones de personas en México (INEGI, Censo 2020). Este cuaderno lee el náhuatl clásico de documentos de los siglos XVI y XVII. Leer esos textos y escuchar a quienes hablan hoy pide reglas claras.')+`
 <div class="care-grid">${[
  ['Primero el permiso, después los datos','En Voces, cada envío separa el permiso de revisión, la autoría y el uso para entrenar (texto y voz por separado). Las casillas de entrenamiento empiezan sin marcar.'],
  ['Lo tuyo sigue siendo tuyo','Aclaraciones y aportes se guardan en tu computadora. Tú decides si los compartes; puedes descargarlos y retirarlos cuando quieras.'],
  ['Sin datos personales','No pedimos nombre real, correo ni ubicación. Los perfiles de Voces son seudónimos.'],
  ['Cada fuente con su crédito y su licencia','El código es MIT; los textos, imágenes y testimonios conservan sus propias condiciones. Lo reservado no se redistribuye. Ver <a href="#fuentes">Fuentes</a>.'],
  ['La comunidad decide sobre su variante','Tu variante se registra como tú la nombras. No se mezcla el náhuatl de hoy con el clásico, y lo que aporta una comunidad no se publica en abierto ni entrena modelos fuera del proyecto sin acuerdo con ella.'],
  ['Una persona revisa, con la fuente','Las herramientas ordenan y comparan; no deciden. Nada se aprueba solo ni por mayoría: cada cambio se coteja con su fuente y queda registrado con su motivo.'],
 ].map(([t,d])=>`<section class="card"><h2>${t}</h2><p>${d}</p></section>`).join('')}</div>
 <section class="project-section"><h2>Qué pasa con una aclaración</h2><ol class="care-flow"><li><strong>Tocas «Aclarar»</strong> en el pasaje, la palabra o la ficha.</li><li><strong>Eliges qué pasa</strong> con un toque. Si quieres, agregas una frase, una propuesta y cómo lo sabes.</li><li><strong>Se guarda aquí</strong> con su contexto ya puesto: ID, el texto que viste y la versión.</li><li><strong>Si la compartes, llega ordenada</strong>: se etiqueta sola, se comprueba que el pasaje exista, se pone junto al registro actual y se detectan las repetidas.</li><li><strong>Una persona la coteja</strong> con la fuente. Si se confirma, se corrige y queda en el historial. Si toca una variante actual, la revisan hablantes de esa variante.</li></ol><div class="entry-actions"><a class="secondary" href="#aclaraciones">Mis aclaraciones</a><a href="/aportar">Aportar tu voz (Voces)</a></div></section>
 <section class="project-section"><h2>En qué nos apoyamos</h2><p>${link('https://www.gida-global.org/careprinciples','Principios CARE para la gobernanza de datos indígenas')} · ${link('https://normlex.ilo.org/dyn/nrmlx_es/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C169','Convenio 169 de la OIT')} · ${link('https://www.diputados.gob.mx/LeyesBiblio/ref/lgdlpi.htm','Ley General de Derechos Lingüísticos de los Pueblos Indígenas')} · ${link('https://www.inali.gob.mx/sitios/clin-inali/html/l_nahuatl.html','Catálogo de variantes del INALI')}</p><p class="meta">Son referencias para el diseño; no implican aval de ninguna institución.</p></section>`;
}
