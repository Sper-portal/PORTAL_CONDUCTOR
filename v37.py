import re,os
if not os.path.exists('www/index.html'):
    os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
p='www/index.html'
s=open(p,encoding='utf-8').read()
if 'id="v37-script"' in s:
    print('v3.7 ya aplicado'); raise SystemExit
if 'id="v36-script"' not in s:
    raise SystemExit('ERROR: primero hay que tener aplicada la v3.6')
JS=r'''/* v3.7: guardar PDF, información renovada, editar viajes en Calculadora */
const APP_VERSION='v3.7';
function reportFileData(kind){const cv=reportCanvas(kind==='pdf');if(!cv)return null;const st=new Date().toISOString().slice(0,10);if(kind==='pdf'){const jb=Uint8Array.from(atob(cv.toDataURL('image/jpeg',.92).split(',')[1]),c=>c.charCodeAt(0));return{b64:bytesToB64(jpegToPdf(jb,cv.width,cv.height)),mime:'application/pdf',name:'informe_'+st+'.pdf'}}return{b64:cv.toDataURL('image/png').split(',')[1],mime:'image/png',name:'informe_'+st+'.png'}}
async function saveB64(b64,name,mime){const P=window.Capacitor&&Capacitor.Plugins&&Capacitor.Plugins.ShareFile;if(P&&P.saveFile){try{const r=await P.saveFile({base64:b64,filename:name,mime});alert('✅ Guardado en tu móvil:\n'+((r&&r.path)||'Descargas'));return}catch(e){}if(P.shareFile){try{await P.shareFile({base64:b64,filename:name,mime,title:name});return}catch(e){}}}const a=document.createElement('a');a.href='data:'+mime+';base64,'+b64;a.download=name;document.body.appendChild(a);a.click();a.remove()}
async function saveReportFile(kind){const f=reportFileData(kind);if(f)await saveB64(f.b64,f.name,f.mime)}
async function saveDataCopy(){const json=JSON.stringify(currentDbSnapshot(),null,1),b64=btoa(unescape(encodeURIComponent(json)));await saveB64(b64,'copia_portal_'+new Date().toISOString().slice(0,10)+'.json','application/json')}
function lastSyncText(){try{const v=localStorage.getItem('pdc_last_sync');if(!v)return'Todavía no se ha sincronizado en este móvil.';const d=new Date(v);return d.toLocaleDateString('es-ES')+' a las '+d.toLocaleTimeString('es-ES',{hour:'2-digit',minute:'2-digit'})}catch(e){return'—'}}
async function syncNow(){if(typeof hasRealCloud!=='function'||!hasRealCloud()){alert('No hay una cuenta iniciada. Inicia sesión para sincronizar.');return}const before=localStorage.getItem('pdc_last_sync');window.__pdcLastSig=null;await cloudPushData();const after=localStorage.getItem('pdc_last_sync');alert(after&&after!==before?'✅ Datos sincronizados.':'No se ha podido sincronizar. Revisa tu conexión e inténtalo de nuevo.');renderSyncInfo()}
function infoPage(title,paras,extra){jPanel('Información','renderInfo()','<div class="help-hero"><h2>'+title+'</h2>'+paras.map(p=>'<p style="margin-top:9px;line-height:1.5">'+escapeHtml(p)+'</p>').join('')+'</div>'+(extra||''))}
function renderSyncInfo(){infoPage('☁️ Datos y sincronización',['Tus datos se guardan en tu móvil y, si has iniciado sesión, también en la nube. Así puedes trabajar sin internet y no los pierdes si cambias de móvil: inicias sesión con tu cuenta y vuelven solos.','La sincronización es automática: se hace cuando dejas de usar la app unos segundos o la cierras, y solo si algo ha cambiado.','Última sincronización: '+lastSyncText()],'<button class="action" style="width:100%" onclick="syncNow()">☁️ Sincronizar ahora</button><button class="secondary" style="width:100%;margin-top:10px" onclick="saveDataCopy()">💾 Guardar copia de mis datos en el móvil</button>')}
function showInfoDetail(type){const T='✈ Abrir Telegram (@'+PORTAL_TG+')',tg='<button class="action" style="width:100%" onclick="openTelegramSupport(\'\')">'+T+'</button>';
if(type==='sincronizacion')return renderSyncInfo();
if(type==='actualizar')return infoPage('↻ Versión y actualizaciones',['Tienes instalada la versión '+APP_VERSION+'. La puedes ver también arriba a la derecha, en la pantalla principal.','Esta app se instala desde un archivo, no desde una tienda. Cuando hay una versión nueva te llega el archivo y lo instalas encima de la actual: no hace falta desinstalar y no pierdes tus datos.','Si te falta la última versión o algo no funciona tras actualizar, escribe a soporte.'],tg);
if(type==='privacidad')return infoPage('🔐 Privacidad y datos',['Tus datos son tuyos. Se usan solo para que la app funcione: calcular tu facturación, tus horas, tu gasolina y tus kilómetros.','El GPS solo suma los metros recorridos mientras tienes la jornada iniciada. No guarda tus rutas ni tus posiciones.','El lector de pantalla solo busca el importe del viaje y si se paga con tarjeta o efectivo. No guarda ni envía nada más de lo que ves en pantalla.','Tus datos no se venden ni se comparten con nadie.']);
if(type==='funciona')return infoPage('📖 Cómo funciona Portal del Conductor',['Calculadora: apunta tus viajes (también con Importe automático), y desde Últimos viajes puedes añadir propina, editar o borrar cada viaje.','Facturación: tus ingresos por día, semana y mes, con la facturación manual por plataforma, compensaciones y nómina.','Control: tu jornada, horas, gasolina y kilómetros (con GPS automático).','Informe: resumen por periodos que puedes guardar o compartir en PDF o imagen.','Ajustes: comisión, tasa de aeropuerto, objetivos, burbuja y GPS.'],'<button class="action" style="width:100%" onclick="renderHelpCarga()">📥 Ver la guía completa</button>');
if(type==='soporte')return infoPage('🛠️ Ayuda y soporte',['En Ayuda tienes una guía para cargar datos, preguntas frecuentes y a Jenny, que responde al momento a dudas sobre la app.','Si Jenny no sabe algo, te lo dice y puedes escribir a una persona por Telegram.'],'<button class="action" style="width:100%" onclick="renderHelp()">🛟 Ir a Ayuda</button><button class="secondary" style="width:100%;margin-top:10px" onclick="openTelegramSupport(\'\')">'+T+'</button>');
if(type==='condiciones')return infoPage('📄 Condiciones de uso',['Portal del Conductor es una herramienta de organización personal para conductores. Es gratuita y se ofrece tal cual, sin garantía de disponibilidad.','Las cifras las introduces tú o las lee la app de tu pantalla: revísalas siempre. La app no es asesoría fiscal ni laboral, y no sustituye a tu gestor.','Portal del Conductor no tiene relación con Bolt, Uber ni Cabify. Sus nombres pertenecen a sus propietarios y se usan solo para identificar las plataformas.','Cuida tu cuenta y tu contraseña: eres responsable de lo que se haga con ellas.']);
if(type==='privacidadLegal')return infoPage('🔒 Política de privacidad',['Responsable: Portal del Conductor. Contacto: Telegram @'+PORTAL_TG+'.','Datos que se guardan: tu cuenta (correo o teléfono), tus viajes, horas, gasolina, kilómetros, ajustes y la configuración de la app.','Para qué: solo para prestarte el servicio de la app. No se usan para publicidad ni se venden.','Dónde: en tu móvil y, si inicias sesión, en la nube, en los servidores del proveedor Supabase. El administrador de la app puede acceder técnicamente a estos datos para mantener el servicio.','Permisos: la ubicación solo suma kilómetros; el servicio de accesibilidad solo se usa para leer el importe y la forma de pago del viaje. No se guarda nada más.','Cuánto tiempo: mientras tengas cuenta. Puedes pedir una copia o el borrado de tus datos escribiendo por Telegram, y puedes guardar una copia tú mismo desde Datos y sincronización.','Tus derechos: acceso, rectificación, supresión, oposición, limitación y portabilidad. Escríbenos y te respondemos.','Este texto puede actualizarse; la versión vigente es la que ves aquí.'],tg)}
function renderInfo(){const R=(i,t,s,f)=>'<button class="subpage-row" onclick="'+f+'"><span class="sicon">'+i+'</span><div style="flex:1"><b>'+t+'</b><small style="display:block;color:#64748b;margin-top:3px">'+s+'</small></div><span>›</span></button>';jPanel('Información','backToGeneralMenu()','<div class="info-center"><div class="info-logo">🚗</div><div class="info-version"><b>Super Portal del Conductor</b><br>Versión de la app: '+APP_VERSION+'</div></div><div class="subpage-list">'+R('↻','Versión y actualizaciones','Qué versión tienes y cómo actualizar.',"showInfoDetail('actualizar')")+R('🔐','Privacidad y datos','Qué se guarda y qué no.',"showInfoDetail('privacidad')")+R('☁️','Datos y sincronización','Última sincronización y copia de tus datos.',"showInfoDetail('sincronizacion')")+R('📖','Cómo funciona Portal del Conductor','Un repaso a todos los apartados.',"showInfoDetail('funciona')")+R('🛠️','Ayuda y soporte','Jenny, preguntas frecuentes y Telegram.',"showInfoDetail('soporte')")+R('📄','Condiciones de uso','Reglas básicas de uso de la app.',"showInfoDetail('condiciones')")+R('🔒','Política de privacidad','Cómo se tratan tus datos.',"showInfoDetail('privacidadLegal')")+'</div><div class="info-footer"><b>Super Portal del Conductor</b><br><span>Organiza. Controla. Factura.</span><br><small>© 2026 Portal del Conductor</small></div>')}
/* editar viajes desde Calculadora */
function closeCalcEdit(){const o=document.getElementById('calcEditModal');if(o)o.remove()}
function editCalcTrip(id){const t=db.trips.find(x=>String(x.id)===String(id));if(!t)return;closeCalcEdit();const cur=t.platform==='Bolt'&&t.airport?'BoltAirport':t.platform,opts=[['Bolt','Bolt'],['BoltAirport','Bolt · Aeropuerto ✈'],['Uber','Uber'],['Cabify','Cabify'],['Privados','Privados']].map(([v,l])=>'<option value="'+v+'"'+(cur===v?' selected':'')+'>'+l+'</option>').join(''),pay='<option value=""'+(t.payment!=='cash'&&t.payment!=='card'?' selected':'')+'>Sin indicar</option><option value="cash"'+(t.payment==='cash'?' selected':'')+'>💵 Efectivo</option><option value="card"'+(t.payment==='card'?' selected':'')+'>💳 Tarjeta</option>',ov=document.createElement('div');ov.id='calcEditModal';ov.style.cssText='position:fixed;inset:0;background:rgba(2,8,20,.75);z-index:9999;display:flex;align-items:flex-end;justify-content:center;padding:12px;box-sizing:border-box';ov.innerHTML='<div style="width:100%;max-width:520px;background:linear-gradient(160deg,#0d2a52,#071a33);border:2px solid #3fc8ff;border-radius:22px;padding:16px;color:#fff;box-shadow:0 0 24px #1e9bff66;box-sizing:border-box"><div style="font-weight:900;font-size:19px">✏️ Editar viaje</div><div style="color:#9fb4c8;font-size:13px;margin:4px 0 12px">La fecha ('+fmtDate(t.date)+') y la hora ('+(t.time||'—')+') se mantienen.</div><label style="font-size:13px;color:#cfe3f5">Plataforma</label><select id="ceP" class="input" style="width:100%;margin:4px 0 10px">'+opts+'</select><label style="font-size:13px;color:#cfe3f5">Importe del viaje (€)</label><input id="ceA" class="input" type="number" inputmode="decimal" min="0.01" step=".01" value="'+(Number(t.orig)||0)+'" style="width:100%;margin:4px 0 10px;box-sizing:border-box"><label style="font-size:13px;color:#cfe3f5">Forma de pago</label><select id="ceM" class="input" style="width:100%;margin:4px 0 4px">'+pay+'</select><div class="row" style="margin-top:14px;gap:8px"><button class="action" style="flex:1" onclick="saveCalcTripEdit(\''+t.id+'\')">Guardar cambios</button><button class="back" style="flex:1" onclick="closeCalcEdit()">Cancelar</button></div></div>';document.body.appendChild(ov)}
function saveCalcTripEdit(id){const t=db.trips.find(x=>String(x.id)===String(id));if(!t)return closeCalcEdit();const amount=Number(String((document.getElementById('ceA')||{}).value||'').replace(',','.'));let platform=(document.getElementById('ceP')||{}).value,airport=false;if(platform==='BoltAirport'){platform='Bolt';airport=true}const pay=(document.getElementById('ceM')||{}).value;if(!Number.isFinite(amount)||amount<=0){alert('Introduce un importe válido mayor que cero.');return}if(!['Bolt','Uber','Cabify','Privados'].includes(platform)){alert('Revisa la plataforma.');return}t.platform=platform;t.airport=airport;t.orig=Number(amount.toFixed(2));t.net=net(platform,t.orig,airport);if(pay==='cash'||pay==='card')t.payment=pay;closeCalcEdit();save();renderCalc()}
/* respuestas de Jenny al día con los cambios */
(function(){const set=(id,a)=>{const e=jEntry(id);if(e)e[4]=a};(function(){const e=jEntry('corregir');if(e)e[3]+=',edito^4,editar^4,modificar^4,cambiar un viaje^5,lapiz^4'})();set('propinas','En Calculadora, en Últimos viajes, pulsa el 🎁 del viaje y escribe lo que te dieron. Las propinas se cuentan aparte y no pagan comisión.');set('corregir','En Calculadora, en Últimos viajes, pulsa el lápiz ✏️ del viaje para cambiar la plataforma, el importe o la forma de pago. Con la papelera 🗑 lo borras. Los totales se recalculan solos.');set('otrodia','Usa las flechas de fecha de Calculadora o de Facturación para ir al día que quieras. Para corregir un viaje de otro día, ve a ese día en Calculadora y edítalo en Últimos viajes.');set('pdf','Genera el informe y usa «Guardar PDF» para dejarlo en la carpeta Descargas de tu móvil, o «Compartir PDF» o «Compartir imagen» para mandarlo por WhatsApp o correo.');set('copia','Con tu cuenta tus datos ya están a salvo en la nube. Además, en Información → Datos y sincronización puedes pulsar «Guardar copia de mis datos» y se guarda un archivo en tu móvil.')})();

/* totales grandes: se reducen solo si no caben */
function fitMetrics(){document.querySelectorAll('.results .metric>b').forEach(b=>{b.style.removeProperty('font-size');let fs=parseFloat(getComputedStyle(b).fontSize);let n=0;while(b.scrollWidth>b.clientWidth&&fs>13){fs-=1;n++;b.style.setProperty('font-size',fs+'px','important')}if(n&&fs>13)b.style.setProperty('font-size',(fs-1)+'px','important')})}
try{const c=document.querySelector('#content');new MutationObserver(()=>{clearTimeout(window.__fitT);window.__fitT=setTimeout(fitMetrics,30)}).observe(c,{childList:true,subtree:true});window.addEventListener('resize',()=>setTimeout(fitMetrics,60));setTimeout(fitMetrics,400)}catch(e){}
'''
rep=[]
def edit(path,old,new,label,cnt=1):
    t=open(path,encoding='utf-8').read(); n=t.count(old)
    if n==cnt: t=t.replace(old,new); open(path,'w',encoding='utf-8').write(t)
    rep.append((label,n))
