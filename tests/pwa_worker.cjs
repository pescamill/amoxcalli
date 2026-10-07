// Contrato de desconexión y privacidad; no sustituye la instalación en un teléfono.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const handlers={},writes=[],deleted=[];
const fallback={status:200,body:'Conecta con tu servidor'};
const context={URL,Promise,fetch:async()=>{throw Error('offline');},
 self:{location:{origin:'https://local.example'},addEventListener:(name,fn)=>handlers[name]=fn,clients:{claim:async()=>{}}},
 caches:{open:async()=>({addAll:async urls=>writes.push(...urls)}),
 keys:async()=>['unrelated-cache','scriptorium-offline-old','scriptorium-offline-v1'],
 delete:async key=>deleted.push(key),match:async path=>path==='/offline.html'?fallback:{body:'css'}}};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../nahuatl_local/platform_web/sw.js'),'utf8'),context);
(async()=>{
 let job;handlers.install({waitUntil:p=>job=p});await job;
 assert.deepEqual(writes,['/offline.html','/offline.css']);
 handlers.activate({waitUntil:p=>job=p});await job;
 assert.deepEqual(deleted,['scriptorium-offline-old']);
 for(const request of [
  {method:'POST',url:'https://local.example/api/proposals'},
  {method:'GET',url:'https://local.example/api/corpus'},
  {method:'GET',url:'https://local.example/api/profile'},
  {method:'GET',url:'https://external.example/page',mode:'navigate'}]){
   let intercepted=false;handlers.fetch({request,respondWith:()=>intercepted=true});assert.equal(intercepted,false);
 }
 handlers.fetch({request:{method:'GET',url:'https://local.example/aportar',mode:'navigate'},respondWith:p=>job=p});
 assert.equal(await job,fallback);
 console.log('PASS: offline navigation fallback; no cached corpus, profiles, submissions or external requests; scoped cache cleanup');
})().catch(e=>{console.error(e);process.exit(1);});
