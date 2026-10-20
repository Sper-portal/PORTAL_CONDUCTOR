cd /workspaces/PORTAL_CONDUCTOR/portal || exit 1
MA=$(find android/app/src/main/java -name MainActivity.java | head -1)
[ -z "$MA" ] && { echo "ERROR: no encuentro MainActivity.java"; exit 1; }
PKG=$(grep -m1 '^package' "$MA" | sed 's/package \(.*\);/\1/' | tr -d ' \r')
DIR=$(dirname "$MA")
echo "Paquete: $PKG"

cat > "$DIR/ScreenReaderService.java" <<JAVA1
package $PKG;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.List;

public class ScreenReaderService extends AccessibilityService {
    public static ScreenReaderService instance;

    @Override protected void onServiceConnected() { instance = this; }
    @Override public boolean onUnbind(android.content.Intent i) { instance = null; return super.onUnbind(i); }
    @Override public void onAccessibilityEvent(AccessibilityEvent e) { }
    @Override public void onInterrupt() { }

    public JSONArray readAll(String ownPkg) {
        JSONArray out = new JSONArray();
        try {
            List<AccessibilityWindowInfo> ws = getWindows();
            if (ws != null) {
                for (AccessibilityWindowInfo w : ws) {
                    AccessibilityNodeInfo root = w.getRoot();
                    if (root == null) continue;
                    addWindow(out, root, ownPkg);
                }
            }
            if (out.length() == 0) {
                AccessibilityNodeInfo root = getRootInActiveWindow();
                if (root != null) addWindow(out, root, ownPkg);
            }
        } catch (Exception e) { }
        return out;
    }

    private void addWindow(JSONArray out, AccessibilityNodeInfo root, String ownPkg) throws Exception {
        String pkg = String.valueOf(root.getPackageName());
        if (pkg.equals(ownPkg) || pkg.equals("com.android.systemui")) return;
        JSONArray texts = new JSONArray();
        collect(root, texts, 0);
        JSONObject o = new JSONObject();
        o.put("pkg", pkg);
        o.put("texts", texts);
        out.put(o);
    }

    private void collect(AccessibilityNodeInfo n, JSONArray out, int depth) {
        if (n == null || depth > 80) return;
        CharSequence t = n.getText();
        CharSequence d = n.getContentDescription();
        if (t != null && t.length() > 0) out.put(t.toString());
        else if (d != null && d.length() > 0) out.put(d.toString());
        int c = n.getChildCount();
        for (int i = 0; i < c; i++) collect(n.getChild(i), out, depth + 1);
    }
}
JAVA1

cat > "$DIR/ScreenReaderPlugin.java" <<JAVA2
package $PKG;

import android.content.Intent;
import android.net.Uri;
import android.provider.Settings;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "ScreenReader")
public class ScreenReaderPlugin extends Plugin {

    @PluginMethod
    public void status(PluginCall call) {
        JSObject r = new JSObject();
        r.put("enabled", ScreenReaderService.instance != null);
        call.resolve(r);
    }

    @PluginMethod
    public void openSettings(PluginCall call) {
        Intent i = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(i);
        call.resolve();
    }

    @PluginMethod
    public void openAppInfo(PluginCall call) {
        Intent i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getContext().getPackageName()));
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(i);
        call.resolve();
    }

    @PluginMethod
    public void read(PluginCall call) {
        ScreenReaderService s = ScreenReaderService.instance;
        if (s == null) { call.reject("not_enabled"); return; }
        JSObject r = new JSObject();
        r.put("windows", s.readAll(getContext().getPackageName()));
        call.resolve(r);
    }
}
JAVA2

cat > "$DIR/MainActivity.java" <<JAVA3
package $PKG;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ScreenReaderPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
JAVA3

mkdir -p android/app/src/main/res/xml
cat > android/app/src/main/res/xml/accessibility_service_config.xml <<'XML1'
<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeWindowStateChanged"
    android:accessibilityFeedbackType="feedbackGeneric"
    android:accessibilityFlags="flagRetrieveInteractiveWindows|flagIncludeNotImportantViews|flagReportViewIds"
    android:canRetrieveWindowContent="true"
    android:notificationTimeout="300"
    android:description="@string/screen_reader_desc" />