SH='android/app/src/main/java/com/portal/conductor/ShareFilePlugin.java'
edit(SH,'import android.content.Intent;','import android.content.ContentValues;\nimport android.content.Intent;\nimport android.os.Environment;\nimport android.provider.MediaStore;\nimport com.getcapacitor.JSObject;\nimport java.io.OutputStream;','java-imports')
edit(SH,'    @PluginMethod\n    public void openUrl','''    @PluginMethod
    public void saveFile(PluginCall call) {
        try {
            String b64 = call.getString("base64");
            String name = call.getString("filename", "archivo");
            String mime = call.getString("mime", "application/octet-stream");
            if (b64 == null) { call.reject("Sin datos"); return; }
            if (android.os.Build.VERSION.SDK_INT < 29) { call.reject("Android antiguo"); return; }
            name = name.replaceAll("[^A-Za-z0-9._-]", "_");
            ContentValues v = new ContentValues();
            v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
            v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
            v.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/Portal del Conductor");
            Uri uri = getContext().getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
            if (uri == null) { call.reject("No se pudo crear el archivo"); return; }
            OutputStream o = getContext().getContentResolver().openOutputStream(uri);
            o.write(Base64.decode(b64, Base64.DEFAULT));
            o.close();
            JSObject r = new JSObject();
            r.put("path", "Descargas/Portal del Conductor/" + name);
            call.resolve(r);
        } catch (Exception e) {
            call.reject("No se pudo guardar: " + e.getMessage());
        }
    }

    @PluginMethod
    public void openUrl''','java-saveFile')
