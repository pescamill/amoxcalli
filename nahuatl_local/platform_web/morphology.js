'use strict';
// Análisis morfológico y glosa interlineal en las lecturas.
// Todo lo que se muestra aquí es una hipótesis automática con su base declarada
// (diccionario, tabla de partículas, corpus o solo reglas). No se usa un LLM.

const morphBasis={
 dictionary:'Raíz en el diccionario',
 dictionary_truncated:'Raíz en el diccionario (forma sin vocal final)',
 dictionary_compound:'Compuesto de dos entradas',
 particle_table:'Partícula frecuente',
 corpus:'Raíz recurrente en el archivo',
 rules:'Solo reglas',
 loan_or_name:'Préstamo, nombre o cifra'
};
const morphCache=new Map();
async function morphWord(word,exclude){
 const key=word+'\u0000'+(exclude||'');
 if(!morphCache.has(key))morphCache.set(key,api('/api/word?'+new URLSearchParams(exclude?{w:word,exclude}:{w:word})).catch(e=>{morphCache.delete(key);throw e;}));
 return morphCache.get(key);
}
function morphemeChips(a){
 return `<ol class="morph-chips" aria-label="Segmentación">${a.morphemes.map(m=>`<li class="morph-chip ${esc(m.role)}"><span class="morph-form" lang="nci">${esc(m.surface||m.key)}${m.role==='prefix'?'-':m.role==='suffix'?'':''}</span><span class="morph-tag">${esc(m.tag)}</span>${m.gloss?`<span class="morph-gloss">${esc(m.gloss)}</span>`:''}</li>`).join('')}</ol>`;
}
function morphDictionaryHTML(a){
 if(!a.dictionary?.length)return '';
 return `<p class="morph-dictionary">Entrada: ${a.dictionary.slice(0,2).map(d=>{const sense=state.byId?.[d.sense_id];const label=`<span lang="nci">${esc(d.written)}</span> · ${esc(d.label.slice(0,90))}`;return sense?`<a href="#lexico/${esc(d.sense_id)}">${label}</a>`:label;}).join(' · ')}${a.dictionary[0].automatic?` <span class="pill proposed">${esc(originLabel(state.byId?.[a.dictionary[0].sense_id]))}</span>`:''}</p>`;
}
function wordAnalysisHTML(data){
 const [best,...alternatives]=data.analyses||[];
 if(!best)return `<div class="word-analysis"><p>No se pudo analizar «${esc(data.word)}».</p></div>`;
 const hints=data.gloss_hints||[],att=data.attestations;
 const saveable=best.dictionary?.find(d=>state.byId?.[d.sense_id]?.kind==='sense');
 return `<div class="word-analysis">
  <p class="eyebrow">Análisis automático · hipótesis de lectura</p>
  <h3 lang="nci">${esc(data.word)}</h3>
  ${morphemeChips(best)}
  <p class="meta"><span class="basis-pill basis-${esc(best.basis)}">${esc(morphBasis[best.basis]||best.basis)}</span> ${esc(best.note)}${typeof best.relative_confidence==='number'&&alternatives.length?` Preferencia frente a las alternativas: ${Math.round(best.relative_confidence*100)} %.`:''}</p>
  ${morphDictionaryHTML(best)}
  ${hints.length?`<div class="gloss-hints"><p><strong>En las traducciones del archivo</strong>, esta raíz suele acompañar a: ${hints.map(h=>`<span class="hint-word">≈ ${esc(h.word)}</span> <span class="meta">(${h.support} pasajes)</span>`).join(', ')}.</p><p class="meta">Asociación estadística entre pasajes alineados (IBM‑1), no una definición. Compruébala en los ejemplos.</p></div>`:''}
  ${att&&att.total_passages?`<div class="attestations"><p><strong>La raíz <span lang="nci">${esc(att.stem)}</span> aparece en ${att.total_passages} pasajes</strong> en ${att.distinct_forms??att.forms.length} ${(att.distinct_forms??att.forms.length)===1?'forma':'formas'}: ${att.forms.slice(0,8).map(f=>`<button type="button" class="link-button" data-morph-word="${esc(f.form)}" lang="nci">${esc(f.form)}</button> <span class="meta">${f.count}</span>`).join(' · ')}</p>
   <div class="attestation-list">${att.passages.slice(0,3).map(p=>`<article class="attestation"><p class="meta">${esc(p.document)} · ${esc(p.id)}</p><blockquote lang="nci">${highlightForm(p.nah,p.form)}</blockquote><button type="button" class="link-button" data-preview-translation aria-expanded="false">Mostrar traducción</button><p class="preview-translation" hidden>${esc(p.es)}</p></article>`).join('')}</div>
   <a href="#investigar/${encodeURIComponent(data.word)}">Buscar en el archivo completo →</a></div>`:''}
  ${alternatives.length?`<details class="morph-alternatives"><summary>Otros análisis posibles (${alternatives.length})</summary>${alternatives.map(a=>`<div class="morph-alt">${morphemeChips(a)}<p class="meta">${esc(morphBasis[a.basis]||a.basis)}${a.dictionary?.length?' · '+esc(a.dictionary[0].written)+': '+esc(a.dictionary[0].label.slice(0,60)):''}</p></div>`).join('')}</details>`:''}
  <div class="entry-actions">${saveable?saveWordButton(saveable.sense_id):''}<a class="secondary" href="#extraer">Proponer una corrección</a></div>
  <p class="meta">${esc(data.note)}</p>
 </div>`;
}
function highlightForm(text,form){
 const i=text.toLowerCase().indexOf(String(form).toLowerCase());
 if(i<0)return esc(text.length>260?text.slice(0,260)+'…':text);
 const start=Math.max(0,i-110),end=Math.min(text.length,i+form.length+130);
 return (start?'…':'')+esc(text.slice(start,i))+'<mark>'+esc(text.slice(i,i+form.length))+'</mark>'+esc(text.slice(i+form.length,end))+(end<text.length?'…':'');
}
function bindAnalysis(container,help,example){
 help.querySelectorAll('[data-morph-word]').forEach(b=>b.onclick=()=>showWordAnalysis(help,b.dataset.morphWord,example));
 help.querySelectorAll('[data-preview-translation]').forEach(b=>b.onclick=()=>{const es=b.parentElement.querySelector('.preview-translation');es.hidden=!es.hidden;b.textContent=es.hidden?'Mostrar traducción':'Ocultar traducción';b.setAttribute('aria-expanded',String(!es.hidden));});
 if(typeof bindSaved==='function')bindSaved(help);
}
async function showWordAnalysis(help,word,example){
 help.innerHTML=`<div class="word-analysis"><p class="meta" role="status">Analizando «${esc(word)}»…</p></div>`;
 try{
  const data=await morphWord(word,example?.archive_id);
  if(!help.isConnected)return;
  help.innerHTML=wordAnalysisHTML(data);bindAnalysis(help.closest('.reading-card')||help,help,example);
 }catch(e){if(help.isConnected)help.innerHTML=`<div class="word-analysis"><p>No se pudo analizar la palabra: ${esc(e.message)}</p></div>`;}
}
// En un ejercicio de completar, la palabra del hueco no se muestra en la glosa.
function maskGloss(tokens,blank){
 if(!blank)return tokens;let done=false;
 return tokens.map(t=>{if(done||t.token!==blank)return t;done=true;return {token:'_____',segmentation:'_____',tags:[],gloss:'?',gloss_source:'none'};});
}
function interlinearHTML(data,blank){
 return `<div class="interlinear" role="table" aria-label="Glosa interlineal automática">${maskGloss(data.tokens,blank).map(t=>`<div class="igt-word" role="row"><span class="igt-surface" lang="nci" role="cell">${esc(t.token)}</span><span class="igt-seg" lang="nci" role="cell">${esc(t.segmentation)}</span><span class="igt-tags" role="cell">${esc(t.tags.join('-'))}</span><span class="igt-gloss ${esc(t.gloss_source||'none')}" role="cell">${esc(t.gloss||'—')}</span></div>`).join('')}</div><p class="meta">Glosa interlineal automática (reglas + diccionario + corpus). Las glosas con «≈» son pistas estadísticas del corpus paralelo; las demás provienen del diccionario o de la tabla de partículas.</p>`;
}
function bindWordStudy(container,example){
 const help=container.querySelector('.reading-help');
 container.querySelectorAll('[data-word]').forEach(b=>b.onclick=()=>{
  container.querySelectorAll('[data-word],[data-annotation]').forEach(x=>x.setAttribute('aria-expanded',String(x===b)));
  showWordAnalysis(help,b.dataset.word,example);
 });
 const toggle=container.querySelector('[data-interlinear]'),box=container.querySelector('.interlinear-box');
 if(toggle&&box)toggle.onclick=async()=>{
  if(!box.hidden){box.hidden=true;toggle.textContent='Mostrar glosa interlineal';toggle.setAttribute('aria-expanded','false');return;}
  box.hidden=false;toggle.textContent='Ocultar glosa interlineal';toggle.setAttribute('aria-expanded','true');
  if(box.dataset.loaded)return;
  box.innerHTML='<p class="meta" role="status">Preparando la glosa…</p>';
  try{box.innerHTML=interlinearHTML(await api('/api/gloss?'+new URLSearchParams({id:example.archive_id})),container.dataset.clozeBlank);box.dataset.loaded='1';}
  catch(e){box.innerHTML=`<p>No se pudo preparar la glosa: ${esc(e.message)}</p>`;}
 };
}
// Palabras del pasaje como botones; respeta las anotaciones editoriales existentes.
const MORPH_WORD=/[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu;
function clickableWords(text,mask=null){
 let out='',end=0;
 for(const m of String(text).matchAll(MORPH_WORD)){
  if(mask&&!mask.done&&m[0]===mask.word){mask.done=true;out+=esc(text.slice(end,m.index))+'<span class="cloze-blank" aria-label="Palabra por completar">_____</span>';end=m.index+m[0].length;continue;}
  out+=esc(text.slice(end,m.index))+`<button type="button" class="plain-word" data-word="${esc(m[0])}" aria-expanded="false" aria-label="Analizar ${esc(m[0])}">${esc(m[0])}</button>`;
  end=m.index+m[0].length;
 }
 return out+esc(text.slice(end));
}
