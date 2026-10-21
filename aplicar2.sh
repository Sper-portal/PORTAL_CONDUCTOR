cd /workspaces/PORTAL_CONDUCTOR/portal || exit 1
MA=$(find android/app/src/main/java -name MainActivity.java | head -1)
[ -z "$MA" ] && { echo "ERROR: no encuentro MainActivity.java"; exit 1; }
PKG=$(grep -m1 '^package' "$MA" | sed 's/package \(.*\);/\1/' | tr -d ' \r')
DIR=$(dirname "$MA")
echo "Paquete: $PKG"

cat > "$DIR/ScreenReaderService.java" <<'JAVA1'
package __PKG__;

import android.accessibilityservice.AccessibilityService;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONArray;
import org.json.JSONObject;
import java.text.Normalizer;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ScreenReaderService extends AccessibilityService {
    public static ScreenReaderService instance;
    public static volatile String pendingJson = null;

    private static final Pattern DRIVER = Pattern.compile("mtakso|bolt|uber|cabify", Pattern.CASE_INSENSITIVE);
    private static final Pattern AMT = Pattern.compile("(\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}[.,]\\d{2})(?!\\d)\\s*(\\u20AC|[eE][uU][rR]\\b)?");
    private static final Pattern TOTAL = Pattern.compile("\\btotal\\b");

    private WindowManager wm;
    private TextView bubble;
    private WindowManager.LayoutParams lp;
    private boolean shown = false;
    private String fgPkg = "";

    public static boolean bubbleOn(Context c) {
        int v = c.getSharedPreferences("portal", Context.MODE_PRIVATE).getInt("bubble", -1);
        if (v == -1) return c.getResources().getConfiguration().smallestScreenWidthDp < 600;
        return v == 1;
    }

    @Override protected void onServiceConnected() {
        instance = this;
        wm = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
        buildBubble();
        try {
            AccessibilityNodeInfo r = getRootInActiveWindow();
            if (r != null && r.getPackageName() != null) fgPkg = r.getPackageName().toString();
        } catch (Exception e) { }
        refreshBubble();
    }

    @Override public boolean onUnbind(Intent i) {
        hideBubble();
        instance = null;
        return super.onUnbind(i);
    }

    @Override public void onAccessibilityEvent(AccessibilityEvent e) {
        if (e.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
        CharSequence p = e.getPackageName();
        if (p == null) return;
        String pkg = p.toString();
        String low = pkg.toLowerCase();
        if (pkg.equals("com.android.systemui") || low.contains("inputmethod") || low.contains("keyboard")) return;
        fgPkg = pkg;
        refreshBubble();
    }

    @Override public void onInterrupt() { }

    public void postRefresh() {
        new Handler(Looper.getMainLooper()).post(new Runnable() {
            @Override public void run() { refreshBubble(); }
        });
    }

    private void refreshBubble() {
        boolean want = bubbleOn(this) && !fgPkg.equals(getPackageName()) && DRIVER.matcher(fgPkg).find();
        if (want && !shown) showBubble();
        else if (!want && shown) hideBubble();
    }

    private void showBubble() {
        try { wm.addView(bubble, lp); shown = true; } catch (Exception e) { }
    }

    private void hideBubble() {
        try { if (shown) wm.removeView(bubble); } catch (Exception e) { }
        shown = false;
    }

    private void buildBubble() {
        final float d = getResources().getDisplayMetrics().density;
        int size = (int) (58 * d);
        bubble = new TextView(this);
        bubble.setText("\u20AC");
        bubble.setTextColor(Color.WHITE);
        bubble.setTextSize(24);
        bubble.setGravity(Gravity.CENTER);
        GradientDrawable g = new GradientDrawable();
        g.setShape(GradientDrawable.OVAL);
        g.setColor(Color.parseColor("#2563EB"));
        g.setStroke((int) (2 * d), Color.WHITE);
        bubble.setBackground(g);
        bubble.setElevation(8 * d);
        lp = new WindowManager.LayoutParams(size, size,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.TOP | Gravity.START;
        final SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
        lp.x = sp.getInt("bx", 20);
        lp.y = sp.getInt("by", (int) (200 * d));
        bubble.setOnTouchListener(new View.OnTouchListener() {
            float sx, sy;
            int ox, oy;
            boolean moved;
            @Override public boolean onTouch(View v, MotionEvent ev) {
                int a = ev.getAction();
                if (a == MotionEvent.ACTION_DOWN) {
                    sx = ev.getRawX(); sy = ev.getRawY(); ox = lp.x; oy = lp.y; moved = false;
                    return true;
                } else if (a == MotionEvent.ACTION_MOVE) {
                    float dx = ev.getRawX() - sx;
                    float dy = ev.getRawY() - sy;
                    if (Math.abs(dx) > 12 || Math.abs(dy) > 12) moved = true;
                    if (moved) {
                        lp.x = (int) (ox + dx);
                        lp.y = (int) (oy + dy);
                        try { wm.updateViewLayout(bubble, lp); } catch (Exception e) { }
                    }
                    return true;
                } else if (a == MotionEvent.ACTION_UP) {
                    if (moved) sp.edit().putInt("bx", lp.x).putInt("by", lp.y).apply();
                    else onBubbleTap();
                    return true;
                }
                return false;
            }
        });
    }

    private static class Cand {
        double amount;
        int score;
        String label;
        String hint;
    }

    private static String norm(String s) {
        return Normalizer.normalize(s, Normalizer.Form.NFD).replaceAll("\\p{M}", "").toLowerCase();
    }

    private Cand pickBest(JSONArray wins) {
        Cand best = null;
        try {
            for (int w = 0; w < wins.length(); w++) {
                JSONObject o = wins.getJSONObject(w);
                String pkg = o.getString("pkg");
                JSONArray texts = o.getJSONArray("texts");
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < texts.length(); i++) sb.append(texts.getString(i)).append(" | ");
                String all = norm(sb.toString());
                int bonus = 0;
                if (all.contains("confirmar precio") || all.contains("confirm price")) bonus += 6;
                if (TOTAL.matcher(all).find()) bonus += 2;
                if (DRIVER.matcher(pkg).find()) bonus += 3;
                String label = pkg;
                String low = pkg.toLowerCase();
                if (low.contains("bolt") || low.contains("mtakso")) label = "Bolt";
                else if (low.contains("uber")) label = "Uber";
                else if (low.contains("cabify")) label = "Cabify";
                String hint = "";
                if (all.contains("no cobrar") || all.contains("pago a traves de la app") || all.contains("pagado con tarjeta")) hint = "Parece TARJETA.";
                else if (all.contains("recoge el dinero") || all.contains("cobrar al pasajero") || all.contains("en efectivo")) hint = "Parece EFECTIVO.";
                for (int i = 0; i < texts.length(); i++) {
                    String t = texts.getString(i);
                    Matcher m = AMT.matcher(t);
                    while (m.find()) {
                        String v = m.group(1);
                        if (v.contains(",") && v.contains(".")) v = v.replace(".", "").replace(",", ".");
                        else v = v.replace(",", ".");
                        double amount = Double.parseDouble(v);
                        if (amount <= 0 || amount >= 10000) continue;
                        boolean euro = m.group(2) != null || (m.start() > 0 && t.charAt(m.start() - 1) == '\u20AC');
                        int score = bonus + (euro ? 4 : 0) + (t.length() < 14 ? 2 : 0);
                        if (best == null || score > best.score) {
                            best = new Cand();
                            best.amount = amount;
                            best.score = score;
                            best.label = label;
                            best.hint = hint;
                        }
                    }
                }
            }
        } catch (Exception e) { }
        return best;
    }

    private void onBubbleTap() {
        Cand best = pickBest(readAll(getPackageName()));
        if (best == null) {
            Toast.makeText(this, "No veo ning\u00fan importe en esta pantalla", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            JSONObject o = new JSONObject();
            o.put("amount", best.amount);
            o.put("label", best.label);
            o.put("hint", best.hint);
            pendingJson = o.toString();
        } catch (Exception e) { return; }
        Intent i = new Intent(this, MainActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(i);
    }

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

cat > "$DIR/ScreenReaderPlugin.java" <<'JAVA2'
package __PKG__;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.provider.Settings;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import org.json.JSONObject;

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

    @PluginMethod
    public void takePending(PluginCall call) {
        JSObject r = new JSObject();
        String p = ScreenReaderService.pendingJson;
        if (p == null) {
            r.put("has", false);
        } else {
            ScreenReaderService.pendingJson = null;
            try {
                JSONObject o = new JSONObject(p);
                r.put("has", true);
                r.put("amount", o.getDouble("amount"));
                r.put("label", o.optString("label"));
                r.put("hint", o.optString("hint"));
            } catch (Exception e) {
                r.put("has", false);
            }
        }
        call.resolve(r);
    }

    @PluginMethod
    public void getBubble(PluginCall call) {
        JSObject r = new JSObject();
        r.put("enabled", ScreenReaderService.bubbleOn(getContext()));
        call.resolve(r);
    }

    @PluginMethod
    public void setBubble(PluginCall call) {
        boolean en = call.getBoolean("enabled", true);
        getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).edit().putInt("bubble", en ? 1 : 0).apply();
        ScreenReaderService s = ScreenReaderService.instance;
        if (s != null) s.postRefresh();
        call.resolve();
    }
}
JAVA2
sed -i "s/__PKG__/$PKG/g" "$DIR/ScreenReaderService.java" "$DIR/ScreenReaderPlugin.java"
echo "Java OK"

cat > /tmp/sr_patch2.js <<'JS2'
<script id="screenReaderPatch2">
/* v2.3 Burbuja flotante (movil): recibe el precio leido y lo pone en la calculadora */
(function(){
let SR=null;
try{if(window.Capacitor&&Capacitor.isNativePlatform&&Capacitor.isNativePlatform())SR=(Capacitor.Plugins&&Capacitor.Plugins.ScreenReader)||Capacitor.registerPlugin('ScreenReader');}catch(e){}
if(!SR)return;
const fmt=n=>new Intl.NumberFormat('es-ES',{style:'currency',currency:'EUR'}).format(n);
function toast(msg){let t=document.getElementById('srToast2');if(!t){t=document.createElement('div');t.id='srToast2';t.style.cssText='position:fixed;left:50%;bottom:90px;transform:translateX(-50%);max-width:90%;background:#0b1a33;color:#fff;border:1px solid #3b82f6;border-radius:14px;padding:12px 16px;z-index:99999;font:600 15px system-ui;text-align:center';document.body.appendChild(t);}t.textContent=msg;t.style.display='block';clearTimeout(t._h);t._h=setTimeout(()=>{t.style.display='none'},3500);}
async function takePending(){
  if(document.hidden)return;
  try{
    const r=await SR.takePending();
    if(!r||!r.has)return;
    if(!document.querySelector('#price')){try{show('calc');}catch(e){}}
    const inp=document.querySelector('#price');
    if(inp){inp.value=Number(r.amount).toFixed(2).replace('.',',');inp.dispatchEvent(new Event('input',{bubbles:true}));}
    toast((r.label||'')+': '+fmt(r.amount)+' '+(r.hint||''));
  }catch(e){}
}
setInterval(takePending,1000);
document.addEventListener('visibilitychange',takePending);
const content=document.querySelector('#content');
function injectCard(){
  if(!content||document.getElementById('srBubbleCard'))return;
  const t=content.querySelector('.section-title');
  if(!t||!/Ajustes/.test(t.textContent))return;
  const card=document.createElement('div');
  card.id='srBubbleCard';card.className='note';
  card.style.cssText='margin:12px 0;display:flex;align-items:center;justify-content:space-between;gap:12px';
  card.innerHTML='<div><b>Burbuja flotante</b><br><small>Para el móvil: aparece sobre Bolt/Uber/Cabify y al tocarla lee el precio y abre el Portal.</small></div><input type="checkbox" id="srBubbleChk" style="width:26px;height:26px;flex:none">';
  t.insertAdjacentElement('afterend',card);
  const chk=document.getElementById('srBubbleChk');
  SR.getBubble().then(r=>{chk.checked=!!r.enabled;}).catch(()=>{});
  chk.onchange=()=>{SR.setBubble({enabled:chk.checked}).catch(()=>{});};
}
if(content){new MutationObserver(injectCard).observe(content,{childList:true,subtree:true});injectCard();}
})();
</script>
JS2

python3 - <<'PY3'
import re
p='www/index.html'
s=open(p,encoding='utf-8').read()
if 'screenReaderPatch2' not in s:
    js=open('/tmp/sr_patch2.js',encoding='utf-8').read()
    i=s.rfind('</body>')
    s=s[:i]+js+'\n'+s[i:] if i>=0 else s+js
s=s.replace('v2.2 lector','v2.3 lector')
open(p,'w',encoding='utf-8').write(s)
print('index.html v2.3 OK')
PY3

python3 - <<'PYI'
import glob,os,subprocess,sys
os.makedirs('assets',exist_ok=True)
ext=('.png','.jpg','.jpeg','.webp')
files=[f for pat in ('assets/*','../assets/*','../Assets/*','../*') for f in glob.glob(pat) if os.path.isfile(f) and f.lower().endswith(ext)]
if not files:
    print('AVISO: no encuentro la imagen (ni en portal/assets ni en assets), se deja el icono actual'); sys.exit(0)
src=[f for f in files if os.path.basename(f)=='icon-only.png'] or files
try:
    from PIL import Image
except ImportError:
    if subprocess.call([sys.executable,'-m','pip','install','-q','pillow'])!=0:
        subprocess.call([sys.executable,'-m','pip','install','-q','--break-system-packages','pillow'])
    from PIL import Image
im=Image.open(src[0]).convert('RGBA')
side=max(im.size)
c=Image.new('RGBA',(side,side),(0,0,0,0))
c.paste(im,((side-im.size[0])//2,(side-im.size[1])//2))
c.resize((1024,1024),Image.LANCZOS).save('assets/icon-only.png')
print('icono listo desde',src[0])
PYI
if [ -f assets/icon-only.png ]; then
  npm i -D @capacitor/assets >/dev/null 2>&1
  npx capacitor-assets generate --android --iconBackgroundColor '#0b1a33' --iconBackgroundColorDark '#0b1a33' 2>&1 | tail -4
fi
echo "LISTO"
