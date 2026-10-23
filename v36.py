import re,os,sys
if not os.path.exists('www/index.html'):
    os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
p='www/index.html'
s=open(p,encoding='utf-8').read()
if 'id="v36-script"' in s:
    print('v3.6 ya aplicado'); raise SystemExit
JS=r'''/* v3.6: Jenny natural, ayuda completa, Telegram, PDF/imagen */
const PORTAL_TG='Portal26';
const J_KB=[
['viajes','🚕','¿Cómo registro un viaje?','viaje,registr,apunt,anad,meter,bolt,uber,cabify,privado,calculadora,plataforma','Ve a Calculadora, escribe el importe del viaje y pulsa la plataforma (Bolt, Uber, Cabify o Privados). Se guarda en el día que tengas seleccionado arriba, así que mira que la fecha sea la correcta.'],
['aeropuerto','✈️','¿Y los viajes de aeropuerto?','aeropuert,ida y vuelta,tasa','Escribe el importe y pulsa el botón grande de Aeropuerto, el azul. La app aplica sola la comisión y la tasa que tengas en Ajustes, y las ves en la etiqueta amarilla del botón.'],
['pago','💳','¿Tarjeta o efectivo?','tarjeta,efectivo,pago,cobr,metalico,cash,pagan','Al pulsar la plataforma te pregunta cómo pagó el cliente. Si fue en efectivo, pon el efectivo real que cobraste. Con el lector de pantalla activado, la app detecta sola si es tarjeta o efectivo y no te pregunta.'],
['propinas','🎁','¿Dónde pongo una propina?','propin','En Facturación → Diario, en la lista de viajes del día, pulsa la opción de propina del viaje y escribe lo que te dieron. Las propinas se cuentan aparte y no pagan comisión.'],
['corregir','✏️','Me equivoqué en un viaje','borrar,eliminar,quitar,corregir,editar,equivoc^4,equivoq^4,error,cambiar importe,mal puesto','Entra en Facturación → Diario, busca el viaje en la lista del día y edítalo o bórralo desde ahí. Los totales se recalculan solos.'],
['otrodia','📅','Quiero cargar o ver otro día','otro dia,ayer,anterior,fecha,flecha,dia pasado,antes de ayer','Usa las flechas de fecha de Calculadora o de Facturación para ir al día que quieras. Lo que cargues se guarda en ese día.'],
['facturacion','💶','¿Dónde veo mi facturación?','factur,ingres,gane,ganado,cuanto llevo,semana,mensual,mes','En Facturación tienes Diario, Semanal y Mensual, con el total, tu comisión y el desglose por plataforma. También lo ves de un vistazo arriba, en Calculadora.'],
['compensaciones','🔁','Cancelaciones y compensaciones','compensac,cancelac,cancelad,bonus,bono','Las compensaciones por cancelaciones se apuntan en Facturación → Semanal. Se suman al total del día, al €/hora y al €/km.'],
['nomina','🧾','Nómina y pago semanal','nomina,liquidac,pago semanal,transferencia,pagaron','En Facturación → Semanal puedes revisar la semana y compararla con lo que te ingresan. Si algo no cuadra, mira primero las compensaciones y el efectivo.'],
['jornada','⏱️','Iniciar y finalizar la jornada','jornada,iniciar,finalizar,empezar,terminar,horario,horas,turno','En Control pulsa Iniciar jornada cuando empieces y Finalizar cuando termines. La app cuenta tus horas y, con el GPS activado, también tus kilómetros.'],
['olvido','😅','Se me olvidó iniciar la jornada','olvid^5,se me olvido^6,no inicie^4,no puse,sin iniciar,corregir horas,hora manual','No pasa nada. En Control elige el día y corrige las horas a mano. Sirve también para días anteriores.'],
['gasolina','⛽','¿Cómo apunto la gasolina?','gasolin,combustible,repost,gasoil,diesel','En Control elige el día, escribe lo que has repostado y guarda. Puedes apuntar varios repostajes en el mismo día.'],
['km','📍','Kilómetros y GPS','kilomet,odometro,km,gps,recorrid,distancia','Si activas el odómetro automático (GPS) en Control o en Ajustes, la app cuenta tus kilómetros sola mientras la jornada está iniciada. También puedes escribirlos a mano.'],
['gpsfalla','🛰️','El GPS no cuenta kilómetros','gps no,no cuenta,no suma,permiso,ubicacion,no funciona gps,kilometros no','Revisa tres cosas: que la jornada esté iniciada, que le diste permiso de ubicación a la app (mejor «Permitir siempre») y que el ahorro de batería no la esté frenando. Si sigue igual, ciérrala y ábrela otra vez.'],
['lector','🔍','Importe automático','importe automatico,leer precio,lector,leer pantalla,accesibilidad,lee el precio,automatic','El botón Importe automático lee el precio que ves en Bolt, Uber o Cabify, sin hacer fotos. Para que funcione, activa Portal Lector en Ajustes de Android → Accesibilidad y tócalo con el viaje en pantalla.'],
['lectorfalla','❌','El lector no detecta el precio','no me lee^5,no lee^5,no me detecta^5,no detecta^5,no me reconoce^5,no reconoce^5,no me coge^5,no pilla^5,no sale el precio^5,no funciona lector^5','Suele pasar si el viaje no está visible o si el servicio se apagó. Mira que Portal Lector siga activado en Accesibilidad, ten el viaje en pantalla y toca otra vez. Si no hay manera, escribe el importe a mano.'],
['burbuja','🫧','Burbuja flotante','burbuja,flotante,widget,bolita,circulo','Es el botón redondo con el icono de la app que aparece sobre Bolt, Uber y Cabify. Arrástrala a donde menos moleste y tócala para leer el precio. Se activa o se apaga en Ajustes.'],
['informe','📊','Informe','informe,reporte,resumen,periodo','En Informe eliges el periodo y lo generas: total, efectivo, tarjeta, viajes, comisión, gasolina, horas y kilómetros.'],
['pdf','📄','PDF o imagen del informe','pdf^4,compartir^4,enviar^3,mandar^3,imagen^3,whatsapp^4','Genera el informe y usa «Compartir PDF» o «Compartir imagen». Se abre el menú de tu móvil para mandarlo por WhatsApp, por correo o guardarlo.'],
['comision','🧮','¿Cómo se calcula mi comisión?','comision,porcentaje,tasa,cuanto me toca,mi parte','Tu comisión se calcula sobre la facturación del día con los porcentajes que tengas en Ajustes. Las propinas no pagan comisión.'],
['rentab','📈','€/hora, €/viaje y €/km','euro hora,por hora,por viaje,rentabil,media,por km,eur/h','Son tu rendimiento del día: lo que facturas por hora trabajada, por viaje y por kilómetro. El €/km se actualiza en vivo si tienes el GPS activo.'],
['ojo','👁️','Ocultar la facturación','ojo,ocult^4,esconder^4,tapar,privacidad','Toca el ojo junto al Total facturación diaria para ocultar o mostrar los importes, por si llevas a alguien en el coche.'],
['ajustes','⚙️','Ajustes','ajuste,configur,objetivo,meta,prioritari,personalizar','En Ajustes están tu comisión, la tasa del aeropuerto, los objetivos, los horarios prioritarios y los interruptores de la burbuja y del GPS.'],
['cuenta','👤','Cuenta y sincronización','cuenta,sincroniz,nube,sesion,contrasena,login,correo','Con tu cuenta tus datos se guardan en la nube y los tienes en cualquier dispositivo. Se sincronizan solos cuando dejas de usar la app unos segundos o la cierras.'],
['cambiomovil','📱','Cambié de móvil','cambie de telefono^5,cambie de movil^5,cambiar de movil^5,cambiar de telefono^5,telefono nuevo^4,movil nuevo^4,nuevo movil^4,nuevo telefono^4,otro movil^4,mis datos^3,recuper,perdi,reinstal','Instala la app, inicia sesión con tu misma cuenta y tus datos vuelven solos desde la nube. No tienes que hacer nada más.'],
['copia','💾','Copia de seguridad','copia,seguridad,backup,exportar','Con tu cuenta tus datos ya están a salvo en la nube. En Ajustes también puedes crear una copia de seguridad local cuando quieras.'],
['consumo','🔋','Batería e internet','bateria,consume,internet,datos moviles,gasta,megas,lento','La app sube los datos solo cuando dejas de usarla unos segundos y solo si algo cambió, así que gasta muy poco internet. Lo que más batería usa es el GPS: si no lo necesitas, apágalo.'],
['actualizar','⬆️','Actualizar la app','actualiz,version,nueva version,instalar,apk','Cuando hay versión nueva te llega el archivo y lo instalas encima de la anterior, sin desinstalar y sin perder datos. Arriba a la derecha ves qué versión tienes.'],
['recordatorios','🔔','Avisos y recordatorios','notific,record,aviso,alarma','La app puede recordarte cosas como generar el informe del mes. Mira que Android no tenga bloqueadas las notificaciones de la app.'],
['nocuadra','🤔','Los totales no me cuadran','cuadr^4,no coincide^4,diferencia,distinto,falta dinero,sobra','Repasa por orden: 1) que los viajes estén en el día correcto, 2) que el pago (tarjeta o efectivo) sea el real y 3) las compensaciones y propinas. Con las flechas de fecha revisa el día en Facturación.'],
['tablet','🖥️','Tablet y pantalla dividida','tablet,pantalla dividida,multiventana,ventana,dos apps','Con pantalla dividida puedes tener Bolt a un lado y el Portal al otro. El lector lee el precio de la otra ventana y lo mete en el Portal.'],
['frase','💬','Frase del día','frase,impulso,motivac,cita','Arriba, en Calculadora, tienes cada día una frase distinta. Hay 365, una para cada día del año.'],
['contacto','🧑','Hablar con una persona','telegram,persona,humano,soporte,contactar,hablar con alguien,tecnico','Claro. Pulsa el botón de Telegram y se abre el chat con soporte (@'+PORTAL_TG+').']
];
const J_OPEN=['¡Claro! 😊','Te lo explico fácil 👇','Buena pregunta 👍','Vale, mira:','Sin problema 😉','Eso es sencillo:'];
const J_CLOSE=['¿Te ha servido? Si no, dímelo con otras palabras.','Si algo no te cuadra, dime y lo vemos juntos.','Y si te queda alguna duda, aquí estoy 🙂','Pruébalo y me cuentas cómo te va.','¿Lo ves claro? Si no, te lo explico de otra forma.'];
const J_FOLLOW=['Vale, probemos por otro lado 🤔','Quizá iba por aquí la cosa:','Entiendo, a lo mejor te ayuda esto:'];
const jPick=a=>a[Math.floor(Math.random()*a.length)];
function jNorm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9€ ]/g,' ').replace(/\s+/g,' ').trim()}
function jLev(a,b){const m=a.length,n=b.length;if(Math.abs(m-n)>1)return 9;const d=[];for(let i=0;i<=m;i++){d[i]=[i];}for(let j=1;j<=n;j++)d[0][j]=j;for(let i=1;i<=m;i++)for(let j=1;j<=n;j++)d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));return d[m][n]}
function jennyMatch(text,exclude){const n=jNorm(text),toks=n.split(' ').filter(Boolean),res=[];J_KB.forEach(e=>{if((exclude||[]).includes(e[0]))return;let sc=0;e[3].split(',').forEach(raw=>{const sp=raw.split('^'),st=sp[0],wt=sp[1]?+sp[1]:0;if(st.length<=3){if(toks.includes(st))sc+=wt||2;return}if(n.includes(st)){sc+=wt||((st.length>=6||st.includes(' '))?3:2);return}if(st.length>=7&&!st.includes(' ')&&toks.some(w=>w.length>=6&&jLev(w.slice(0,st.length),st)<=1))sc+=2});if(sc>=2)res.push({id:e[0],score:sc})});return res.sort((a,b)=>b.score-a.score)}
function jennySmall(text){const n=jNorm(text),w=n.split(' ').filter(Boolean);if(w.length<=6&&/\b(gracias|genial|perfecto|mil gracias)\b/.test(n))return'¡De nada! 😊 Para eso estoy. Si necesitas algo más de la app, pregúntame.';if(w.length<=4&&/^(hola|buenas|buenos dias|buenas tardes|buenas noches|hey|ey|que tal)/.test(n))return'¡Hola! 👋 Soy Jenny. Pregúntame lo que quieras de la app: cómo apuntar un viaje, la gasolina, los kilómetros, el informe…';if(w.length<=4&&/\b(adios|hasta luego|chao)\b/.test(n))return'¡Hasta luego! 🚕 Buen día de trabajo y conduce con calma.';return null}
function jEntry(id){return J_KB.find(e=>e[0]===id)}
function jennyReply(id,attempt){const e=jEntry(id);if(!e)return'Mmm, de eso no estoy segura 😅';return attempt>1?jPick(J_FOLLOW)+' '+e[4]:jPick(J_OPEN)+' '+e[4]+' '+jPick(J_CLOSE)}
function autoReplyText(type){return jennyReply(type,1)}
function classifySupportQuery(subject,body){const m=jennyMatch((subject||'')+' '+(body||''));return m.length?m[0].id:null}
function openTelegramSupport(text){const msg='Hola, soy conductor de Portal del Conductor (v3.6). '+(text||'');try{if(navigator.clipboard)navigator.clipboard.writeText(msg)}catch(e){}alert('He copiado tu mensaje. Cuando se abra el chat de Telegram, pégalo y envíalo.');const url='https://t.me/'+PORTAL_TG,P=window.Capacitor&&Capacitor.Plugins&&Capacitor.Plugins.ShareFile;if(P&&P.openUrl){P.openUrl({url}).catch(()=>window.open(url,'_blank'))}else window.open(url,'_blank')}
function jPanel(title,backFn,inner){document.querySelector('#content').innerHTML='<section class="panel futuristic"><div class="settings-head"><button class="back" onclick="'+backFn+'">←</button><div class="section-title" style="margin:0">'+title+'</div></div>'+inner+'</section>'}
function renderJennyCard(text){jPanel('😊 Jenny','renderSendSupport()','<div class="help-hero"><h2>😊 Jenny</h2><p>'+escapeHtml(text)+'</p></div><button class="action" style="width:100%" onclick="renderWriteQuestion()">Preguntar otra cosa</button>')}
function renderNoAnswer(text){jPanel('😊 Jenny','renderWriteQuestion()','<div class="help-hero"><h2>Eso no me lo sé 😅</h2><p>No quiero inventarme nada. Prueba a contármelo con otras palabras o, si prefieres, escríbele a una persona por Telegram y te lo resuelve.</p></div><button class="action" style="width:100%" onclick="openTelegramSupport(decodeURIComponent(\''+encodeURIComponent(text)+'\'))">✈ Abrir Telegram (@'+PORTAL_TG+')</button><button class="secondary" style="width:100%;margin-top:10px" onclick="renderWriteQuestion()">Probar con otras palabras</button>')}
function askJenny(text,subject){text=(text||'').trim();if(!text){alert('Escribe tu consulta.');return}const st=jennySmall(text);if(st){renderJennyCard(st);return}const ms=jennyMatch(text);if(!ms.length){renderNoAnswer(text);return}const id=ms[0].id,key='thread_'+Date.now()+'_'+Math.random().toString(36).slice(2,8),now=new Date().toISOString(),sub=subject||text.slice(0,48);db.supportThreads=db.supportThreads||{};db.supportSent=db.supportSent||[];db.supportReplies=db.supportReplies||[];db.supportThreads[key]={key,subject:sub,body:text,type:id,used:[id],attempts:1,createdAt:now,active:true};db.supportSent.unshift({id:Date.now(),threadKey:key,subject:sub,body:text,date:now,status:'respondido automáticamente',autoType:id,attempt:1});db.supportReplies.unshift({id:Date.now()+1,threadKey:key,subject:'Re: '+sub,body:jennyReply(id,1),date:now,from:'Jenny · Ayuda automática',status:'respondido',attempt:1});save();showJohnnyConversation(key)}
function answerUserQuery(){askJenny((document.querySelector('#autoQuery')||{}).value,'Consulta del conductor')}
function saveSupportMessage(){askJenny((document.querySelector('#supportBody')||{}).value,(document.querySelector('#supportSubject')||{}).value)}
function continueJohnny(enc){const key=decodeURIComponent(enc),th=(db.supportThreads||{})[key];if(!th)return;if((th.attempts||0)>=3){th.escalated=true;th.active=false;save();showJohnnyConversation(key);return}th.attempts=(th.attempts||0)+1;const now=new Date().toISOString(),ms=jennyMatch(th.body,th.used||[]);let body;if(ms.length){th.used=(th.used||[]).concat(ms[0].id);body=jennyReply(ms[0].id,th.attempts)}else body='Mmm, con eso no he dado en el clavo 😅 Cuéntame con otras palabras qué quieres hacer o qué pantalla estás viendo.';db.supportSent.unshift({id:Date.now(),threadKey:key,subject:th.subject,body:'Necesito otra respuesta.',date:now,status:'respondido automáticamente',autoType:th.type,attempt:th.attempts});db.supportReplies.unshift({id:Date.now()+1,threadKey:key,subject:'Re: '+th.subject,body,date:now,from:'Jenny · Ayuda automática',status:'respondido',attempt:th.attempts});save();showJohnnyConversation(key)}
function showJohnnyConversation(key){const th=(db.supportThreads||{})[key];if(!th)return renderSupportMessages();const replies=(db.supportReplies||[]).filter(x=>x.threadKey===key),sent=(db.supportSent||[]).filter(x=>x.threadKey===key);const hist=[...sent.map(x=>({u:1,date:x.date,body:x.body})),...replies.map(x=>({u:0,date:x.date,body:x.body}))].sort((a,b)=>new Date(a.date)-new Date(b.date));const hh=hist.map(m=>'<div class="subpage-row"><span class="sicon">'+(m.u?'👤':'😊')+'</span><div style="flex:1"><b>'+(m.u?'Tú':'Jenny')+'</b><small style="display:block;color:#64748b;margin-top:3px">'+escapeHtml(m.body)+'</small></div></div>').join('');let f='';const enc=encodeURIComponent(key);if(th.escalated){f='<div class="help-hero"><h3>🧑‍💻 Mejor con una persona</h3><p>Esto ya se me escapa. Escríbele a soporte por Telegram y te lo resuelven.</p><button class="action" style="width:100%;margin-top:10px" onclick="openTelegramSupport(decodeURIComponent(\''+encodeURIComponent(th.body)+'\'))">✈ Abrir Telegram (@'+PORTAL_TG+')</button><button class="secondary" style="width:100%;margin-top:8px" onclick="resolveJohnny(\''+enc+'\')">Cerrar conversación</button></div>'}else if(th.resolved){f='<div class="help-hero"><h3>✅ Resuelto</h3><p>La conversación se ha cerrado.</p></div>'}else{f='<div class="help-hero"><h3>😊 Jenny</h3><p>¿Te he ayudado a resolverlo?</p><div class="row" style="margin-top:10px"><button class="action" onclick="resolveJohnny(\''+enc+'\')">Sí, resuelto</button><button class="action" onclick="continueJohnny(\''+enc+'\')">'+(th.attempts>=3?'No, quiero hablar con una persona':'No, otra respuesta')+'</button></div></div>'}jPanel('💬 Conversación con Jenny','renderSendSupport()','<div class="help-hero"><h2>😊 Jenny</h2><p>'+escapeHtml(th.subject)+'</p></div><div class="subpage-list">'+hh+'</div>'+f)}
function showAutoAnswer(id){renderJennyCard(jennyReply(id,1))}
function jRow(icon,title,sub,fn){return '<button class="subpage-row" onclick="'+fn+'"><span class="sicon">'+icon+'</span><div style="flex:1;text-align:left"><b>'+title+'</b><small style="display:block;color:#64748b;margin-top:3px">'+sub+'</small></div><span>›</span></button>'}
function renderHelp(){jPanel('Ayuda','backToGeneralMenu()','<div class="help-hero"><h2>Ayuda a conductores</h2><p>Aquí tienes guías, respuestas rápidas y a Jenny para lo que necesites.</p></div><div class="subpage-list">'+jRow('📥','Ayuda con cargar datos','Dónde y cómo se carga cada dato en la app.','renderHelpCarga()')+jRow('❓','Preguntas frecuentes','Las dudas más habituales, resueltas.','renderFaq()')+jRow('😊','Pregúntale a Jenny','Escribe tu duda y te responde al momento.','renderSendSupport()')+jRow('✈','Hablar con una persona','Abre el chat de Telegram con soporte.','openTelegramSupport(\'\')')+jRow('💬','Mensajes','Tus conversaciones con Jenny.','renderSupportMessages()')+'</div>')}
function renderSendSupport(){jPanel('Pregúntale a Jenny','helpBack()','<div class="help-hero"><h2>😊 Hola, soy Jenny</h2><p>Cuéntame qué necesitas con tus palabras o elige una pregunta rápida. Si no sé algo, te lo digo y te paso con una persona.</p></div><div class="subpage-list">'+jRow('✍️','Escribir mi pregunta','Te contesto al momento.','renderWriteQuestion()')+jRow('⚡','Preguntas rápidas','Las dudas más comunes con un toque.','renderAutoHelp()')+jRow('✈','Hablar con una persona','Telegram (@'+PORTAL_TG+').','openTelegramSupport(\'\')')+'</div>')}
function renderWriteQuestion(){jPanel('Escribir mi pregunta','renderSendSupport()','<div class="help-hero"><h2>¿Qué necesitas?</h2><p>Escríbelo como lo dirías hablando. Por ejemplo: «se me olvidó iniciar la jornada» o «cómo apunto una propina».</p></div><textarea id="autoQuery" rows="6" placeholder="Escribe aquí tu pregunta…" style="width:100%;margin-top:6px;border-radius:14px;padding:12px;box-sizing:border-box"></textarea><button class="action" style="width:100%;margin-top:10px" onclick="answerUserQuery()">😊 Preguntar a Jenny</button>')}
function renderAutoHelp(){jPanel('Preguntas rápidas','renderSendSupport()','<div class="subpage-list">'+['viajes','aeropuerto','pago','corregir','jornada','gasolina','km','lector','pdf','nocuadra'].map(id=>{const e=jEntry(id);return jRow(e[1],e[2],'','showAutoAnswer(\''+id+'\')')}).join('')+'</div>')}
function renderFaq(){jPanel('Preguntas frecuentes','helpBack()','<div class="subpage-list">'+J_KB.filter(e=>e[0]!=='contacto').map(e=>'<details class="subpage-row" style="display:block"><summary style="cursor:pointer;list-style:none"><span class="sicon" style="display:inline-grid;margin-right:8px">'+e[1]+'</span><b>'+e[2]+'</b></summary><small style="display:block;color:#64748b;margin:8px 0 2px;line-height:1.45">'+e[4]+'</small></details>').join('')+'</div>')}
function renderHelpCarga(){const S=[['🧮','Calculadora','Escribe el importe y pulsa la plataforma (Bolt, Uber, Cabify o Privados). Para aeropuerto, usa el botón azul. Con «Importe automático» la app lee el precio de la otra ventana. Elige tarjeta o efectivo cuando te lo pregunte.'],['🧾','Facturación','Diario, Semanal y Mensual. Aquí corriges o borras un viaje, apuntas propinas y, en Semanal, las compensaciones por cancelaciones y la nómina.'],['◉','Control','Iniciar y finalizar jornada, corregir horas de días anteriores, apuntar gasolina y kilómetros (con GPS automático o a mano).'],['📍','GPS y lector de pantalla','El odómetro GPS cuenta los kilómetros con la jornada iniciada. El lector y la burbuja necesitan activar Portal Lector en Accesibilidad de Android.'],['📊','Informe','Elige el periodo, genera el informe y compártelo en PDF o imagen.'],['⚙️','Ajustes','Comisión, tasa de aeropuerto, objetivos, horarios prioritarios, burbuja, GPS y copia de seguridad.'],['👤','Cuenta','Inicia sesión para guardar tus datos en la nube y recuperarlos si cambias de móvil.']];jPanel('Ayuda con cargar datos','helpBack()','<div class="help-hero"><h2>Dónde se carga cada cosa</h2><p>Un repaso rápido por pantallas. Si te queda alguna duda, pregúntale a Jenny.</p></div><div class="subpage-list">'+S.map(s=>'<div class="subpage-row"><span class="sicon">'+s[0]+'</span><div><b>'+s[1]+'</b><small style="display:block;color:#64748b;margin-top:3px;line-height:1.45">'+s[2]+'</small></div></div>').join('')+'</div>')}
/* PDF e imagen del informe */
function reportCanvas(light){const out=document.querySelector('#reportOut');if(!out||!out.dataset.ready){alert('Primero genera el informe.');return null}const clean=x=>String(x||'').replace(/[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/gu,'').replace(/\s+/g,' ').trim();const period=clean((out.querySelector('.metric b')||{}).innerText),plats=[...out.querySelectorAll('.platform-summary .ps')].map(e=>[clean(e.childNodes[0].textContent),clean((e.querySelector('b')||{}).innerText)]),rows=[...out.querySelectorAll('table tr')].map(tr=>[...tr.children].map(c=>clean(c.innerText))).filter(r=>r.length>=2&&r[0]);const W=1080,P=56,RH=84,H=260+(plats.length?190:0)+rows.length*RH+150,cv=document.createElement('canvas');cv.width=W;cv.height=H;const g=cv.getContext('2d'),C=light?{bg:'#ffffff',row:'#f1f5f9',txt:'#0f172a',mut:'#475569',acc:'#1d4ed8'}:{bg:'#07111f',row:'#0e2038',txt:'#ffffff',mut:'#9fb4c8',acc:'#5fe6ff'};g.fillStyle=C.bg;g.fillRect(0,0,W,H);const hg=g.createLinearGradient(0,0,W,0);hg.addColorStop(0,'#0a3d9c');hg.addColorStop(1,'#0b6fd6');g.fillStyle=hg;g.fillRect(0,0,W,210);g.fillStyle='#fff';g.font='bold 54px sans-serif';g.textBaseline='alphabetic';g.fillText('Super Portal del Conductor',P,92);g.font='36px sans-serif';g.fillStyle='#dff3ff';g.fillText('Informe · '+period,P,152);let y=250;const fit=(t,mx,font)=>{g.font=font;while(g.measureText(t).width>mx&&t.length>3)t=t.slice(0,-2);return t};if(plats.length){const cw=(W-2*P-(plats.length-1)*16)/plats.length,col={Bolt:'#00b85c',Uber:'#1f2937',Cabify:'#7c3aed',Privados:'#2563eb'};plats.forEach((p,i)=>{const x=P+i*(cw+16);g.fillStyle=col[p[0]]||'#2563eb';g.beginPath();g.roundRect?g.roundRect(x,y,cw,150,22):g.rect(x,y,cw,150);g.fill();g.fillStyle='#fff';g.font='bold 30px sans-serif';g.textAlign='center';g.fillText(p[0],x+cw/2,y+54);g.font='bold 40px sans-serif';g.fillText(fit(p[1],cw-16,'bold 40px sans-serif'),x+cw/2,y+114);g.textAlign='left'});y+=190}rows.forEach((r,i)=>{if(i%2===0){g.fillStyle=C.row;g.fillRect(P-16,y,W-2*P+32,RH-6)}g.fillStyle=C.mut;g.textAlign='left';g.fillText(fit(r[0],W-2*P-300,'30px sans-serif'),P,y+52);g.fillStyle=C.txt;g.textAlign='right';g.font='bold 34px sans-serif';g.fillText(r[r.length-1],W-P,y+52);g.textAlign='left';y+=RH});g.fillStyle=C.mut;g.font='26px sans-serif';g.fillText('Generado el '+new Date().toLocaleDateString('es-ES')+' · Portal del Conductor',P,H-56);return cv}
function jpegToPdf(jb,w,h){const pw=595,ph=Math.round(595*h/w),enc=new TextEncoder(),parts=[],offs=[];let off=0;const push=x=>{const b=typeof x==='string'?enc.encode(x):x;parts.push(b);off+=b.length};push('%PDF-1.4\n');offs[1]=off;push('1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n');offs[2]=off;push('2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n');offs[3]=off;push('3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 '+pw+' '+ph+']/Resources<</XObject<</Im0 4 0 R>>>>/Contents 5 0 R>>endobj\n');offs[4]=off;push('4 0 obj<</Type/XObject/Subtype/Image/Width '+w+'/Height '+h+'/ColorSpace/DeviceRGB/BitsPerComponent 8/Filter/DCTDecode/Length '+jb.length+'>>stream\n');push(jb);push('\nendstream endobj\n');const cs='q '+pw+' 0 0 '+ph+' 0 0 cm /Im0 Do Q';offs[5]=off;push('5 0 obj<</Length '+cs.length+'>>stream\n'+cs+'\nendstream endobj\n');const xo=off;let x='xref\n0 6\n0000000000 65535 f \n';for(let i=1;i<=5;i++)x+=String(offs[i]).padStart(10,'0')+' 00000 n \n';push(x+'trailer<</Size 6/Root 1 0 R>>\nstartxref\n'+xo+'\n%%EOF');const all=new Uint8Array(off);let p=0;parts.forEach(b=>{all.set(b,p);p+=b.length});return all}
function bytesToB64(u){let s='';for(let i=0;i<u.length;i+=0x8000)s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));return btoa(s)}
async function shareReportFile(kind){const cv=reportCanvas(kind==='pdf');if(!cv)return;let b64,mime,name;const st=new Date().toISOString().slice(0,10);if(kind==='pdf'){const jb=Uint8Array.from(atob(cv.toDataURL('image/jpeg',.92).split(',')[1]),c=>c.charCodeAt(0));b64=bytesToB64(jpegToPdf(jb,cv.width,cv.height));mime='application/pdf';name='informe_'+st+'.pdf'}else{b64=cv.toDataURL('image/png').split(',')[1];mime='image/png';name='informe_'+st+'.png'}const P=window.Capacitor&&Capacitor.Plugins&&Capacitor.Plugins.ShareFile;if(P&&P.shareFile){try{await P.shareFile({base64:b64,filename:name,mime,title:'Informe Portal del Conductor'});return}catch(e){alert('No se pudo abrir el menú de compartir.');return}}const a=document.createElement('a');a.href='data:'+mime+';base64,'+b64;a.download=name;document.body.appendChild(a);a.click();a.remove()}
function exportReportPdf(){shareReportFile('pdf')}
function shareReport(){shareReportFile('png')}
setTimeout(()=>{try{if(!window.db)return;let ch=false;(db.supportSent||[]).forEach(x=>{if(x.status==='pendiente'){x.status='cerrado';ch=true}});const n=(db.supportMessages||[]).length;db.supportMessages=(db.supportMessages||[]).filter(m=>!(m.status==='pendiente'&&/Derivaci/.test(m.from||'')));if(db.supportMessages.length!==n)ch=true;if(ch)save()}catch(e){}},3000);
'''
J='android/app/src/main/java/com/portal/conductor/'
SHARE=r'''package com.portal.conductor;

import android.content.Intent;
import android.net.Uri;
import android.util.Base64;
import androidx.core.content.FileProvider;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;

@CapacitorPlugin(name = "ShareFile")
public class ShareFilePlugin extends Plugin {
    @PluginMethod
    public void shareFile(PluginCall call) {
        try {
            String b64 = call.getString("base64");
            String name = call.getString("filename", "informe.pdf");
            String mime = call.getString("mime", "application/pdf");
            String title = call.getString("title", "Compartir");
            if (b64 == null) { call.reject("Sin datos"); return; }
            name = name.replaceAll("[^A-Za-z0-9._-]", "_");
            File dir = new File(getContext().getCacheDir(), "shared");
            dir.mkdirs();
            File f = new File(dir, name);
            FileOutputStream o = new FileOutputStream(f);
            o.write(Base64.decode(b64, Base64.DEFAULT));
            o.close();
            Uri uri = FileProvider.getUriForFile(getContext(), getContext().getPackageName() + ".shareprovider", f);
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType(mime);
            i.putExtra(Intent.EXTRA_STREAM, uri);
            i.putExtra(Intent.EXTRA_SUBJECT, title);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            Intent ch = Intent.createChooser(i, title);
            ch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(ch);
            call.resolve();
        } catch (Exception e) {
            call.reject("No se pudo compartir: " + e.getMessage());
        }
    }

    @PluginMethod
    public void openUrl(PluginCall call) {
        try {
            String u = call.getString("url");
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(u));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(i);
            call.resolve();
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }
}
'''
PROV='package com.portal.conductor;\n\nimport androidx.core.content.FileProvider;\n\npublic class PortalFileProvider extends FileProvider {\n}\n'
def put(path,txt):
    os.makedirs(os.path.dirname(path),exist_ok=True); open(path,'w',encoding='utf-8').write(txt)
