package com.portal.conductor;

import android.accessibilityservice.AccessibilityService;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.common.InputImage;
import com.google.android.gms.tasks.OnSuccessListener;
import com.google.android.gms.tasks.OnFailureListener;
import android.graphics.Paint;
import android.graphics.Rect;
import java.util.ArrayList;
import android.widget.LinearLayout;
import android.graphics.Typeface;
import android.accessibilityservice.AccessibilityServiceInfo;
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
import android.widget.ImageView;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.view.ViewOutlineProvider;
import android.widget.Toast;
import java.util.Locale;
import android.os.Bundle;
import android.media.AudioAttributes;
import android.speech.tts.TextToSpeech;
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
    private static final Pattern NAVAPP = Pattern.compile("^(com\\.waze|com\\.google\\.android\\.apps\\.maps)$", Pattern.CASE_INSENSITIVE);   // v3.65: navegadores sobre los que la burbuja se queda
    private static final long NAV_KEEP_MS = 2L * 60L * 60L * 1000L;   // v3.65: ...si en las ultimas 2 horas has estado en una app de conductor
    private static final Pattern AMT = Pattern.compile("(\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}[.,]\\d{2})(?!\\d)\\s*(\\u20AC|[eE][uU][rR]\\b)?");
    private static final Pattern TOTAL = Pattern.compile("\\btotal\\b");

    private WindowManager wm;
    private ImageView bubble;
    private WindowManager.LayoutParams lp;
    private boolean shown = false;
    private String fgPkg = "";
    private long lastDriverMs = 0;   // v3.65: ultima vez que se vio (o se dejo) una app de conductor delante

    public static boolean bubbleOn(Context c) {
        int v = c.getSharedPreferences("portal", Context.MODE_PRIVATE).getInt("bubble", -1);
        if (v == -1) return c.getResources().getConfiguration().smallestScreenWidthDp < 600;
        return v == 1;
    }

    /** v3.62: la primera vez que se activa el lector, la rentabilidad (el aviso del "neto aprox.") se enciende sola. Si ya hay una eleccion guardada ("rent_on" existe: la guardo la pantalla de Rentabilidad o ya se encendio sola) NO se toca nada. true = la encendio ahora. */
    static boolean autoRent(android.content.SharedPreferences sp) {
        if (sp == null || sp.contains("rent_on")) return false;
        sp.edit().putInt("rent_on", 1).apply();
        return true;
    }

    @Override protected void onServiceConnected() {
        instance = this;
        try { autoRent(getSharedPreferences("portal", Context.MODE_PRIVATE)); } catch (Throwable t) { }
        wm = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
        buildBubble();
        try {
            AccessibilityNodeInfo r = getRootInActiveWindow();
            if (r != null && r.getPackageName() != null) { fgPkg = r.getPackageName().toString(); if (DRIVER.matcher(fgPkg).find()) lastDriverMs = System.currentTimeMillis(); }
        } catch (Exception e) { }
        refreshBubble();
        applyRentConfig();
    }

    @Override public boolean onUnbind(Intent i) {
        hideBubble();
        hideAlert();
        shutdownTts();
        try { bg.shutdownNow(); } catch (Throwable t) { }         // v3.49
        try { ocrEx.shutdownNow(); } catch (Throwable t) { }
        instance = null;
        return super.onUnbind(i);
    }

    @Override public void onAccessibilityEvent(AccessibilityEvent e) {
        int et = e.getEventType();
        if (et == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) {
            if (trackOn(this)) {
                CharSequence cp = e.getPackageName();
                if (cp != null && DRIVER.matcher(cp).find() && !cp.toString().equals(getPackageName())) scheduleEval();
            }
            return;
        }
        if (et == AccessibilityEvent.TYPE_WINDOWS_CHANGED) {
            try {
                AccessibilityNodeInfo ar = getRootInActiveWindow();
                if (ar != null && ar.getPackageName() != null) {
                    String ap = ar.getPackageName().toString(), al = ap.toLowerCase();
                    if (!ap.equals("com.android.systemui") && !al.contains("inputmethod") && !al.contains("keyboard")) {
                        noteFg(ap);
                        refreshBubble();
                        if (trackOn(this) && DRIVER.matcher(ap).find()) scheduleEval();
                    }
                }
            } catch (Exception ex) { }
            return;
        }
        if (et != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
        CharSequence p = e.getPackageName();
        if (p == null) return;
        String pkg = p.toString();
        String low = pkg.toLowerCase();
        if (pkg.equals("com.android.systemui") || low.contains("inputmethod") || low.contains("keyboard")) return;
        if (pkg.equals(getPackageName())) {   /*v330-guard*/
            // los avisos y la burbuja del propio Portal no cuentan como app en primer plano; solo la pantalla del Portal
            CharSequence cn330 = e.getClassName();
            if (cn330 == null || !cn330.toString().endsWith("Activity")) return;
        }
        noteFg(pkg);
        refreshBubble();
        if (trackOn(this) && DRIVER.matcher(pkg).find()) scheduleEval();
    }

    @Override public void onInterrupt() { }

    public void postRefresh() {
        new Handler(Looper.getMainLooper()).post(new Runnable() {
            @Override public void run() { refreshBubble(); }
        });
    }

    /*v330-bub*/
    // v3.30: la burbuja no se quita por cambios cortos de ventana, tiene un aro luminoso que late, y se anotan los cambios de app para el diagnostico
    private final android.os.Handler ui330 = new android.os.Handler(android.os.Looper.getMainLooper());
    private android.widget.FrameLayout bubbleBox;
    private android.view.View halo;
    private android.animation.ObjectAnimator haloAnim;
    private int bubblePad = 0;
    private boolean hidePending = false;
    private int showCount = 0, hideCount = 0;
    private final java.util.ArrayList<String> fgLog = new java.util.ArrayList<String>();
    private final Runnable hideLater = new Runnable() {
        @Override public void run() {
            hidePending = false;
            try {
                android.view.accessibility.AccessibilityNodeInfo ar = getRootInActiveWindow();
                if (ar != null && ar.getPackageName() != null) {
                    String ap = ar.getPackageName().toString(), al = ap.toLowerCase();
                    if (!ap.equals(getPackageName()) && !ap.equals("com.android.systemui") && !al.contains("inputmethod") && !al.contains("keyboard")) noteFg(ap);
                }
            } catch (Exception ex) { }
            if (shown && !wantBubble()) hideBubble();
        }
    };

    private boolean wantBubble() {
        return forced || (bubbleOn(this) && !fgPkg.equals(getPackageName()) && (DRIVER.matcher(fgPkg).find() || navKeep()));
    }

    /** v3.65: Waze o Google Maps delante y has estado en Bolt, Uber o Cabify en las ultimas 2 horas: la burbuja se queda */
    private boolean navKeep() {
        return NAVAPP.matcher(fgPkg).find() && lastDriverMs > 0 && System.currentTimeMillis() - lastDriverMs < NAV_KEEP_MS;
    }

    private android.view.View bubbleRoot() {
        return bubbleBox != null ? bubbleBox : bubble;
    }

    private void cancelHide() {
        ui330.removeCallbacks(hideLater);
        hidePending = false;
    }

    /** Android cambia la ventana activa muchas veces; si vuelve a Bolt, Uber o Cabify enseguida, la burbuja ni se entera */
    private void hideSoon() {
        if (!bubbleOn(this)) {
            cancelHide();
            hideBubble();
        } else if (!hidePending) {
            hidePending = true;
            ui330.postDelayed(hideLater, 1500);   /*v333-wait*/
        }
    }

    /** anota los cambios de app en primer plano (los ultimos 8 salen en el diagnostico de la burbuja) */
    private void noteFg(String pkg) {
        if (pkg == null || pkg.equals(fgPkg)) return;
        try {
            String t = new java.text.SimpleDateFormat("HH:mm:ss.SSS", java.util.Locale.US).format(new java.util.Date());
            fgLog.add(t + " " + fgPkg + " > " + pkg);
            while (fgLog.size() > 8) fgLog.remove(0);
        } catch (Exception ex) { }
        if (DRIVER.matcher(fgPkg).find() || DRIVER.matcher(pkg).find()) lastDriverMs = System.currentTimeMillis();   // v3.65: al entrar o al salir de una app de conductor
        fgPkg = pkg;
    }

    private String fgLogText() {
        StringBuilder sb = new StringBuilder();
        for (String ln : fgLog) { if (sb.length() > 0) sb.append('\n'); sb.append(ln); }
        return sb.toString();
    }

    private void beforeShow330() {
        try { android.view.View v = bubbleRoot(); v.animate().cancel(); v.setAlpha(0f); } catch (Exception ex) { }
    }

    private void afterShow330() {
        showCount++;
        try { bubbleRoot().animate().alpha(1f).setDuration(250).start(); } catch (Exception ex) { }
        startHalo();
    }

    private void beforeHide330() {
        ui330.removeCallbacks(hideLater);
        hidePending = false;
        stopHalo();
        if (shown) hideCount++;
        try { bubbleRoot().animate().cancel(); } catch (Exception ex) { }
    }

    /** mete el icono dentro de un contenedor con un aro luminoso por fuera; el icono mide lo mismo y queda donde estaba */
    private void wrapHalo() {
        try {
            final float d = getResources().getDisplayMetrics().density;
            int size = lp.width;
            int pad = (int) (7 * d);   /*v333-ring*/
            int box = size + 2 * pad;
            android.view.View h = new android.view.View(this);
            android.graphics.drawable.GradientDrawable hg = new android.graphics.drawable.GradientDrawable();
            hg.setShape(android.graphics.drawable.GradientDrawable.OVAL);
            hg.setColor(android.graphics.Color.parseColor("#403B82F6"));
            hg.setStroke((int) (3 * d), android.graphics.Color.parseColor("#FF60A5FA"));
            h.setBackground(hg);
            android.widget.FrameLayout bx = new android.widget.FrameLayout(this);
            bx.addView(h, new android.widget.FrameLayout.LayoutParams(box, box, android.view.Gravity.CENTER));
            bx.addView(bubble, new android.widget.FrameLayout.LayoutParams(size, size, android.view.Gravity.CENTER));
            halo = h;
            bubbleBox = bx;
            bubblePad = pad;
            lp.width = box;
            lp.height = box;
            lp.x -= pad;
            lp.y -= pad;
        } catch (Throwable t) {
            try { if (bubble.getParent() != null) ((android.view.ViewGroup) bubble.getParent()).removeView(bubble); } catch (Throwable t2) { }
            bubbleBox = null; halo = null; bubblePad = 0;
        }
    }

    /** v3.33: el aro de fuera se queda QUIETO y visible (sin latido, como las otras burbujas) */
    private void startHalo() {   /*v333-calm*/
        if (halo == null) return;
        stopHalo();
        halo.setScaleX(1f);
        halo.setScaleY(1f);
        halo.setAlpha(1f);
    }

    private void stopHalo() {
        try { if (haloAnim != null) haloAnim.cancel(); } catch (Throwable t) { }
        haloAnim = null;
    }

    private void refreshBubble() {
        applyRentConfig();
        boolean want = wantBubble(); if (want) cancelHide();
        if (want && !shown) showBubble();
        else if (!want && shown) hideSoon();
    }

    private void showBubble() {
        beforeShow330();
        try { wm.addView(bubbleRoot(), lp); shown = true; afterShow330(); } catch (Exception e) { }
    }

    private void hideBubble() {
        beforeHide330();
        try { if (shown) wm.removeView(bubbleRoot()); } catch (Exception e) { }
        shown = false;
    }

    private void buildBubble() {
        final float d = getResources().getDisplayMetrics().density;
        int size = (int) (58 * d);
        bubble = new ImageView(this);
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
        bubble.setPadding((int) (2 * d), (int) (2 * d), (int) (2 * d), (int) (2 * d));
        GradientDrawable g = new GradientDrawable();
        g.setShape(GradientDrawable.OVAL);
        g.setColor(Color.parseColor("#2563EB"));
        g.setStroke((int) (2 * d), Color.WHITE);
        bubble.setBackground(g);
        bubble.setOutlineProvider(ViewOutlineProvider.BACKGROUND);
        bubble.setClipToOutline(true);
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
                        try { wm.updateViewLayout(bubbleRoot(), lp); } catch (Exception e) { }
                    }
                    return true;
                } else if (a == MotionEvent.ACTION_UP) {
                    if (moved) sp.edit().putInt("bx", lp.x + bubblePad).putInt("by", lp.y + bubblePad).apply();
                    else onBubbleTap();
                    return true;
                }
                return false;
            }
        });
        wrapHalo(); /*v330-halo*/
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
                if (all.contains("no cobrar al pasajero") || all.contains("no cobres") || all.contains("pago a traves de la app") || all.contains("app o tarjeta") || all.contains("pagado con tarjeta") || all.contains("pago con tarjeta")) hint = "Parece TARJETA.";
                else if (all.contains("cobrar al pasajero") || all.contains("cobrar al cliente") || all.contains("recoge el dinero") || all.contains("efectivo")) hint = "Parece EFECTIVO.";
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
        Cand best = pickBest(readWithCache(getPackageName(), null));
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

    public JSONArray readAll(String ownPkg) { return readWindows(ownPkg, 0); }

    /** v3.49: sin el ruido de siempre (pantalla de inicio, teclado): lo que leen Importe automatico y la burbuja */
    public JSONArray readQuick(String ownPkg) { return readWindows(ownPkg, 1); }

    /** v3.49: solo las ventanas de Bolt / Uber / Cabify: lo que lee la oferta en segundo plano */
    public JSONArray readDrivers(String ownPkg) { return readWindows(ownPkg, 2); }

    private static final Pattern NOISE = Pattern.compile("launcher|inputmethod|keyboard", Pattern.CASE_INSENSITIVE);

    /** mode 0 = todas las ventanas, 1 = sin pantalla de inicio ni teclado, 2 = solo Bolt / Uber / Cabify */
    private JSONArray readWindows(String ownPkg, int mode) {
        JSONArray out = new JSONArray();
        try {
            List<AccessibilityWindowInfo> ws = getWindows();
            if (ws != null) {
                for (AccessibilityWindowInfo w : ws) {
                    AccessibilityNodeInfo root = w.getRoot();
                    if (root == null) continue;
                    addWindow(out, root, ownPkg, mode);
                }
            }
            if (out.length() == 0) {
                AccessibilityNodeInfo root = getRootInActiveWindow();
                if (root != null) addWindow(out, root, ownPkg, mode);
            }
        } catch (Exception e) { }
        return out;
    }

    private void addWindow(JSONArray out, AccessibilityNodeInfo root, String ownPkg, int mode) throws Exception {
        String pkg = String.valueOf(root.getPackageName());
        if (pkg.equals(ownPkg) || pkg.equals("com.android.systemui")) return;
        if (mode == 2 && !DRIVER.matcher(pkg).find()) return;      // v3.49: no se recorre lo que no es una app de conductor
        if (mode == 1 && NOISE.matcher(pkg).find()) return;        // v3.49: ni la pantalla de inicio ni el teclado
        JSONArray texts = new JSONArray();
        collect(root, texts, 0);
        JSONObject o = new JSONObject();
        o.put("pkg", pkg);
        o.put("texts", texts);
        out.put(o);
    }

    // ===== Rentabilidad de viajes + diagnostico de la burbuja (v3.9) =====
    private final Handler rh = new Handler(Looper.getMainLooper());
    private boolean evalPending = false;
    private long lastOfferSeen = 0;
    private LinearLayout alertView;
    private TextView aChip, aMain, aDetail;
    private boolean alertShown = false;
    private int manualKind = -1;            // v3.37: zona de la recogida elegida a mano en el aviso (-1 = la de la ubicacion)
    private String manualSig = "";          // v3.37: oferta a la que vale esa eleccion (huella sin zona)
    private long manualTs = 0;
    private LinearLayout zcView;            // v3.37: botones de zona: ventana aparte (esta SI se toca) justo debajo del aviso
    private WindowManager.LayoutParams zcp;
    private boolean zcShown = false, zcListen = false;
    // v3.62: lengueta del cartel: «Mas datos» y botones ✗ / ✓ (ventana aparte, esta SI se toca) justo debajo del aviso
    private LinearLayout tabView, tabBtns;
    private TextView tabTitle, tabMore, tabNo, tabYes, tabMsg, tabRateA, tabRateB;
    private LinearLayout tabRate;
    private WindowManager.LayoutParams tabLp;
    private boolean tabShown = false, tabListen = false, tabDemo = false, tabLastEst = false;
    private int tabLevel = 0;                // 0 plegado \u00B7 1 \u00ABMas datos\u00BB (4 lineas: viaje, recogida, bruto y comision, reserva) \u00B7 2 \u00ABCalculo completo\u00BB (todas las lineas de siempre)
    private TextView aSum, tabCalc;          // aSum: las lineas sencillas (dentro del cartel); tabCalc: boton \u00ABCalculo completo\u00BB
    private LinearLayout tabMoreRow;
    private int tabMode = 0;                 // 0 nada · 1 oferta en pantalla · 2 la oferta ya desaparecio (solo los botones)
    private long tabOpenSeq = -1L;
    private final Runnable tabHideRun = new Runnable() { @Override public void run() { hideTab(); } };
    private String zcSig = "";
    private boolean forced = false;
    private WindowManager.LayoutParams alp;
    // v3.49: la lectura de la pantalla (cada nodo es una consulta a la otra app) y la captura de Uber ya no van en el hilo principal: no frenan el Portal ni la propia app
    private final java.util.concurrent.ExecutorService bg = java.util.concurrent.Executors.newSingleThreadExecutor();
    private final java.util.concurrent.ExecutorService ocrEx = java.util.concurrent.Executors.newSingleThreadExecutor();
    private boolean readBusy = false, scanBusy = false, evalAgain = false;
    private final Runnable evalRun = new Runnable() { @Override public void run() { evalPending = false; evaluateAsync(); } };

    /** lee las ventanas de conductor en el hilo de fondo y juzga la oferta en el principal; si llega otra peticion mientras lee, repite al acabar */
    private void evaluateAsync() {
        if (!trackOn(this)) return;
        if (readBusy) { evalAgain = true; return; }
        readBusy = true;
        try {
            bg.execute(new Runnable() {
                @Override public void run() {
                    JSONArray w = null;
                    try { w = readDrivers(getPackageName()); } catch (Throwable t) { }
                    final JSONArray wins = w;
                    try {
                        rh.post(new Runnable() {
                            @Override public void run() {
                                readBusy = false;
                                try { if (wins != null) evaluateWith(wins); } catch (Throwable t) { }
                                if (evalAgain) { evalAgain = false; scheduleEval(); }
                            }
                        });
                    } catch (Throwable t) { readBusy = false; }
                }
            });
        } catch (Throwable t) { readBusy = false; evaluateOffer(); }
    }
    private final Runnable hideRun = new Runnable() { @Override public void run() { hideAlert(); } };
    private final Runnable unforceRun = new Runnable() { @Override public void run() { forced = false; refreshBubble(); } };

    public static boolean rentOn(Context c) {
        return c.getSharedPreferences("portal", Context.MODE_PRIVATE).getInt("rent_on", 0) == 1;
    }

    /** true si hay que vigilar los cambios de las apps de conductor (burbuja o rentabilidad activadas) */
    public static boolean trackOn(Context c) {
        return rentOn(c) || bubbleOn(c);
    }

    // memoria: lo ultimo que se vio en Bolt/Uber/Cabify, para poder usarlo cuando el Portal esta delante (movil)
    private String cacheJson = null;
    private long cacheTime = 0;

    private void updateCache(JSONArray wins) {
        try {
            JSONArray keep = new JSONArray();
            for (int i = 0; i < wins.length(); i++) {
                JSONObject w = wins.getJSONObject(i);
                if (DRIVER.matcher(w.optString("pkg")).find()) keep.put(w);
            }
            if (keep.length() > 0 && pickBest(keep) != null) { cacheJson = keep.toString(); cacheTime = System.currentTimeMillis(); }
        } catch (Exception e) { }
    }

    private boolean hasDriverWindow(JSONArray wins) {
        try {
            for (int i = 0; i < wins.length(); i++) if (DRIVER.matcher(wins.getJSONObject(i).optString("pkg")).find()) return true;
        } catch (Exception e) { }
        return false;
    }

    /** lectura en vivo; si no hay ninguna app de conductor visible, usa la memoria (hasta 150 s) */
    public JSONArray readWithCache(String ownPkg, JSONObject meta) {
        JSONArray wins = readQuick(ownPkg);          // v3.49: sin pantalla de inicio ni teclado
        try {
            if (!hasDriverWindow(wins) && cacheJson != null) {
                long age = System.currentTimeMillis() - cacheTime;
                if (age <= 150000) {
                    JSONArray c = new JSONArray(cacheJson);
                    for (int i = 0; i < c.length(); i++) wins.put(c.getJSONObject(i));
                    if (meta != null) { meta.put("cached", true); meta.put("cachedAgeMs", age); }
                }
            }
        } catch (Exception e) { }
        saveReadDiag(wins);
        return wins;
    }

    private void saveReadDiag(JSONArray wins) {
        try {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < wins.length(); i++) {
                JSONObject w = wins.getJSONObject(i);
                JSONArray ta = w.getJSONArray("texts");
                sb.append("[").append(w.optString("pkg")).append("] ").append(ta.length()).append(" textos\n");
                int used = 0;
                for (int j = 0; j < ta.length() && used < 1800; j++) { String s = ta.getString(j); sb.append(s).append(" | "); used += s.length() + 3; }
                sb.append("\n\n");
            }
            getSharedPreferences("portal", Context.MODE_PRIVATE).edit().putString("read_lastText", sb.toString()).putLong("read_lastWhen", System.currentTimeMillis()).apply();
        } catch (Exception e) { }
    }

    public void applyRentConfig() {
        try {
            AccessibilityServiceInfo info = getServiceInfo();
            if (info != null) {
                int t = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED | AccessibilityEvent.TYPE_WINDOWS_CHANGED;
                if (trackOn(this)) t |= AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED;
                if (info.eventTypes != t) { info.eventTypes = t; setServiceInfo(info); }
            }
        } catch (Exception e) { }
        if (!rentOn(this)) rh.post(hideRun);
        else startPoll();
    }

    // revision periodica (por si el movil no avisa de los cambios de pantalla) + lectura por imagen para Uber
    private static final Pattern OCR_PKG = Pattern.compile("uber", Pattern.CASE_INSENSITIVE);
    private boolean polling = false;
    private long treeFoundTs = 0, lastSnapTs = 0;
    private final Runnable pollRun = new Runnable() {
        @Override public void run() {
            if (!rentOn(ScreenReaderService.this)) { polling = false; return; }
            rh.postDelayed(this, 1500);
            // v3.49: el recorrido de ventanas va en un hilo aparte (cada una es una consulta a otra app); aqui solo se decide que hacer con el resultado
            if (scanBusy) return;
            scanBusy = true;
            try { bg.execute(scanRun); } catch (Throwable t) { scanBusy = false; }
        }
    };

    private final Runnable scanRun = new Runnable() {
        @Override public void run() {
            boolean any = false, uber = false;
            Rect ub = null;
            try {
                List<AccessibilityWindowInfo> ws = getWindows();
                if (ws != null) for (AccessibilityWindowInfo w : ws) {
                    AccessibilityNodeInfo rt = w.getRoot();
                    if (rt == null) continue;
                    CharSequence pk = rt.getPackageName();
                    if (pk != null && DRIVER.matcher(pk).find() && !pk.toString().equals(getPackageName())) {
                        any = true;
                        if (OCR_PKG.matcher(pk).find()) {
                            uber = true;
                            if (ub == null) { ub = new Rect(); w.getBoundsInScreen(ub); }
                        }
                    }
                }
            } catch (Throwable t) { }
            final boolean fAny = any, fUber = uber;
            final Rect fUb = ub;
            try {
                rh.post(new Runnable() {
                    @Override public void run() {
                        scanBusy = false;
                        try {
                            if (!rentOn(ScreenReaderService.this)) return;
                            if (fAny) {
                                getSharedPreferences("portal", Context.MODE_PRIVATE).edit().putLong("rent_seenTs", System.currentTimeMillis()).apply();
                                scheduleEval();
                            }
                            if (fUber && System.currentTimeMillis() - treeFoundTs > 3000) ocrTick(fUb);
                        } catch (Throwable t) { }
                    }
                });
            } catch (Throwable t) { scanBusy = false; }
        }
    };

    private void startPoll() {
        if (polling) return;
        polling = true;
        rh.postDelayed(pollRun, 1500);
    }

    private OfferAnalyzer.Params rentParams() {
        SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
        OfferAnalyzer.Params p = new OfferAnalyzer.Params();
        p.minHour = sp.getFloat("rent_minHour", 15f);
        p.minKm = sp.getFloat("rent_minKm", 1f);
        p.maxPickup = sp.getFloat("rent_maxPickup", 5f);
        p.commission = sp.getFloat("rent_comm", 0f);
        p.includePickup = sp.getInt("rent_incl", 1) == 1;
        p.tolPct = sp.getFloat("rent_tolPct", 15f);
        p.tolPickup = sp.getFloat("rent_tolPickup", 1f);
        p.bolt = boltCfg();
        p.streets = streetList();   // v3.57
        p.weekendNow = OfferAnalyzer.isWeekend(p.bolt, java.util.Calendar.getInstance());
        if (manualKind >= 0 && manualSig.length() > 0 && System.currentTimeMillis() - manualTs < 120000L) { p.manualKind = manualKind; p.manualSig = manualSig; }   // v3.37
        return p;
    }

    // ---- lectura por imagen (OCR): para apps que esconden la oferta al lector de accesibilidad (Uber) ----
    private volatile boolean ocrBusy = false;         // v3.49: se toca desde el hilo de la captura y desde el principal
    private volatile long ocrNextAt = 0;
    private long ocrFoundTs = 0;
    private OfferAnalyzer.Result ocrFound = null;
    private TextRecognizer recognizer;

    private void setOcrState(String s) {
        getSharedPreferences("portal", Context.MODE_PRIVATE).edit().putString("ocr_state", s).putLong("ocr_ts", System.currentTimeMillis()).apply();
    }

    /** zona de pantalla que ocupa la app de Uber (en tablet con pantalla dividida, solo su mitad) */
    private Rect uberBounds() {
        try {
            List<AccessibilityWindowInfo> ws = getWindows();
            if (ws == null) return null;
            for (AccessibilityWindowInfo w : ws) {
                AccessibilityNodeInfo rt = w.getRoot();
                if (rt == null) continue;
                CharSequence pk = rt.getPackageName();
                if (pk != null && OCR_PKG.matcher(pk).find() && !pk.toString().equals(getPackageName())) {
                    Rect r = new Rect();
                    w.getBoundsInScreen(r);
                    return r;
                }
            }
        } catch (Exception e) { }
        return null;
    }

    private void ocrTick(final Rect area) {
        if (android.os.Build.VERSION.SDK_INT < 30) { setOcrState("No disponible: hace falta Android 11 o superior."); return; }
        long now = System.currentTimeMillis();
        if (ocrBusy || now < ocrNextAt) return;
        if (area == null) return;
        // el hueco que ocupa nuestro propio aviso se mide aqui (hilo principal): luego se tapa para no leernos a nosotros mismos
        Rect al = null;
        try {
            if (alertShown && alertView != null) {
                int[] loc = new int[2];
                alertView.getLocationOnScreen(loc);
                al = new Rect(loc[0], loc[1], loc[0] + alertView.getWidth(), loc[1] + alertView.getHeight());
            }
        } catch (Throwable t) { al = null; }
        try {   // v3.62: la lengueta (ventana aparte) tambien se tapa
            if (tabShown && tabView != null) {
                int[] lt = new int[2];
                tabView.getLocationOnScreen(lt);
                Rect tr = new Rect(lt[0], lt[1], lt[0] + tabView.getWidth(), lt[1] + tabView.getHeight());
                al = al == null ? tr : new Rect(Math.min(al.left, tr.left), Math.min(al.top, tr.top), Math.max(al.right, tr.right), Math.max(al.bottom, tr.bottom));
            }
        } catch (Throwable t) { }
        final Rect alertRect = al;
        ocrBusy = true;
        ocrNextAt = now + 2000;
        final long t0 = System.nanoTime();
        try {
            // v3.49: la captura se recibe en un hilo aparte (antes en el principal): la copia, el recorte y el reconocimiento no frenan la pantalla
            takeScreenshot(android.view.Display.DEFAULT_DISPLAY, ocrEx, new TakeScreenshotCallback() {
                @Override public void onSuccess(ScreenshotResult sr) {
                    Bitmap hw = null;
                    try {
                        hw = Bitmap.wrapHardwareBuffer(sr.getHardwareBuffer(), sr.getColorSpace());
                        if (hw == null) { ocrBusy = false; setOcrState("La captura llego vacia."); return; }
                        runOcr(hw, area, alertRect, t0);
                    } catch (Throwable t) { ocrBusy = false; setOcrState("Error al procesar la captura: " + t); }
                    finally {
                        try { if (hw != null) hw.recycle(); } catch (Throwable t) { }
                        try { sr.getHardwareBuffer().close(); } catch (Throwable t) { }
                    }
                }
                @Override public void onFailure(int code) {
                    ocrBusy = false;
                    ocrNextAt = System.currentTimeMillis() + (code == 3 ? 1200 : 8000);
                    setOcrState("La captura de pantalla no esta permitida (codigo " + code + "). Apaga y vuelve a encender el lector en Accesibilidad.");
                }
            });
        } catch (Throwable t) {
            ocrBusy = false;
            ocrNextAt = System.currentTimeMillis() + 10000;
            setOcrState("Captura no disponible: " + t);
        }
    }

    /** v3.49: copia solo la zona de Uber (no la pantalla entera), tapa nuestro aviso, y libera cada imagen en cuanto deja de hacer falta */
    private void runOcr(Bitmap hw, Rect area, Rect alertRect, final long t0) {
        Bitmap full = null, crop = null;
        try {
            int x = Math.max(0, area.left), y = Math.max(0, area.top);
            int w = Math.min(hw.getWidth() - x, area.width()), h = Math.min(hw.getHeight() - y, area.height());
            if (w < 80 || h < 80) { ocrBusy = false; return; }
            full = hw.copy(Bitmap.Config.ARGB_8888, true);
            crop = Bitmap.createBitmap(full, x, y, w, h);
            if (full != crop) full.recycle();      // (un recorte de todo el bitmap no devuelve el mismo objeto si es modificable, pero por si acaso)
            full = null;
            if (alertRect != null) {
                Paint pt = new Paint();
                pt.setColor(Color.BLACK);
                new Canvas(crop).drawRect(alertRect.left - x, alertRect.top - y, alertRect.right - x, alertRect.bottom - y, pt);
            }
            if (recognizer == null) recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
            final Bitmap cropF = crop;
            crop = null;
            recognizer.process(InputImage.fromBitmap(cropF, 0))
                .addOnSuccessListener(new OnSuccessListener<Text>() {
                    @Override public void onSuccess(Text text) {
                        ocrBusy = false;
                        try { cropF.recycle(); } catch (Throwable t) { }
                        onOcrText(text, (System.nanoTime() - t0) / 1000000L);
                    }
                })
                .addOnFailureListener(new OnFailureListener() {
                    @Override public void onFailure(Exception e) {
                        ocrBusy = false;
                        try { cropF.recycle(); } catch (Throwable t) { }
                        setOcrState("Fallo del reconocimiento: " + e);
                    }
                });
        } catch (Throwable t) {
            ocrBusy = false;
            setOcrState("Fallo en la lectura por imagen: " + t);
            try { if (full != null) full.recycle(); } catch (Throwable u) { }
            try { if (crop != null) crop.recycle(); } catch (Throwable u) { }
        }
    }

    private void onOcrText(Text text, long ms) {
        List<String> lines = new ArrayList<String>();
        StringBuilder sb = new StringBuilder();
        for (Text.TextBlock b : text.getTextBlocks()) {
            for (Text.Line l : b.getLines()) {
                String s = l.getText();
                lines.add(s);
                if (sb.length() < 3500) sb.append(s).append(" | ");
            }
        }
        OfferAnalyzer.Result r = OfferAnalyzer.analyze(lines, rentParams(), true);
        long now = System.currentTimeMillis();
        setOcrState(lines.size() + " lineas leidas por imagen" + (r.offer ? " - oferta reconocida" : (r.acceptSeen ? " - veo el boton Aceptar pero no entendi la oferta" : ""))
            + (r.ocrFix.length() > 0 ? " - corregido: " + r.ocrFix : "") + " (" + ms + " ms)");
        if (r.offer || r.acceptSeen) {
            getSharedPreferences("portal", Context.MODE_PRIVATE).edit()
                .putString("rent_lastText", "[lectura por imagen de Uber]\n" + sb)
                .putString("rent_lastInfo", r.offer ? ("veredicto=" + r.verdict + " precio=" + r.price + " viaje=" + r.tripKm + "km/" + r.tripMin + "min recogida=" + r.pickupKm + "km/" + r.pickupMin + "min") : r.why).apply();
        }
        if (r.offer) { ocrFound = r; ocrFoundTs = now; }
        else if (r.acceptSeen) { r.unreadable = true; r.verdict = "DATA"; r.reason = "No pude leer los datos de esta oferta."; ocrFound = r; ocrFoundTs = now; }
        else ocrFound = null;
        scheduleEval();
    }

    private void scheduleEval() {
        if (evalPending) return;
        evalPending = true;
        rh.postDelayed(evalRun, 450);
    }

    /** lectura y juicio seguidos en el hilo que llama (lo usa el aviso de zona; el camino normal lee en segundo plano: evaluateAsync) */
    private void evaluateOffer() {
        if (!trackOn(this)) return;
        evaluateWith(readAll(getPackageName()));
    }

    /** v3.49: juzga lo leido; siempre en el hilo principal */
    private void evaluateWith(JSONArray wins) {
        if (!trackOn(this)) return;
        try {
            updateCache(wins);
            if (!rentOn(this)) return;
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            long now = System.currentTimeMillis();
            OfferAnalyzer.Result found = null, unreadable = null;
            boolean foundNfx = false;
            for (int i = 0; i < wins.length(); i++) {
                JSONObject w = wins.getJSONObject(i);
                String pkg = w.optString("pkg");
                if (!DRIVER.matcher(pkg).find()) continue;
                JSONArray ta = w.getJSONArray("texts");
                List<String> nodes = new ArrayList<String>();
                StringBuilder sb = new StringBuilder();
                for (int j = 0; j < ta.length(); j++) { String s = ta.getString(j); nodes.add(s); if (sb.length() < 3500) sb.append(s).append(" | "); }
                String all = sb.toString();
                if (now - lastSnapTs > 3000) {
                    sp.edit().putString("snap_" + pkg, ta.length() + " textos visibles: " + (all.length() > 600 ? all.substring(0, 600) : all)).apply();
                }
                OfferAnalyzer.Result r = OfferAnalyzer.analyze(nodes, rentParams(), false, BOLT_PKG.matcher(pkg).find());
                touchStreet(r);   // v3.57
                if (all.contains("\u20AC") || all.toLowerCase().contains("km")) {
                    sp.edit().putLong("rent_evalTs", now).putString("rent_why", r.offer
                        ? ("Oferta reconocida: " + r.verdict + (r.estimated ? " | neto estimado Bolt " : " | precio ") + r.price + " | viaje " + r.tripKm + " km/" + r.tripMin + " min | recogida " + r.pickupKm + " km/" + r.pickupMin + " min" + (r.orderAssumed ? " (orden estimado)" : ""))
                        : ("Texto con importes o km, pero NO reconocido como oferta: " + r.why)).apply();
                }
                if (r.offer || r.acceptSeen || (all.contains("\u20AC") && all.toLowerCase().contains("km"))) {
                    String info = r.offer ? ("veredicto=" + r.verdict + (r.estimated ? " netoEstimadoBolt=" : " precio=") + r.price + " viajeKm=" + r.tripKm + " viajeMin=" + r.tripMin + " recogidaKm=" + r.pickupKm + " recogidaMin=" + r.pickupMin + (r.orderAssumed ? " (orden asumido)" : "")) : "no reconocida como oferta";
                    sp.edit().putString("rent_lastText", pkg + "\n" + all).putString("rent_lastInfo", info).apply();
                }
                if (r.offer) { found = r; r.booking = r.isBolt && RateNotice.booking(nodes); foundNfx = r.isBolt && (RateNotice.noEffect(nodes) || RateNotice.farBooking(nodes, r.pickupKm)); break; }
                else if (r.acceptSeen && unreadable == null) { r.unreadable = true; r.verdict = "DATA"; r.reason = "No pude leer los datos de esta oferta."; unreadable = r; }
            }
            if (now - lastSnapTs > 3000) lastSnapTs = now;
            if (found != null) treeFoundTs = now;
            if (found == null && ocrFound != null && now - ocrFoundTs < 4500 && !ocrFound.unreadable) found = ocrFound;
            if (found == null && unreadable != null) found = unreadable;
            if (found == null && ocrFound != null && now - ocrFoundTs < 4500) found = ocrFound;
            if (found != null) {
                lastOfferSeen = now;
                logTripOffer(found, now, foundNfx);
                tabDemo = false;
                showAlert(found);
                speakOffer(found);
                rh.removeCallbacks(hideRun);
                rh.postDelayed(hideRun, 25000);
            } else if (alertShown && now - lastOfferSeen > 1800) {
                hideAlert();
                startAfter();   // v3.62: la oferta ha desaparecido (p. ej. la has aceptado en Bolt): ✗ / ✓ siguen unos segundos
            }
        } catch (Exception e) { }
    }

    // ===================== Viajes guardados (lengueta del Portal): apunta cada oferta de Bolt que sale en el aviso =====================
    // El Portal (en pantalla dividida) pregunta cada poco «tripCur» y, si hay una oferta nueva, enseña la lengueta con X y V.
    // Aqui solo se guarda la ULTIMA oferta (con un numero de serie que va subiendo); todo lo demas (lista, albaran...) lo lleva el Portal.
    static String jq(String s) {
        StringBuilder b = new StringBuilder("\"");
        if (s != null) for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 0x20) b.append(' ');
            else b.append(c);
        }
        return b.append('"').toString();
    }

    static String jn(double v) {
        if (Double.isNaN(v) || Double.isInfinite(v)) return "-1";
        String s = String.format(java.util.Locale.US, "%.4f", v);
        if (s.indexOf('.') >= 0) { while (s.endsWith("0")) s = s.substring(0, s.length() - 1); if (s.endsWith(".")) s = s.substring(0, s.length() - 1); }
        return s.equals("-0") ? "0" : s;
    }

    /** huella de la oferta: mismos datos = misma oferta (la lectura se repite cada 1,5 s mientras se ve en pantalla) */
    static String tripSig(OfferAnalyzer.Result r) {
        double net = r.estNetAuto >= 0 ? r.estNetAuto : r.estNet;     // v3.37: con la zona de la ubicacion: elegir otra zona en el aviso NO cambia la huella (es la misma oferta)
        double pr = r.estimated ? net : r.price;
        return Math.round(net * 100) + "|" + Math.round(pr * 100) + "|" + Math.round(r.tripKm * 10) + "|" + Math.round(r.tripMin) + "|"
            + Math.round(r.pickupKm * 10) + "|" + Math.round(r.pickupMin);
    }

    static String tripJson(OfferAnalyzer.Result r, long seq, long now) { return tripJson(r, seq, now, 0); }

    /** rev: 0 la primera vez; sube cada vez que la MISMA oferta cambia de cifra porque elegiste otra zona en el aviso (el Portal la actualiza en vez de apuntar otra) */
    static String tripJson(OfferAnalyzer.Result r, long seq, long now, int rev) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"seq\":").append(seq).append(",\"ts\":").append(now);
        b.append(",\"est\":").append(r.estimated ? "true" : "false");
        b.append(",\"verdict\":").append(jq(r.verdict));
        b.append(",\"price\":").append(jn(r.price));
        b.append(",\"net\":").append(jn(r.estNet)).append(",\"gross\":").append(jn(r.estGross)).append(",\"comm\":").append(jn(r.estComm)).append(",\"commPct\":").append(jn(r.estCommPct));
        b.append(",\"fee\":").append(jn(r.estFee)).append(",\"mult\":").append(jn(r.estMult)).append(",\"offerMult\":").append(jn(r.estOfferMult));
        b.append(",\"lo\":").append(jn(r.estRange ? r.estNetLo : -1)).append(",\"hi\":").append(jn(r.estRange ? r.estNetHi : -1)).append(",\"alt\":").append(jn(r.estAlt));
        b.append(",\"zone\":").append(r.estZone).append(",\"zoneName\":").append(jq(OfferAnalyzer.zoneName(r.estZone))).append(",\"zoneSrc\":").append(jq(r.estZoneSrc)).append(",\"area\":").append(jq(r.estArea));
        b.append(",\"peak\":").append(r.estPeakUsed ? "true" : "false").append(",\"weekend\":").append(r.estWeekend ? "true" : "false").append(",\"peakShort\":").append(r.estPeakShort ? "true" : "false");
        b.append(",\"adj\":").append(jn(r.estAdj)).append(",\"disc\":").append(jn(r.estDisc)).append(",\"event\":").append(jq(r.estEvent)).append(",\"fine\":").append(jn(r.estFine)).append(",\"airport\":").append(jq(r.estAirport));
        b.append(",\"tripKm\":").append(jn(r.tripKm)).append(",\"tripMin\":").append(jn(r.tripMin)).append(",\"pickupKm\":").append(jn(r.pickupKm)).append(",\"pickupMin\":").append(jn(r.pickupMin));
        b.append(",\"rev\":").append(rev).append(",\"cpUnlisted\":").append(jq(r.estCpUnlisted));
        b.append(",\"cat\":").append(jq(r.estCat == null ? "" : r.estCat));
        b.append(",\"assign\":").append(r.assignOffer ? "true" : "false");   // v3.62: oferta con el boton «Asignar»
        b.append(",\"booking\":").append(r.booking ? "true" : "false");     // v3.62: oferta con la etiqueta «Reservado»
        return b.append("}").toString();
    }

    /** v3.62: una oferta «Asignar» que lleva tanto tiempo seguido en pantalla sin que nadie la acepte cuenta (si la dejas pasar, como rechazada). Dato de Juan (20-11): unos 30 s; menos de eso no cuenta ni como viaje recibido. */
    static final int ASSIGN_DEFAULT_SEC = 30;
    static final float CK = 0.8f;   // v3.63: el cartel y su lengueta, un 20 % mas pequenos (letras, huecos y botones); la posicion no cambia
    /** los segundos son un ajuste (pantalla de la tasa → trip_asg_sec); entre 5 y 300 */
    static long assignCountMs(android.content.SharedPreferences sp) {
        int s = ASSIGN_DEFAULT_SEC;
        try { s = sp.getInt("trip_asg_sec", ASSIGN_DEFAULT_SEC); } catch (Exception e) { }
        if (s < 5) s = 5;
        if (s > 300) s = 300;
        return s * 1000L;
    }
    /** huecos de mas de esto entre dos lecturas (se lee cada 1,5 s) cortan «seguido en pantalla» */
    static final long ASSIGN_GAP_MS = 6000L;

    /** apunta la oferta de Bolt que se esta viendo (una sola vez por oferta) si el interruptor «Viajes guardados» esta encendido */
    private void logTripOffer(OfferAnalyzer.Result r, long now, boolean nfx) {
        try {
            if (r == null || !r.offer || !r.isBolt || r.unreadable) return;
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            if (sp.getInt("trip_on", 1) != 1) return;
            String sig = tripSig(r);
            long prevTs = sp.getLong("trip_ts", 0L);
            boolean isNew = !sig.equals(sp.getString("trip_sig", "")) || now - prevTs > 90000L;
            boolean asg = r.assignOffer;   // v3.62: boton «Asignar»
            long cents = Math.round(r.estNet * 100);
            SharedPreferences.Editor ed = sp.edit().putLong("trip_ts", now);
            if (isNew) {
                long seq = sp.getLong("trip_seq", 0L) + 1L;
                ed.putString("trip_sig", sig).putLong("trip_seq", seq).putLong("trip_first", now).putInt("trip_rev", 0).putLong("trip_cents", cents).putString("trip_cur", tripJson(r, seq, now, 0));
            } else if (cents != sp.getLong("trip_cents", cents)) {
                // v3.37: es la MISMA oferta con otra cifra (elegiste otra zona en el aviso): se actualiza la ya apuntada, no se apunta otra
                int rev = sp.getInt("trip_rev", 0) + 1;
                ed.putInt("trip_rev", rev).putLong("trip_cents", cents).putString("trip_cur", tripJson(r, sp.getLong("trip_seq", 0L), sp.getLong("trip_first", now), rev));
            }
            // v3.43: aviso «Fuera del radio / no te afectara»: se marca la oferta actual y se cuenta UNA sola vez (el aviso puede leerse un poco despues que el precio)
            // v3.62: la oferta «Asignar» se apunta como las de «Con aviso» (no suma a la tasa salvo que la aceptes) hasta que lleva los segundos del ajuste (30 por defecto) seguidos en pantalla
            if (nfx) ed.putBoolean("trip_nfx_real", true); else if (isNew) ed.putBoolean("trip_nfx_real", false);
            if ((nfx || (asg && isNew)) && (isNew || !sp.getBoolean("trip_nofx", false))) {   // la «Asignar» se marca solo al apuntarla (despues, al contar, no se vuelve a marcar)
                ed.putBoolean("trip_nofx", true).putLong("trip_nofx_n", sp.getLong("trip_nofx_n", 0L) + 1L);
            } else if (isNew) {
                ed.putBoolean("trip_nofx", false);
            }
            if (isNew) ed.putBoolean("trip_asg_done", false).putBoolean("trip_asg_on", asg).putInt("trip_asg_back", 0);
            else if (asg) ed.putBoolean("trip_asg_on", true).putInt("trip_asg_back", 0);
            else if (sp.getBoolean("trip_asg_on", false) && !sp.getBoolean("trip_asg_done", false)) {
                int back = sp.getInt("trip_asg_back", 0) + 1;   // la misma oferta ya pone «Aceptar»: Bolt la ha vuelto una oferta normal
                ed.putInt("trip_asg_back", back);
                if (back >= 2) {
                    ed.putBoolean("trip_asg_done", true);
                    if (!nfx && !sp.getBoolean("trip_nfx_real", false)) {
                        ed.putBoolean("trip_nofx", false).putLong("trip_asg_n", sp.getLong("trip_asg_n", 0L) + 1L).putLong("trip_asg_seq", sp.getLong("trip_seq", 0L));
                    }
                }
            }
            if (asg) {
                boolean cut = isNew || now - prevTs > ASSIGN_GAP_MS;
                if (cut) ed.putLong("trip_asg_since", now);
                long since = cut ? now : sp.getLong("trip_asg_since", now);
                if (!isNew && !sp.getBoolean("trip_asg_done", false) && now - since >= assignCountMs(sp)) {
                    ed.putBoolean("trip_asg_done", true);
                    if (!nfx && !sp.getBoolean("trip_nfx_real", false)) {   // sin aviso de «no te afectara» / fuera de radio: ahora cuenta como una oferta mas
                        ed.putBoolean("trip_nofx", false).putLong("trip_asg_n", sp.getLong("trip_asg_n", 0L) + 1L).putLong("trip_asg_seq", sp.getLong("trip_seq", 0L));
                    }
                }
            }
            ed.apply();
        } catch (Exception e) { }
    }

    private LinearLayout aRow;
    private TextView aP1, aP2, aP3;

    private TextView pill() {
        final float d = getResources().getDisplayMetrics().density * CK;
        TextView t = new TextView(this);
        t.setTextColor(Color.WHITE);
        t.setTextSize(CK * 14);
        t.setGravity(Gravity.CENTER);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setPadding((int) (9 * d), (int) (5 * d), (int) (9 * d), (int) (5 * d));
        return t;
    }

    private void paintPill(TextView t, int st, String text) {
        if (st < 0) { t.setVisibility(View.GONE); return; }
        final float d = getResources().getDisplayMetrics().density * CK;
        GradientDrawable g = new GradientDrawable();
        g.setColor(st == 0 ? Color.parseColor("#16A34A") : (st == 1 ? Color.parseColor("#F59E0B") : Color.parseColor("#DC2626")));
        g.setCornerRadius(12 * d);
        t.setBackground(g);
        t.setTextColor(st == 1 ? Color.BLACK : Color.WHITE);
        t.setText(text);
        t.setVisibility(View.VISIBLE);
    }

    private void buildAlert() {
        final float d = getResources().getDisplayMetrics().density * CK;
        alertView = new LinearLayout(this);
        alertView.setOrientation(LinearLayout.VERTICAL);
        alertView.setGravity(Gravity.CENTER_HORIZONTAL);
        alertView.setPadding((int) (14 * d), (int) (10 * d), (int) (14 * d), (int) (12 * d));
        aChip = new TextView(this);
        aChip.setTextColor(Color.WHITE);
        aChip.setTextSize(CK * 20);
        aChip.setGravity(Gravity.CENTER);
        aChip.setTypeface(Typeface.DEFAULT_BOLD);
        aChip.setPadding((int) (16 * d), (int) (4 * d), (int) (16 * d), (int) (4 * d));
        aRow = new LinearLayout(this);
        aRow.setOrientation(LinearLayout.HORIZONTAL);
        aRow.setGravity(Gravity.CENTER);
        aRow.setPadding(0, (int) (8 * d), 0, 0);
        aP1 = pill(); aP2 = pill(); aP3 = pill();
        LinearLayout.LayoutParams plp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        plp.setMargins((int) (3 * d), 0, (int) (3 * d), 0);
        aRow.addView(aP1, plp);
        aRow.addView(aP2, plp);
        aRow.addView(aP3, plp);
        aMain = new TextView(this);
        aMain.setTextColor(Color.WHITE);
        aMain.setTextSize(CK * 18);
        aMain.setGravity(Gravity.CENTER);
        aMain.setTypeface(Typeface.DEFAULT_BOLD);
        aMain.setPadding(0, (int) (8 * d), 0, 0);
        aDetail = new TextView(this);
        aDetail.setTextColor(Color.parseColor("#DCEBFF"));
        aDetail.setTextSize(CK * 14);
        aDetail.setGravity(Gravity.CENTER);
        aDetail.setPadding(0, (int) (4 * d), 0, 0);
        alertView.addView(aChip);
        alertView.addView(aRow);
        alertView.addView(aMain);
        alertView.addView(aDetail);
        int w = (int) Math.min(getResources().getDisplayMetrics().widthPixels * 0.94f, 400 * d);
        alp = new WindowManager.LayoutParams(w, WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE,
                PixelFormat.TRANSLUCENT);
        alp.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        alp.y = (int) (70 * getResources().getDisplayMetrics().density);
    }

    private static String f(double v, int dec) { return String.format(java.util.Locale.GERMANY, "%." + dec + "f", v); }

    private void showAlert(OfferAnalyzer.Result r) {
        if (r.estimated) { showEstimateAlert(r); return; }
        resetEstimateViews();
        hideZoneChips();
        try {
            if (alertView == null) buildAlert();
            final float d = getResources().getDisplayMetrics().density * CK;
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
            aChip.setText(ok ? "\u2713  ACEPTAR" : (no ? "\u2715  RECHAZAR" : ("WARN".equals(v) ? "\u26A0  A VALORAR" : "\u26A0  DATOS INSUFICIENTES")));
            paintPill(aP1, r.perHour > 0 ? r.stH : -1, f(r.perHour, 1) + " \u20AC/h");
            paintPill(aP2, r.perKm > 0 ? r.stK : -1, f(r.perKm, 2) + " \u20AC/km");
            paintPill(aP3, r.pickupKm > 0 ? r.stP : -1, "Recog. " + f(r.pickupKm, 1) + " km");
            if (r.unreadable) aMain.setText("No pude leer la oferta");
            else if (r.price > 0) aMain.setText("Precio " + f(r.price, 2) + " \u20AC" + (r.booking ? "  \u00B7  RESERVA" : ""));
            else aMain.setText("Sin precio en la oferta");
            StringBuilder dt = new StringBuilder();
            if (r.pickupKm > 0 || r.pickupMin > 0) {
                dt.append("Recogida: ");
                if (r.pickupMin > 0) dt.append((int) r.pickupMin).append(" min");
                if (r.pickupKm > 0) dt.append(r.pickupMin > 0 ? " (" : "").append(f(r.pickupKm, 1)).append(" km").append(r.pickupMin > 0 ? ")" : "");
                dt.append("\n");
            }
            if (r.tripKm > 0) {
                dt.append("Viaje: ");
                if (r.tripMin > 0) dt.append((int) r.tripMin).append(" min (");
                dt.append(f(r.tripKm, 1)).append(" km");
                if (r.tripMin > 0) dt.append(")");
                dt.append("\n");
            }
            dt.append(r.reason);
            if (r.orderAssumed) dt.append("\n(lectura estimada)");
            aDetail.setText(dt.toString());
            if (!alertShown) { wm.addView(alertView, alp); alertShown = true; }
            updateTab(r, false);
        } catch (Exception e) { }
    }

    private void hideAlert() {
        stopSpeech();
        hideZoneChips();
        hideTab();
        try { if (alertShown && alertView != null) wm.removeView(alertView); } catch (Exception e) { }
        alertShown = false;
    }

    public void demoAlert(String verdict) {
        OfferAnalyzer.Result r = new OfferAnalyzer.Result();
        r.offer = true; r.verdict = verdict; r.price = 15.2;
        if ("OK".equals(verdict)) { r.perHour = 31.4; r.perKm = 1.62; r.pickupKm = 1.2; r.pickupMin = 4; r.tripKm = 9.0; r.tripMin = 16; r.stH = 0; r.stK = 0; r.stP = 0; r.reason = "Cumple tus objetivos."; }
        else if ("NO".equals(verdict)) { r.perHour = 9.8; r.perKm = 0.78; r.pickupKm = 6.1; r.pickupMin = 11; r.tripKm = 9.0; r.tripMin = 16; r.stH = 2; r.stK = 2; r.stP = 2; r.reason = "\u20AC/h 9,8 (m\u00EDn. 15,00) \u00B7 \u20AC/km 0,78 (m\u00EDn. 1,00) \u00B7 recogida 6,1 km (m\u00E1x. 5,0)"; }
        else if ("WARN".equals(verdict)) { r.perHour = 31.0; r.perKm = 0.93; r.pickupKm = 5.8; r.pickupMin = 9; r.tripKm = 9.0; r.tripMin = 16; r.stH = 0; r.stK = 1; r.stP = 1; r.reason = "\u20AC/km 0,93 (m\u00EDn. 1,00) \u00B7 recogida 5,8 km (m\u00E1x. 5,0)"; }
        else { r.reason = "No se pudo leer el tiempo del viaje."; }
        tabDemo = true;
        showAlert(r);
        rh.removeCallbacks(hideRun);
        rh.postDelayed(hideRun, 6000);
    }

    // ===================== Bolt: precio estimado, aviso destacado y voz =====================
    private static final Pattern BOLT_PKG = Pattern.compile("mtakso|bolt", Pattern.CASE_INSENSITIVE);
    private String boltJsonCache = null;
    private OfferAnalyzer.BoltCfg boltCfgCache = null;

    /** ajustes de la estimacion de Bolt (se vuelven a leer solo si han cambiado) */
    private OfferAnalyzer.BoltCfg boltCfg() {
        String js = getSharedPreferences("portal", Context.MODE_PRIVATE).getString("bolt_cfg", "");
        if (js == null) js = "";
        if (boltCfgCache == null || !js.equals(boltJsonCache)) { boltCfgCache = BoltConfig.parse(js); boltJsonCache = js; }
        try { ZoneLocator.apply(this, boltCfgCache, System.currentTimeMillis()); } catch (Exception e) { boltCfgCache.zoneKind = boltCfgCache.zoneDef; boltCfgCache.zoneName = ""; boltCfgCache.zoneSrc = "default"; }   // zona de la recogida segun el GPS (si falla: la zona por defecto)
        return boltCfgCache;
    }

    // ===================== v3.57: calles limitrofes (memoria de la zona por direccion) =====================
    private String streetsJsonCache = null;
    private List<StreetMemory.Entry> streetsCache = null;

    /** calles guardadas (se vuelven a leer solo si han cambiado) */
    private List<StreetMemory.Entry> streetList() {
        try {
            String js = getSharedPreferences("portal", Context.MODE_PRIVATE).getString("bolt_streets", "");
            if (js == null) js = "";
            if (streetsCache == null || !js.equals(streetsJsonCache)) { streetsCache = StreetMemory.parseJson(js); streetsJsonCache = js; }
            return streetsCache;
        } catch (Exception e) { return null; }
    }

    /** apunta la zona que acabas de elegir en el aviso para la direccion de la recogida (solo hay botones cuando habia duda entre zonas) */
    private void rememberStreet(String street, String num, String cp, int kind) {
        try {
            if (street == null || street.length() == 0 || kind < 0 || kind > 2) return;
            StreetMemory.Addr a = StreetMemory.addrOf(street, num, cp);
            if (a == null) return;
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            List<StreetMemory.Entry> l = StreetMemory.parseJson(sp.getString("bolt_streets", ""));
            StreetMemory.put(l, a, kind, 'u', System.currentTimeMillis());
            sp.edit().putString("bolt_streets", StreetMemory.toJson(l)).apply();
        } catch (Exception e) { }
    }

    /** anota que una calle guardada se ha usado (como mucho cada 12 horas) para olvidar primero las que no se usan */
    private void touchStreet(OfferAnalyzer.Result r) {
        try {
            if (r == null || !"street".equals(r.estZoneSrc) || r.memKey == null || r.memKey.length() == 0) return;
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            List<StreetMemory.Entry> l = StreetMemory.parseJson(sp.getString("bolt_streets", ""));
            for (StreetMemory.Entry e : l) {
                if (!e.del && e.key().equals(r.memKey)) {
                    if (StreetMemory.touch(e, System.currentTimeMillis())) sp.edit().putString("bolt_streets", StreetMemory.toJson(l)).apply();
                    break;
                }
            }
        } catch (Exception e) { }
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
        if (aSum != null) aSum.setVisibility(View.GONE);
        if (aMain != null) aMain.setTextSize(CK * 18);
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

    private static String pct(double v) { return (v > 1e-9 ? "+" : (v < -1e-9 ? "\u2212" : "")) + num1(Math.abs(v)) + " %"; }

    /** linea de la zona de la recogida del aviso: cual es y de donde sale (zona dibujada, forzada en Ajustes o la de por defecto) */
    static String zoneLine(OfferAnalyzer.Result r) {
        String z = "Zona " + OfferAnalyzer.zoneName(r.estZone);
        String cp = r.estCpUnlisted != null && r.estCpUnlisted.length() > 0 ? " \u00B7 CP " + r.estCpUnlisted + " sin zona en tus listas" : "";
        if ("forced".equals(r.estZoneSrc)) return z + " (forzada en Ajustes)";
        if ("street".equals(r.estZoneSrc)) return z + " (calle guardada: " + (r.estArea == null ? "" : r.estArea) + (r.zoneAuto >= 0 && r.zoneAuto != r.estZone ? "; por ubicaci\u00F3n: " + OfferAnalyzer.zoneName(r.zoneAuto) : "") + ")" + cp;
        if ("manual".equals(r.estZoneSrc)) return z + " (elegida por ti" + (r.zoneAuto >= 0 ? "; por ubicaci\u00F3n: " + OfferAnalyzer.zoneName(r.zoneAuto) : "") + ")" + cp;
        String dud = r.zoneKinds != null && r.zoneKinds.length >= 2 ? " \u00B7 zona no confirmada: elige abajo" : "";   // v3.57: hay botones de zona y esta direccion no esta guardada
        if ("area".equals(r.estZoneSrc) || "postal".equals(r.estZoneSrc)) return z + (r.estArea != null && r.estArea.length() > 0 ? " (" + r.estArea + ")" : "") + cp + dud;
        String w = ZoneLocator.why();
        return z + " (" + (w.length() > 0 ? w + " \u2192 zona por defecto" : "fuera de tus zonas dibujadas") + ")" + cp + dud;
    }

    /** linea de la tarjeta usada: la del aeropuerto (recogidas) o la de la zona de la recogida, de valle o de hora punta */
    static String cardLine(OfferAnalyzer.Result r) {
        String per = r.estPeakUsed ? "hora punta" : "valle";
        if ("pickup".equals(r.estAirport)) {
            String ac = OfferAnalyzer.catLabel(r.estCat);   // v3.47: categoria (Comfort, XL, Premium) tambien en el aeropuerto
            return "Aeropuerto (recogida) \u00B7 tarjeta " + (ac.length() > 0 ? ac + " " : "") + "del aeropuerto \u00B7 " + per;
        }
        String cl = OfferAnalyzer.catLabel(r.estCat);   // v3.46: categoria (Comfort, XL, Premium)
        String t = "Tarjeta " + (cl.length() > 0 ? cl + " " : "") + "de zona " + OfferAnalyzer.zoneName(r.estZone) + " \u00B7 " + per;
        return "dest".equals(r.estAirport) ? "Aeropuerto (viaje hacia all\u00ED) \u00B7 " + t : t;
    }

    /** linea de la demanda: la que muestra la oferta (siempre se aplica), con el ajuste fino si lo hay */
    static String zoneDemand(OfferAnalyzer.Result r) {
        if (r.estOfferMult <= 0) return "Sin demanda en la oferta";
        String s = "Demanda \u00D7" + multTxt(r.estOfferMult) + " (de la oferta)";
        if (Math.abs(r.estFine) > 1e-9) s += " \u00B7 ajuste fino " + pct(r.estFine);
        return s;
    }

    /** viaje corto con demanda: el inicial real de Bolt sube de forma impredecible, asi que se da un rango de neto */
    static String rangeLine(OfferAnalyzer.Result r) {
        return "Viaje corto con demanda: el neto puede ir de " + OfferAnalyzer.money(r.estNetLo) + " a " + OfferAnalyzer.money(r.estNetHi) + " \u20AC";
    }

    /** hora punta ahora pero la tarifa de punta no sube tu precio (Ajustes): se dice lo que saldria si contara */
    static String peakLine(OfferAnalyzer.Result r) {
        if (r.estPeakShort) return "Hora punta, pero es un viaje largo: tarifa de valle";
        if (r.estWeekend && !r.estPeakUsed) return "Ahora es hora punta: no sube tu precio" + (r.estAlt >= 0 ? " (con tarifa de punta: neto " + OfferAnalyzer.money(r.estAlt) + " \u20AC)" : "");
        return "";
    }

    /** viaje largo (con o sin demanda desde la v3.56): el descuento medio de la tarjeta; en un lugar de evento, sin descuento (v3.34) */
    static String longLine(OfferAnalyzer.Result r) {
        if (Math.abs(r.estAdj) > 1e-9) return "Ajuste por distancia: " + pct(r.estAdj);   // v3.58
        if (r.estDisc > 1e-9) return "Viaje largo: precio base \u2212" + num1(r.estDisc) + " %";
        if (r.estEvent != null && r.estEvent.length() > 0) return "Lugar de evento (" + r.estEvent + "): sin descuento";
        return "";
    }

    private void showEstimateAlert(OfferAnalyzer.Result r) {
        try {
            if (alertView == null) buildAlert();
            final float d = getResources().getDisplayMetrics().density * CK;
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
            aChip.setText(ok ? "\u2713  ACEPTAR" : (no ? "\u2715  RECHAZAR" : ("WARN".equals(v) ? "\u26a0  A VALORAR" : "\u26a0  DATOS INSUFICIENTES")));
            paintPill(aP1, r.perHour > 0 ? r.stH : -1, f(r.perHour, 1) + " \u20ac/h");
            paintPill(aP2, r.perKm > 0 ? r.stK : -1, f(r.perKm, 2) + " \u20ac/km");
            paintPill(aP3, r.pickupKm > 0 ? r.stP : -1, "Recog. " + f(r.pickupKm, 1) + " km");
            if (aNetBox == null) {
                aNetBox = new LinearLayout(this);
                aNetBox.setOrientation(LinearLayout.VERTICAL);
                aNetBox.setGravity(Gravity.CENTER_HORIZONTAL);
                aNetLbl = new TextView(this);
                aNetLbl.setTextColor(Color.parseColor("#DCEBFF"));
                aNetLbl.setTextSize(CK * 12);
                aNetLbl.setTypeface(Typeface.DEFAULT_BOLD);
                aNetLbl.setGravity(Gravity.CENTER);
                aNetVal = new TextView(this);
                aNetVal.setTextColor(Color.WHITE);
                aNetVal.setTextSize(CK * 34);
                aNetVal.setTypeface(Typeface.DEFAULT_BOLD);
                aNetVal.setGravity(Gravity.CENTER);
                aNetBox.addView(aNetLbl);
                aNetBox.addView(aNetVal);
                LinearLayout.LayoutParams nlp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
                nlp.setMargins(0, (int) (8 * d), 0, 0);
                alertView.addView(aNetBox, 2, nlp);
                aSum = new TextView(this);
                aSum.setTextColor(Color.parseColor("#DCEBFF"));
                aSum.setTextSize(CK * 15);
                aSum.setGravity(Gravity.CENTER);
                aSum.setPadding(0, (int) (6 * d), 0, 0);
                aSum.setVisibility(View.GONE);
                alertView.addView(aSum, 3, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
            }
            GradientDrawable nb = new GradientDrawable();
            nb.setColor(Color.parseColor("#33000000"));
            nb.setCornerRadius(14 * d);
            nb.setStroke((int) (2 * d), col);
            aNetBox.setBackground(nb);
            aNetBox.setPadding((int) (10 * d), (int) (4 * d), (int) (10 * d), (int) (6 * d));
            aNetLbl.setText((r.estRange && r.estNetHi > r.estNetLo + 1e-9 ? "NETO ESTIMADO \u00B7 entre " + OfferAnalyzer.money(r.estNetLo) + " y " + OfferAnalyzer.money(r.estNetHi) + " \u20AC" : "NETO ESTIMADO") + (r.booking ? " \u00B7 RESERVA" : ""));
            aNetVal.setText(OfferAnalyzer.money(r.estNet) + " \u20ac");
            aNetBox.setVisibility(View.VISIBLE);
            aMain.setTextSize(CK * 15);
            if (r.estFee > 0) aMain.setText("Bruto est. " + OfferAnalyzer.money(r.estGross) + " \u20ac  \u2212  tasa aeropuerto " + OfferAnalyzer.money(r.estFee) + " \u20ac  =  " + OfferAnalyzer.money(Math.max(0, r.estGross - r.estFee)) + " \u20ac"
                + "\nComisi\u00f3n est. " + OfferAnalyzer.money(r.estComm) + " \u20ac (" + num1(r.estCommPct) + " %)");
            else aMain.setText("Bruto est. " + OfferAnalyzer.money(r.estGross) + " \u20ac  \u00b7  Comisi\u00f3n est. " + OfferAnalyzer.money(r.estComm) + " \u20ac (" + num1(r.estCommPct) + " %)");
            StringBuilder dt = new StringBuilder();
            dt.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)\n");
            dt.append(cardLine(r)).append("\n");
            if (!"pickup".equals(r.estAirport)) dt.append(zoneLine(r)).append("\n");   // la recogida en el aeropuerto usa su propia tarjeta: la zona no pinta nada
            dt.append(zoneDemand(r)).append("\n");
            if (r.estRange) dt.append(rangeLine(r)).append("\n");
            if (peakLine(r).length() > 0) dt.append(peakLine(r)).append("\n");
            if (longLine(r).length() > 0) dt.append(longLine(r)).append("\n");
            if (r.estMinApplied) dt.append("Se aplic\u00f3 la tarifa m\u00ednima estimada\n");
            if (r.pickupKm > 0 || r.pickupMin > 0) {
                dt.append("Recogida (no cuenta en el precio): ");
                if (r.pickupMin > 0) dt.append((int) r.pickupMin).append(" min");
                if (r.pickupKm > 0) dt.append(r.pickupMin > 0 ? " (" : "").append(f(r.pickupKm, 1)).append(" km").append(r.pickupMin > 0 ? ")" : "");
                dt.append("\n");
            }
            dt.append(r.reason);
            dt.append("\nPrecio ESTIMADO con tarifas aproximadas (no son las oficiales de Bolt)");
            aDetail.setText(dt.toString());
            StringBuilder sm = new StringBuilder();          // v3.62: las lineas sencillas de \u00ABMas datos\u00BB: viaje, recogida y reserva (el bruto y la comision son aMain)
            sm.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)");
            if (r.pickupKm > 0 || r.pickupMin > 0) {
                sm.append("\nRecogida: ");
                if (r.pickupMin > 0) sm.append((int) r.pickupMin).append(" min");
                if (r.pickupKm > 0) sm.append(r.pickupMin > 0 ? " (" : "").append(f(r.pickupKm, 1)).append(" km").append(r.pickupMin > 0 ? ")" : "");
            }
            if (r.booking) sm.append("\nEs una reserva");
            aSum.setText(sm.toString());
            if (!alertShown) { wm.addView(alertView, alp); alertShown = true; }
            updateTab(r, true);
            updateZoneChips(r);
        } catch (Exception e) { }
    }

    // ===================== v3.62: lengueta «Mas datos» + botones ✗ «No la hice» / ✓ «La acepte» =====================
    // El cartel (que no se toca) sale plegado: veredicto, tres datos y neto. Debajo, una ventana aparte (esta SI se toca): «Mas datos» abre el resto
    // y los botones apuntan la oferta en la tasa (dejan la marca en las preferencias y el Portal la recoge con tripCur, este abierto o no).
    private void updateTab(OfferAnalyzer.Result r, boolean estimated) {
        try {
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            long now = System.currentTimeMillis();
            long seq = TabLogic.seq(sp);
            if (seq != tabOpenSeq) { tabOpenSeq = seq; tabLevel = 0; }         // cada oferta nueva empieza plegada
            tabLastEst = estimated;
            rh.removeCallbacks(tabHideRun);
            boolean fold = TabLogic.fold(sp);
            boolean logged = !tabDemo && r != null && r.offer && r.isBolt && !r.unreadable && TabLogic.buttons(sp) && seq > 0 && now - sp.getLong("trip_ts", 0L) <= TabLogic.VALID_MS;
            applyFold(fold);
            if (!fold && !logged) { hideTab(); return; }                      // completo y sin botones: nada debajo
            tabMode = 1;
            buildTab();
            String v = r == null ? "" : r.verdict;
            int col = "OK".equals(v) ? Color.parseColor("#22C55E") : ("NO".equals(v) ? Color.parseColor("#EF4444") : Color.parseColor("#F59E0B"));
            paintTabBg(col);
            tabTitle.setVisibility(View.GONE);
            paintTabMore(fold);
            paintTabButtons(logged, sp, seq);
            showTabWindow();
        } catch (Exception e) { }
    }

    /**
     * plegado = veredicto, tres datos y neto (en el aviso sin neto estimado queda el precio).
     * \u00ABMas datos\u00BB = 4 lineas sencillas (viaje, recogida, bruto y comision, reserva). \u00ABCalculo completo\u00BB = todas las lineas de siempre. Ajuste \u00ABcompleto\u00BB = todo, como antes.
     */
    private void applyFold(boolean fold) {
        int lv = fold ? tabLevel : 2;
        if (tabLastEst) {
            if (aSum != null) aSum.setVisibility(lv == 1 ? View.VISIBLE : View.GONE);
            if (aMain != null) aMain.setVisibility(lv >= 1 ? View.VISIBLE : View.GONE);
            if (aDetail != null) aDetail.setVisibility(lv == 2 ? View.VISIBLE : View.GONE);
        } else {
            if (aSum != null) aSum.setVisibility(View.GONE);
            if (aMain != null) aMain.setVisibility(View.VISIBLE);
            if (aDetail != null) aDetail.setVisibility(lv >= 1 ? View.VISIBLE : View.GONE);
        }
    }

    private void paintTabMore(boolean fold) {
        tabMoreRow.setVisibility(fold ? View.VISIBLE : View.GONE);
        tabMore.setText(tabLevel == 0 ? "\u25BE  M\u00E1s datos" : "\u25B4  Menos datos");
        tabCalc.setVisibility(fold && tabLevel == 1 && tabLastEst ? View.VISIBLE : View.GONE);
    }

    private void paintTabBg(int col) {
        final float d = getResources().getDisplayMetrics().density * CK;
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.parseColor("#F00A2E70"));
        bg.setCornerRadius(20 * d);
        bg.setStroke((int) (3 * d), col);
        tabView.setBackground(bg);
    }

    private void paintTabButtons(boolean logged, SharedPreferences sp, long seq) {
        int dec = TabLogic.decision(sp, seq);
        if (dec >= 0) {
            tabBtns.setVisibility(View.GONE);
            tabMsg.setVisibility(View.VISIBLE);
            tabMsg.setTextColor(Color.parseColor(dec == 1 ? "#86EFAC" : "#FCA5A5"));
            tabMsg.setText(dec == 1 ? "\u2713  Apuntada: la aceptaste" : "\u2715  Apuntada: no la hiciste");
        } else if (logged) {
            tabBtns.setVisibility(View.VISIBLE);
            tabMsg.setVisibility(View.GONE);
        } else {
            tabBtns.setVisibility(View.GONE);
            tabMsg.setVisibility(View.GONE);
        }
        paintTabRate(sp, seq, dec < 0 && logged);
    }

    private static int rateColor(char z) {
        return Color.parseColor(z == 'g' ? "#86EFAC" : z == 'o' ? "#FCD34D" : z == 'r' ? "#FCA5A5" : "#AFCBFF");
    }

    /** v3.63: lo que le pasa a tu tasa si dejas pasar la oferta o la aceptas (solo mientras se puede marcar) */
    private void paintTabRate(SharedPreferences sp, long seq, boolean show) {
        try {
            if (tabRate == null) return;
            TabLogic.Rate rt = null;
            if (show) {
                boolean nx = sp.getBoolean("trip_nofx", false);
                int sec = (int) Math.max(5, Math.min(300, sp.getInt("trip_asg_sec", 30)));
                rt = TabLogic.rate(sp, System.currentTimeMillis(), seq, nx, nx && sp.getBoolean("trip_asg_on", false), sec);
            }
            if (rt == null) { tabRate.setVisibility(View.GONE); return; }
            tabRateA.setText(rt.a);
            tabRateA.setTextColor(rateColor(rt.za));
            tabRateB.setText(rt.b);
            tabRateB.setTextColor(rateColor(rt.zb));
            tabRateB.setVisibility(rt.b.length() == 0 ? View.GONE : View.VISIBLE);
            tabRate.setVisibility(View.VISIBLE);
        } catch (Exception e) { }
    }

    private void buildTab() {
        if (tabView != null) return;
        final float d = getResources().getDisplayMetrics().density * CK;
        tabView = new LinearLayout(this);
        tabView.setOrientation(LinearLayout.VERTICAL);
        tabView.setGravity(Gravity.CENTER_HORIZONTAL);
        tabView.setPadding((int) (10 * d), (int) (2 * d), (int) (10 * d), (int) (10 * d));
        tabTitle = new TextView(this);
        tabTitle.setTextColor(Color.WHITE);
        tabTitle.setTextSize(CK * 15);
        tabTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tabTitle.setGravity(Gravity.CENTER);
        tabTitle.setPadding(0, (int) (8 * d), 0, (int) (4 * d));
        tabTitle.setText("\u00BFLa aceptaste?");
        tabMore = new TextView(this);
        tabMore.setTextColor(Color.parseColor("#AFCBFF"));
        tabMore.setTextSize(CK * 15);
        tabMore.setTypeface(Typeface.DEFAULT_BOLD);
        tabMore.setGravity(Gravity.CENTER);
        tabMore.setMinHeight((int) (38 * d));
        tabMore.setPadding(0, (int) (6 * d), 0, (int) (4 * d));
        tabMore.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { tabToggle(); } });
        tabCalc = new TextView(this);
        tabCalc.setTextColor(Color.parseColor("#AFCBFF"));
        tabCalc.setTextSize(CK * 15);
        tabCalc.setTypeface(Typeface.DEFAULT_BOLD);
        tabCalc.setGravity(Gravity.CENTER);
        tabCalc.setMinHeight((int) (38 * d));
        tabCalc.setPadding(0, (int) (6 * d), 0, (int) (4 * d));
        tabCalc.setText("\u25BE  C\u00E1lculo completo");
        tabCalc.setVisibility(View.GONE);
        tabCalc.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { tabCalcOpen(); } });
        tabMoreRow = new LinearLayout(this);
        tabMoreRow.setOrientation(LinearLayout.HORIZONTAL);
        tabMoreRow.setGravity(Gravity.CENTER);
        tabMoreRow.addView(tabMore, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        tabMoreRow.addView(tabCalc, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        tabBtns = new LinearLayout(this);
        tabBtns.setOrientation(LinearLayout.HORIZONTAL);
        tabBtns.setGravity(Gravity.CENTER);
        tabNo = tabButton("\u2715  No la hice", "#DC2626", false);
        tabYes = tabButton("\u2713  La acept\u00E9", "#16A34A", true);
        LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(0, (int) (48 * getResources().getDisplayMetrics().density), 1f);
        blp.setMargins((int) (4 * d), 0, (int) (4 * d), 0);
        tabBtns.addView(tabNo, blp);
        tabBtns.addView(tabYes, blp);
        tabMsg = new TextView(this);
        tabMsg.setTextSize(CK * 16);
        tabMsg.setTypeface(Typeface.DEFAULT_BOLD);
        tabMsg.setGravity(Gravity.CENTER);
        tabMsg.setPadding(0, (int) (8 * d), 0, (int) (2 * d));
        tabRateA = new TextView(this);
        tabRateB = new TextView(this);
        for (TextView tv : new TextView[]{tabRateA, tabRateB}) {
            tv.setTextSize(CK * 15);
            tv.setTypeface(Typeface.DEFAULT_BOLD);
            tv.setGravity(Gravity.CENTER);
            tv.setPadding((int) (4 * d), (int) (6 * d), (int) (4 * d), (int) (4 * d));
        }
        tabRate = new LinearLayout(this);   // v3.63: «Dejarla: 87,3 %  ·  Aceptarla: 90,0 %» encima de los botones (lo que le pasa a la tasa)
        tabRate.setOrientation(LinearLayout.HORIZONTAL);
        tabRate.setGravity(Gravity.CENTER);
        tabRate.addView(tabRateA, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        tabRate.addView(tabRateB, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        tabRate.setVisibility(View.GONE);
        tabView.addView(tabTitle);
        tabView.addView(tabMoreRow);
        tabView.addView(tabRate);
        tabView.addView(tabBtns);
        tabView.addView(tabMsg);
        int w = alp != null ? alp.width : (int) Math.min(getResources().getDisplayMetrics().widthPixels * 0.94f, 400 * d);
        tabLp = new WindowManager.LayoutParams(w, WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT);
        tabLp.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        tabLp.y = alp != null ? alp.y : (int) (70 * getResources().getDisplayMetrics().density);
        tabView.addOnLayoutChangeListener(new View.OnLayoutChangeListener() {
            @Override public void onLayoutChange(View v, int l, int t, int rr, int bb, int ol, int ot, int orr, int obb) { placeZoneChips(); }
        });
    }

    /** \u00ABMas datos\u00BB (plegado -> 4 lineas) / \u00ABMenos datos\u00BB (vuelve a plegar) */
    private void tabToggle() {
        try {
            tabLevel = tabLevel == 0 ? 1 : 0;
            tabRefresh();
        } catch (Exception e) { }
    }

    /** \u00ABCalculo completo\u00BB: todas las lineas de siempre (tarjeta, zona, demanda, ajustes...) */
    private void tabCalcOpen() {
        try {
            tabLevel = 2;
            tabRefresh();
        } catch (Exception e) { }
    }

    private void tabRefresh() {
        boolean fold = TabLogic.fold(getSharedPreferences("portal", Context.MODE_PRIVATE));
        applyFold(fold);
        paintTabMore(fold);
        placeTab();
        placeZoneChips();
    }

    private TextView tabButton(String txt, String color, final boolean yes) {
        final float d = getResources().getDisplayMetrics().density * CK;
        TextView b = new TextView(this);
        b.setText(txt);
        b.setTextColor(Color.WHITE);
        b.setTextSize(CK * 18);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setGravity(Gravity.CENTER);
        GradientDrawable g = new GradientDrawable();
        g.setCornerRadius(16 * d);
        g.setColor(Color.parseColor(color));
        b.setBackground(g);
        b.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { tabMark(yes); } });
        return b;
    }

    private void showTabWindow() {
        try {
            if (!tabListen && alertView != null) {
                alertView.addOnLayoutChangeListener(new View.OnLayoutChangeListener() {
                    @Override public void onLayoutChange(View v, int l, int t, int rr, int bb, int ol, int ot, int orr, int obb) { placeTab(); }
                });
                tabListen = true;
            }
            if (!tabShown) { wm.addView(tabView, tabLp); tabShown = true; }
            placeTab();
            placeZoneChips();
        } catch (Exception e) { }
    }

    /** va justo debajo del cartel (o, si el cartel ya no esta, en su sitio) */
    private void placeTab() {
        try {
            if (!tabShown || tabView == null || tabLp == null || alp == null) return;
            final float d = getResources().getDisplayMetrics().density;
            int y = (tabMode == 2 || !alertShown || alertView == null) ? alp.y : alp.y + alertView.getHeight() + (int) (4 * d);
            if (tabLp.y != y) { tabLp.y = y; wm.updateViewLayout(tabView, tabLp); }
        } catch (Exception e) { }
    }

    /** lo que ocupa la lengueta para bajar los botones de zona */
    private int tabExtra() {
        try {
            if (tabShown && tabMode == 1 && tabView != null) return tabView.getHeight() + (int) (4 * getResources().getDisplayMetrics().density);
        } catch (Exception e) { }
        return 0;
    }

    private void hideTab() {
        rh.removeCallbacks(tabHideRun);
        try { if (tabShown && tabView != null) wm.removeView(tabView); } catch (Exception e) { }
        tabShown = false;
        tabMode = 0;
    }

    /** la oferta ha desaparecido: ✗ / ✓ siguen 15 s mas (solo los botones, donde estaba el cartel) por si quieres marcarla ahora */
    private void startAfter() {
        try {
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            if (tabDemo || !TabLogic.canMark(sp, System.currentTimeMillis())) return;
            tabMode = 2;
            buildTab();
            paintTabBg(Color.parseColor("#3B82F6"));
            tabTitle.setVisibility(View.VISIBLE);
            tabMoreRow.setVisibility(View.GONE);
            paintTabButtons(true, sp, TabLogic.seq(sp));
            showTabWindow();
            rh.removeCallbacks(tabHideRun);
            rh.postDelayed(tabHideRun, TabLogic.AFTER_MS);
        } catch (Exception e) { }
    }

    /** ✗ / ✓ tocados: se deja la marca para el Portal */
    private void tabMark(boolean yes) {
        try {
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            long seq = TabLogic.seq(sp);
            if (!TabLogic.mark(sp, yes, System.currentTimeMillis())) return;
            paintTabButtons(true, sp, seq);
            placeTab();
            placeZoneChips();
            if (tabMode == 2) { rh.removeCallbacks(tabHideRun); rh.postDelayed(tabHideRun, 1600L); }
        } catch (Exception e) { }
    }

    // ===================== v3.37: botones de zona (solo Bolt, solo cuando hay duda) =====================
    // Si la zona de la recogida sale de TU ubicacion y cerca hay otra zona (o el codigo postal de la oferta no esta en tus listas), debajo del aviso salen
    // unos botones con las zonas posibles y el neto con cada una. Tocas uno y se recalcula al momento. Es una ventana aparte, pequena, porque la del aviso no se toca.
    private void hideZoneChips() {
        try { if (zcShown && zcView != null) wm.removeView(zcView); } catch (Exception e) { }
        zcShown = false;
        zcSig = "";
    }

    private void placeZoneChips() {
        try {
            if (!zcShown || zcView == null || zcp == null || alertView == null || alp == null) return;
            final float d = getResources().getDisplayMetrics().density;
            int y = alp.y + alertView.getHeight() + (int) (6 * d) + tabExtra();
            if (zcp.y != y) { zcp.y = y; wm.updateViewLayout(zcView, zcp); }
        } catch (Exception e) { }
    }

    private void chooseZone(int kind, int auto, String sig, String street, String num, String cp) {
        try {
            manualKind = kind == auto ? -1 : kind;
            manualSig = manualKind < 0 || sig == null ? "" : sig;
            manualTs = System.currentTimeMillis();
            rememberStreet(street, num, cp, kind);      // v3.57: la zona que eliges se guarda con la direccion de la recogida
            zcSig = "";
            evaluateOffer();      // se vuelve a leer la oferta que sigue en pantalla y se recalcula con la zona elegida
        } catch (Exception e) { }
    }

    private void updateZoneChips(final OfferAnalyzer.Result r) {
        try {
            if (r == null || r.zoneKinds == null || r.zoneKinds.length < 2 || r.zoneNets == null || r.zoneNets.length != r.zoneKinds.length || r.baseSig == null || r.baseSig.length() == 0) { hideZoneChips(); return; }
            final float d = getResources().getDisplayMetrics().density;
            StringBuilder sg = new StringBuilder(r.baseSig).append('#').append(r.estZone).append('#').append(r.zoneAuto);
            for (int i = 0; i < r.zoneKinds.length; i++) sg.append('#').append(r.zoneKinds[i]).append(':').append(Math.round(r.zoneNets[i] * 100));
            String sig = sg.toString();
            if (zcView == null) {
                zcView = new LinearLayout(this);
                zcView.setOrientation(LinearLayout.HORIZONTAL);
                zcView.setGravity(Gravity.CENTER);
                GradientDrawable bgz = new GradientDrawable();
                bgz.setColor(Color.parseColor("#F00A2E70"));
                bgz.setCornerRadius(22 * d);
                zcView.setBackground(bgz);
                zcView.setPadding((int) (8 * d), (int) (6 * d), (int) (8 * d), (int) (6 * d));
                zcp = new WindowManager.LayoutParams(WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
                        WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                        WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                        PixelFormat.TRANSLUCENT);
                zcp.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
                zcp.y = (alp != null ? alp.y : (int) (70 * d)) + (int) (200 * d);
            }
            if (!zcListen && alertView != null) {
                alertView.addOnLayoutChangeListener(new View.OnLayoutChangeListener() {
                    @Override public void onLayoutChange(View v, int l, int t, int rr, int bb, int ol, int ot, int orr, int obb) { placeZoneChips(); }
                });
                zcListen = true;
            }
            if (!sig.equals(zcSig) || !zcShown) {
                zcView.removeAllViews();
                TextView lab = new TextView(this);
                lab.setText("Zona:");
                lab.setTextColor(Color.parseColor("#DCEBFF"));
                lab.setTextSize(13);
                lab.setTypeface(Typeface.DEFAULT_BOLD);
                lab.setGravity(Gravity.CENTER);
                lab.setPadding((int) (4 * d), 0, (int) (4 * d), 0);
                zcView.addView(lab);
                final String sigC = r.baseSig;
                final int autoC = r.zoneAuto;
                final String stS = r.pickStreet, stN = r.pickNum, stC = r.pickCp;   // v3.57
                for (int i = 0; i < r.zoneKinds.length; i++) {
                    final int kind = r.zoneKinds[i];
                    boolean sel = kind == r.estZone;
                    String nm = OfferAnalyzer.zoneName(kind);
                    TextView c = new TextView(this);
                    c.setText(Character.toUpperCase(nm.charAt(0)) + nm.substring(1) + "  " + OfferAnalyzer.money(r.zoneNets[i]) + " \u20AC");
                    c.setTextColor(Color.WHITE);
                    c.setTextSize(15);
                    c.setTypeface(Typeface.DEFAULT_BOLD);
                    c.setGravity(Gravity.CENTER);
                    c.setMinHeight((int) (44 * d));
                    c.setPadding((int) (12 * d), (int) (6 * d), (int) (12 * d), (int) (6 * d));
                    GradientDrawable g = new GradientDrawable();
                    g.setCornerRadius(16 * d);
                    g.setColor(Color.parseColor(sel ? "#2563EB" : "#1E3A8A"));
                    g.setStroke((int) (2 * d), Color.parseColor(sel ? "#FFFFFF" : "#60A5FA"));
                    c.setBackground(g);
                    c.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { chooseZone(kind, autoC, sigC, stS, stN, stC); } });
                    LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
                    clp.setMargins((int) (3 * d), 0, (int) (3 * d), 0);
                    zcView.addView(c, clp);
                }
                zcSig = sig;
            }
            if (!zcShown) { wm.addView(zcView, zcp); zcShown = true; }
            placeZoneChips();
        } catch (Exception e) { }
    }

    /** prueba desde Ajustes: oferta de Bolt de ejemplo (8,3 km, 12 min, x1,4) con TUS tarifas; se ve y se oye */
    public void demoBolt() {
        try {
            List<String> n = new ArrayList<String>();
            for (String s : new String[]{"x1.4", "6 min", "\u2022", "2.1 km", "Calle de ejemplo", "12 min", "\u2022", "8.3 km", "Destino de ejemplo", "Aceptar"}) n.add(s);
            OfferAnalyzer.Result r = OfferAnalyzer.analyze(n, rentParams(), false, true);
            lastVoice = null;
            tabDemo = true;
            showAlert(r);
            hideZoneChips();
            speakOffer(r);
            rh.removeCallbacks(hideRun);
            rh.postDelayed(hideRun, 9000);
        } catch (Exception e) { }
    }

    public void forceBubble() {
        forced = true;
        refreshBubble();
        rh.removeCallbacks(unforceRun);
        rh.postDelayed(unforceRun, 6000);
    }

    public JSONObject bubbleDiag() {
        JSONObject o = new JSONObject();
        try {
            o.put("serviceOn", true);
            o.put("bubbleOn", bubbleOn(this));
            o.put("fgPkg", fgPkg);
            o.put("matchesDriver", DRIVER.matcher(fgPkg).find());
            o.put("shown", shown);
            o.put("puesta", showCount); /*v330-diag*/
            o.put("quitada", hideCount);
            o.put("log", fgLogText());
        } catch (Exception e) { }
        return o;
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
