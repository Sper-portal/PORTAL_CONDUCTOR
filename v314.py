# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.14)

Un solo archivo, se puede aplicar mas de una vez (la segunda no hace nada).
Necesita tener aplicada antes la v3.13. Si falta cualquier ancla NO se cambia nada.

  - Cancelaciones (Bolt/Uber/Cabify), compensaciones y nomina con auditoria completa (propinas 100 % del conductor).
  - Kilometros: guardado continuo, recuperacion y GPS sin perdidas.
  - Rendimiento: guardados agrupados, caches, copias fuera de la base de datos.
  - Nube: nunca pisa datos locales sin subir; fusion con copia de seguridad; reintentos; subida solo si hay cambios.
  - Bolt: estimacion de precio por tramos (ajustable en la app), aviso con NETO destacado y voz solo para Bolt.
  - Portada: texto «Portal del Conductor» un 20 % mas grande.
"""
import re, os, base64

if not os.path.exists('www/index.html'):
    os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
p = 'www/index.html'
J = 'android/app/src/main/java/com/portal/conductor/'
MAN = 'android/app/src/main/AndroidManifest.xml'
s = open(p, encoding='utf-8').read()
if 'id="v314-script"' in s:
    print('v3.14 ya aplicado'); raise SystemExit
if 'id="v313-script"' not in s:
    raise SystemExit('ERROR: primero hace falta tener aplicada la v3.13')
for f in (J + 'ScreenReaderService.java', J + 'ScreenReaderPlugin.java', J + 'OfferAnalyzer.java', MAN):
    if not os.path.exists(f):
        raise SystemExit('ERROR: no encuentro ' + f + ' (ejecuta el parche desde la carpeta portal). No se ha cambiado nada.')

# ---------------------------------------------------------------- JS y CSS
MODS = [
    ('01_pre.js', r'''/* ===================== v3.14 · ENGANCHE TEMPRANO CON LA NUBE =====================
   Se ejecuta ANTES del programa principal: así la primera consulta de sesión que hace la app al abrir (bootV33) ya pasa por aquí.
   - Si la sesión o el usuario tardan mucho (sin cobertura) se usa la sesión guardada en el teléfono en vez de dejar la app esperando.
   - La lectura de «driver_data» se entrega a PDC314.wrapDriverSelect (módulo de sincronización) para decidir con seguridad. */
(function(){
if(window.__pdcPre)return;window.__pdcPre=true;
const cfg=()=>Object.assign({pull:4000,sess:5000},window.__pdcSyncCfg||{});
const TIMEOUT={};
function storedSession(){
  try{
    for(let i=0;i<localStorage.length;i++){
      const k=localStorage.key(i);
      if(/^sb-.*-auth-token$/.test(k)){
        const s=JSON.parse(localStorage.getItem(k)||'null');const ss=s&&(s.currentSession||s);
        if(ss&&ss.user)return ss;
      }
    }
  }catch(e){}
  return null;
}
function hook(sb){
  try{
    if(!sb||sb.__pdcHooked||!sb.auth||typeof sb.from!=='function')return sb;
    sb.__pdcHooked=true;
    const _from=sb.from.bind(sb);sb.__rawFrom=_from;
    sb.from=function(table){
      const q=_from(table);
      if(table!=='driver_data')return q;
      return new Proxy(q,{get(t,prop){
        const v=Reflect.get(t,prop,t);
        if(prop==='select'&&typeof v==='function')return (...a)=>{
          const b=v.apply(t,a),P=window.PDC314;
          return P&&P.wrapDriverSelect?P.wrapDriverSelect(b,{login:!!P.inLogin}):b;
        };
        return typeof v==='function'?v.bind(t):v;
      }});
    };
    const _gs=sb.auth.getSession.bind(sb.auth);
    sb.auth.getSession=function(){
      return Promise.race([_gs(),new Promise(r=>setTimeout(()=>r(TIMEOUT),navigator.onLine===false?1000:cfg().sess))]).then(x=>x===TIMEOUT?{data:{session:storedSession()},error:null}:x);
    };
    const _gu=sb.auth.getUser.bind(sb.auth);
    sb.auth.getUser=async function(){
      const fb=async()=>{const s=await sb.auth.getSession();return {data:{user:s&&s.data&&s.data.session?s.data.session.user:null},error:null}};
      if(navigator.onLine===false)return fb();
      try{return await Promise.race([_gu(),new Promise((_,rej)=>setTimeout(()=>rej(new Error('tiempo agotado')),cfg().pull*0.75))])}
      catch(e){return fb()}
    };
  }catch(e){console.warn('v3.14 enganche nube',e)}
  return sb;
}
window.__pdcHookSB=hook;
try{
  const S=window.supabase;
  if(S&&typeof S.createClient==='function'&&!S.createClient.__pdc){
    const orig=S.createClient;
    const w=function(){return hook(orig.apply(this,arguments))};w.__pdc=1;
    try{S.createClient=w}catch(e){}
    if(S.createClient!==w){                                 // la biblioteca real no deja cambiar la función: se sustituye el objeto
      const copy=Object.assign({},S);copy.createClient=w;
      window.supabase=copy;
    }
  }
}catch(e){console.warn('v3.14 enganche temprano',e)}
})();
'''),
    ('05_early.js', r'''/* ===================== v3.14 · ARRANQUE TEMPRANO =====================
   Se carga justo después del programa principal y ANTES de los demás parches (también del GPS). Vigila window.__gpsDay y
   window.__gpsLiveKm, que el código del GPS usa para saber a qué día pertenecen los km en curso: así quedan guardados en la jornada
   (sobreviven a que Android cierre la app) y, al reabrir pasada la medianoche, no se apuntan al día equivocado. */
(function(){
if(window.__pdcEarly)return;window.__pdcEarly=true;
const nm=v=>{const n=Number(v);return Number.isFinite(n)?n:0};
const r1=v=>Math.round(nm(v)*10)/10;
let gd=window.__gpsDay,lk=window.__gpsLiveKm;
try{if(db.activeSession&&db.activeSession.gpsDay)gd=db.activeSession.gpsDay}catch(e){}
Object.defineProperty(window,'__gpsDay',{configurable:true,enumerable:true,
  get(){try{const a=db&&db.activeSession;if(a)return a.gpsDay||dateKey(a.start)}catch(e){}return gd},   // con jornada en curso manda el día guardado (la memoria, tras reabrir la app, trae el del inicio)
  set(v){
    gd=v;
    try{const a=db.activeSession;if(a&&v&&a.gpsDay!==v){a.gpsDay=v;a.liveKm=0;a.nat=0;window.save()}}catch(e){}
  }});
Object.defineProperty(window,'__gpsLiveKm',{configurable:true,enumerable:true,
  get(){return lk},
  set(v){
    lk=v;
    try{
      const a=db.activeSession;if(!a)return;
      const n=nm(v);if(n<=0)return;
      // acumula sin perder lo ya contado aunque el contador nativo se reinicie; «nat» = última lectura nativa (guardada también)
      const prev=nm(a.liveKm),last=nm(a.nat);
      if(n>=last-0.05)a.liveKm=r1(prev+(n-last));else a.liveKm=r1(prev+n);
      a.nat=n;
      if(!a.gpsDay)a.gpsDay=dateKey(a.start);
      window.save();
    }catch(e){}
  }});
})();
'''),
    ('10_core.js', r'''/* ===================== v3.14 · NÚCLEO =====================
   Una sola fuente de verdad para los totales: viajes (netos), propinas (íntegras) y compensaciones
   (cancelaciones + ajustables), todo por FECHA. Cada importe se cuenta una sola vez, en el día, la semana y el mes.
   Además: mes correcto el día 29-31, caché de viajes por día y guardado diferido (con vaciado al salir). */
(function(){
if(window.PDC314&&window.PDC314.core)return;
const P=window.PDC314=window.PDC314||{};P.core=true;
const PLATS=['Bolt','Uber','Cabify','Privados'];
const nm=v=>{const n=Number(v);return Number.isFinite(n)?n:0};
const ps=v=>Math.max(0,nm(v));
let LV=0;                                   // versión de los datos: sube con cada guardado
P.bump=()=>{LV++};
P.version=()=>LV;

/* ---------- compensaciones por fecha (cancelaciones + ajustables) ---------- */
const ZERO=Object.freeze({cancellations:0,adjustable:0,total:0,byPlat:Object.freeze({Bolt:0,Uber:0,Cabify:0,Privados:0})});
let cIdx=null,cV=-1,cDb=null;
function compIndex(){
  if(cIdx&&cV===LV&&cDb===db)return cIdx;
  const idx=new Map();
  let store={};
  try{store=billingCompensationStore()||{}}catch(e){store={}}
  for(const key of Object.keys(store)){
    let entries=[];
    try{entries=billingCompensationEntries(key)||[]}catch(e){entries=[]}
    for(const e of entries){
      if(!e)continue;
      const date=String(e.date||key).slice(0,10);
      const c=ps(e.cancellations),a=ps(e.adjustable);
      if(!c&&!a)continue;
      let r=idx.get(date);
      if(!r){r={cancellations:0,adjustable:0,total:0,byPlat:{Bolt:0,Uber:0,Cabify:0,Privados:0}};idx.set(date,r)}
      const pl=PLATS.includes(e.platform)?e.platform:'Bolt';   // lo antiguo (sin plataforma) siempre fue de Bolt
      r.cancellations+=c;r.adjustable+=a;r.total+=c+a;r.byPlat[pl]+=c+a;
    }
  }
  cIdx=idx;cV=LV;cDb=db;return idx;
}
P.compOnDate=k=>compIndex().get(k)||ZERO;
P.compEntriesOnDate=function(k){
  const out=[];let store={};
  try{store=billingCompensationStore()||{}}catch(e){}
  for(const key of Object.keys(store)){
    let entries=[];try{entries=billingCompensationEntries(key)||[]}catch(e){}
    for(const e of entries){if(e&&String(e.date||key).slice(0,10)===k)out.push({key,entry:e})}
  }
  return out;
};

/* ---------- viajes por día (caché) ---------- */
let dIdx=null,dArr=null,dLen=-1,dV=-1;
window.dayTrips=function(k){
  const arr=db.trips||[];
  if(!dIdx||dArr!==arr||dLen!==arr.length||dV!==LV){
    dIdx=new Map();
    for(const t of arr){let l=dIdx.get(t.date);if(!l){l=[];dIdx.set(t.date,l)}l.push(t)}
    dArr=arr;dLen=arr.length;dV=LV;
  }
  const l=dIdx.get(k);return l?l.slice():[];
};

/* ---------- totales ---------- */
// calcDayComp: la pantalla principal de algunas versiones lo suma aparte; ahora ya va dentro de fact(k)
window.calcDayComp=function(k){return 0};
window.fact=function(k){return baseFact(k)+tipsForDay(k)+P.compOnDate(k).total};
window.commission=function(k){return commissionAmount(baseFact(k)+P.compOnDate(k).total)};   // las propinas nunca pagan comisión

const _billingDay=window.billingDay;
window.billingDay=function(k){
  const x=_billingDay(k);
  const c=P.compOnDate(k);
  x.comp=c;
  x.trips=x.ts.length;                    // la tarjeta diaria de Facturación pintaba «Viajes: undefined»
  if(c.total>0){
    x.f+=c.total;
    for(const p of PLATS)x.plat[p]=(Number(x.plat[p])||0)+(c.byPlat[p]||0);
    x.card+=c.total;                       // las compensaciones las ingresa la plataforma (no son efectivo)
  }
  x.comm=commissionAmount((Number(x.base)||0)+c.total);
  x.pct=x.f?x.g/x.f*100:0;
  return x;
};

window.periodData=function(type,offset){
  let start,end;
  if(type==='weekly'){[start,end]=weekBounds(offset)}
  else{
    const d=new Date(today()+'T12:00:00');
    d.setDate(1);                           // evita el salto de mes cuando hoy es 29, 30 o 31
    d.setMonth(d.getMonth()+offset);
    start=new Date(d.getFullYear(),d.getMonth(),1,12);
    end=new Date(d.getFullYear(),d.getMonth()+1,0,12);
  }
  let total=0,c=0,card=0,g=0,trips=0,tips=0,base=0,plat={Bolt:0,Uber:0,Cabify:0,Privados:0},canc=0,adj=0;
  for(let d=new Date(start);d<=end;d.setDate(d.getDate()+1)){
    const k=dateKey(d),x=billingDay(k);
    total+=x.f;c+=x.c;card+=x.card;g+=x.g;trips+=x.ts.length;tips+=x.tips||0;base+=x.base||0;
    canc+=x.comp?x.comp.cancellations:0;adj+=x.comp?x.comp.adjustable:0;
    for(const p of PLATS)plat[p]+=x.plat[p];
  }
  return {start,end,total,cash:c,card,g,trips,tips,base,plat,
    comm:commissionAmount(Math.max(0,total-tips)),
    pct:total?g/total*100:0,
    compensation:{cancellations:canc,adjustable:adj}};
};

/* ---------- guardado diferido ---------- */
const SAVE_BURST=300;                        // varias acciones seguidas se juntan en una sola escritura
const SAVE_QUIET=1500;                       // una acción aislada se escribe en seguida (como hacía la versión original)
let dirty=false,tm=null,lastFlush=0;
P.storageError=false;
function showStorageProblem(msg){
  P.storageError=true;
  try{
    let t=document.getElementById('pdcStorageWarn');
    if(!t){t=document.createElement('div');t.id='pdcStorageWarn';t.style.cssText='position:fixed;left:8px;right:8px;top:8px;z-index:100000;background:#7f1d1d;color:#fff;border:2px solid #fca5a5;border-radius:14px;padding:12px 14px;font:700 14px system-ui;text-align:center';document.body.appendChild(t)}
    t.textContent=msg;t.style.display='block';clearTimeout(t._h);t._h=setTimeout(()=>{t.style.display='none'},15000);
  }catch(e){}
}
P.putLS=function(key,val){
  try{localStorage.setItem(key,val);return true}
  catch(e){
    try{localStorage.removeItem('pdc_trip_backups_v2');localStorage.setItem(key,val);return true}catch(e2){}
    try{localStorage.removeItem('pdc_pre_merge_backup');localStorage.setItem(key,val);return true}catch(e3){}
    showStorageProblem('⚠️ No se puede guardar: la memoria del navegador está llena. Haz una copia de seguridad y libera espacio.');
    return false;
  }
};
function accountRecKey(){
  try{
    const pr=JSON.parse(localStorage.getItem(AUTH_KEY)||'null');
    if(pr&&pr.loggedIn&&pr.identifier&&pr.identifier!=='dispositivo-local')return ACCOUNT_PREFIX+authHash(pr.identifier);
  }catch(e){}
  return null;
}
const recMeta={};
function writeAccountCopy(json){
  const rk=accountRecKey();if(!rk)return;
  let meta=recMeta[rk];
  if(!meta){
    const raw=localStorage.getItem(rk);if(!raw)return;          // sin registro local de cuenta (cuentas de la nube): nada que copiar
    try{meta=JSON.parse(raw);delete meta.data}catch(e){return}
    recMeta[rk]=meta;
  }
  const rec=Object.assign({},meta,{data:'__PDC_DATA__',updatedAt:new Date().toISOString()});
  P.putLS(rk,JSON.stringify(rec).replace('"__PDC_DATA__"',()=>json));
}
function flushNow(){
  if(!dirty)return true;
  dirty=false;clearTimeout(tm);tm=null;lastFlush=Date.now();
  try{
    if(P.syncMark)P.syncMark();                 // «hay cambios sin subir a la nube»: se anota ANTES de guardar los datos
    if(window.backupTripsEighteenMonths)window.backupTripsEighteenMonths();
    let json=JSON.stringify(db);
    let ok=P.putLS(KEY,json);
    if(!ok&&db.settings&&Array.isArray(db.settings.tripBackups)&&db.settings.tripBackups.length){
      // memoria llena por culpa de las copias antiguas: se dejan solo las dos últimas (los viajes siguen en db.trips)
      db.settings.tripBackups=db.settings.tripBackups.slice(-2);
      json=JSON.stringify(db);ok=P.putLS(KEY,json);
    }
    if(ok)writeAccountCopy(json);
    scheduleCloudPush();
    return ok;
  }catch(e){
    dirty=true;
    showStorageProblem('⚠️ No se pudo guardar: '+(e&&e.message?e.message:e));
    return false;
  }
}
window.flushSave=flushNow;
window.save=function(){
  LV++;dirty=true;
  if(!tm)tm=setTimeout(flushNow,Date.now()-lastFlush>SAVE_QUIET?0:SAVE_BURST);
};
P.saveNow=function(){window.save();return flushNow()};   // operaciones importantes (cancelaciones, compensaciones…): escritura inmediata
P.flush=flushNow;
P.isDirty=()=>dirty;
document.addEventListener('visibilitychange',()=>{if(document.hidden)flushNow()});
window.addEventListener('pagehide',flushNow);
window.addEventListener('beforeunload',flushNow);
document.addEventListener('freeze',flushNow);
try{
  const App=window.Capacitor&&Capacitor.Plugins&&Capacitor.Plugins.App;
  if(App&&App.addListener){App.addListener('pause',flushNow);App.addListener('appStateChange',s=>{if(s&&!s.isActive)flushNow()})}
}catch(e){}
// antes de cerrar sesión o borrar la cuenta se guarda lo pendiente (así nada se pierde ni se «resucita» después)
for(const fn of ['logoutV33','deleteAccountV33']){
  const o=window[fn];
  if(typeof o==='function')window[fn]=function(){flushNow();return o.apply(this,arguments)};
}

/* ---------- copias diarias de viajes: fuera de la base de datos (no se sincronizan ni duplican espacio) ---------- */
const BK='pdc_trip_backups_v2';
let bkDay=null,bkTimer=null;
function readBk(){try{return JSON.parse(localStorage.getItem(BK)||'[]')||[]}catch(e){return[]}}
window.backupTripsEighteenMonths=function(){
  try{
    const day=today();
    if(bkDay===day||bkTimer)return;
    bkTimer=setTimeout(()=>{
      bkTimer=null;
      try{
        const list=readBk();
        if(list.some(b=>b.day===day)){bkDay=day;return}
        const cutoff=new Date(day+'T12:00:00');cutoff.setMonth(cutoff.getMonth()-18);
        const trips=db.trips.filter(t=>t.date&&new Date(t.date+'T12:00:00')>=cutoff);
        list.push({day,createdAt:new Date().toISOString(),trips});
        while(list.length>2)list.shift();               // solo las dos últimas (cada una ya trae los viajes de 18 meses)
        if(P.putLS(BK,JSON.stringify(list)))bkDay=day;
      }catch(e){}
    },4000);
  }catch(e){}
};
// migración: las copias que vivían dentro de db.settings.tripBackups pasan a su propia clave (se conservan las más recientes)
P.migrateBackups=function(){
  try{
    const old=db.settings&&db.settings.tripBackups;
    if(!Array.isArray(old)||!old.length)return;
    const cur=readBk();
    const have=new Set(cur.map(b=>b.day));
    const keep=old.filter(b=>b&&b.day&&Array.isArray(b.trips)&&!have.has(b.day)).slice(-2);
    const merged=cur.concat(keep).sort((a,b)=>String(a.day).localeCompare(String(b.day))).slice(-2);
    if(merged.length&&!P.putLS(BK,JSON.stringify(merged))){
      db.settings.tripBackups=old.slice(-2);     // no cabe en otra clave: al menos se recorta lo que ocupa dentro de db
    }else db.settings.tripBackups=[];
    window.save();
  }catch(e){}
};
P.migrateBackups();
})();
'''),
    ('20_cancel.js', r'''/* ===================== v3.14 · CANCELACIONES =====================
   Botón «Cancelaciones» junto a Aeropuerto. Cada cancelación es un registro con fecha (compensación guardada en la semana
   de ese día, igual que las de Facturación → Semanal): suma al total del día, de la semana y del mes, pero NO cuenta como viaje. */
(function(){
const P=window.PDC314;if(!P||P.cancel)return;P.cancel=true;
const PLATS=['Uber','Bolt','Cabify'];
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cls=p=>p==='Bolt'?'bolt':p==='Uber'?'uber':p==='Cabify'?'cabify':'private';
const hm=()=>new Date().toLocaleTimeString('es-ES',{hour:'2-digit',minute:'2-digit'});
const r2=v=>Math.round((Number(v)||0)*100)/100;
const parseAmt=s=>{const n=Number(String(s==null?'':s).trim().replace(',','.'));return Number.isFinite(n)?n:NaN};
const money=v=>(typeof moneyDisplay==='function'&&typeof dailyBillingHidden!=='undefined')?moneyDisplay(v,dailyBillingHidden):euro(v);

/* ---------- registros ---------- */
function bucketFor(date){
  const key=billingWeekKey(date),store=billingCompensationStore();
  let raw=store[key];
  if(!raw)raw=store[key]={entries:[]};
  if(!Array.isArray(raw.entries)){      // registro antiguo (importes sueltos de la semana): se convierte sin perder nada
    const old=billingCompensationEntries(key).map(e=>Object.assign({},e));
    raw.entries=old;delete raw.cancellations;delete raw.adjustable;delete raw.date;
  }
  return {key,raw};
}
P.addCancellation=function({date,platform,amount,note}){
  amount=r2(amount);
  if(!(amount>0))throw new Error('importe no válido');
  if(!PLATS.includes(platform))throw new Error('plataforma no válida');
  const {key,raw}=bucketFor(date);
  const e={id:'canc-'+Date.now()+'-'+Math.random().toString(36).slice(2,7),date,cancellations:amount,adjustable:0,platform,note:String(note||'').trim().slice(0,120),time:hm(),daily:true,updatedAt:new Date().toISOString()};
  raw.entries.push(e);raw.updatedAt=e.updatedAt;
  P.saveNow();return e;
};
function findEntry(id){
  const store=billingCompensationStore();
  for(const key of Object.keys(store)){
    const list=billingCompensationEntries(key);
    const e=list.find(x=>x.id===id);
    if(e)return {key,entry:e};
  }
  return null;
}
P.updateCancellation=function(id,{platform,amount,adjustable,note}){
  const f=findEntry(id);if(!f)throw new Error('registro no encontrado');
  const {raw}=bucketFor(f.entry.date||f.key);
  const e=raw.entries.find(x=>x.id===id);if(!e)throw new Error('registro no encontrado');
  if(amount!=null){amount=r2(amount);if(amount<0)throw new Error('importe no válido');e.cancellations=amount}
  if(adjustable!=null){adjustable=r2(adjustable);if(adjustable<0)throw new Error('importe no válido');e.adjustable=adjustable}
  if(platform)e.platform=platform;
  if(note!=null)e.note=String(note).trim().slice(0,120);
  e.updatedAt=new Date().toISOString();raw.updatedAt=e.updatedAt;
  P.saveNow();return e;
};
P.deleteCancellation=function(id){
  const f=findEntry(id);if(!f)return false;
  const store=billingCompensationStore();
  const raw=store[f.key];
  if(raw&&Array.isArray(raw.entries)){
    raw.entries=raw.entries.filter(x=>x.id!==id);
    if(raw.entries.length)raw.updatedAt=new Date().toISOString();else delete store[f.key];
  }else{
    // registro antiguo con importes sueltos
    delete store[f.key];
  }
  P.saveNow();return true;
};

/* ---------- aviso verde ---------- */
function toastOk(msg){
  let t=document.getElementById('pdcToastOk');
  if(!t){t=document.createElement('div');t.id='pdcToastOk';t.className='pdc-toast-ok';document.body.appendChild(t)}
  t.textContent=msg;t.classList.add('show');
  clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),2600);
}
P.toastOk=toastOk;

/* ---------- ventana ---------- */
let sel=null,editId=null,saving=false;
function shield(){
  try{
    let z=document.getElementById('cnShield');if(z)z.remove();
    z=document.createElement('div');z.id='cnShield';z.style.cssText='position:fixed;inset:0;z-index:99995;background:transparent';
    const stop=e=>{e.preventDefault();e.stopPropagation()};
    ['click','pointerdown','touchstart','mousedown'].forEach(t=>z.addEventListener(t,stop,true));
    document.body.appendChild(z);setTimeout(()=>{if(z.parentNode)z.remove()},450);
  }catch(e){}
}
function closeModal(){const o=document.getElementById('cancelModal');if(o)o.remove();sel=null;editId=null;saving=false}
window.cancelClose=closeModal;
window.cancelPick=function(p){
  sel=p;
  document.querySelectorAll('#cancelModal .cn-plat').forEach(b=>b.classList.toggle('on',b.dataset.p===p));
  const a=document.getElementById('cnAmt');if(a)a.focus();
  const e=document.getElementById('cnErr');if(e)e.textContent='';
};
window.cancelOpen=function(id){
  closeModal();
  let ent=null,day=(typeof calcAnchor!=='undefined'&&calcAnchor)?calcAnchor:today();
  if(id){const f=findEntry(id);if(!f)return;ent=f.entry;day=String(ent.date||f.key).slice(0,10);editId=id;sel=PLATS.includes(ent.platform)?ent.platform:'Bolt'}
  const adj=ent&&Number(ent.adjustable)>0;
  const o=document.createElement('div');o.id='cancelModal';o.className='cn-overlay';
  o.innerHTML='<div class="cn-card" role="dialog" aria-modal="true" aria-label="Cancelaciones">'
   +'<div class="cn-title">✕ '+(ent?'Editar cancelación':'Cancelación')+'</div>'
   +'<div class="cn-day">'+esc(fmtDate(day))+'</div>'
   +'<div class="cn-label">Plataforma</div>'
   +'<div class="cn-plats">'+PLATS.map(p=>'<button type="button" class="cn-plat '+cls(p)+(sel===p?' on':'')+'" data-p="'+p+'" onclick="cancelPick(\''+p+'\')">'+p+'</button>').join('')+'</div>'
   +'<div class="cn-label">Importe de la cancelación (€)</div>'
   +'<input id="cnAmt" class="cn-in" type="text" inputmode="decimal" autocomplete="off" placeholder="0,00" value="'+(ent?esc(String(r2(ent.cancellations)).replace('.',',')):'')+'">'
   +(adj?'<div class="cn-label">Compensación ajustable (€)</div><input id="cnAdj" class="cn-in" type="text" inputmode="decimal" autocomplete="off" value="'+esc(String(r2(ent.adjustable)).replace('.',','))+'">':'')
   +'<div class="cn-label">Nota (opcional)</div>'
   +'<input id="cnNote" class="cn-in" type="text" maxlength="120" autocomplete="off" placeholder="Ej.: cliente no apareció" value="'+(ent?esc(ent.note||''):'')+'">'
   +'<div id="cnErr" class="cn-err" role="alert"></div>'
   +'<div class="cn-row"><button type="button" class="cn-save" id="cnSave" onclick="cancelSave()">✓ '+(ent?'Guardar cambios':'Guardar cancelación')+'</button><button type="button" class="cn-cancel" onclick="cancelClose()">Cancelar</button></div>'
   +'</div>';
  o.addEventListener('click',ev=>{if(ev.target===o)closeModal()});
  document.body.appendChild(o);
  window.cancelDayForSave=day;
  setTimeout(()=>{const a=document.getElementById('cnAmt');if(a){a.focus();a.select&&a.select()}},60);
};
window.cancelEdit=id=>window.cancelOpen(id);
window.cancelSave=function(){
  if(saving)return;
  const err=m=>{const e=document.getElementById('cnErr');if(e)e.textContent=m};
  const amt=parseAmt((document.getElementById('cnAmt')||{}).value);
  const note=(document.getElementById('cnNote')||{}).value||'';
  if(!sel){err('Elige la plataforma: Uber, Bolt o Cabify.');return}
  const adjEl=document.getElementById('cnAdj');
  const adj=adjEl?parseAmt(adjEl.value):null;
  if(!Number.isFinite(amt)||amt<0||(!editId&&amt<=0)){err('Escribe un importe mayor que 0 (por ejemplo 4,50).');return}
  if(adjEl&&(!Number.isFinite(adj)||adj<0)){err('Revisa la compensación ajustable.');return}
  if(amt>1000){err('El importe parece demasiado alto. Revísalo.');return}
  saving=true;
  const b=document.getElementById('cnSave');if(b)b.disabled=true;
  try{
    let shown;
    if(editId){P.updateCancellation(editId,{platform:sel,amount:amt,adjustable:adjEl?adj:null,note});shown=amt}
    else{P.addCancellation({date:window.cancelDayForSave||calcAnchor||today(),platform:sel,amount:amt,note});shown=amt}
    const label=sel;
    closeModal();
    shield();                 // un segundo toque rápido sobre «Guardar» no debe caer en lo que hay debajo (menú, borrar…)
    refreshView();
    toastOk('✓ Cancelación '+(editId?'actualizada':'guardada')+' · '+label+' · '+euro(shown));
  }catch(e){saving=false;if(b)b.disabled=false;err('No se pudo guardar: '+e.message)}
};
window.cancelDelete=function(id){
  const f=findEntry(id);if(!f)return;
  const e=f.entry;
  if(!confirm('¿Eliminar esta cancelación de '+(e.platform||'Bolt')+' ('+euro((Number(e.cancellations)||0)+(Number(e.adjustable)||0))+')?'))return;
  P.deleteCancellation(id);
  refreshView();
};
function refreshView(){
  const v=document.querySelector('.navbtn.active')?.dataset?.view;
  if(v==='billing')renderBilling();else if(v==='calc'||!v)renderCalc();
}

/* ---------- pantalla principal ---------- */
function platTotal(k,p){
  let s=0;
  for(const t of dayTrips(k))if(t.platform===p)s+=(Number(t.net)||0)+(Number(t.tip)||0);
  return s+(P.compOnDate(k).byPlat[p]||0);
}
function entryRow(item){
  const e=item.entry,c=Number(e.cancellations)||0,a=Number(e.adjustable)||0,pl=e.platform||'Bolt';
  const name=(c>0?'✕ ':'± ')+pl;
  const extra=(c>0&&a>0)?' + ajuste '+money(a):'';
  return '<div class="trip canc" data-cid="'+esc(e.id)+'"><i class="dot '+cls(pl)+'"></i><span class="platform-name '+cls(pl)+'">'+esc(name)+'</span><span>'+esc(e.time||'')+'</span>'
   +'<span class="orig">+'+money(c+a)+extra+(e.note?'<small style="display:block;color:#9fb4c8">'+esc(e.note)+'</small>':'')+'</span>'
   +'<span class="trip-actions"><button class="action" title="Editar cancelación" onclick="cancelEdit(\''+esc(e.id)+'\')">✏️</button><button class="trash" title="Borrar cancelación" onclick="cancelDelete(\''+esc(e.id)+'\')">🗑</button></span></div>';
}
function summaryHtml(title,trips,tripsEur,cancEur,cancN,total,tips,note){
  return '<div class="canc-sum"><div class="canc-sum-title">'+esc(title)+'</div><div class="canc-sum-grid">'
   +'<div class="cs-cell"><small>Total viajes</small><b>'+trips+'</b><span>'+money(tripsEur)+'</span></div>'
   +'<div class="cs-cell cs-canc"><small>Total cancelaciones</small><b>'+money(cancEur)+'</b><span>'+cancN+(cancN===1?' registro':' registros')+'</span></div>'
   +'<div class="cs-cell cs-total"><small>Facturación</small><b>'+money(total)+'</b><span>'+(note||'')+'</span></div>'
   +'</div>'+(tips>0?'<div class="canc-sum-tips">🎁 Propinas incluidas: <b>'+money(tips)+'</b></div>':'')+'</div>';
}
function daySummary(k,title){
  const x=billingDay(k);
  const tripsEur=x.ts.reduce((a,t)=>a+(Number(t.net)||0),0);
  const ents=P.compEntriesOnDate(k);
  return summaryHtml(title||'Resumen del día',x.ts.length,tripsEur,x.comp.total,ents.length,x.f,x.tips||0,'viajes + cancelaciones + propinas');
}
P.daySummary=daySummary;
function decorateCalc(){
  const root=document.getElementById('content');if(!root)return;
  const k=(typeof calcAnchor!=='undefined'&&calcAnchor)?calcAnchor:today();
  // 1) botón junto a Aeropuerto
  const ap=root.querySelector('.airport-premium');
  if(ap&&!root.querySelector('.airport-row')){
    const row=document.createElement('div');row.className='airport-row';
    ap.parentNode.insertBefore(row,ap);row.appendChild(ap);
    const b=document.createElement('button');b.type='button';b.className='cancel-btn';b.setAttribute('aria-label','Añadir cancelación');
    b.innerHTML='<span class="cancel-ico" aria-hidden="true">✕</span><span class="cancel-txt">Cancela&shy;ciones</span>';
    b.onclick=()=>window.cancelOpen();
    row.appendChild(b);
  }
  // 2) totales por plataforma (con las compensaciones de cada una)
  const ps=root.querySelector('.platform-summary');
  if(ps){
    for(const p of ['Bolt','Uber','Cabify','Privados']){
      const el=ps.querySelector('.ps.'+cls(p)+' b');
      if(el)el.innerHTML=money(platTotal(k,p));
    }
    // 3) resumen del día
    if(!root.querySelector('.canc-sum')){
      let anchor=ps.nextElementSibling;
      if(!(anchor&&anchor.classList.contains('note')))anchor=ps;
      anchor.insertAdjacentHTML('afterend',daySummary(k,'Resumen del día'));
    }
  }
  // 4) cancelaciones dentro de la lista del día (no cuentan como viaje)
  const list=root.querySelector('.triplist');
  if(list&&!list.querySelector('.trip.canc')){
    const items=P.compEntriesOnDate(k).sort((a,b)=>String(b.entry.time||'').localeCompare(String(a.entry.time||'')));
    for(const it of items){
      const html=entryRow(it);
      const rows=[...list.querySelectorAll('.trip:not(.canc)')];
      const t=String(it.entry.time||'');
      const before=rows.find(r=>{const tt=(r.children[2]&&r.children[2].textContent||'').trim();return tt&&t&&tt<t});
      if(before)before.insertAdjacentHTML('beforebegin',html);
      else{
        const last=[...list.querySelectorAll('.trip')].pop();
        if(last)last.insertAdjacentHTML('afterend',html);
        else{const head=list.querySelector('.triplist-head');(head||list).insertAdjacentHTML(head?'afterend':'beforeend',html)}
      }
    }
    const empty=list.querySelector('.empty');
    if(empty&&items.length)empty.style.display='none';
  }
}
const _rc=window.renderCalc;
window.renderCalc=function(){const r=_rc.apply(this,arguments);try{decorateCalc()}catch(e){console.warn('v3.14 calc',e)}return r};

/* ---------- editar una compensación de Facturación → Semanal ----------
   La función original rechazaba SIEMPRE la fecha («Fecha no válida»): su patrón estaba escrito con una barra de más (\\d).
   Se reescribe igual de simple (mismos avisos) pero validando bien, y conservando plataforma, nota e identificador. */
window.editBillingCompensation=function(key,id){
  const entries=billingCompensationEntries(key);
  const entry=entries.find(e=>e.id===id);if(!entry)return;
  const pl=entry.platform||'Bolt';
  let date=prompt('Fecha de la compensación (AAAA-MM-DD):',entry.date||key);if(date===null)return;
  date=String(date).trim();
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||isNaN(new Date(date+'T12:00:00'))){alert('Fecha no válida. Usa el formato AAAA-MM-DD (por ejemplo 2026-10-20).');return}
  if(billingWeekKey(date)!==key){alert('La fecha debe permanecer dentro de la semana del registro.');return}
  const c=prompt('Compensación de '+pl+' por cancelaciones (€):',String(entry.cancellations||0));if(c===null)return;
  const a=prompt('Compensación ajustable (€):',String(entry.adjustable||0));if(a===null)return;
  const num=v=>{const n=Number(String(v).trim().replace(',','.'));return Number.isFinite(n)?Math.max(0,Math.round(n*100)/100):NaN};
  const cancellations=num(c),adjustable=num(a);
  if(!Number.isFinite(cancellations)||!Number.isFinite(adjustable)){alert('Importe no válido.');return}
  const {raw}=bucketFor(key);
  const e=raw.entries.find(x=>x.id===id);if(!e)return;
  e.date=date;e.cancellations=cancellations;e.adjustable=adjustable;e.updatedAt=new Date().toISOString();raw.updatedAt=e.updatedAt;
  P.saveNow();renderBilling();
};

for(const fn of ['saveBillingCompensation','deleteBillingCompensation']){
  const o=window[fn];
  if(typeof o==='function')window[fn]=function(){const r=o.apply(this,arguments);try{P.flush()}catch(e){}return r};
}

/* ---------- facturación (diario / semanal / mensual) ---------- */
const ZEROP={cancellations:0,adjustable:0};
const _cfd=window.billingCompensationForDate;
window.billingCompensationForDate=function(d){return P.inRB?ZEROP:_cfd.apply(this,arguments)};   // el día ya trae las compensaciones dentro de billingDay()
function decorateBilling(){
  const root=document.getElementById('content');if(!root)return;
  const per=typeof billPeriod!=='undefined'?billPeriod:'daily';
  const first=root.querySelector('section.panel');
  if(!first||root.querySelector('.canc-sum'))return;
  if(per==='daily'){
    const x=billingDay(billAnchor);
    const note=x.comp.total>0?'<div class="note">Cancelaciones y compensaciones de este día incluidas automáticamente: Cancelaciones <b>'+euro(x.comp.cancellations)+'</b> · Ajustable <b>'+euro(x.comp.adjustable)+'</b>.</div>':'';
    first.insertAdjacentHTML('afterend',daySummary(billAnchor,'Resumen del día')+note);
  }else{
    const x=periodData(per==='weekly'?'weekly':'monthly',per==='weekly'?billWeekOffset:billMonthOffset);
    const cN=(()=>{let n=0;for(let d=new Date(x.start);d<=x.end;d.setDate(d.getDate()+1))n+=P.compEntriesOnDate(dateKey(d)).length;return n})();
    const tripsEur=Math.max(0,x.total-x.tips-x.compensation.cancellations-x.compensation.adjustable);
    first.insertAdjacentHTML('afterend',summaryHtml(per==='weekly'?'Resumen de la semana':'Resumen del mes',x.trips,tripsEur,x.compensation.cancellations+x.compensation.adjustable,cN,x.total,x.tips,'viajes + cancelaciones + propinas'));
  }
  // etiquetas de la lista semanal: plataforma real y nota
  root.querySelectorAll('.compensation-entry').forEach(div=>{
    const btn=div.querySelector('button[onclick^="editBillingCompensation"]');if(!btn)return;
    const m=/editBillingCompensation\('([^']*)','([^']*)'\)/.exec(btn.getAttribute('onclick')||'');if(!m)return;
    const f=findEntry(m[2]);if(!f||!f.entry.platform)return;
    const sm=div.querySelector('small');
    if(sm&&/Bolt por cancelaciones/.test(sm.textContent)){
      sm.textContent=f.entry.platform+' por cancelaciones';
      if(f.entry.note){const n=document.createElement('small');n.style.cssText='display:block;color:#9fb4c8';n.textContent=f.entry.note;sm.parentNode.appendChild(n)}
    }
  });
}
P.decorateBilling=decorateBilling;
const _rb=window.renderBilling;
window.renderBilling=function(){
  P.inRB=true;
  try{_rb.apply(this,arguments)}finally{P.inRB=false}
  try{decorateBilling();if(P.decorateBillingPayroll)P.decorateBillingPayroll()}catch(e){console.warn('v3.14 billing',e)}
};
})();
'''),
    ('30_payroll.js', r'''/* ===================== v3.14 · NÓMINA (cálculo nuevo) =====================
   Una sola función matemática (P.payrollCalc) con tres perfiles y dos reglas de comisión que NO se mezclan:
     · Regla «desde el primer euro»:   remuneración total = facturación × %
     · Regla «sobre el exceso»:        remuneración total = nómina base + (facturación − mínimo) × %   (si no se llega al mínimo: solo la base)
   Perfiles: Todo en nómina · Nómina + comisión en efectivo · Nómina variable + fijo (el fijo se paga en nómina o fuera de ella).
   El IRPF se calcula SOLO sobre la parte que va en nómina, nunca sobre la facturación del vehículo ni sobre el efectivo.
   Los meses ya cerrados con el cálculo anterior se conservan tal cual (con un botón para recalcularlos con el nuevo). */
(function(){
const P=window.PDC314;if(!P||P.payroll)return;P.payroll=true;
const nm=v=>{const n=Number(v);return Number.isFinite(n)?n:0};
const ps=v=>Math.max(0,nm(v));
const c2=v=>Math.round(nm(v)*100+(nm(v)>=0?1e-7:-1e-7))/100;
const clampPct=v=>Math.min(100,Math.max(0,nm(v)));
const PROFILES={allPayroll:'Todo en nómina',basePayrollVariableCash:'Nómina + comisión en efectivo',variableFixedCash:'Nómina variable + fijo',weeklyMonthly:'Nómina mensual semanal'};
P.PAYROLL_PROFILES=PROFILES;

/* ---------- el cálculo ---------- */
P.payrollCalc=function(i){
  const profile=['allPayroll','basePayrollVariableCash','variableFixedCash'].includes(i.profile)?i.profile:'variableFixedCash';
  const rule=i.rule==='minimum'?'minimum':'firstEuro';             // 'minimum' = «solo sobre el exceso del mínimo» (nombre heredado)
  const pct=clampPct(i.pct), minimum=c2(ps(i.minimum)), base=c2(ps(i.base)), fixed=c2(ps(i.fixed));
  const irpfPct=clampPct(i.irpf);
  const fixedVia=i.fixedVia==='payroll'?'payroll':'cash';
  const underBase=i.underBase==='total'?'total':'base';
  const vehicle=c2(ps(i.vehicle)), manual=c2(ps(i.manual)), tips=c2(ps(i.tips));
  const basis=c2(vehicle+manual);                                   // facturación sobre la que se calcula el %
  const reached=rule==='minimum'?basis>=minimum:true;
  const excess=rule==='minimum'?c2(Math.max(0,basis-minimum)):basis;
  const variable=c2(excess*pct/100);                                // comisión variable
  const total=rule==='minimum'?c2(base+variable):variable;          // remuneración (sin el fijo)
  let gross=0,cashComm=0,fixedPayroll=0,fixedCash=0,shortfall=0,lifted=false;
  if(profile==='allPayroll'){
    gross=total;
  }else if(profile==='basePayrollVariableCash'){
    if(total>=base){gross=base;cashComm=c2(total-base)}
    else{                                                           // la remuneración no llega a la nómina base: nunca se muestra un efectivo negativo
      shortfall=c2(base-total);
      if(underBase==='base'){gross=base;lifted=true}else gross=total;
      cashComm=0;
    }
  }else{
    gross=total;
    if(fixed>0){if(fixedVia==='payroll'){gross=c2(gross+fixed);fixedPayroll=fixed}else fixedCash=fixed}
  }
  const tax=c2(gross*irpfPct/100);
  const net=c2(gross-tax);
  const cash=c2(cashComm+fixedCash);
  const remuneration=c2(total+(profile==='variableFixedCash'?fixed:0));   // total antes de deducciones
  const final=c2(net+cash);
  return {model:2,profile,rule,pct,minimum,base,irpfPct,fixedVia,underBase,
    vehicle,manual,basis,reached,excess,variable,total,remuneration,
    gross,tax,net,cashCommission:cashComm,fixedExtra:profile==='variableFixedCash'?fixed:0,fixedPayroll,fixedCash,cash,
    shortfall,lifted,tips,final,finalWithTips:c2(final+tips)};
};

/* ---------- integración con el cálculo del programa ---------- */
const _calc=window.calculatePayrollForMonth;
window.calculatePayrollForMonth=function(x,cfg){
  cfg=cfg||{};
  const profile=cfg.payrollProfile||'variableFixedCash';
  if(profile==='weeklyMonthly')return _calc.call(this,x,cfg);       // este perfil tiene su propio cálculo (semanas, descuento de Bolt, contingencias)
  // el programa original ya sumaba el «ajustable» dentro del total del periodo y solo las cancelaciones quedaban fuera: se restan solo estas
  const comps=x&&x.compensation?nm(x.compensation.cancellations):0;
  if(cfg.model===1){                                                // mes guardado con el cálculo anterior: se conserva (el original sumaba aparte las compensaciones)
    return _calc.call(this,Object.assign({},x,{total:Math.max(0,nm(x.total)-comps)}),cfg);
  }
  const key=monthKeyFromDate(x.start||new Date(today()+'T12:00:00'));
  const manual=cfg.manualComp!=null?nm(cfg.manualComp):payrollCompensationForMonth(key);
  const r=P.payrollCalc({profile,rule:cfg.commissionMode,pct:cfg.commission,minimum:cfg.commissionMinimum,base:cfg.salaryBase,fixed:cfg.cashPayroll,
    fixedVia:cfg.fixedExtraVia,underBase:cfg.underBase,irpf:cfg.irpf,vehicle:Math.max(0,nm(x.total)-nm(x.tips)),manual,tips:nm(x.tips)});
  // campos con los nombres de siempre (los usa el resto de la app) + los nuevos
  return Object.assign(r,{commission:r.total,grossPayroll:r.gross,netPayroll:r.net,total:c2(r.net+r.cash),profile,modelTotal:r.total});
};

const _psm=window.payrollSettingsForMonth;
window.payrollSettingsForMonth=function(offset){
  try{P.migratePayroll()}catch(e){}
  const key=monthKeyFromOffset(offset);
  const snap=db.settings.payrollByMonth&&db.settings.payrollByMonth[key];
  const out=Object.assign({},_psm.call(this,offset));
  if(snap)out.model=snap.model===1?1:snap.model===2?2:(key<monthKeyFromOffset(0)?1:2);
  else out.model=2;
  if(out.fixedExtraVia==null)out.fixedExtraVia=db.settings.fixedExtraVia==='payroll'?'payroll':'cash';
  if(out.underBase==null)out.underBase=db.settings.underBase==='total'?'total':'base';
  return out;
};

/* ---------- migración: lo ya guardado se respeta ---------- */
function globalsCfg(){
  const s=db.settings;
  return {payrollProfile:s.payrollProfile||'variableFixedCash',commission:s.commission,commissionMode:s.commissionMode,commissionMinimum:s.commissionMinimum,
    salaryBase:Number(s.salaryBase??1425),cashPayroll:Number(s.cashPayroll??2000),irpf:Number(s.irpf??14.5),
    fixedExtraVia:s.fixedExtraVia==='payroll'?'payroll':'cash',underBase:s.underBase==='total'?'total':'base'};
}
function monthsWithData(){
  const set=new Set();
  for(const t of db.trips||[])if(t.date)set.add(String(t.date).slice(0,7));
  for(const k of Object.keys(db.manual||{}))set.add(k.slice(0,7));
  try{
    const st=billingCompensationStore();
    for(const key of Object.keys(st))for(const e of billingCompensationEntries(key)||[])set.add(String(e.date||key).slice(0,7));
  }catch(e){}
  return set;
}
P.migratePayroll=function(){
  const s=db&&db.settings;if(!s||s.payrollMigrated)return false;
  s.payrollMigrated=1;
  s.fixedExtraVia=s.fixedExtraVia==='payroll'?'payroll':'cash';
  s.underBase=s.underBase==='total'?'total':'base';
  s.payrollByMonth=s.payrollByMonth||{};
  const cur=monthKeyFromOffset(0),g=globalsCfg(),stamp=new Date().toISOString();
  for(const mk of monthsWithData()){
    if(mk>=cur)continue;
    if(!s.payrollByMonth[mk])s.payrollByMonth[mk]=Object.assign({},g,{model:1,frozenAt:stamp});   // mes cerrado: se queda con el cálculo con el que se veía
  }
  for(const [mk,snap] of Object.entries(s.payrollByMonth)){
    if(!snap||snap.model!=null)continue;
    if(mk<cur)snap.model=1;
    else{snap.model=2;if(snap.fixedExtraVia==null)snap.fixedExtraVia=s.fixedExtraVia;if(snap.underBase==null)snap.underBase=s.underBase}
  }
  window.save();return true;
};
// antes de cambiar la configuración, los meses cerrados sin «foto» la reciben con los valores de ANTES (el histórico no se mueve)
function freezeHistory(){
  const s=db.settings;s.payrollByMonth=s.payrollByMonth||{};
  const cur=monthKeyFromOffset(0),g=globalsCfg(),stamp=new Date().toISOString();
  for(const mk of monthsWithData()){
    if(mk>=cur||s.payrollByMonth[mk])continue;
    s.payrollByMonth[mk]=Object.assign({},g,{model:2,frozenAt:stamp});
  }
}
P.migratePayroll();

window.payrollRecalc=function(key){
  const snap=db.settings.payrollByMonth&&db.settings.payrollByMonth[key];if(!snap)return;
  if(!confirm('¿Recalcular este mes con el cálculo nuevo?\n\nSe mantienen tu configuración de ese mes (perfil, %, base, mínimo, IRPF), pero la nómina se calculará con las reglas nuevas y el resultado cambiará.'))return;
  snap.model=2;if(snap.fixedExtraVia==null)snap.fixedExtraVia=db.settings.fixedExtraVia||'cash';if(snap.underBase==null)snap.underBase=db.settings.underBase||'base';
  snap.recalculatedAt=new Date().toISOString();
  P.saveNow();renderBilling();
};

/* ---------- presentación del desglose ---------- */
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pc=v=>Number(v).toLocaleString('es-ES',{minimumFractionDigits:0,maximumFractionDigits:2});
const row=(label,val,cls)=>'<div class="payroll-row'+(cls?' '+cls:'')+'"><span>'+label+'</span><b>'+val+'</b></div>';
function breakdown(r){
  const ruleTxt=r.rule==='minimum'
    ?'Solo sobre el exceso del mínimo: base '+euro(r.base)+' + (facturación − '+euro(r.minimum)+') × '+pc(r.pct)+' %'
    :'Desde el primer euro: facturación × '+pc(r.pct)+' %';
  let h='<div class="note pr-rule">Perfil: <b>'+esc(PROFILES[r.profile])+'</b><br>Regla: '+esc(ruleTxt)+'</div>';
  h+=row('Facturación del vehículo (sin propinas)',euro(r.vehicle));
  if(r.manual>0)h+=row('Ajustes manuales del mes (compensaciones aparte)','+ '+euro(r.manual));
  if(r.rule==='minimum'){
    h+=r.reached
      ?row('Exceso sobre el mínimo ('+euro(r.minimum)+')',euro(r.excess))+row('Comisión variable ('+pc(r.pct)+' % del exceso)',euro(r.variable))
      :'<div class="note pr-warn">No se llega al mínimo de '+esc(euro(r.minimum))+': solo se cobra la nómina base.</div>';
  }
  h+=row('Remuneración total calculada',euro(r.remuneration),'pr-strong');
  if(r.lifted)h+='<div class="note pr-warn">La remuneración calculada ('+esc(euro(r.total))+') no llega a la nómina base: se garantiza la base (+'+esc(euro(r.shortfall))+').</div>';
  else if(r.shortfall>0)h+='<div class="note pr-warn">La remuneración calculada no llega a la nómina base ('+esc(euro(r.base))+'): la nómina bruta es solo la calculada y no hay efectivo.</div>';
  h+=row('Nómina bruta',euro(r.gross));
  h+=row('Retención de IRPF ('+pc(r.irpfPct)+' % de la nómina bruta)','− '+euro(r.tax));
  h+=row('Nómina neta estimada',euro(r.net));
  h+=row('Comisión en efectivo',euro(r.cashCommission));
  if(r.profile==='variableFixedCash')h+=row('Fijo adicional ('+(r.fixedVia==='payroll'?'incluido en la nómina bruta':'en efectivo, sin IRPF')+')',euro(r.fixedExtra));
  else h+=row('Fijo adicional','—');
  h+='<div class="payroll-final"><span>Total final estimado para el conductor</span><b>'+euro(r.final)+'</b></div>';
  if(r.tips>0)h+=row('Propinas (100 % tuyas, aparte del cálculo)','+ '+euro(r.tips),'pr-tips')+row('Total con propinas',euro(r.finalWithTips),'pr-tips');
  h+='<div class="note pr-disc">Esto es una <b>estimación</b>, no una nómina legal definitiva: no incluye necesariamente cotizaciones a la Seguridad Social ni otros conceptos que no hayas configurado.</div>';
  return h;
}
P.payrollBreakdownHtml=breakdown;

/* ---------- Facturación → Mensual ---------- */
P.decorateBillingPayroll=function(){
  if(typeof billPeriod==='undefined'||billPeriod!=='monthly')return;
  const root=document.getElementById('content');if(!root)return;
  const panel=root.querySelector('section.payroll-panel:not(#weeklyPayrollPanel)');if(!panel||panel.dataset.v314)return;
  panel.dataset.v314='1';
  const cfg=payrollSettingsForMonth(billMonthOffset);
  const key=monthKeyFromOffset(billMonthOffset);
  if(cfg.payrollProfile==='weeklyMonthly'){
    panel.insertAdjacentHTML('beforeend','<div class="note pr-disc">Esto es una <b>estimación</b>, no una nómina legal definitiva: no incluye necesariamente cotizaciones a la Seguridad Social ni otros conceptos que no hayas configurado.</div>');
    return;
  }
  if(cfg.model===1){
    panel.insertAdjacentHTML('afterbegin','<div class="note pr-legacy">📌 Este mes se guardó con el <b>cálculo anterior</b> y se muestra tal como lo viste. <button type="button" class="pr-btn" onclick="payrollRecalc(\''+esc(key)+'\')">Recalcular con el cálculo nuevo</button></div>');
    panel.insertAdjacentHTML('beforeend','<div class="note pr-disc">Esto es una <b>estimación</b>, no una nómina legal definitiva: no incluye necesariamente cotizaciones a la Seguridad Social ni otros conceptos que no hayas configurado.</div>');
    return;
  }
  const x=periodData('monthly',billMonthOffset);
  const r=calculatePayrollForMonth(x,cfg);
  panel.innerHTML='<div class="section-title">Cálculo de nómina mensual</div>'+breakdown(r);
};

/* ---------- Ajustes ---------- */
const $=id=>document.getElementById(id);
function setLabel(id,text){const el=$(id);const l=el&&el.previousElementSibling;if(l&&l.tagName==='LABEL')l.textContent=text}
function setNoteAfter(id,html){
  const el=$(id);if(!el)return;
  let n=el.nextElementSibling;
  if(n&&n.classList.contains('note')){n.innerHTML=html;n.dataset.pr='1';return}
  el.insertAdjacentHTML('afterend','<div class="note" data-pr="1" style="margin-bottom:10px">'+html+'</div>');
}
function decorateSettings(){
  if(!$('payrollProfile')||$('fixedVia'))return;
  const s=db.settings;
  // nombres claros
  const po=$('payrollProfile').options;
  for(const o of po)if(PROFILES[o.value])o.textContent=PROFILES[o.value];
  const mo=$('commMode').options;
  for(const o of mo)o.textContent=o.value==='minimum'?'Solo sobre el exceso del mínimo':'Desde el primer euro';
  setLabel('commMode','Regla de comisión');
  setNoteAfter('commMode','<b>Desde el primer euro:</b> remuneración = facturación × %.<br><b>Solo sobre el exceso:</b> remuneración = nómina base + (facturación − mínimo) × %. Si no se llega al mínimo, solo se cobra la base.');
  setLabel('comm','Mi comisión personal (%)');
  setLabel('commMinimum','Mínimo de facturación (€) — solo regla «sobre el exceso»');
  setNoteAfter('commMinimum','El % se aplica <b>únicamente a lo que supere</b> este importe. No es la nómina base ni el fijo.');
  setLabel('salaryBase','Nómina base mensual (€) — bruta');
  setNoteAfter('salaryBase','Se usa en la regla «sobre el exceso» y en el perfil «Nómina + comisión en efectivo» (parte que va en nómina).');
  setLabel('cashPayroll','Fijo adicional (€) — perfil «Nómina variable + fijo»');
  setLabel('payrollCompensation','Ajustes manuales del mes (€) — solo lo que cobras aparte y NO has registrado');
  setNoteAfter('payrollCompensation','Las cancelaciones y compensaciones que registras en la app ya se suman solas. Aquí solo va lo que no está registrado en ningún sitio; se suma a la facturación antes de aplicar el %.');
  const cp=$('cashPayroll');
  cp.insertAdjacentHTML('afterend',
    '<label id="fixedViaLabel">El fijo adicional se paga</label><select id="fixedVia" style="margin:6px 0 10px" oninput="previewPayrollSettings()" onchange="previewPayrollSettings()">'
    +'<option value="cash"'+(s.fixedExtraVia!=='payroll'?' selected':'')+'>En efectivo (fuera de nómina, sin IRPF)</option>'
    +'<option value="payroll"'+(s.fixedExtraVia==='payroll'?' selected':'')+'>En nómina (se suma a la nómina bruta y lleva IRPF)</option></select>'
    +'<div class="note" style="margin-bottom:10px">Es una cantidad que tú eliges. No es la nómina base ni el mínimo de facturación.</div>');
  const sb=$('salaryBase'),nb=sb.nextElementSibling;
  (nb&&nb.dataset.pr?nb:sb).insertAdjacentHTML('afterend',
    '<label id="underBaseLabel">Si la remuneración no llega a la nómina base</label><select id="underBase" style="margin:6px 0 10px" oninput="previewPayrollSettings()" onchange="previewPayrollSettings()">'
    +'<option value="base"'+(s.underBase!=='total'?' selected':'')+'>Se garantiza la nómina base (sin efectivo)</option>'
    +'<option value="total"'+(s.underBase==='total'?' selected':'')+'>La nómina bruta es solo lo calculado (sin efectivo)</option></select>'
    +'<div class="note" style="margin-bottom:10px">Solo para «Nómina + comisión en efectivo». El efectivo nunca sale negativo.</div>');
  const irn=$('irpf').nextElementSibling;
  if(irn&&irn.classList.contains('note'))irn.innerHTML='Se aplica <b>solo a la nómina bruta</b> (y al fijo si lo pagas en nómina). Nunca sobre la facturación del vehículo ni sobre el efectivo.';
  const prev=$('payrollSettingsPreview');
  if(prev&&prev.parentElement){const t=prev.parentElement.querySelector('.section-title');if(t)t.textContent='Vista previa de este mes (estimación)'}
  for(const id of ['payrollProfile','commMode','comm','commMinimum','salaryBase','cashPayroll','irpf','payrollCompensation']){
    const el=$(id);if(el){el.setAttribute('oninput','previewPayrollSettings()');el.setAttribute('onchange','previewPayrollSettings()')}
  }
}
// qué campos se usan con cada perfil y cada regla (los demás se muestran atenuados; su valor se conserva)
function fieldState(profile,rule){
  const weekly=profile==='weeklyMonthly';
  return {
    commMode:!weekly,comm:!weekly,
    commMinimum:!weekly&&rule==='minimum',
    salaryBase:!weekly&&(profile==='basePayrollVariableCash'||rule==='minimum'),
    underBase:!weekly&&profile==='basePayrollVariableCash',
    cashPayroll:!weekly&&profile==='variableFixedCash',
    fixedVia:!weekly&&profile==='variableFixedCash',
    irpf:!weekly,payrollCompensation:!weekly
  };
}
function applyFieldState(){
  const profile=($('payrollProfile')||{}).value,rule=($('commMode')||{}).value==='minimum'?'minimum':'firstEuro';
  const st=fieldState(profile,rule);
  for(const id of Object.keys(st)){
    const el=$(id);if(!el)continue;
    const on=st[id];
    el.disabled=!on;
    const lab=el.previousElementSibling,note=el.nextElementSibling;
    for(const n of [el,lab,note]){if(n&&(n===el||n.tagName==='LABEL'||(n.classList&&n.classList.contains('note'))))n.classList.toggle('pr-off',!on)}
  }
  const w=$('fixedViaLabel');if(w)w.classList.toggle('pr-off',!st.fixedVia);
  const u=$('underBaseLabel');if(u)u.classList.toggle('pr-off',!st.underBase);
}
const readNum=(id,fb)=>{const el=$(id);if(!el||el.value==='')return fb;const n=Number(String(el.value).replace(',','.'));return Number.isFinite(n)?n:fb};
window.previewPayrollSettings=function(){
  const target=$('payrollSettingsPreview');if(!target)return;
  const s=db.settings;
  applyFieldState();
  const profile=($('payrollProfile')||{}).value||s.payrollProfile||'variableFixedCash';
  if(profile==='weeklyMonthly'){
    target.innerHTML='Este perfil se calcula en <b>Facturación → Mensual → Nómina mensual semanal</b> (semanas, descuento de Bolt, IRPF y contingencias propios). Los demás campos de esta pantalla no le afectan.';
    return;
  }
  const cfg={payrollProfile:profile,salaryBase:readNum('salaryBase',s.salaryBase),cashPayroll:readNum('cashPayroll',s.cashPayroll),irpf:readNum('irpf',s.irpf),
    commission:readNum('comm',s.commission),commissionMode:($('commMode')||{}).value||s.commissionMode,commissionMinimum:readNum('commMinimum',s.commissionMinimum),
    fixedExtraVia:($('fixedVia')||{}).value||s.fixedExtraVia,underBase:($('underBase')||{}).value||s.underBase,model:2,manualComp:Math.max(0,readNum('payrollCompensation',payrollCompensationForMonth(monthKeyFromOffset(0))))};
  const x=periodData('monthly',0);
  target.innerHTML=breakdown(calculatePayrollForMonth(x,cfg));
};
const _ras=window.renderAppSettings;
window.renderAppSettings=function(){
  const r=_ras.apply(this,arguments);
  try{decorateSettings();window.previewPayrollSettings()}catch(e){console.warn('v3.14 ajustes',e)}
  return r;
};
const _ss=window.saveSettings;
window.saveSettings=function(){
  try{freezeHistory()}catch(e){console.warn('v3.14 histórico',e)}
  const via=($('fixedVia')||{}).value,ub=($('underBase')||{}).value;
  const r=_ss.apply(this,arguments);
  try{
    const s=db.settings;
    if(via)s.fixedExtraVia=via==='payroll'?'payroll':'cash';
    if(ub)s.underBase=ub==='total'?'total':'base';
    s.commission=clampPct(s.commission);
    const snap=s.payrollByMonth&&s.payrollByMonth[monthKeyFromOffset(0)];
    if(snap){snap.model=2;snap.fixedExtraVia=s.fixedExtraVia;snap.underBase=s.underBase;snap.commission=s.commission}
    P.saveNow();
    if($('payrollProfile'))window.renderAppSettings();
  }catch(e){console.warn('v3.14 guardar ajustes',e)}
  return r;
};
})();
'''),
    ('40_km.js', r'''/* ===================== v3.14 · KILÓMETROS =====================
   Causas encontradas de que «desaparezcan» los km:
   1) Guardar el odómetro (inicio/final) borraba los km del GPS de ese día (en el proyecto base: db.odometer[k]={start,end}).
   2) Lo escrito en Inicio/Final solo se guardaba con el botón; al cambiar de día, de pantalla o cerrar se perdía.
   3) Con el GPS activo, los km en curso solo vivían en memoria: si Android cerraba la app, se perdían; y al reabrirla pasada la
      medianoche se apuntaban al día equivocado (la jornada empezó el día anterior).
   4) Si el GPS estaba parado al finalizar la jornada, no se apuntaba nada.
   5) Al abrir la app la copia de la nube sustituía a la local sin mirar si había cambios sin subir (ver 50_sync.js).
   Aquí se corrigen 1-4 y se añade una recuperación que SOLO añade lo que exista en copias guardadas (nunca inventa ni sobrescribe). */
(function(){
const P=window.PDC314;if(!P||P.km)return;P.km=true;
const nm=v=>{const n=Number(v);return Number.isFinite(n)?n:0};
const r1=v=>Math.round(nm(v)*10)/10;
const $=id=>document.getElementById(id);
const hasNum=v=>v!==''&&v!=null&&Number.isFinite(Number(v));

function setOdo(k,patch){
  db.odometer=db.odometer||{};
  const o=db.odometer[k]||{start:'',end:''};
  db.odometer[k]=Object.assign({},o,patch,{updatedAt:new Date().toISOString()});   // se conservan gpsKm y cualquier otro dato del día
}
P.setOdo=setOdo;

/* ---------- guardar / leer ---------- */
window.saveOdometer=function(k){
  const s=$('odoStart'),e=$('odoEnd');
  if(!s||!e)return;                                   // sin los cuadros en pantalla no se toca nada (antes se borraba el día)
  const start=s.value===''?'':Number(s.value),end=e.value===''?'':Number(e.value);
  if((start!==''&&(!Number.isFinite(start)||start<0))||(end!==''&&(!Number.isFinite(end)||end<0))){alert('Revisa los kilómetros: tienen que ser números positivos.');return}
  if(start!==''&&end!==''&&end<start){alert('El odómetro final no puede ser inferior al inicial.');return}
  setOdo(k,{start,end});
  P.saveNow();
  renderControl();
  if(P.toastOk)P.toastOk('✓ Kilómetros guardados');
};
window.kilometersForDay=function(k){
  const o=dayOdometer(k);
  if(hasNum(o.start)&&hasNum(o.end)&&Number(o.end)>=Number(o.start))return Number(o.end)-Number(o.start);
  const g=nm(o.gpsKm);
  let live=0;
  const a=db.activeSession;
  if(a&&k===today()){
    const gd=a.gpsDay||dateKey(a.start);
    if(gd===k)live=Math.max(nm(a.liveKm),nm(window.__gpsLiveKm));
  }
  const sum=g+live;
  return sum>=1?sum:null;
};

/* ---------- autoguardado de lo que se escribe en Inicio / Final ---------- */
let typing=null;
function commitFrom(s,e){
  if(!s||!e)return false;
  const day=s.dataset.day;if(!day)return false;
  const ns=s.value===''?'':Number(s.value),ne=e.value===''?'':Number(e.value);
  if((ns!==''&&(!Number.isFinite(ns)||ns<0))||(ne!==''&&(!Number.isFinite(ne)||ne<0)))return false;
  const cur=(db.odometer&&db.odometer[day])||{start:'',end:''};
  if(String(cur.start)===String(ns)&&String(cur.end)===String(ne))return false;
  setOdo(day,{start:ns,end:ne});
  save();
  return true;
}
function commitNow(){clearTimeout(typing);typing=null;const did=commitFrom($('odoStart'),$('odoEnd'));if(did)paintAuto();return did}
// el resultado se actualiza mientras escribes (antes solo al pulsar el botón)
function paintResult(){
  const s=$('odoStart'),e=$('odoEnd'),box=document.querySelector('.odometer-result');if(!s||!e||!box)return;
  const day=s.dataset.day;if(!day)return;
  const sv=s.value===''?'':Number(s.value),ev=e.value===''?'':Number(e.value);
  let km;
  if(hasNum(sv)&&hasNum(ev)&&ev>=sv)km=ev-sv;
  else{const o=dayOdometer(day);const g=nm(o.gpsKm);km=g>=1?g:null}
  const b=box.querySelectorAll('.odo-line b');
  if(b[0])b[0].textContent=km===null?'—':km+' km';
  if(b[1])b[1].textContent=km>0?euro(fact(day)/km)+'/km':'—';
}
function paintAuto(){
  paintResult();
  const m=$('odoAuto');if(!m)return;
  const s=$('odoStart'),e=$('odoEnd');
  if(s&&e&&s.value!==''&&e.value!==''&&Number(e.value)<Number(s.value)){m.textContent='⚠️ El final es menor que el inicio: no se cuenta hasta que lo corrijas.';m.style.color='#ffd166';return}
  m.textContent='✓ Se guarda solo mientras escribes';m.style.color='#9fb4c8';
}
document.addEventListener('input',ev=>{
  const t=ev.target;if(!t||(t.id!=='odoStart'&&t.id!=='odoEnd'))return;
  clearTimeout(typing);typing=setTimeout(commitNow,600);paintAuto();
},true);
document.addEventListener('change',ev=>{const t=ev.target;if(t&&(t.id==='odoStart'||t.id==='odoEnd'))commitNow()},true);
document.addEventListener('visibilitychange',()=>{if(document.hidden)commitNow()});
window.addEventListener('pagehide',commitNow);
// si los cuadros salen de la pantalla por CUALQUIER motivo (cambio de día, de pantalla…), lo escrito se guarda con su propio día
function watchContent(){
  const c=$('content');if(!c||c.__pdcKm)return;c.__pdcKm=true;
  new MutationObserver(list=>{
    for(const m of list)for(const n of m.removedNodes){
      if(n.nodeType!==1)continue;
      const s=n.id==='odoStart'?n:n.querySelector&&n.querySelector('#odoStart');
      const e=n.id==='odoEnd'?n:n.querySelector&&n.querySelector('#odoEnd');
      if(s&&e&&commitFrom(s,e)){clearTimeout(typing);typing=null}
    }
  }).observe(c,{childList:true});
}
watchContent();
const _rc=window.renderControl;
window.renderControl=function(){
  commitNow();
  const r=_rc.apply(this,arguments);
  try{decorateControl()}catch(e){console.warn('v3.14 km',e)}
  return r;
};

/* ---------- recuperación (solo añade lo que exista en copias guardadas) ---------- */
function storedCopies(){
  const out=[];
  const ids=new Set((db.trips||[]).map(t=>t.id));
  // lineage: una copia solo vale si es de ESTA cuenta (comparte algún viaje con los datos actuales); así nunca entran datos de una cuenta borrada
  const add=(name,raw,needLineage)=>{try{const o=typeof raw==='string'?JSON.parse(raw):raw;const d=o&&(o.data&&typeof o.data==='object'?o.data:o);
    if(!d||!d.odometer||typeof d.odometer!=='object')return;
    if(needLineage&&!(Array.isArray(d.trips)&&d.trips.some(t=>ids.has(t.id))))return;
    out.push({name,odometer:d.odometer})}catch(e){}};
  try{add('copia local',localStorage.getItem(BACKUP_KEY),true)}catch(e){}
  try{
    const pr=JSON.parse(localStorage.getItem(AUTH_KEY)||'null');
    if(pr&&pr.loggedIn&&pr.identifier&&pr.identifier!=='dispositivo-local')add('copia de la cuenta',localStorage.getItem(ACCOUNT_PREFIX+authHash(pr.identifier)));
  }catch(e){}
  try{
    let pm=JSON.parse(localStorage.getItem('pdc_pre_merge_backup')||'null');
    if(pm&&!Array.isArray(pm))pm=[pm];
    for(const r of pm||[]){
      if(!r||r.why==='cambio de cuenta')continue;                   // la copia de otra cuenta nunca se usa para recuperar
      add('copia anterior a la unión (este teléfono)',r.local);add('copia anterior a la unión (nube)',r.cloud);
    }
  }catch(e){}
  return out;
}
P.recoverKm=function(opts){
  opts=opts||{};
  const found={};                              // día -> datos que faltan
  const cutoff=new Date(today()+'T12:00:00');cutoff.setMonth(cutoff.getMonth()-18);
  for(const c of storedCopies()){
    for(const [k,o] of Object.entries(c.odometer||{})){
      if(!/^\d{4}-\d{2}-\d{2}$/.test(k)||!o||typeof o!=='object')continue;
      if(new Date(k+'T12:00:00')<cutoff)continue;
      const cur=db.odometer&&db.odometer[k];
      const add={};
      if(!cur){
        if(hasNum(o.start))add.start=Number(o.start);
        if(hasNum(o.end))add.end=Number(o.end);
      }else if(!opts.auto&&!hasNum(cur.start)&&!hasNum(cur.end)&&hasNum(o.start)&&hasNum(o.end)&&Number(o.end)>=Number(o.start)){
        add.start=Number(o.start);add.end=Number(o.end);
      }
      const g=nm(o.gpsKm);
      if(g>0&&g>nm(cur&&cur.gpsKm))add.gpsKm=r1(g);
      if(Object.keys(add).length){
        const f=found[k]||(found[k]={});
        for(const [kk,v] of Object.entries(add))if(f[kk]==null||(kk==='gpsKm'&&v>f[kk]))f[kk]=v;
        f.from=c.name;
      }
    }
  }
  const days=Object.keys(found).sort();
  if(!opts.dry&&days.length){
    db.odometer=db.odometer||{};
    for(const k of days){
      const f=found[k];
      const cur=db.odometer[k]||{start:'',end:''};
      const patch={};
      if(f.start!=null)patch.start=f.start;
      if(f.end!=null)patch.end=f.end;
      if(f.gpsKm!=null)patch.gpsKm=f.gpsKm;
      db.odometer[k]=Object.assign({start:'',end:''},cur,patch,{updatedAt:new Date().toISOString(),recovered:true});
    }
    P.saveNow();
  }
  return days.map(k=>Object.assign({day:k},found[k]));
};
P.recoverable=0;
P.rescanKm=function(){try{P.recoverable=P.recoverKm({dry:true}).length}catch(e){P.recoverable=0}return P.recoverable};
window.recoverKmNow=function(){
  const r=P.recoverKm();
  P.rescanKm();
  if(P.toastOk)P.toastOk(r.length?'✓ Recuperados los km de '+r.length+(r.length===1?' día':' días'):'No hay kilómetros pendientes de recuperar');
  if($('content')&&document.querySelector('.navbtn.active')&&document.querySelector('.navbtn.active').dataset.view==='control')renderControl();
};

function decorateControl(){
  const box=document.querySelector('.odometer-box');if(!box)return;
  const s=$('odoStart'),e=$('odoEnd');
  if(s)s.dataset.day=fuelSelected;
  if(e)e.dataset.day=fuelSelected;
  if(!$('odoAuto')){
    const res=box.querySelector('.odometer-result');
    const m=document.createElement('div');m.id='odoAuto';m.style.cssText='margin-top:6px;font:700 12px system-ui;color:#9fb4c8';
    (res||box).insertAdjacentElement(res?'beforebegin':'beforeend',m);paintAuto();
  }
  if(!$('odoRecover')){
    const n=P.recoverable;
    if(n>0){
      const b=document.createElement('button');b.type='button';b.id='odoRecover';b.className='action';b.style.cssText='display:block;width:100%;margin-top:8px';
      b.textContent='Recuperar km de copias guardadas ('+n+(n===1?' día':' días')+')';b.onclick=()=>window.recoverKmNow();
      box.appendChild(b);
    }
  }
}

/* ---------- GPS: los km en curso se guardan y se apuntan al día correcto ----------
   (las dos variables que usa el código del GPS se vigilan desde 05_early.js, que se carga ANTES que ese código) */
// al finalizar la jornada: si el GPS estaba parado (o devolvió menos de lo contado) se apunta lo guardado, una sola vez
(function(){
  const o=window.toggleSession;if(typeof o!=='function')return;
  window.toggleSession=async function(){
    const a=db.activeSession;
    const day=a?(a.gpsDay||dateKey(a.start)):null;
    const live=a?nm(a.liveKm):0;
    const g0=day?nm((db.odometer&&db.odometer[day]||{}).gpsKm):0;
    const r=await o.apply(this,arguments);
    try{
      if(a&&day&&live>=0.1){
        const g1=nm((db.odometer&&db.odometer[day]||{}).gpsKm);
        const credited=Math.max(0,g1-g0);
        if(live-credited>=0.1){
          setOdo(day,{gpsKm:r1(g1+(live-credited))});
          P.saveNow();
          if(P.toastOk)P.toastOk('📍 '+r1(live).toLocaleString('es-ES')+' km de jornada guardados');
          if(document.querySelector('.navbtn.active')&&document.querySelector('.navbtn.active').dataset.view==='control')renderControl();
        }
      }
    }catch(e){console.warn('v3.14 fin de jornada',e)}
    return r;
  };
})();
// arranque: recuperar (solo lo que falte por completo) y avisar
try{
  const rec=P.recoverKm({auto:true});
  P.rescanKm();
  if(rec.length)setTimeout(()=>{if(P.toastOk)P.toastOk('✓ Recuperados los km de '+rec.length+(rec.length===1?' día':' días')+' desde copias guardadas')},1500);
}catch(e){}
})();
'''),
    ('50_sync.js', r'''/* ===================== v3.14 · SINCRONIZACIÓN SEGURA =====================
   Fallo original: al abrir la app la copia de la nube SUSTITUÍA siempre a la del teléfono (db=cloud). Si lo último que habías
   guardado (viajes, km, cancelaciones…) aún no se había subido —la subida esperaba 20 s, no se repetía si estaba ocupada o sin
   cobertura, y Android puede cerrar la app antes— la copia vieja de la nube lo borraba. Ahora:
     · el teléfono anota «hay cambios sin subir» (sobrevive al cierre) y la revisión de la nube que ya contiene;
     · al abrir: sin cambios pendientes la nube manda (otro móvil, etc.); con cambios pendientes NADA se pierde:
       si la nube no ha cambiado se conserva lo del teléfono y si ha cambiado se UNEN las dos copias (dejando antes una copia
       de seguridad de ambas); una cuenta distinta nunca se mezcla (y lo local se guarda aparte);
     · antes de subir se comprueba que nadie más haya subido nada (si lo hizo, se une y después se sube);
     · sin cobertura o con red lenta la app abre con los datos del teléfono (antes se quedaba en la pantalla de acceso/esperando);
     · si la subida falla o está ocupada se reintenta (al volver la conexión y con espera creciente);
     · menos consumo: no se sube si no hay cambios y se espera un mínimo entre subidas. */
(function(){
const P=window.PDC314;if(!P||P.sync)return;P.sync=true;
const DIRTY='pdc_sync_dirty',BASE='pdc_cloud_base',PRE='pdc_pre_merge_backup';
const cfg=()=>Object.assign({pull:4000,sess:5000,gap:45000,boot:3000,debounce:20000},window.__pdcSyncCfg||{});
const nm=v=>{const n=Number(v);return Number.isFinite(n)?n:0};
const hasNum=v=>v!==''&&v!=null&&Number.isFinite(Number(v));
const jget=k=>{try{return JSON.parse(localStorage.getItem(k)||'null')}catch(e){return null}};
const jset=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v));return true}catch(e){return false}};
const clone=o=>JSON.parse(JSON.stringify(o));
function profile(){return jget(AUTH_KEY)}
function isCloudProfile(){const p=profile();return !!(p&&p.loggedIn&&p.cloud)}
function owner(){const p=profile();return p&&p.userId||null}
let pullsInFlight=0,pullStart=0,lastPushDone=0,lastUpload=0;

/* ---------- estado: «hay cambios sin subir» + revisión de la nube que ya contiene lo local ---------- */
P.syncDirty=()=>!!jget(DIRTY);
P.syncMark=function(o){
  if(!o&&!isCloudProfile())return;
  trackDeletes();
  if(!localStorage.getItem(DIRTY))jset(DIRTY,{since:new Date().toISOString(),owner:o||owner()});
};
P.syncClear=()=>{try{localStorage.removeItem(DIRTY)}catch(e){}};
function setBase(updated,uid){jset(BASE,{updated_at:updated,owner:uid||owner()})}
P.setBase=setBase;
const own=(o,uid)=>!!(o&&uid&&o.owner===uid);
function needsPush(uid){return P.syncDirty()||!own(jget(BASE),uid)}

/* ---------- viajes borrados (para que al unir copias no «resuciten») ---------- */
let known=new Set((db.trips||[]).map(t=>String(t.id))),knownDb=db;
function trackDeletes(){
  try{
    const cur=new Set((db.trips||[]).map(t=>String(t.id)));
    if(db!==knownDb){knownDb=db;known=cur;return}            // se cargó otra copia completa: no es un borrado del usuario
    const st=db.settings.deletedTrips=db.settings.deletedTrips||{};
    const now=Date.now();
    for(const id of known)if(!cur.has(id))st[id]=now;
    for(const id of cur)if(st[id])delete st[id];             // un viaje restaurado deja de contar como borrado
    for(const id of Object.keys(st))if(now-st[id]>90*864e5)delete st[id];
    if(!Object.keys(st).length)delete db.settings.deletedTrips;
    known=cur;
  }catch(e){}
}
P.resetKnown=()=>{known=new Set((db.trips||[]).map(t=>String(t.id)));knownDb=db};

/* ---------- unir dos copias sin perder nada (lo local manda si hay conflicto) ---------- */
function unionById(a,b,keyFn){          // b (local) pisa a (nube) cuando es el mismo elemento
  const out=[],seen=new Map();
  for(const x of a||[]){const k=keyFn(x);if(!seen.has(k)){seen.set(k,out.length);out.push(x)}}
  for(const x of b||[]){const k=keyFn(x);if(seen.has(k))out[seen.get(k)]=x;else{seen.set(k,out.length);out.push(x)}}
  return out;
}
function byDate(arr){const m=new Map();for(const h of arr||[]){const k=h&&h.date||'';if(!m.has(k))m.set(k,[]);m.get(k).push(h)}return m}
P.mergeDb=function(L,C){
  L=L||{};C=C||{};
  const out=clone(C);
  const Ls=L.settings||{},Cs=C.settings||{};
  const dead=Object.assign({},Cs.deletedTrips||{},Ls.deletedTrips||{});
  // viajes: unión por identificador (los borrados a propósito no vuelven)
  out.trips=unionById(C.trips,L.trips,t=>String(t.id)).filter(t=>!dead[String(t.id)]);
  // jornadas y gasolina: por día manda lo del teléfono si tiene algo ese día
  const cm=byDate(C.hours),lm=byDate(L.hours),hrs=[];
  for(const [k,v] of cm)if(!lm.has(k))hrs.push(...clone(v));
  for(const v of lm.values())hrs.push(...clone(v));
  out.hours=hrs;
  out.manual=Object.assign({},C.manual||{},L.manual||{});
  out.fuel=Object.assign({},C.fuel||{},L.fuel||{});
  if(C.fuelEntries||L.fuelEntries){out.fuelEntries=Object.assign({},C.fuelEntries||{},L.fuelEntries||{})}
  // odómetro: los km nunca bajan; inicio/final del que tenga dato
  out.odometer=clone(C.odometer||{});
  for(const [d,o] of Object.entries(L.odometer||{})){
    const c=out.odometer[d];
    if(!c){out.odometer[d]=clone(o);continue}
    const m=Object.assign({},c,o);
    m.start=hasNum(o.start)?o.start:(hasNum(c.start)?c.start:'');
    m.end=hasNum(o.end)?o.end:(hasNum(c.end)?c.end:'');
    const g=Math.max(nm(o.gpsKm),nm(c.gpsKm));if(g>0)m.gpsKm=g;
    const u=[o.updatedAt,c.updatedAt].filter(Boolean).sort().pop();if(u)m.updatedAt=u;
    out.odometer[d]=m;
  }
  // ajustes: lo del teléfono manda; los registros por mes/semana se unen
  const s=Object.assign({},Cs,Ls);
  for(const k of ['payrollByMonth','payrollCompensations','weeklyPayrolls']){
    if(Cs[k]||Ls[k])s[k]=Object.assign({},Cs[k]||{},Ls[k]||{});
  }
  const bc={};
  for(const k of new Set([...Object.keys(Cs.billingCompensations||{}),...Object.keys(Ls.billingCompensations||{})])){
    const a=(Cs.billingCompensations||{})[k],b=(Ls.billingCompensations||{})[k];
    if(a&&b&&Array.isArray(a.entries)&&Array.isArray(b.entries))bc[k]=Object.assign({},a,b,{entries:unionById(a.entries,b.entries,e=>String(e.id))});
    else bc[k]=b||a;
  }
  if(Object.keys(bc).length||Cs.billingCompensations||Ls.billingCompensations)s.billingCompensations=bc;
  if(Object.keys(dead).length)s.deletedTrips=dead;else delete s.deletedTrips;
  if('tripBackups' in s)s.tripBackups=[];
  out.settings=s;
  if('activeSession' in L)out.activeSession=L.activeSession;
  // el resto (mensajes de soporte, etc.)
  for(const k of Object.keys(L)){
    if(['trips','hours','fuel','manual','fuelEntries','odometer','settings','activeSession'].includes(k))continue;
    const a=C[k],b=L[k];
    if(Array.isArray(b)&&Array.isArray(a)&&[...a,...b].every(x=>x&&typeof x==='object'&&x.id!=null))out[k]=unionById(a,b,x=>String(x.id));
    else if(b&&typeof b==='object'&&!Array.isArray(b)&&a&&typeof a==='object'&&!Array.isArray(a))out[k]=Object.assign({},a,b);
    else if(b!==undefined)out[k]=b;
  }
  return out;
};

/* ---------- copia de seguridad antes de unir / de cambiar de cuenta (sin alarmar si no cabe) ---------- */
const sz=o=>{try{return JSON.stringify(o).length}catch(e){return 0}};
function saveBackup(local,cloud,why){
  try{
    let arr=jget(PRE);if(!Array.isArray(arr))arr=[];
    const rec={at:new Date().toISOString(),why,local:clone(local)};
    if(cloud&&sz(local)+sz(cloud)<1800000)rec.cloud=clone(cloud);
    arr.push(rec);arr=arr.slice(-2);
    for(let i=0;i<4;i++){
      if(jset(PRE,arr))return true;
      if(arr.length>1)arr=arr.slice(-1);else if(rec.cloud)delete rec.cloud;else break;
    }
  }catch(e){}
  return false;
}
P.preMergeBackups=()=>jget(PRE)||[];

/* ---------- decidir qué hacer con la copia de la nube ---------- */
// devuelve {action:'take'|'keep'|'merge', db}
P.decidePull=function(cloudDb,cloudUpdated,uid,ctx){
  ctx=ctx||{};
  const base=jget(BASE),p=profile();
  P.flush();                                                   // lo pendiente en memoria pasa a disco y queda marcado
  const dirty=jget(DIRTY);
  // ¿lo que hay en el teléfono es de esta misma cuenta?
  const same=ctx.login?(own(dirty,uid)||own(base,uid)):!(p&&p.userId&&p.userId!==uid);
  const localHas=localDataHasContent(db);
  if(!same){
    if(localHas)saveBackup(db,null,'cambio de cuenta');
    return {action:'take',db:cloudDb};
  }
  if(!localHas)return {action:'take',db:cloudDb};
  if(!dirty&&own(base,uid))return {action:'take',db:cloudDb};   // todo lo local ya estaba subido: la nube manda
  if(dirty&&own(base,uid)&&base.updated_at===cloudUpdated)return {action:'keep',db};   // la nube no ha cambiado desde mi última sincronización
  // hay cambios sin subir (o no se sabe) y la nube tiene algo distinto: se unen
  const merged=P.mergeDb(db,cloudDb);
  if(JSON.stringify(merged)===JSON.stringify(cloudDb))return {action:'take',db:cloudDb};   // lo local no aporta nada nuevo
  saveBackup(db,cloudDb,'unión de copias');
  return {action:'merge',db:merged};
};
function userId(){
  try{return pdcSupabase.auth.getSession().then(r=>r&&r.data&&r.data.session&&r.data.session.user&&r.data.session.user.id||null,()=>null)}catch(e){return Promise.resolve(null)}
}
async function decide(res,ctx){
  try{
    if(!res||res.error||!res.data||!res.data.data)return res;
    const uid=await userId();
    if(ctx&&ctx.started&&lastPushDone>ctx.started)return {data:null,error:null,__pdc:'stale'};   // lo que llegó es anterior a mi última subida
    if(!uid)return res;
    const upd=res.data.updated_at;
    const d=P.decidePull(res.data.data,upd,uid,ctx);
    if(d.action==='take'){setBase(upd,uid);P.syncClear();return res}
    setBase(upd,uid);                                           // lo local ya incluye esta revisión de la nube
    if(d.action==='merge')P.syncMark(uid);                      // lo unido aún no está en la nube
    return {data:{data:d.db,updated_at:upd},error:null,__pdc:d.action};
  }catch(e){console.warn('v3.14 sync decide',e);return res}
}

/* ---------- aplicar copia de la nube a la app ya abierta ---------- */
function refreshView(){
  try{
    const ae=document.activeElement;
    if(ae&&/^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName))return;          // no molestar si está escribiendo
    const v=document.querySelector('.navbtn.active');
    if(v&&typeof window.show==='function')window.show(v.dataset.view);
  }catch(e){}
}
function adoptDb(next,note){
  db=next;
  try{normalizeDbSettings()}catch(e){}
  try{normalizeHourRecordsByDay()}catch(e){}
  P.resetKnown();P.bump();
  try{P.putLS(KEY,JSON.stringify(db))}catch(e){}
  refreshView();
  if(note&&P.toastOk)P.toastOk(note);
}
P.applyLate=function(res){
  try{
    if(!res||res.error||!res.data||!res.data.data)return;
    const next=res.data.data;
    if(next===db)return;
    adoptDb(next,res.__pdc==='merge'?'☁️ Datos del teléfono y de la nube unidos':'☁️ Datos de la nube cargados');
    if(res.__pdc==='merge')window.scheduleCloudPush();
  }catch(e){console.warn('v3.14 applyLate',e)}
};

/* ---------- enganchar Supabase: lectura con tiempo máximo + decisión segura ---------- */
const TIMEOUT={};
const raw={};
function guarded(execute,ctx){
  const started=Date.now();ctx.started=started;pullStart=started;pullsInFlight++;
  const done=()=>{pullsInFlight=Math.max(0,pullsInFlight-1)};
  const real=Promise.resolve().then(execute);
  if(ctx.login){                                              // al iniciar sesión se espera la respuesta y los errores se muestran como siempre
    return real.then(r=>decide(r,ctx)).finally(done);
  }
  let late=false;
  const decided=real.then(r=>decide(r,ctx),e=>{throw e});
  decided.then(res=>{if(late)P.applyLate(res)},()=>{}).finally(done);
  const wait=navigator.onLine===false?50:cfg().pull;
  const timer=new Promise(r=>setTimeout(()=>r(TIMEOUT),wait));
  return Promise.race([decided.then(r=>({r}),e=>({e})),timer]).then(x=>{
    if(x===TIMEOUT){late=true;return {data:null,error:null}}     // la app abre con lo del teléfono; la nube se aplica si llega después
    if(x.e||(x.r&&x.r.error)){console.warn('v3.14 nube no disponible',x.e||x.r.error);return {data:null,error:null}}
    return x.r;
  });
}
function wrapSelect(b,ctx){
  return new Proxy(b,{get(t,prop){
    if(prop==='then')return (ok,bad)=>guarded(()=>new Promise((res,rej)=>t.then(res,rej)),ctx).then(ok,bad);
    const v=Reflect.get(t,prop,t);
    if(typeof v==='function')return (...a)=>{const r=v.apply(t,a);return r&&typeof r==='object'&&typeof r.then==='function'?wrapSelect(r,ctx):r};
    return v;
  }});
}
P.wrapDriverSelect=wrapSelect;
try{    // si el enganche temprano no se pudo hacer, se hace ahora (algo más tarde, pero igual de seguro)
  if(typeof pdcSupabase!=='undefined'&&pdcSupabase&&window.__pdcHookSB)window.__pdcHookSB(pdcSupabase);
  if(typeof pdcSupabase!=='undefined'&&pdcSupabase)raw.from=pdcSupabase.__rawFrom;
}catch(e){console.warn('v3.14 enganche nube',e)}
for(const fn of ['cloudLogin','cloudRegister']){
  const o=window[fn];
  if(typeof o==='function')window[fn]=async function(){P.inLogin=true;try{return await o.apply(this,arguments)}finally{P.inLogin=false}};
}

/* ---------- subir: sin perder subidas, con reintentos y sin gastar datos de más ---------- */
let pushing=null,retryT=null,gapT=null,fails=0,force=false;
P.pushCount=0;P.lastPayloadBytes=0;
function scheduleRetry(){
  clearTimeout(retryT);
  const uid=owner();
  if(!isCloudProfile()||!needsPush(uid))return;
  const wait=Math.min(300,15*Math.pow(2,Math.max(0,fails-1)))*1000;
  retryT=setTimeout(()=>{if(navigator.onLine!==false)window.cloudPushData()},wait);
}
async function cloudMeta(uid){
  const r=await (raw.from||pdcSupabase.from.bind(pdcSupabase))('driver_data').select('updated_at').eq('user_id',uid).maybeSingle();
  if(r&&r.error)throw r.error;
  return r&&r.data?r.data.updated_at:null;
}
async function cloudFull(uid){
  const r=await (raw.from||pdcSupabase.from.bind(pdcSupabase))('driver_data').select('data,updated_at').eq('user_id',uid).maybeSingle();
  if(r&&r.error)throw r.error;
  return r&&r.data||null;
}
window.cloudPushData=function(){
  const f=force;force=false;
  if(!hasRealCloud())return Promise.resolve();
  if(pushing){if(!f)window.scheduleCloudPush();else force=true;return pushing}
  if(navigator.onLine===false)return Promise.resolve();                       // al volver la conexión se sube (evento «online»)
  if(pullsInFlight>0&&Date.now()-pullStart<90000){                              // primero termina la lectura de la nube
    clearTimeout(gapT);gapT=setTimeout(()=>window.cloudPushData(),3000);if(f)force=true;return Promise.resolve();
  }
  const wait=lastUpload+cfg().gap-Date.now();
  if(!f&&fails===0&&wait>0){clearTimeout(gapT);gapT=setTimeout(()=>window.cloudPushData(),wait+50);return Promise.resolve()}   // mínimo entre subidas
  pushing=(async()=>{
    try{
      const s=await pdcSupabase.auth.getSession();const user=s&&s.data&&s.data.session&&s.data.session.user;if(!user)return;
      P.flush();
      if(!f&&!needsPush(user.id))return;                                       // nada que subir (antes se subía todo en cada apertura)
      // ¿ha subido alguien más algo desde mi última sincronización? → se une antes de subir
      const cu=await cloudMeta(user.id);
      const base=jget(BASE);
      if(cu&&!(own(base,user.id)&&base.updated_at===cu)){
        const full=await cloudFull(user.id);
        if(full&&full.data){
          const merged=P.mergeDb(db,full.data);
          if(JSON.stringify(merged)!==JSON.stringify(db)){
            saveBackup(db,full.data,'antes de subir');
            adoptDb(merged,'☁️ Datos del teléfono y de la nube unidos');
          }
          setBase(full.updated_at,user.id);
        }
      }
      const v0=P.version();
      const snap=currentDbSnapshot();const sig=JSON.stringify(snap);
      if(sig===window.__pdcLastSig&&!f){if(P.version()===v0&&!P.isDirty())P.syncClear();return}
      const payload={user_id:user.id,data:snap,updated_at:new Date().toISOString()};
      P.lastPayloadBytes=sig.length;lastUpload=Date.now();
      let r;
      try{
        const q=pdcSupabase.from('driver_data').upsert(payload,{onConflict:'user_id'});
        r=await (typeof q.select==='function'?q.select('updated_at'):q);      // devuelve la revisión exacta que queda en la nube
        if(r&&r.error)throw r.error;
      }catch(e){
        if(!/policy|permission|row-level|return|select/i.test(String(e&&e.message||e)))throw e;
        r=await pdcSupabase.from('driver_data').upsert(payload,{onConflict:'user_id'});   // como antes
        if(r&&r.error)throw r.error;
      }
      P.pushCount++;
      window.__pdcLastSig=sig;lastPushDone=Date.now();
      try{localStorage.setItem('pdc_last_sync',new Date().toISOString())}catch(e){}
      const row=r&&Array.isArray(r.data)?r.data[0]:null;
      setBase(row&&row.updated_at||payload.updated_at,user.id);
      fails=0;
      if(P.version()===v0&&!P.isDirty())P.syncClear();else window.scheduleCloudPush();   // hubo cambios mientras subía
    }catch(e){
      console.warn('Sincronización nube:',e);
      fails++;scheduleRetry();
    }finally{pushing=null}
  })();
  return pushing;
};
window.scheduleCloudPush=function(){
  if(!hasRealCloud())return;
  clearTimeout(pdcCloudSyncTimer);
  pdcCloudSyncTimer=setTimeout(()=>window.cloudPushData(),cfg().debounce);
};
const _sn=window.syncNow;
if(typeof _sn==='function')window.syncNow=function(){force=true;return _sn.apply(this,arguments)};   // «Sincronizar ahora» sube siempre
window.addEventListener('online',()=>{fails=0;if(isCloudProfile()&&needsPush(owner()))window.cloudPushData()});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&isCloudProfile()&&navigator.onLine!==false&&!pushing&&P.syncDirty())window.cloudPushData()});
// cambios pendientes de una vez anterior (la app se cerró antes de subirlos)
setTimeout(()=>{if(isCloudProfile()&&navigator.onLine!==false&&P.syncDirty())window.cloudPushData()},cfg().boot);

/* ---------- abrir la app aunque no haya conexión ---------- */
function rescueOffline(){
  try{
    const p=profile();
    if(!(p&&p.loggedIn&&p.cloud))return false;
    const app=document.querySelector('.app');
    if(!app||!app.classList.contains('auth-hidden'))return false;
    if(!localDataHasContent(db))return false;
    try{normalizeHourRecordsByDay()}catch(e){}
    document.querySelector('#authScreen').classList.add('auth-hide');
    app.classList.remove('auth-hidden');
    window.show('calc');
    try{runStartupReminders()}catch(e){}
    if(P.toastOk)P.toastOk('📴 Sin conexión: usando los datos de este teléfono');
    return true;
  }catch(e){return false}
}
P.rescueOffline=rescueOffline;
const _sam=window.setAuthMode;
if(typeof _sam==='function')window.setAuthMode=function(m){
  const r=_sam.apply(this,arguments);
  if(m==='login')setTimeout(rescueOffline,0);                 // solo actúa si la sesión sigue «iniciada» en el teléfono
  return r;
};
})();
'''),
    ('60_bolt.js', r'''/* ===================== v3.14 · ESTIMACIÓN DEL PRECIO DE BOLT (pantalla de ajustes) =====================
   Cuando la oferta de Bolt no muestra el precio, el lector (Java) lo estima con 4 tramos por los km del viaje con pasajero, con un perfil
   para lunes–viernes y otro para sábados, domingos y festivos. Aquí se editan TODOS los valores. Son estimaciones del conductor (no tarifas
   oficiales de Bolt). Los valores iniciales son los mismos que usa el código nativo (se comprueba en las pruebas contra Java). */
(function(){
const P=window.PDC314;if(!P||P.bolt)return;P.bolt=true;
const SR=()=>{try{if(window.Capacitor&&Capacitor.isNativePlatform&&Capacitor.isNativePlatform())return (Capacitor.Plugins&&Capacitor.Plugins.ScreenReader)||Capacitor.registerPlugin('ScreenReader')}catch(e){}return null};
const LSK='pdc_bolt';
const T=(b,k,m)=>({base:b,km:k,min:m,mult:1,mode:'A'});
const defaults=()=>({on:true,mode:'auto',comm:25,
  holidays:['01-01','01-06','05-01','05-02','08-15','10-12','11-01','12-06','12-08','12-25'],
  wd:{minFare:5.95,offerMult:true,bp:[5,10,15],t:[T(3.5,0.95,0.11),T(3.5,0.8,0.11),T(1.95,0.95,0.11),T(1.95,0.8,0.11)]},
  we:{minFare:9,offerMult:true,bp:[5,10,15],t:[T(5.5,1.7,0.22),T(5.5,1.7,0.22),T(5.5,1.7,0.22),T(5.5,1.7,0.22)]}});
P.boltDefaults=defaults;
const clone=o=>JSON.parse(JSON.stringify(o));
const isN=v=>typeof v==='number'&&Number.isFinite(v);
const rng=(v,d,lo,hi)=>isN(v)&&v>=lo&&v<=hi?v:d;
/* misma validación que el código nativo: lo no válido vuelve a su valor inicial */
function normTier(o,d){const t=clone(d);if(!o||typeof o!=='object')return t;t.base=rng(o.base,d.base,0,100);t.km=rng(o.km,d.km,0,20);t.min=rng(o.min,d.min,0,10);t.mult=rng(o.mult,d.mult,0.1,10);t.mode=typeof o.mode==='string'&&o.mode.trim().toUpperCase()==='B'?'B':'A';return t}
function normProf(o,d){const p=clone(d);if(!o||typeof o!=='object')return p;p.minFare=rng(o.minFare,d.minFare,0,200);p.offerMult=typeof o.offerMult==='boolean'?o.offerMult:d.offerMult;
  if(Array.isArray(o.bp)&&o.bp.length===3){const [a,b,c]=o.bp.map(v=>rng(v,-1,0.01,1000));if(a>0&&b>a&&c>b)p.bp=[a,b,c]}
  if(Array.isArray(o.t))for(let i=0;i<4&&i<o.t.length;i++)p.t[i]=normTier(o.t[i],d.t[i]);return p}
function norm(o){const d=defaults(),c=d;if(!o||typeof o!=='object')return c;
  if(typeof o.on==='boolean')c.on=o.on;if(['auto','week','weekend'].includes(o.mode))c.mode=o.mode;c.comm=rng(o.comm,c.comm,0,90);
  c.wd=normProf(o.wd,d.wd);c.we=normProf(o.we,d.we);
  if(Array.isArray(o.holidays)){const h=[];for(const x of o.holidays)if(typeof x==='string'){const y=x.trim();if(/^(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})$/.test(y)&&!h.includes(y))h.push(y)}c.holidays=h}
  return c}
P.boltNorm=norm;

/* ---------- el mismo cálculo que el aviso (sin redondeos intermedios) ---------- */
function tierIndex(p,km){return km<=p.bp[0]?0:km<=p.bp[1]?1:km<=p.bp[2]?2:3}
function estimate(c,weekend,km,min,offerMult){
  const pr=weekend?c.we:c.wd,ti=tierIndex(pr,km),t=pr.t[ti];
  const fromOffer=pr.offerMult&&offerMult>0;
  let mult=fromOffer?offerMult:t.mult;mult=Math.max(0.1,Math.min(10,mult));
  let gross=t.mode==='B'?(t.base+km*t.km+min*t.min)*mult:t.base+km*t.km*mult+min*t.min;
  let ma=false;if(pr.minFare>0&&gross<pr.minFare){gross=pr.minFare;ma=true}
  const pct=Math.max(0,Math.min(90,c.comm)),comm=gross*pct/100;
  return {gross,comm,net:gross-comm,mult,tier:ti+1,mode:t.mode==='B'?'B':'A',lo:ti===0?0:pr.bp[ti-1],hi:ti===3?-1:pr.bp[ti],minApplied:ma,weekend,fromOffer};
}
P.boltEstimate=estimate;
// decimales como el código nativo: sobre la representación decimal más corta, redondeo «medio hacia arriba»
function rhu(v,dec){
  v=Math.round(v*1e6)/1e6;const neg=v<0;if(neg)v=-v;
  let s=String(v);if(/e/i.test(s))s=v.toFixed(6);
  let [i,f='']=s.split('.');f=(f+'0'.repeat(dec+1));const up=f.charCodeAt(dec)>=53;
  let n=parseInt(i+f.slice(0,dec),10)+(up?1:0);
  let t=String(n);while(t.length<=dec)t='0'+t;
  const out=dec>0?t.slice(0,t.length-dec)+'.'+t.slice(t.length-dec):t;
  return (neg&&n>0?'-':'')+out;
}
const money=v=>rhu(v,2).replace('.',',');
const spoken=(v,dec)=>{let s=rhu(v,dec);if(s.indexOf('.')>=0)s=s.replace(/0+$/,'').replace(/\.$/,'');return s.replace('.',',')};
P.boltMoney=money;
function voiceText(e,km,min){
  const m=Math.round(min),k=spoken(km,1);
  return 'Bolt. Viaje de '+k+(k==='1'?' kilómetro y ':' kilómetros y ')+m+(m===1?' minuto':' minutos')+(Math.abs(e.mult-1)>1e-9?', demanda por '+spoken(e.mult,2):'')+
    '. Bruto estimado: '+money(e.gross)+' euros. Comisión estimada: '+money(e.comm)+' euros. Neto estimado: '+money(e.net)+' euros.';
}
P.boltVoice=voiceText;
function isWeekend(c,d){
  if(c.mode==='week')return false;if(c.mode==='weekend')return true;
  const dow=d.getDay();if(dow===0||dow===6)return true;
  const p2=n=>String(n).padStart(2,'0'),md=p2(d.getMonth()+1)+'-'+p2(d.getDate()),full=d.getFullYear()+'-'+md;
  return (c.holidays||[]).some(h=>h===full||h===md);
}
P.boltIsWeekend=isWeekend;

/* ---------- estado y guardado permanente ---------- */
const B={cfg:defaults(),voice:true,vol:1,weekendNow:false,prof:'wd',open:false,sim:{km:8.3,min:10,mult:'',prof:'auto'},native:false,loaded:false};
P.boltState=B;
function mirrorToDb(cfgJson){
  try{db.settings.boltCfg=cfgJson;db.settings.boltVoice=B.voice;db.settings.boltVol=B.vol}catch(e){}
}
async function load(){
  const sr=SR();B.native=!!sr;let d=null;
  if(sr){try{d=await sr.getBolt()}catch(e){d=null}}
  if(d&&d.cfg){
    try{B.cfg=norm(JSON.parse(d.cfg))}catch(e){B.cfg=defaults()}
    B.voice=d.voice!==false;B.vol=isN(d.vol)?d.vol:1;B.weekendNow=!!d.weekendNow;B.saved=!!d.saved;
    // el teléfono perdió sus ajustes (reinstalación…) pero la copia de la cuenta los tiene
    if(!d.saved&&db&&db.settings&&db.settings.boltCfg){
      try{
        const r=await sr.setBolt({cfg:db.settings.boltCfg,voice:db.settings.boltVoice!==false,vol:isN(db.settings.boltVol)?db.settings.boltVol:1});
        B.cfg=norm(JSON.parse((r&&r.cfg)||db.settings.boltCfg));B.voice=db.settings.boltVoice!==false;B.vol=isN(db.settings.boltVol)?db.settings.boltVol:1;B.saved=true;
      }catch(e){}
    }
  }else{
    let o=null;try{o=JSON.parse(localStorage.getItem(LSK)||'null')}catch(e){}
    if(!o&&db&&db.settings&&db.settings.boltCfg){try{o={cfg:JSON.parse(db.settings.boltCfg),voice:db.settings.boltVoice,vol:db.settings.boltVol}}catch(e){}}
    if(o){B.cfg=norm(o.cfg);B.voice=o.voice!==false;B.vol=isN(o.vol)?o.vol:1}
    B.weekendNow=isWeekend(B.cfg,new Date());
  }
  B.loaded=true;
}
P.boltLoad=load;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
async function persist(){
  const sent=clone(B.cfg),json=JSON.stringify(sent);let back=sent;
  const sr=SR();
  if(sr){
    const r=await sr.setBolt({cfg:json,voice:B.voice,vol:B.vol});
    if(r&&r.cfg){try{back=norm(JSON.parse(r.cfg))}catch(e){}}
    B.saved=true;
  }
  B.cfg=back;
  const out=JSON.stringify(back);
  try{localStorage.setItem(LSK,JSON.stringify({cfg:back,voice:B.voice,vol:B.vol}))}catch(e){}
  mirrorToDb(out);P.saveNow();
  B.weekendNow=isWeekend(B.cfg,new Date());
  return !same(sent,back);                       // true = algún valor se corrigió
}

/* ---------- pantalla ---------- */
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const num=v=>{const s=String(v==null?'':v).trim().replace(',','.');if(s==='')return NaN;const n=Number(s);return Number.isFinite(n)?n:NaN};
const show=v=>String(Math.round(v*1e6)/1e6);
const LIM={base:[0,100],km:[0,20],min:[0,10],mult:[0.1,10],minFare:[0,200],comm:[0,90],bp:[0.01,1000]};
function rangeTxt(p,i){const b=p.bp;return i===0?'De 0 a '+show(b[0])+' km':i===1?'Más de '+show(b[0])+' hasta '+show(b[1])+' km':i===2?'Más de '+show(b[1])+' hasta '+show(b[2])+' km':'Más de '+show(b[2])+' km'}
const cell=(lab,id,val,path,opts)=>{opts=opts||{};return '<label class="bz-f"><span>'+lab+'</span><input id="'+id+'" type="number" inputmode="decimal" step="'+(opts.step||'0.01')+'" min="'+(opts.min!=null?opts.min:0)+'" value="'+esc(val)+'"'+(opts.on?' oninput="'+opts.on+'"':' data-p="'+path+'" oninput="boltIn(this)"')+(opts.dis?' disabled':'')+'></label>'};
function tierHtml(pk,i){
  const pr=B.cfg[pk],t=pr.t[i],id=n=>'bz_'+pk+'_'+i+'_'+n;
  const lo=i===0?cell('Desde (km)',id('lo'),0,'',{dis:1}):cell('Desde (km)',id('lo'),show(pr.bp[i-1]),pk+'.bp.'+(i-1),{step:'0.1'});
  const hi=i===3?'<label class="bz-f"><span>Hasta (km)</span><input value="sin límite" disabled></label>':cell('Hasta (km)',id('hi'),show(pr.bp[i]),pk+'.bp.'+i,{step:'0.1'});
  return '<div class="bz-t"><div class="bz-th"><b>Tramo '+(i+1)+'</b><span id="'+id('rg')+'">'+rangeTxt(pr,i)+'</span></div><div class="bz-g">'+lo+hi
   +cell('Tarifa base (€)',id('base'),show(t.base),pk+'.t.'+i+'.base')+cell('Precio por km (€)',id('km'),show(t.km),pk+'.t.'+i+'.km')
   +cell('Precio por minuto (€)',id('min'),show(t.min),pk+'.t.'+i+'.min')+cell('Multiplicador de demanda',id('mult'),show(t.mult),pk+'.t.'+i+'.mult',{min:0.1,step:'0.05'})
   +'<label class="bz-f bz-w"><span>Cómo se aplica el multiplicador</span><select id="'+id('mode')+'" data-p="'+pk+'.t.'+i+'.mode" onchange="boltIn(this)"><option value="A"'+(t.mode==='A'?' selected':'')+'>A · solo a los kilómetros</option><option value="B"'+(t.mode==='B'?' selected':'')+'>B · al importe completo</option></select></label>'
   +'</div></div>';
}
function profHtml(pk){
  const pr=B.cfg[pk];
  return '<div class="bz-prof" id="bz_prof_'+pk+'">'
   +'<div class="bz-g bz-top">'+cell('Tarifa mínima estimada (€)','bz_'+pk+'_minFare',show(pr.minFare),pk+'.minFare')
   +'<label class="bz-f bz-chk"><input type="checkbox" id="bz_'+pk+'_offerMult" data-p="'+pk+'.offerMult"'+(pr.offerMult?' checked':'')+' onchange="boltIn(this)"><span>Usar el multiplicador que muestre la oferta (×1,4…) en lugar del de cada tramo</span></label></div>'
   +[0,1,2,3].map(i=>tierHtml(pk,i)).join('')+'</div>';
}
function simHtml(){
  return '<div class="bz-sec"><b>🧮 Simulador (para contrastar con viajes reales)</b><small>Escribe los km y minutos del viaje con pasajero y mira qué estimaría la app con los valores de arriba.</small>'
   +'<div class="bz-g">'+cell('Km del viaje','bz_sKm',show(B.sim.km),'',{step:'0.1',on:'boltSim()'})+cell('Minutos del viaje','bz_sMin',show(B.sim.min),'',{step:'1',on:'boltSim()'})
   +cell('Demanda de la oferta (opcional)','bz_sMult',B.sim.mult,'',{step:'0.05',on:'boltSim()'})
   +'<label class="bz-f"><span>Perfil</span><select id="bz_sProf" onchange="boltSim()"><option value="auto"'+(B.sim.prof==='auto'?' selected':'')+'>Hoy (automático)</option><option value="wd"'+(B.sim.prof==='wd'?' selected':'')+'>Lunes a viernes</option><option value="we"'+(B.sim.prof==='we'?' selected':'')+'>Sáb., dom. y festivos</option></select></label></div>'
   +'<div id="bz_sOut" class="bz-out"></div></div>';
}
function bodyHtml(){
  const c=B.cfg;
  return '<div class="bz-note">Cuando la oferta de Bolt <b>no muestra el precio</b>, la app lo <b>estima</b> con estos valores y te dice el bruto, la comisión y el <b>neto estimado</b> (en pantalla y por voz). '
   +'<b>Son estimaciones nuestras con viajes reales, no tarifas oficiales de Bolt</b>: si ves que Bolt paga más o menos, corrígelas aquí. Si la oferta sí trae el precio, se usa ese y no se estima nada.</div>'
   +'<div class="bz-row"><div><b>Estimar el precio de Bolt</b><br><small>Solo cuando la oferta no lo muestra.</small></div><input type="checkbox" id="bz_on" data-p="on"'+(c.on?' checked':'')+' onchange="boltIn(this)" style="width:26px;height:26px;flex:none"></div>'
   +'<div class="bz-g">'
   +'<label class="bz-f bz-w"><span>Qué perfil usar</span><select id="bz_mode" data-p="mode" onchange="boltIn(this)"><option value="auto"'+(c.mode==='auto'?' selected':'')+'>Automático por la fecha</option><option value="week"'+(c.mode==='week'?' selected':'')+'>Siempre lunes a viernes</option><option value="weekend"'+(c.mode==='weekend'?' selected':'')+'>Siempre fin de semana</option></select></label>'
   +cell('Comisión de Bolt (%)','bz_comm',show(c.comm),'comm',{step:'0.5'})+'<div></div></div>'
   +'<div class="bz-hint" id="bz_today"></div>'
   +'<div class="bz-seg"><button type="button" id="bz_tab_wd" class="'+(B.prof==='wd'?'on':'')+'" onclick="boltTab(\'wd\')">Lunes a viernes</button><button type="button" id="bz_tab_we" class="'+(B.prof==='we'?'on':'')+'" onclick="boltTab(\'we\')">Sáb., dom. y festivos</button></div>'
   +'<div class="bz-hint">El límite de arriba de cada tramo pertenece a ese tramo (un viaje de exactamente 10 km es del tramo 2). Los tramos van seguidos: al cambiar el «Hasta» de uno cambia el «Desde» del siguiente.</div>'
   +profHtml(B.prof)
   +'<div class="bz-sec"><b>Festivos (usan el perfil de fin de semana)</b><small>Fechas MM-DD (cada año) o AAAA-MM-DD, separadas por comas. Semana Santa y otros que cambian cada año, añádelos con el año.</small>'
   +'<textarea id="bz_hol" rows="3" data-p="holidays" oninput="boltIn(this)">'+esc((c.holidays||[]).join(', '))+'</textarea></div>'
   +simHtml()
   +'<div class="bz-sec"><b>🔊 Aviso por voz</b><div class="bz-row"><div><b>Leer en voz alta la estimación</b><br><small>«Bolt. Viaje de 8,3 kilómetros y 10 minutos. Bruto estimado… Neto estimado…»</small></div><input type="checkbox" id="bz_voice" onchange="boltIn(this)" data-p="#voice"'+(B.voice?' checked':'')+' style="width:26px;height:26px;flex:none"></div>'
   +'<label class="bz-f"><span>Volumen de la voz</span><input type="range" id="bz_vol" min="0.1" max="1" step="0.1" value="'+B.vol+'" data-p="#vol" oninput="boltIn(this)"></label></div>'
   +'<div class="bz-btns"><button type="button" class="action" onclick="boltSave()">✔ Guardar estimación de Bolt</button>'
   +'<button type="button" class="secondary" onclick="boltTestVoice()">🔊 Probar aviso de Bolt</button>'
   +'<button type="button" class="secondary" onclick="boltReset(\'cur\')">↺ Valores iniciales de este perfil</button>'
   +'<button type="button" class="secondary" onclick="boltReset(\'all\')">↺ Valores iniciales de todo</button></div>'
   +'<div id="bz_err" class="bz-err"></div>';
}
function render(){
  const box=document.getElementById('boltBox');if(!box)return;
  box.innerHTML='<details id="bz_det"'+(B.open?' open':'')+'><summary><b>💶 Estimación del precio de Bolt</b> <span class="bz-badge">NUEVO</span><br><small id="bz_sum"></small></summary><div id="bz_body">'+bodyHtml()+'</div></details>';
  const d=document.getElementById('bz_det');d.addEventListener('toggle',()=>{B.open=d.open});
  refreshDerived();
}
function refreshDerived(){
  const c=B.cfg,e=document.getElementById('bz_sum');
  if(e)e.textContent=(c.on?'Activada':'Desactivada')+' · comisión '+show(c.comm)+' % · hoy: '+(B.weekendNow?'fin de semana / festivo':'entre semana');
  const t=document.getElementById('bz_today');
  if(t)t.textContent='Hoy se usaría el perfil de '+(B.weekendNow?'sábados, domingos y festivos':'lunes a viernes')+'.';
  for(const pk of ['wd','we'])if(document.getElementById('bz_prof_'+pk))for(let i=0;i<4;i++){
    const r=document.getElementById('bz_'+pk+'_'+i+'_rg');if(r)r.textContent=rangeTxt(c[pk],i);
    if(i>0){const lo=document.getElementById('bz_'+pk+'_'+i+'_lo');if(lo&&document.activeElement!==lo)lo.value=show(c[pk].bp[i-1])}
    if(i<3){const hi=document.getElementById('bz_'+pk+'_'+i+'_hi');if(hi&&document.activeElement!==hi)hi.value=show(c[pk].bp[i])}
  }
  boltSim();
}
function getPath(o,p){return p.split('.').reduce((a,k)=>a&&a[k],o)}
function setPath(o,p,v){const ks=p.split('.'),l=ks.pop();const t=ks.reduce((a,k)=>a[k],o);t[l]=v}
function bad(el,on){el.classList.toggle('bz-bad',!!on)}
const errors=new Set();
window.boltIn=function(el){
  const p=el.getAttribute('data-p');if(p==null)return;
  if(p==='#voice'){B.voice=el.checked;return}
  if(p==='#vol'){B.vol=num(el.value)||1;return}
  if(el.type==='checkbox'){setPath(B.cfg,p,el.checked);if(p==='on')refreshDerived();return}
  if(p==='mode'){B.cfg.mode=el.value;B.weekendNow=isWeekend(B.cfg,new Date());refreshDerived();return}
  if(/\.mode$/.test(p)){setPath(B.cfg,p,el.value==='B'?'B':'A');boltSim();return}
  if(p==='holidays'){
    const items=el.value.split(/[\s,;]+/).filter(Boolean);const okAll=items.every(x=>/^(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})$/.test(x));
    bad(el,!okAll);okAll?errors.delete(el.id):errors.add(el.id);
    if(okAll){B.cfg.holidays=[...new Set(items)];B.weekendNow=isWeekend(B.cfg,new Date());refreshDerived()}
    return;
  }
  const v=num(el.value);
  const key=p.split('.').pop();
  const lim=/\.bp\./.test(p)?LIM.bp:key==='comm'?LIM.comm:key==='minFare'?LIM.minFare:LIM[key];
  let okv=Number.isFinite(v)&&(!lim||(v>=lim[0]&&v<=lim[1]));
  if(okv&&/\.bp\./.test(p)){            // los límites tienen que ir creciendo
    const [pk,,ix]=p.split('.'),arr=B.cfg[pk].bp.slice();arr[Number(ix)]=v;
    okv=arr[0]>0&&arr[1]>arr[0]&&arr[2]>arr[1];
  }
  bad(el,!okv);okv?errors.delete(el.id):errors.add(el.id);
  if(!okv)return;
  setPath(B.cfg,p,v);
  if(/\.bp\./.test(p)){                 // el «Hasta» de un tramo y el «Desde» del siguiente son el mismo límite
    const [pk,,ix]=p.split('.'),i=Number(ix);
    for(const id of ['bz_'+pk+'_'+i+'_hi','bz_'+pk+'_'+(i+1)+'_lo']){const o=document.getElementById(id);if(o&&o!==el){o.value=show(v);bad(o,false);errors.delete(o.id)}}
    errors.delete('bz_'+pk+'_'+i+'_hi');errors.delete('bz_'+pk+'_'+(i+1)+'_lo');
  }
  refreshDerived();
};
window.boltTab=function(pk){B.prof=pk;errors.clear();const b=document.getElementById('bz_body');if(b)b.innerHTML=bodyHtml();refreshDerived()};
window.boltSim=function(){
  const out=document.getElementById('bz_sOut');if(!out)return;
  const g=id=>{const e=document.getElementById(id);return e?num(e.value):NaN};
  const km=g('bz_sKm'),min=g('bz_sMin');let om=g('bz_sMult');const sp=document.getElementById('bz_sProf');
  if(sp)B.sim.prof=sp.value;
  B.sim.km=Number.isFinite(km)?km:B.sim.km;B.sim.min=Number.isFinite(min)?min:B.sim.min;
  const e0=document.getElementById('bz_sMult');B.sim.mult=e0?e0.value:'';
  if(!(km>=0)||!(min>=0)){out.innerHTML='<span class="bz-warn">Escribe los km y los minutos del viaje con pasajero.</span>';return}
  const wk=B.sim.prof==='we'?true:B.sim.prof==='wd'?false:B.weekendNow;
  const e=estimate(B.cfg,wk,km,min,Number.isFinite(om)&&om>0?om:-1);
  out.innerHTML='<div class="bz-big"><span>NETO ESTIMADO</span><b id="bz_sNet">'+money(e.net)+' €</b></div>'
   +'<div class="bz-line">Bruto estimado: <b id="bz_sGross">'+money(e.gross)+' €</b>'+(e.minApplied?' (tarifa mínima)':'')+' · Comisión ('+show(B.cfg.comm)+' %): <b id="bz_sComm">'+money(e.comm)+' €</b></div>'
   +'<div class="bz-line">Perfil: '+(wk?'fin de semana / festivo':'entre semana')+' · Tramo '+e.tier+' ('+rangeTxt(wk?B.cfg.we:B.cfg.wd,e.tier-1)+') · Demanda ×'+spoken(e.mult,2)+(e.fromOffer?' (de la oferta)':'')+' · Modo '+e.mode+'</div>'
   +'<div class="bz-line bz-voice">🔊 «'+esc(voiceText(e,km,min))+'»</div>';
};
window.boltSave=async function(silent){
  const err=document.getElementById('bz_err');
  if(errors.size){if(err)err.textContent='Revisa los campos marcados en rojo: hay valores fuera de rango o límites que no van creciendo.';if(!silent)alert('Revisa los campos marcados en rojo.');return false}
  if(!(B.cfg.wd.bp[0]>0&&B.cfg.wd.bp[1]>B.cfg.wd.bp[0]&&B.cfg.wd.bp[2]>B.cfg.wd.bp[1]&&B.cfg.we.bp[0]>0&&B.cfg.we.bp[1]>B.cfg.we.bp[0]&&B.cfg.we.bp[2]>B.cfg.we.bp[1])){if(err)err.textContent='Los límites de los tramos tienen que ir de menor a mayor.';return false}
  if(err)err.textContent='';
  let fixed=false;
  try{fixed=await persist()}catch(e){alert('No se pudo guardar la estimación de Bolt.');return false}
  if(fixed){const b=document.getElementById('bz_body');if(b)b.innerHTML=bodyHtml();refreshDerived();alert('Algún valor no era válido y se ha corregido. Revísalo antes de seguir.');return true}
  refreshDerived();
  if(!silent&&P.toastOk)P.toastOk('✅ Estimación de Bolt guardada');
  return true;
};
window.boltReset=function(which){
  const d=defaults();
  if(!confirm(which==='all'?'¿Volver a los valores iniciales de TODA la estimación de Bolt (los dos perfiles, comisión y festivos)?':'¿Volver a los valores iniciales de este perfil?\n\nNo se guarda hasta que pulses «Guardar».'))return;
  if(which==='all'){B.cfg=d}else B.cfg[B.prof]=d[B.prof];
  errors.clear();B.weekendNow=isWeekend(B.cfg,new Date());
  const b=document.getElementById('bz_body');if(b)b.innerHTML=bodyHtml();refreshDerived();
};
window.boltTestVoice=async function(){
  const ok=await window.boltSave(true);if(ok===false)return;
  const sr=SR();if(!sr){alert('Esta prueba solo funciona en el móvil, con la app instalada.');return}
  try{await sr.testBolt();if(P.toastOk)P.toastOk('Mira y escucha el aviso 👆')}catch(e){alert('Activa primero el lector de pantalla (Accesibilidad).')}
};

/* ---------- se integra en «Rentabilidad de viajes» ---------- */
const _rr=window.renderRent;
if(typeof _rr==='function')window.renderRent=async function(){
  const r=await _rr.apply(this,arguments);
  try{
    if(!document.getElementById('boltBox')){
      const anchor=document.getElementById('rStatBox')||document.querySelector('button[onclick="rentSave()"]');
      if(anchor){
        const box=document.createElement('div');box.id='boltBox';box.className='note bz-box';
        anchor.insertAdjacentElement('beforebegin',box);
        errors.clear();
        await load();
        render();
      }
    }
  }catch(e){console.warn('v3.14 bolt',e)}
  return r;
};
// «Guardar parámetros» de la pantalla guarda también la estimación de Bolt
const _rs=window.rentSave;
if(typeof _rs==='function')window.rentSave=async function(){
  const ok=await _rs.apply(this,arguments);
  if(ok===false)return false;
  if(document.getElementById('boltBox')&&document.getElementById('bz_body')){const b=await window.boltSave(true);if(b===false)return false}
  return ok;
};
// textos de ayuda
try{
  const e=jEntry('rentabilidad');
  if(e)e[4]='Es un aviso que salta arriba cuando te llega una oferta de Bolt, Uber o Cabify. Cada dato (€/hora, €/km y distancia de recogida) sale con su color: verde si cumple tu objetivo, naranja si se queda un poco corto y rojo si está lejos. Arriba del todo: ACEPTAR si todo está bien, RECHAZAR si algo está muy mal, y A VALORAR si está justo. Se activa en Ajustes → Rentabilidad de viajes. La oferta de Bolt no muestra el precio: la app lo ESTIMA con tus tarifas (4 tramos según los km del viaje con pasajero, con un perfil para entre semana y otro para sábados, domingos y festivos) y te dice bruto, comisión y NETO estimados, en pantalla y por voz. Son estimaciones tuyas, no tarifas oficiales de Bolt: los valores se corrigen en Ajustes → Rentabilidad de viajes → Estimación del precio de Bolt. En Uber la app lee una captura de la pantalla (dentro del móvil, sin guardarla). Solo avisa: no pulsa nada por ti.';
  J_KB.push(['boltestimacion','💶','Precio estimado de Bolt','precio bolt^6,estimar bolt^7,estimacion bolt^7,neto bolt^6,neto estimado^7,bolt no muestra el precio^8,tramos bolt^6,tarifa bolt^5,comision bolt^5,bruto estimado^6,voz bolt^5,multiplicador^5,demanda^4,fin de semana bolt^5','Bolt no enseña el precio en la oferta, así que la app lo estima: según los km del viaje con pasajero elige uno de 4 tramos (hasta 5, hasta 10, hasta 15 y más de 15 km por defecto), con un perfil para lunes a viernes y otro para sábados, domingos y festivos. Calcula bruto = base + km × precio/km + minutos × precio/min (con el multiplicador de demanda si lo hay), le quita la comisión (25 % al principio) y te da el NETO estimado, en pantalla y por voz. Son estimaciones, no tarifas oficiales: todos los valores se cambian en Ajustes → Rentabilidad de viajes → Estimación del precio de Bolt, donde también hay un simulador para contrastarlas con viajes reales.']);
}catch(e){}
// al abrir: si el teléfono perdió los ajustes de Bolt y la cuenta los tiene, se recuperan; y la cuenta guarda una copia
setTimeout(async()=>{
  try{
    const sr=SR();if(!sr)return;
    await load();
    if(B.saved&&db&&db.settings&&!db.settings.boltCfg){mirrorToDb(JSON.stringify(B.cfg));P.saveNow()}
  }catch(e){}
},1500);
})();
''')
]
CSS = r'''/* ===================== v3.14 ===================== */
/* --- botón Cancelaciones junto a Aeropuerto --- */
.airport-row{display:flex;gap:8px;align-items:stretch;margin-top:12px}
html body .airport-row>.airport-premium{flex:1 1 0;min-width:0;margin-top:0!important;gap:6px!important;padding:8px!important;min-height:78px!important}
html body .airport-row>.airport-premium .airport-plane{flex:0 0 40px!important;width:40px!important;height:40px!important;font-size:21px!important}
html body .airport-row>.airport-premium .airport-copy{padding-left:0!important;gap:3px!important}
html body .airport-row>.airport-premium .airport-copy strong{font-size:clamp(12px,3.5vw,15px)!important;white-space:normal!important;line-height:1.12!important}
html body .airport-row>.airport-premium .airport-copy small{font-size:clamp(9px,2.6vw,11px)!important;white-space:normal!important;line-height:1.2!important}
html body .airport-row>.airport-premium .airport-add{padding:0 5px!important;min-height:34px!important}
html body .airport-row>.airport-premium .airport-add>span{display:none}
html body .airport-row>.airport-premium .airport-luggage{display:none}
.cancel-btn{flex:0 0 clamp(80px,22.5vw,100px);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;padding:6px 2px;border:1px solid #ff9f73cc;border-radius:22px;background:linear-gradient(160deg,#3a120e 0%,#a3341d 55%,#34100c 100%);color:#fff;font-weight:900;font-size:clamp(9.5px,2.65vw,12px);line-height:1.1;letter-spacing:-.1px;text-align:center;box-shadow:0 0 14px #ff6a3d55,inset 0 1px 3px #ffffff44;cursor:pointer;touch-action:manipulation;-webkit-tap-highlight-color:transparent}
.cancel-btn:active{transform:scale(.97)}
.cancel-ico{display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;border:1px solid #ffb89a;background:radial-gradient(circle at 30% 20%,#ff7a4d,#7a1d0e 80%);font-size:16px;box-shadow:0 0 10px #ff6a3d77}
.cancel-txt{max-width:100%;overflow-wrap:anywhere}
/* --- ventana --- */
.cn-overlay{position:fixed;inset:0;z-index:99990;background:rgba(2,8,20,.78);display:flex;align-items:flex-end;justify-content:center;padding:12px;box-sizing:border-box}
.cn-card{width:100%;max-width:520px;max-height:92vh;overflow:auto;background:linear-gradient(160deg,#0d2a52,#071a33);border:2px solid #3fc8ff;border-radius:22px;padding:16px;color:#fff;box-shadow:0 0 24px #1e9bff66;box-sizing:border-box}
.cn-title{font-weight:900;font-size:20px}
.cn-day{color:#9fb4c8;font-size:13px;margin:3px 0 12px}
.cn-label{font-size:13px;color:#cfe3f5;margin:10px 0 5px;font-weight:700}
.cn-plats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.cn-plat{border:2px solid #ffffff33;border-radius:14px;padding:12px 4px;font-weight:900;font-size:15px;color:#fff;background:#13243d;cursor:pointer;touch-action:manipulation}
.cn-plat.bolt{background:linear-gradient(145deg,#1d9a4f,#0b5a2d)}
.cn-plat.uber{background:linear-gradient(145deg,#2a2f38,#0e1218)}
.cn-plat.cabify{background:linear-gradient(145deg,#8a3df0,#4b1c9e)}
.cn-plat.on{border-color:#7dffb0;box-shadow:0 0 0 2px #1fe58a88,0 0 14px #1fe58a99;transform:translateY(-1px)}
.cn-in{width:100%;box-sizing:border-box;padding:12px;border-radius:12px;border:1px solid #3a6ea5;background:#06142a;color:#fff;font-size:18px}
.cn-err{min-height:18px;color:#ffb4b4;font-size:13px;font-weight:700;margin-top:6px}
.cn-row{display:flex;gap:8px;margin-top:10px}
.cn-save{flex:2;padding:14px;border:0;border-radius:14px;background:linear-gradient(145deg,#22d27a,#0f8f4f);color:#fff;font-weight:900;font-size:16px;box-shadow:0 0 14px #1fe58a66;cursor:pointer}
.cn-save:disabled{opacity:.6}
.cn-cancel{flex:1;padding:14px;border:1px solid #ffffff33;border-radius:14px;background:#13243d;color:#fff;font-weight:800;font-size:15px;cursor:pointer}
.pdc-toast-ok{position:fixed;left:50%;bottom:92px;transform:translate(-50%,20px);opacity:0;pointer-events:none;z-index:99995;background:linear-gradient(145deg,#16c46e,#0b7a40);color:#fff;border:2px solid #8dffc0;border-radius:16px;padding:12px 18px;font:800 15px system-ui;box-shadow:0 0 18px #1fe58a88;transition:opacity .2s,transform .2s;max-width:92%;text-align:center}
.pdc-toast-ok.show{opacity:1;transform:translate(-50%,0)}
/* --- resumen y lista --- */
.canc-sum{margin:10px 0;padding:10px;border:1px solid #2b7eb4aa;border-radius:16px;background:rgba(3,20,36,.6)}
.canc-sum-title{font-weight:900;font-size:13px;color:#cfe3f5;margin-bottom:8px;letter-spacing:.3px}
.canc-sum-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.cs-cell{display:flex;flex-direction:column;gap:2px;padding:8px 6px;border-radius:12px;background:rgba(255,255,255,.05);border:1px solid #ffffff1a;min-width:0}
.cs-cell small{font-size:10px;color:#9fb4c8;font-weight:800;line-height:1.15}
.cs-cell b{font-size:clamp(14px,4.4vw,18px);font-weight:900;color:#fff;white-space:nowrap}
.cs-cell span{font-size:10px;color:#8fa6bb;line-height:1.15}
.cs-canc b{color:#ffb089}
.cs-total{border-color:#1fe58a77;background:rgba(18,120,76,.18)}
.cs-total b{color:#35efa0}
.canc-sum-tips{margin-top:8px;font-size:12px;color:#18c987}
.trip.canc{background:linear-gradient(90deg,rgba(255,110,70,.12),transparent 60%);border-left:3px solid #ff8a5c}
.trip.canc .orig{color:#35efa0;font-weight:800}
/* --- nómina --- */
.pr-off{opacity:.42}
.pr-off,input:disabled,select:disabled{cursor:not-allowed}
.pr-rule{margin-bottom:8px;line-height:1.45}
.pr-warn{color:#ffd166;margin:6px 0}
.pr-disc{font-size:12px;color:#9fb4c8;margin-top:10px;line-height:1.4}
.pr-legacy{border:1px solid #c58a2b;border-radius:12px;padding:10px;margin-bottom:10px;background:#3a2a0a55;line-height:1.5}
.pr-btn{display:block;margin-top:8px;padding:9px 12px;border-radius:12px;border:1px solid #ffd166;background:#5a3d08;color:#fff;font-weight:800;font-size:13px;cursor:pointer}
.payroll-row.pr-strong{font-weight:900;border-top:1px dashed #3a638f;padding-top:8px;margin-top:4px}
.payroll-row.pr-tips span,.payroll-row.pr-tips b{color:#18c987}

/* ===== Estimación del precio de Bolt ===== */
#boltBox{margin:12px 0}
#boltBox summary{cursor:pointer;list-style:none;position:relative;padding-right:22px}
#boltBox summary::-webkit-details-marker{display:none}
#boltBox summary::after{content:'›';position:absolute;right:2px;top:2px;font-size:22px;transition:transform .15s}
#boltBox details[open]>summary::after{transform:rotate(90deg)}
#boltBox summary small{color:#7aa2ff;font-weight:600}
#boltBox .bz-badge{background:#22c55e;color:#06210f;font-size:11px;font-weight:900;border-radius:8px;padding:2px 7px;margin-left:4px}
#boltBox .bz-note{margin:12px 0;padding:10px 12px;border-radius:14px;background:#ffffff10;line-height:1.45;font-size:13px;color:#cfe3f5}
#boltBox .bz-hint{margin:8px 0;font-size:12px;line-height:1.4;color:#9fb4c8}
#boltBox .bz-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0;border-top:1px solid #ffffff22}
#boltBox .bz-row small,#boltBox .bz-sec small{color:#9fb4c8;font-weight:500}
#boltBox .bz-g{display:grid;grid-template-columns:1fr 1fr;gap:8px 10px;margin:8px 0}
#boltBox .bz-f{display:flex;flex-direction:column;gap:3px;min-width:0}
#boltBox .bz-f>span{font-size:12px;font-weight:700;color:#cfe3f5;line-height:1.2}
#boltBox .bz-f input:not([type=checkbox]):not([type=range]),#boltBox .bz-f select,#boltBox textarea{width:100%;box-sizing:border-box;padding:9px 10px;border-radius:12px;font-size:15px}
#boltBox .bz-f input:disabled{opacity:.55}
#boltBox .bz-w{grid-column:1/-1}
#boltBox .bz-chk{grid-column:1/-1;flex-direction:row;align-items:center;gap:10px}
#boltBox .bz-chk input{width:24px;height:24px;flex:none}
#boltBox .bz-chk span{font-weight:600}
#boltBox .bz-top{margin-top:4px}
#boltBox .bz-seg{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:12px 0 6px}
#boltBox .bz-seg button{border:1px solid #ffffff33;border-radius:14px;padding:10px 6px;font-weight:800;background:#ffffff12;color:#cfe3f5;font-size:13px}
#boltBox .bz-seg button.on{background:#2563eb;border-color:#60a5fa;color:#fff}
#boltBox .bz-t{margin:10px 0;padding:10px;border:1px solid #ffffff2a;border-radius:16px;background:#ffffff0a}
#boltBox .bz-th{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap}
#boltBox .bz-th span{font-size:12px;color:#7aa2ff;font-weight:700}
#boltBox .bz-sec{margin:14px 0;padding-top:10px;border-top:1px solid #ffffff22}
#boltBox .bz-sec>small{display:block;margin:2px 0 6px}
#boltBox textarea{margin-top:4px;font-family:inherit}
#boltBox .bz-out{margin-top:8px;padding:10px;border-radius:14px;background:#06121f;border:1px solid #1d4ed855}
#boltBox .bz-big{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:8px 12px;border-radius:12px;background:#14532d;border:1px solid #22c55e}
#boltBox .bz-big span{font-size:12px;font-weight:800;letter-spacing:.04em;color:#bbf7d0}
#boltBox .bz-big b{font-size:26px;color:#fff}
#boltBox .bz-line{margin-top:6px;font-size:12.5px;line-height:1.4;color:#cfe3f5}
#boltBox .bz-voice{color:#9fb4c8;font-style:italic}
#boltBox .bz-warn{color:#fbbf24}
#boltBox .bz-btns{display:grid;grid-template-columns:1fr;gap:8px;margin-top:12px}
#boltBox .bz-btns button{width:100%}
#boltBox .bz-err{color:#fca5a5;font-weight:700;font-size:13px;margin-top:8px}
#boltBox input.bz-bad,#boltBox textarea.bz-bad,#boltBox select.bz-bad{border-color:#ef4444!important;background:#fee2e2!important;color:#7f1d1d}
@media (min-width:600px){#boltBox .bz-g{grid-template-columns:repeat(3,1fr)}#boltBox .bz-btns{grid-template-columns:1fr 1fr}}
'''


def kind(n):
    return 'pre' if n.startswith('01_') else ('early' if n.startswith('05_') else 'late')


def bundle(k):
    return '\n'.join(t for n, t in MODS if kind(n) == k)


# ---------------------------------------------------------------- Java
"""Cambios de Java de la v3.14 (Bolt: estimacion por tramos, aviso con NETO destacado, voz, ajustes guardados).
Todo o nada: si falta cualquier ancla no se escribe NADA. Se usa tanto en las pruebas como incrustado en v314.py."""
import os


def apply_java(J, MAN, OFFER, BOLTCFG, SVC_BLOCK, PLG_BLOCK):
    """J: carpeta de los .java, MAN: ruta del AndroidManifest.xml. Devuelve lista de (etiqueta, n) o lanza SystemExit sin escribir nada."""
    svc_path, plg_path = J + 'ScreenReaderService.java', J + 'ScreenReaderPlugin.java'
    svc = open(svc_path, encoding='utf-8').read()
    plg = open(plg_path, encoding='utf-8').read()
    man = open(MAN, encoding='utf-8').read()
    rep = []

    svc_edits = [
        ('import android.widget.Toast;\n',
         'import android.widget.Toast;\nimport android.os.Bundle;\nimport android.media.AudioAttributes;\nimport android.speech.tts.TextToSpeech;\n', 'bolt-imports'),
        ('OfferAnalyzer.Result r = OfferAnalyzer.analyze(nodes, rentParams());',
         'OfferAnalyzer.Result r = OfferAnalyzer.analyze(nodes, rentParams(), false, BOLT_PKG.matcher(pkg).find());', 'bolt-analizar'),
        ('showAlert(found);', 'showAlert(found);\n                speakOffer(found);', 'bolt-voz'),
        ('p.tolPickup = sp.getFloat("rent_tolPickup", 1f);',
         'p.tolPickup = sp.getFloat("rent_tolPickup", 1f);\n        p.bolt = boltCfg();\n        p.weekendNow = OfferAnalyzer.isWeekend(p.bolt, java.util.Calendar.getInstance());', 'bolt-parametros'),
        ('    private void showAlert(OfferAnalyzer.Result r) {\n',
         '    private void showAlert(OfferAnalyzer.Result r) {\n        if (r.estimated) { showEstimateAlert(r); return; }\n        resetEstimateViews();\n', 'bolt-aviso-gancho'),
        ('    private void hideAlert() {\n', '    private void hideAlert() {\n        stopSpeech();\n', 'bolt-callar'),
        ('    public void forceBubble() {\n', SVC_BLOCK.rstrip('\n') + '\n\n    public void forceBubble() {\n', 'bolt-bloque'),
        ('        hideBubble();\n        hideAlert();\n        instance = null;',
         '        hideBubble();\n        hideAlert();\n        shutdownTts();\n        instance = null;', 'bolt-liberar-voz'),
        ('" | precio " + r.price + " | viaje "', '(r.estimated ? " | neto estimado Bolt " : " | precio ") + r.price + " | viaje "', 'bolt-diag-1'),
        ('" precio=" + r.price + " viajeKm="', '(r.estimated ? " netoEstimadoBolt=" : " precio=") + r.price + " viajeKm="', 'bolt-diag-2'),
    ]
    plg_edits = [
        ('    @PluginMethod\n    public void testRent(PluginCall call) {\n',
         PLG_BLOCK.rstrip('\n') + '\n\n    @PluginMethod\n    public void testRent(PluginCall call) {\n', 'bolt-plugin'),
    ]
    applied = 'showEstimateAlert' in svc and 'public void getBolt' in plg

    def plan(text, edits, name):
        out = text
        for old, new, label in edits:
            n = out.count(old)
            if n != 1:
                raise SystemExit('ERROR (%s, %s): la ancla aparece %d veces y debia aparecer 1. No se ha cambiado nada.' % (name, label, n))
            out = out.replace(old, new, 1)
            rep.append((label, 1))
        return out

    new_svc, new_plg = svc, plg
    if not applied:
        new_svc = plan(svc, svc_edits, 'ScreenReaderService.java')
        new_plg = plan(plg, plg_edits, 'ScreenReaderPlugin.java')
    # AndroidManifest: desde Android 11 hay que declarar que se usa el motor de voz
    new_man = man
    if 'TTS_SERVICE' not in man:
        q = '<intent><action android:name="android.intent.action.TTS_SERVICE" /></intent>'
        if '<queries>' in man:
            new_man = man.replace('<queries>', '<queries>\n        ' + q, 1)
        elif man.count('<application') == 1:
            new_man = man.replace('<application', '<queries>\n        ' + q + '\n    </queries>\n\n    <application', 1)
        else:
            raise SystemExit('ERROR (AndroidManifest.xml): no encuentro <application>. No se ha cambiado nada.')
        rep.append(('manifest-voz', 1))
    # todo comprobado: ahora si, escribir
    def ascii_java(t):
        for ch in t:
            if ord(ch) > 0xFFFF:
                raise SystemExit('ERROR: caracter fuera del plano basico en el Java generado')
        return ''.join(c if ord(c) < 128 else '\\u%04x' % ord(c) for c in t)   # escapes de Java (\uXXXX), no los \xNN de Python
    open(J + 'OfferAnalyzer.java', 'w', encoding='utf-8').write(ascii_java(OFFER)); rep.append(('analizador-bolt-por-tramos', 1))
    open(J + 'BoltConfig.java', 'w', encoding='utf-8').write(ascii_java(BOLTCFG)); rep.append(('ajustes-bolt-json', 1))
    if new_svc != svc: open(svc_path, 'w', encoding='utf-8').write(ascii_java(new_svc))
    if new_plg != plg: open(plg_path, 'w', encoding='utf-8').write(ascii_java(new_plg))
    if new_man != man: open(MAN, 'w', encoding='utf-8').write(new_man)
    return rep

OFFER = r'''package com.portal.conductor;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Lee el texto de una oferta (Bolt/Uber/Cabify) y calcula si compensa. Sin dependencias de Android. */
public class OfferAnalyzer {

    public static class Params {
        public double minHour = 15, minKm = 1.0, maxPickup = 5.0, commission = 0, tolPct = 15, tolPickup = 1.0;
        public boolean includePickup = true;
        public BoltCfg bolt = new BoltCfg();     // estimacion de Bolt cuando la oferta no trae precio
        public boolean weekendNow = false;       // perfil de fin de semana/festivo (lo decide quien llama con isWeekend)
    }

    public static class Result {
        public boolean offer;
        public String verdict = "DATA";           // OK, NO, DATA
        public double price = -1, tripKm = -1, tripMin = -1, pickupKm = -1, pickupMin = -1, perHour = -1, perKm = -1;
        public String reason = "";
        public boolean orderAssumed;
        public String why = "";
        public boolean acceptSeen, unreadable;
        public int stH = -1, stK = -1, stP = -1;   // 0 verde, 1 naranja, 2 rojo, -1 sin dato
        // ---- estimacion de Bolt (solo si la oferta no trae precio) ----
        public boolean isBolt, estimated, estWeekend, estMinApplied;
        public double estGross = -1, estComm = -1, estNet = -1, estMult = 1, estOfferMult = -1, estLo = -1, estHi = -1;
        public int estTier = -1;
        public double estCommPct = -1;
        public String estMode = "";
    }

    // =====================================================================
    //  Estimacion del precio de Bolt cuando la oferta NO muestra el precio.
    //  Todos los valores son ESTIMACIONES editables por el conductor, NO son tarifas oficiales de Bolt.
    // =====================================================================

    /** Un tramo de distancia del viaje con pasajero. */
    public static class Tier {
        public double base, perKm, perMin, mult = 1.0;
        public String mode = "A";            // A: el multiplicador solo afecta a los km; B: afecta al importe completo
        public Tier() { }
        public Tier(double base, double perKm, double perMin) { this.base = base; this.perKm = perKm; this.perMin = perMin; }
        public Tier copy() { Tier t = new Tier(base, perKm, perMin); t.mult = mult; t.mode = mode; return t; }
    }

    /** Perfil de tarifas con 4 tramos continuos: bp[0], bp[1] y bp[2] son el fin de los tramos 1, 2 y 3. */
    public static class Profile {
        public double[] bp = {5, 10, 15};
        public Tier[] t = new Tier[4];
        public double minFare = 0;           // 0 = sin tarifa minima
        public boolean offerMult = true;     // usar el xN que muestre la oferta, si aparece
        public Profile copy() {
            Profile p = new Profile();
            p.bp = new double[]{bp[0], bp[1], bp[2]};
            for (int i = 0; i < 4; i++) p.t[i] = t[i].copy();
            p.minFare = minFare; p.offerMult = offerMult;
            return p;
        }
    }

    public static class BoltCfg {
        public boolean on = true;
        public String mode = "auto";         // auto (por fecha) | week | weekend
        public double comm = 25;             // comision de Bolt, %
        public Profile wd = defaultWeekday(), we = defaultWeekend();
        public List<String> holidays = defaultHolidays();   // "yyyy-MM-dd" o "MM-dd"
    }

    public static Profile defaultWeekday() {
        Profile p = new Profile();
        p.t[0] = new Tier(3.50, 0.95, 0.11);
        p.t[1] = new Tier(3.50, 0.80, 0.11);
        p.t[2] = new Tier(1.95, 0.95, 0.11);
        p.t[3] = new Tier(1.95, 0.80, 0.11);
        p.minFare = 5.95;
        return p;
    }

    /** Valores provisionales de fin de semana: 5,50 base, 1,70 por km y 0,22 por minuto en los cuatro tramos. */
    public static Profile defaultWeekend() {
        Profile p = new Profile();
        for (int i = 0; i < 4; i++) p.t[i] = new Tier(5.50, 1.70, 0.22);
        p.minFare = 9.00;
        return p;
    }

    /** Festivos nacionales fijos y el de la Comunidad de Madrid. Los que cambian cada ano (Semana Santa) se anaden a mano con aaaa-mm-dd. */
    public static List<String> defaultHolidays() {
        List<String> l = new ArrayList<String>();
        for (String s : new String[]{"01-01", "01-06", "05-01", "05-02", "08-15", "10-12", "11-01", "12-06", "12-08", "12-25"}) l.add(s);
        return l;
    }

    /** Tramo (0..3) segun los km del viaje con pasajero. El limite superior pertenece al tramo de abajo: sin huecos ni solapes. */
    public static int tierIndex(Profile p, double km) {
        if (km <= p.bp[0]) return 0;
        if (km <= p.bp[1]) return 1;
        if (km <= p.bp[2]) return 2;
        return 3;
    }

    /** true si hoy se aplica el perfil de fin de semana / festivo. */
    public static boolean isWeekend(BoltCfg c, java.util.Calendar cal) {
        if ("week".equals(c.mode)) return false;
        if ("weekend".equals(c.mode)) return true;
        int dow = cal.get(java.util.Calendar.DAY_OF_WEEK);
        if (dow == java.util.Calendar.SATURDAY || dow == java.util.Calendar.SUNDAY) return true;
        int mo = cal.get(java.util.Calendar.MONTH) + 1, dd = cal.get(java.util.Calendar.DAY_OF_MONTH), yy = cal.get(java.util.Calendar.YEAR);
        String full = String.format(Locale.ROOT, "%04d-%02d-%02d", yy, mo, dd), md = String.format(Locale.ROOT, "%02d-%02d", mo, dd);
        if (c.holidays != null) for (String h : c.holidays) if (full.equals(h) || md.equals(h)) return true;
        return false;
    }

    public static class Est {
        public double gross, comm, net, mult, lo, hi;
        public int tier;                     // 1..4
        public String mode = "A";
        public boolean minApplied, weekend, fromOffer;
    }

    /** Bruto = base + km*precioKm*mult + min*precioMin (modo A) o (base + km*precioKm + min*precioMin)*mult (modo B). Sin redondeos intermedios. */
    public static Est estimate(BoltCfg c, boolean weekend, double km, double min, double offerMult) {
        Profile pr = weekend ? c.we : c.wd;
        int ti = tierIndex(pr, km);
        Tier t = pr.t[ti];
        boolean fromOffer = pr.offerMult && offerMult > 0;
        double mult = fromOffer ? offerMult : t.mult;
        mult = Math.max(0.1, Math.min(10.0, mult));
        double gross = "B".equals(t.mode) ? (t.base + km * t.perKm + min * t.perMin) * mult : t.base + km * t.perKm * mult + min * t.perMin;
        boolean ma = false;
        if (pr.minFare > 0 && gross < pr.minFare) { gross = pr.minFare; ma = true; }
        double pct = Math.max(0, Math.min(90, c.comm));
        Est e = new Est();
        e.gross = gross; e.comm = gross * pct / 100.0; e.net = gross - e.comm;
        e.mult = mult; e.tier = ti + 1; e.mode = "B".equals(t.mode) ? "B" : "A";
        e.lo = ti == 0 ? 0 : pr.bp[ti - 1]; e.hi = ti == 3 ? -1 : pr.bp[ti];
        e.minApplied = ma; e.weekend = weekend; e.fromOffer = fromOffer;
        return e;
    }

    // multiplicador de demanda que a veces muestra la oferta: "x1.7", "x1,4", "1.5x"
    private static final Pattern DEM1 = Pattern.compile("(?<![A-Za-z0-9])[x×]\\s?(\\d{1,2}(?:[.,]\\d{1,2})?)(?![\\d%A-Za-z])", Pattern.CASE_INSENSITIVE);
    private static final Pattern DEM2 = Pattern.compile("(?<![\\d.,])(\\d{1,2}(?:[.,]\\d{1,2})?)\\s?[x×](?![A-Za-z0-9])", Pattern.CASE_INSENSITIVE);

    static double detectDemand(List<String> nodes) {
        for (String t : nodes) {
            String s = t.trim(), n = norm(s);
            boolean dem = n.contains("demanda") || n.contains("surge") || n.contains("multiplicador");
            if (!dem && s.length() > 14) continue;
            Matcher m = DEM1.matcher(s);
            if (!m.find()) { m = DEM2.matcher(s); if (!m.find()) continue; }
            double v = num(m.group(1));
            if (v >= 1.0 && v <= 6.0) return v;
        }
        return -1;
    }

    /** Importe con 2 decimales y coma, sin ruido de coma flotante. */
    public static String money(double v) {
        return java.math.BigDecimal.valueOf(Math.round(v * 1e6) / 1e6).setScale(2, java.math.RoundingMode.HALF_UP).toPlainString().replace('.', ',');
    }

    /** Numero para la voz: coma decimal, sin ceros sobrantes (8,3 / 8 / 1,45). */
    private static String spokenNum(double v, int dec) {
        return java.math.BigDecimal.valueOf(v).setScale(dec, java.math.RoundingMode.HALF_UP).stripTrailingZeros().toPlainString().replace('.', ',');
    }

    /** Frase para el aviso por voz (con los valores reales de la oferta). null si no hay nada que decir. */
    public static String voiceText(Result r) {
        if (r == null || !r.isBolt || !r.offer) return null;
        if (r.estimated) {
            long min = Math.round(r.tripMin);
            String km = spokenNum(r.tripKm, 1);
            StringBuilder b = new StringBuilder("Bolt. Viaje de ").append(km).append("1".equals(km) ? " kil\u00F3metro y " : " kil\u00F3metros y ").append(min).append(min == 1 ? " minuto" : " minutos");
            if (Math.abs(r.estMult - 1.0) > 1e-9) b.append(", demanda por ").append(spokenNum(r.estMult, 2));
            b.append(". Bruto estimado: ").append(money(r.estGross)).append(" euros. Comisión estimada: ").append(money(r.estComm)).append(" euros. Neto estimado: ").append(money(r.estNet)).append(" euros.");
            return b.toString();
        }
        if (r.price > 0) return "Bolt. Precio de la oferta: " + money(r.price) + " euros.";
        return null;
    }


    private static class Item { int node; char kind; double v; boolean used; }
    private static class Seg { double km = -1, min = -1; String ctx = ""; int first = 99; }

    private static final Pattern EUR1 = Pattern.compile("(\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}[.,]\\d{1,2})\\s*(?:\u20AC|eur\\b)", Pattern.CASE_INSENSITIVE);
    private static final Pattern EUR2 = Pattern.compile("\u20AC\\s*(\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}[.,]\\d{1,2})", Pattern.CASE_INSENSITIVE);
    private static final Pattern KM = Pattern.compile("(\\d+(?:[.,]\\d+)?)\\s*km\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern MET = Pattern.compile("(?<![\\d.,])(\\d{2,4})\\s*m(?![a-zA-Z])");
    private static final Pattern MIN = Pattern.compile("(?:(\\d+)\\s*h(?:ora)?s?\\s*)?(\\d+)\\s*min", Pattern.CASE_INSENSITIVE);
    private static final Pattern HOURS = Pattern.compile("(?<![\\d.,])(\\d+)\\s*h(?:ora)?s?\\b(?!\\s*\\d+\\s*min)", Pattern.CASE_INSENSITIVE);
    private static final String[] PICK = {"recog", "recoj", "pasajero", "away", "de distancia", "cliente", "pickup", "hasta el"};
    private static final String[] TRIP = {"viaje", "trayecto", "recorrido", "destino", "trip", "total", "duracion", "drop"};
    private static final String[] ACCEPT = {"aceptar", "accept", "seleccionar", "rechazar", "reject", "declinar", "decline", "emparejar", "match"};

    public static String norm(String s) {
        String n = Normalizer.normalize(s == null ? "" : s, Normalizer.Form.NFD).replaceAll("\\p{M}", "");
        return n.toLowerCase(Locale.ROOT);
    }

    private static double num(String s) {
        String t = s.trim();
        if (t.contains(",") && t.contains(".")) t = t.replace(".", "").replace(",", ".");
        else t = t.replace(",", ".");
        try { return Double.parseDouble(t); } catch (Exception e) { return -1; }
    }

    private static boolean has(String s, String[] kws) { for (String k : kws) if (s.contains(k)) return true; return false; }

    private static String clean(String t) {
        String x = t == null ? "" : t.replace('\u00A0', ' ').replace('\u202F', ' ').replace('\u2009', ' ').replace('\u200A', ' ').replace('\u2007', ' ');
        x = x.replaceAll("(?i)\\bkil[o\u00F3]metros?\\b", "km").replaceAll("(?i)\\bminutos?\\b", "min").replaceAll("(?i)\\bmins\\b", "min");
        x = x.replaceAll("(?i)\\beuros?\\b", "\u20AC").replaceAll("(?i)(\\d)\\s*metros?\\b", "$1 m");
        return x;
    }

    /** el boton de aceptar de la oferta (no vale cualquier texto que contenga la palabra) */
    private static boolean isAcceptNode(String raw) {
        String n = norm(raw).replaceAll("[^a-z ]", " ").replaceAll("\\s+", " ").trim();
        if (n.length() == 0 || n.length() > 28) return false;
        return n.startsWith("aceptar") || n.startsWith("emparejar") || n.equals("accept") || n.equals("match");
    }

    private static final Pattern LONEPRICE = Pattern.compile("^\\D{0,3}(\\d{1,3}[.,]\\d{2})\\s*\\S{0,2}$");

    private static int stMin(double v, double min, double tolPct) {
        if (v >= min) return 0;
        return v >= min * (1 - tolPct / 100.0) ? 1 : 2;
    }

    public static Result analyze(List<String> rawNodes, Params p) { return analyze(rawNodes, p, false); }

    public static Result analyze(List<String> rawNodes, Params p, boolean lenient) { return analyze(rawNodes, p, lenient, false); }

    /** isBolt: la oferta viene de Bolt (paquete bolt/mtakso). Solo en ese caso, y sin precio visible, se estima el precio. */
    public static Result analyze(List<String> rawNodes, Params p, boolean lenient, boolean isBolt) {
        List<String> nodes = new ArrayList<String>();
        for (String x : rawNodes) for (String line : clean(x).split("\\n")) if (line.trim().length() > 0) nodes.add(line.trim());
        Result r = new Result();
        // ---- precio: primer importe en euros razonable
        for (String t : nodes) {
            Matcher m = EUR1.matcher(t); double v = -1;
            if (m.find()) v = num(m.group(1)); else { Matcher m2 = EUR2.matcher(t); if (m2.find()) v = num(m2.group(1)); }
            if (v >= 1.0 && v < 1000) { r.price = v; break; }
        }
        if (r.price <= 0 && lenient) {
            for (String t : nodes) { Matcher m = LONEPRICE.matcher(t.trim()); if (m.find()) { double v = num(m.group(1)); if (v >= 1.0 && v < 1000) { r.price = v; break; } } }
        }
        // ---- elementos km / min por nodo
        List<Item> items = new ArrayList<Item>();
        StringBuilder all = new StringBuilder();
        for (int i = 0; i < nodes.size(); i++) {
            String t = nodes.get(i); all.append(norm(t)).append('\n');
            Matcher k = KM.matcher(t);
            while (k.find()) { Item it = new Item(); it.node = i; it.kind = 'k'; it.v = num(k.group(1)); items.add(it); }
            String rest = KM.matcher(t).replaceAll(" ");
            Matcher mt = MET.matcher(rest);
            while (mt.find()) { Item it = new Item(); it.node = i; it.kind = 'k'; it.v = num(mt.group(1)) / 1000.0; items.add(it); }
            Matcher mi = MIN.matcher(t);
            while (mi.find()) { Item it = new Item(); it.node = i; it.kind = 'm'; it.v = (mi.group(1) != null ? num(mi.group(1)) * 60 : 0) + num(mi.group(2)); items.add(it); }
        }
        boolean accept = false;
        for (String nd : nodes) if (isAcceptNode(nd)) { accept = true; break; }
        r.acceptSeen = accept;
        int kmCount = 0, minCount = 0;
        for (Item it : items) { if (it.kind == 'k') kmCount++; else minCount++; }
        r.offer = accept && kmCount >= 1 && minCount >= 1 && (r.price > 0 || (kmCount >= 2 && minCount >= 2));
        if (!r.offer) { r.why = "precio=" + r.price + " km=" + kmCount + " min=" + minCount + " aceptar=" + accept; return r; }
        // ---- emparejar km con minutos: 1) mismo nodo, 2) nodos contiguos
        List<Seg> segs = new ArrayList<Seg>();
        List<Item[]> pairs = new ArrayList<Item[]>();
        // fase A: km y minutos en el mismo nodo
        for (Item a : items) {
            if (a.kind != 'k' || a.used) continue;
            for (Item b : items) {
                if (b.kind == 'm' && !b.used && b.node == a.node) { a.used = true; b.used = true; pairs.add(new Item[]{a, b}); break; }
            }
        }
        // fase B: el minuto va justo antes del km (tambien con un "•" entre medias) o, si no, justo despues
        for (Item a : items) {
            if (a.kind != 'k' || a.used) continue;
            Item best = null;
            for (int d = 1; d <= 2 && best == null; d++) {
                if (d == 2 && (a.node < 1 || nodes.get(a.node - 1).trim().length() > 2)) break;
                for (Item b : items) if (b.kind == 'm' && !b.used && b.node == a.node - d) { best = b; break; }
            }
            if (best == null) for (Item b : items) if (b.kind == 'm' && !b.used && b.node == a.node + 1) { best = b; break; }
            if (best != null) { a.used = true; best.used = true; pairs.add(new Item[]{a, best}); }
        }
        for (Item a : items) if (a.kind == 'k' && !a.used) { a.used = true; pairs.add(new Item[]{a, null}); }
        for (Item[] pr : pairs) {
            Seg s = new Seg(); s.km = pr[0].v; s.first = pr[0].node;
            StringBuilder own = new StringBuilder(norm(nodes.get(pr[0].node)));
            int firstNode = pr[0].node;
            if (pr[1] != null) { s.min = pr[1].v; firstNode = Math.min(firstNode, pr[1].node); s.first = firstNode; if (pr[1].node != pr[0].node) own.append(' ').append(norm(nodes.get(pr[1].node))); }
            String ownS = own.toString();
            // si el propio texto no trae pistas, se mira la l\u00EDnea anterior (etiqueta encima del valor)
            String prevS = firstNode > 0 ? norm(nodes.get(firstNode - 1)).trim() : "";
            boolean prevIsLabel = prevS.length() > 0 && prevS.length() <= 22 && !prevS.matches(".*\\d.*");
            s.ctx = (has(ownS, PICK) || has(ownS, TRIP) || !prevIsLabel) ? ownS : ownS + " " + prevS;
            segs.add(s);
        }
        for (Item b : items) {
            if (b.kind == 'm' && !b.used) { Seg s = new Seg(); s.min = b.v; s.first = b.node; s.ctx = norm(nodes.get(b.node)) + (b.node > 0 ? " " + norm(nodes.get(b.node - 1)) : ""); segs.add(s); }
        }
        java.util.Collections.sort(segs, new java.util.Comparator<Seg>() { public int compare(Seg x, Seg y) { return x.first - y.first; } });
        // ---- recogida o viaje
        Seg pick = null, trip = null;
        for (Seg s : segs) {
            boolean ip = has(s.ctx, PICK), it = has(s.ctx, TRIP);
            if (ip && !it && pick == null) pick = s; else if (it && !ip && trip == null) trip = s;
        }
        List<Seg> rest = new ArrayList<Seg>();
        for (Seg s : segs) if (s != pick && s != trip) rest.add(s);
        if (pick == null && trip == null && rest.size() >= 2) { pick = rest.get(0); trip = rest.get(1); r.orderAssumed = true; }
        else if (trip == null && !rest.isEmpty()) { trip = rest.get(rest.size() - 1); if (pick == null && rest.size() >= 2) pick = rest.get(0); r.orderAssumed = true; }
        else if (pick == null && !rest.isEmpty() && trip != null) { pick = rest.get(0); r.orderAssumed = true; }
        if (trip != null) { r.tripKm = trip.km; r.tripMin = trip.min; }
        if (pick != null) { r.pickupKm = pick.km; r.pickupMin = pick.min; }
        // ---- Bolt sin precio visible: estimacion con los km y minutos del viaje con pasajero (nunca los de recogida)
        r.isBolt = isBolt;
        boolean useEstimate = false;
        boolean boltEst = isBolt && p.bolt != null && p.bolt.on;
        if (r.price <= 0 && boltEst) {
            boolean tripSure = !(r.orderAssumed && pick == null);   // un unico bloque sin etiqueta no se da por viaje
            if (tripSure && r.tripKm > 0 && r.tripMin > 0) {
                double om = detectDemand(nodes);
                Est e = estimate(p.bolt, p.weekendNow, r.tripKm, r.tripMin, om);
                r.estimated = true; r.estGross = e.gross; r.estComm = e.comm; r.estNet = e.net; r.estMult = e.mult;
                r.estOfferMult = om; r.estMode = e.mode; r.estTier = e.tier; r.estLo = e.lo; r.estHi = e.hi;
                r.estMinApplied = e.minApplied; r.estWeekend = e.weekend; r.estCommPct = Math.max(0, Math.min(90, p.bolt.comm));
                r.price = e.net;          // el semaforo se juzga sobre el NETO estimado; no se vuelve a descontar comision
                useEstimate = true;
            }
        }
        // ---- oferta sin precio visible: solo se puede juzgar la distancia de recogida
        if (r.price <= 0) {
            r.stP = r.pickupKm > 0 ? (r.pickupKm <= p.maxPickup ? 0 : (r.pickupKm <= p.maxPickup + p.tolPickup ? 1 : 2)) : -1;
            if (r.stP == 2) { r.verdict = "NO"; r.reason = String.format(Locale.GERMANY, "recogida %.1f km (m\u00E1x. %.1f)", r.pickupKm, p.maxPickup); }
            else { r.verdict = "DATA"; r.reason = boltEst ? "No se pudo estimar el precio de Bolt: faltan los km o los minutos del viaje con pasajero." : "Esta oferta no muestra el precio."; }
            return r;
        }
        // ---- datos suficientes
        if (r.tripKm <= 0 || r.tripMin <= 0) { r.verdict = "DATA"; r.reason = r.tripMin <= 0 ? "No se pudo leer el tiempo del viaje." : "No se pudo leer la distancia del viaje."; return r; }
        double net = useEstimate ? r.price : r.price * (1 - Math.max(0, Math.min(90, p.commission)) / 100.0);
        double km = r.tripKm + (p.includePickup && r.pickupKm > 0 ? r.pickupKm : 0);
        double min = r.tripMin + (p.includePickup && r.pickupMin > 0 ? r.pickupMin : 0);
        r.perKm = net / km; r.perHour = net / (min / 60.0);
        List<String> bad = new ArrayList<String>();
        r.stH = stMin(r.perHour, p.minHour, p.tolPct);
        r.stK = stMin(r.perKm, p.minKm, p.tolPct);
        r.stP = r.pickupKm > 0 ? (r.pickupKm <= p.maxPickup ? 0 : (r.pickupKm <= p.maxPickup + p.tolPickup ? 1 : 2)) : -1;
        if (r.stH > 0) bad.add(String.format(Locale.GERMANY, "\u20AC/h %.1f (m\u00EDn. %.2f)", r.perHour, p.minHour));
        if (r.stK > 0) bad.add(String.format(Locale.GERMANY, "\u20AC/km %.2f (m\u00EDn. %.2f)", r.perKm, p.minKm));
        if (r.stP > 0) bad.add(String.format(Locale.GERMANY, "recogida %.1f km (m\u00E1x. %.1f)", r.pickupKm, p.maxPickup));
        int worst = Math.max(r.stH, Math.max(r.stK, r.stP));
        r.verdict = worst >= 2 ? "NO" : (worst == 1 ? "WARN" : "OK");
        r.reason = bad.isEmpty() ? "Cumple tus objetivos." : join(bad);
        return r;
    }

    private static String join(List<String> l) { StringBuilder b = new StringBuilder(); for (int i = 0; i < l.size(); i++) { if (i > 0) b.append(" \u00B7 "); b.append(l.get(i)); } return b.toString(); }
}
'''
BOLTCFG = r'''package com.portal.conductor;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Lee y escribe (JSON) los ajustes de la estimacion de precio de Bolt. Sin dependencias de Android. */
public class BoltConfig {

    // ------------------------------------------------------------------ mini lector de JSON
    private static class P {
        final String s;
        int i = 0;
        P(String s) { this.s = s; }

        void ws() { while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++; }

        Object val() {
            ws();
            char c = s.charAt(i);
            if (c == '{') return obj();
            if (c == '[') return arr();
            if (c == '"') return str();
            if (s.startsWith("true", i)) { i += 4; return Boolean.TRUE; }
            if (s.startsWith("false", i)) { i += 5; return Boolean.FALSE; }
            if (s.startsWith("null", i)) { i += 4; return null; }
            return num();
        }

        Map<String, Object> obj() {
            Map<String, Object> m = new LinkedHashMap<String, Object>();
            i++; ws();
            if (s.charAt(i) == '}') { i++; return m; }
            while (true) {
                ws();
                String k = str();
                ws();
                if (s.charAt(i++) != ':') throw new IllegalStateException("falta ':'");
                m.put(k, val());
                ws();
                char c = s.charAt(i++);
                if (c == '}') return m;
                if (c != ',') throw new IllegalStateException("falta ','");
            }
        }

        List<Object> arr() {
            List<Object> l = new ArrayList<Object>();
            i++; ws();
            if (s.charAt(i) == ']') { i++; return l; }
            while (true) {
                l.add(val());
                ws();
                char c = s.charAt(i++);
                if (c == ']') return l;
                if (c != ',') throw new IllegalStateException("falta ','");
            }
        }

        String str() {
            if (s.charAt(i) != '"') throw new IllegalStateException("falta '\"'");
            i++;
            StringBuilder b = new StringBuilder();
            while (true) {
                char c = s.charAt(i++);
                if (c == '"') return b.toString();
                if (c == '\\') {
                    char e = s.charAt(i++);
                    if (e == 'n') b.append('\n');
                    else if (e == 't') b.append('\t');
                    else if (e == 'u') { b.append((char) Integer.parseInt(s.substring(i, i + 4), 16)); i += 4; }
                    else b.append(e);
                } else b.append(c);
            }
        }

        Double num() {
            int st = i;
            while (i < s.length() && "+-0123456789.eE".indexOf(s.charAt(i)) >= 0) i++;
            if (st == i) throw new IllegalStateException("valor no valido");
            return Double.valueOf(s.substring(st, i));
        }
    }

    // ------------------------------------------------------------------ validacion
    private static double dbl(Object o, double def, double lo, double hi) {
        if (o instanceof Double) {
            double v = ((Double) o).doubleValue();
            if (!Double.isNaN(v) && !Double.isInfinite(v) && v >= lo && v <= hi) return v;
        }
        return def;
    }

    private static boolean bool(Object o, boolean def) { return o instanceof Boolean ? ((Boolean) o).booleanValue() : def; }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object o) { return o instanceof Map ? (Map<String, Object>) o : null; }

    private static OfferAnalyzer.Tier tier(Object o, OfferAnalyzer.Tier def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Tier t = def.copy();
        if (m == null) return t;
        t.base = dbl(m.get("base"), def.base, 0, 100);
        t.perKm = dbl(m.get("km"), def.perKm, 0, 20);
        t.perMin = dbl(m.get("min"), def.perMin, 0, 10);
        t.mult = dbl(m.get("mult"), def.mult, 0.1, 10);
        Object md = m.get("mode");
        t.mode = md instanceof String && "B".equalsIgnoreCase(((String) md).trim()) ? "B" : "A";
        return t;
    }

    private static OfferAnalyzer.Profile profile(Object o, OfferAnalyzer.Profile def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Profile p = def.copy();
        if (m == null) return p;
        p.minFare = dbl(m.get("minFare"), def.minFare, 0, 200);
        p.offerMult = bool(m.get("offerMult"), def.offerMult);
        Object bp = m.get("bp");
        if (bp instanceof List && ((List<?>) bp).size() == 3) {
            List<?> l = (List<?>) bp;
            double a = dbl(l.get(0), -1, 0.01, 1000), b = dbl(l.get(1), -1, 0.01, 1000), c = dbl(l.get(2), -1, 0.01, 1000);
            if (a > 0 && b > a && c > b) p.bp = new double[]{a, b, c};   // si no son crecientes se conservan los de antes
        }
        Object ts = m.get("t");
        if (ts instanceof List) {
            List<?> l = (List<?>) ts;
            for (int i = 0; i < 4 && i < l.size(); i++) p.t[i] = tier(l.get(i), def.t[i]);
        }
        return p;
    }

    /** Lee la configuracion. Cualquier dato ausente o no valido vuelve a su valor inicial; un JSON roto devuelve todo por defecto. */
    public static OfferAnalyzer.BoltCfg parse(String json) {
        OfferAnalyzer.BoltCfg c = new OfferAnalyzer.BoltCfg();
        if (json == null || json.trim().length() == 0) return c;
        try {
            Map<String, Object> m = map(new P(json).val());
            if (m == null) return c;
            c.on = bool(m.get("on"), c.on);
            Object md = m.get("mode");
            if (md instanceof String && ("auto".equals(md) || "week".equals(md) || "weekend".equals(md))) c.mode = (String) md;
            c.comm = dbl(m.get("comm"), c.comm, 0, 90);
            c.wd = profile(m.get("wd"), c.wd);
            c.we = profile(m.get("we"), c.we);
            if (m.get("holidays") instanceof List) {
                List<String> h = new ArrayList<String>();
                for (Object o : (List<?>) m.get("holidays")) {
                    if (o instanceof String) {
                        String x = ((String) o).trim();
                        if (x.matches("\\d{4}-\\d{2}-\\d{2}|\\d{2}-\\d{2}") && !h.contains(x)) h.add(x);
                    }
                }
                c.holidays = h;
            }
            return c;
        } catch (Exception e) {
            return new OfferAnalyzer.BoltCfg();
        }
    }

    // ------------------------------------------------------------------ escritura
    private static String n(double v) { return BigDecimal.valueOf(v).stripTrailingZeros().toPlainString(); }

    private static String prof(OfferAnalyzer.Profile p) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"minFare\":").append(n(p.minFare)).append(",\"offerMult\":").append(p.offerMult);
        b.append(",\"bp\":[").append(n(p.bp[0])).append(',').append(n(p.bp[1])).append(',').append(n(p.bp[2])).append("],\"t\":[");
        for (int i = 0; i < 4; i++) {
            OfferAnalyzer.Tier t = p.t[i];
            if (i > 0) b.append(',');
            b.append("{\"base\":").append(n(t.base)).append(",\"km\":").append(n(t.perKm)).append(",\"min\":").append(n(t.perMin))
             .append(",\"mult\":").append(n(t.mult)).append(",\"mode\":\"").append("B".equals(t.mode) ? "B" : "A").append("\"}");
        }
        return b.append("]}").toString();
    }

    public static String toJson(OfferAnalyzer.BoltCfg c) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"on\":").append(c.on).append(",\"mode\":\"").append(c.mode).append("\",\"comm\":").append(n(c.comm));
        b.append(",\"holidays\":[");
        boolean first = true;
        if (c.holidays != null) for (String h : c.holidays) {
            if (h == null || !h.matches("\\d{4}-\\d{2}-\\d{2}|\\d{2}-\\d{2}")) continue;
            if (!first) b.append(',');
            b.append('"').append(h).append('"');
            first = false;
        }
        b.append("],\"wd\":").append(prof(c.wd)).append(",\"we\":").append(prof(c.we)).append('}');
        return b.toString();
    }

    /** Configuracion inicial (la unica fuente de verdad de los valores por defecto; la pantalla de ajustes la pide aqui). */
    public static String defaultsJson() { return toJson(new OfferAnalyzer.BoltCfg()); }
}
'''
SVC_BLOCK = r'''    // ===================== Bolt: precio estimado, aviso destacado y voz =====================
    private static final Pattern BOLT_PKG = Pattern.compile("mtakso|bolt", Pattern.CASE_INSENSITIVE);
    private String boltJsonCache = null;
    private OfferAnalyzer.BoltCfg boltCfgCache = null;

    /** ajustes de la estimacion de Bolt (se vuelven a leer solo si han cambiado) */
    private OfferAnalyzer.BoltCfg boltCfg() {
        String js = getSharedPreferences("portal", Context.MODE_PRIVATE).getString("bolt_cfg", "");
        if (js == null) js = "";
        if (boltCfgCache == null || !js.equals(boltJsonCache)) { boltCfgCache = BoltConfig.parse(js); boltJsonCache = js; }
        return boltCfgCache;
    }

    // ---- voz (texto a voz del movil) ----
    private TextToSpeech tts = null;
    private boolean ttsReady = false;
    private String ttsPending = null;
    private float ttsVol = 1f;
    private String lastVoice = null;

    private void ensureTts() {
        if (tts != null) return;
        try {
            tts = new TextToSpeech(getApplicationContext(), new TextToSpeech.OnInitListener() {
                @Override public void onInit(int status) {
                    if (status != TextToSpeech.SUCCESS) { ttsReady = false; return; }
                    try {
                        int lr = tts.setLanguage(new Locale("es", "ES"));
                        if (lr == TextToSpeech.LANG_MISSING_DATA || lr == TextToSpeech.LANG_NOT_SUPPORTED) tts.setLanguage(Locale.getDefault());
                        tts.setAudioAttributes(new AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build());
                    } catch (Exception e) { }
                    ttsReady = true;
                    if (ttsPending != null) { String t = ttsPending; ttsPending = null; sayNow(t); }
                }
            });
        } catch (Exception e) { tts = null; }
    }

    private void sayNow(String text) {
        try {
            Bundle b = new Bundle();
            b.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, ttsVol);
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, b, "portal-bolt");
        } catch (Exception e) { }
    }

    /** dice la oferta de Bolt en voz alta (solo Bolt; una vez por oferta; respeta el interruptor y el volumen de Ajustes) */
    private void speakOffer(OfferAnalyzer.Result r) {
        try {
            String t = OfferAnalyzer.voiceText(r);
            if (t == null) return;
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            if (sp.getInt("bolt_voice", 1) != 1) return;
            if (t.equals(lastVoice)) return;
            lastVoice = t;
            ttsVol = Math.max(0.1f, Math.min(1f, sp.getFloat("bolt_vol", 1f)));
            ensureTts();
            if (tts == null) return;
            if (ttsReady) sayNow(t); else ttsPending = t;
        } catch (Exception e) { }
    }

    private void stopSpeech() {
        lastVoice = null;
        ttsPending = null;
        try { if (tts != null && ttsReady) tts.stop(); } catch (Exception e) { }
    }

    private void shutdownTts() {
        try { if (tts != null) { tts.stop(); tts.shutdown(); } } catch (Exception e) { }
        tts = null;
        ttsReady = false;
    }

    // ---- aviso de Bolt con precio estimado: el NETO estimado va grande y destacado ----
    private LinearLayout aNetBox;
    private TextView aNetLbl, aNetVal;

    private void resetEstimateViews() {
        if (aNetBox != null) aNetBox.setVisibility(View.GONE);
        if (aMain != null) aMain.setTextSize(18);
    }

    private static String num1(double v) {
        String s = f(v, 1);
        return s.endsWith(",0") ? s.substring(0, s.length() - 2) : s;
    }

    private static String multTxt(double v) {
        String s = f(v, 2);
        if (s.endsWith("0")) s = s.substring(0, s.length() - 1);
        return s;
    }

    private void showEstimateAlert(OfferAnalyzer.Result r) {
        try {
            if (alertView == null) buildAlert();
            final float d = getResources().getDisplayMetrics().density;
            String v = r.verdict;
            boolean ok = "OK".equals(v), no = "NO".equals(v);
            int col = ok ? Color.parseColor("#22C55E") : (no ? Color.parseColor("#EF4444") : Color.parseColor("#F59E0B"));
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(Color.parseColor("#F00A2E70"));
            bg.setCornerRadius(20 * d);
            bg.setStroke((int) (3 * d), col);
            alertView.setBackground(bg);
            GradientDrawable chip = new GradientDrawable();
            chip.setColor(col);
            chip.setCornerRadius(14 * d);
            aChip.setBackground(chip);
            aChip.setTextColor(ok || no ? Color.WHITE : Color.BLACK);
            aChip.setText(ok ? "✓  ACEPTAR" : (no ? "✕  RECHAZAR" : ("WARN".equals(v) ? "⚠  A VALORAR" : "⚠  DATOS INSUFICIENTES")));
            paintPill(aP1, r.perHour > 0 ? r.stH : -1, f(r.perHour, 1) + " €/h");
            paintPill(aP2, r.perKm > 0 ? r.stK : -1, f(r.perKm, 2) + " €/km");
            paintPill(aP3, r.pickupKm > 0 ? r.stP : -1, "Recog. " + f(r.pickupKm, 1) + " km");
            if (aNetBox == null) {
                aNetBox = new LinearLayout(this);
                aNetBox.setOrientation(LinearLayout.VERTICAL);
                aNetBox.setGravity(Gravity.CENTER_HORIZONTAL);
                aNetLbl = new TextView(this);
                aNetLbl.setTextColor(Color.parseColor("#DCEBFF"));
                aNetLbl.setTextSize(12);
                aNetLbl.setTypeface(Typeface.DEFAULT_BOLD);
                aNetLbl.setGravity(Gravity.CENTER);
                aNetVal = new TextView(this);
                aNetVal.setTextColor(Color.WHITE);
                aNetVal.setTextSize(34);
                aNetVal.setTypeface(Typeface.DEFAULT_BOLD);
                aNetVal.setGravity(Gravity.CENTER);
                aNetBox.addView(aNetLbl);
                aNetBox.addView(aNetVal);
                LinearLayout.LayoutParams nlp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
                nlp.setMargins(0, (int) (8 * d), 0, 0);
                alertView.addView(aNetBox, 2, nlp);
            }
            GradientDrawable nb = new GradientDrawable();
            nb.setColor(Color.parseColor("#33000000"));
            nb.setCornerRadius(14 * d);
            nb.setStroke((int) (2 * d), col);
            aNetBox.setBackground(nb);
            aNetBox.setPadding((int) (10 * d), (int) (4 * d), (int) (10 * d), (int) (6 * d));
            aNetLbl.setText("NETO ESTIMADO");
            aNetVal.setText(OfferAnalyzer.money(r.estNet) + " €");
            aNetBox.setVisibility(View.VISIBLE);
            aMain.setTextSize(15);
            aMain.setText("Bruto est. " + OfferAnalyzer.money(r.estGross) + " €  ·  Comisión est. " + OfferAnalyzer.money(r.estComm) + " € (" + num1(r.estCommPct) + " %)");
            StringBuilder dt = new StringBuilder();
            dt.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)\n");
            String rango = r.estHi < 0 ? ("más de " + num1(r.estLo) + " km") : (r.estLo <= 0 ? ("hasta " + num1(r.estHi) + " km") : (num1(r.estLo) + "–" + num1(r.estHi) + " km"));
            dt.append("Tramo ").append(r.estTier).append(" (").append(rango).append(") · ").append(r.estWeekend ? "fin de semana / festivo" : "lunes a viernes").append("\n");
            dt.append("Demanda ×").append(multTxt(r.estMult)).append(r.estOfferMult > 0 ? " (de la oferta)" : "").append(" · modo ").append(r.estMode).append("\n");
            if (r.estMinApplied) dt.append("Se aplicó la tarifa mínima estimada\n");
            if (r.pickupKm > 0 || r.pickupMin > 0) {
                dt.append("Recogida (no cuenta en el precio): ");
                if (r.pickupMin > 0) dt.append((int) r.pickupMin).append(" min");
                if (r.pickupKm > 0) dt.append(r.pickupMin > 0 ? " (" : "").append(f(r.pickupKm, 1)).append(" km").append(r.pickupMin > 0 ? ")" : "");
                dt.append("\n");
            }
            dt.append(r.reason);
            dt.append("\nPrecio ESTIMADO con tarifas aproximadas (no son las oficiales de Bolt)");
            aDetail.setText(dt.toString());
            if (!alertShown) { wm.addView(alertView, alp); alertShown = true; }
        } catch (Exception e) { }
    }

    /** prueba desde Ajustes: oferta de Bolt de ejemplo (8,3 km, 12 min, x1,4) con TUS tarifas; se ve y se oye */
    public void demoBolt() {
        try {
            List<String> n = new ArrayList<String>();
            for (String s : new String[]{"x1.4", "6 min", "•", "2.1 km", "Calle de ejemplo", "12 min", "•", "8.3 km", "Destino de ejemplo", "Aceptar"}) n.add(s);
            OfferAnalyzer.Result r = OfferAnalyzer.analyze(n, rentParams(), false, true);
            lastVoice = null;
            showAlert(r);
            speakOffer(r);
            rh.removeCallbacks(hideRun);
            rh.postDelayed(hideRun, 9000);
        } catch (Exception e) { }
    }

'''
PLG_BLOCK = r'''    @PluginMethod
    public void getBolt(PluginCall call) {
        android.content.SharedPreferences sp = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE);
        OfferAnalyzer.BoltCfg c = BoltConfig.parse(sp.getString("bolt_cfg", ""));
        JSObject r = new JSObject();
        r.put("cfg", BoltConfig.toJson(c));
        r.put("defaults", BoltConfig.defaultsJson());
        r.put("saved", sp.contains("bolt_cfg"));
        r.put("voice", sp.getInt("bolt_voice", 1) == 1);
        r.put("vol", (double) sp.getFloat("bolt_vol", 1f));
        r.put("weekendNow", OfferAnalyzer.isWeekend(c, java.util.Calendar.getInstance()));
        call.resolve(r);
    }

    @PluginMethod
    public void setBolt(PluginCall call) {
        android.content.SharedPreferences.Editor e = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).edit();
        JSObject r = new JSObject();
        if (call.hasOption("cfg")) {
            String norm = BoltConfig.toJson(BoltConfig.parse(call.getString("cfg", "")));
            e.putString("bolt_cfg", norm);
            r.put("cfg", norm);
        }
        e.putInt("bolt_voice", Boolean.FALSE.equals(call.getBoolean("voice", true)) ? 0 : 1);
        double vol = call.getDouble("vol", 1.0);
        e.putFloat("bolt_vol", (float) Math.max(0.1, Math.min(1.0, vol)));
        e.apply();
        call.resolve(r);
    }

    @PluginMethod
    public void testBolt(PluginCall call) {
        if (ScreenReaderService.instance == null) { call.reject("El lector de pantalla no está activado"); return; }
        ScreenReaderService.instance.demoBolt();
        call.resolve();
    }

'''

BANNER_B64 = """
UklGRuKmAwBXRUJQVlA4INamAwDQFQidASrcBfUBPjEUiEKiISEW6z5sIAMEtDat7d2/FO/B5+Bx+mPo1PIHduEf5vu/SCS3O5C8
a7/Suyh4A3WX0Jv775tfcEGdf2v/kcw3Pu/yHoX/kfObaP5H8TvG7qPYr87fs/81+0X+D/a/5ReLepzzh9t/yP+n/vv/z/3X3m/t
P+//kPyY8XPlP9n/2/87+VPve+s/xn/J/xv+n/93+d////7+23+r/7v+h/2P/m/f////iT+b/3//o/4r99P9D///wE/VP/Vf3f/M
f+T/Mf///7ffv/k//H/afvn85f7V/w//b/t/9j/+fkz/SP8P/4f8z/oP/z/ufqS/4X/s/2n/B///y4/wP+6/+P+p/4P//+gb+v/4
r/x/th//P+f9bH/k/93uXf5//xf/r/o/AV/XP91/7/93+////+d3/9f8L/jf///4fat/ZP+V/9v97/w////1/sb/p3+a/8/+f/23
/+/5f0Af/n20P4B/+fUA/+/pb8wfQ/8e/lP9F/jv2g/u//v9Xfxj59+7f27/J/6L+5//P/a/H7/d/4ny+9Yf8P/E/7T9ifgf+S/f
X8X/ef8//vf7x+532i/qP99/kv9f/3f8t+6/uj+Ufu/+v/xH+i/6f+O/df7CPxr+Xf3f+1f43/bf3f9zfnG+l/4P+f/5v/f/0H//
9pjTf9N/y/85++H7//Qv7AfTP8z/ef8r/0/8N++X0LfLf67/I/vB/nf//83/tf+A/1X+D/0P/O/yn///8H6Bfzz+nf5X+7f5L/p/
3r///+L4q/+n/sP3d9Lz8X/uP+d/kvy4+wP+cf2b/f/4L/Rf+3/Pf///2fjB/Uf9T/Jf6n9rf///8/kx+df5P/n/5D/Uf/P/T///
/7/oV/K/63/sP75/m//N/lv///7/vg/9v5//UD9zf/77sv7X//f8/wqd4TMmrpN28+8BpVAWLz527WOez7B/0j32pjRxlNoeb43u
um/8WVOlNVHKQjA5oULnUbFYoABd+/174cfgDEeF/u2sL5bIEoGVfw3oMrN2JQ96pIDgfLnEB2AciRCfjFikMAOlDFwTvvqMJhpX
sLrqWOARBWiVvWt2ysBU7vrMtZZo1YHLygnuthAHUUk7tTQGD4zE+qvCSg+fE4SFoPHjMDSA2khcUu32lhgzgquCXV3s36MZ9uFs
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
X/D1K+EIy8A4cRBryHxrhc4FvLWw5mt6pL5fGF/fYf5R/9oNF41N+/3tUwXszqDTqVqELFGLBi1Ea1DP3FWrd1hjmKbeoCUoqd9l
m1O4dJWuhBaMTyzDy/0q18mF4d5yu5ZwDayoc3DPQEPRPctlfmuxmYxmZFXulaVDwHsmPFKlDXgyXsWQYGw875NQ7fAzotdJ0Xlq
20iEMPt/wc4bfKXZWK5YBBp9Vw+7iGeCXHrQpQdK8JmLn7qrv0GmlOUYItwSNzTOqfolZ5AJB0631kU0Te2PcRrpqTkAZRq2F6Ta
lVGi7l4iudQc8jhobBTN0Dt1LaQZcMT+t3atSfoC9wom4ktlJjLJDJOHT3PxV1SyU6XqR1E7ieUP8BatsMfhsyy64flaRSt341Gl
Gu32tj3qyRb30Wequd7izaUYP6iZfg02BAqXhyhdxh5bpuE0R/v47eyvJErQdvaa0lI0WpIrC5g/5tgTBBDNMbMPSnArsq8n59h1
6Lo8LJSzhqwkWUdUqtBSq8IwpclTmYIsoTrnk0f2oFQ9jFH5p14pJYIGwS/4o0DJn9Q+G3Kb/e1xkhfbZb1/JkilPatF5eexHhx6
t1TetMNGHVNS+kc6MilV/8mO0E3Pr0P2ItC6fWjQU1+hlgVJFbiuGLWEX04km02D96yRNBQNHTSIPatlcjVvQC9l17CFX7ICGfJe
kINveLKap7Na96Xzp26zDZZQ9aDzaTNDJD5I9HJyj/KOtsYG/Jbxt2duzdyWPy2MR0fOxL7+rM1cGXWBYciOkquarrNX/M2ABWsi
glLnW5hPvEuFK4WMF6YbuMKoGQnjYssJYJFafPSQF/Eq91i2v/x0IEtBHQ5j8LAITu28k+RqKbErPBiEvrcmA+0Wt90dj+psXruy
qZonqns8yNMUVZyKh128eTidZBYoxvqKx4Huk36DNmVZ1x/xeGWgqbeKwITdtLIT6zj0YreLqD/Po4KsQBRtNJKbFXAEhvePk7ph
KDnlOjO8bMrKdrFS2VJcv2CVlkgbeeRFQ3q5d6aidJI2rBp8bEZKWLcT3cs++dUnSfip3iIN9ohfS2zjPSiePxa4tVR0ooXPdvP2
T61+AR93O07i9/k31IgtTw0ebPU4ZNWs5cqaofo5QWiW7NgPSy+oOxtPcrdp1BLrnOVoWp4dU5gIWWAo76ylIUJSako4izFE3tZt
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
CGyFcJgZZNQAAc4QAA==
"""

# ---------------------------------------------------------------- 1) preparar el index.html en memoria (si falta una ancla, se para sin escribir nada)
rep = []
k = s.find('const PDC_SUPABASE_URL')
if k < 0 or s.count('const PDC_SUPABASE_URL') != 1:
    raise SystemExit('ERROR: no encuentro el programa principal (const PDC_SUPABASE_URL). No se ha cambiado nada.')
a = s.rfind('<script', 0, k)                       # inicio del programa principal
if a < 0 or '</script>' in s[a:k]:
    raise SystemExit('ERROR: no encuentro el inicio del programa principal. No se ha cambiado nada.')
e = s.find('</script>', k)
b = s.rfind('</body>')
if e < 0 or b < 0 or b < e:
    raise SystemExit('ERROR: estructura inesperada del index.html. No se ha cambiado nada.')
e += len('</script>')
c = s.find('<script id="', e)                      # primer parche despues del programa principal
if c < 0 or c > b:
    c = b
late = '<script id="v314-script">\n' + bundle('late') + '\n</script>\n<style id="v314-style">\n' + CSS + '\n</style>\n'
early = '<script id="v314-early">\n' + bundle('early') + '\n</script>\n'
pre = '<script id="v314-pre">\n' + bundle('pre') + '\n</script>\n'
n = s[:a] + pre + s[a:c] + early + s[c:b] + late + s[b:]       # de atras hacia delante: las posiciones no se desplazan
n, nv = re.subn(r'v3\.\d+ lector', 'v3.14 lector', n)
rep.append(('modulo-previo-nube', 1)); rep.append(('modulo-temprano', 1)); rep.append(('modulos-principales-y-estilos', 1))
if nv == 0:
    print('(la etiqueta «v3.xx lector» no existe en esta pagina; es solo un detalle visual)')
for mk in ('v314-pre', 'v314-early', 'v314-script', 'v314-style'):
    if n.count('id="' + mk + '"') != 1:
        raise SystemExit('ERROR: marca ' + mk + ' duplicada o ausente. No se ha cambiado nada.')

# ---------------------------------------------------------------- 2) Java (todo o nada) y manifiesto
jr = apply_java(J, MAN, OFFER, BOLTCFG, SVC_BLOCK, PLG_BLOCK)
rep.extend(jr)

# ---------------------------------------------------------------- 3) portada y pagina
img = base64.b64decode(''.join(BANNER_B64.split()))
cur = open('www/header-banner.webp', 'rb').read() if os.path.exists('www/header-banner.webp') else b''
if cur != img:
    open('www/header-banner.webp', 'wb').write(img)
rep.append(('portada-texto-20-por-ciento-mas-grande', 1))
if 'header-banner.webp' not in n:
    print('AVISO: la pagina no usa header-banner.webp; se ha guardado la imagen pero la portada no cambia')
open(p, 'w', encoding='utf-8').write(n)

bad = [l for l, c_ in rep if c_ != 1]
for l, c_ in rep:
    print('%s: %d' % (l, c_))
if bad:
    raise SystemExit('ERROR en: ' + ', '.join(bad))
print('v3.14 aplicado')
