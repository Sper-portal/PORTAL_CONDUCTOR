cd /workspaces/PORTAL_CONDUCTOR/portal || exit 1
MA=$(find android/app/src/main/java -name MainActivity.java | head -1)
[ -z "$MA" ] && { echo "ERROR: no encuentro MainActivity.java"; exit 1; }
PKG=$(grep -m1 '^package' "$MA" | sed 's/package \(.*\);/\1/' | tr -d ' \r')
DIR=$(dirname "$MA")
echo "Paquete: $PKG"

cat > "$DIR/GpsService.java" <<'JAVA1'
package __PKG__;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ServiceInfo;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.os.Looper;

public class GpsService extends Service implements LocationListener {
    public static volatile boolean running = false;
    public static volatile long lastFix = 0;

    private LocationManager lm;
    private Location last;
    private double meters = 0;
    private SharedPreferences sp;

    @Override public IBinder onBind(Intent i) { return null; }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
        boolean reset = intent != null && intent.getBooleanExtra("reset", false);
        String session = intent != null ? intent.getStringExtra("session") : null;
        if (session == null) session = "";
        if (reset || (intent != null && !session.equals(sp.getString("gps_session", "")))) {
            meters = 0;
            last = null;
            sp.edit().putFloat("gps_m", 0f).putString("gps_session", session).apply();
        } else {
            meters = sp.getFloat("gps_m", 0f);
        }
        startAsForeground();
        if (!running) {
            try {
                lm = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
                lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 2000L, 0f, this, Looper.getMainLooper());
                running = true;
            } catch (SecurityException e) {
                stopSelf();
            }
        }
        return START_STICKY;
    }

    private void startAsForeground() {
        NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(new NotificationChannel("gps_odo", "Kil\u00f3metros de jornada", NotificationManager.IMPORTANCE_LOW));
        }
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, "gps_odo") : new Notification.Builder(this);
        b.setContentTitle("Portal: contando kil\u00f3metros");
        b.setContentText("Jornada en curso");
        b.setSmallIcon(android.R.drawable.ic_menu_mylocation);
        b.setOngoing(true);
        b.setContentIntent(pi);
        Notification n = b.build();
        if (Build.VERSION.SDK_INT >= 29) startForeground(77, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION);
        else startForeground(77, n);
    }

    @Override public void onLocationChanged(Location loc) {
        lastFix = System.currentTimeMillis();
        if (loc.hasAccuracy() && loc.getAccuracy() > 30f) return;
        if (last != null) {
            float d = last.distanceTo(loc);
            double dt = (loc.getTime() - last.getTime()) / 1000.0;
            if (dt > 0) {
                double v = d / dt;
                double speed = loc.hasSpeed() ? loc.getSpeed() : v;
                if (speed >= 0.7 && d >= 3f && v < 70) {
                    meters += d;
                    sp.edit().putFloat("gps_m", (float) meters).apply();
                }
            }
        }
        last = loc;
    }

    @Override public void onProviderEnabled(String p) { }
    @Override public void onProviderDisabled(String p) { }
    @Override public void onStatusChanged(String p, int s, Bundle b) { }

    @Override public void onDestroy() {
        try { if (lm != null) lm.removeUpdates(this); } catch (Exception e) { }
        running = false;
        super.onDestroy();
    }
}
JAVA1

cat > "$DIR/GpsOdometerPlugin.java" <<'JAVA2'
package __PKG__;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

@CapacitorPlugin(
    name = "GpsOdometer",
    permissions = {
        @Permission(alias = "location", strings = { Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION }),
        @Permission(alias = "notifications", strings = { "android.permission.POST_NOTIFICATIONS" })
    }
)
public class GpsOdometerPlugin extends Plugin {

    @PluginMethod
    public void start(PluginCall call) {
        if (getPermissionState("location") != PermissionState.GRANTED) {
            requestPermissionForAlias("location", call, "locCb");
            return;
        }
        afterLocation(call);
    }

    @PermissionCallback
    private void locCb(PluginCall call) {
        if (getPermissionState("location") == PermissionState.GRANTED) {
            afterLocation(call);
        } else {
            JSObject r = new JSObject();
            r.put("ok", false);
            r.put("reason", "denied");
            call.resolve(r);
        }
    }

    private void afterLocation(PluginCall call) {
        if (Build.VERSION.SDK_INT >= 33 && getPermissionState("notifications") != PermissionState.GRANTED) {
            requestPermissionForAlias("notifications", call, "notifCb");
            return;
        }
        begin(call);
    }

    @PermissionCallback
    private void notifCb(PluginCall call) {
        begin(call);
    }

    private void begin(PluginCall call) {
        boolean reset = call.getBoolean("reset", true);
        String session = call.getString("session", "");
        Intent i = new Intent(getContext(), GpsService.class);
        i.putExtra("reset", reset);
        i.putExtra("session", session);
        try {
            if (Build.VERSION.SDK_INT >= 26) getContext().startForegroundService(i);
            else getContext().startService(i);
            JSObject r = new JSObject();
            r.put("ok", true);
            call.resolve(r);
        } catch (Exception e) {
            JSObject r = new JSObject();
            r.put("ok", false);
            r.put("reason", "error");
            call.resolve(r);
        }
    }