def sedit(old,new,label):
    global s
    n=s.count(old)
    if n==1: s=s.replace(old,new)
    rep.append((label,n))
sedit('${dailyTripsList(billAnchor)}','','facturacion-sin-lista-de-viajes')
sedit('''<button class="action" title="Añadir o editar propina" onclick="addTripTip('${t.id}','calc')">🎁 ${Number(t.tip)>0?'Editar':'+'}</button><button class="trash" onclick="delTrip(${t.id})">🗑</button>''','''<span class="trip-actions"><button class="action" title="Propina" onclick="addTripTip('${t.id}','calc')">🎁</button><button class="action" title="Editar viaje" onclick="editCalcTrip('${t.id}')">✏️</button><button class="trash" title="Borrar viaje" onclick="delTrip(${t.id})">🗑</button></span>''','calculadora-boton-editar')
sedit('<button class="action" onclick="exportReportPdf()">📄 Compartir PDF</button>','<button class="action" onclick="saveReportFile(\'pdf\')">💾 Guardar PDF</button><button class="action" onclick="exportReportPdf()">📄 Compartir PDF</button>','informe-guardar-pdf')
sedit('<button class="action" onclick="shareReport()">🖼 Compartir imagen</button>','<button class="action" onclick="saveReportFile(\'png\')">💾 Guardar imagen</button><button class="action" onclick="shareReport()">🖼 Compartir imagen</button>','informe-guardar-imagen')
sedit("window.__pdcLastSig=sig;","window.__pdcLastSig=sig;try{localStorage.setItem('pdc_last_sync',new Date().toISOString())}catch(e){}",'ultima-sincronizacion')
sedit('Diario, Semanal y Mensual. Aquí corriges o borras un viaje, apuntas propinas y, en Semanal, las compensaciones por cancelaciones y la nómina.','Diario, Semanal y Mensual, con totales por plataforma y facturación manual. En Semanal, las compensaciones por cancelaciones y la nómina.','ayuda-facturacion')
sedit('Elige tarjeta o efectivo cuando te lo pregunte.','Elige tarjeta o efectivo cuando te lo pregunte. En Últimos viajes puedes añadir propina (🎁), editar (✏️) o borrar (🗑) cada viaje.','ayuda-calculadora')
s=s.replace('(v3.6). ','(v3.7). ')
s=re.sub(r'v3\.\d lector','v3.7 lector',s)
css='''<style id="v37-style">
.triplist .trip{grid-template-columns:6px 54px 34px minmax(0,1fr) auto!important}
.trip-actions{display:flex;gap:3px;justify-content:flex-end;align-items:center;flex:none;width:max-content}
.trip-actions>*{flex:0 0 29px!important}
.triplist .trip .orig{white-space:normal!important;min-width:0!important;line-height:1.2;overflow-wrap:anywhere}
.trip-actions button,.trip-actions .action,.trip-actions .trash{width:29px!important;height:29px!important;min-width:0!important;padding:0!important;font-size:14px!important;display:grid!important;place-items:center;border-radius:9px!important}
</style>'''
i=s.rfind('</body>')
s=s[:i]+'<script id="v37-script">\n'+JS+'\n</script>\n'+s[i:]
s=s.rstrip()+'\n'+css+'\n'
open(p,'w',encoding='utf-8').write(s)
for l,n in rep: print(f'{l}: {n}')
print('v3.7 aplicado')
