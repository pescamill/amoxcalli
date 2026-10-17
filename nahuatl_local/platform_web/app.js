'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Único plegado del navegador (equivale a text.fold): minúsculas y sin marcas diacríticas. Lo comparten todos los módulos.
const norm=s=>String(s??'').toLowerCase().normalize('NFD').replace(/\p{Mn}/gu,'');
const state={records:[],byId:{},variants:[],profile:null,model:false,filter:{q:'',period:'',variant:'',sourceType:''}};
const kindNames={source:'Fuente',sense:'Acepción',form:'Forma léxica',text:'Texto',glyph:'Referencia glífica',note:'Nota de investigación'};
const statuses={inherited:'Referencia heredada · por cotejar',catalog_checked:'Ficha consultada · sin cotejo primario',reviewed:'Revisión registrada'};
const sourceTypes={primary:'Fuente primaria',edition:'Edición',research:'Investigación',catalog:'Catálogo',community:'Testimonio comunitario'};
const periods={historical:'Histórico',modern:'Contemporáneo',unknown:'Por identificar'};
const variationNames={historical:'Testimonio histórico',dialectal:'Variación dialectal',orthographic:'Variación ortográfica',unspecified:'Relación por revisar'};
async function api(url,options={}){const slow=preparing.watch(url);try{const r=await fetch(url,options);const d=await r.json();if(!r.ok)throw Error(d.error||'No se pudo completar la solicitud.');return d;}finally{slow&&preparing.done(slow);}}
// Arranque en frío: si una consulta de análisis tarda, se muestra el avance de /api/system en lugar de una espera muda.
const preparing={waiting:new Set(),timer:0,poll:0,
 watch(url){if(!/^\/api\/(word|gloss|ask|research|terms|units|corpus|learning|pictography)\b/.test(url))return null;const t={};this.waiting.add(t);if(!this.timer)this.timer=setTimeout(()=>this.show(),700);return t;},
 done(t){this.waiting.delete(t);if(!this.waiting.size){clearTimeout(this.timer);clearTimeout(this.poll);this.timer=this.poll=0;if($('preparing'))$('preparing').hidden=true;}},
 async show(){if(!this.waiting.size)return;const first=$('preparing');if(first&&first.hidden&&!this.poll){first.innerHTML='<strong>Preparando el análisis…</strong><small>Solo la primera vez en esta instalación.</small>';first.hidden=false;}let p;try{p=(await (await fetch('/api/system')).json()).preparation;}catch{}
  if(!this.waiting.size||!globalThis.document)return;const box=$('preparing');if(!box)return;  // la página pudo cerrarse durante la espera
  if(p&&!p.ready){const now=p.stages.find(s=>s.state==='building')||p.stages.find(s=>s.state!=='ready');
   box.innerHTML=`<strong>Preparando el análisis…</strong> <span>${p.done} de ${p.total}${now?' · '+esc(now.label):''}</span><progress max="${p.total}" value="${p.done}"></progress><small>Solo la primera vez en esta instalación.</small>`;box.hidden=false;}
  else if(p){box.hidden=true;return;}  // ya preparado: la espera era de la consulta, no del arranque
  this.poll=setTimeout(()=>this.show(),800);}};
