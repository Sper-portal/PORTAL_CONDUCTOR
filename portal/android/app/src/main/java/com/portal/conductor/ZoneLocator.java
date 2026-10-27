package com.portal.conductor;

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
            if (!fine && !coarse) why = "sin permiso de ubicaci\u00f3n";
            else {
                Object o = ctx.getSystemService(Context.LOCATION_SERVICE);
                if (!(o instanceof LocationManager)) why = "el m\u00f3vil no da la ubicaci\u00f3n";
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
                    if (best == null) why = any ? "la \u00faltima ubicaci\u00f3n es muy vieja (m\u00e1s de " + (MAX_AGE_MS / 60000) + " min)" : "no hay ubicaci\u00f3n reciente";
                }
            }
        } catch (Exception e) { why = "error leyendo la ubicaci\u00f3n"; best = null; }
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
