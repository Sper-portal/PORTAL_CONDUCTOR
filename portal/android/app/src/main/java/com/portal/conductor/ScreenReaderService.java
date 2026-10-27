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
    private static final Pattern AMT = Pattern.compile("(\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}[.,]\\d{2})(?!\\d)\\s*(\\u20AC|[eE][uU][rR]\\b)?");
    private static final Pattern TOTAL = Pattern.compile("\\btotal\\b");

    private WindowManager wm;
    private ImageView bubble;
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
        applyRentConfig();
    }

    @Override public boolean onUnbind(Intent i) {
        hideBubble();
        hideAlert();
        shutdownTts();
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
                        fgPkg = ap;
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
        fgPkg = pkg;
        refreshBubble();
        if (trackOn(this) && DRIVER.matcher(pkg).find()) scheduleEval();
    }

    @Override public void onInterrupt() { }

    public void postRefresh() {
        new Handler(Looper.getMainLooper()).post(new Runnable() {
            @Override public void run() { refreshBubble(); }
        });
    }

    private void refreshBubble() {
        applyRentConfig();
        boolean want = forced || (bubbleOn(this) && !fgPkg.equals(getPackageName()) && DRIVER.matcher(fgPkg).find());
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

    // ===== Rentabilidad de viajes + diagnostico de la burbuja (v3.9) =====
    private final Handler rh = new Handler(Looper.getMainLooper());
    private boolean evalPending = false;
    private long lastOfferSeen = 0;
    private LinearLayout alertView;
    private TextView aChip, aMain, aDetail;
    private boolean alertShown = false;
    private boolean forced = false;
    private WindowManager.LayoutParams alp;
    private final Runnable evalRun = new Runnable() { @Override public void run() { evalPending = false; evaluateOffer(); } };
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
        JSONArray wins = readAll(ownPkg);
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
            try {
                List<AccessibilityWindowInfo> ws = getWindows();
                boolean any = false, uber = false;
                if (ws != null) for (AccessibilityWindowInfo w : ws) {
                    AccessibilityNodeInfo rt = w.getRoot();
                    if (rt == null) continue;
                    CharSequence pk = rt.getPackageName();
                    if (pk != null && DRIVER.matcher(pk).find() && !pk.toString().equals(getPackageName())) {
                        any = true;
                        if (OCR_PKG.matcher(pk).find()) uber = true;
                    }
                }
                if (any) {
                    getSharedPreferences("portal", Context.MODE_PRIVATE).edit().putLong("rent_seenTs", System.currentTimeMillis()).apply();
                    scheduleEval();
                }
                if (uber && System.currentTimeMillis() - treeFoundTs > 3000) ocrTick();
            } catch (Exception e) { }
            rh.postDelayed(this, 1500);
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
        p.weekendNow = OfferAnalyzer.isWeekend(p.bolt, java.util.Calendar.getInstance());
        return p;
    }

    // ---- lectura por imagen (OCR): para apps que esconden la oferta al lector de accesibilidad (Uber) ----
    private boolean ocrBusy = false;
    private long ocrNextAt = 0, ocrFoundTs = 0;
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

    private void ocrTick() {
        if (android.os.Build.VERSION.SDK_INT < 30) { setOcrState("No disponible: hace falta Android 11 o superior."); return; }
        long now = System.currentTimeMillis();
        if (ocrBusy || now < ocrNextAt) return;
        final Rect area = uberBounds();
        if (area == null) return;
        ocrBusy = true;
        ocrNextAt = now + 2000;
        try {
            takeScreenshot(android.view.Display.DEFAULT_DISPLAY, getMainExecutor(), new TakeScreenshotCallback() {
                @Override public void onSuccess(ScreenshotResult sr) {
                    try {
                        Bitmap hw = Bitmap.wrapHardwareBuffer(sr.getHardwareBuffer(), sr.getColorSpace());
                        if (hw == null) { ocrBusy = false; setOcrState("La captura llego vacia."); return; }
                        Bitmap bmp = hw.copy(Bitmap.Config.ARGB_8888, true);
                        hw.recycle();
                        sr.getHardwareBuffer().close();
                        runOcr(bmp, area);
                    } catch (Throwable t) { ocrBusy = false; setOcrState("Error al procesar la captura: " + t); }
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

    private void runOcr(Bitmap full, Rect area) {
        try {
            // se tapa nuestro propio aviso para no leernos a nosotros mismos
            if (alertShown && alertView != null) {
                int[] loc = new int[2];
                alertView.getLocationOnScreen(loc);
                Paint pt = new Paint();
                pt.setColor(Color.BLACK);
                new Canvas(full).drawRect(loc[0], loc[1], loc[0] + alertView.getWidth(), loc[1] + alertView.getHeight(), pt);
            }
            int x = Math.max(0, area.left), y = Math.max(0, area.top);
            int w = Math.min(full.getWidth() - x, area.width()), h = Math.min(full.getHeight() - y, area.height());
            if (w < 80 || h < 80) { ocrBusy = false; return; }
            Bitmap crop = Bitmap.createBitmap(full, x, y, w, h);
            if (recognizer == null) recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
            recognizer.process(InputImage.fromBitmap(crop, 0))
                .addOnSuccessListener(new OnSuccessListener<Text>() {
                    @Override public void onSuccess(Text text) { ocrBusy = false; onOcrText(text); }
                })
                .addOnFailureListener(new OnFailureListener() {
                    @Override public void onFailure(Exception e) { ocrBusy = false; setOcrState("Fallo del reconocimiento: " + e); }
                });
        } catch (Throwable t) { ocrBusy = false; setOcrState("Fallo en la lectura por imagen: " + t); }
    }

    private void onOcrText(Text text) {
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
        setOcrState(lines.size() + " lineas leidas por imagen" + (r.offer ? " - oferta reconocida" : (r.acceptSeen ? " - veo el boton Aceptar pero no entendi la oferta" : "")));
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

    private void evaluateOffer() {
        if (!trackOn(this)) return;
        try {
            JSONArray wins = readAll(getPackageName());
            updateCache(wins);
            if (!rentOn(this)) return;
            SharedPreferences sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
            long now = System.currentTimeMillis();
            OfferAnalyzer.Result found = null, unreadable = null;
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
                if (all.contains("\u20AC") || all.toLowerCase().contains("km")) {
                    sp.edit().putLong("rent_evalTs", now).putString("rent_why", r.offer
                        ? ("Oferta reconocida: " + r.verdict + (r.estimated ? " | neto estimado Bolt " : " | precio ") + r.price + " | viaje " + r.tripKm + " km/" + r.tripMin + " min | recogida " + r.pickupKm + " km/" + r.pickupMin + " min" + (r.orderAssumed ? " (orden estimado)" : ""))
                        : ("Texto con importes o km, pero NO reconocido como oferta: " + r.why)).apply();
                }
                if (r.offer || r.acceptSeen || (all.contains("\u20AC") && all.toLowerCase().contains("km"))) {
                    String info = r.offer ? ("veredicto=" + r.verdict + (r.estimated ? " netoEstimadoBolt=" : " precio=") + r.price + " viajeKm=" + r.tripKm + " viajeMin=" + r.tripMin + " recogidaKm=" + r.pickupKm + " recogidaMin=" + r.pickupMin + (r.orderAssumed ? " (orden asumido)" : "")) : "no reconocida como oferta";
                    sp.edit().putString("rent_lastText", pkg + "\n" + all).putString("rent_lastInfo", info).apply();
                }
                if (r.offer) { found = r; break; }
                else if (r.acceptSeen && unreadable == null) { r.unreadable = true; r.verdict = "DATA"; r.reason = "No pude leer los datos de esta oferta."; unreadable = r; }
            }
            if (now - lastSnapTs > 3000) lastSnapTs = now;
            if (found != null) treeFoundTs = now;
            if (found == null && ocrFound != null && now - ocrFoundTs < 4500 && !ocrFound.unreadable) found = ocrFound;
            if (found == null && unreadable != null) found = unreadable;
            if (found == null && ocrFound != null && now - ocrFoundTs < 4500) found = ocrFound;
            if (found != null) {
                lastOfferSeen = now;
                showAlert(found);
                speakOffer(found);
                rh.removeCallbacks(hideRun);
                rh.postDelayed(hideRun, 25000);
            } else if (alertShown && now - lastOfferSeen > 1800) {
                hideAlert();
            }
        } catch (Exception e) { }
    }

    private LinearLayout aRow;
    private TextView aP1, aP2, aP3;

    private TextView pill() {
        final float d = getResources().getDisplayMetrics().density;
        TextView t = new TextView(this);
        t.setTextColor(Color.WHITE);
        t.setTextSize(14);
        t.setGravity(Gravity.CENTER);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setPadding((int) (9 * d), (int) (5 * d), (int) (9 * d), (int) (5 * d));
        return t;
    }

    private void paintPill(TextView t, int st, String text) {
        if (st < 0) { t.setVisibility(View.GONE); return; }
        final float d = getResources().getDisplayMetrics().density;
        GradientDrawable g = new GradientDrawable();
        g.setColor(st == 0 ? Color.parseColor("#16A34A") : (st == 1 ? Color.parseColor("#F59E0B") : Color.parseColor("#DC2626")));
        g.setCornerRadius(12 * d);
        t.setBackground(g);
        t.setTextColor(st == 1 ? Color.BLACK : Color.WHITE);
        t.setText(text);
        t.setVisibility(View.VISIBLE);
    }

    private void buildAlert() {
        final float d = getResources().getDisplayMetrics().density;
        alertView = new LinearLayout(this);
        alertView.setOrientation(LinearLayout.VERTICAL);
        alertView.setGravity(Gravity.CENTER_HORIZONTAL);
        alertView.setPadding((int) (14 * d), (int) (10 * d), (int) (14 * d), (int) (12 * d));
        aChip = new TextView(this);
        aChip.setTextColor(Color.WHITE);
        aChip.setTextSize(20);
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
        aMain.setTextSize(18);
        aMain.setGravity(Gravity.CENTER);
        aMain.setTypeface(Typeface.DEFAULT_BOLD);
        aMain.setPadding(0, (int) (8 * d), 0, 0);
        aDetail = new TextView(this);
        aDetail.setTextColor(Color.parseColor("#DCEBFF"));
        aDetail.setTextSize(14);
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
        alp.y = (int) (70 * d);
    }

    private static String f(double v, int dec) { return String.format(java.util.Locale.GERMANY, "%." + dec + "f", v); }

    private void showAlert(OfferAnalyzer.Result r) {
        if (r.estimated) { showEstimateAlert(r); return; }
        resetEstimateViews();
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
            aChip.setText(ok ? "\u2713  ACEPTAR" : (no ? "\u2715  RECHAZAR" : ("WARN".equals(v) ? "\u26A0  A VALORAR" : "\u26A0  DATOS INSUFICIENTES")));
            paintPill(aP1, r.perHour > 0 ? r.stH : -1, f(r.perHour, 1) + " \u20AC/h");
            paintPill(aP2, r.perKm > 0 ? r.stK : -1, f(r.perKm, 2) + " \u20AC/km");
            paintPill(aP3, r.pickupKm > 0 ? r.stP : -1, "Recog. " + f(r.pickupKm, 1) + " km");
            if (r.unreadable) aMain.setText("No pude leer la oferta");
            else if (r.price > 0) aMain.setText("Precio " + f(r.price, 2) + " \u20AC");
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
        } catch (Exception e) { }
    }

    private void hideAlert() {
        stopSpeech();
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
            aNetVal.setText(OfferAnalyzer.money(r.estNet) + " \u20ac");
            aNetBox.setVisibility(View.VISIBLE);
            aMain.setTextSize(15);
            aMain.setText("Bruto est. " + OfferAnalyzer.money(r.estGross) + " \u20ac  \u00b7  Comisi\u00f3n est. " + OfferAnalyzer.money(r.estComm) + " \u20ac (" + num1(r.estCommPct) + " %)");
            StringBuilder dt = new StringBuilder();
            dt.append("Viaje con pasajero: ").append((int) Math.round(r.tripMin)).append(" min (").append(num1(r.tripKm)).append(" km)\n");
            String rango = r.estHi < 0 ? ("m\u00e1s de " + num1(r.estLo) + " km") : (r.estLo <= 0 ? ("hasta " + num1(r.estHi) + " km") : (num1(r.estLo) + "\u2013" + num1(r.estHi) + " km"));
            dt.append("Tramo ").append(r.estTier).append(" (").append(rango).append(") \u00b7 ").append(r.estWeekend ? "fin de semana / festivo" : "lunes a viernes").append("\n");
            dt.append("Demanda \u00d7").append(multTxt(r.estMult)).append(r.estOfferMult > 0 ? " (de la oferta)" : "").append(" \u00b7 modo ").append(r.estMode).append("\n");
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
            if (!alertShown) { wm.addView(alertView, alp); alertShown = true; }
        } catch (Exception e) { }
    }

    /** prueba desde Ajustes: oferta de Bolt de ejemplo (8,3 km, 12 min, x1,4) con TUS tarifas; se ve y se oye */
    public void demoBolt() {
        try {
            List<String> n = new ArrayList<String>();
            for (String s : new String[]{"x1.4", "6 min", "\u2022", "2.1 km", "Calle de ejemplo", "12 min", "\u2022", "8.3 km", "Destino de ejemplo", "Aceptar"}) n.add(s);
            OfferAnalyzer.Result r = OfferAnalyzer.analyze(n, rentParams(), false, true);
            lastVoice = null;
            showAlert(r);
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
