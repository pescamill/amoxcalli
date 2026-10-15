const assert=require('node:assert/strict');
const {JSDOM,CookieJar,VirtualConsole}=require('jsdom');
const wavBuffer=Buffer.alloc(16044);
wavBuffer.write('RIFF',0);wavBuffer.writeUInt32LE(16036,4);wavBuffer.write('WAVEfmt ',8);wavBuffer.writeUInt32LE(16,16);wavBuffer.writeUInt16LE(1,20);wavBuffer.writeUInt16LE(1,22);wavBuffer.writeUInt32LE(8000,24);wavBuffer.writeUInt32LE(16000,28);wavBuffer.writeUInt16LE(2,32);wavBuffer.writeUInt16LE(16,34);wavBuffer.write('data',36);wavBuffer.writeUInt32LE(16000,40);
const origin=process.env.VOCES_QA_ORIGIN||'http://127.0.0.1:8766',cookieJar=new CookieJar(),errors=[];
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){for(let i=0;i<100;i++){if(fn())return;await delay(30)}throw Error('Timed out waiting for UI condition')}
(async()=>{
 const virtualConsole=new VirtualConsole();virtualConsole.on('jsdomError',e=>{if(!e.message.includes('HTMLMediaElement'))errors.push(e.message)});
 const dom=await JSDOM.fromURL(origin+'/aportar',{runScripts:'dangerously',resources:'usable',pretendToBeVisual:true,cookieJar,virtualConsole,beforeParse(w){
  w.fetch=async(url,options={})=>{const absolute=new URL(url,origin).href;const headers=new Headers(options.headers);const cookie=cookieJar.getCookieStringSync(absolute);if(cookie)headers.set('Cookie',cookie);if(options.method&&options.method!=='GET')headers.set('Origin',origin);const response=await fetch(absolute,{...options,headers});for(const value of response.headers.getSetCookie())cookieJar.setCookieSync(value,absolute);return response};
  // /aportar carga install.js (instalación PWA), que consulta matchMedia; jsdom no lo implementa.
  w.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});
  w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};
  w.Blob=Blob;w.URL.createObjectURL=()=> 'blob:http://127.0.0.1:8766/test-only';w.URL.revokeObjectURL=()=>{};
 }});
 const w=dom.window,d=w.document,$=s=>d.querySelector(s);
 await until(()=>$('#start-profile'));
 $('#start-profile').click();const p=$('#profile-form');p.elements.alias.value='QA sintético';p.elements.variant_id.value='inali-04';p.elements.experience.value='learning';p.elements.participation_consent.checked=true;p.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 await until(()=>$('#answer-form'));
 $('[data-mode="recognize"]').click();await until(()=>$('#answer-form')?.elements.recognition);
 assert.equal($('#profile-label').textContent,'QA sintético');
 $('#answer-form').elements.recognition.value='partly';$('#answer-form').elements.perceived.value='unsure';$('#answer-form').elements.certainty.value='unsure';$('#answer-form').elements.review_consent.checked=true;$('#answer-form').elements.rights_confirm.checked=true;
 $('#answer-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 await until(()=>$('#next-task'));await until(()=>$('#points').textContent==='10');
 console.log('PASS: profile, recognition, uncertainty and equal points without training permission');
 $('[data-mode="translate"]').click();await until(()=>$('#audio-file'));
 // File bytes remain real; bridge File to native Blob for the Fetch implementation used in this DOM-only test.
 const nativeFile=new Blob([wavBuffer],{type:'audio/wav'});nativeFile.name='silencio.wav';
 Object.defineProperty($('#audio-file'),'files',{value:[nativeFile],configurable:true});$('#audio-file').dispatchEvent(new w.Event('change',{bubbles:true}));
 await until(()=>$('#local-audio'));
 $('#answer-form').elements.text.value='<script>NO EJECUTAR</script> · prueba';$('#answer-form').elements.review_consent.checked=true;$('#answer-form').elements.rights_confirm.checked=true;
 $('#answer-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await until(()=>$('#next-task'));await until(()=>$('#points').textContent==='20');
 console.log('PASS: real WAV file passes the UI upload and text submission pipeline');
 $('#mine-button').click();await until(()=>$('.mine-item audio'));
 assert.equal($('#mine-list script'),null);assert($('#mine-list').textContent.includes('<script>NO EJECUTAR</script>'));
 const audioUrl=$('.mine-item audio').getAttribute('src'),res=await w.fetch(audioUrl);assert.equal(res.status,200);assert.equal((await res.arrayBuffer()).byteLength,16044);
 console.log('PASS: private audio retrieval, contribution list and escaped text');
 const remove=$('.mine-item audio').closest('.mine-item').querySelector('.withdraw');remove.click();$('#confirm-withdraw').click();await until(()=>$('#points').textContent==='10');await until(()=>!$('#withdraw-dialog').open);
 const missing=await w.fetch(audioUrl);assert.equal(missing.status,404);
 console.log('PASS: withdrawal removes the active audio and updates progress');
 const records=await (await w.fetch('/api/mine')).json();assert.equal(records.contributions.filter(c=>c.status==='withdrawn').length,1);assert.equal(records.contributions.find(c=>c.status==='pending').answer.train_text,false);
 assert.deepEqual(errors,[]);console.log('PASS: no application JavaScript errors');
 dom.window.close();
})().catch(e=>{console.error(e);process.exit(1)});