XML1

python3 - "$PKG" <<'PY1'
import sys,re
pkg=sys.argv[1]
mf='android/app/src/main/AndroidManifest.xml'
s=open(mf,encoding='utf-8').read()
if 'ScreenReaderService' not in s:
    svc=('    <service android:name="%s.ScreenReaderService" android:exported="true" '
         'android:label="Portal lector de pantalla" android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">\n'
         '        <intent-filter><action android:name="android.accessibilityservice.AccessibilityService"/></intent-filter>\n'
         '        <meta-data android:name="android.accessibilityservice" android:resource="@xml/accessibility_service_config"/>\n'
         '    </service>\n    ') % pkg
    s=s.replace('</application>',svc+'</application>',1)
    open(mf,'w',encoding='utf-8').write(s)
st='android/app/src/main/res/values/strings.xml'
t=open(st,encoding='utf-8').read()
if 'screen_reader_desc' not in t:
    t=t.replace('</resources>','    <string name="screen_reader_desc">Lee el importe del viaje que aparece en Bolt, Uber o Cabify para pasarlo a la calculadora del Portal. No guarda ni envía nada.</string>\n</resources>')
    open(st,'w',encoding='utf-8').write(t)
print('Manifest y strings OK')
PY1

cat > /tmp/sr_patch.js <<'JS1'
<script id="screenReaderPatch">
/* v2.1 Lectura de pantalla nativa: lee el importe de Bolt/Uber/Cabify en las otras ventanas */
(function(){
const PKGS={'ee.mtakso.driver':'Bolt','com.ubercab.driver':'Uber','com.cabify.driver':'Cabify'};
const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const fmt=n=>new Intl.NumberFormat('es-ES',{style:'currency',currency:'EUR'}).format(n);
function plugin(){try{if(window.Capacitor&&Capacitor.isNativePlatform&&Capacitor.isNativePlatform())return Capacitor.registerPlugin('ScreenReader');}catch(e){}return null;}
function toast(msg){let t=document.getElementById('srToast');if(!t){t=document.createElement('div');t.id='srToast';t.style.cssText='position:fixed;left:50%;bottom:90px;transform:translateX(-50%);max-width:90%;background:#0b1a33;color:#fff;border:1px solid #3b82f6;border-radius:14px;padding:12px 16px;z-index:99999;font:600 15px system-ui;text-align:center';document.body.appendChild(t);}t.textContent=msg;t.style.display='block';clearTimeout(t._h);t._h=setTimeout(()=>{t.style.display='none'},3500);}
function amountsIn(text){const out=[];const re=/(\d{1,3}(?:\.\d{3})+,\d{2}|\d{1,4}[.,]\d{2})(?!\d)\s*(€|eur\b)?/gi;let m;while((m=re.exec(text))){let v=m[1];v=v.includes(',')&&v.includes('.')?v.replace(/\./g,'').replace(',','.'):v.replace(',','.');const n=Number(v);const pre=text.slice(Math.max(0,m.index-2),m.index);if(Number.isFinite(n)&&n>0&&n<10000)out.push({amount:n,euro:!!m[2]||pre.includes('€')});}return out;}
function analyze(wins){const map={};for(const w of wins){const all=norm((w.texts||[]).join(' | '));const bonus=(/confirmar precio|confirm price/.test(all)?6:0)+(/\btotal\b/.test(all)?2:0)+(PKGS[w.pkg]?3:0);const label=PKGS[w.pkg]||String(w.pkg).split('.').pop();for(const t of (w.texts||[])){for(const a of amountsIn(t)){const score=bonus+(a.euro?4:0)+(String(t).length<14?2:0);const k=a.amount.toFixed(2);if(!map[k]||map[k].score<score)map[k]={amount:a.amount,score,label,win:all};}}}return Object.values(map).sort((a,b)=>b.score-a.score);}
function payHint(win){if(/no cobrar|pago a traves de la app|pagado con tarjeta/.test(win))return'Parece TARJETA.';if(/recoge el dinero|cobrar al pasajero|en efectivo/.test(win))return'Parece EFECTIVO.';return'';}
function fill(c){const inp=document.querySelector('#price');if(inp){inp.value=c.amount.toFixed(2).replace('.',',');inp.dispatchEvent(new Event('input',{bubbles:true}));}toast(c.label+': '+fmt(c.amount)+' '+payHint(c.win));}
function choose(list){const o=document.createElement('div');o.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:99998;display:flex;align-items:center;justify-content:center';const b=document.createElement('div');b.style.cssText='background:#0b1a33;border:1px solid #3b82f6;border-radius:18px;padding:16px;width:min(88%,340px);text-align:center;color:#fff;font:600 16px system-ui';b.innerHTML='<div style="margin-bottom:10px">¿Cuál es el precio del viaje?</div>';list.slice(0,4).forEach(c=>{const x=document.createElement('button');x.type='button';x.textContent=fmt(c.amount)+' · '+c.label;x.style.cssText='display:block;width:100%;margin:6px 0;padding:12px;border-radius:12px;border:0;background:#2563eb;color:#fff;font:700 17px system-ui';x.onclick=()=>{o.remove();fill(c);};b.appendChild(x);});const k=document.createElement('button');k.type='button';k.textContent='Cancelar';k.style.cssText='margin-top:6px;padding:8px;border:0;background:none;color:#9db4d8;font:600 14px system-ui';k.onclick=()=>o.remove();b.appendChild(k);o.appendChild(b);document.body.appendChild(o);}
window.fareReadScreen=async function(){
  const SR=plugin();
  if(!SR){const i=document.querySelector('#fareCameraInput');if(i)i.click();return;}
  try{
    const st=await SR.status();
    if(!st.enabled){
      if(confirm('Para leer el precio de otras apps hay que activar «Portal lector de pantalla» en Accesibilidad (Apps instaladas). Solo se hace una vez.\n\nSi aparece "Ajuste restringido", pulsa Aceptar en el siguiente aviso para ir a la ficha de la app y permitirlo.\n\n¿Abrir ajustes de accesibilidad?'))await SR.openSettings();
      else if(confirm('¿Abrir la ficha de la app para permitir ajustes restringidos? (menú ⋮ arriba a la derecha → Permitir ajustes restringidos)'))await SR.openAppInfo();
      return;
    }
    const r=await SR.read();const wins=r.windows||[];
    const cands=analyze(wins);
    if(!cands.length){
      const dbg=wins.map(w=>w.pkg+' ('+(w.texts||[]).length+' textos): '+(w.texts||[]).slice(0,12).join(' | ')).join('\n\n')||'No he podido ver ninguna otra ventana.';
      alert('No encuentro ningún importe en las otras ventanas.\n\n'+dbg);return;
    }
    const top=cands[0];const rivals=cands.filter(c=>c!==top&&c.score>=top.score-1);
    if(rivals.length)choose([top].concat(rivals));else fill(top);
  }catch(e){toast('No se pudo leer: '+(e&&e.message||e));}
};
})();
</script>
JS1

python3 - <<'PY2'
p='www/index.html'
s=open(p,encoding='utf-8').read()
if 'screenReaderPatch' in s:
    print('index.html ya parcheado'); raise SystemExit
old="onclick=\"document.querySelector('#fareCameraInput').click()\""
assert old in s, 'no encuentro el boton de camara'
s=s.replace(old,"onclick=\"fareReadScreen()\"",1)
js=open('/tmp/sr_patch.js',encoding='utf-8').read()
i=s.rfind('</body>')
s=s[:i]+js+'\n'+s[i:] if i>=0 else s+js
open(p,'w',encoding='utf-8').write(s)
print('index.html parcheado')
PY2
echo "LISTO"
