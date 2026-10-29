cd /workspaces/PORTAL_CONDUCTOR && gh run download $(gh run list -L 1 --status success --json databaseId -q '.[0].databaseId') -D apk_v315g && ls -R apk_v315g
# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.15g)

Estimacion del precio de Bolt (cuando la oferta no enseña el precio), version «cuatro tarjetas»:
  - CUATRO tarjetas individuales (Inicial / Por km / Por minuto / Minima): Normal entre semana, Normal fin de semana, Aeropuerto entre semana y
    Aeropuerto fin de semana. Normal: 2,10 / 0,77 / 0,15 / minima 6,75. Aeropuerto: 2,89 / 0,82 / 0,15 / minima 13,50 (recogidas Y viajes hacia el aeropuerto).
  - Una lista de FRANJAS (dia y hora de inicio -> dia y hora de fin; por defecto viernes 18:00 -> domingo 06:00): lo que cae dentro de una franja usa las tarjetas
    de fin de semana, lo demas las de entre semana. Manda la franja que tu eliges, no el dia del calendario. Los festivos cuentan como fin de semana (se puede quitar).
  - Aeropuerto: tasa de 2,57 euros restada del bruto ANTES de la comision; la demanda multiplica todo (la minima tambien); sin ajuste de zona.
  - Zonas buenas DIBUJADAS A MANO en el mapa (poligonos punto a punto: mover, borrar o insertar puntos, borrar la zona). El mapa empieza vacio.
  - Propina visible en la lista de viajes: «38,90 -> 29,25» con «27,25 + 2,00 propina» debajo; el total del dia la cuenta una sola vez y la propina nunca paga comision.
  - Los tramos antiguos desaparecen.
