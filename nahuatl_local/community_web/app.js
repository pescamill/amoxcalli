'use strict';
const $ = s => document.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {profile:null, mode:'translate', task:null, request:0, busy:false, blob:null, audioId:null, recorder:null, stream:null, timer:null, objectUrl:null, mine:null};
const modes = {
  recognize:['LECTURA Y COMPRENSIÓN','¿Qué te dice este texto?','Cuéntanos qué reconoces desde tu forma de hablar.',10],
  translate:['ESCRITURA Y VOZ','¿Cómo lo dirías tú?','Usa las palabras de tu comunidad. Puedes escribir, grabar o hacer ambas cosas.',10],
  listen:['ESCUCHA ENTRE HABLANTES','Escucha otra forma de decirlo.','Compara la voz con la idea en español. Si puedes, escribe lo que escuchas.',5],
  review:['REVISIÓN ENTRE HABLANTES','Una segunda mirada.','¿Esta propuesta expresa la idea en tu variante? El desacuerdo también se conserva.',5]
};

async function api(url, options={}) {
  const response = await fetch(url,{credentials:'same-origin',...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'No se pudo completar la solicitud.');
  return data;
}
const post = (url, body) => api(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function toast(message) {
  $('#toast').textContent=message;$('#toast').hidden=false;
  clearTimeout(state.toastTimer);state.toastTimer=setTimeout(()=>$('#toast').hidden=true,6000);
}
function openDialog(id) { const d=$('#'+id); if (!d.open) d.showModal(); }
function error(message) { const el=$('#answer-error'); if(el)el.textContent=message;else toast(message); }
function safeUrl(url) {try { const u=new URL(url);return ['http:','https:'].includes(u.protocol)?u.href:''; }catch{return '';} }
function sourceMarkup(task) {
  const s=task.source||{},url=safeUrl(s.url);
  return `<details class="source"><summary>Procedencia del texto</summary><p>${esc(s.label||'Aportación de la comunidad')}${url?` · <a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Consultar fuente ↗</a>`:''}</p></details>`;
}
function options(name, choices, cls='options') {
  return `<div class="${cls}">${choices.map(([value,label])=>`<label class="option"><input type="radio" name="${name}" value="${value}" required><span>${label}</span></label>`).join('')}</div>`;
}
function permissions(isReview=false, voice=false) {
  return `<div class="permissions"><label class="check"><input type="checkbox" name="review_consent" required><span>${isReview?'Acepto guardar esta revisión para que el proyecto la consulte.':'Acepto que el proyecto y participantes de mi variante revisen esta aportación.'}</span></label>
  ${isReview?'':`<label class="check"><input type="checkbox" name="rights_confirm" required><span>La respuesta y la voz que aporto son mías y puedo compartirlas.</span></label>`}
  <label class="check optional-permission"><input type="checkbox" name="train_text"><span>También autorizo usar mi texto y sus transcripciones revisadas para entrenar modelos de este proyecto. <strong>Opcional.</strong></span></label>
  ${voice?'<label class="check optional-permission"><input type="checkbox" name="train_audio"><span>También autorizo usar mi grabación para entrenar modelos de este proyecto. <strong>Opcional.</strong></span></label>':''}
  <p class="subtle">Los puntos son los mismos con o sin permiso de entrenamiento. No se publica un corpus automáticamente.</p></div>`;
}

async function refresh() {
  const b=await api('/api/bootstrap');state.profile=b.profile;state.bootstrap=b;
  $('#profile-label').textContent=b.profile?.alias||'Elegir mi variante';$('#avatar').textContent=b.profile?.alias?.slice(0,1).toUpperCase()||'+';
  const s=b.stats;$('#daily-count').textContent=`${s.today} de ${s.goal}`;$('#daily-progress').value=Math.min(s.today,s.goal);
  $('#points').textContent=s.points;$('#count-contributions').textContent=s.contributions;$('#count-reviews').textContent=s.reviews;$('#count-accepted').textContent=s.accepted;$('#community-count').textContent=s.community_total;
  if(s.accepted>0){$('#badge-title').textContent='Primera traducción revisada';$('#badge-description').textContent='Una de tus propuestas ya pasó por revisión del proyecto.';}
  else if(s.contributions+s.reviews>=5){$('#badge-title').textContent='Cinco aportaciones';$('#badge-description').textContent='Tu recorrido ya reúne cinco aportaciones o revisiones. Gracias por compartir.';}
  else if(s.contributions+s.reviews>0){$('#badge-title').textContent='Rumbo a cinco';$('#badge-description').textContent=`Tu recorrido lleva ${s.contributions+s.reviews} de cinco. Continúa cuando tú quieras.`;}
  $('#variant-select').innerHTML='<option value="">Elige una opción</option>'+b.variants.map(v=>`<option value="${esc(v.id)}">${esc(v.label)}</option>`).join('')+'<option value="custom">Otra denominación: la escribo yo</option><option value="unknown">No sé cuál elegir todavía</option>';
  $('#variant-source').href=safeUrl(b.variant_source.url);
}

function profileDialog() {
  const form=$('#profile-form');form.reset();$('#profile-error').textContent='';
  if(state.profile) for(const key of ['alias','variant_id','own_name','community','experience','historical'])form.elements[key].value=state.profile[key]||'';
  form.elements.participation_consent.checked=Boolean(state.profile);
  openDialog('profile-dialog');
}

async function discardAudio() {
  if(state.recorder && state.recorder.state!=='inactive') {
    state.recorder.onstop=null;state.recorder.stop();
  }
  state.stream?.getTracks().forEach(t=>t.stop());state.stream=null;state.recorder=null;
  clearInterval(state.timer);state.timer=null;
  if(state.objectUrl)URL.revokeObjectURL(state.objectUrl);
  if(state.audioId) {
    const old=state.audioId;state.audioId=null;
    try{await api('/api/audio/'+old,{method:'DELETE'});}catch{/* Unused uploads remain private; can be cleaned by the organizer. */}
  }
  state.blob=null;state.objectUrl=null;
}

async function task(after='') {
  const request=++state.request;
  $('#task-card').setAttribute('aria-busy','true');
  const [label,title,description,points]=modes[state.mode];$('#mode-label').textContent=label;$('#reward').textContent=`+${points} puntos por ${points===5?'revisar':'aportar'}`;
  if(!state.profile) {
    $('#task-content').innerHTML='<div class="empty"><p class="eyebrow">APORTAR</p><h2>Tu voz y tu escritura.</h2><p>Elige tu variante para empezar.<br>No necesitas escribir igual que otras personas.</p><button id="start-profile" class="primary">Elegir mi variante <span aria-hidden="true">→</span></button></div>';
    $('#start-profile').onclick=profileDialog;$('#task-card').setAttribute('aria-busy','false');return;
  }
  $('#task-content').innerHTML='<div class="loading" role="status">Buscando tu siguiente misión…</div>';
  try {
    const result=await api('/api/task?mode='+state.mode+'&after='+encodeURIComponent(after));
    if(request!==state.request)return;
    state.task=result.task;
    if(!result.task) {
      const peer=['listen','review'].includes(state.mode);
      $('#task-content').innerHTML=`<div class="empty"><p class="eyebrow">TODO AL DÍA</p><h2>${peer?'Aún no hay aportaciones para revisar.':'Completaste las misiones disponibles.'}</h2><p>${peer?'Aquí aparecerán aportaciones de otras personas que eligieron tu misma variante. Puedes comenzar compartiendo una propia.':'Prueba otra misión o vuelve cuando el proyecto añada más textos.'}</p><button id="try-other" class="primary">${peer?'Compartir una propuesta':'Probar otra misión'} <span aria-hidden="true">→</span></button></div>`;
      $('#try-other').onclick=()=>switchMode(state.mode==='translate'?'recognize':'translate');return;
    }
    renderTask(title,description);
  } catch(e) {
    $('#task-content').innerHTML=`<div class="empty"><h2>No pudimos cargar la misión.</h2><p>${esc(e.message)}</p><button id="retry-task" class="primary">Volver a intentar</button></div>`;$('#retry-task').onclick=()=>task(after);
  } finally {if(request===state.request)$('#task-card').setAttribute('aria-busy','false');}
}

function renderTask(title,description) {
  const t=state.task,kind=state.mode,isPeer=['listen','review'].includes(kind);
  let fields='';
  if(kind==='recognize') {
    fields=`<div class="prompt"><span class="prompt-label">Texto para leer</span><blockquote>${esc(t.text)}</blockquote></div>
    <fieldset><legend>¿Lo entiendes?</legend>${options('recognition',[['yes','Sí, lo entiendo'],['partly','Entiendo una parte'],['no','No lo reconozco'],['unreadable','No sé leer esta escritura']])}</fieldset>
    <fieldset><legend>¿A qué te suena?</legend>${options('perceived',[['own','A mi variante'],['other','A otra forma actual'],['historical','Podría ser náhuatl clásico'],['unsure','No puedo decirlo']])}</fieldset>
    <fieldset><legend>¿Qué tan segura es tu impresión?</legend>${options('certainty',[['sure','Segura'],['somewhat','Más o menos'],['unsure','Tengo dudas']],'certainty')}</fieldset>
    <label class="field">¿Qué significa para ti? <span class="optional">Opcional</span><textarea name="text" maxlength="4000" placeholder="Puedes explicarlo en español o en tu lengua."></textarea></label>${sourceMarkup(t)}${permissions()}`;
  } else if(kind==='translate') {
    fields=`<div class="prompt"><span class="prompt-label">Idea en español</span><blockquote>${esc(t.text)}</blockquote><span class="variant-tag">Tu variante: ${esc(state.profile.variant_label)}</span></div>
    <label class="field">Así lo escribo <span class="optional">Puedes responder solo con voz</span><textarea name="text" maxlength="4000" placeholder="Escribe como acostumbras en tu comunidad."></textarea></label>
    <div class="recorder"><div class="recorder-top"><button type="button" id="record-button" class="record-button"><span class="record-dot" aria-hidden="true"></span><span id="record-label">Grabar mi voz</span></button><span class="timer" id="record-timer">0:00 / 1:00</span></div><p class="record-status" id="record-status">La grabación empieza cuando tú lo indiques.</p><div id="audio-preview"></div><label class="file-label">O elige una grabación de tu voz (hasta 8 MB)<input id="audio-file" type="file" accept="audio/webm,audio/ogg,audio/wav,audio/mp4,audio/x-m4a,.m4a,.wav,.ogg,.webm"></label></div>
    ${sourceMarkup(t)}${permissions(false,true)}`;
  } else {
    fields=`<div class="peer-original">La idea en español<strong>${esc(t.source_text)}</strong></div><div class="prompt"><span class="prompt-label">${kind==='listen'?'Voz de otra persona':'Propuesta de otra persona'}</span>${kind==='review'?`<blockquote>${esc(t.text)}</blockquote>`:''}${t.audio_id?`<audio controls preload="metadata" src="/api/audio/${esc(t.audio_id)}"></audio>`:''}<span class="variant-tag">${esc(t.variant_label)}</span></div>
    ${kind==='listen'?'<label class="field">¿Qué escuchas? <span class="optional">Transcripción opcional</span><textarea name="transcript" maxlength="4000" placeholder="Escribe las palabras que reconoces, conservando su forma."></textarea></label>':''}
    <fieldset><legend>¿Expresa la idea en español?</legend>${options('verdict',[['matches','Sí, la expresa'],['partial','Solo una parte'],['different','Dice algo diferente'],['unsure','No estoy seguro/a']])}</fieldset>
    <label class="field">Tu observación o propuesta <span class="optional">Opcional</span><textarea name="correction" maxlength="4000" placeholder="Explica qué cambiarías y por qué, o señala una diferencia de tu comunidad."></textarea></label>${permissions(true)}`;
  }
  $('#task-content').innerHTML=`<div class="task-header"><p class="eyebrow">${isPeer?'APORTACIÓN POR REVISAR':'MISIÓN '+esc(t.id.split('-').pop())}</p><h2>${title}</h2><p>${description}</p></div><form id="answer-form" class="task-body">${fields}<p class="form-error" id="answer-error" role="alert"></p><div class="submit-row"><button type="button" id="skip-task" class="quiet">Saltar sin perder puntos</button><button type="submit" id="submit-answer" class="primary">${isPeer?'Enviar revisión':'Enviar aportación'} <span aria-hidden="true">→</span></button></div></form>`;
  $('#answer-form').onsubmit=submit;
  $('#skip-task').onclick=async()=>{if(state.busy)return;await discardAudio();await task(t.id);};
  if(kind==='translate')bindRecorder();
}

function showAudio(blob) {
  if(state.objectUrl)URL.revokeObjectURL(state.objectUrl);
  state.blob=blob;state.objectUrl=URL.createObjectURL(blob);
  $('#audio-preview').innerHTML='<audio id="local-audio" controls></audio><button type="button" class="record-remove" id="remove-audio">Descartar grabación</button>';
  $('#local-audio').src=state.objectUrl;
  $('#record-status').textContent='Escucha tu voz antes de enviarla. Todavía no se ha guardado en el proyecto.';
  $('#remove-audio').onclick=async()=>{await discardAudio();$('#audio-preview').innerHTML='';$('#record-status').textContent='Puedes volver a grabar.';$('#audio-file').value='';};
}

function bindRecorder() {
  if(!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    $('#record-button').disabled=true;$('#record-status').textContent='El micrófono requiere localhost o una conexión HTTPS compatible. Puedes subir una grabación.';
  }
  $('#record-button').onclick=async()=>{
    if(state.busy)return;
    if(state.recorder?.state==='recording'){state.recorder.stop();return;}
    try {
      $('#record-button').disabled=true;
      await discardAudio();
      $('#audio-preview').innerHTML='';
      const request=state.request;
      const stream=await navigator.mediaDevices.getUserMedia({audio:true});
      if(request!==state.request){stream.getTracks().forEach(t=>t.stop());return;}
      state.stream=stream;
      const mime=['audio/webm;codecs=opus','audio/mp4','audio/webm','audio/ogg;codecs=opus'].find(x=>MediaRecorder.isTypeSupported(x));
      const recorder=new MediaRecorder(stream,mime?{mimeType:mime}:undefined),parts=[];state.recorder=recorder;
      recorder.ondataavailable=e=>{if(e.data.size)parts.push(e.data);};
      recorder.onerror=()=>{error('No se pudo completar la grabación. Intenta subir un archivo.');stream.getTracks().forEach(t=>t.stop());clearInterval(state.timer);};
      recorder.onstop=()=>{
        stream.getTracks().forEach(t=>t.stop());clearInterval(state.timer);state.stream=null;
        $('#record-button')?.classList.remove('recording');if($('#record-label'))$('#record-label').textContent='Volver a grabar';
        const blob=new Blob(parts,{type:recorder.mimeType||mime});
        if(blob.size>8*1024*1024){error('La grabación supera 8 MB. Prueba una más corta.');return;}
        if(!blob.size){error('La grabación está vacía. Intenta otra vez.');return;}
        if(request===state.request)showAudio(blob);
      };
      recorder.start(250);const started=Date.now();
      $('#record-button').classList.add('recording');$('#record-label').textContent='Detener grabación';$('#record-status').textContent='Grabando tu voz. Puedes detenerte cuando quieras.';
      state.timer=setInterval(()=>{const seconds=Math.min(60,Math.floor((Date.now()-started)/1000));if($('#record-timer'))$('#record-timer').textContent=`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')} / 1:00`;if(seconds>=60&&recorder.state==='recording')recorder.stop();},250);
    }catch(e){error(e.name==='NotAllowedError'?'No se autorizó el micrófono. Puedes escribir o subir una grabación.':'No se encontró un micrófono disponible. Puedes subir una grabación.');}
    finally{if($('#record-button'))$('#record-button').disabled=false;}
  };
  $('#audio-file').onchange=async e=>{
    const file=e.target.files[0];if(!file)return;
    if(file.size>8*1024*1024){error('Elige un archivo de hasta 8 MB.');e.target.value='';return;}
    await discardAudio();
    const ext=file.name.split('.').pop().toLowerCase();
    const mime=file.type||({webm:'audio/webm',ogg:'audio/ogg',wav:'audio/wav',m4a:'audio/mp4'}[ext]||'application/octet-stream');
    showAudio(new Blob([file],{type:mime}));
  };
}

async function submit(e) {
  e.preventDefault();if(state.busy)return;
  if(state.recorder?.state==='recording'){error('Detén y escucha la grabación antes de enviarla.');return;}
  const form=e.currentTarget, data=Object.fromEntries(new FormData(form));
  if(state.mode==='translate' && !data.text?.trim() && !state.blob){error('Escribe una propuesta o graba tu voz.');return;}
  state.busy=true;$('#submit-answer').disabled=true;$('#answer-error').textContent='';
  for(const key of ['review_consent','rights_confirm','train_text','train_audio'])data[key]=data[key]==='on';
  try {
    let result;
    if(['review','listen'].includes(state.mode)) {
      result=await post('/api/reviews',{...data,contribution_id:state.task.id});
    }else {
      if(state.blob&&!state.audioId){const upload=await api('/api/audio',{method:'POST',headers:{'Content-Type':state.blob.type},body:state.blob});state.audioId=upload.id;}
      result=await post('/api/contributions',{...data,task_id:state.task.id,audio_id:state.audioId});
      state.audioId=null; // El audio ya pertenece a la aportación, no se borra al limpiar la pantalla.
    }
    await discardAudio();
    $('#task-content').innerHTML=`<div class="success-card"><div class="success-symbol" aria-hidden="true">✓</div><p class="eyebrow">APORTACIÓN GUARDADA</p><h2>Gracias por compartir.</h2><p>Tu respuesta conserva tu variante y tus permisos. Queda disponible para revisión.</p><p class="success-score">+${result.points} puntos de participación</p><p class="subtle">Responder con dudas es tan válido como reconocer el texto.</p><button id="next-task" class="primary">Siguiente misión <span aria-hidden="true">→</span></button><button id="see-mine" class="text-button">Ver mi aportación</button></div>`;
    $('#next-task').onclick=()=>task();$('#see-mine').onclick=showMine;
    await refresh();
  }catch(err){error(err.message);if($('#submit-answer'))$('#submit-answer').disabled=false;}
  finally{state.busy=false;}
}

async function switchMode(mode) {
  if(state.busy)return;
  await discardAudio();state.mode=mode;
  document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.mode===mode);if(b.dataset.mode===mode)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  await task();
}

async function showMine() {
  if(!state.profile){profileDialog();return;}
  openDialog('mine-dialog');$('#mine-list').innerHTML='<p>Cargando tus aportaciones…</p>';
  try {
    const data=await api('/api/mine');state.mine=data;
    const status={pending:'Pendiente',accepted:'Aprobada por el proyecto',rejected:'Requiere revisión',withdrawn:'Retirada'};
    $('#mine-list').innerHTML=data.contributions.map(c=>`<article class="mine-item"><div class="mine-meta"><span class="status">${status[c.status]}</span><span>${esc(new Date(c.created).toLocaleDateString('es-MX'))}</span><span>${c.reviews} revisiones</span></div><h3>${esc(c.source.text)}</h3><p>${esc(c.answer.text|| (c.status==='withdrawn'?'Contenido retirado.':c.kind==='recognize'?'Impresión de lectura guardada.':'Aportación de voz.'))}</p>${c.audio_id?`<audio controls preload="none" src="/api/audio/${esc(c.audio_id)}"></audio>`:''}${c.status!=='withdrawn'?`<p class="subtle">Entrenamiento: texto ${c.answer.train_text?'autorizado':'no autorizado'} · voz ${c.answer.train_audio?'autorizada':'no autorizada'}</p><button class="text-button withdraw" data-id="${esc(c.id)}" data-type="contributions">Retirar aportación</button>`:''}<p class="subtle">ID: ${esc(c.id)}</p></article>`).join('')+data.reviews.map(r=>`<article class="mine-item"><div class="mine-meta"><span class="status">Revisión entre participantes</span></div><p>${esc({matches:'Expresa la idea',partial:'Expresa parte de la idea',different:'Dice algo diferente',unsure:'No tengo certeza'}[r.answer.verdict])}</p><p>${esc(r.answer.correction||r.answer.transcript||'')}</p><button class="text-button withdraw" data-id="${esc(r.id)}" data-type="reviews">Retirar revisión</button></article>`).join('')||'<p>Tus respuestas y grabaciones aparecerán aquí después de enviarlas.</p>';
    document.querySelectorAll('.withdraw').forEach(b=>b.onclick=()=>{state.withdraw={id:b.dataset.id,type:b.dataset.type};openDialog('withdraw-dialog');});
  }catch(e){$('#mine-list').textContent=e.message;}
}

$('#confirm-withdraw').onclick=async()=>{
  if(!state.withdraw)return;
  $('#confirm-withdraw').disabled=true;
  try {
    await api('/api/'+state.withdraw.type+'/'+state.withdraw.id,{method:'DELETE'});
    $('#withdraw-dialog').close();toast('Retirada completada. Se excluye de futuras exportaciones.');await refresh();await showMine();await task();
  }catch(e){toast(e.message);}finally{$('#confirm-withdraw').disabled=false;}
};
$('#download-mine').onclick=()=>{
  if(!state.mine)return;
  const blob=new Blob([JSON.stringify({profile:state.profile,...state.mine},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='mis-aportaciones-voces.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Se descargaron tus respuestas. Las grabaciones se escuchan desde la lista.');
};
$('#profile-form').onsubmit=async e=>{
  e.preventDefault();if(state.busy)return;
  const form=e.currentTarget,button=form.querySelector('button[type=submit]'),body=Object.fromEntries(new FormData(form));body.participation_consent=body.participation_consent==='on';button.disabled=true;
  try{await post('/api/profile',body);$('#profile-dialog').close();await refresh();await discardAudio();await task();toast('Tu perfil está listo. Puedes participar a tu ritmo.');}
  catch(err){$('#profile-error').textContent=err.message;}finally{button.disabled=false;}
};
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>switchMode(b.dataset.mode));
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$('#'+b.dataset.close).close());
$('#profile-button').onclick=profileDialog;$('#mine-button').onclick=showMine;
$('#about-button').onclick=$('#footer-about').onclick=()=>openDialog('about-dialog');
window.addEventListener('beforeunload',e=>{state.stream?.getTracks().forEach(t=>t.stop());if(state.blob||state.recorder?.state==='recording'){e.preventDefault();e.returnValue='';}});
refresh().then(()=>switchMode(state.mode)).catch(e=>{
  $('#task-card').setAttribute('aria-busy','false');$('#task-content').innerHTML=`<div class="empty"><h2>El proyecto no está disponible.</h2><p>${esc(e.message)}</p><button id="reload" class="primary">Volver a intentar</button></div>`;$('#reload').onclick=()=>location.reload();
});