put(J+'ShareFilePlugin.java',SHARE); put(J+'PortalFileProvider.java',PROV)
put('android/app/src/main/res/xml/portal_share_paths.xml','<?xml version="1.0" encoding="utf-8"?>\n<paths>\n    <cache-path name="shared" path="shared/" />\n</paths>\n')
rep=[]
def edit(path,old,new,label):
    t=open(path,encoding='utf-8').read(); n=t.count(old)
    if n>=1: t=t.replace(old,new,1); open(path,'w',encoding='utf-8').write(t)
    rep.append((label,n))
edit(J+'MainActivity.java','registerPlugin(GpsOdometerPlugin.class);','registerPlugin(GpsOdometerPlugin.class);\n        registerPlugin(ShareFilePlugin.class);','registrar-plugin')
M='android/app/src/main/AndroidManifest.xml'
mt=open(M,encoding='utf-8').read()
if 'portal_share_paths' not in mt:
    edit(M,'    </application>','        <provider android:name="com.portal.conductor.PortalFileProvider" android:authorities="${applicationId}.shareprovider" android:exported="false" android:grantUriPermissions="true"><meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/portal_share_paths"/></provider>\n    </application>','manifest-provider')
SR=J+'ScreenReaderService.java'
srt=open(SR,encoding='utf-8').read()
if 'ImageView' not in srt:
    edit(SR,'import android.widget.TextView;','import android.widget.TextView;\nimport android.widget.ImageView;\nimport android.graphics.Bitmap;\nimport android.graphics.Canvas;\nimport android.graphics.drawable.Drawable;\nimport android.view.ViewOutlineProvider;','burbuja-imports')
    edit(SR,'private TextView bubble;','private ImageView bubble;','burbuja-campo')
    edit(SR,'''        bubble = new TextView(this);
        bubble.setText("\\u20AC");
        bubble.setTextColor(Color.WHITE);
        bubble.setTextSize(24);
        bubble.setGravity(Gravity.CENTER);''','''        bubble = new ImageView(this);
        try {
            Drawable ic = getPackageManager().getApplicationIcon(getPackageName());
            int big = (int) (size * 1.5f);
            Bitmap bm = Bitmap.createBitmap(big, big, Bitmap.Config.ARGB_8888);
            Canvas cv = new Canvas(bm);
            ic.setBounds(0, 0, big, big);
            ic.draw(cv);
            int off = (big - size) / 2;
            bubble.setImageBitmap(Bitmap.createBitmap(bm, off, off, size, size));
        } catch (Throwable e) { }
        bubble.setScaleType(ImageView.ScaleType.CENTER_CROP);
        bubble.setPadding((int) (2 * d), (int) (2 * d), (int) (2 * d), (int) (2 * d));''','burbuja-icono')
    edit(SR,'        bubble.setBackground(g);','        bubble.setBackground(g);\n        bubble.setOutlineProvider(ViewOutlineProvider.BACKGROUND);\n        bubble.setClipToOutline(true);','burbuja-recorte')