Es un parche UNICO para quien ya tiene la v3.15 (con o sin v315b / c / d / e / f: da igual cuales, esta lo deja todo igual).
Se puede aplicar mas de una vez (la segunda no hace nada). Todo o nada: si falta cualquier ancla NO se cambia nada.
Cambia: www/index.html, OfferAnalyzer.java, BoltConfig.java, ZoneLocator.java, ScreenReaderService.java y ScreenReaderPlugin.java.
"""
import os, re

if not os.path.exists('www/index.html'):
    os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
p = 'www/index.html'
J = 'android/app/src/main/java/com/portal/conductor/'
if not os.path.exists(p):
    raise SystemExit('ERROR: no encuentro www/index.html (ejecuta el parche desde la carpeta portal). No se ha cambiado nada.')
s = open(p, encoding='utf-8').read()
for mk in ('v315-script', 'v315-style'):
    if s.count('id="' + mk + '"') != 1:
        raise SystemExit('ERROR: primero hace falta la v3.15 (falta o esta repetido el bloque ' + mk + '). No se ha cambiado nada.')
for f in ('ScreenReaderService.java', 'ScreenReaderPlugin.java', 'OfferAnalyzer.java', 'BoltConfig.java'):
    if not os.path.exists(J + f):
        raise SystemExit('ERROR: no encuentro ' + J + f + ' (ejecuta el parche desde la carpeta portal). No se ha cambiado nada.')

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
// Aeropuerto y Cancelaciones miden lo mismo que los botones de plataforma (Bolt/Uber/Cabify/Privados): se copia su altura y su separación.
let rowRO=null;
function syncBtnRow(){
  try{
    const row=document.querySelector('.airport-row');if(!row)return;
    const pl=document.querySelector('.platforms .platform');if(!pl)return;
    const h=Math.round(pl.getBoundingClientRect().height*100)/100;
    if(h>=40&&h<=200)row.style.setProperty('--pdc-bh',h+'px');
    const g=parseFloat(getComputedStyle(pl.parentElement).columnGap);
    if(g>=0&&g<=24)row.style.setProperty('--pdc-bg',g+'px');
  }catch(e){}
}
function watchBtnRow(){
  syncBtnRow();
  try{
    if(typeof ResizeObserver==='undefined')return;
    const pl=document.querySelector('.platforms .platform');if(!pl)return;
    if(rowRO)rowRO.disconnect();
    rowRO=new ResizeObserver(()=>syncBtnRow());rowRO.observe(pl);
  }catch(e){}
}
// Etiqueta «Comisión 25 % · 2,57 €» del botón de aeropuerto: se busca por su TEXTO (no por su clase) y se le pone una marca para
// reducirla un 30 % y fijarla en la esquina de abajo a la derecha, sin tapar la palabra «Aeropuerto».
function fixFeeChip(ap){
  try{
    if(!ap)return;
    const norm=s=>String(s||'').replace(/\s+/g,' ').trim();
    const isChip=el=>{const x=norm(el.textContent);return x.length>0&&x.length<=40&&/^comisi[oó]n/i.test(x)&&x.indexOf('%')>=0&&x.indexOf('€')>=0&&!/aeropuerto|ida y/i.test(x)};
    let top=null;
    for(const el of ap.querySelectorAll('*')){
      if(top&&top.contains(el))continue;
      if(el.classList.contains('airport-copy')||el.classList.contains('airport-plane'))continue;
      if(isChip(el)){top=el;if(!el.classList.contains('pdc-fee-chip'))el.classList.add('pdc-fee-chip')}
    }
    if(top&&!ap.classList.contains('pdc-has-chip'))ap.classList.add('pdc-has-chip');
    if(!ap.__pdcChipMO&&typeof MutationObserver!=='undefined'){
      ap.__pdcChipMO=new MutationObserver(()=>fixFeeChip(ap));
      ap.__pdcChipMO.observe(ap,{childList:true,subtree:true,characterData:true});
    }
  }catch(e){}
}
P.fixFeeChip=fixFeeChip;
window.addEventListener('resize',syncBtnRow);
window.addEventListener('orientationchange',()=>setTimeout(syncBtnRow,200));
// Los cuatro cuadros por plataforma de la CALCULADORA son los totales del día. Los del Informe general (#reportOut) llevan la SUMA DEL PERIODO que
// pide el usuario (semana, mes o fechas) y no se tocan: antes se pisaban con los importes de hoy y se colaba un «Resumen del día».
function calcPS(root){
  try{for(const ps of root.querySelectorAll('.platform-summary')){if(!ps.closest('#reportOut'))return ps}}catch(e){}
  return null;
}
function decorateCalc(){
  const root=document.getElementById('content');if(!root)return;
  const k=(typeof calcAnchor!=='undefined'&&calcAnchor)?calcAnchor:today();
  // 1) botón junto a Aeropuerto
  const ap=root.querySelector('.airport-premium');
  if(ap)fixFeeChip(ap);
  if(ap&&!root.querySelector('.airport-row')){
    const row=document.createElement('div');row.className='airport-row';
    ap.parentNode.insertBefore(row,ap);row.appendChild(ap);
    const b=document.createElement('button');b.type='button';b.className='cancel-btn';b.setAttribute('aria-label','Añadir cancelación');
    b.innerHTML='<span class="cancel-ico" aria-hidden="true">✕</span><span class="cancel-txt">Cancelaciones</span>';
    b.onclick=()=>window.cancelOpen();
    row.appendChild(b);
  }
  watchBtnRow();
  // 2) totales por plataforma (con las compensaciones de cada una)
  const ps=calcPS(root);
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
// La primera pantalla la dibuja la app ANTES de que este módulo exista (el botón Cancelaciones no salía hasta cambiar de pestaña y volver):
// se decora ahora, y si algún otro módulo añade el botón de aeropuerto o los totales más tarde, también se decora entonces.
function calcNeeds(root){
  if(!root)return false;
  if(root.querySelector('.airport-premium')&&!root.querySelector('.airport-row'))return true;
  if(calcPS(root)&&!root.querySelector('.canc-sum'))return true;
  return false;
}
try{if(calcNeeds(document.getElementById('content')))decorateCalc()}catch(e){console.warn('v3.15 calc inicial',e)}
(function(){
  const root=document.getElementById('content');if(!root||!window.MutationObserver)return;
  let busy=false;
  new MutationObserver(()=>{
    if(busy||!calcNeeds(root))return;busy=true;
    Promise.resolve().then(()=>{busy=false;try{if(calcNeeds(root))decorateCalc()}catch(e){console.warn('v3.15 calc',e)}});
  }).observe(root,{childList:true,subtree:true});
})();

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
   Los meses ya cerrados con el cálculo anterior se conservan tal cual (con un botón para recalcularlos con el nuevo).
   v3.15 · PROPINAS, tres formas (cada conductor elige en Ajustes → Nómina):
     · «apart» (la de siempre): 100 % del conductor, fuera de la nómina y sin comisión.
     · «all»:   se suman a la facturación del mes y se tratan como ella (comisión, nómina bruta e IRPF).
     · «pct»:   entran en la nómina pero solo se les resta el % que se indique (p. ej. contingencias comunes): sin IRPF y sin comisión. */
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
  const tipMode=i.tipMode==='all'||i.tipMode==='pct'?i.tipMode:'apart', tipPct=clampPct(i.tipPct);
  const tipsBilling=tipMode==='all'?tips:0;                          // «todo en nómina»: las propinas se suman a la facturación
  const basis=c2(vehicle+manual+tipsBilling);                       // facturación sobre la que se calcula el %
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
  const tipsWithheld=tipMode==='pct'?c2(tips*tipPct/100):0;                  // «con retención»: solo se resta este %, sin IRPF
  const tipsNet=tipMode==='apart'?tips:(tipMode==='pct'?c2(tips-tipsWithheld):0);   // lo que se suma aparte al total final («todo en nómina» ya va dentro)
  return {model:2,profile,rule,pct,minimum,base,irpfPct,fixedVia,underBase,
    vehicle,manual,basis,reached,excess,variable,total,remuneration,
    gross,tax,net,cashCommission:cashComm,fixedExtra:profile==='variableFixedCash'?fixed:0,fixedPayroll,fixedCash,cash,
    shortfall,lifted,tips,tipMode,tipPct,tipsBilling,tipsWithheld,tipsNet,final,finalWithTips:c2(final+tipsNet)};
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
    fixedVia:cfg.fixedExtraVia,underBase:cfg.underBase,irpf:cfg.irpf,vehicle:Math.max(0,nm(x.total)-nm(x.tips)),manual,tips:nm(x.tips),tipMode:cfg.tipMode,tipPct:cfg.tipPct});
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
  // propinas: los meses guardados antes de existir esta opción siguen con «aparte» (así se veían); el resto usa lo elegido en Ajustes
  const tm=snap?snap.tipMode:db.settings.tipMode;
  out.tipMode=tm==='all'||tm==='pct'?tm:'apart';
  out.tipPct=clampPct(snap?snap.tipPct:db.settings.tipPct);
  return out;
};

/* ---------- migración: lo ya guardado se respeta ---------- */
function globalsCfg(){
  const s=db.settings;
  return {payrollProfile:s.payrollProfile||'variableFixedCash',commission:s.commission,commissionMode:s.commissionMode,commissionMinimum:s.commissionMinimum,
    salaryBase:Number(s.salaryBase??1425),cashPayroll:Number(s.cashPayroll??2000),irpf:Number(s.irpf??14.5),
    fixedExtraVia:s.fixedExtraVia==='payroll'?'payroll':'cash',underBase:s.underBase==='total'?'total':'base',
    tipMode:s.tipMode==='all'||s.tipMode==='pct'?s.tipMode:'apart',tipPct:clampPct(s.tipPct)};
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
  if(r.tipsBilling>0)h+=row('Propinas sumadas a la facturación (como el resto)','+ '+euro(r.tipsBilling));
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
  if(r.tips>0){
    if(r.tipMode==='all')h+='<div class="note pr-tipsnote">🎁 Las propinas ('+esc(euro(r.tips))+') van dentro de la facturación y de la nómina: pagan comisión y llevan IRPF como todo lo demás.</div>';
    else if(r.tipMode==='pct')h+=row('Propinas en nómina (solo retención del '+pc(r.tipPct)+' %, sin IRPF)','+ '+euro(r.tips),'pr-tips')+row('Retención sobre las propinas ('+pc(r.tipPct)+' %)','− '+euro(r.tipsWithheld),'pr-tips')+row('Total con propinas',euro(r.finalWithTips),'pr-tips');
    else h+=row('Propinas (100 % tuyas, aparte del cálculo)','+ '+euro(r.tips),'pr-tips')+row('Total con propinas',euro(r.finalWithTips),'pr-tips');
  }
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
  // propinas: tres formas (la elige cada conductor)
  const pcn=$('payrollCompensation'),pcNote=pcn&&pcn.nextElementSibling;
  const tipHtml='<label id="tipModeLabel">Propinas</label><select id="tipMode" style="margin:6px 0 10px" oninput="previewPayrollSettings()" onchange="previewPayrollSettings()">'
    +'<option value="apart"'+(s.tipMode!=='all'&&s.tipMode!=='pct'?' selected':'')+'>Aparte (100 % para mí, fuera de la nómina)</option>'
    +'<option value="all"'+(s.tipMode==='all'?' selected':'')+'>Todo en nómina (se suman a la facturación)</option>'
    +'<option value="pct"'+(s.tipMode==='pct'?' selected':'')+'>En nómina, solo con una retención (%)</option></select>'
    +'<div class="note" id="tipModeNote" style="margin-bottom:10px"><b>Aparte:</b> son 100 % tuyas, no pagan comisión y no entran en la nómina. <b>Todo en nómina:</b> se suman a la facturación del mes y reciben el mismo trato (comisión, nómina bruta e IRPF). <b>Con retención:</b> entran en la nómina, pero solo se les resta el % que pongas debajo (por ejemplo, contingencias comunes), sin IRPF y sin comisión. Los meses ya cerrados no cambian.</div>'
    +'<label id="tipPctLabel">Retención sobre las propinas (%)</label><input id="tipPct" type="number" inputmode="decimal" step="0.01" min="0" max="100" value="'+esc(s.tipPct==null?0:s.tipPct)+'" oninput="previewPayrollSettings()" onchange="previewPayrollSettings()">'
    +'<div class="note" id="tipPctNote" style="margin-bottom:10px">Solo para «En nómina, solo con una retención». Es el % que se descuenta de las propinas (sin IRPF y sin comisión).</div>';
  (pcNote&&pcNote.classList.contains('note')?pcNote:pcn).insertAdjacentHTML('afterend',tipHtml);
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
    irpf:!weekly,payrollCompensation:!weekly,
    tipMode:!weekly,tipPct:!weekly&&(($('tipMode')||{}).value==='pct')
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
    fixedExtraVia:($('fixedVia')||{}).value||s.fixedExtraVia,underBase:($('underBase')||{}).value||s.underBase,
    tipMode:($('tipMode')||{}).value||s.tipMode,tipPct:readNum('tipPct',s.tipPct),model:2,manualComp:Math.max(0,readNum('payrollCompensation',payrollCompensationForMonth(monthKeyFromOffset(0))))};
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
  const via=($('fixedVia')||{}).value,ub=($('underBase')||{}).value,tm=($('tipMode')||{}).value,tp=readNum('tipPct',null);
  const r=_ss.apply(this,arguments);
  try{
    const s=db.settings;
    if(via)s.fixedExtraVia=via==='payroll'?'payroll':'cash';
    if(ub)s.underBase=ub==='total'?'total':'base';
    s.commission=clampPct(s.commission);
    if(tm)s.tipMode=tm==='all'||tm==='pct'?tm:'apart';
    if(tp!=null)s.tipPct=clampPct(tp);
    const snap=s.payrollByMonth&&s.payrollByMonth[monthKeyFromOffset(0)];
    if(snap){snap.model=2;snap.fixedExtraVia=s.fixedExtraVia;snap.underBase=s.underBase;snap.commission=s.commission;snap.tipMode=s.tipMode==='all'||s.tipMode==='pct'?s.tipMode:'apart';snap.tipPct=clampPct(s.tipPct)}
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
    ('60_bolt.js', r'''/* ===================== v3.15g · ESTIMACIÓN DEL PRECIO DE BOLT (pantalla de ajustes) =====================
   Cuando la oferta de Bolt no muestra el precio, el lector (Java) lo estima por los km y los minutos del viaje con pasajero.
   Hay CUATRO tarjetas de precios, cada una con su propio inicial, precio por km, precio por minuto y mínima: la tarjeta NORMAL y la del AEROPUERTO
   (recogidas y viajes hacia el aeropuerto), cada una para ENTRE SEMANA y para FIN DE SEMANA. Qué tarjeta se usa lo deciden las FRANJAS de fin de semana
   que tú defines (por defecto de viernes 18:00 a domingo 06:00, y los festivos cuentan como fin de semana), no el día del calendario.
   Aeropuerto: la demanda multiplica todo (mínima incluida), no lleva ajuste de zona y se resta la tasa antes de la comisión.
   Viajes normales: ajuste por ZONA y por DEMANDA con el GPS (fuera de zona buena: sin demanda o menos de ×1,2 → −8 %; de ×1,2 a ×1,4 → tarifa real;
   desde ×1,4 → tarifa × demanda, con +5/+8/+10 % desde ×1,5/×2/×2,5; en zona buena: tarifa +12 % × la demanda tal como salga).
   Las zonas buenas son polígonos que dibujas tú en un mapa. Son estimaciones del conductor (no tarifas oficiales de Bolt). Los valores iniciales y el cálculo
   son los mismos que usa el código nativo (se comprueba en las pruebas contra Java). */
(function(){
const P=window.PDC314;if(!P||P.bolt)return;P.bolt=true;
const SR=()=>{try{if(window.Capacitor&&Capacitor.isNativePlatform&&Capacitor.isNativePlatform())return (Capacitor.Plugins&&Capacitor.Plugins.ScreenReader)||Capacitor.registerPlugin('ScreenReader')}catch(e){}return null};
const LSK='pdc_bolt';
const MAXZ=40,MAXPT=200,MAXS=20,WEEK=10080;
const CARD=(b,k,m,f)=>({base:b,km:k,min:m,minFare:f});
const SLOTS=()=>[{on:true,from:4*1440+18*60,to:6*1440+6*60}];          // viernes 18:00 → domingo 06:00
const ZONE=()=>({on:true,adj:-8,adjGood:12,mult:1,realFrom:1.2,from:1.4,a1:1.5,p1:5,a2:2,p2:8,a3:2.5,p3:10,zones:[]});
const defaults=()=>({on:true,mode:'auto',comm:25,offerMult:true,airOn:true,airFee:2.57,holidaysWe:true,
  holidays:['01-01','01-06','05-01','05-02','08-15','10-12','11-01','12-06','12-08','12-25'],
  slots:SLOTS(),
  cards:{nwd:CARD(2.1,0.77,0.15,6.75),nwe:CARD(2.1,0.77,0.15,6.75),awd:CARD(2.89,0.82,0.15,13.5),awe:CARD(2.89,0.82,0.15,13.5)},
  zone:ZONE()});
P.boltDefaults=defaults;
const clone=o=>JSON.parse(JSON.stringify(o));
const isN=v=>typeof v==='number'&&Number.isFinite(v);
const isObj=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
const rng=(v,d,lo,hi)=>isN(v)&&v>=lo&&v<=hi?v:d;
/* misma validación que el código nativo: lo no válido vuelve a su valor inicial */
function normCard(o,d){const c=clone(d);if(!isObj(o))return c;c.base=rng(o.base,d.base,0,100);c.km=rng(o.km,d.km,0,20);c.min=rng(o.min,d.min,0,10);c.minFare=rng(o.minFare,d.minFare,0,200);return c}
const areaName=v=>{if(typeof v!=='string')return '';let s=v.replace(/[\u0000-\u001F\u007F]/g,' ').replace(/^ +| +$/g,'');if(s.length>40)s=s.slice(0,40).replace(/^ +| +$/g,'');return s};
function normZone(o,d){const z=clone(d);if(!isObj(o))return z;
  z.on=typeof o.on==='boolean'?o.on:d.on;
  z.adj=rng(o.adj,d.adj,-90,300);z.adjGood=rng(o.adjGood,d.adjGood,-90,300);z.mult=rng(o.mult,d.mult,0.1,10);
  const rf=rng(o.realFrom,d.realFrom,1,10),df=rng(o.from,d.from,1,10),a1=rng(o.a1,d.a1,1,10),a2=rng(o.a2,d.a2,1,10),a3=rng(o.a3,d.a3,1,10);
  if(rf<=df&&df<=a1&&a1<=a2&&a2<=a3){z.realFrom=rf;z.from=df;z.a1=a1;z.a2=a2;z.a3=a3}else{z.realFrom=d.realFrom;z.from=d.from;z.a1=d.a1;z.a2=d.a2;z.a3=d.a3}
  z.p1=rng(o.p1,d.p1,0,100);z.p2=rng(o.p2,d.p2,0,100);z.p3=rng(o.p3,d.p3,0,100);
  // zonas buenas: polígonos [latitud, longitud]. Los ajustes de la v3.15f traían círculos en «good»: se ignoran (el mapa empieza vacío)
  if(Array.isArray(o.zones)){
    const l=[];for(const a of o.zones){if(!isObj(a)||l.length>=MAXZ||!Array.isArray(a.pts))continue;
      const pts=[];for(const p of a.pts){if(!Array.isArray(p)||p.length!==2||pts.length>=MAXPT)continue;
        const lat=rng(p[0],999,-90,90),lon=rng(p[1],999,-180,180);if(lat===999||lon===999)continue;pts.push([lat,lon])}
      if(pts.length>=3)l.push({n:areaName(a.n),pts})}
    z.zones=l}
  return z}
function normSlots(o,d){if(!Array.isArray(o))return d;const l=[];
  for(const x of o){if(!isObj(x)||l.length>=MAXS)continue;const f=rng(x.from,-1,0,WEEK-1),t=rng(x.to,-1,0,WEEK-1);
    if(f<0||t<0||!Number.isInteger(f)||!Number.isInteger(t)||f===t)continue;l.push({on:typeof x.on==='boolean'?x.on:true,from:f,to:t})}
  return l}
function norm(o){const d=defaults(),c=d;if(!isObj(o))return c;
  if(typeof o.on==='boolean')c.on=o.on;if(['auto','week','weekend'].includes(o.mode))c.mode=o.mode;c.comm=rng(o.comm,c.comm,0,90);
  // wd / zone.base…: ajustes de la v3.15 y de la v3.15f (de ahí se aprovechan algunos valores)
  const zm=isObj(o.zone)?o.zone:null,wdm=isObj(o.wd)?o.wd:null,airm=wdm&&isObj(wdm.air)?wdm.air:null;
  let om=o.offerMult;if(typeof om!=='boolean'&&wdm)om=wdm.offerMult;c.offerMult=typeof om==='boolean'?om:c.offerMult;
  let ao=o.airOn;if(typeof ao!=='boolean'&&airm)ao=airm.on;c.airOn=typeof ao==='boolean'?ao:c.airOn;
  let af=o.airFee;if(typeof af!=='number'&&airm)af=airm.fee;c.airFee=rng(af,c.airFee,0,50);
  c.holidaysWe=typeof o.holidaysWe==='boolean'?o.holidaysWe:c.holidaysWe;
  if(Array.isArray(o.holidays)){const h=[];for(const x of o.holidays)if(typeof x==='string'){const y=x.trim();if(/^(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})$/.test(y)&&!h.includes(y))h.push(y)}c.holidays=h}
  c.slots=normSlots(o.slots,c.slots);
  const cm=isObj(o.cards)?o.cards:null;
  if(cm){c.cards.nwd=normCard(cm.nwd,c.cards.nwd);c.cards.nwe=normCard(cm.nwe,c.cards.nwe);c.cards.awd=normCard(cm.awd,c.cards.awd);c.cards.awe=normCard(cm.awe,c.cards.awe)}
  else if(zm){c.cards.nwd=normCard(zm,c.cards.nwd);c.cards.nwe=clone(c.cards.nwd)}      // la v3.15f tenía una sola tarjeta normal para todos los días
  c.zone=normZone(o.zone,d.zone);
  return c}
P.boltNorm=norm;

/* ---------- el mismo cálculo que el aviso (sin redondeos intermedios) ---------- */
/* ajuste (%) y demanda realmente aplicada (igual que Zone.adjust / Zone.demand de Java) */
const zAdjust=(z,m,good)=>good?z.adjGood:(m<z.realFrom?z.adj:0);
const zDemand=(z,m,good)=>{if(good)return m;if(m<z.from)return 1;const extra=m>=z.a3?z.p3:(m>=z.a2?z.p2:(m>=z.a1?z.p1:0));return m*(1+extra/100)};
function estimate(c,weekend,km,min,offerMult,airKind,good){
  const air=!!c.airOn&&(airKind==='pickup'||airKind==='dest'),ak=air?airKind:'';
  const card=air?(weekend?c.cards.awe:c.cards.awd):(weekend?c.cards.nwe:c.cards.nwd);
  const fromOffer=!!c.offerMult&&offerMult>0;
  let raw=card.base+km*card.km+min*card.min,ma=false;
  if(card.minFare>0&&raw<card.minFare){raw=card.minFare;ma=true}
  const z=c.zone;good=!!good;
  const m=Math.max(0.1,Math.min(10,fromOffer?offerMult:z.mult));
  let gross,mult,lo=0,hi=0,mode='',zone=0,eadj=0,eeff=m;
  if(!air&&z.on){
    const adj=zAdjust(z,m,good),eff=zDemand(z,m,good);
    mult=(eff>1+1e-9||good)?m:1;
    gross=raw*(1+adj/100)*eff;
    lo=z.realFrom;hi=z.from;mode='Z';zone=good?2:1;eadj=adj;eeff=eff;
  }else{mult=m;gross=raw*m}
  const pct=Math.max(0,Math.min(90,c.comm)),fee=air?c.airFee:0,after=fee>0?Math.max(0,gross-fee):gross,comm=after*pct/100;
  return {gross,comm,net:after-comm,fee,airport:ak,mult,tier:0,mode,lo,hi,minApplied:ma,weekend,fromOffer,zone,adj:eadj,eff:eeff};
}
P.boltEstimate=estimate;
function distKm(lat1,lon1,lat2,lon2){const rad=Math.PI/180,dLat=(lat2-lat1)*rad,dLon=(lon2-lon1)*rad;const a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(lat1*rad)*Math.cos(lat2*rad)*Math.sin(dLon/2)*Math.sin(dLon/2);return 6371*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a))}
/* punto dentro de un polígono [[lat,lon],…] (regla par-impar; igual que Area.contains de Java) */
function inPoly(pts,lat,lon){let inside=false;for(let i=0,j=pts.length-1;i<pts.length;j=i++){const yi=pts[i][0],xi=pts[i][1],yj=pts[j][0],xj=pts[j][1];if(((yi>lat)!==(yj>lat))&&(lon<(xj-xi)*(lat-yi)/(yj-yi)+xi))inside=!inside}return inside}
function goodAreaAt(z,lat,lon){if(!z||!Array.isArray(z.zones))return null;for(const a of z.zones)if(a&&inPoly(a.pts,lat,lon))return a.n;return null}
P.boltDist=distKm;P.boltZoneAt=goodAreaAt;P.boltInPoly=inPoly;
/* aeropuerto: se detecta por el texto de la oferta (igual que el código nativo) */
const nrm=s=>String(s==null?'':s).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
const AIR_PICK=/\b(t\s?[1-4]|p\s?1|express|modulo\s?d|terminal|aeropuerto|barajas)\b/,AIR_DEST=/terminal\s?[1-4]|aeropuerto|barajas|hispanidad/;
function detectAirport(nodes){
  let pick=false,dest=false;if(!Array.isArray(nodes))return '';
  for(const raw of nodes){if(raw==null||String(raw).length>120)continue;const n=nrm(raw);
    if(n.includes('parking')&&AIR_PICK.test(n))pick=true;else if(AIR_DEST.test(n))dest=true}
  return pick?'pickup':dest?'dest':'';
}
P.boltAirport=detectAirport;
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
  return 'Bolt. '+(e.airport==='pickup'?'Recogida en el aeropuerto. ':e.airport==='dest'?'Hacia el aeropuerto. ':'')+'Viaje de '+k+(k==='1'?' kilómetro y ':' kilómetros y ')+m+(m===1?' minuto':' minutos')+(e.zone===2?', zona buena':'')+(e.weekend?', tarifa de fin de semana':'')+(Math.abs(e.mult-1)>1e-9?', demanda por '+spoken(e.mult,2):'')+
    '. Bruto estimado: '+money(e.gross)+' euros. '+(e.fee>0?'Tasa del aeropuerto: '+money(e.fee)+' euros. ':'')+'Comisión estimada: '+money(e.comm)+' euros. Neto estimado: '+money(e.net)+' euros.';
}
P.boltVoice=voiceText;
/* franjas de fin de semana: minutos desde el lunes 00:00; si «to» es menor que «from» da la vuelta al domingo (igual que Slot.contains de Java) */
const inSlot=(s,w)=>s.from<s.to?(w>=s.from&&w<s.to):(w>=s.from||w<s.to);
function isHoliday(c,d){
  const p2=n=>String(n).padStart(2,'0'),md=p2(d.getMonth()+1)+'-'+p2(d.getDate()),full=d.getFullYear()+'-'+md;
  return (c.holidays||[]).some(h=>h===full||h===md);
}
const weekMinute=d=>((d.getDay()+6)%7)*1440+d.getHours()*60+d.getMinutes();
function isWeekend(c,d){
  if(c.mode==='week')return false;if(c.mode==='weekend')return true;
  if(c.holidaysWe&&isHoliday(c,d))return true;
  const w=weekMinute(d);
  return (c.slots||[]).some(s=>s&&s.on&&inSlot(s,w));
}
P.boltIsWeekend=isWeekend;

/* ---------- estado y guardado permanente ---------- */
const B={cfg:defaults(),voice:true,vol:1,weekendNow:false,open:false,sim:{km:8.3,min:10,mult:'',prof:'auto',kind:'',zone:'0'},native:false,loaded:false,zoneLast:'',holOpen:null,base:'',slotEdit:null};
const snap=()=>JSON.stringify(B.cfg)+'|'+B.voice+'|'+B.vol;B.base=snap();
P.boltState=B;
function mirrorToDb(cfgJson){
  try{db.settings.boltCfg=cfgJson;db.settings.boltVoice=B.voice;db.settings.boltVol=B.vol}catch(e){}
}
async function load(guard){
  const sr=SR();B.native=!!sr;let d=null;
  if(sr){try{d=await sr.getBolt()}catch(e){d=null}}
  if(guard&&snap()!==B.base)return false;
  if(d&&d.cfg){
    try{B.cfg=norm(JSON.parse(d.cfg))}catch(e){B.cfg=defaults()}
    B.voice=d.voice!==false;B.vol=isN(d.vol)?d.vol:1;B.weekendNow=!!d.weekendNow;B.saved=!!d.saved;B.zoneLast=typeof d.zoneLast==='string'?d.zoneLast:'';
    // el teléfono perdió sus ajustes (reinstalación…) pero la copia de la cuenta los tiene
    if(!d.saved&&db&&db.settings&&db.settings.boltCfg){
      try{
        const r=await sr.setBolt({cfg:db.settings.boltCfg,voice:db.settings.boltVoice!==false,vol:isN(db.settings.boltVol)?db.settings.boltVol:1});
        if(guard&&snap()!==B.base)return false;
        B.cfg=norm(JSON.parse((r&&r.cfg)||db.settings.boltCfg));B.voice=db.settings.boltVoice!==false;B.vol=isN(db.settings.boltVol)?db.settings.boltVol:1;B.saved=true;
      }catch(e){}
    }
  }else{
    let o=null;try{o=JSON.parse(localStorage.getItem(LSK)||'null')}catch(e){}
    if(!o&&db&&db.settings&&db.settings.boltCfg){try{o={cfg:JSON.parse(db.settings.boltCfg),voice:db.settings.boltVoice,vol:db.settings.boltVol}}catch(e){}}
    if(o){B.cfg=norm(o.cfg);B.voice=o.voice!==false;B.vol=isN(o.vol)?o.vol:1}
    B.weekendNow=isWeekend(B.cfg,new Date());
  }
  B.loaded=true;B.base=snap();return true;
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
  B.cfg=back;B.base=snap();
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
const LIMC={base:[0,100],km:[0,20],min:[0,10],minFare:[0,200]};
const LIMZ={adj:[-90,300],adjGood:[-90,300],mult:[0.1,10],realFrom:[1,10],from:[1,10],a1:[1,10],a2:[1,10],a3:[1,10],p1:[0,100],p2:[0,100],p3:[0,100]};
const ZORD=['realFrom','from','a1','a2','a3'];
const DAYS=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'],DAYS3=['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];
const p2=n=>String(n).padStart(2,'0');
const hhmm=w=>p2(Math.floor((w%1440)/60))+':'+p2(w%60);
const slotTxt=s=>DAYS[Math.floor(s.from/1440)]+' '+hhmm(s.from)+' → '+DAYS[Math.floor(s.to/1440)]+' '+hhmm(s.to);
const cell=(lab,id,val,path,opts)=>{opts=opts||{};return '<label class="bz-f"><span>'+lab+'</span><input id="'+id+'" type="number" inputmode="decimal" step="'+(opts.step||'0.01')+'" min="'+(opts.min!=null?opts.min:0)+'" value="'+esc(val)+'"'+(opts.on?' oninput="'+opts.on+'"':' data-p="'+path+'" oninput="boltIn(this)"')+(opts.dis?' disabled':'')+'></label>'};
const chk=(lab,id,path,on,extra)=>'<label class="bz-f bz-chk'+(extra||'')+'"><input type="checkbox" id="'+id+'" data-p="'+path+'"'+(on?' checked':'')+' onchange="boltIn(this)"><span>'+lab+'</span></label>';

/* ---------- las cuatro tarjetas ---------- */
const CARDS=[
  ['nwd','Tarjeta normal','Entre semana','Todos los viajes menos el aeropuerto',0],
  ['nwe','Tarjeta normal','Fin de semana','Todos los viajes menos el aeropuerto',0],
  ['awd','Tarjeta del aeropuerto','Entre semana','Recogidas y viajes hacia el aeropuerto',1],
  ['awe','Tarjeta del aeropuerto','Fin de semana','Recogidas y viajes hacia el aeropuerto',1]];
function cardHtml(k,title,day,sub,air){
  const c=B.cfg.cards[k],id=x=>'bz_c_'+k+'_'+x,p='cards.'+k+'.',we=k.charAt(2)==='e';
  return '<div class="bz-t bz-card'+(air?' bz-air':'')+'" id="bz_card_'+k+'"><div class="bz-th"><b>'+title+'</b><span class="bz-day '+(we?'we':'wd')+'">'+day+'</span></div><small class="bz-cs">'+sub+'</small>'
   +'<div class="bz-g">'+cell('Inicial (€)',id('base'),show(c.base),p+'base')+cell('Por km (€)',id('km'),show(c.km),p+'km')
   +cell('Por minuto (€)',id('min'),show(c.min),p+'min')+cell('Mínima (€)',id('minFare'),show(c.minFare),p+'minFare')+'</div></div>';
}
function cardsHtml(){
  const c=B.cfg;
  return '<div class="bz-sec" id="bz_cards"><b>💳 Tarjetas de precios</b><small>Cada tarjeta tiene sus 4 precios. La app usa la de <b>fin de semana</b> cuando la hora cae dentro de una de tus franjas (o es festivo) y la de <b>entre semana</b> el resto del tiempo.</small>'
   +CARDS.filter(x=>!x[4]).map(x=>cardHtml.apply(null,x)).join('')
   +'<div class="bz-sub-air"><b>✈ Aeropuerto</b></div>'
   +chk('Usar la tarjeta del aeropuerto (recogidas y viajes hacia el aeropuerto) y restar la tasa','bz_airOn','airOn',c.airOn)
   +'<div class="bz-g">'+cell('Tasa del aeropuerto (€)','bz_airFee',show(c.airFee),'airFee')+'<div></div></div>'
   +CARDS.filter(x=>x[4]).map(x=>cardHtml.apply(null,x)).join('')
   +'<div class="bz-hint">En el <b>aeropuerto</b> (una recogida en «parking P1 de la T1», «parking express T2» o «parking módulo D … T4», o un viaje hacia «Terminal 1–4», «Aeropuerto» o «Avenida de la Hispanidad») se usa la tarjeta del aeropuerto: <b>inicial + km × precio + minutos × precio</b>, pero nunca menos que la mínima. La <b>demanda multiplica todo</b> (la mínima también) y <b>no hay ajuste de zona</b>. Después se resta la tasa del bruto <b>antes</b> de la comisión de Bolt. '
   +'Si no se detecta el aeropuerto, o desmarcas la casilla, se usa la tarjeta normal.</div>'
   +'<div class="bz-btns"><button type="button" class="secondary" id="bz_cards_def" onclick="boltReset(\'cards\')">↺ Valores iniciales de las tarjetas</button></div></div>';
}

/* ---------- franjas de fin de semana ---------- */
function barSegs(d){        // tramos (en % del día) de las franjas activas que caen en el día d (0 = lunes)
  const out=[],a=d*1440,b=a+1440,add=(x,y)=>{const s=Math.max(x,a),e=Math.min(y,b);if(e>s)out.push([(s-a)/1440*100,(e-s)/1440*100])};
  for(const s of B.cfg.slots){if(!s.on)continue;if(s.from<s.to)add(s.from,s.to);else{add(s.from,WEEK);add(0,s.to)}}
  return out;
}
function weekBarHtml(){
  let h='<div class="bz-wk" id="bz_wk"><div class="bz-wh"><span></span><span>0 h</span><span>6 h</span><span>12 h</span><span>18 h</span><span>24 h</span></div>';
  for(let d=0;d<7;d++)h+='<div class="bz-wr"><span class="bz-wd">'+DAYS3[d]+'</span><div class="bz-wb" id="bz_wk'+d+'">'+barSegs(d).map(s=>'<i style="left:'+s[0].toFixed(2)+'%;width:'+s[1].toFixed(2)+'%"></i>').join('')+'</div></div>';
  return h+'<div class="bz-wl"><span><i class="we"></i>Fin de semana</span><span><i class="wd"></i>Entre semana</span></div></div>';
}
function slotRowHtml(s,i){
  return '<div class="bz-sl" id="bz_sl_'+i+'"><label class="bz-sw"><input type="checkbox" id="bz_sl_'+i+'_on" '+(s.on?'checked ':'')+'onchange="boltSlotOn('+i+',this)" aria-label="Franja activada"></label>'
   +'<span class="bz-st" id="bz_sl_'+i+'_t">'+esc(slotTxt(s))+'</span>'
   +'<button type="button" class="secondary" id="bz_sl_'+i+'_ed" onclick="boltSlotEdit('+i+')" aria-label="Cambiar la franja">✏️</button>'
   +'<button type="button" class="secondary" id="bz_sl_'+i+'_del" onclick="boltSlotDel('+i+')" aria-label="Borrar la franja">🗑</button></div>';
}
function dayOpts(sel){return DAYS.map((n,i)=>'<option value="'+i+'"'+(i===sel?' selected':'')+'>'+n+'</option>').join('')}
function slotEditorHtml(){
  const e=B.slotEdit;if(e==null)return '';
  const cur=e>=0&&B.cfg.slots[e]?B.cfg.slots[e]:{from:4*1440+18*60,to:6*1440+6*60};
  return '<div class="bz-sled" id="bz_sl_edit"><b>'+(e>=0?'Cambiar la franja':'Añadir franja')+'</b>'
   +'<div class="bz-g"><label class="bz-f"><span>Desde (día)</span><select id="bz_sl_d1">'+dayOpts(Math.floor(cur.from/1440))+'</select></label>'
   +'<label class="bz-f"><span>Hora</span><input type="time" id="bz_sl_h1" value="'+hhmm(cur.from)+'"></label>'
   +'<label class="bz-f"><span>Hasta (día)</span><select id="bz_sl_d2">'+dayOpts(Math.floor(cur.to/1440))+'</select></label>'
   +'<label class="bz-f"><span>Hora</span><input type="time" id="bz_sl_h2" value="'+hhmm(cur.to)+'"></label></div>'
   +'<div class="bz-hint">Si «hasta» es antes que «desde», la franja da la vuelta al domingo (por ejemplo de domingo 22:00 a lunes 06:00).</div>'
   +'<div class="bz-err" id="bz_sl_err"></div>'
   +'<div class="bz-zb"><button type="button" class="action" id="bz_sl_save" onclick="boltSlotSave()">Guardar franja</button><button type="button" class="secondary" id="bz_sl_cancel" onclick="boltSlotCancel()">Cancelar</button></div></div>';
}
function slotNowHtml(){
  const d=new Date(),wk=isWeekend(B.cfg,d),w=weekMinute(d);
  const when=DAYS[Math.floor(w/1440)].toLowerCase()+' '+hhmm(w);
  let why;
  if(B.cfg.mode==='week')why='has elegido «Siempre entre semana»';else if(B.cfg.mode==='weekend')why='has elegido «Siempre fin de semana»';
  else if(wk)why=(B.cfg.holidaysWe&&isHoliday(B.cfg,d))?'es festivo':'cae dentro de una franja';else why='no cae en ninguna franja';
  return 'Ahora mismo: '+when+' → '+why+' → se usan las tarjetas de <b>'+(wk?'fin de semana':'entre semana')+'</b>.';
}
function slotsBodyHtml(){
  const sl=B.cfg.slots;
  return weekBarHtml()
   +'<div class="bz-sls" id="bz_sl_list">'+(sl.length?sl.map(slotRowHtml).join(''):'<div class="bz-hint" id="bz_sl_none">No hay ninguna franja: siempre se usan las tarjetas de entre semana (salvo festivos).</div>')+'</div>'
   +(B.slotEdit==null?'<div class="bz-zb"><button type="button" class="secondary" id="bz_sl_add" onclick="boltSlotAdd()"'+(sl.length>=MAXS?' disabled':'')+'>➕ Añadir franja</button><button type="button" class="secondary" id="bz_sl_def" onclick="boltReset(\'slots\')">↺ Franjas iniciales</button></div>':slotEditorHtml())
   +'<div class="bz-out" id="bz_sl_now">'+slotNowHtml()+'</div>';
}
function slotsHtml(){
  const c=B.cfg;
  return '<div class="bz-sec" id="bz_slots"><b>📅 Franjas de fin de semana</b><small>Una sola lista para todas las tarjetas. En estas franjas se usan los precios de fin de semana; fuera de ellas, los de entre semana. Lo decide la hora a la que llega la oferta, no el día del calendario.</small>'
   +'<div id="bz_slots_body">'+slotsBodyHtml()+'</div>'
   +chk('Los festivos cuentan como fin de semana (todo el día)','bz_holWe','holidaysWe',c.holidaysWe)
   +'<details id="bz_hol_det"'+(B.holOpen?' open':'')+'><summary class="bz-tsum"><b>🎌 Lista de festivos</b></summary>'
   +'<small>Fechas MM-DD (cada año) o AAAA-MM-DD, separadas por comas. Semana Santa y otros que cambian cada año, añádelos con el año.</small>'
   +'<textarea id="bz_hol" rows="3" data-p="holidays" oninput="boltIn(this)">'+esc((c.holidays||[]).join(', '))+'</textarea></details></div>';
}
function renderSlots(){const b=document.getElementById('bz_slots_body');if(b)b.innerHTML=slotsBodyHtml()}
window.boltSlotOn=function(i,el){const s=B.cfg.slots[i];if(!s)return;s.on=!!el.checked;refreshDerived()};
window.boltSlotEdit=function(i){if(i<0||i>=B.cfg.slots.length)return;B.slotEdit=i;renderSlots()};
window.boltSlotAdd=function(){if(B.cfg.slots.length>=MAXS)return;B.slotEdit=-1;renderSlots()};
window.boltSlotCancel=function(){B.slotEdit=null;renderSlots()};
window.boltSlotDel=function(i){
  const s=B.cfg.slots[i];if(!s)return;
  if(!confirm('¿Borrar la franja «'+slotTxt(s)+'»?\n\nNo se guarda hasta que pulses «Guardar».'))return;
  B.cfg.slots.splice(i,1);if(B.slotEdit!=null)B.slotEdit=null;renderSlots();refreshDerived();
};
function timeMin(v){const m=/^(\d{1,2}):(\d{2})$/.exec(String(v||'').trim());if(!m)return -1;const h=+m[1],mi=+m[2];return h<=23&&mi<=59?h*60+mi:-1}
window.boltSlotSave=function(){
  const g=id=>document.getElementById(id),err=g('bz_sl_err');
  const t1=timeMin(g('bz_sl_h1')&&g('bz_sl_h1').value),t2=timeMin(g('bz_sl_h2')&&g('bz_sl_h2').value);
  const d1=Number(g('bz_sl_d1').value),d2=Number(g('bz_sl_d2').value);
  if(t1<0||t2<0){err.textContent='Pon una hora válida en «desde» y en «hasta».';return false}
  const from=d1*1440+t1,to=d2*1440+t2;
  if(from===to){err.textContent='El principio y el final no pueden ser iguales.';return false}
  const e=B.slotEdit;
  if(e>=0&&B.cfg.slots[e]){B.cfg.slots[e].from=from;B.cfg.slots[e].to=to}
  else{if(B.cfg.slots.length>=MAXS){err.textContent='Hay un máximo de '+MAXS+' franjas.';return false}B.cfg.slots.push({on:true,from,to})}
  B.slotEdit=null;renderSlots();refreshDerived();return true;
};

/* ---------- ajuste por zona y demanda ---------- */
const mt=v=>{let s=spoken(v,2);return s};
const pc=v=>(v>1e-9?'+':v<-1e-9?'−':'')+spoken(Math.abs(v),2)+' %';
function zoneRuleTxt(z){
  return '<b>Fuera de zona buena</b> (M30, sur…): sin demanda o menos de ×'+mt(z.realFrom)+' → tarifa '+pc(z.adj)+'; de ×'+mt(z.realFrom)+' a menos de ×'+mt(z.from)+' → tarifa real (sin descuento y sin demanda); desde ×'+mt(z.from)+' → tarifa × demanda'
   +' (desde ×'+mt(z.a1)+' sube '+mt(z.p1)+' %, desde ×'+mt(z.a2)+' sube '+mt(z.p2)+' %, desde ×'+mt(z.a3)+' sube '+mt(z.p3)+' %; cada escalón sustituye al anterior). '
   +'<b>En zona buena</b>: tarifa '+pc(z.adjGood)+' × la demanda tal como salga, sin escalones.';
}
function zonesHtml(){
  const g=B.cfg.zone.zones;
  if(!g.length)return '<div class="bz-hint" id="bz_z_none">Todavía no has dibujado ninguna zona buena: en todas partes se usa la tarifa de fuera de zona buena. Pulsa «Dibujar zona nueva» y ve poniendo puntos en el mapa.</div>';
  return g.map((a,i)=>{const id=x=>'bz_z_a'+i+'_'+x;
    return '<div class="bz-ar" id="bz_z_ar'+i+'"><input type="text" class="bz-an" id="'+id('n')+'" maxlength="40" placeholder="Nombre de la zona" value="'+esc(a.n)+'" oninput="boltZoneName('+i+',this)">'
     +'<div class="bz-az"><span class="bz-zc" id="'+id('c')+'">'+a.pts.length+' puntos</span><button type="button" class="secondary" id="'+id('ed')+'" onclick="boltMapEdit('+i+')">✏️ Editar en el mapa</button>'
     +'<button type="button" class="secondary bz-adel" id="'+id('del')+'" onclick="boltZoneDel('+i+')" aria-label="Borrar la zona">🗑</button></div></div>'}).join('');
}
function zoneLastTxt(js){
  let o=null;try{o=js?JSON.parse(js):null}catch(e){}
  if(!o||!isN(o.t))return '';
  const ago=Math.max(0,Math.round((Date.now()-o.t)/60000)),when=ago<1?'hace menos de 1 min':ago<60?'hace '+ago+' min':'hace '+Math.round(ago/60)+' h';
  return 'Última lectura real del lector de pantalla ('+when+'): '+(o.ok?(o.good?'zona buena: '+o.good:'fuera de zona buena')+' · ubicación de hace '+o.age+' s ('+o.prov+')':'sin ubicación ('+o.why+') → se usó el ajuste de fuera de zona buena');
}
function zoneHtml(){
  const z=B.cfg.zone,c=B.cfg;
  return '<div class="bz-sec bz-zone'+(z.on?'':' bz-off')+'" id="bz_zone"><b>📍 Ajuste por zona y demanda (con el GPS)</b>'
   +'<div class="bz-row"><div><b>Ajustar los viajes normales según la zona y la demanda</b><br><small>La app mira dónde estás: en una zona buena usa un ajuste y en el resto (M30, sur…) otro. Solo para la tarjeta normal; el aeropuerto no lo usa. Apagado: tarjeta × demanda tal como salga.</small></div><input type="checkbox" id="bz_z_on" data-p="zone.on"'+(z.on?' checked':'')+' onchange="boltIn(this)" style="width:26px;height:26px;flex:none"></div>'
   +'<div class="bz-hint" id="bz_z_rule">'+zoneRuleTxt(z)+'</div>'
   +'<div class="bz-g">'+cell('Fuera de zona buena: ajuste (%)','bz_z_adj',show(z.adj),'zone.adj',{min:-90,step:'1'})+cell('En zona buena: ajuste (%)','bz_z_adjGood',show(z.adjGood),'zone.adjGood',{min:-90,step:'1'})
   +cell('Demanda si la oferta no la trae (×)','bz_z_mult',show(z.mult),'zone.mult',{min:0.1,step:'0.05'})+'<div></div>'
   +chk('Usar el multiplicador que muestre la oferta (×1,4…) en lugar del de arriba','bz_offerMult','offerMult',c.offerMult)+'</div>'
   +'<b class="bz-sub">Demanda de la oferta (fuera de zona buena)</b>'
   +'<div class="bz-g">'+cell('Se acaba el descuento desde ×','bz_z_realFrom',show(z.realFrom),'zone.realFrom',{min:1,step:'0.05'})+cell('Se aplica la demanda desde ×','bz_z_from',show(z.from),'zone.from',{min:1,step:'0.05'})
   +cell('Escalón 1: desde ×','bz_z_a1',show(z.a1),'zone.a1',{min:1,step:'0.05'})+cell('… sube (%)','bz_z_p1',show(z.p1),'zone.p1',{step:'1'})
   +cell('Escalón 2: desde ×','bz_z_a2',show(z.a2),'zone.a2',{min:1,step:'0.05'})+cell('… sube (%)','bz_z_p2',show(z.p2),'zone.p2',{step:'1'})
   +cell('Escalón 3: desde ×','bz_z_a3',show(z.a3),'zone.a3',{min:1,step:'0.05'})+cell('… sube (%)','bz_z_p3',show(z.p3),'zone.p3',{step:'1'})+'</div>'
   +'<div class="bz-err" id="bz_z_ordmsg"></div>'
   +'<b class="bz-sub">Zonas buenas</b><div class="bz-hint">Cada zona es un polígono que dibujas tú, punto a punto, sobre el mapa (así sigues el contorno real: una urbanización, un polígono, el aeropuerto…). Todo lo que quede dentro cuenta como zona buena. Se detectan con la ubicación del móvil.</div>'
   +'<div id="bz_z_list">'+zonesHtml()+'</div>'
   +'<div class="bz-zb"><button type="button" class="action" id="bz_z_map" onclick="boltMap(\'draw\')">🗺 Dibujar zona nueva</button>'
   +'<button type="button" class="secondary" id="bz_z_where" onclick="boltWhere()">📍 Probar ubicación</button>'
   +'<button type="button" class="secondary" id="bz_z_clear" onclick="boltReset(\'areas\')">🗑 Quitar todas las zonas</button>'
   +'<button type="button" class="secondary" id="bz_z_defz" onclick="boltReset(\'zone\')">↺ Valores iniciales del ajuste (las zonas se quedan)</button></div>'
   +'<div class="bz-out" id="bz_z_loc">'+esc(zoneLastTxt(B.zoneLast)||'Pulsa «Probar ubicación» para ver dónde cree la app que estás.')+'</div>'
   +'<div class="bz-hint">Si el móvil no da la ubicación (sin permiso o sin datos recientes), se usa el ajuste de fuera de zona buena.</div></div>';
}
function zoneCheck(){
  const z=B.cfg.zone,v=ZORD.map(k=>z[k]);let okOrd=true;
  for(let i=1;i<v.length;i++)if(!(v[i]>=v[i-1]))okOrd=false;
  ZORD.forEach((k,i)=>{const el=document.getElementById('bz_z_'+k);if(!el)return;const wrong=!okOrd&&((i>0&&v[i]<v[i-1])||(i<v.length-1&&v[i+1]<v[i]));bad(el,wrong||errors.has(el.id))});
  okOrd?errors.delete('zord'):errors.add('zord');
  const m=document.getElementById('bz_z_ordmsg');if(m)m.textContent=okOrd?'':'Los umbrales tienen que ir de menor a mayor: «se acaba el descuento» ≤ «se aplica la demanda» ≤ escalón 1 ≤ escalón 2 ≤ escalón 3.';
  const r=document.getElementById('bz_z_rule');if(r)r.innerHTML=zoneRuleTxt(z);
}
window.boltZoneName=function(i,el){const a=B.cfg.zone.zones[i];if(!a)return;a.n=areaName(el.value);if(P.zmap&&P.zmap.open)P.zmap.redraw()};
function renderZones(){const l=document.getElementById('bz_z_list');if(l)l.innerHTML=zonesHtml();boltSim()}
window.boltZoneDel=function(i){
  const g=B.cfg.zone.zones;if(i<0||i>=g.length)return;
  if(!confirm('¿Borrar la zona «'+(g[i].n||'sin nombre')+'»?\n\nNo se guarda hasta que pulses «Guardar».'))return;
  g.splice(i,1);if(P.zmap&&P.zmap.open){P.zmap.sel=-1;P.zmap.vsel=-1;P.zmap.panel();P.zmap.redraw()}renderZones();
};
function newZoneName(){const g=B.cfg.zone.zones;let n=g.length+1;while(g.some(a=>a.n==='Zona '+n))n++;return 'Zona '+n}
function addZone(pts,name){
  const g=B.cfg.zone.zones;if(g.length>=MAXZ){alert('Hay un máximo de '+MAXZ+' zonas.');return -1}
  if(!Array.isArray(pts)||pts.length<3)return -1;
  g.push({n:areaName(name||newZoneName()),pts:pts.slice(0,MAXPT).map(p=>[Math.round(p[0]*1e6)/1e6,Math.round(p[1]*1e6)/1e6])});renderZones();return g.length-1;
}
P.boltAddZone=addZone;
/* ubicación: primero la del navegador/WebView; si no, la última que tiene el sistema (la lee el código nativo) */
function getPos(ms,age){return new Promise(res=>{try{if(!navigator.geolocation)return res({err:'este móvil no da la ubicación a la página'});navigator.geolocation.getCurrentPosition(p=>res({lat:p.coords.latitude,lon:p.coords.longitude,acc:p.coords.accuracy}),e=>res({err:(e&&e.message)||'sin permiso'}),{enableHighAccuracy:true,timeout:ms,maximumAge:age||0})}catch(e){res({err:String(e)})}})}
async function nativeFix(){
  const sr=SR();if(!sr)return null;
  try{const r=await sr.zoneNow({cfg:JSON.stringify(B.cfg)});const o=r&&r.zone?JSON.parse(r.zone):null;return o}catch(e){return null}
}
async function myPos(){
  let g=await getPos(8000,0);if(g&&!g.err)return g;
  const g2=await getPos(1500,60000);if(g2&&!g2.err)return g2;
  const n=await nativeFix();if(n&&n.ok)return {lat:n.lat,lon:n.lon,acc:-1,old:n.age};
  return {err:(g&&g.err)||'sin ubicación'};
}
window.boltWhere=async function(){
  const out=document.getElementById('bz_z_loc');if(!out)return;
  out.textContent='Buscando tu ubicación…';
  const lines=[];
  const g=await getPos(8000);
  if(g&&!g.err){const n=goodAreaAt(B.cfg.zone,g.lat,g.lon);lines.push('📍 Ahora (GPS): '+show(Math.round(g.lat*1e5)/1e5)+', '+show(Math.round(g.lon*1e5)/1e5)+(g.acc>0?' (±'+Math.round(g.acc)+' m)':'')+' → '+(n!==null?'ZONA BUENA'+(n?': '+n:''):'fuera de zona buena'))}
  else lines.push('📍 Ahora (GPS): sin ubicación ('+g.err+')');
  const sr=SR();
  if(sr){
    const n=await nativeFix();
    if(n)lines.push('🔧 Lo que ve el lector de pantalla: '+(n.ok?'ubicación de hace '+n.age+' s ('+n.prov+') → '+(n.good?'ZONA BUENA: '+n.good:'fuera de zona buena'):'sin ubicación ('+n.why+') → usaría el ajuste de fuera de zona buena'));
    else lines.push('🔧 Lo que ve el lector de pantalla: no se pudo consultar');
    try{const d=await sr.getBolt();if(d&&typeof d.zoneLast==='string')B.zoneLast=d.zoneLast}catch(e){}
    const l=zoneLastTxt(B.zoneLast);if(l)lines.push(l);
  }
  out.innerHTML=lines.map(esc).join('<br>');
};
const pctSign=v=>(v>1e-9?'+':v<-1e-9?'−':'')+spoken(Math.abs(v),1)+' %';
function zoneLine(e){const zero=Math.abs(e.adj)<1e-9;return e.zone===2?'Zona buena · tarifa '+(zero?'normal':pctSign(e.adj)):'Fuera de zona buena · tarifa '+(zero?'real':pctSign(e.adj))}
function zoneDemand(e,om){
  if(!(om>0))return e.mult>1+1e-9?'Demanda ×'+mt(e.mult)+' (a mano)':'Sin demanda en la oferta';
  if(!e.fromOffer)return 'Demanda ×'+mt(om)+' de la oferta: ignorada (lo tienes desactivado)';
  let s='Demanda ×'+mt(om)+' (de la oferta)';
  if(e.zone===1){if(Math.abs(e.eff-1)<1e-9)s+=': no se aplica (solo desde ×'+mt(e.hi)+')';else if(e.eff>om+1e-9)s+=' +'+spoken(Math.round((e.eff/om-1)*1000)/10,1)+' % = ×'+mt(e.eff)}
  return s;
}
const cardTxt=e=>(e.airport==='pickup'?'Aeropuerto (recogida)':e.airport==='dest'?'Aeropuerto (viaje hacia allí)':'Tarjeta normal')+' · '+(e.weekend?'fin de semana':'entre semana');
P.boltZoneTxt={line:zoneLine,demand:zoneDemand,card:cardTxt};
function simHtml(){
  const k=B.sim.kind;
  return '<div class="bz-sec"><b>🧮 Simulador (para contrastar con viajes reales)</b><small>Escribe los km y minutos del viaje con pasajero y mira qué estimaría la app con los valores de arriba.</small>'
   +'<div class="bz-g">'+cell('Km del viaje','bz_sKm',show(B.sim.km),'',{step:'0.1',on:'boltSim()'})+cell('Minutos del viaje','bz_sMin',show(B.sim.min),'',{step:'1',on:'boltSim()'})
   +cell('Demanda de la oferta (opcional)','bz_sMult',B.sim.mult,'',{step:'0.05',on:'boltSim()'})
   +'<label class="bz-f"><span>Tarjeta</span><select id="bz_sProf" onchange="boltSim()"><option value="auto"'+(B.sim.prof==='auto'?' selected':'')+'>Ahora (según tus franjas)</option><option value="wd"'+(B.sim.prof==='wd'?' selected':'')+'>Entre semana</option><option value="we"'+(B.sim.prof==='we'?' selected':'')+'>Fin de semana</option></select></label>'
   +'<label class="bz-f bz-w"><span>Tipo de viaje</span><select id="bz_sKind" onchange="boltSim()"><option value=""'+(k===''?' selected':'')+'>Normal (fuera del aeropuerto)</option><option value="pickup"'+(k==='pickup'?' selected':'')+'>Recogida en el aeropuerto</option><option value="dest"'+(k==='dest'?' selected':'')+'>Viaje hacia el aeropuerto</option></select></label>'
   +'<label class="bz-f bz-w"><span>Ubicación (ajuste por zona)</span><select id="bz_sGood" onchange="boltSim()"><option value="0"'+(B.sim.zone!=='1'?' selected':'')+'>Fuera de zona buena (M30, sur…)</option><option value="1"'+(B.sim.zone==='1'?' selected':'')+'>En zona buena</option></select></label></div>'
   +'<div id="bz_sOut" class="bz-out"></div></div>';
}
function bodyHtml(){
  const c=B.cfg;
  return '<div class="bz-note">Cuando la oferta de Bolt <b>no muestra el precio</b>, la app lo <b>estima</b> con estas tarjetas (según el tipo de viaje, las franjas de fin de semana y tu ubicación) y te dice el bruto, la comisión y el <b>neto estimado</b> (en pantalla y por voz). '
   +'<b>Son estimaciones nuestras con viajes reales, no tarifas oficiales de Bolt</b>: si ves que Bolt paga más o menos, corrígelas aquí. Si la oferta sí trae el precio, se usa ese y no se estima nada.</div>'
   +'<div class="bz-row"><div><b>Estimar el precio de Bolt</b><br><small>Solo cuando la oferta no lo muestra.</small></div><input type="checkbox" id="bz_on" data-p="on"'+(c.on?' checked':'')+' onchange="boltIn(this)" style="width:26px;height:26px;flex:none"></div>'
   +'<div class="bz-g">'
   +'<label class="bz-f bz-w"><span>Qué tarjetas usar</span><select id="bz_mode" data-p="mode" onchange="boltIn(this)"><option value="auto"'+(c.mode==='auto'?' selected':'')+'>Automático por mis franjas</option><option value="week"'+(c.mode==='week'?' selected':'')+'>Siempre las de entre semana</option><option value="weekend"'+(c.mode==='weekend'?' selected':'')+'>Siempre las de fin de semana</option></select></label>'
   +cell('Comisión de Bolt (%)','bz_comm',show(c.comm),'comm',{step:'0.5'})+'<div></div></div>'
   +'<div class="bz-hint" id="bz_today"></div>'
   +cardsHtml()
   +slotsHtml()
   +zoneHtml()
   +simHtml()
   +'<div class="bz-sec"><b>🔊 Aviso por voz</b><div class="bz-row"><div><b>Leer en voz alta la estimación</b><br><small>«Bolt. Viaje de 8,3 kilómetros y 10 minutos. Bruto estimado… Neto estimado…»</small></div><input type="checkbox" id="bz_voice" onchange="boltIn(this)" data-p="#voice"'+(B.voice?' checked':'')+' style="width:26px;height:26px;flex:none"></div>'
   +'<label class="bz-f"><span>Volumen de la voz</span><input type="range" id="bz_vol" min="0.1" max="1" step="0.1" value="'+B.vol+'" data-p="#vol" oninput="boltIn(this)"></label></div>'
   +'<div class="bz-btns"><button type="button" class="action" onclick="boltSave()">✔ Guardar estimación de Bolt</button>'
   +'<button type="button" class="secondary" onclick="boltTestVoice()">🔊 Probar aviso de Bolt</button>'
   +'<button type="button" class="secondary" id="bz_all_def" onclick="boltReset(\'all\')">↺ Valores iniciales de todo</button></div>'
   +'<div id="bz_err" class="bz-err"></div>';
}
function render(){
  const box=document.getElementById('boltBox');if(!box)return;
  box.innerHTML='<details id="bz_det"'+(B.open?' open':'')+'><summary><b>💶 Estimación del precio de Bolt</b> <span class="bz-badge">NUEVO</span><br><small id="bz_sum"></small></summary><div id="bz_body">'+bodyHtml()+'</div></details>';
  const d=document.getElementById('bz_det');d.addEventListener('toggle',()=>{B.open=d.open});
  afterBody();
}
function afterBody(){const t=document.getElementById('bz_hol_det');if(t&&!t._z){t._z=1;t.addEventListener('toggle',()=>{B.holOpen=t.open})}refreshDerived()}
function reloadBody(){errors.clear();B.slotEdit=null;const b=document.getElementById('bz_body');if(b)b.innerHTML=bodyHtml();afterBody()}
function refreshDerived(){
  const c=B.cfg,e=document.getElementById('bz_sum');
  B.weekendNow=isWeekend(c,new Date());
  if(e)e.textContent=(c.on?'Activada':'Desactivada')+' · 4 tarjetas por franjas · '+(c.zone.on?'ajuste por zona (GPS)':'sin ajuste de zona')+' · comisión '+show(c.comm)+' %';
  const zb=document.getElementById('bz_zone');if(zb)zb.classList.toggle('bz-off',!c.zone.on);
  const t=document.getElementById('bz_today');
  if(t)t.textContent='Ahora se usarían las tarjetas de '+(B.weekendNow?'fin de semana':'entre semana')+'.';
  for(let d=0;d<7;d++){const bar=document.getElementById('bz_wk'+d);if(bar)bar.innerHTML=barSegs(d).map(s=>'<i style="left:'+s[0].toFixed(2)+'%;width:'+s[1].toFixed(2)+'%"></i>').join('')}
  for(let i=0;i<c.slots.length;i++){const x=document.getElementById('bz_sl_'+i+'_t');if(x)x.textContent=slotTxt(c.slots[i])}
  const sn=document.getElementById('bz_sl_now');if(sn)sn.innerHTML=slotNowHtml();
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
  if(el.type==='checkbox'){setPath(B.cfg,p,el.checked);if(p==='on'||p==='zone.on'||p==='holidaysWe')refreshDerived();else boltSim();return}
  if(p==='mode'){B.cfg.mode=el.value;refreshDerived();return}
  if(p==='holidays'){
    const items=el.value.split(/[\s,;]+/).filter(Boolean);const okAll=items.every(x=>/^(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})$/.test(x));
    bad(el,!okAll);okAll?errors.delete(el.id):errors.add(el.id);
    if(okAll){B.cfg.holidays=[...new Set(items)];refreshDerived()}
    return;
  }
  const v=num(el.value);
  const key=p.split('.').pop();
  const isZ=/^zone\./.test(p);
  const lim=isZ?LIMZ[key]:/^cards\./.test(p)?LIMC[key]:p==='airFee'?[0,50]:p==='comm'?[0,90]:null;
  const okv=Number.isFinite(v)&&(!lim||(v>=lim[0]&&v<=lim[1]));
  bad(el,!okv);okv?errors.delete(el.id):errors.add(el.id);
  if(!okv)return;
  setPath(B.cfg,p,v);
  if(isZ){zoneCheck();boltSim();return}
  refreshDerived();
};
window.boltSim=function(){
  const out=document.getElementById('bz_sOut');if(!out)return;
  const g=id=>{const e=document.getElementById(id);return e?num(e.value):NaN};
  const km=g('bz_sKm'),min=g('bz_sMin');let om=g('bz_sMult');const sp=document.getElementById('bz_sProf'),sk=document.getElementById('bz_sKind');
  if(sp)B.sim.prof=sp.value;if(sk)B.sim.kind=sk.value;
  B.sim.km=Number.isFinite(km)?km:B.sim.km;B.sim.min=Number.isFinite(min)?min:B.sim.min;
  const e0=document.getElementById('bz_sMult');B.sim.mult=e0?e0.value:'';
  if(!(km>=0)||!(min>=0)){out.innerHTML='<span class="bz-warn">Escribe los km y los minutos del viaje con pasajero.</span>';return}
  const sg=document.getElementById('bz_sGood');if(sg)B.sim.zone=sg.value;
  const wk=B.sim.prof==='we'?true:B.sim.prof==='wd'?false:isWeekend(B.cfg,new Date());
  const omv=Number.isFinite(om)&&om>0?om:-1,gz=B.sim.zone==='1';
  const e=estimate(B.cfg,wk,km,min,omv,B.sim.kind,gz);
  out.innerHTML='<div class="bz-big"><span>NETO ESTIMADO</span><b id="bz_sNet">'+money(e.net)+' €</b></div>'
   +'<div class="bz-line">Bruto estimado: <b id="bz_sGross">'+money(e.gross)+' €</b>'+(e.minApplied?' (tarifa mínima)':'')+(e.fee>0?' − Tasa del aeropuerto: <b id="bz_sFee">'+money(e.fee)+' €</b> = <b id="bz_sAfter">'+money(Math.max(0,e.gross-e.fee))+' €</b> (la tasa se resta antes de la comisión)':'')+' · Comisión ('+show(B.cfg.comm)+' %): <b id="bz_sComm">'+money(e.comm)+' €</b></div>'
   +'<div class="bz-line" id="bz_sCard">'+esc(cardTxt(e))+'</div>'
   +'<div class="bz-line">'+(e.zone>0?esc(zoneLine(e))+' · ':'')+esc(zoneDemand(e,omv))+'</div>'
   +'<div class="bz-line bz-voice">🔊 «'+esc(voiceText(e,km,min))+'»</div>';
};
window.boltSave=async function(silent){
  const err=document.getElementById('bz_err');
  zoneCheck();
  if(errors.size){if(err)err.textContent='Revisa los campos marcados en rojo: hay valores fuera de rango o umbrales que no van creciendo.';if(!silent)alert('Revisa los campos marcados en rojo.');return false}
  if(err)err.textContent='';
  let fixed=false;
  try{fixed=await persist()}catch(e){alert('No se pudo guardar la estimación de Bolt.');return false}
  if(fixed){const b=document.getElementById('bz_body');if(b)b.innerHTML=bodyHtml();afterBody();alert('Algún valor no era válido y se ha corregido. Revísalo antes de seguir.');return true}
  refreshDerived();
  if(!silent&&P.toastOk)P.toastOk('✅ Estimación de Bolt guardada');
  return true;
};
window.boltReset=function(which){
  const d=defaults();
  const msg=which==='all'?'¿Volver a los valores iniciales de TODA la estimación de Bolt (tarjetas, franjas, ajuste por zona, comisión y festivos)?\n\nTambién se quitarán las zonas buenas que hayas dibujado. No se guarda hasta que pulses «Guardar».'
    :which==='zone'?'¿Volver a los valores iniciales del ajuste por zona y demanda (porcentajes y escalones)?\n\nLas zonas que hayas dibujado se quedan. No se guarda hasta que pulses «Guardar».'
    :which==='areas'?'¿Quitar TODAS las zonas buenas que hayas dibujado?\n\nNo se guarda hasta que pulses «Guardar».'
    :which==='slots'?'¿Volver a las franjas iniciales (viernes 18:00 → domingo 06:00)?\n\nNo se guarda hasta que pulses «Guardar».'
    :'¿Volver a los valores iniciales de las cuatro tarjetas, el aeropuerto y la tasa?\n\nNo se guarda hasta que pulses «Guardar».';
  if(!confirm(msg))return;
  if(which==='all'){B.cfg=d}
  else if(which==='zone'){const keep=B.cfg.zone.zones;B.cfg.zone=d.zone;B.cfg.zone.zones=keep;B.cfg.offerMult=d.offerMult}
  else if(which==='areas'){B.cfg.zone.zones=[];if(P.zmap){P.zmap.sel=-1;P.zmap.vsel=-1;P.zmap.draft=null}}
  else if(which==='slots'){B.cfg.slots=d.slots}
  else{B.cfg.cards=d.cards;B.cfg.airOn=d.airOn;B.cfg.airFee=d.airFee}
  reloadBody();refreshDerived();if(P.zmap&&P.zmap.open){P.zmap.panel();P.zmap.redraw()}
};
window.boltTestVoice=async function(){
  const ok=await window.boltSave(true);if(ok===false)return;
  const sr=SR();if(!sr){alert('Esta prueba solo funciona en el móvil, con la app instalada.');return}
  try{await sr.testBolt();if(P.toastOk)P.toastOk('Mira y escucha el aviso 👆')}catch(e){alert('Activa primero el lector de pantalla (Accesibilidad).')}
};

/* ---------- mapa para dibujar las zonas buenas ----------
   Mapa propio y sencillo (sin librerías): arrastras para moverte, ＋/－ o pellizcar para acercar. «Dibujar zona nueva»: tocas el mapa para ir poniendo puntos
   alrededor de la zona y la cierras tocando el punto 1 (verde) o con «Cerrar zona». Tocando una zona: arrastras sus puntos blancos para moverlos, tocas un punto
   para elegirlo y borrarlo, tocas el círculo pequeño del medio de un lado para añadir un punto, o borras la zona entera. Una zona no puede cruzarse consigo misma.
   Las IMÁGENES del mapa se descargan de internet (OpenStreetMap, y si no responde CARTO o Esri); sin internet se ven igualmente las zonas sobre un fondo liso y se pueden editar. */
const TILE_SRC=[
  {n:'OpenStreetMap',u:'https://tile.openstreetmap.org/{z}/{x}/{y}.png',a:'© OpenStreetMap'},
  {n:'CARTO',u:'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',a:'© OpenStreetMap · © CARTO'},
  {n:'Esri',u:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',a:'© Esri'}];
const TS=256,ZMIN=8,ZMAX=18;
const M={open:false,lat:40.4168,lon:-3.7038,z:11,w:0,h:0,sel:-1,vsel:-1,mode:'view',draft:null,bad:false,me:null,src:0,ok:0,err:0,tiles:new Map(),el:null,gone:false,wt:0};
P.zmap=M;
const wx=(lon,z)=>(lon+180)/360*TS*Math.pow(2,z);
const wy=(lat,z)=>{const s=Math.sin(Math.max(-85.0511,Math.min(85.0511,lat))*Math.PI/180);return (0.5-Math.log((1+s)/(1-s))/(4*Math.PI))*TS*Math.pow(2,z)};
const lonAt=(x,z)=>x/(TS*Math.pow(2,z))*360-180;
const latAt=(y,z)=>{const n=Math.PI-2*Math.PI*y/(TS*Math.pow(2,z));return 180/Math.PI*Math.atan(0.5*(Math.exp(n)-Math.exp(-n)))};
const mpp=(lat,z)=>156543.03392*Math.cos(lat*Math.PI/180)/Math.pow(2,z);
M.toScreen=(lat,lon)=>({x:wx(lon,M.z)-wx(M.lon,M.z)+M.w/2,y:wy(lat,M.z)-wy(M.lat,M.z)+M.h/2});
M.fromScreen=(x,y)=>({lat:latAt(wy(M.lat,M.z)+(y-M.h/2),M.z),lon:lonAt(wx(M.lon,M.z)+(x-M.w/2),M.z)});
function mapDrawTiles(){
  const host=M.el.tiles,n=Math.pow(2,M.z),cx=wx(M.lon,M.z),cy=wy(M.lat,M.z);
  const x0=Math.floor((cx-M.w/2)/TS),x1=Math.floor((cx+M.w/2)/TS),y0=Math.max(0,Math.floor((cy-M.h/2)/TS)),y1=Math.min(n-1,Math.floor((cy+M.h/2)/TS));
  const keep=new Set();
  for(let ty=y0;ty<=y1;ty++)for(let tx=x0;tx<=x1;tx++){
    const wxm=((tx%n)+n)%n,key=M.src+'/'+M.z+'/'+tx+'/'+ty;keep.add(key);
    let img=M.tiles.get(key);
    if(!img){
      img=new Image();img.className='zm-tile';img.alt='';img.draggable=false;const sIdx=M.src;
      img.onload=()=>{if(sIdx!==M.src)return;M.ok++;mapInfo()};
      img.onerror=()=>{img.remove();if(M.tiles.get(key)===img)M.tiles.delete(key);if(sIdx!==M.src)return;M.err++;mapTileFail()};
      img.src=TILE_SRC[M.src].u.replace('{z}',M.z).replace('{x}',wxm).replace('{y}',ty);
      host.appendChild(img);M.tiles.set(key,img);
    }
    img.style.transform='translate('+Math.round(tx*TS-cx+M.w/2)+'px,'+Math.round(ty*TS-cy+M.h/2)+'px)';
  }
  for(const [k,img] of Array.from(M.tiles))if(!keep.has(k)){img.remove();M.tiles.delete(k)}
}
function mapTileFail(){
  if(M.ok===0&&M.err>=6){
    if(M.src<TILE_SRC.length-1){M.src++;M.err=0;for(const i of M.tiles.values())i.remove();M.tiles.clear();mapDrawTiles()}
    else if(!M.gone){M.gone=true;mapInfo()}
  }
}
function mapInfo(){
  if(!M.el)return;
  const g=B.cfg.zone.zones.length;
  const a=M.el.attr;if(a)a.textContent=M.gone?'Sin imágenes de mapa (¿sin internet?)':TILE_SRC[M.src].a;
  const m=M.el.msg;if(m){if(M.gone){m.style.display='block';m.textContent='No se pueden cargar las imágenes del mapa (sin internet o el servidor no responde). Puedes seguir dibujando y editando zonas: se ven como formas sobre fondo liso.'}else m.style.display='none'}
  const i=M.el.info;if(i)i.textContent=(M.mode==='draw'?'dibujando · ':'')+g+(g===1?' zona':' zonas')+' · zoom '+M.z;
}
function mapWarn(t){
  const w=M.el&&M.el.warn;if(!w)return;
  w.textContent=t;w.style.display=t?'block':'none';
  clearTimeout(M.wt);if(t)M.wt=setTimeout(()=>{if(M.el&&M.el.warn)M.el.warn.style.display='none'},4000);
}
/* ¿el polígono (o la línea, si no está cerrado) se cruza consigo mismo? Proyección plana: sobra para el tamaño de una zona */
const pj=(p,lat0)=>[p[1]*Math.cos(lat0*Math.PI/180),p[0]];
const orient=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
const segX=(a,b,c,d)=>{const o1=orient(a,b,c),o2=orient(a,b,d),o3=orient(c,d,a),o4=orient(c,d,b);return o1*o2<0&&o3*o4<0};
function crosses(pts,closed){
  const n=pts.length;if(n<4)return false;
  const q=pts.map(p=>pj(p,pts[0][0])),segs=closed?n:n-1;
  for(let i=0;i<segs;i++)for(let j=i+2;j<segs;j++){
    if(closed&&i===0&&j===n-1)continue;                      // el primer y el último lado comparten el punto 1
    if(segX(q[i],q[(i+1)%n],q[j],q[(j+1)%n]))return true;
  }
  return false;
}
P.boltCrosses=crosses;
const polyArea=pts=>{let s=0;for(let i=0,j=pts.length-1;i<pts.length;j=i++)s+=(pts[j][1]*pts[i][0]-pts[i][1]*pts[j][0]);return Math.abs(s/2)};
function scr(p){return M.toScreen(p[0],p[1])}
function polyStr(pts){return pts.map(p=>{const q=scr(p);return q.x.toFixed(1)+','+q.y.toFixed(1)}).join(' ')}
function mapDrawSvg(){
  const g=B.cfg.zone.zones;let h='';
  g.forEach((a,i)=>{
    const sel=i===M.sel&&M.mode!=='draw';
    h+='<polygon class="zm-p'+(sel?' sel':'')+(sel&&M.bad?' bad':'')+'" data-i="'+i+'" points="'+polyStr(a.pts)+'"/>';
    let la=0,lo=0;for(const p of a.pts){la+=p[0];lo+=p[1]}
    const c=M.toScreen(la/a.pts.length,lo/a.pts.length);
    h+='<text class="zm-t" x="'+c.x.toFixed(1)+'" y="'+(c.y+4).toFixed(1)+'">'+esc(a.n||'(sin nombre)')+'</text>';
  });
  if(M.mode==='draw'&&M.draft&&M.draft.length){
    const d=M.draft;
    if(d.length>1)h+='<polyline class="zm-dr" points="'+polyStr(d)+'"/>';
    if(d.length>=3){const a=scr(d[d.length-1]),b=scr(d[0]);h+='<line class="zm-dc" x1="'+a.x.toFixed(1)+'" y1="'+a.y.toFixed(1)+'" x2="'+b.x.toFixed(1)+'" y2="'+b.y.toFixed(1)+'"/>'}
    d.forEach((p,k)=>{const q=scr(p);h+='<circle class="zm-dv'+(k===0?' first':'')+'" data-v="'+k+'" cx="'+q.x.toFixed(1)+'" cy="'+q.y.toFixed(1)+'" r="'+(k===0?12:8)+'"/>';if(k===0)h+='<text class="zm-n" x="'+q.x.toFixed(1)+'" y="'+(q.y+4).toFixed(1)+'">1</text>'});
  }else{
    const a=g[M.sel];
    if(a&&M.mode!=='draw'){
      a.pts.forEach((p,k)=>{const n=a.pts[(k+1)%a.pts.length],q=M.toScreen((p[0]+n[0])/2,(p[1]+n[1])/2);h+='<circle class="zm-mid" data-m="'+k+'" cx="'+q.x.toFixed(1)+'" cy="'+q.y.toFixed(1)+'" r="6"/>'});
      a.pts.forEach((p,k)=>{const q=scr(p);h+='<circle class="zm-v'+(k===M.vsel?' sel':'')+'" data-v="'+k+'" cx="'+q.x.toFixed(1)+'" cy="'+q.y.toFixed(1)+'" r="'+(k===M.vsel?11:9)+'"/>'});
    }
  }
  if(M.me){const p=M.toScreen(M.me.lat,M.me.lon);if(M.me.acc>0)h+='<circle class="zm-ma" cx="'+p.x.toFixed(1)+'" cy="'+p.y.toFixed(1)+'" r="'+Math.max(6,M.me.acc/mpp(M.me.lat,M.z)).toFixed(1)+'"/>';h+='<circle class="zm-me" cx="'+p.x.toFixed(1)+'" cy="'+p.y.toFixed(1)+'" r="7"/>'}
  M.el.svg.innerHTML=h;
}
M.redraw=function(){if(!M.open||!M.el)return;mapDrawTiles();mapDrawSvg();mapInfo()};
M.zoom=function(dz,fx,fy){
  const nz=Math.max(ZMIN,Math.min(ZMAX,M.z+dz));if(nz===M.z)return;
  const px=fx==null?M.w/2:fx,py=fy==null?M.h/2:fy,f=M.fromScreen(px,py);
  M.z=nz;M.lon=lonAt(wx(f.lon,nz)-(px-M.w/2),nz);M.lat=latAt(wy(f.lat,nz)-(py-M.h/2),nz);
  for(const i of M.tiles.values())i.remove();M.tiles.clear();M.redraw();
};
/* encuadra todas las zonas (o solo la zona i) */
M.fit=function(only){
  const all=B.cfg.zone.zones,g=only!=null&&all[only]?[all[only]]:all;
  if(!g.length){M.lat=40.4168;M.lon=-3.7038;M.z=11;return}
  let s=90,n=-90,w=180,e=-180;
  for(const a of g)for(const p of a.pts){s=Math.min(s,p[0]);n=Math.max(n,p[0]);w=Math.min(w,p[1]);e=Math.max(e,p[1])}
  M.lat=(s+n)/2;M.lon=(w+e)/2;
  for(let z=17;z>=ZMIN;z--){const W=wx(e,z)-wx(w,z),H=wy(s,z)-wy(n,z);if(W<=M.w*0.8&&H<=M.h*0.8){M.z=z;return}}
  M.z=ZMIN;
};
M.select=function(i,v){M.sel=i;M.vsel=v==null?-1:v;M.bad=false;mapPanel();M.redraw()};
M.panel=function(){if(M.open&&M.el)mapPanel()};
function btn(id,txt,cls,dis){return '<button type="button" id="'+id+'"'+(cls?' class="'+cls+'"':'')+(dis?' disabled':'')+'>'+txt+'</button>'}
function mapPanel(){
  const b=M.el.bot,g=B.cfg.zone.zones,a=M.mode==='draw'?null:g[M.sel];
  if(M.mode==='draw'){
    const n=M.draft?M.draft.length:0;
    b.innerHTML='<div class="zm-row"><b id="zm_dn">Zona nueva · '+n+(n===1?' punto':' puntos')+'</b></div>'
     +'<div class="zm-row">'+btn('zm_undo','↩ Deshacer punto','',n===0)+btn('zm_close','✔ Cerrar zona','zm-ok',n<3)+btn('zm_cancel','Cancelar','')+'</div>'
     +'<div class="zm-help">Toca el mapa para ir poniendo puntos alrededor de la zona (arrastra para mover el mapa). Para terminar, toca el punto 1 (el verde) o «Cerrar zona». Hacen falta al menos 3 puntos.</div>';
    M.el.bot.querySelector('#zm_undo').onclick=mapUndo;M.el.bot.querySelector('#zm_close').onclick=mapClose;M.el.bot.querySelector('#zm_cancel').onclick=mapCancel;
  }else if(a){
    b.innerHTML='<div class="zm-row"><input id="zm_name" type="text" maxlength="40" placeholder="Nombre de la zona" value="'+esc(a.n)+'">'+btn('zm_del','🗑 Borrar zona','')+'</div>'
     +'<div class="zm-row">'+btn('zm_vdel','✖ Borrar punto','',!(M.vsel>=0&&a.pts.length>3))+btn('zm_draw','✏️ Dibujar otra zona','')+btn('zm_me','📍 Mi ubicación','')+'</div>'
     +'<div class="zm-help">Arrastra un punto blanco para moverlo. Toca un punto para elegirlo y bórralo con «Borrar punto» (mínimo 3). Toca el círculo pequeño del medio de un lado para añadir un punto. Toca un sitio vacío para dejar de editar.</div>';
    const nm=b.querySelector('#zm_name');nm.oninput=()=>{a.n=areaName(nm.value);M.redraw();const l=document.getElementById('bz_z_a'+M.sel+'_n');if(l)l.value=a.n};
    b.querySelector('#zm_del').onclick=()=>{window.boltZoneDel(M.sel)};
    b.querySelector('#zm_vdel').onclick=mapVertexDel;
    b.querySelector('#zm_draw').onclick=()=>mapStartDraw();
    b.querySelector('#zm_me').onclick=mapLocate;
  }else{
    b.innerHTML='<div class="zm-row">'+btn('zm_draw','✏️ Dibujar zona nueva','zm-ok')+btn('zm_me','📍 Mi ubicación','')+'</div>'
     +'<div class="zm-help">'+(g.length?'Toca una zona para cambiarla o borrarla. ':'Todavía no hay zonas. ')+'«Dibujar zona nueva» te deja ir poniendo puntos alrededor de la zona. Las zonas buenas usan el ajuste de zona buena.</div>';
    b.querySelector('#zm_draw').onclick=()=>mapStartDraw();
    b.querySelector('#zm_me').onclick=mapLocate;
  }
}
function syncList(){const g=B.cfg.zone.zones;g.forEach((a,i)=>{const c=document.getElementById('bz_z_a'+i+'_c');if(c)c.textContent=a.pts.length+' puntos'})}
function mapStartDraw(){M.mode='draw';M.draft=[];M.sel=-1;M.vsel=-1;M.bad=false;mapWarn('');mapPanel();M.redraw()}
function mapUndo(){if(M.draft&&M.draft.length){M.draft.pop();mapWarn('');mapPanel();M.redraw()}}
function mapCancel(){M.draft=null;M.mode='view';mapWarn('');mapPanel();M.redraw()}
function mapClose(){
  const d=M.draft;if(!d||d.length<3)return false;
  if(crosses(d,true)){mapWarn('Esa zona se cruzaría consigo misma: deshaz el último punto o ponlo en otro sitio.');return false}
  const i=addZone(d);if(i<0)return false;
  M.draft=null;M.mode='view';mapWarn('');M.select(i,-1);return true;
}
function mapVertexDel(){
  const a=B.cfg.zone.zones[M.sel];if(!a||M.vsel<0||a.pts.length<=3)return;
  const t=a.pts.slice();t.splice(M.vsel,1);
  if(crosses(t,true)){mapWarn('Si quitas ese punto la zona se cruzaría consigo misma.');return}
  a.pts=t;M.vsel=-1;syncList();mapPanel();M.redraw();
}
async function mapLocate(){
  const msg=M.el.msg;
  const pos=await myPos();
  if(!M.open)return;
  if(pos.err){msg.style.display='block';msg.textContent='No se pudo obtener tu ubicación ('+pos.err+'). Comprueba el permiso de ubicación.';return}
  M.me={lat:pos.lat,lon:pos.lon,acc:pos.acc};M.lat=pos.lat;M.lon=pos.lon;if(M.z<13){M.z=13;for(const i of M.tiles.values())i.remove();M.tiles.clear()}
  M.redraw();
}
/* qué hay bajo el dedo: el punto 1 del borrador, un punto de la zona elegida o el círculo del medio de un lado */
function mapHit(x,y){
  if(M.mode==='draw'){
    if(M.draft&&M.draft.length>=3){const q=scr(M.draft[0]);if(Math.hypot(q.x-x,q.y-y)<24)return {t:'first'}}
    return null;
  }
  const a=B.cfg.zone.zones[M.sel];if(!a)return null;
  let best=-1,bd=24;
  a.pts.forEach((p,k)=>{const q=scr(p),d=Math.hypot(q.x-x,q.y-y);if(d<bd){bd=d;best=k}});
  if(best>=0)return {t:'v',k:best};
  bd=22;
  a.pts.forEach((p,k)=>{const n=a.pts[(k+1)%a.pts.length],q=M.toScreen((p[0]+n[0])/2,(p[1]+n[1])/2),d=Math.hypot(q.x-x,q.y-y);if(d<bd){bd=d;best=k}});
  if(best>=0)return {t:'m',k:best};
  return null;
}
function mapPointer(){
  const el=M.el.map,ptrs=new Map();let pan=null,pinch=null,moved=false,t0=0,drag=null;
  const pos=e=>{const r=el.getBoundingClientRect();return {x:e.clientX-r.left,y:e.clientY-r.top}};
  const dist=()=>{const a=Array.from(ptrs.values());return Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y)};
  const mid=()=>{const a=Array.from(ptrs.values());return {x:(a[0].x+a[1].x)/2,y:(a[0].y+a[1].y)/2}};
  const rd=v=>Math.round(v*1e6)/1e6;
  el.addEventListener('pointerdown',e=>{
    try{el.setPointerCapture(e.pointerId)}catch(x){}
    ptrs.set(e.pointerId,pos(e));
    if(ptrs.size===1){
      const p=ptrs.get(e.pointerId);pan={x:p.x,y:p.y,lat:M.lat,lon:M.lon};moved=false;t0=Date.now();drag=null;
      const h=mapHit(p.x,p.y);if(h&&h.t!=='first')drag={t:h.t,k:h.k,done:false,orig:null};
    }else if(ptrs.size===2){pinch={d:dist()};pan=null;drag=null;moved=true}
  });
  el.addEventListener('pointermove',e=>{
    if(!ptrs.has(e.pointerId))return;ptrs.set(e.pointerId,pos(e));
    if(ptrs.size===2&&pinch){const d=dist(),r=d/pinch.d,m=mid();if(r>1.6){M.zoom(1,m.x,m.y);pinch.d=d}else if(r<0.62){M.zoom(-1,m.x,m.y);pinch.d=d}return}
    if(!pan)return;const p=ptrs.get(e.pointerId),dx=p.x-pan.x,dy=p.y-pan.y;
    if(!moved&&Math.hypot(dx,dy)>6)moved=true;
    if(!moved)return;
    if(drag){
      const a=B.cfg.zone.zones[M.sel];if(!a)return;
      if(drag.t==='m'&&!drag.done){                           // arrastrar el círculo del medio de un lado: nace un punto nuevo ahí
        const k=drag.k,n=a.pts[(k+1)%a.pts.length];a.pts.splice(k+1,0,[(a.pts[k][0]+n[0])/2,(a.pts[k][1]+n[1])/2]);
        drag={t:'v',k:k+1,done:true,orig:null,added:true};M.vsel=k+1;
      }
      if(!drag.orig)drag.orig=a.pts[drag.k].slice();
      const c=M.fromScreen(p.x,p.y);a.pts[drag.k]=[rd(c.lat),rd(c.lon)];M.vsel=drag.k;
      M.bad=crosses(a.pts,true);
    }else{const nlon=lonAt(wx(pan.lon,M.z)-dx,M.z),nlat=latAt(wy(pan.lat,M.z)-dy,M.z);M.lon=nlon;M.lat=Math.max(-84,Math.min(84,nlat))}
    M.redraw();
  });
  const up=e=>{
    if(!ptrs.has(e.pointerId))return;
    const p=ptrs.get(e.pointerId);
    if(ptrs.size===1&&drag&&moved&&drag.orig){                // terminó de arrastrar un punto
      const a=B.cfg.zone.zones[M.sel];
      if(a&&crosses(a.pts,true)){
        if(drag.added)a.pts.splice(drag.k,1);else a.pts[drag.k]=drag.orig;
        M.vsel=drag.added?-1:drag.k;mapWarn('La zona no puede cruzarse consigo misma: el punto ha vuelto a su sitio.');
      }
      M.bad=false;syncList();mapPanel();M.redraw();
    }else if(ptrs.size===1&&!moved&&Date.now()-t0<700&&e.type==='pointerup')mapTap(p.x,p.y);
    ptrs.delete(e.pointerId);if(ptrs.size<2)pinch=null;if(ptrs.size===0){pan=null;drag=null}
  };
  el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);
  el.addEventListener('wheel',e=>{e.preventDefault();const p=pos(e);M.zoom(e.deltaY<0?1:-1,p.x,p.y)},{passive:false});
}
function mapTap(x,y){
  const g=B.cfg.zone.zones,h=mapHit(x,y);
  if(M.mode==='draw'){
    if(h&&h.t==='first'){mapClose();return}
    const c=M.fromScreen(x,y),pt=[Math.round(c.lat*1e6)/1e6,Math.round(c.lon*1e6)/1e6];
    if(M.draft.length>=MAXPT){mapWarn('Hay un máximo de '+MAXPT+' puntos por zona.');return}
    if(crosses(M.draft.concat([pt]),false)){mapWarn('Ese punto haría que la zona se cruce consigo misma: ponlo en otro sitio.');return}
    mapWarn('');M.draft.push(pt);mapPanel();M.redraw();return;
  }
  if(h&&h.t==='v'){M.select(M.sel,h.k);return}
  if(h&&h.t==='m'){
    const a=g[M.sel],k=h.k,n=a.pts[(k+1)%a.pts.length];
    if(a.pts.length>=MAXPT){mapWarn('Hay un máximo de '+MAXPT+' puntos por zona.');return}
    a.pts.splice(k+1,0,[Math.round((a.pts[k][0]+n[0])/2*1e6)/1e6,Math.round((a.pts[k][1]+n[1])/2*1e6)/1e6]);syncList();M.select(M.sel,k+1);return;
  }
  const c=M.fromScreen(x,y);let best=-1,ba=1e18;                // la zona más pequeña que contiene el punto
  g.forEach((a,i)=>{if(inPoly(a.pts,c.lat,c.lon)){const ar=polyArea(a.pts);if(ar<ba){ba=ar;best=i}}});
  M.select(best,-1);
}
/* el mapa cambia de alto cuando cambia el panel de abajo (dibujando / zona elegida / nada): se vuelve a medir y lo que se ve se queda en su sitio (se ancla la esquina de arriba a la izquierda) */
function mapResize(){
  if(!M.open||!M.el)return;
  const r=M.el.map.getBoundingClientRect(),w=Math.round(r.width),h=Math.round(r.height);
  if(!(w>0&&h>0)||(w===M.w&&h===M.h))return;
  if(M.w>0&&M.h>0){M.lon=lonAt(wx(M.lon,M.z)+(w-M.w)/2,M.z);M.lat=Math.max(-84,Math.min(84,latAt(wy(M.lat,M.z)+(h-M.h)/2,M.z)))}
  M.w=w;M.h=h;M.redraw();
}
M.close=function(force){
  if(!M.open)return;
  if(M.mode==='draw'&&M.draft&&M.draft.length&&!force){
    if(M.draft.length>=3&&!crosses(M.draft,true)){mapClose()}
    else if(!confirm('Hay una zona sin cerrar ('+M.draft.length+(M.draft.length===1?' punto':' puntos')+'). ¿Salir y descartarla?'))return;
  }
  M.open=false;window.removeEventListener('resize',mapResize);if(M.ro){try{M.ro.disconnect()}catch(e){}M.ro=null}clearTimeout(M.wt);
  const o=document.getElementById('zmap');if(o)o.remove();
  for(const i of M.tiles.values())i.remove();M.tiles.clear();M.el=null;M.draft=null;M.mode='view';M.vsel=-1;M.bad=false;
  renderZones();
};
/* mode: 'draw' = empieza a dibujar una zona nueva · otro = ver las zonas; idx = zona que se deja elegida */
window.boltMap=function(mode,idx){
  if(M.open){if(mode==='draw')mapStartDraw();else if(typeof idx==='number'&&B.cfg.zone.zones[idx]){M.mode='view';M.draft=null;M.fit(idx);M.select(idx,-1)}return}
  try{
    const o=document.createElement('div');o.id='zmap';o.className='zm';o.setAttribute('role','dialog');o.setAttribute('aria-label','Mapa de zonas buenas');
    o.innerHTML='<div class="zm-top"><b>🗺 Zonas buenas</b><span class="zm-info" id="zm_info"></span><span class="zm-sp"></span><button type="button" id="zm_in" aria-label="Acercar">＋</button><button type="button" id="zm_out" aria-label="Alejar">－</button><button type="button" class="zm-done" id="zm_done">✔ Listo</button></div>'
     +'<div class="zm-map" id="zm_map"><div class="zm-tiles" id="zm_tiles"></div><svg class="zm-svg" id="zm_svg" xmlns="http://www.w3.org/2000/svg"></svg><div class="zm-msg" id="zm_msg"></div><div class="zm-warn" id="zm_warn"></div><div class="zm-attr" id="zm_attr"></div></div>'
     +'<div class="zm-bot" id="zm_bot"></div>';
    document.body.appendChild(o);
    M.el={root:o,map:o.querySelector('#zm_map'),tiles:o.querySelector('#zm_tiles'),svg:o.querySelector('#zm_svg'),msg:o.querySelector('#zm_msg'),warn:o.querySelector('#zm_warn'),attr:o.querySelector('#zm_attr'),bot:o.querySelector('#zm_bot'),info:o.querySelector('#zm_info')};
    M.open=true;M.sel=-1;M.vsel=-1;M.me=null;M.ok=0;M.err=0;M.gone=false;M.src=0;M.bad=false;
    M.mode=mode==='draw'?'draw':'view';M.draft=mode==='draw'?[]:null;
    const has=typeof idx==='number'&&B.cfg.zone.zones[idx];
    if(has)M.sel=idx;
    mapPanel();                                                   // primero el panel de abajo: de él depende el alto del mapa
    const r=M.el.map.getBoundingClientRect();M.w=Math.round(r.width)||360;M.h=Math.round(r.height)||400;
    M.fit(has?idx:null);
    o.querySelector('#zm_in').onclick=()=>M.zoom(1);o.querySelector('#zm_out').onclick=()=>M.zoom(-1);o.querySelector('#zm_done').onclick=()=>M.close();
    mapPointer();M.redraw();
    window.addEventListener('resize',mapResize);
    if(window.ResizeObserver){try{M.ro=new ResizeObserver(()=>mapResize());M.ro.observe(M.el.map)}catch(e){M.ro=null}}
  }catch(e){console.warn('mapa de zonas',e);M.open=false;const o=document.getElementById('zmap');if(o)o.remove();alert('No se pudo abrir el mapa. Puedes cambiar los nombres de las zonas en la lista.')}
};
window.boltMapEdit=function(i){window.boltMap('view',i)};

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
  if(e)e[4]='Es un aviso que salta arriba cuando te llega una oferta de Bolt, Uber o Cabify. Cada dato (€/hora, €/km y distancia de recogida) sale con su color: verde si cumple tu objetivo, naranja si se queda un poco corto y rojo si está lejos. Arriba del todo: ACEPTAR si todo está bien, RECHAZAR si algo está muy mal, y A VALORAR si está justo. Se activa en Ajustes → Rentabilidad de viajes. La oferta de Bolt no muestra el precio: la app lo ESTIMA con tus tarjetas de precios (cuatro: normal y aeropuerto, cada una para entre semana y para fin de semana; la de fin de semana se usa en las franjas que tú defines) y te dice bruto, comisión y NETO estimados, en pantalla y por voz. Son estimaciones tuyas, no tarifas oficiales de Bolt: los valores se corrigen en Ajustes → Rentabilidad de viajes → Estimación del precio de Bolt. En Uber la app lee una captura de la pantalla (dentro del móvil, sin guardarla). Solo avisa: no pulsa nada por ti.';
  J_KB.push(['boltzonas','📍','Zonas buenas de Bolt','zona buena^8,zonas buenas^8,dibujar zona^8,poligono^7,mapa zonas^8,marcar zonas^7,zona bolt^6,descuento bolt^5,8 por ciento^4,m30 bolt^5,sur bolt^4,demanda desde 1,4^6,ubicacion bolt^5,probar ubicacion^6,mover punto^6,borrar punto^6,borrar zona^6,ajuste por zona^7,gps bolt^6','El ajuste por zona corrige el precio estimado de Bolt según dónde estés (la app mira la ubicación del móvil), solo en los viajes normales: el aeropuerto no lo usa. Fuera de zona buena (M30, sur…): sin demanda o con menos de ×1,2 → tarifa −8 %; de ×1,2 a ×1,3 → tarifa real; desde ×1,4 → tarifa × demanda, y desde ×1,5 sube un 5 %, desde ×2 un 8 % y desde ×2,5 un 10 % (cada escalón sustituye al anterior). En zona buena → tarifa +12 % × la demanda tal como salga (el 12 % se puede cambiar, también a 0). Las zonas buenas las dibujas tú como polígonos: Ajustes → Rentabilidad de viajes → Estimación del precio de Bolt → «Dibujar zona nueva». Tocas el mapa para ir poniendo puntos alrededor de la zona (arrastras para mover el mapa, ＋/－ o pellizcar para acercar) y la cierras tocando el punto 1 (el verde) o con «Cerrar zona». Para cambiar una zona la tocas: arrastras un punto blanco para moverlo, tocas un punto y «Borrar punto» (mínimo 3), tocas el círculo pequeño del medio de un lado para añadir un punto, o «Borrar zona». Una zona no puede cruzarse consigo misma. Al principio no hay ninguna zona. «Probar ubicación» dice dónde cree la app que estás y qué ve el lector de pantalla. Si el móvil no da la ubicación (sin permiso o sin datos recientes) se usa el ajuste de fuera de zona buena y el aviso lo dice. Las imágenes del mapa necesitan internet; sin internet las zonas se ven igual sobre un fondo liso. Son estimaciones, no tarifas oficiales de Bolt.']);
  J_KB.push(['boltestimacion','💶','Precio estimado de Bolt','tarjetas bolt^7,tarjeta aeropuerto^7,tarjeta normal^7,franjas^8,franja fin de semana^8,fin de semana bolt^6,entre semana bolt^6,aeropuerto bolt^6,tasa aeropuerto^6,precio bolt^6,estimar bolt^7,estimacion bolt^7,neto bolt^6,neto estimado^7,bolt no muestra el precio^8,tarifa bolt^5,comision bolt^5,bruto estimado^6,voz bolt^5,demanda^4,festivos bolt^5,minima aeropuerto^6','Bolt no enseña el precio en la oferta, así que la app lo estima con cuatro tarjetas de precios que editas en Ajustes → Rentabilidad de viajes → Estimación del precio de Bolt: tarjeta normal y tarjeta del aeropuerto, cada una para entre semana y para fin de semana, con su inicial, su precio por km, su precio por minuto y su mínima. Al principio la normal es 2,10 + 0,77 €/km + 0,15 €/min (mínima 6,75 €) y la del aeropuerto 2,89 + 0,82 €/km + 0,15 €/min (mínima 13,50 €). Qué tarjetas se usan lo deciden las franjas de fin de semana que tú defines (una sola lista para las dos: por defecto de viernes 18:00 a domingo 06:00; puedes añadir, cambiar y borrar franjas); los festivos cuentan como fin de semana todo el día. Manda la hora a la que llega la oferta, no el día del calendario: si cae en una franja se usan los precios de fin de semana aunque sea lunes. Bruto = inicial + km × precio + minutos × precio, nunca menos que la mínima; le quita la comisión (25 % al principio) y te da el NETO estimado, en pantalla y por voz. El aeropuerto (recogida en «parking P1 de la T1», «parking express T2», «parking módulo D … T4», o viaje hacia «Terminal 1–4», «Aeropuerto» o «Avenida de la Hispanidad») usa la tarjeta del aeropuerto: la demanda multiplica todo, incluida la mínima, no lleva ajuste de zona, y SIEMPRE se resta primero la tasa de 2,57 € (el precio de Bolt ya la incluye) y sobre lo que queda se aplica la comisión. Por ejemplo, 13 km y 20 min entre semana sin demanda: 2,89 + 13 × 0,82 + 20 × 0,15 = 16,55 €; menos la tasa 2,57 € = 13,98 €; comisión 25 % = 3,50 €; neto 10,49 €. Son estimaciones, no tarifas oficiales: todos los valores se cambian en esa pantalla, donde también hay un simulador para contrastarlas con viajes reales.']);
}catch(e){}
// al abrir: si el teléfono perdió los ajustes de Bolt y la cuenta los tiene, se recuperan; y la cuenta guarda una copia
setTimeout(async()=>{
  try{
    const sr=SR();if(!sr)return;
    const before=snap(),fresh=await load(true);
    if(fresh&&snap()!==before){const b=document.getElementById('bz_body');if(b&&!errors.size){b.innerHTML=bodyHtml();afterBody()}}
    if(B.saved&&db&&db.settings&&!db.settings.boltCfg){mirrorToDb(JSON.stringify(B.cfg));P.saveNow()}
  }catch(e){}
},1500);
})();
'''),
    ('65_tips.js', r'''/* ===================== v3.15g · PROPINA EN LA LISTA DE VIAJES =====================
   En la lista de viajes del día (Calculadora y Facturación → Diario) el importe de un viaje con propina sale YA SUMADO: «38,90 € → 29,25 €» y debajo
   «🎁 27,25 € + 2,00 € propina» (el neto del viaje más la propina; va en un <span class="tipsum">). Los totales no cambian: la propina se suma UNA sola vez
   (día = neto de los viajes + propinas; por plataforma = neto + propina) y nunca paga comisión. Esto solo cambia cómo se ve la fila. */
(function(){
const P=window.PDC314;if(!P||P.tipsList)return;P.tipsList=true;
const euroF=v=>{try{return euro(v)}catch(e){return (Math.round(v*100)/100).toFixed(2).replace('.',',')+' €'}};
const calcF=v=>{try{return (typeof moneyDisplay==='function'&&typeof dailyBillingHidden!=='undefined')?moneyDisplay(v,dailyBillingHidden):euroF(v)}catch(e){return euroF(v)}};
function decorate(root){
  if(!root)return;
  let trips;try{trips=db.trips||[]}catch(e){return}
  for(const row of root.querySelectorAll('.trip:not(.canc)')){
    if(row.getAttribute('data-tip-sum'))continue;
    const b=row.querySelector('button[onclick^="addTripTip("]');if(!b)continue;
    const m=/^addTripTip\('([^']*)','([^']*)'/.exec(b.getAttribute('onclick')||'');if(!m)continue;
    const t=trips.find(x=>String(x.id)===m[1]);if(!t)continue;
    const tip=Math.max(0,Number(t.tip)||0);if(!(tip>0))continue;
    const orig=row.querySelector('.orig'),small=orig&&orig.querySelector('small');if(!orig||!small)continue;
    const F=m[2]==='billing'?euroF:calcF,net=Number(t.net)||0,P1=euroF(net),P2=euroF(net+tip);
    const kids=Array.from(orig.childNodes).filter(n=>n.nodeName!=='SMALL');
    const ai=kids.findIndex(n=>n.nodeType===3&&n.data.indexOf('→')>=0);if(ai<0)continue;
    const an=kids[ai],ix=an.data.indexOf('→'),after=an.data.slice(ix+1).replace(/^\s+/,'');
    if(after.indexOf(P1)===0)an.data=an.data.slice(0,ix+1)+' '+P2+after.slice(P1.length);
    else{const sp=kids[ai+1];if(sp&&sp.nodeType===1&&sp.textContent===P1)sp.textContent=P2;else continue}      // con los importes ocultos cada cifra va en su span
    // la línea original es un <small> que el diseño de la lista oculta con !important; la suma va en un <span class="tipsum"> que sí se ve
    const sp=document.createElement('span');sp.className='tipsum';sp.innerHTML='🎁 '+F(net)+' + '+F(tip)+' propina';
    small.replaceWith(sp);
    row.setAttribute('data-tip-sum','1');
  }
  for(const n of root.querySelectorAll('.note')){
    if(n.getAttribute('data-tip-note')||!/^\s*🎁\s*Propinas del día/.test(n.textContent))continue;
    n.setAttribute('data-tip-note','1');
    n.insertAdjacentHTML('beforeend',' <small style="color:#9fb4c8">· ya incluidas en el total, una sola vez</small>');
  }
}
P.decorateTips=decorate;
const _rc=window.renderCalc;
if(typeof _rc==='function')window.renderCalc=function(){const r=_rc.apply(this,arguments);try{decorate(document)}catch(e){console.warn('v3.15 propina',e)}return r};
const _rb=window.renderBilling;
if(typeof _rb==='function')window.renderBilling=function(){const r=_rb.apply(this,arguments);try{decorate(document)}catch(e){console.warn('v3.15 propina',e)}return r};
try{decorate(document)}catch(e){}
})();
'''),
    ('70_settings.js', r'''/* ===================== v3.15 · AJUSTES: «Rentabilidad de viajes» como opción propia =====================
   · En la pantalla principal de Ajustes aparece una tercera opción, junto a «Cuenta» y «Configuración de la app».
   · La pantalla de Rentabilidad (con su flecha ←) reúne todo en desplegables: objetivos, burbuja flotante, semáforos, estimación de Bolt,
     opciones avanzadas, estado de la lectura, diagnóstico, prueba del aviso y cómo se calcula.
   · Las tarjetas que estaban sueltas en Ajustes (rentabilidad, burbuja, semáforos, diagnóstico) se ocultan allí (siguen existiendo para que
     los módulos antiguos no las vuelvan a crear) y su contenido vive ahora dentro de Rentabilidad, con las mismas funciones. */
(function(){
const P=window.PDC314;if(!P||P.settings315)return;P.settings315=true;
const SR=()=>{try{if(window.Capacitor&&Capacitor.isNativePlatform&&Capacitor.isNativePlatform())return (Capacitor.Plugins&&Capacitor.Plugins.ScreenReader)||Capacitor.registerPlugin('ScreenReader')}catch(e){}return null};
const SUM='cursor:pointer;font-weight:800';
/* aviso pequeño (el de la lectura de pantalla está dentro de otro módulo y no se ve desde aquí): mismo aspecto, mismo elemento */
P.say=function(msg){
  try{
    let t=document.getElementById('srToast');
    if(!t){t=document.createElement('div');t.id='srToast';t.style.cssText='position:fixed;left:50%;bottom:90px;transform:translateX(-50%);max-width:90%;background:#0b1a33;color:#fff;border:1px solid #3b82f6;border-radius:14px;padding:12px 16px;z-index:99999;font:600 15px system-ui;text-align:center';document.body.appendChild(t)}
    t.textContent=msg;t.style.display='block';clearTimeout(t._h);t._h=setTimeout(()=>{t.style.display='none'},3500);
  }catch(e){}
};

/* ---------- pantalla principal de Ajustes ---------- */
function addRentOption(){
  const menu=document.querySelector('#content .settings-menu');
  if(!menu||menu.querySelector('.settings-option.rentopt'))return;
  menu.insertAdjacentHTML('beforeend','<button class="settings-option rentopt" onclick="renderRent()"><span class="ico">🚦</span><span><b>Rentabilidad de viajes</b><small id="rentOptState">Avisos de ofertas, burbuja, semáforos, estimación de Bolt y diagnóstico</small></span><span style="margin-left:auto;font-size:24px;color:#7b8794">›</span></button>');
  try{
    const sr=SR();
    if(sr&&sr.getRent)sr.getRent().then(c=>{const s=document.getElementById('rentOptState');if(s&&c&&typeof c.on==='boolean')s.textContent=(c.on?'Activada':'Desactivada')+' · avisos de ofertas, burbuja, semáforos y estimación de Bolt'}).catch(()=>{});
  }catch(e){}
}
const _rs=window.renderSettings;
if(typeof _rs==='function')window.renderSettings=function(){
  const r=_rs.apply(this,arguments);
  try{addRentOption()}catch(e){console.warn('v3.15 ajustes',e)}
  return r;
};

/* ---------- pantalla de Rentabilidad con desplegables ---------- */
function toDetails(el,icon,title,open){
  if(!el)return null;
  const d=document.createElement('details');
  d.className='note rt-sec';d.setAttribute('data-rt','1');d.style.cssText=el.style.cssText||'margin:12px 0';
  if(open)d.open=true;
  const s=document.createElement('summary');s.style.cssText=SUM;s.textContent=icon+' '+title;d.appendChild(s);
  const first=el.querySelector(':scope > b');
  if(first){const nx=first.nextSibling;first.remove();if(nx&&nx.nodeName==='BR')nx.remove()}      // el título pasa a ser el de la cabecera del desplegable
  while(el.firstChild)d.appendChild(el.firstChild);
  if(el.id)d.id=el.id;                                                                          // otros módulos buscan estas cajas por su id
  el.replaceWith(d);
  return d;
}
function mkSection(id,icon,title,html){
  const d=document.createElement('details');d.className='note rt-sec';d.id=id;d.setAttribute('data-rt','1');d.style.cssText='margin:12px 0';
  d.innerHTML='<summary style="'+SUM+'">'+icon+' '+title+'</summary>'+html;
  return d;
}
function bubbleHtml(){
  return '<div class="rt-row"><div><b>Mostrar la burbuja</b><br><small>Para el móvil: aparece sobre Bolt/Uber/Cabify y al tocarla lee el precio y abre el Portal.</small></div><input type="checkbox" id="srBubbleChk" style="width:26px;height:26px;flex:none"></div><div class="rt-off" id="srBubbleOff"></div>';
}
function thrHtml(){
  const inp='style="width:90px;text-align:right" inputmode="decimal"';
  return '<small>Verde si cumple tu objetivo, naranja si va un poco por debajo (15 %), rojo si queda lejos. En la recogida, naranja hasta un 40 % más de km.</small>'
    +'<div style="display:grid;grid-template-columns:1fr auto;gap:8px 12px;align-items:center;margin-top:10px">'
    +'<span>Objetivo € / hora</span><input id="srThH" '+inp+'><span>Objetivo € / km</span><input id="srThK" '+inp+'><span>Recogida máxima (km)</span><input id="srThP" '+inp+'></div><div class="rt-off" id="srThrOff"></div>';
}
function diagHtml(){
  return '<small>Mira qué le pasa a tu móvil.</small><div class="row" style="margin-top:8px;gap:8px"><button class="secondary" style="flex:1" onclick="bubbleDiagShow()">🔎 Diagnóstico</button><button class="secondary" style="flex:1" onclick="bubbleTest()">Probar 6 s</button></div>'
    +'<button class="secondary" style="width:100%;margin-top:8px" onclick="renderReadDiag()">📋 Último texto leído</button>';
}
function initBubble(){
  const chk=document.getElementById('srBubbleChk');if(!chk)return;
  const sr=SR();
  if(!sr){chk.disabled=true;const o=document.getElementById('srBubbleOff');if(o)o.textContent='Solo funciona en el móvil con la app instalada.';return}
  sr.getBubble().then(r=>{chk.checked=!!(r&&r.enabled)}).catch(()=>{});
  chk.onchange=()=>{sr.setBubble({enabled:chk.checked}).catch(()=>{})};
}
function initThr(){
  const H=document.getElementById('srThH'),K=document.getElementById('srThK'),Pk=document.getElementById('srThP');if(!H||!K||!Pk)return;
  const sr=SR();
  if(!sr){[H,K,Pk].forEach(e=>{e.disabled=true});const o=document.getElementById('srThrOff');if(o)o.textContent='Solo funciona en el móvil con la app instalada.';return}
  const f=(n,d)=>Number(n).toFixed(d).replace('.',',').replace(/,0+$/,'').replace(/(,\d)0$/,'$1');
  sr.getThresholds().then(r=>{if(r&&r.eurH!=null){H.value=f(r.eurH,2);K.value=f(r.eurKm,2);Pk.value=f(r.pickKm,1)}}).catch(()=>{});
  const num=el=>{const n=Number(String(el.value).replace(',','.'));return Number.isFinite(n)&&n>0?n:null};
  const save=()=>{const h=num(H),k=num(K),p=num(Pk);if(h&&k&&p)sr.setThresholds({eurH:h,eurKm:k,pickKm:p}).then(()=>{P.say('Objetivos guardados')}).catch(()=>{})};
  [H,K,Pk].forEach(el=>{el.onchange=save});
}
const bText=el=>((el.querySelector(':scope > b')||{}).textContent||'').trim();
function restructureRent(){
  const root=document.querySelector('#content');
  if(!root||!document.getElementById('rOn')||root.querySelector('[data-rt]'))return;
  const panel=document.getElementById('rOn').closest('section')||root;
  const kids=[...panel.children];
  const note=re=>kids.find(e=>e.classList&&e.classList.contains('note')&&re.test(bText(e)));
  const obj=toDetails(note(/^Tus objetivos$/),'🎯','Tus objetivos',true);
  const est=toDetails(document.getElementById('rStatBox'),'👀','Estado de la lectura',false);
  const tst=toDetails(note(/^Probar el aviso$/),'🧪','Probar el aviso',false);
  const how=toDetails(note(/^C.mo se calcula$/),'ℹ️','Cómo se calcula',false);
  const adv=[...panel.querySelectorAll(':scope > details.note')].find(d=>!d.hasAttribute('data-rt')&&/^\s*Opciones avanzadas/.test((d.querySelector('summary')||{}).textContent||''));
  if(adv){adv.classList.add('rt-sec');adv.setAttribute('data-rt','1');const sm=adv.querySelector('summary');if(sm&&sm.textContent.indexOf('⚙')<0)sm.textContent='⚙️ '+sm.textContent.trim()}
  const bub=mkSection('rtBubble','🫧','Burbuja flotante',bubbleHtml());
  const thr=mkSection('rtThr','🚦','Semáforos de viajes',thrHtml());
  const dg=mkSection('rtDiag','🔎','¿No te sale la burbuja? Diagnóstico',diagHtml());
  if(obj){obj.insertAdjacentElement('afterend',bub);bub.insertAdjacentElement('afterend',thr)}
  else{const anchor=document.getElementById('rOn').closest('.note');if(anchor){anchor.insertAdjacentElement('afterend',bub);bub.insertAdjacentElement('afterend',thr)}}
  const save=panel.querySelector('button[onclick="rentSave()"]');
  if(save){                                              // primero lo que se ajusta, luego «Guardar», y debajo las herramientas
    if(est)save.insertAdjacentElement('afterend',est);
    (est||save).insertAdjacentElement('afterend',dg);
  }else if(est)est.insertAdjacentElement('afterend',dg);
  else panel.appendChild(dg);
  initBubble();initThr();
}
P.restructureRent=restructureRent;
const _rr=window.renderRent;
if(typeof _rr==='function')window.renderRent=async function(){
  const r=await _rr.apply(this,arguments);
  try{restructureRent()}catch(e){console.warn('v3.15 rentabilidad',e)}
  return r;
};

/* ---------- ayuda ---------- */
try{
  const e=jEntry('rentabilidad');
  if(e)e[4]=String(e[4]).replace('Se activa en Ajustes → Rentabilidad de viajes.','Se activa en Ajustes → Rentabilidad de viajes (es una opción propia, con desplegables: objetivos, burbuja flotante, semáforos, estimación de Bolt, opciones avanzadas, estado de la lectura y diagnóstico).');
}catch(e){}
})();
'''),
    ('80_perf.js', r'''/* ===================== v3.15 · VELOCIDAD DE LA APP: medidor + «Modo ligero» =====================
   · «Medir velocidad» (Ajustes → Configuración de la app): prueba en tu propio móvil/tableta cuánto tarda cada pantalla en prepararse (la app)
     y en dibujarse (el aparato), cuánta fluidez hay al deslizar y una pequeña prueba de potencia del procesador que sirve para saber si el
     aparato va lento por calor o por otras apps (se compara con tu mejor medida guardada).
   · «Modo ligero»: quita sombras, brillos, desenfoques y animaciones. No cambia ningún dato ni ningún cálculo; solo el dibujo.
   Nada de esto se sincroniza con la nube: es una preferencia de cada aparato. */
(function(){
const P=window.PDC314;if(!P||P.perf315)return;P.perf315=true;
const KL='pdc_lite',KH='pdc_perf_hist';
const lsGet=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
const lsSet=(k,v)=>{try{localStorage.setItem(k,v);return true}catch(e){return false}};
const isLite=()=>lsGet(KL)==='1';
function applyLite(on){try{document.documentElement.classList.toggle('pdc-lite',!!on)}catch(e){}}
applyLite(isLite());
P.setLite=function(on){lsSet(KL,on?'1':'0');applyLite(on);return !!on};
P.isLite=isLite;

/* ---------- historial de mediciones (solo en este aparato) ---------- */
function hist(){try{const a=JSON.parse(lsGet(KH)||'[]');return Array.isArray(a)?a.filter(x=>x&&typeof x.bench==='number'):[]}catch(e){return []}}
function pushHist(r){const a=hist();a.push(r);while(a.length>12)a.shift();lsSet(KH,JSON.stringify(a))}

/* ---------- veredicto (función pura, probada con una tabla de casos) ---------- */
// r: {bench, bestBench, jsMax, paintMax, fps, lite}.  Devuelve {level:'ok'|'justa'|'lenta', lines:[...]}
P.perfVerdict=function(r){
  const L=[];let level='ok';
  const up=l=>{if(l==='lenta')level='lenta';else if(l==='justa'&&level==='ok')level='justa'};
  if(r.jsMax>150){up('lenta');L.push('La app tarda '+r.jsMax+' ms en preparar su pantalla más pesada: eso es cosa de la app (muchos datos). Envíame este resultado.')}
  else if(r.jsMax>60){up('justa');L.push('La app prepara sus pantallas en '+r.jsMax+' ms como máximo: es aceptable.')}
  else L.push('La app prepara sus pantallas rápido ('+r.jsMax+' ms como máximo). El código de la app no es el problema.');
  if(r.paintMax>200){up('lenta');L.push('Dibujar la pantalla cuesta '+r.paintMax+' ms: el aparato va justo de gráficos.'+(r.lite?'':' Prueba el «Modo ligero».'))}
  else if(r.paintMax>100){up('justa');L.push('Dibujar la pantalla tarda '+r.paintMax+' ms.'+(r.lite?'':' Si lo notas lento, prueba el «Modo ligero».'))}
  if(r.fps!=null){
    if(r.fps<30){up('lenta');L.push('Al deslizar va a '+r.fps+' imágenes por segundo (se nota a tirones).'+(r.lite?'':' El «Modo ligero» suele arreglarlo.'))}
    else if(r.fps<50){up('justa');L.push('Al deslizar va a '+r.fps+' imágenes por segundo.')}
  }
  if(r.bestBench>0&&r.bench>0){
    const q=r.bench/r.bestBench;
    if(q>=1.5){up('justa');L.push('El procesador va '+q.toFixed(1).replace('.',',')+' veces más lento que en tu mejor medida: el aparato está caliente o saturado (otras apps abiertas). Déjalo enfriar y cierra apps.')}
    else if(hist().length>1)L.push('El procesador va como en tu mejor medida: el aparato no está frenado por calor.');
  }
  return {level,lines:L};
};

/* ---------- prueba de potencia fija (no usa datos de la app) ---------- */
function benchOnce(){
  const t0=performance.now();let x=0;
  for(let i=1;i<=250000;i++){x+=Math.sqrt(i)*Math.sin(i)}
  const a=new Array(12000);for(let i=0;i<a.length;i++)a[i]=(i*7919)%10007;a.sort((p,q)=>p-q);
  const s=JSON.stringify(a.slice(0,2000));JSON.parse(s);
  return performance.now()-t0+(x===1.234?1:0);
}
P.perfBench=function(){if(typeof P.benchHook==='function')return P.benchHook();let m=1e9;for(let i=0;i<3;i++)m=Math.min(m,benchOnce());return Math.max(1,Math.round(m))};

/* ---------- medición ---------- */
const VIEWS=[['calc','Calculadora'],['control','Control'],['billing','Facturación'],['report','Informe'],['settings','Ajustes']];
const raf2=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r())));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function tabTime(v){
  const b=document.querySelector('.navbtn[data-view="'+v+'"]');
  const t0=performance.now();
  if(b)b.click();else if(typeof show==='function')show(v);
  const t1=performance.now();
  await raf2();
  return {js:Math.round(t1-t0),paint:Math.round(performance.now()-t0)};
}
async function scrollTest(){
  const el=document.scrollingElement||document.documentElement;
  const max=el.scrollHeight-window.innerHeight;
  if(!(max>300))return null;
  const dts=[];let last=performance.now();const y0=el.scrollTop;
  for(let i=0;i<40;i++){
    el.scrollTop=Math.round(max*(i<20?i/19:(39-i)/19));
    await new Promise(r=>requestAnimationFrame(r));
    const n=performance.now();dts.push(n-last);last=n;
  }
  el.scrollTop=y0;
  dts.shift();
  const avg=dts.reduce((a,b)=>a+b,0)/dts.length;
  return {fps:Math.round(1000/avg),worst:Math.round(Math.max.apply(null,dts))};
}
P.measureSpeed=async function(opts){
  opts=opts||{};
  const back=(document.querySelector('.navbtn.active')||{}).dataset;const backView=back&&back.view;
  const out={at:Date.now(),lite:isLite(),views:{}};
  out.bench=P.perfBench();
  for(const round of [1,2]){
    for(const [v] of VIEWS){
      const t=await tabTime(v);
      await sleep(80);
      if(round===2)out.views[v]=t;                 // la 1.ª vuelta calienta; se anota la 2.ª
    }
  }
  // fluidez al deslizar: en la pantalla que más pesa
  let best=null;
  for(const v of ['report','billing']){await tabTime(v);await sleep(60);const sct=await scrollTest();if(sct&&(!best||sct.fps<best.fps))best=sct}
  out.fps=best?best.fps:null;out.worst=best?best.worst:null;
  out.nodes=document.querySelectorAll('*').length;
  out.trips=(window.db&&db.trips&&db.trips.length)||0;
  const vs=Object.values(out.views);
  out.jsMax=Math.max.apply(null,vs.map(x=>x.js));out.paintMax=Math.max.apply(null,vs.map(x=>x.paint));
  const h0=hist();out.bestBench=h0.length?Math.min(out.bench,Math.min.apply(null,h0.map(x=>x.bench))):out.bench;
  out.verdict=P.perfVerdict(out);
  pushHist({t:out.at,bench:out.bench,jsMax:out.jsMax,paintMax:out.paintMax,fps:out.fps,lite:out.lite});
  if(opts.restore!==false){try{if(backView&&typeof show==='function')show(backView)}catch(e){}}
  return out;
};
function reportText(o){
  const d=new Date(o.at),p2=n=>String(n).padStart(2,'0');
  const L=['Velocidad de la app · '+p2(d.getDate())+'/'+p2(d.getMonth()+1)+'/'+d.getFullYear()+' '+p2(d.getHours())+':'+p2(d.getMinutes())+(o.lite?' · Modo ligero':'')];
  for(const [v,n] of VIEWS){const t=o.views[v];if(t)L.push(n.padEnd(12)+' app '+String(t.js).padStart(4)+' ms · dibujo '+String(t.paint).padStart(4)+' ms')}
  L.push('Deslizar: '+(o.fps==null?'sin pantalla larga para medir':o.fps+' imág./s (peor imagen '+o.worst+' ms)'));
  L.push('Procesador: '+o.bench+' ms (tu mejor medida: '+o.bestBench+' ms)');
  L.push('Viajes: '+o.trips+' · elementos en pantalla: '+o.nodes);
  L.push('Resultado: '+({ok:'FLUIDA',justa:'JUSTA',lenta:'LENTA'})[o.verdict.level]);
  return L.join('\n');
}
P.perfReportText=reportText;

/* ---------- ventana de resultados ---------- */
function closeModal(){const m=document.getElementById('perfModal');if(m)m.remove()}
function showModal(inner){
  let m=document.getElementById('perfModal');
  if(!m){m=document.createElement('div');m.id='perfModal';m.style.cssText='position:fixed;inset:0;z-index:99999;background:#000c;display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box';document.body.appendChild(m)}
  m.innerHTML='<div style="background:#0f2236;border:1px solid #2f6fa3;border-radius:18px;padding:16px;max-width:460px;width:100%;max-height:90vh;overflow:auto;color:#eaf4ff;box-sizing:border-box">'+inner+'</div>';
  return m;
}
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let running=false;
window.perfMeasure=async function(){
  if(running)return;running=true;
  const back=(document.querySelector('.navbtn.active')||{}).dataset;const backView=(back&&back.view)||'settings';
  showModal('<b style="font-size:17px">⚡ Midiendo…</b><p style="margin:10px 0 0;line-height:1.5">No toques la pantalla. Va a pasar por todas las pestañas (unos 10 segundos).</p>');
  let o;
  try{o=await P.measureSpeed({restore:false})}
  catch(e){running=false;showModal('<b>No se pudo medir</b><p style="margin:10px 0">'+esc(e&&e.message||e)+'</p><button class="secondary" style="width:100%" onclick="perfClose()">Cerrar</button>');return}
  running=false;
  window.__perfLast=o;
  const col={ok:'#22c55e',justa:'#f59e0b',lenta:'#ef4444'}[o.verdict.level],ttl={ok:'Va fluida',justa:'Va justa',lenta:'Va lenta'}[o.verdict.level];
  const rows=VIEWS.map(([v,n])=>{const t=o.views[v];return '<tr><td>'+n+'</td><td style="text-align:right">'+t.js+' ms</td><td style="text-align:right">'+t.paint+' ms</td></tr>'}).join('');
  showModal('<b style="font-size:18px;color:'+col+'">⚡ '+ttl+'</b>'
    +'<table style="width:100%;margin:10px 0;font-size:14px;border-collapse:collapse"><tr style="color:#9fb4c8"><td></td><td style="text-align:right">App</td><td style="text-align:right">Dibujo</td></tr>'+rows+'</table>'
    +'<div style="font-size:13px;color:#cfe3f5;line-height:1.45">Deslizar: <b>'+(o.fps==null?'—':o.fps+' imág./s')+'</b> · Procesador: <b>'+o.bench+' ms</b> <span style="color:#9fb4c8">(mejor: '+o.bestBench+' ms)</span></div>'
    +'<ul style="margin:10px 0 0;padding-left:18px;font-size:13px;line-height:1.5;color:#eaf4ff">'+o.verdict.lines.map(l=>'<li>'+esc(l)+'</li>').join('')+'</ul>'
    +'<p style="font-size:11px;color:#9fb4c8;margin:10px 0 0">«App» = lo que tarda la app en preparar la pantalla. «Dibujo» = hasta que se ve. Si miras esto con el aparato frío y luego caliente, compara el «Procesador».</p>'
    +'<div class="row" style="margin-top:12px;gap:8px">'
    +(o.lite?'':'<button class="secondary" style="flex:1" onclick="perfLiteOn()">Activar Modo ligero</button>')
    +'<button class="secondary" style="flex:1" onclick="perfCopy()">📋 Copiar</button></div>'
    +'<button class="action" style="width:100%;margin-top:8px" onclick="perfClose()">Cerrar</button>');
  P.perfBackView=backView;
};
window.perfClose=function(){
  closeModal();
  const v=P.perfBackView||'settings';P.perfBackView=null;
  try{show(v);if(v==='settings'&&typeof renderAppSettings==='function')renderAppSettings()}catch(e){}
};
window.perfCopy=async function(){
  const t=window.__perfLast?reportText(window.__perfLast):'';
  try{await navigator.clipboard.writeText(t);P.say('Copiado. Pégalo en Telegram.')}
  catch(e){const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();try{document.execCommand('copy')}catch(x){}ta.remove();P.say('Copiado')}
};
window.perfLiteOn=function(){P.setLite(true);const c=document.getElementById('perfLiteChk');if(c)c.checked=true;P.say('Modo ligero activado. Pulsa «Medir velocidad» otra vez para ver la diferencia.');closeModal();
  const v=P.perfBackView||'settings';P.perfBackView=null;try{show(v);if(v==='settings'&&typeof renderAppSettings==='function')renderAppSettings()}catch(e){}};

/* ---------- tarjeta dentro de «Configuración de la app» ---------- */
function lastLine(){const a=hist();if(!a.length)return 'Todavía no has medido.';const x=a[a.length-1],d=new Date(x.t),p2=n=>String(n).padStart(2,'0');
  return 'Última medida: '+p2(d.getDate())+'/'+p2(d.getMonth()+1)+' '+p2(d.getHours())+':'+p2(d.getMinutes())+' · procesador '+x.bench+' ms · pantalla más lenta '+x.paintMax+' ms'+(x.lite?' (Modo ligero)':'')}
function addPerfCard(){
  const head=document.querySelector('#content .settings-head .section-title');
  if(!head||!/Configuraci/.test(head.textContent)||document.getElementById('perfCard'))return;
  const panel=head.closest('section')||document.querySelector('#content');
  const c=document.createElement('details');c.id='perfCard';c.className='note rt-sec';c.style.cssText='margin:14px 0 10px';
  c.innerHTML='<summary style="cursor:pointer;font-weight:800">⚡ Velocidad de la app</summary>'
   +'<p style="margin:8px 0;line-height:1.5"><small>Si notas lento al cambiar de pestaña, mide aquí. Te dice si es la app o si es tu aparato (por calor o por tener muchas apps abiertas).</small></p>'
   +'<button class="action" style="width:100%" onclick="perfMeasure()">⏱ Medir velocidad</button>'
   +'<div id="perfLast" style="font-size:12px;color:#9fb4c8;margin:8px 0 0"></div>'
   +'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:12px;border-top:1px solid #ffffff22;padding-top:10px"><div><b>Modo ligero</b><br><small style="color:#9fb4c8">Quita sombras, brillos y animaciones para que el aparato trabaje menos y se caliente menos. No cambia tus datos ni los cálculos.</small></div><input type="checkbox" id="perfLiteChk" style="width:26px;height:26px;flex:none"></div>';
  panel.appendChild(c);
  const chk=document.getElementById('perfLiteChk');chk.checked=isLite();
  chk.onchange=()=>{P.setLite(chk.checked)};
  document.getElementById('perfLast').textContent=lastLine();
}
const _ras=window.renderAppSettings;
if(typeof _ras==='function')window.renderAppSettings=function(){
  const r=_ras.apply(this,arguments);
  try{addPerfCard()}catch(e){console.warn('v3.15 velocidad',e)}
  return r;
};
})();
''')
]
CSS = r'''/* ===================== v3.14 ===================== */
/* --- botón Cancelaciones junto a Aeropuerto --- */
/* Aeropuerto (verde, como Bolt) y Cancelaciones: MISMA altura que los botones Bolt/Uber/Cabify/Privados y cada uno ocupa dos de sus columnas.
   La altura y la separacion exactas las copia 20_cancel.js de los botones de plataforma (--pdc-bh y --pdc-bg); estos valores son solo el plan B. */
.airport-row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--pdc-bg,6px);align-items:stretch;margin-top:12px}
html body .airport-row>.airport-premium,html body .airport-row>.cancel-btn{box-sizing:border-box!important;position:relative!important;width:auto!important;min-width:0!important;margin:0!important;height:var(--pdc-bh,75px)!important;min-height:0!important;max-height:var(--pdc-bh,75px)!important;padding:6px 8px!important;display:flex!important;flex-direction:row!important;align-items:center!important;gap:7px!important;overflow:hidden!important;border-radius:14px!important}
html body .airport-row>.airport-premium{justify-content:flex-start!important;text-align:left!important;background:linear-gradient(130deg,#008c4a 0%,#00d66a 42%,#00f18b 100%)!important;border:1px solid #ffffffa8!important;box-shadow:0 0 0 1px #00f58b99,0 0 12px #00f58b99,0 6px 18px #00101d35,inset 0 1px 0 #ffffff70!important}
html body .airport-row>.airport-premium:before{content:"";position:absolute;z-index:-1;inset:3px 4px 50% 4px;border-radius:11px;border:0;background:linear-gradient(180deg,#ffffff38,#ffffff00);pointer-events:none}
html body .airport-row>.airport-premium:after{display:none!important}
html body .airport-row>.airport-premium .airport-plane{flex:0 0 auto!important;width:32px!important;height:32px!important;font-size:17px!important;background:linear-gradient(145deg,#ffffff35,#ffffff08)!important;border:1px solid #ffffff70!important;box-shadow:inset 0 1px 2px #ffffff44,0 0 9px #ffffff22!important;transform:none!important}
html body .airport-row>.airport-premium .airport-copy{flex:1 1 auto!important;min-width:0!important;max-width:100%!important;padding:0!important;gap:1px!important;align-items:flex-start!important;text-align:left!important;box-sizing:border-box!important}
html body .airport-row>.airport-premium .airport-copy strong{font-size:clamp(11.5px,3.3vw,15px)!important;white-space:normal!important;line-height:1.1!important;overflow-wrap:break-word;color:#fff!important;text-shadow:0 1px 3px #00101c99!important}
html body .airport-row>.airport-premium .airport-copy small{font-size:clamp(8.5px,2.4vw,11px)!important;white-space:normal!important;line-height:1.15!important;overflow-wrap:break-word;color:#fff!important;font-weight:800!important;text-shadow:0 1px 3px #00101c99!important;display:-webkit-box!important;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden}
html body .airport-row>.airport-premium .airport-add,html body .airport-row>.airport-premium .airport-luggage{display:none!important}
html body .airport-row>.airport-premium.pdc-has-chip .airport-copy{align-self:flex-start!important;padding-top:5px!important}
html body .airport-row>.airport-premium .pdc-fee-chip{position:absolute!important;right:5px!important;bottom:3px!important;top:auto!important;left:auto!important;margin:0!important;transform:scale(.7)!important;transform-origin:100% 100%!important;z-index:2!important;width:auto!important;max-width:none!important;flex:none!important}
html body .airport-row>.cancel-btn{justify-content:center!important;border:1px solid #ff9f73cc;background:linear-gradient(160deg,#3a120e 0%,#a3341d 55%,#34100c 100%);color:#fff;font-weight:900;font-size:clamp(11.5px,3.4vw,15px);line-height:1.1;letter-spacing:-.1px;text-align:center;box-shadow:0 0 14px #ff6a3d55,inset 0 1px 3px #ffffff44;cursor:pointer;touch-action:manipulation;-webkit-tap-highlight-color:transparent}
.cancel-btn:active{transform:scale(.97)}
.cancel-ico{flex:0 0 auto;display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;border:1px solid #ffb89a;background:radial-gradient(circle at 30% 20%,#ff7a4d,#7a1d0e 80%);font-size:16px;box-shadow:0 0 10px #ff6a3d77}
.cancel-txt{min-width:0;max-width:100%;white-space:nowrap}
@media(max-width:340px){html body .airport-row>.airport-premium,html body .airport-row>.cancel-btn{padding:6px 5px!important;gap:5px!important}.cancel-ico{width:26px;height:26px;font-size:14px}html body .airport-row>.airport-premium .airport-plane{width:28px!important;height:28px!important;font-size:15px!important}html body .airport-row>.cancel-btn{font-size:11px}}
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
/* ===================== v3.15 ===================== */
/* --- Ajustes: las tarjetas sueltas pasan dentro de «Rentabilidad de viajes» (se ocultan aquí; siguen existiendo para que los módulos antiguos no las vuelvan a crear) --- */
#rentCard,#bubbleDiagCard,#srBubbleCard,#srThrCard{display:none!important}
.rt-sec>summary{padding:2px 0}
.rt-sec[open]>summary{margin-bottom:8px}
.rt-row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.rt-off{color:#9fb4c8;font-size:12px;margin-top:6px}
.rt-off:empty{display:none}
/* --- Modo ligero (Ajustes → Configuración de la app → Velocidad de la app): sin sombras, brillos, desenfoques ni animaciones.
       La clase se repite para ganar a las reglas con !important del diseño; «.money-hidden» (ocultar importes) NO se toca. --- */
html.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite *,
html.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite *::before,
html.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite *::after{box-shadow:none!important;text-shadow:none!important;transition:none!important;animation:none!important;-webkit-backdrop-filter:none!important;backdrop-filter:none!important}
html.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite .header img,
html.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite .navbtn.active{filter:none!important}
html.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite.pdc-lite .header::before{display:none!important}

/* ---- v3.15f · tarifa por zona y mapa de zonas ---- */
#boltBox .bz-sub{display:block;margin:12px 0 2px;color:#cfe3f5}
#boltBox .bz-zone{border-top:2px solid #22c55e66}
#boltBox .bz-zone.bz-off>.bz-g,#boltBox .bz-zone.bz-off>.bz-hint,#boltBox .bz-zone.bz-off #bz_z_list{opacity:.5}
#boltBox .bz-ar{margin:8px 0;padding:8px;border:1px solid #ffffff2a;border-radius:14px;background:#ffffff0a}
#boltBox .bz-ar input.bz-an{width:100%;box-sizing:border-box;padding:9px 10px;border-radius:12px;font-size:15px;margin-bottom:6px}
#boltBox .bz-zb{display:grid;grid-template-columns:1fr;gap:8px;margin:10px 0}
#boltBox .bz-zb button{width:100%}
#boltBox .bz-zb button.secondary{padding:12px 14px;border-radius:14px;border:1px solid #ffffff33;background:#ffffff12;color:inherit;font-size:15px;font-weight:700;line-height:1.25}
#boltBox .bz-tsum{cursor:pointer;margin:12px 0 4px}
#boltBox .bz-tsum small{color:#9fb4c8;font-weight:500}
@media (min-width:600px){#boltBox .bz-zb{grid-template-columns:1fr 1fr}}
.zm{position:fixed;left:0;top:0;right:0;bottom:0;z-index:100000;background:#06121f;color:#e6f0fa;display:flex;flex-direction:column;font-family:inherit}
.zm-top{display:flex;align-items:center;gap:8px;padding:calc(env(safe-area-inset-top,0px) + 8px) 10px 8px;background:#0a1f33;border-bottom:1px solid #1e9dff55}
.zm-top button,.zm-bot button{border:1px solid #ffffff33;background:#ffffff14;color:#fff;border-radius:12px;padding:9px 12px;font-weight:800;font-size:14px}
.zm-top button.zm-done{background:#16a34a;border-color:#22c55e}
.zm-sp{flex:1}
.zm-info{font-size:11px;color:#9fb4c8}
.zm-map{position:relative;flex:1;min-height:200px;overflow:hidden;touch-action:none;background:#d6dde2;-webkit-user-select:none;user-select:none;cursor:grab}
.zm-tiles{position:absolute;left:0;top:0;right:0;bottom:0}
.zm-tile{position:absolute;left:0;top:0;width:256px;height:256px;max-width:none;pointer-events:none;-webkit-user-select:none;user-select:none}
.zm-svg{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none}
.zm-t{font:700 12px system-ui,sans-serif;fill:#0b2540;paint-order:stroke;stroke:rgba(255,255,255,.85);stroke-width:3px;text-anchor:middle}
.zm-me{fill:#2563eb;stroke:#fff;stroke-width:3}
.zm-ma{fill:rgba(37,99,235,.15);stroke:rgba(37,99,235,.5);stroke-width:1}
.zm-msg{position:absolute;left:10px;right:10px;top:10px;background:rgba(11,37,64,.92);color:#fde68a;border-radius:12px;padding:8px 10px;font-size:12.5px;display:none;pointer-events:none}
.zm-attr{position:absolute;right:4px;bottom:2px;font-size:10px;color:#0b2540;background:rgba(255,255,255,.75);padding:1px 5px;border-radius:6px;pointer-events:none}
.zm-bot{background:#0a1f33;padding:8px 10px calc(env(safe-area-inset-bottom,0px) + 10px);border-top:1px solid #1e9dff55}
.zm-row{display:flex;gap:8px;align-items:center;margin:6px 0;flex-wrap:wrap}
.zm-row input[type=text]{flex:1;min-width:0;padding:9px 10px;border-radius:12px;font-size:15px}
.zm-row input[type=range]{flex:1;min-width:120px}
.zm-help{font-size:12px;color:#9fb4c8;line-height:1.35}
/* v3.15g · tarjetas, franjas y zonas dibujadas */
#boltBox .bz-day{font-size:12px;font-weight:800;border-radius:10px;padding:3px 10px;white-space:nowrap}
#boltBox .bz-day.wd{background:#12365a;color:#bfdbfe}
#boltBox .bz-day.we{background:#3a2a05;color:#fcd34d}
#boltBox .bz-cs{display:block;color:#9fb4c8;font-size:12px;margin:2px 0 4px}
#boltBox .bz-card.bz-air{border-color:#22c55e66}
#boltBox .bz-sub-air{margin:16px 0 4px;color:#86efac}
#boltBox .bz-wk{margin:10px 0;padding:10px;border:1px solid #ffffff2a;border-radius:16px;background:#ffffff0a}
#boltBox .bz-wh{display:flex;padding-left:34px;justify-content:space-between;font-size:11px;color:#9fb4c8;margin-bottom:4px}
#boltBox .bz-wr{display:flex;align-items:center;gap:6px;margin:3px 0}
#boltBox .bz-wr .bz-wd{width:28px;flex:none;font-size:12px;font-weight:700;color:#cfe3f5}
#boltBox .bz-wb{position:relative;flex:1;height:16px;border-radius:6px;background:#12304c;overflow:hidden}
#boltBox .bz-wb i{position:absolute;top:0;bottom:0;background:#f59e0b}
#boltBox .bz-wl{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:12px;color:#cfe3f5;padding-left:34px;margin-top:6px}
#boltBox .bz-wl i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-2px}
#boltBox .bz-wl i.we{background:#f59e0b}
#boltBox .bz-wl i.wd{background:#12304c;border:1px solid #2c4a68}
#boltBox .bz-sl{display:flex;align-items:center;gap:8px;padding:6px 8px;border:1px solid #ffffff2a;border-radius:12px;background:#0a1f33;margin:6px 0}
#boltBox .bz-sw{display:flex;flex:none}
#boltBox .bz-sw input{width:26px;height:26px}
#boltBox .bz-st{flex:1;min-width:0;font-weight:800;font-size:14px;line-height:1.3}
#boltBox .bz-sl button.secondary,#boltBox .bz-az button.secondary{padding:9px 12px;border-radius:12px;border:1px solid #ffffff33;background:#ffffff12;color:inherit;font-size:15px;font-weight:700;line-height:1.2;width:auto}
#boltBox .bz-sled{margin:10px 0;padding:10px;border:1px solid #ffffff2a;border-radius:16px;background:#ffffff0a}
#boltBox .bz-sled select,#boltBox .bz-sled input[type=time]{width:100%;box-sizing:border-box;padding:9px 10px;border-radius:12px;font-size:15px}
#boltBox .bz-az{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#boltBox .bz-zc{flex:1;min-width:70px;font-size:12px;color:#9fb4c8;font-weight:700}
#boltBox .bz-zb button.secondary:disabled,#boltBox .bz-sl button:disabled{opacity:.5}
.zm-p{fill:rgba(22,163,74,.25);stroke:#15803d;stroke-width:2.5;stroke-linejoin:round}
.zm-p.sel{fill:rgba(37,99,235,.22);stroke:#1d4ed8;stroke-width:3}
.zm-p.bad{fill:rgba(239,68,68,.28);stroke:#dc2626}
.zm-v{fill:#fff;stroke:#1d4ed8;stroke-width:3}
.zm-v.sel{fill:#1d4ed8;stroke:#fff}
.zm-mid{fill:rgba(255,255,255,.85);stroke:#1d4ed8;stroke-width:2}
.zm-dr{fill:none;stroke:#15803d;stroke-width:3;stroke-dasharray:9 6;stroke-linejoin:round}
.zm-dc{stroke:#15803d;stroke-width:2;stroke-dasharray:3 6;opacity:.7}
.zm-dv{fill:#fff;stroke:#15803d;stroke-width:3}
.zm-dv.first{fill:#22c55e;stroke:#fff}
.zm-n{font:800 13px system-ui,sans-serif;fill:#04210f;text-anchor:middle}
.zm-warn{position:absolute;left:10px;right:10px;bottom:34px;background:rgba(127,29,29,.95);color:#fff;border-radius:12px;padding:8px 10px;font-size:12.5px;display:none;pointer-events:none}
.zm-bot button:disabled{opacity:.45}
.zm-bot button.zm-ok{background:#16a34a;border-color:#22c55e}

/* v3.15g · propina sumada en la lista de viajes: la línea «🎁 27,25 € + 2,00 € propina» debajo del importe (el diseño de la lista oculta los <small>, por eso es un span propio) */
.trip .orig .tipsum{display:block!important;color:#18c987!important;font-size:9px!important;font-weight:700;line-height:1.2!important;white-space:normal!important;margin-top:1px;text-align:inherit}
@media(max-width:360px){.trip .orig .tipsum{font-size:8px!important}}
'''
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
        public String estAirport = "";              // "" | "pickup" (recogida en el aeropuerto) | "dest" (viaje hacia el aeropuerto)
        public double estFee = 0;                   // tasa del aeropuerto restada antes de la comision
        // ---- ajuste por zona (v3.15f/g) ----
        public int estZone = 0;                     // 0 = sin ajuste de zona (aeropuerto, o ajuste apagado) | 1 = fuera de zona buena (M30 y sur) | 2 = zona buena
        public double estAdj = 0;                   // % de ajuste aplicado al calculo con la tarifa de Bolt (-8 fuera con poca demanda, 0 con x1,2 o mas, +12 en zona buena)
        public double estEff = 1;                   // demanda realmente aplicada (la curva de la demanda, no solo el xN de la oferta)
        public String estArea = "";                 // nombre de la zona buena donde se detecto la ubicacion
        public boolean estFromOffer = false;        // true si el calculo uso la demanda que muestra la oferta (false: la de Ajustes)
    }

    // =====================================================================
    //  Estimacion del precio de Bolt cuando la oferta NO muestra el precio (v3.15g).
    //  Todos los valores son ESTIMACIONES editables por el conductor, NO son tarifas oficiales de Bolt.
    //  Cuatro tarjetas de precios: normal y aeropuerto, cada una para entre semana y para fin de semana.
    //  Que tarjeta se usa lo deciden las franjas de fin de semana que define el conductor (y los festivos), no el dia del calendario.
    // =====================================================================

    /** Una tarjeta de precios: inicial + km * precioKm + min * precioMin, nunca menos que la minima (0 = sin minima). */
    public static class Card {
        public double base, perKm, perMin, minFare;
        public Card() { }
        public Card(double base, double perKm, double perMin, double minFare) { this.base = base; this.perKm = perKm; this.perMin = perMin; this.minFare = minFare; }
        public Card copy() { return new Card(base, perKm, perMin, minFare); }
    }

    /** Minutos de una semana (de lunes 00:00 a domingo 24:00). */
    public static final int WEEK_MIN = 10080;

    /** Franja de fin de semana: de "from" a "to" en minutos desde el lunes 00:00 (0..10079); si "to" es menor que "from" da la vuelta al domingo. */
    public static class Slot {
        public boolean on = true;
        public int from, to;
        public Slot() { }
        public Slot(int from, int to) { this.from = from; this.to = to; }
        public Slot copy() { Slot s = new Slot(from, to); s.on = on; return s; }
        /** true si el minuto de la semana w (0..10079) cae dentro: el principio cuenta, el final no. */
        public boolean contains(int w) { return from < to ? (w >= from && w < to) : (w >= from || w < to); }
    }

    /** Franjas iniciales: de viernes 18:00 a domingo 06:00. */
    public static List<Slot> defaultSlots() {
        List<Slot> l = new ArrayList<Slot>();
        l.add(new Slot(4 * 1440 + 18 * 60, 6 * 1440 + 6 * 60));
        return l;
    }

    /** Una zona buena: un poligono dibujado a mano (puntos [latitud, longitud] en orden). */
    public static class Area {
        public String name = "";
        public List<double[]> pts = new ArrayList<double[]>();
        public Area() { }
        public Area(String name, List<double[]> pts) { this.name = name; this.pts = pts; }
        public Area copy() {
            List<double[]> p = new ArrayList<double[]>();
            for (double[] q : pts) p.add(new double[]{q[0], q[1]});
            return new Area(name, p);
        }
        /** Punto dentro del poligono (regla par-impar; la orilla puede salir en cualquiera de los dos lados). */
        public boolean contains(double lat, double lon) {
            boolean in = false;
            for (int i = 0, j = pts.size() - 1; i < pts.size(); j = i++) {
                double yi = pts.get(i)[0], xi = pts.get(i)[1], yj = pts.get(j)[0], xj = pts.get(j)[1];
                if (((yi > lat) != (yj > lat)) && (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) in = !in;
            }
            return in;
        }
    }

    /**
     * Ajuste por zona y por demanda (solo viajes normales; el aeropuerto no lo usa). Se aplica a la tarjeta normal:
     *   calculo = inicial + km * precio_km + min * precio_min  (nunca menos que la minima)
     * FUERA de zona buena (M30, sur...), segun la demanda m que muestra la oferta:
     *   m menor que realFrom (x1,2) ........ calculo * (1 + adj/100)            (por defecto -8 %)
     *   de realFrom a dFrom (x1,2 a x1,3) .. calculo * 1                         (tarifa real, sin demanda)
     *   desde dFrom (x1,4) ................. calculo * m * (1 + extra/100)       (extra: desde dA1 dP1 %, desde dA2 dP2 %, desde dA3 dP3 %; cada escalon sustituye al anterior)
     * EN zona buena: calculo * (1 + adjGood/100) * m   (por defecto +12 %; el multiplicador tal como sale, sin escalones)
     * Las zonas buenas son poligonos que dibuja el conductor y se detectan con la ubicacion del movil (sin ubicacion reciente: fuera de zona buena).
     * Con "on" apagado no hay ajustes: tarjeta * demanda tal como sale.
     */
    public static class Zone {
        public boolean on = true;
        public double adj = -8, adjGood = 12;
        public double mult = 1.0;                         // demanda a mano si la oferta no muestra ninguna (se trata como si la mostrara)
        public double realFrom = 1.2;
        public double dFrom = 1.4, dA1 = 1.5, dP1 = 5, dA2 = 2.0, dP2 = 8, dA3 = 2.5, dP3 = 10;
        public List<Area> good = new ArrayList<Area>();   // sin zonas al principio
        public Zone copy() {
            Zone z = new Zone();
            z.on = on; z.adj = adj; z.adjGood = adjGood; z.mult = mult;
            z.realFrom = realFrom; z.dFrom = dFrom; z.dA1 = dA1; z.dP1 = dP1; z.dA2 = dA2; z.dP2 = dP2; z.dA3 = dA3; z.dP3 = dP3;
            z.good = new ArrayList<Area>();
            for (Area a : good) z.good.add(a.copy());
            return z;
        }
        /** Demanda realmente aplicada para el xN que muestra la oferta. */
        public double demand(double m, boolean goodZone) {
            if (goodZone) return m;
            if (m < dFrom) return 1.0;
            double extra = m >= dA3 ? dP3 : (m >= dA2 ? dP2 : (m >= dA1 ? dP1 : 0));
            return m * (1 + extra / 100.0);
        }
        /** Ajuste (%) sobre el calculo de la tarjeta: -8 fuera si hay poca demanda, 0 fuera con x1,2 o mas, +12 en zona buena. */
        public double adjust(double m, boolean goodZone) {
            if (goodZone) return adjGood;
            return m < realFrom ? adj : 0;
        }
    }

    /** Distancia en km entre dos puntos (formula de haversine). */
    public static double distKm(double lat1, double lon1, double lat2, double lon2) {
        double rad = Math.PI / 180.0, dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return 6371.0 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    /** Nombre de la zona buena que contiene el punto, o null si no esta en ninguna. */
    public static String goodAreaAt(Zone z, double lat, double lon) {
        if (z == null || z.good == null) return null;
        for (Area a : z.good) if (a != null && a.contains(lat, lon)) return a.name;
        return null;
    }

    public static class BoltCfg {
        public Zone zone = new Zone();
        public boolean goodZone = false;     // lo pone el servicio en cada lectura segun la ubicacion (no se guarda)
        public String goodName = "";
        public boolean on = true;
        public String mode = "auto";         // auto (por las franjas) | week (siempre entre semana) | weekend (siempre fin de semana)
        public double comm = 25;             // comision de Bolt, %
        public boolean offerMult = true;     // usar el xN que muestre la oferta, si aparece
        // las cuatro tarjetas: normal / aeropuerto, entre semana (wd) / fin de semana (we)
        public Card nWd = new Card(2.10, 0.77, 0.15, 6.75), nWe = new Card(2.10, 0.77, 0.15, 6.75);
        public Card aWd = new Card(2.89, 0.82, 0.15, 13.50), aWe = new Card(2.89, 0.82, 0.15, 13.50);
        public boolean airOn = true;         // usar la tarjeta del aeropuerto (recogidas y viajes hacia el aeropuerto)
        public double airFee = 2.57;         // tasa del aeropuerto: se resta del bruto ANTES de la comision
        public List<Slot> slots = defaultSlots();
        public boolean holidaysWe = true;    // los festivos cuentan como fin de semana
        public List<String> holidays = defaultHolidays();   // "yyyy-MM-dd" o "MM-dd"
    }

    /** Festivos nacionales fijos y el de la Comunidad de Madrid. Los que cambian cada ano (Semana Santa) se anaden a mano con aaaa-mm-dd. */
    public static List<String> defaultHolidays() {
        List<String> l = new ArrayList<String>();
        for (String s : new String[]{"01-01", "01-06", "05-01", "05-02", "08-15", "10-12", "11-01", "12-06", "12-08", "12-25"}) l.add(s);
        return l;
    }

    /** true si el dia del calendario es uno de los festivos de la lista. */
    public static boolean isHoliday(BoltCfg c, java.util.Calendar cal) {
        int mo = cal.get(java.util.Calendar.MONTH) + 1, dd = cal.get(java.util.Calendar.DAY_OF_MONTH), yy = cal.get(java.util.Calendar.YEAR);
        String full = String.format(Locale.ROOT, "%04d-%02d-%02d", yy, mo, dd), md = String.format(Locale.ROOT, "%02d-%02d", mo, dd);
        if (c.holidays != null) for (String h : c.holidays) if (full.equals(h) || md.equals(h)) return true;
        return false;
    }

    /** Minuto de la semana (0 = lunes 00:00 ... 10079 = domingo 23:59) de un instante. */
    public static int weekMinute(java.util.Calendar cal) {
        int dow = (cal.get(java.util.Calendar.DAY_OF_WEEK) + 5) % 7;       // lunes = 0 ... domingo = 6
        return dow * 1440 + cal.get(java.util.Calendar.HOUR_OF_DAY) * 60 + cal.get(java.util.Calendar.MINUTE);
    }

    /** true si ahora se usa la tarjeta de fin de semana: lo decide la franja en la que cae la hora (o un festivo), no el dia del calendario. */
    public static boolean isWeekend(BoltCfg c, java.util.Calendar cal) {
        if ("week".equals(c.mode)) return false;
        if ("weekend".equals(c.mode)) return true;
        if (c.holidaysWe && isHoliday(c, cal)) return true;
        int w = weekMinute(cal);
        if (c.slots != null) for (Slot s : c.slots) if (s != null && s.on && s.contains(w)) return true;
        return false;
    }

    public static class Est {
        public double gross, comm, net, mult, lo, hi, fee;
        public int tier;                     // siempre 0 (ya no hay tramos; se deja para no cambiar el resto del codigo)
        public String mode = "";             // "Z" = ajuste por zona y demanda | "" = tarjeta por la demanda tal como sale
        public String airport = "";          // "" | "pickup" | "dest"
        public boolean minApplied, weekend, fromOffer;
        public int zone = 0;                 // 0 = sin ajuste de zona | 1 = fuera de zona buena | 2 = zona buena
        public double adj = 0, eff = 1;      // % de ajuste aplicado y demanda realmente aplicada
    }

    // ---- aeropuerto: se detecta por el texto de la oferta ----
    // recogida: "parking P1 de la T1", "parking express T2", "parking modulo D planta 4 de la T4"
    private static final Pattern AIR_PICK_HINT = Pattern.compile("\\b(t\\s?[1-4]|p\\s?1|express|modulo\\s?d|terminal|aeropuerto|barajas)\\b");
    // destino: "Terminal 1..4", "Aeropuerto ...", "Avenida de la Hispanidad"
    private static final Pattern AIR_DEST = Pattern.compile("terminal\\s?[1-4]|aeropuerto|barajas|hispanidad");

    /** "pickup" si se recoge en el aeropuerto, "dest" si el viaje va al aeropuerto, "" si no tiene que ver con el aeropuerto. */
    public static String detectAirport(List<String> nodes) {
        boolean pick = false, dest = false;
        if (nodes == null) return "";
        for (String raw : nodes) {
            if (raw == null || raw.length() > 120) continue;          // los textos largos (avisos, condiciones) no son direcciones
            String n = norm(raw);
            if (n.contains("parking") && AIR_PICK_HINT.matcher(n).find()) pick = true;
            else if (AIR_DEST.matcher(n).find()) dest = true;
        }
        return pick ? "pickup" : (dest ? "dest" : "");
    }

    public static Est estimate(BoltCfg c, boolean weekend, double km, double min, double offerMult) { return estimate(c, weekend, km, min, offerMult, ""); }

    /**
     * Bruto = (inicial + km*precioKm + min*precioMin, nunca menos que la minima) de la tarjeta que toca, sin redondeos intermedios.
     *  - Tarjeta: la del aeropuerto (recogidas Y viajes hacia el aeropuerto) o la normal; la de entre semana o la de fin de semana segun "weekend".
     *  - Aeropuerto: la demanda multiplica todo (minima incluida), sin ajustes de zona; despues se resta la tasa del aeropuerto y sobre el resto se calcula la comision.
     *  - Normal con el ajuste por zona activado: ver Zone. Con el ajuste apagado: tarjeta * demanda tal como sale.
     */
    public static Est estimate(BoltCfg c, boolean weekend, double km, double min, double offerMult, String airKind) {
        boolean air = c.airOn && ("pickup".equals(airKind) || "dest".equals(airKind));
        String ak = air ? airKind : "";
        Card card = air ? (weekend ? c.aWe : c.aWd) : (weekend ? c.nWe : c.nWd);
        boolean fromOffer = c.offerMult && offerMult > 0;
        Est e = new Est();
        double raw = card.base + km * card.perKm + min * card.perMin;
        boolean ma = false;
        if (card.minFare > 0 && raw < card.minFare) { raw = card.minFare; ma = true; }
        Zone z = c.zone;
        double m = Math.max(0.1, Math.min(10.0, fromOffer ? offerMult : z.mult));
        double gross, mult;
        if (!air && z.on) {
            double adj = z.adjust(m, c.goodZone), eff = z.demand(m, c.goodZone);
            mult = eff > 1.0 + 1e-9 || c.goodZone ? m : 1.0;       // lo que se dice en voz alta: solo la demanda que de verdad se aplica
            gross = raw * (1 + adj / 100.0) * eff;
            e.lo = z.realFrom; e.hi = z.dFrom; e.mode = "Z";       // en modo zona: lo = desde que demanda se acaba el descuento, hi = desde que demanda se aplica
            e.zone = c.goodZone ? 2 : 1; e.adj = adj; e.eff = eff;
        } else {
            mult = m;
            gross = raw * m;
            e.eff = m;
        }
        double pct = Math.max(0, Math.min(90, c.comm));
        double fee = air ? c.airFee : 0;
        double after = fee > 0 ? Math.max(0, gross - fee) : gross;
        e.gross = gross; e.fee = fee; e.comm = after * pct / 100.0; e.net = after - e.comm;
        e.mult = mult; e.airport = ak; e.tier = 0;
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
            StringBuilder b = new StringBuilder("Bolt. ");
            if ("pickup".equals(r.estAirport)) b.append("Recogida en el aeropuerto. ");
            else if ("dest".equals(r.estAirport)) b.append("Hacia el aeropuerto. ");
            b.append("Viaje de ").append(km).append("1".equals(km) ? " kil\u00F3metro y " : " kil\u00F3metros y ").append(min).append(min == 1 ? " minuto" : " minutos");
            if (r.estZone == 2) b.append(", zona buena");
            if (r.estWeekend) b.append(", tarifa de fin de semana");
            if (Math.abs(r.estMult - 1.0) > 1e-9) b.append(", demanda por ").append(spokenNum(r.estMult, 2));
            b.append(". Bruto estimado: ").append(money(r.estGross)).append(" euros. ");
            if (r.estFee > 0) b.append("Tasa del aeropuerto: ").append(money(r.estFee)).append(" euros. ");
            b.append("Comisión estimada: ").append(money(r.estComm)).append(" euros. Neto estimado: ").append(money(r.estNet)).append(" euros.");
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

    // ---- peajes: un importe junto a la palabra «peaje» NO es el precio del viaje (se ignora al buscar el precio) ----
    private static final String AMT_RE = "(?:\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}(?:[.,]\\d{1,2})?)";
    private static final String TOLL_W = "(?<![\\p{L}])(?:peajes?|tolls?)(?![\\p{L}])";
    /** «Peaje incluido 2,50 €», «Peajes: €2,50», «Toll 2.50 EUR» (la palabra primero y el importe detras, con la moneda a un lado) */
    private static final Pattern TOLL_AFTER = Pattern.compile("(?i)" + TOLL_W + "[^\\d\u20AC]{0,25}?(?:\u20AC\\s*" + AMT_RE + "|" + AMT_RE + "\\s*(?:\u20AC|eur\\b))");
    /** «Incluye 2,50 € de peajes», «+2,50 € peaje», «2,50 € de peaje» (importe con un nexo claro de peaje; «12,50 € Peaje incluido» NO se toca: ahi el importe es el precio) */
    private static final Pattern TOLL_BEFORE = Pattern.compile("(?i)(?:(?:incluy\\w*|incluid\\w*|incl\\.?|con|m[a\u00E1]s|\\+)\\s*" + AMT_RE + "\\s*(?:\u20AC|eur\\b)\\s*(?:(?:de|en|por)\\s+)?"
            + "|" + AMT_RE + "\\s*(?:\u20AC|eur\\b)\\s*(?:de|en|por)\\s+)" + TOLL_W);
    private static final Pattern TOLL_WORD = Pattern.compile("(?i)" + TOLL_W);
    private static final Pattern TOLL_LONE = Pattern.compile("^[+\\-]?\\s*(?:\u20AC\\s*)?" + AMT_RE + "\\s*(?:\u20AC|eur)?$", Pattern.CASE_INSENSITIVE);

    /**
     * Copia de los nodos SIN los importes de peaje, solo para buscar el precio. Los km, los minutos, el aviso del aeropuerto y todo lo demas
     * siguen leyendo los nodos originales. Si ninguno nombra el peaje, devuelve la misma lista (Uber y Cabify no cambian).
     */
    static List<String> withoutTolls(List<String> nodes) {
        boolean any = false;
        for (String s : nodes) if (TOLL_WORD.matcher(s).find()) { any = true; break; }
        if (!any) return nodes;
        List<String> out = new ArrayList<String>();
        boolean priceBefore = false;               // ya se vio un importe en euros antes (el precio suele ir arriba)
        for (int i = 0; i < nodes.size(); i++) {
            String s = nodes.get(i);
            if (TOLL_WORD.matcher(s).find()) {
                String c = TOLL_AFTER.matcher(s).replaceAll(" ");
                c = TOLL_BEFORE.matcher(c).replaceAll(" ");
                boolean hadAmount = !c.equals(s);
                boolean stillEur = EUR1.matcher(c).find() || EUR2.matcher(c).find();
                out.add(c.trim());
                // «Peajes:» / «Peaje incluido» en un nodo y el importe en el siguiente
                if (!hadAmount && !stillEur && i + 1 < nodes.size() && TOLL_LONE.matcher(nodes.get(i + 1).trim()).find()
                        && (s.trim().endsWith(":") || priceBefore)) { out.add(""); i++; }
                if (stillEur) priceBefore = true;
            } else {
                out.add(s);
                if (EUR1.matcher(s).find() || EUR2.matcher(s).find()) priceBefore = true;
            }
        }
        return out;
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
        // ---- precio: primer importe en euros razonable (sin contar los importes de peaje)
        List<String> priceNodes = withoutTolls(nodes);
        for (String t : priceNodes) {
            Matcher m = EUR1.matcher(t); double v = -1;
            if (m.find()) v = num(m.group(1)); else { Matcher m2 = EUR2.matcher(t); if (m2.find()) v = num(m2.group(1)); }
            if (v >= 1.0 && v < 1000) { r.price = v; break; }
        }
        if (r.price <= 0 && lenient) {
            for (String t : priceNodes) { Matcher m = LONEPRICE.matcher(t.trim()); if (m.find()) { double v = num(m.group(1)); if (v >= 1.0 && v < 1000) { r.price = v; break; } } }
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
                Est e = estimate(p.bolt, p.weekendNow, r.tripKm, r.tripMin, om, detectAirport(nodes));
                r.estimated = true; r.estGross = e.gross; r.estComm = e.comm; r.estNet = e.net; r.estMult = e.mult;
                r.estOfferMult = om; r.estMode = e.mode; r.estTier = e.tier; r.estLo = e.lo; r.estHi = e.hi;
                r.estAirport = e.airport; r.estFee = e.fee;
                r.estZone = e.zone; r.estAdj = e.adj; r.estEff = e.eff; r.estFromOffer = e.fromOffer; r.estArea = p.bolt.goodZone ? p.bolt.goodName : "";
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

    /** Una tarjeta de precios. Cualquier dato ausente o no valido vuelve a su valor inicial. */
    private static OfferAnalyzer.Card card(Object o, OfferAnalyzer.Card def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Card c = def.copy();
        if (m == null) return c;
        c.base = dbl(m.get("base"), def.base, 0, 100);
        c.perKm = dbl(m.get("km"), def.perKm, 0, 20);
        c.perMin = dbl(m.get("min"), def.perMin, 0, 10);
        c.minFare = dbl(m.get("minFare"), def.minFare, 0, 200);
        return c;
    }

    /** Nombre de zona: sin caracteres de control, recortado y de hasta 40 caracteres. */
    private static String areaName(Object o) {
        if (!(o instanceof String)) return "";
        String s = ((String) o).replaceAll("[\\u0000-\\u001F\\u007F]", " ").trim();
        return s.length() > 40 ? s.substring(0, 40).trim() : s;
    }

    /** Ajuste por zona y demanda (v3.15f/g). Cualquier dato ausente o no valido vuelve a su valor inicial. */
    private static OfferAnalyzer.Zone zone(Object o, OfferAnalyzer.Zone def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Zone z = def.copy();
        if (m == null) return z;
        z.on = bool(m.get("on"), def.on);
        z.adj = dbl(m.get("adj"), def.adj, -90, 300);
        z.adjGood = dbl(m.get("adjGood"), def.adjGood, -90, 300);
        z.mult = dbl(m.get("mult"), def.mult, 0.1, 10);
        double rf = dbl(m.get("realFrom"), def.realFrom, 1, 10), df = dbl(m.get("from"), def.dFrom, 1, 10);
        double a1 = dbl(m.get("a1"), def.dA1, 1, 10), a2 = dbl(m.get("a2"), def.dA2, 1, 10), a3 = dbl(m.get("a3"), def.dA3, 1, 10);
        if (rf <= df && df <= a1 && a1 <= a2 && a2 <= a3) { z.realFrom = rf; z.dFrom = df; z.dA1 = a1; z.dA2 = a2; z.dA3 = a3; }
        else { z.realFrom = def.realFrom; z.dFrom = def.dFrom; z.dA1 = def.dA1; z.dA2 = def.dA2; z.dA3 = def.dA3; }
        z.dP1 = dbl(m.get("p1"), def.dP1, 0, 100);
        z.dP2 = dbl(m.get("p2"), def.dP2, 0, 100);
        z.dP3 = dbl(m.get("p3"), def.dP3, 0, 100);
        // zonas buenas: poligonos [latitud, longitud]. Los ajustes de la v3.15f traian circulos en "good": se ignoran (el mapa empieza vacio).
        if (m.get("zones") instanceof List) {
            List<OfferAnalyzer.Area> l = new ArrayList<OfferAnalyzer.Area>();
            for (Object a : (List<?>) m.get("zones")) {
                Map<String, Object> am = map(a);
                if (am == null || l.size() >= MAX_ZONES || !(am.get("pts") instanceof List)) continue;
                List<double[]> pts = new ArrayList<double[]>();
                for (Object po : (List<?>) am.get("pts")) {
                    if (!(po instanceof List) || ((List<?>) po).size() != 2 || pts.size() >= MAX_PTS) continue;
                    List<?> pp = (List<?>) po;
                    double lat = dbl(pp.get(0), 999, -90, 90), lon = dbl(pp.get(1), 999, -180, 180);
                    if (lat == 999 || lon == 999) continue;
                    pts.add(new double[]{lat, lon});
                }
                if (pts.size() >= 3) l.add(new OfferAnalyzer.Area(areaName(am.get("n")), pts));
            }
            z.good = l;
        }
        return z;
    }

    private static final int MAX_ZONES = 40, MAX_PTS = 200, MAX_SLOTS = 20;

    /** Franjas de fin de semana: [{on, from, to}] con minutos desde el lunes 00:00 (enteros 0..10079, distintos). Lo no valido se descarta. */
    private static List<OfferAnalyzer.Slot> slots(Object o, List<OfferAnalyzer.Slot> def) {
        if (!(o instanceof List)) return def;
        List<OfferAnalyzer.Slot> l = new ArrayList<OfferAnalyzer.Slot>();
        for (Object x : (List<?>) o) {
            Map<String, Object> sm = map(x);
            if (sm == null || l.size() >= MAX_SLOTS) continue;
            double f = dbl(sm.get("from"), -1, 0, OfferAnalyzer.WEEK_MIN - 1), t = dbl(sm.get("to"), -1, 0, OfferAnalyzer.WEEK_MIN - 1);
            if (f < 0 || t < 0 || f != Math.floor(f) || t != Math.floor(t) || f == t) continue;
            OfferAnalyzer.Slot s = new OfferAnalyzer.Slot((int) f, (int) t);
            s.on = bool(sm.get("on"), true);
            l.add(s);
        }
        return l;
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
            Map<String, Object> zm = map(m.get("zone")), wdm = map(m.get("wd"));        // wd / zone.base...: ajustes de la v3.15 / v3.15f (se aprovechan algunos valores)
            Map<String, Object> airm = wdm == null ? null : map(wdm.get("air"));
            Object om = m.get("offerMult");
            if (!(om instanceof Boolean) && wdm != null) om = wdm.get("offerMult");
            c.offerMult = bool(om, c.offerMult);
            Object ao = m.get("airOn");
            if (!(ao instanceof Boolean) && airm != null) ao = airm.get("on");
            c.airOn = bool(ao, c.airOn);
            Object af = m.get("airFee");
            if (!(af instanceof Double) && airm != null) af = airm.get("fee");
            c.airFee = dbl(af, c.airFee, 0, 50);
            c.holidaysWe = bool(m.get("holidaysWe"), c.holidaysWe);
            c.slots = slots(m.get("slots"), c.slots);
            Map<String, Object> cm = map(m.get("cards"));
            if (cm != null) {
                c.nWd = card(cm.get("nwd"), c.nWd);
                c.nWe = card(cm.get("nwe"), c.nWe);
                c.aWd = card(cm.get("awd"), c.aWd);
                c.aWe = card(cm.get("awe"), c.aWe);
            } else if (zm != null) {                                 // la v3.15f tenia una sola tarjeta normal para todos los dias
                c.nWd = card(zm, c.nWd);
                c.nWe = c.nWd.copy();
            }
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
            c.zone = zone(m.get("zone"), c.zone);
            return c;
        } catch (Exception e) {
            return new OfferAnalyzer.BoltCfg();
        }
    }

    // ------------------------------------------------------------------ escritura
    private static String n(double v) { return BigDecimal.valueOf(v).stripTrailingZeros().toPlainString(); }

    private static String cardJson(OfferAnalyzer.Card c) {
        return "{\"base\":" + n(c.base) + ",\"km\":" + n(c.perKm) + ",\"min\":" + n(c.perMin) + ",\"minFare\":" + n(c.minFare) + "}";
    }

    private static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '"' || ch == '\\') b.append('\\').append(ch);
            else if (ch < 0x20 || ch == 0x7F) b.append(String.format("\\u%04x", (int) ch));
            else b.append(ch);
        }
        return b.append('"').toString();
    }

    private static String zoneJson(OfferAnalyzer.Zone z) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"on\":").append(z.on).append(",\"adj\":").append(n(z.adj)).append(",\"adjGood\":").append(n(z.adjGood)).append(",\"mult\":").append(n(z.mult))
         .append(",\"realFrom\":").append(n(z.realFrom)).append(",\"from\":").append(n(z.dFrom))
         .append(",\"a1\":").append(n(z.dA1)).append(",\"p1\":").append(n(z.dP1)).append(",\"a2\":").append(n(z.dA2)).append(",\"p2\":").append(n(z.dP2))
         .append(",\"a3\":").append(n(z.dA3)).append(",\"p3\":").append(n(z.dP3)).append(",\"zones\":[");
        boolean first = true;
        if (z.good != null) for (OfferAnalyzer.Area a : z.good) {
            if (a == null || a.pts == null || a.pts.size() < 3) continue;
            if (!first) b.append(',');
            b.append("{\"n\":").append(q(a.name == null ? "" : a.name)).append(",\"pts\":[");
            for (int i = 0; i < a.pts.size(); i++) {
                if (i > 0) b.append(',');
                b.append('[').append(n(a.pts.get(i)[0])).append(',').append(n(a.pts.get(i)[1])).append(']');
            }
            b.append("]}");
            first = false;
        }
        return b.append("]}").toString();
    }

    public static String toJson(OfferAnalyzer.BoltCfg c) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"on\":").append(c.on).append(",\"mode\":\"").append(c.mode).append("\",\"comm\":").append(n(c.comm));
        b.append(",\"offerMult\":").append(c.offerMult).append(",\"airOn\":").append(c.airOn).append(",\"airFee\":").append(n(c.airFee));
        b.append(",\"holidaysWe\":").append(c.holidaysWe).append(",\"holidays\":[");
        boolean first = true;
        if (c.holidays != null) for (String h : c.holidays) {
            if (h == null || !h.matches("\\d{4}-\\d{2}-\\d{2}|\\d{2}-\\d{2}")) continue;
            if (!first) b.append(',');
            b.append('"').append(h).append('"');
            first = false;
        }
        b.append("],\"slots\":[");
        first = true;
        if (c.slots != null) for (OfferAnalyzer.Slot s : c.slots) {
            if (s == null) continue;
            if (!first) b.append(',');
            b.append("{\"on\":").append(s.on).append(",\"from\":").append(s.from).append(",\"to\":").append(s.to).append('}');
            first = false;
        }
        b.append("],\"cards\":{\"nwd\":").append(cardJson(c.nWd)).append(",\"nwe\":").append(cardJson(c.nWe))
         .append(",\"awd\":").append(cardJson(c.aWd)).append(",\"awe\":").append(cardJson(c.aWe))
         .append("},\"zone\":").append(zoneJson(c.zone)).append('}');
        return b.toString();
    }

    /** Configuracion inicial (la unica fuente de verdad de los valores por defecto; la pantalla de ajustes la pide aqui). */
    public static String defaultsJson() { return toJson(new OfferAnalyzer.BoltCfg()); }
}
'''
ZONE = r'''package com.portal.conductor;

import android.content.Context;
import android.content.SharedPreferences;
import android.location.Location;
import android.location.LocationManager;

/**
 * Detecta si el movil esta en una zona buena (v3.15f) con la ULTIMA ubicacion conocida del sistema (no enciende el GPS ni gasta bateria).
 * Si no hay permiso, no hay ubicacion o es muy vieja, devuelve "fuera de zona buena" y deja escrito el motivo en el ajuste "zone_last"
 * (Ajustes lo muestra) para poder comprobar en la calle si funciona con la app en segundo plano.
 */
public class ZoneLocator {
    /** ubicacion mas vieja que esto (milisegundos) no se usa */
    public static final long MAX_AGE_MS = 180000L;
    private static final String[] PROVIDERS = {"gps", "network", "passive", "fused"};

    public static class Fix {
        public double lat, lon;
        public long ageMs;
        public String provider = "";
        public float acc = -1;
    }

    // lo ultimo leido, para no consultar al sistema en cada revision de pantalla (se lee cada pocos segundos como mucho)
    private static Fix cacheFix = null;
    private static String cacheWhy = "";
    private static long cacheAt = -1000000L;
    private static final long CACHE_MS = 2000L;
    private static String lastDiag = "";
    private static long lastDiagAt = 0;

    /** Para las pruebas: olvida la cache. */
    public static void reset() { cacheFix = null; cacheWhy = ""; cacheAt = -1000000L; lastDiag = ""; lastDiagAt = 0; }

    /** El motivo por el que no hay ubicacion (vacio si la hay). */
    public static String why() { return cacheWhy; }

    private static boolean granted(Context ctx, String perm) {
        try { return ctx.checkPermission(perm, android.os.Process.myPid(), android.os.Process.myUid()) == 0; } catch (Exception e) { return false; }
    }

    /** La ubicacion conocida mas reciente de entre todos los proveedores, o null (y why() dice por que). */
    public static synchronized Fix lastFix(Context ctx, long now) {
        if (cacheAt >= 0 && now - cacheAt >= 0 && now - cacheAt < CACHE_MS) return cacheFix;
        Fix best = null;
        String why = "";
        try {
            boolean fine = granted(ctx, "android.permission.ACCESS_FINE_LOCATION"), coarse = granted(ctx, "android.permission.ACCESS_COARSE_LOCATION");
            if (!fine && !coarse) why = "sin permiso de ubicación";
            else {
                Object o = ctx.getSystemService(Context.LOCATION_SERVICE);
                if (!(o instanceof LocationManager)) why = "el móvil no da la ubicación";
                else {
                    LocationManager lm = (LocationManager) o;
                    boolean any = false;
                    for (String p : PROVIDERS) {
                        try {
                            Location l = lm.getLastKnownLocation(p);
                            if (l == null) continue;
                            any = true;
                            long age = now - l.getTime();
                            if (age < 0) age = 0;
                            if (age > MAX_AGE_MS) continue;
                            if (best == null || age < best.ageMs) {
                                best = new Fix();
                                best.lat = l.getLatitude(); best.lon = l.getLongitude(); best.ageMs = age; best.provider = p; best.acc = l.getAccuracy();
                            }
                        } catch (Exception e) { /* este proveedor no existe o no se puede leer: se prueba el siguiente */ }
                    }
                    if (best == null) why = any ? "la última ubicación es muy vieja (más de " + (MAX_AGE_MS / 60000) + " min)" : "no hay ubicación reciente";
                }
            }
        } catch (Exception e) { why = "error leyendo la ubicación"; best = null; }
        cacheFix = best; cacheWhy = why; cacheAt = now;
        return best;
    }

    /** Pone en la configuracion si el movil esta en una zona buena (goodZone / goodName). Nunca falla: ante cualquier problema, fuera de zona buena. */
    public static boolean apply(Context ctx, OfferAnalyzer.BoltCfg c, long now) {
        c.goodZone = false; c.goodName = "";
        try {
            if (c.zone == null || !c.zone.on) return false;
            Fix f = lastFix(ctx, now);
            if (f != null) {
                String n = OfferAnalyzer.goodAreaAt(c.zone, f.lat, f.lon);
                if (n != null) { c.goodZone = true; c.goodName = n; }
            }
            diag(ctx, f, c, now);
        } catch (Exception e) { c.goodZone = false; c.goodName = ""; }
        return c.goodZone;
    }

    private static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '"' || ch == '\\') b.append('\\').append(ch);
            else if (ch < 0x20) b.append(' ');
            else b.append(ch);
        }
        return b.append('"').toString();
    }

    /** JSON con lo que se ve ahora mismo: {"t":ms,"ok":bool,"lat":..,"lon":..,"age":seg,"prov":"..","good":"nombre o vacio","why":"motivo"} */
    public static String json(Fix f, OfferAnalyzer.BoltCfg c, long now) {
        StringBuilder b = new StringBuilder("{\"t\":").append(now);
        if (f != null) {
            b.append(",\"ok\":true,\"lat\":").append(String.format(java.util.Locale.ROOT, "%.5f", f.lat)).append(",\"lon\":").append(String.format(java.util.Locale.ROOT, "%.5f", f.lon))
             .append(",\"age\":").append(f.ageMs / 1000).append(",\"prov\":").append(q(f.provider)).append(",\"why\":\"\"");
        } else b.append(",\"ok\":false,\"why\":").append(q(cacheWhy));
        b.append(",\"good\":").append(q(c != null && c.goodZone ? c.goodName : "")).append('}');
        return b.toString();
    }

    /** Deja escrito el ultimo resultado para que Ajustes lo muestre (como mucho una vez cada 3 s). */
    private static void diag(Context ctx, Fix f, OfferAnalyzer.BoltCfg c, long now) {
        try {
            String key = (f != null) + "|" + c.goodName + "|" + cacheWhy;
            if (key.equals(lastDiag) && now - lastDiagAt < 60000L) return;
            if (!key.equals(lastDiag) && lastDiagAt > 0 && now - lastDiagAt < 3000L) return;
            SharedPreferences sp = ctx.getSharedPreferences("portal", Context.MODE_PRIVATE);
            sp.edit().putString("zone_last", json(f, c, now)).apply();
            lastDiag = key; lastDiagAt = now;
        } catch (Exception e) { }
    }
}
'''
SVC_SETS = [
  [
    (r'''
    /** linea de la demanda en modo zona: cuanto marca la oferta y cuanto se aplica de verdad */''',
     r'''
    /** linea de la tarjeta usada: normal o aeropuerto, entre semana o fin de semana (lo decide la franja que has definido, no el dia del calendario) */
    static String cardLine(OfferAnalyzer.Result r) {
        String t = "pickup".equals(r.estAirport) ? "Aeropuerto (recogida)" : ("dest".equals(r.estAirport) ? "Aeropuerto (viaje hacia allí)" : "Tarjeta normal");
        return t + " \u00B7 " + (r.estWeekend ? "fin de semana" : "entre semana");
    }

    /** linea de la demanda en modo zona: cuanto marca la oferta y cuanto se aplica de verdad */'''),
    (r'''            dt.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)\n");
            if (r.estZone > 0) {
                dt.append(zoneLine(r)).append("\n").append(zoneDemand(r)).append("\n");
            } else {
                String rango = r.estHi < 0 ? ("más de " + num1(r.estLo) + " km") : (r.estLo <= 0 ? ("hasta " + num1(r.estHi) + " km") : (num1(r.estLo) + "–" + num1(r.estHi) + " km"));
                String dia = r.estWeekend ? "fin de semana / festivo" : "lunes a viernes";
                if ("pickup".equals(r.estAirport)) dt.append("Recogida en el aeropuerto: tarifa proporcional a los km (referencia ").append(num1(r.estHi)).append(" km; los minutos no cuentan) · ").append(dia).append("\n");
                else dt.append("dest".equals(r.estAirport) ? "Viaje hacia el aeropuerto · " : "").append("Tramo ").append(r.estTier).append(" (").append(rango).append(") · ").append(dia).append("\n");
                dt.append("Demanda ×").append(multTxt(r.estMult)).append(r.estOfferMult > 0 ? " (de la oferta)" : "").append(r.estMode.length() > 0 ? " · modo " + r.estMode : "").append("\n");
            }
            if (r.estMinApplied) dt.append("Se aplicó la tarifa mínima estimada\n");''',
     r'''            dt.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)\n");
            dt.append(cardLine(r)).append("\n");
            if (r.estZone > 0) dt.append(zoneLine(r)).append("\n");
            dt.append(zoneDemand(r)).append("\n");
            if (r.estMinApplied) dt.append("Se aplicó la tarifa mínima estimada\n");''')
  ],
  [
    (r'''        if (boltCfgCache == null || !js.equals(boltJsonCache)) { boltCfgCache = BoltConfig.parse(js); boltJsonCache = js; }
        return boltCfgCache;''',
     r'''        if (boltCfgCache == null || !js.equals(boltJsonCache)) { boltCfgCache = BoltConfig.parse(js); boltJsonCache = js; }
        try { ZoneLocator.apply(this, boltCfgCache, System.currentTimeMillis()); } catch (Exception e) { boltCfgCache.goodZone = false; boltCfgCache.goodName = ""; }   // zona buena segun el GPS (si falla: fuera de zona buena)
        return boltCfgCache;'''),
    (r'''
    private void showEstimateAlert(OfferAnalyzer.Result r) {''',
     r'''
    private static String pct(double v) { return (v > 1e-9 ? "+" : (v < -1e-9 ? "\u2212" : "")) + num1(Math.abs(v)) + " %"; }

    /** linea de la tarifa por zona del aviso: en que zona esta y que ajuste se ha aplicado */
    static String zoneLine(OfferAnalyzer.Result r) {
        boolean zero = Math.abs(r.estAdj) < 1e-9;
        if (r.estZone == 2) return "Zona buena" + (r.estArea != null && r.estArea.length() > 0 ? " (" + r.estArea + ")" : "") + " \u00B7 tarifa " + (zero ? "normal" : pct(r.estAdj));
        String w = ZoneLocator.why();
        return "Fuera de zona buena" + (w.length() > 0 ? " (" + w + ")" : "") + " \u00B7 tarifa " + (zero ? "real" : pct(r.estAdj));
    }

    /** linea de la tarjeta usada: normal o aeropuerto, entre semana o fin de semana (lo decide la franja que has definido, no el dia del calendario) */
    static String cardLine(OfferAnalyzer.Result r) {
        String t = "pickup".equals(r.estAirport) ? "Aeropuerto (recogida)" : ("dest".equals(r.estAirport) ? "Aeropuerto (viaje hacia allí)" : "Tarjeta normal");
        return t + " \u00B7 " + (r.estWeekend ? "fin de semana" : "entre semana");
    }

    /** linea de la demanda en modo zona: cuanto marca la oferta y cuanto se aplica de verdad */
    static String zoneDemand(OfferAnalyzer.Result r) {
        if (r.estOfferMult <= 0) return r.estMult > 1.0 + 1e-9 ? "Demanda \u00D7" + multTxt(r.estMult) + " (a mano)" : "Sin demanda en la oferta";
        if (!r.estFromOffer) return "Demanda \u00D7" + multTxt(r.estOfferMult) + " de la oferta: ignorada (lo tienes desactivado en Ajustes)";
        String s = "Demanda \u00D7" + multTxt(r.estOfferMult) + " (de la oferta)";
        if (r.estZone == 1) {
            if (Math.abs(r.estEff - 1.0) < 1e-9) s += ": no se aplica (solo desde \u00D7" + multTxt(r.estHi) + ")";
            else if (r.estEff > r.estOfferMult + 1e-9) s += " +" + num1(Math.round((r.estEff / r.estOfferMult - 1) * 1000) / 10.0) + " % = \u00D7" + multTxt(r.estEff);
        }
        return s;
    }

    private void showEstimateAlert(OfferAnalyzer.Result r) {'''),
    (r'''            dt.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)\n");
            String rango = r.estHi < 0 ? ("más de " + num1(r.estLo) + " km") : (r.estLo <= 0 ? ("hasta " + num1(r.estHi) + " km") : (num1(r.estLo) + "–" + num1(r.estHi) + " km"));
            String dia = r.estWeekend ? "fin de semana / festivo" : "lunes a viernes";
            if ("pickup".equals(r.estAirport)) dt.append("Recogida en el aeropuerto: tarifa proporcional a los km (referencia ").append(num1(r.estHi)).append(" km; los minutos no cuentan) · ").append(dia).append("\n");
            else dt.append("dest".equals(r.estAirport) ? "Viaje hacia el aeropuerto · " : "").append("Tramo ").append(r.estTier).append(" (").append(rango).append(") · ").append(dia).append("\n");
            dt.append("Demanda ×").append(multTxt(r.estMult)).append(r.estOfferMult > 0 ? " (de la oferta)" : "").append(r.estMode.length() > 0 ? " · modo " + r.estMode : "").append("\n");
            if (r.estMinApplied) dt.append("Se aplicó la tarifa mínima estimada\n");''',
     r'''            dt.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)\n");
            dt.append(cardLine(r)).append("\n");
            if (r.estZone > 0) dt.append(zoneLine(r)).append("\n");
            dt.append(zoneDemand(r)).append("\n");
            if (r.estMinApplied) dt.append("Se aplicó la tarifa mínima estimada\n");''')
  ]
]
PLG_SETS = [
  [
    (r'''        r.put("weekendNow", OfferAnalyzer.isWeekend(c, java.util.Calendar.getInstance()));
        call.resolve(r);''',
     r'''        r.put("weekendNow", OfferAnalyzer.isWeekend(c, java.util.Calendar.getInstance()));
        r.put("zoneLast", sp.getString("zone_last", ""));
        call.resolve(r);'''),
    (r'''        ScreenReaderService.instance.demoBolt();
        call.resolve();
    }''',
     r'''        ScreenReaderService.instance.demoBolt();
        call.resolve();
    }

    /** v3.15f: donde esta el movil ahora segun la ultima ubicacion del sistema y si cae en una zona buena (para el boton "Probar ubicacion" de Ajustes) */
    @PluginMethod
    public void zoneNow(PluginCall call) {
        android.content.SharedPreferences sp = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE);
        OfferAnalyzer.BoltCfg c = BoltConfig.parse(call.hasOption("cfg") ? call.getString("cfg", "") : sp.getString("bolt_cfg", ""));
        long now = System.currentTimeMillis();
        ZoneLocator.reset();
        ZoneLocator.Fix f = ZoneLocator.lastFix(getContext(), now);
        if (f != null) {
            String n = OfferAnalyzer.goodAreaAt(c.zone, f.lat, f.lon);
            if (n != null) { c.goodZone = true; c.goodName = n; }
        }
        JSObject r = new JSObject();
        r.put("zone", ZoneLocator.json(f, c, now));
        call.resolve(r);
    }''')
  ]
]


def kind(n):
    return 'pre' if n.startswith('01_') else ('early' if n.startswith('05_') else 'late')


def bundle(k):
    return '\n'.join(t for n, t in MODS if kind(n) == k)


def ascii_java(t):
    for ch in t:
        if ord(ch) > 0xFFFF:
            raise SystemExit('ERROR: caracter fuera del plano basico en el Java generado. No se ha cambiado nada.')
    return ''.join(c if ord(c) < 128 else '\\u%04x' % ord(c) for c in t)   # escapes de Java (\uXXXX)


def swap(text, tag, bid, inner):
    a = text.find('<%s id="%s">' % (tag, bid))
    if a < 0 or text.count('id="%s"' % bid) != 1:
        raise SystemExit('ERROR: no encuentro (o esta repetido) el bloque %s. No se ha cambiado nada.' % bid)
    e = text.find('</%s>' % tag, a)
    if e < 0:
        raise SystemExit('ERROR: el bloque %s esta incompleto. No se ha cambiado nada.' % bid)
    e += len('</%s>' % tag)
    return text[:a] + '<%s id="%s">\n%s\n</%s>' % (tag, bid, inner, tag) + text[e:]


def try_plan(text, edits):
    """Aplica una serie de cambios (viejo -> nuevo). Devuelve (texto, None) o (None, motivo). Los que ya estan hechos se saltan."""
    out = text
    for i, (old, new) in enumerate(edits, 1):
        eo, en = ascii_java(old), ascii_java(new)
        if out.count(en) == 1:
            continue                                            # ya estaba
        if out.count(eo) == 1 and out.count(en) == 0:
            out = out.replace(eo, en, 1)
        else:
            return None, 'cambio %d de %d: la ancla aparece %d veces y debia aparecer 1' % (i, len(edits), out.count(eo))
    return out, None


def plan(text, sets, name, need):
    """Prueba cada punto de partida posible (v3.15f o v3.15 sin la f) hasta que uno encaje Y deje el archivo completo (need = trozos que deben estar);
    si ninguno encaja, no se toca nada."""
    why = []
    for k, edits in enumerate(sets):
        out, err = try_plan(text, edits)
        if out is not None:
            miss = [x for x in need if x not in out]
            if not miss:
                return out
            err = 'faltaria %s' % miss[0]
        why.append('punto de partida %d: %s' % (k + 1, err))
    raise SystemExit('ERROR (%s): %s. No se ha cambiado nada.' % (name, '; '.join(why)))


# ---------------------------------------------------------------- 1) todo en memoria (si algo falla no se toca ningun archivo)
n = s
if 'id="v315-pre"' in n: n = swap(n, 'script', 'v315-pre', bundle('pre'))
if 'id="v315-early"' in n: n = swap(n, 'script', 'v315-early', bundle('early'))
n = swap(n, 'script', 'v315-script', bundle('late'))
n = swap(n, 'style', 'v315-style', CSS)
n = re.sub(r'v3\.\d+[a-z]? lector', 'v3.15g lector', n)
for mk in ('v315-script', 'v315-style'):
    if n.count('id="' + mk + '"') != 1:
        raise SystemExit('ERROR: marca ' + mk + ' duplicada o ausente. No se ha cambiado nada.')

cur = {f: open(J + f, encoding='utf-8').read() for f in ('ScreenReaderService.java', 'ScreenReaderPlugin.java', 'OfferAnalyzer.java', 'BoltConfig.java')}
if 'estFee' not in cur['OfferAnalyzer.java'] or 'showEstimateAlert' not in cur['ScreenReaderService.java'] or 'public void getBolt' not in cur['ScreenReaderPlugin.java']:
    raise SystemExit('ERROR: el Java no es el de la v3.15 (falta el aviso de Bolt). No se ha cambiado nada.')
new = {
    'ScreenReaderService.java': plan(cur['ScreenReaderService.java'], SVC_SETS, 'ScreenReaderService.java', ['ZoneLocator.apply', 'static String cardLine(', 'static String zoneLine(', 'static String zoneDemand(', 'dt.append(cardLine(r))']),
    'ScreenReaderPlugin.java': plan(cur['ScreenReaderPlugin.java'], PLG_SETS, 'ScreenReaderPlugin.java', ['public void zoneNow(', 'zone_last']),
    'OfferAnalyzer.java': ascii_java(OFFER),
    'BoltConfig.java': ascii_java(BOLTCFG),
    'ZoneLocator.java': ascii_java(ZONE),
}
if 'ZoneLocator.apply' not in new['ScreenReaderService.java'] or 'zoneNow' not in new['ScreenReaderPlugin.java']:
    raise SystemExit('ERROR: los cambios del servicio o del plugin no han quedado como se esperaba. No se ha cambiado nada.')

zl_path = J + 'ZoneLocator.java'
zl_old = open(zl_path, encoding='utf-8').read() if os.path.exists(zl_path) else None
changed = [f for f in new if (cur.get(f) if f in cur else zl_old) != new[f]]
if n == s and not changed:
    print('v3.15g ya aplicado (las cuatro tarjetas ya estaban). No se cambia nada.')
    raise SystemExit

# ---------------------------------------------------------------- 2) escribir (ya esta todo comprobado)
for f in changed:
    open(J + f, 'w', encoding='utf-8').write(new[f])
if n != s:
    open(p, 'w', encoding='utf-8').write(n)
print('pagina: ' + ('actualizada' if n != s else 'igual'))
for f in changed:
    print('java: ' + f)
print('v3.15g aplicado: cuatro tarjetas (normal/aeropuerto x semana/fin de semana) + franjas + zonas dibujadas + propina sumada')