    @PluginMethod
    public void stop(PluginCall call) {
        float m = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).getFloat("gps_m", 0f);
        getContext().stopService(new Intent(getContext(), GpsService.class));
        JSObject r = new JSObject();
        r.put("meters", (double) m);
        call.resolve(r);
    }

    @PluginMethod
    public void status(PluginCall call) {
        float m = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).getFloat("gps_m", 0f);
        JSObject r = new JSObject();
        r.put("active", GpsService.running);
        r.put("meters", (double) m);
        long age = GpsService.lastFix == 0 ? -1 : (System.currentTimeMillis() - GpsService.lastFix) / 1000;
        r.put("fixAgeSec", (double) age);
        call.resolve(r);
    }
}
JAVA2

cat > "$DIR/MainActivity.java" <<'JAVA3'
package __PKG__;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ScreenReaderPlugin.class);
        registerPlugin(GpsOdometerPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
JAVA3
sed -i "s/__PKG__/$PKG/g" "$DIR/GpsService.java" "$DIR/GpsOdometerPlugin.java" "$DIR/MainActivity.java"
echo "Java OK"

python3 - "$PKG" <<'PY1'
import sys
pkg=sys.argv[1]
mf='android/app/src/main/AndroidManifest.xml'
s=open(mf,encoding='utf-8').read()
if 'GpsService' not in s:
    perms=''.join('    <uses-permission android:name="android.permission.%s" />\n'%n for n in ('ACCESS_FINE_LOCATION','ACCESS_COARSE_LOCATION','FOREGROUND_SERVICE','FOREGROUND_SERVICE_LOCATION','POST_NOTIFICATIONS'))
    svc='    <service android:name="%s.GpsService" android:exported="false" android:foregroundServiceType="location" />\n    '%pkg
    s=s.replace('</application>',svc+'</application>',1)
    i=s.rfind('</manifest>')
    s=s[:i]+perms+s[i:]
    open(mf,'w',encoding='utf-8').write(s)
print('Manifest GPS OK')
PY1

cat > /tmp/sr_patch3.js <<'JS3'
<script id="gpsPatch">
/* v3.0 Odometro automatico por GPS */
(function(){
let G=null;
try{if(window.Capacitor&&Capacitor.isNativePlatform&&Capacitor.isNativePlatform())G=(Capacitor.Plugins&&Capacitor.Plugins.GpsOdometer)||Capacitor.registerPlugin('GpsOdometer');}catch(e){}
if(!G)return;
const AUTO_KEY='pdc_gps_auto';
const auto=()=>localStorage.getItem(AUTO_KEY)!=='0';
const nf=n=>Number(n).toLocaleString('es-ES',{minimumFractionDigits:1,maximumFractionDigits:1});
function toast(msg){let t=document.getElementById('srToast3');if(!t){t=document.createElement('div');t.id='srToast3';t.style.cssText='position:fixed;left:50%;bottom:90px;transform:translateX(-50%);max-width:90%;background:#0b1a33;color:#fff;border:1px solid #3b82f6;border-radius:14px;padding:12px 16px;z-index:99999;font:600 15px system-ui;text-align:center';document.body.appendChild(t);}t.textContent=msg;t.style.display='block';clearTimeout(t._h);t._h=setTimeout(()=>{t.style.display='none'},4000);}
const orig=window.toggleSession;
window.toggleSession=async function(){
  const starting=!db.activeSession;
  const k0=db.activeSession?dateKey(db.activeSession.start):null;
  orig();
  try{
    if(starting){
      if(!auto())return;
      const sess=db.activeSession?db.activeSession.start:'';
      const r=await G.start({reset:true,session:sess});
      if(!r||!r.ok)toast('GPS sin permiso: usa el odómetro manual');
    }else{
      const r=await G.stop();
      const km=Math.round((Number(r&&r.meters)||0)/100)/10;
      if(km>0&&k0){
        db.odometer=db.odometer||{};
        db.odometer[k0]=Object.assign({start:'',end:''},db.odometer[k0]||{},{gpsKm:km,updatedAt:new Date().toISOString()});
        save();renderControl();
        toast('📍 '+nf(km)+' km de jornada');
      }
    }
  }catch(e){}
};
(async function resume(){
  try{
    if(auto()&&db.activeSession){
      const s=await G.status();
      if(!s.active)await G.start({reset:false,session:db.activeSession.start});
    }
  }catch(e){}
})();
const content=document.querySelector('#content');
function inject(){
  if(!content)return;
  const run=content.querySelector('.toggle.running');
  if(run&&!document.getElementById('gpsLive')&&auto()){
    const d=document.createElement('div');d.id='gpsLive';
    d.style.cssText='margin:8px 0;text-align:center;font:700 14px system-ui;color:#7aa2ff';
    d.textContent='📍 GPS activo · calculando…';
    run.insertAdjacentElement('afterend',d);refreshLive();
  }
  const box=content.querySelector('.odometer-box');
  if(box&&!document.getElementById('gpsOdoLine')&&typeof fuelSelected!=='undefined'){
    const o=dayOdometer(fuelSelected);const g=Number(o.gpsKm);
    if(Number.isFinite(g)&&g>0){
      const line=document.createElement('div');line.id='gpsOdoLine';
      line.style.cssText='margin-top:8px;font:700 14px system-ui;color:#7aa2ff';
      line.innerHTML='📍 Kilómetros por GPS: <b>'+nf(g)+' km</b>';
      if(o.start!==''&&Number.isFinite(Number(o.start))){
        const b=document.createElement('button');b.type='button';b.className='action';b.style.cssText='display:block;width:100%;margin-top:8px';
        b.textContent='Rellenar el final con el GPS';
        b.onclick=()=>{const e=document.querySelector('#odoEnd');if(e){e.value=String(Math.round(Number(o.start)+g));saveOdometer(fuelSelected);}};
        line.appendChild(b);
      }
      box.appendChild(line);
    }
  }
  const t=content.querySelector('.section-title');
  if(t&&/Ajustes/.test(t.textContent)&&!document.getElementById('gpsAutoCard')){
    const card=document.createElement('div');card.id='gpsAutoCard';card.className='note';
    card.style.cssText='margin:12px 0;display:flex;align-items:center;justify-content:space-between;gap:12px';
    card.innerHTML='<div><b>Odómetro automático (GPS)</b><br><small>Cuenta los km desde «Iniciar jornada» hasta «Finalizar jornada». Si lo apagas, sigues con el odómetro manual.</small></div><input type="checkbox" id="gpsAutoChk" style="width:26px;height:26px;flex:none">';
    t.insertAdjacentElement('afterend',card);
    const chk=document.getElementById('gpsAutoChk');chk.checked=auto();
    chk.onchange=()=>{localStorage.setItem(AUTO_KEY,chk.checked?'1':'0');};
  }
}
async function refreshLive(){
  const d=document.getElementById('gpsLive');if(!d)return;
  try{const s=await G.status();
    d.textContent=s.active?('📍 '+nf((Number(s.meters)||0)/1000)+' km · GPS activo'):'📍 GPS parado';
  }catch(e){}
}
setInterval(refreshLive,5000);
if(content){new MutationObserver(inject).observe(content,{childList:true,subtree:true});inject();}
})();
</script>
JS3

python3 - <<'PY3'
import re
p='www/index.html'
s=open(p,encoding='utf-8').read()
if 'id="gpsPatch"' in s:
    print('GPS ya aplicado'); raise SystemExit
n=[]
s,a=re.subn(r"(function kilometersForDay\(k\)\{const o=dayOdometer\(k\);return .*?):null\}",r"\1:(Number.isFinite(Number(o.gpsKm))&&Number(o.gpsKm)>0?Number(o.gpsKm):null)}",s,count=1,flags=re.S); n.append(('km-con-gps',a))
old="db.odometer[k]={start,end,updatedAt:new Date().toISOString()};"
a=s.count(old); s=s.replace(old,"db.odometer[k]=Object.assign({},db.odometer[k]||{},{start,end,updatedAt:new Date().toISOString()});"); n.append(('guardar-odometro',a))
js=open('/tmp/sr_patch3.js',encoding='utf-8').read()
i=s.rfind('</body>'); s=s[:i]+js+'\n'+s[i:] if i>=0 else s+js
s=s.replace('v2.4 lector','v3.0 lector')
open(p,'w',encoding='utf-8').write(s)
for l,c in n: print(f'{l}: {c} cambio(s)')
print('index.html v3.0 OK')
PY3

echo "--- firma fija ---"
cd android/app
if [ ! -f portal-debug.keystore ]; then
  keytool -genkeypair -keystore portal-debug.keystore -storepass portal2026 -keypass portal2026 -alias portal -keyalg RSA -keysize 2048 -validity 36500 -dname "CN=Portal Conductor" >/dev/null 2>&1
fi
if [ -f portal-debug.keystore ]; then
  python3 - <<'PY4'
s=open('build.gradle',encoding='utf-8').read()
if 'portal-debug.keystore' not in s:
    blk="""android {
    signingConfigs {
        debug {
            storeFile file('portal-debug.keystore')
            storePassword 'portal2026'
            keyAlias 'portal'
            keyPassword 'portal2026'
        }
    }
"""
    s=s.replace('android {\n',blk,1)
    open('build.gradle','w',encoding='utf-8').write(s)
print('Firma fija configurada' if 'portal-debug.keystore' in s else 'AVISO: no se pudo configurar la firma')
PY4
  git add -f portal-debug.keystore 2>/dev/null
else
  echo "AVISO: no hay keytool; se compila sin firma fija"
fi
cd ../..
gh repo view --json isPrivate -q '"Repositorio privado: "+(.isPrivate|tostring)' 2>/dev/null
echo "LISTO"