for a,b,l in [('📄 Descargar PDF','📄 Compartir PDF','boton-pdf'),('↗ Compartir informe','🖼 Compartir imagen','boton-imagen')]:
    n=s.count(a); s=s.replace(a,b); rep.append((l,n))
css='''<style id="v36-style">
.airport-premium{gap:clamp(6px,2.4vw,12px)!important;padding-left:clamp(8px,2.6vw,14px)!important;padding-right:clamp(8px,2.6vw,14px)!important;overflow:hidden}
.airport-premium .airport-plane{flex:0 0 clamp(44px,14vw,60px)!important;width:clamp(44px,14vw,60px)!important;height:clamp(44px,14vw,60px)!important;font-size:clamp(22px,7vw,30px)!important}
.airport-premium .airport-copy{min-width:0;flex:1 1 auto;padding-left:clamp(6px,2.4vw,12px)!important}
.airport-premium .airport-copy strong{font-size:clamp(19px,6.2vw,27px)!important;white-space:nowrap}
.airport-premium .airport-copy small{font-size:clamp(13px,4.5vw,19px)!important;white-space:nowrap}
.airport-chip{padding:4px clamp(6px,2.2vw,10px)!important}
.airport-chip small{font-size:clamp(9px,2.7vw,11px)!important}
.airport-chip b{font-size:clamp(11px,3.2vw,13px)!important}
.billing-eye,.results .totalMetric .billing-eye{width:clamp(32px,10.4vw,46px)!important;height:clamp(32px,10.4vw,46px)!important;flex:0 0 clamp(32px,10.4vw,46px)!important;border-radius:14px!important}
.billing-eye svg{width:clamp(21px,6.2vw,27px)!important;height:clamp(21px,6.2vw,27px)!important}
.metricLabelRow{gap:4px!important}
.results .metric small,.metricLabelRow small{min-width:0;font-size:clamp(9px,2.7vw,13px)!important;letter-spacing:0!important;overflow-wrap:normal;hyphens:none}
details.subpage-row summary::-webkit-details-marker{display:none}
</style>'''
s=re.sub(r'v3\.\d lector','v3.6 lector',s)
i=s.rfind('</body>')
s=s[:i]+'<script id="v36-script">\n'+JS+'\n</script>\n'+s[i:]
s=s.rstrip()+'\n'+css+'\n'
open(p,'w',encoding='utf-8').write(s)
for l,n in rep: print(f'{l}: {n}')
print('v3.6 aplicado')
