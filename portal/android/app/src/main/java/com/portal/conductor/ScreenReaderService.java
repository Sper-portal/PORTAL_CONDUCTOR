package com.portal.conductor;

import android.accessibilityservice.AccessibilityService;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
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

    // revision periodica (por si el movil no avisa de los cambios de pantalla)
    private boolean polling = false;
    private final Runnable pollRun = new Runnable() {
        @Override public void run() {
            if (!rentOn(ScreenReaderService.this)) { polling = false; return; }
            try {
                List<AccessibilityWindowInfo> ws = getWindows();
                boolean any = false;
                if (ws != null) for (AccessibilityWindowInfo w : ws) {
                    AccessibilityNodeInfo rt = w.getRoot();
                    if (rt == null) continue;
                    CharSequence pk = rt.getPackageName();
                    if (pk != null && DRIVER.matcher(pk).find() && !pk.toString().equals(getPackageName())) { any = true; break; }
                }
                if (any) {
                    getSharedPreferences("portal", Context.MODE_PRIVATE).edit().putLong("rent_seenTs", System.currentTimeMillis()).apply();
                    scheduleEval();
                }
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
        return p;
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
            boolean diag = sp.getInt("rent_diag", 0) == 1;
            OfferAnalyzer.Result found = null, unreadable = null;
            for (int i = 0; i < wins.length(); i++) {
                JSONObject w = wins.getJSONObject(i);
                String pkg = w.optString("pkg");
                if (!DRIVER.matcher(pkg).find()) continue;
                JSONArray ta = w.getJSONArray("texts");
                List<String> nodes = new ArrayList<String>();
                StringBuilder sb = new StringBuilder();
                for (int j = 0; j < ta.length(); j++) { String s = ta.getString(j); nodes.add(s); if (sb.length() < 3500) sb.append(s).append(" | "); }
                OfferAnalyzer.Result r = OfferAnalyzer.analyze(nodes, rentParams());
                String all = sb.toString();
                if (all.contains("\u20AC") || all.toLowerCase().contains("km")) {
                    sp.edit().putLong("rent_evalTs", System.currentTimeMillis()).putString("rent_why", r.offer
                        ? ("Oferta reconocida: " + r.verdict + " | precio " + r.price + " | viaje " + r.tripKm + " km/" + r.tripMin + " min | recogida " + r.pickupKm + " km/" + r.pickupMin + " min" + (r.orderAssumed ? " (orden estimado)" : ""))
                        : ("Texto con importes o km, pero NO reconocido como oferta: " + r.why)).apply();
                }
                if (r.offer || r.acceptSeen || (all.contains("\u20AC") && all.toLowerCase().contains("km"))) {
                    String info = r.offer ? ("veredicto=" + r.verdict + " precio=" + r.price + " viajeKm=" + r.tripKm + " viajeMin=" + r.tripMin + " recogidaKm=" + r.pickupKm + " recogidaMin=" + r.pickupMin + (r.orderAssumed ? " (orden asumido)" : "")) : "no reconocida como oferta";
                    sp.edit().putString("rent_lastText", pkg + "\n" + all).putString("rent_lastInfo", info).apply();
                }
                if (r.offer) { found = r; break; }
                else if (r.acceptSeen && unreadable == null) { r.unreadable = true; r.verdict = "DATA"; r.reason = "No pude leer los datos de esta oferta."; unreadable = r; }
            }
            if (found == null && unreadable != null) found = unreadable;
            long now = System.currentTimeMillis();
            if (found != null) {
                lastOfferSeen = now;
                showAlert(found);
                rh.removeCallbacks(hideRun);
                rh.postDelayed(hideRun, 25000);
            } else if (alertShown && now - lastOfferSeen > 1800) {
                hideAlert();
            }
        } catch (Exception e) { }
    }

    private void buildAlert() {
        final float d = getResources().getDisplayMetrics().density;
        alertView = new LinearLayout(this);
        alertView.setOrientation(LinearLayout.VERTICAL);
        alertView.setGravity(Gravity.CENTER_HORIZONTAL);
        alertView.setPadding((int) (16 * d), (int) (10 * d), (int) (16 * d), (int) (12 * d));
        aChip = new TextView(this);
        aChip.setTextColor(Color.WHITE);
        aChip.setTextSize(20);
        aChip.setGravity(Gravity.CENTER);
        aChip.setTypeface(Typeface.DEFAULT_BOLD);
        aChip.setPadding((int) (16 * d), (int) (4 * d), (int) (16 * d), (int) (4 * d));
        aMain = new TextView(this);
        aMain.setTextColor(Color.WHITE);
        aMain.setTextSize(22);
        aMain.setGravity(Gravity.CENTER);
        aMain.setTypeface(Typeface.DEFAULT_BOLD);
        aMain.setPadding(0, (int) (8 * d), 0, 0);
        aDetail = new TextView(this);
        aDetail.setTextColor(Color.parseColor("#DCEBFF"));
        aDetail.setTextSize(14);
        aDetail.setGravity(Gravity.CENTER);
        aDetail.setPadding(0, (int) (4 * d), 0, 0);
        alertView.addView(aChip);
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
        try {
            if (alertView == null) buildAlert();
            final float d = getResources().getDisplayMetrics().density;
            boolean ok = "OK".equals(r.verdict), no = "NO".equals(r.verdict);
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
            aChip.setText(ok ? "\u2713  ACEPTAR" : (no ? "\u2715  RECHAZAR" : "\u26A0  DATOS INSUFICIENTES"));
            if (r.unreadable) aMain.setText("No pude leer la oferta");
            else if (r.perHour > 0) aMain.setText(f(r.perHour, 1) + " \u20AC/h   |   " + f(r.perKm, 2) + " \u20AC/km");
            else if (r.price > 0) aMain.setText("Precio " + f(r.price, 2) + " \u20AC");
            else aMain.setText("Sin precio en la oferta");
            StringBuilder dt = new StringBuilder();
            if (r.pickupKm > 0 || r.pickupMin > 0) {
                dt.append("Recogida: ");
                if (r.pickupMin > 0) dt.append((int) r.pickupMin).append(" min");
                if (r.pickupKm > 0) dt.append(r.pickupMin > 0 ? " (" : "").append(f(r.pickupKm, 1)).append(" km").append(r.pickupMin > 0 ? ")" : "");
                dt.append("\n");
            }
            if (r.perHour <= 0 && r.tripKm > 0) {
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
        try { if (alertShown && alertView != null) wm.removeView(alertView); } catch (Exception e) { }
        alertShown = false;
    }

    public void demoAlert(String verdict) {
        OfferAnalyzer.Result r = new OfferAnalyzer.Result();
        r.offer = true; r.verdict = verdict; r.price = 15.2;
        if ("OK".equals(verdict)) { r.perHour = 31.4; r.perKm = 1.62; r.pickupKm = 1.2; r.pickupMin = 4; r.reason = "Cumple tus objetivos."; }
        else if ("NO".equals(verdict)) { r.perHour = 9.8; r.perKm = 0.78; r.pickupKm = 6.1; r.pickupMin = 11; r.reason = "\u20AC/h por debajo de 15,00 \u00B7 \u20AC/km por debajo de 1,00"; }
        else { r.reason = "No se pudo leer el tiempo del viaje."; }
        showAlert(r);
        rh.removeCallbacks(hideRun);
        rh.postDelayed(hideRun, 6000);
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
