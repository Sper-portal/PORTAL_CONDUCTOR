package com.portal.conductor;

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
        r.put("windows", s.readWithCache(getContext().getPackageName(), r));
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

    @PluginMethod
    public void getRent(PluginCall call) {
        android.content.SharedPreferences sp = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE);
        JSObject r = new JSObject();
        r.put("on", sp.getInt("rent_on", 0) == 1);
        r.put("minHour", (double) sp.getFloat("rent_minHour", 15f));
        r.put("minKm", (double) sp.getFloat("rent_minKm", 1f));
        r.put("maxPickup", (double) sp.getFloat("rent_maxPickup", 5f));
        r.put("comm", (double) sp.getFloat("rent_comm", 0f));
        r.put("incl", sp.getInt("rent_incl", 1) == 1);
        r.put("diag", sp.getInt("rent_diag", 0) == 1);
        r.put("tolPct", (double) sp.getFloat("rent_tolPct", 15f));
        r.put("tolPickup", (double) sp.getFloat("rent_tolPickup", 1f));
        call.resolve(r);
    }

    @PluginMethod
    public void setRent(PluginCall call) {
        android.content.SharedPreferences.Editor e = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).edit();
        e.putInt("rent_on", Boolean.TRUE.equals(call.getBoolean("on", false)) ? 1 : 0);
        e.putFloat("rent_minHour", call.getDouble("minHour", 15.0).floatValue());
        e.putFloat("rent_minKm", call.getDouble("minKm", 1.0).floatValue());
        e.putFloat("rent_maxPickup", call.getDouble("maxPickup", 5.0).floatValue());
        e.putFloat("rent_comm", call.getDouble("comm", 0.0).floatValue());
        e.putInt("rent_incl", Boolean.TRUE.equals(call.getBoolean("incl", true)) ? 1 : 0);
        e.putInt("rent_diag", Boolean.TRUE.equals(call.getBoolean("diag", false)) ? 1 : 0);
        e.putFloat("rent_tolPct", call.getDouble("tolPct", 15.0).floatValue());
        e.putFloat("rent_tolPickup", call.getDouble("tolPickup", 1.0).floatValue());
        e.apply();
        if (ScreenReaderService.instance != null) ScreenReaderService.instance.applyRentConfig();
        call.resolve();
    }

    @PluginMethod
    public void getRentDiag(PluginCall call) {
        android.content.SharedPreferences sp = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE);
        JSObject r = new JSObject();
        r.put("text", sp.getString("rent_lastText", ""));
        r.put("info", sp.getString("rent_lastInfo", ""));
        r.put("evalAgeMs", System.currentTimeMillis() - sp.getLong("rent_evalTs", 0L));
        r.put("seenAgeMs", System.currentTimeMillis() - sp.getLong("rent_seenTs", 0L));
        r.put("why", sp.getString("rent_why", ""));
        r.put("ocr", sp.getString("ocr_state", "todavia no se ha intentado"));
        StringBuilder snaps = new StringBuilder();
        for (java.util.Map.Entry<String, ?> en : sp.getAll().entrySet()) {
            if (en.getKey().startsWith("snap_")) snaps.append(en.getKey().substring(5)).append(" -> ").append(String.valueOf(en.getValue())).append("\n");
        }
        r.put("snaps", snaps.toString());
        call.resolve(r);
    }

    @PluginMethod
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
        r.put("zoneLast", sp.getString("zone_last", ""));
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
        if (ScreenReaderService.instance == null) { call.reject("El lector de pantalla no est\u00e1 activado"); return; }
        ScreenReaderService.instance.demoBolt();
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
        ZoneLocator.resolve(c, f);
        JSObject r = new JSObject();
        r.put("zone", ZoneLocator.json(f, c, now));
        call.resolve(r);
    }

    @PluginMethod
    public void testRent(PluginCall call) {
        if (ScreenReaderService.instance == null) { call.reject("El lector de pantalla no est\u00E1 activado"); return; }
        ScreenReaderService.instance.demoAlert(call.getString("verdict", "OK"));
        call.resolve();
    }

    @PluginMethod
    public void bubbleDiag(PluginCall call) {
        JSObject r = new JSObject();
        r.put("serviceOn", ScreenReaderService.instance != null);
        r.put("bubbleOn", ScreenReaderService.bubbleOn(getContext()));
        r.put("brand", android.os.Build.MANUFACTURER);
        r.put("model", android.os.Build.MODEL);
        r.put("sdk", android.os.Build.VERSION.SDK_INT);
        if (ScreenReaderService.instance != null) {
            try {
                org.json.JSONObject o = ScreenReaderService.instance.bubbleDiag();
                r.put("fgPkg", o.optString("fgPkg"));
                r.put("matchesDriver", o.optBoolean("matchesDriver"));
                r.put("shown", o.optBoolean("shown"));
            } catch (Exception e) { }
        }
        call.resolve(r);
    }

    @PluginMethod
    public void getReadDiag(PluginCall call) {
        android.content.SharedPreferences sp = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE);
        JSObject r = new JSObject();
        r.put("text", sp.getString("read_lastText", ""));
        r.put("ageMs", System.currentTimeMillis() - sp.getLong("read_lastWhen", 0L));
        call.resolve(r);
    }

    @PluginMethod
    public void testBubble(PluginCall call) {
        if (ScreenReaderService.instance == null) { call.reject("El lector de pantalla no est\u00E1 activado"); return; }
        ScreenReaderService.instance.forceBubble();
        call.resolve();
    }
}
