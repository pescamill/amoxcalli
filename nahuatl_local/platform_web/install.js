"use strict";
(() => {
 let promptEvent=null;
 const box=document.createElement('details');box.className='app-install';
 const summary=document.createElement('summary');summary.textContent='Instalar app';box.append(summary);
 const help=document.createElement('p');help.textContent='Abre el menú del navegador y elige «Instalar aplicación» o «Añadir a pantalla de inicio». En iPhone o iPad: Compartir → Añadir a pantalla de inicio.';box.append(help);
 const button=document.createElement('button');button.textContent='Instalar Scriptorium';button.type='button';button.hidden=true;box.append(button);
 const note=document.createElement('p');note.textContent='El servidor debe estar encendido para consultar y guardar aportaciones.';box.append(note);
 const tools=document.querySelector('[data-app-tools]');if(tools)tools.append(box);else document.querySelector('header')?.insertAdjacentElement('afterend',box);
 if(!window.isSecureContext)help.textContent='Puedes usar esta webapp aquí. Para instalarla y grabar con el micrófono desde tu teléfono, abre la dirección HTTPS de tu servidor.';
 if(window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone)box.hidden=true;
 window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();promptEvent=event;button.hidden=false;});
 button.addEventListener('click',async()=>{
  if(!promptEvent)return;
  try{await promptEvent.prompt();const result=await promptEvent.userChoice;if(result.outcome==='accepted')box.hidden=true;}
  catch{note.textContent='No se pudo abrir la instalación. Usa el menú del navegador.';}
  finally{promptEvent=null;button.hidden=true;}
 });
 window.addEventListener('appinstalled',()=>{box.hidden=true;});
 if('serviceWorker' in navigator&&window.isSecureContext)navigator.serviceWorker.register('/sw.js').catch(()=>{note.textContent='La webapp funciona; no se pudo preparar la pantalla de desconexión.';});
})();