// Respuesta servida antes de que existan las pistas de glosa: se dice, y no se guarda en caché.
const preparingHintsHTML=d=>d?.preparing?.includes('gloss_hints')?'<p class="meta preparing-hints">Las pistas de las traducciones se están preparando; aparecerán al volver a abrir la palabra.</p>':'';
function toast(message){$('notice').textContent=message;$('notice').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('notice').hidden=true,5000);}
function download(name,value,mime='application/json'){const a=document.createElement('a');const u=URL.createObjectURL(new Blob([typeof value==='string'?value:JSON.stringify(value,null,2)],{type:mime}));a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
function link(url,label){try{const u=new URL(url);if(!['http:','https:'].includes(u.protocol))return '';}catch{return '';}return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;}
function badge(r){return `<span class="pill ${r.verification==='reviewed'?'':'proposed'}">${esc(statuses[r.verification]||r.verification)}</span>`;}
function sourceCitations(r){return (r.evidence||[]).map(e=>{const s=state.byId[e.source_id],via=state.byId[e.via_source_id];return `<div class="source-citation"><a href="#fuentes/${esc(e.source_id)}">${esc(s?.label||e.source_id)}</a> · ${esc(e.locator)}${via?`<small>Consultado a través de <a href="#fuentes/${esc(via.id)}">${esc(via.label)}</a></small>`:''}<small>${e.status==='primary_checked'?`Cotejo primario declarado por ${esc(e.checked_by)} · ${esc(e.checked_at)}`:e.status==='catalog_checked'?'Se comprobó la ficha secundaria; falta cotejar el original.':'Referencia importada; no cotejada nuevamente.'}</small></div>`;}).join('');}
function originLabel(r){return r?.import_source==='wiktionary'?`Wiktionary${r.gloss_language==='en'?' (acepción en inglés)':''} · CC BY-SA · extracción automática`:'Molina / GDN · extracción automática';}
function rightsLine(r){const x=r?.rights||{};return `<p class="meta rights-line">${x.license?`Licencia: ${x.license_url?link(x.license_url,x.license):esc(x.license)} · `:''}${esc(x.note||'')}${x.attribution?`<br>Atribución: ${esc(x.attribution)}`:''}</p>`;}
function heading(kicker,title,description,count=''){return `<div class="page-heading"><div><p class="eyebrow">${esc(kicker)}</p><h1>${esc(title)}</h1><p class="intro">${esc(description)}</p></div>${count?`<span class="counter">${esc(count)}</span>`:''}</div>`;}
function variantsOptions(){return `<option value="">Todas las variantes</option><option value="nci">Náhuatl histórico</option>`+state.variants.map(v=>`<option value="${esc(v.id)}">${esc(v.label)}</option>`).join('')+[...new Set(state.records.map(r=>r.variant).filter(v=>v&&v.startsWith('custom:')))].map(v=>`<option value="${esc(v)}">${esc(v.slice(7))}</option>`).join('');}
// Filtros de una lista (Diccionario, Fuentes, Fichas textuales). El texto viene de la búsqueda global (#search).
function toolbar(type){return `<div class="toolbar">${type==='fuentes'?`<label class="source-filter">Tipo de fuente<select id="source-type"><option value="">Todos los tipos</option>${Object.entries(sourceTypes).map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select></label>`:`<label>Época<select id="period"><option value="">Todas las épocas</option><option value="historical">Histórico</option><option value="modern">Contemporáneo</option><option value="unknown">Por identificar</option></select></label><label>Variante<select id="variant">${variantsOptions()}</select></label>`}</div>`;}
function filterRecord(r){return (!state.filter.period||r.period===state.filter.period)&&(!state.filter.variant||r.variant===state.filter.variant);}
function includes(text){return norm(state.filter.q).split(/\s+/).every(t=>norm(text).includes(t));}
function bindToolbar(renderResults){$('search').oninput=e=>{state.filter.q=e.target.value;renderResults();};for(const [id,key] of [['period','period'],['variant','variant'],['source-type','sourceType']]){const el=$(id);if(el){el.value=state.filter[key];el.onchange=()=>{state.filter[key]=el.value;renderResults();};}}}
function route(){const hash=location.hash.slice(1)||'aprender',separator=hash.indexOf('?'),path=separator<0?hash:hash.slice(0,separator);const [page='aprender',...parts]=path.split('/');return {page,id:parts.join('/'),params:new URLSearchParams(separator<0?'':hash.slice(separator+1))};}
async function reloadData(){const [d,learning]=await Promise.all([api('/api/corpus'),api('/api/learning')]);state.learning=learning;try{state.pictography=await api('/api/pictography');state.pictographyError='';}catch(e){state.pictography=null;state.pictographyError=e.message;}state.dictionaryFeatured=d.dictionary_featured_ids||[];state.records=d.records;state.byId=Object.fromEntries(d.records.map(r=>[r.id,r]));state.variants=d.variants;state.archive=d.archive;$('corpus-count').textContent=`${d.archive.total.toLocaleString('es-MX')} pares · ${d.count.toLocaleString('es-MX')} fichas del catálogo`;}
async function exportAll(){try{download('amoxcalli-corpus.json',await api('/api/corpus/export'));}catch(e){toast(e.message);}}
function passageHTML(r){return `<article class="research-passage"><div class="passage-meta"><span>${esc(r.variant_label)}</span><span>${esc(r.document||'Obra no indicada')}</span></div><p class="nah-passage">${esc(r.nah)}</p><p class="spanish-passage">${esc(r.es)}</p><details><summary>Fuente y contexto</summary><p>${esc(r.locator)} · ${esc(r.verification)}</p>${link(r.source_url,'Consultar distribución original')}<p class="meta">${esc(r.rights_note)}</p></details><div class="card-actions"><button class="link-button save-passage" data-id="${esc(r.id)}">Descargar ficha</button><a href="#extraer/${esc(r.id)}">Aportar cotejo</a></div></article>`;}
function bindPassageDownloads(container,rows){container.querySelectorAll('.save-passage').forEach(b=>b.onclick=()=>download(b.dataset.id+'.json',rows.find(r=>r.id===b.dataset.id)));}
// Búsqueda global: la única caja de texto de la aplicación. En Diccionario, Fuentes y Fichas textuales
// filtra la lista mientras se escribe; en las demás secciones, al enviarla, Preguntar muestra el término
// (sus grafías, glifos, pasajes y fichas con sus originales) con enlaces a Diccionario y Archivo.
const liveSearch={lexico:'Busca en el diccionario: agua, atl, árbol…',fuentes:'Busca título, autor o institución…',textos:'Busca en los textos…'};
const ownSearch=new Set(['investigar']);// herramienta avanzada con su propio formulario
const searchPlaceholder='Busca una palabra: xochitl, agua, kuali…';
const pageTitles={unidades:'Unidades',aprender:'Lecturas',leer:'Leer',palabras:'Mis palabras',grafias:'Grafías',lexico:'Diccionario',preguntar:'Preguntar',glifos:'Glifos',investigar:'Archivo',modelos:'Laboratorio (histórico)',proyecto:'Proyecto',taller:'Ficha para taller',textos:'Fichas textuales',extraer:'Aportar evidencia',opciones:'Opciones'};
// Cada sección vive en su módulo; se resuelven al navegar, cuando todos ya se cargaron. «consultar» solo redirige
// los enlaces anteriores a Consultar fichas, que ahora vive dentro de Preguntar.
const renderers={aprender:id=>renderLearn(id),grafias:id=>renderSpellings(id),unidades:id=>renderUnits(id),leer:id=>renderReader(id),proyecto:()=>renderProject(),taller:id=>renderWorkshop(id),palabras:()=>renderSaved(),glifos:id=>renderPictography(id),preguntar:id=>renderAsk(id),consultar:()=>{location.replace(location.hash.replace('#consultar','#preguntar'));},investigar:id=>renderArchive(id),opciones:()=>renderSettings(),textos:id=>renderTexts(id),fuentes:id=>renderSources(id),extraer:id=>renderExtract(id),modelos:()=>renderModels(),lexico:id=>renderDictionary(id)};
// Escuchas de la página actual sobre elementos permanentes (búsqueda global); se retiran al cambiar de página.
let pageSignal=new AbortController();
function decodeHash(value){try{return decodeURIComponent(value);}catch{return value;}}
function prepareGlobalSearch(page,id){
 const input=$('search');input.oninput=null;
 input.placeholder=liveSearch[page]||searchPlaceholder;
 input.value=page==='lexico'&&id.startsWith('buscar/')?decodeHash(id.slice(7)):liveSearch[page]?state.filter.q:page==='preguntar'?decodeHash(id):'';
 document.body.classList.toggle('has-own-search',ownSearch.has(page));
}
$('global-search').onsubmit=e=>{
 e.preventDefault();const q=$('search').value.trim(),{page}=route();
 if(!q||page==='fuentes'||page==='textos')return;// ya filtrado al escribir
 location.hash=(page==='lexico'?'lexico/buscar/':'preguntar/')+encodeURIComponent(q);
};
function markNavigation(page){
 document.querySelectorAll('[data-page]').forEach(a=>{if(a.dataset.page===page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 const more=$('more-menu');more.open=false;more.classList.toggle('current',!!more.querySelector(`[data-page="${page}"]`));
}
let pageBefore='';
async function render(){
 const {page,id}=route();
 pageSignal.abort();pageSignal=new AbortController();
 document.body.classList.toggle('workshop-view',page==='taller');
 if(page!==pageBefore||id){state.filter={q:'',period:'',variant:'',sourceType:''};pageBefore=page;}
 markNavigation(page);prepareGlobalSearch(page,id);
 document.title='Amoxcalli · '+(pageTitles[page]||'Fuentes');
 try{await (renderers[page]||renderers.lexico)(id);appendSourceCredits();}
 catch(e){$('content').innerHTML=`<div class="global-error"><h1>No se pudo abrir esta sección</h1><p>${esc(e.message)}</p><button class="secondary" id="retry">Volver a intentar</button></div>`;$('retry').onclick=render;}
}
$('export-all').onclick=exportAll;
// El menú «Más» se cierra al elegir, al pulsar fuera o con Escape.
document.addEventListener('click',e=>{const more=$('more-menu');if(more.open&&!more.contains(e.target))more.open=false;});
document.addEventListener('keydown',e=>{const more=$('more-menu');if(e.key==='Escape'&&more.open){more.open=false;more.querySelector('summary').focus();}});
// Hasta que llegan los datos iniciales, un cambio de ruta solo espera: el primer render ya lee la ruta actual.
window.addEventListener('hashchange',()=>{if(state.booted)render();});
// Todos los módulos (defer) ya se ejecutaron en DOMContentLoaded.
document.addEventListener('DOMContentLoaded',()=>reloadData().then(()=>{state.booted=true;return render();}).catch(e=>{$('loading').textContent='No se pudo abrir el corpus: '+e.message;}));
