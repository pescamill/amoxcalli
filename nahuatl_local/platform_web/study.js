'use strict';
// Cuaderno local: progreso de lecturas, palabras guardadas, fragmentos y repasos.
// Vive solo en este navegador (localStorage 'scriptorium-study-v1'); nunca se envía al servidor.

let studyStorageAvailable=true;
function readStudy(){
 try{
  const value=JSON.parse(localStorage.getItem('scriptorium-study-v1')||'null');
  if(value?.version===1)return {version:1,saved:Array.isArray(value.saved)?value.saved.filter(x=>typeof x==='string'):[],lessons:value.lessons&&typeof value.lessons==='object'?value.lessons:{},reviews:value.reviews&&typeof value.reviews==='object'?value.reviews:{},contexts:value.contexts&&typeof value.contexts==='object'?value.contexts:{}};
 }catch{/* Un almacenamiento vacío o corrupto no impide estudiar. */}
 return {version:1,saved:[],lessons:{},reviews:{},contexts:{}};
}
const study=readStudy();
function writeStudy(){try{localStorage.setItem('scriptorium-study-v1',JSON.stringify(study));return true;}catch{studyStorageAvailable=false;toast('Tu navegador no permite guardar el progreso. Puedes seguir estudiando durante esta sesión.');return false;}}
function isSaved(id){return study.saved.includes(id);}
function toggleSaved(id,context){
 if(!state.byId[id]||state.byId[id].kind!=='sense')return;
 const removing=isSaved(id);
 study.saved=removing?study.saved.filter(x=>x!==id):[...study.saved,id];
 if(removing)delete study.contexts[id];else if(context)study.contexts[id]=context;
 writeStudy();
 document.querySelectorAll('[data-save-word]').forEach(b=>{b.textContent=isSaved(b.dataset.saveWord)?'Guardada ✓':'Guardar palabra';b.setAttribute('aria-pressed',String(isSaved(b.dataset.saveWord)));});
}
function bindSaved(container){
 container.querySelectorAll('[data-save-word]').forEach(b=>b.onclick=()=>{
  toggleSaved(b.dataset.saveWord,savedContext(b));
  document.querySelectorAll('[data-save-context]').forEach(x=>x.hidden=!isSaved(x.dataset.saveContext));
 });
 container.querySelectorAll('[data-save-context]').forEach(b=>b.onclick=()=>{
  const context=savedContext(b);if(!context||!isSaved(b.dataset.saveContext))return;
  study.contexts[b.dataset.saveContext]=context;writeStudy();b.textContent='Fragmento guardado ✓';
 });
 appendSourceCredits();
}
function savedContext(button){
 const article=button.closest('[data-archive-id]')||button.closest('.lesson-layout')?.querySelector('[data-archive-id]');
 if(!article)return;
 const example=state.learning.lessons.flatMap(l=>l.examples).find(e=>e.archive_id===article.dataset.archiveId);
 if(example?.annotations.some(a=>a.sense_id===(button.dataset.saveWord||button.dataset.saveContext)))return {archive_id:example.archive_id};
}
function savedPassage(id){
 const rid=study.contexts[id]?.archive_id;
 // Resolve only against current, source-checked readings; storage is not evidence.
 return rid&&state.learning.lessons.flatMap(l=>l.examples.map(e=>({lesson:l,example:e}))).find(v=>v.example.archive_id===rid&&v.example.annotations.some(a=>a.sense_id===id));
}
function savedPassageHTML(id,review=false){
 const context=savedPassage(id);if(!context)return '';
 const {lesson,example}=context,p=example.passage;
 return `<details class="saved-context"><summary>El fragmento donde la guardaste</summary><blockquote lang="nci">${esc(p.nah)}</blockquote>${review?'':`<p>${esc(p.es)}</p>`}<p class="meta">${esc(p.document)} · ${esc(p.locator)}</p><a href="#leer/${esc(lesson.id)}">Volver a esta lectura →</a></details>`;
}
function saveWordButton(id){return `<button class="secondary" data-save-word="${esc(id)}" aria-pressed="${isSaved(id)}">${isSaved(id)?'Guardada ✓':'Guardar palabra'}</button>`;}
function lessonProgress(lesson){
 const edition=state.learning.id+':'+(lesson.practice_version||lesson.version||state.learning.version);
 const old=study.lessons[lesson.id];
 const valid=xs=>Array.isArray(xs)?xs.filter(x=>Number.isInteger(x)&&x>=0&&x<lesson.examples.length):[];
 if(old?.edition===edition)return {edition,passed:valid(old.passed),comprehension:valid(old.comprehension),step:Number.isInteger(old.step)?Math.max(0,Math.min(old.step,lesson.examples.length-1)):0};
 return {edition,passed:[],comprehension:[],step:0};
}
function exampleComplete(lesson,progress,index){return progress.passed.includes(index)&&(!lesson.examples[index].comprehension||progress.comprehension.includes(index));}
function completedExamples(lesson){const p=lessonProgress(lesson);return lesson.examples.filter((_,i)=>exampleComplete(lesson,p,i)).length;}
