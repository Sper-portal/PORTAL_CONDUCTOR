package com.portal.conductor;

import android.content.Context;
import android.content.SharedPreferences;
import android.location.Location;
import android.location.LocationManager;

/**
 * Detecta en que zona esta el movil (baja, media o alta; v3.15h) con la ULTIMA ubicacion conocida del sistema (no enciende el GPS ni gasta bateria).
 * Si no hay permiso, no hay ubicacion o es muy vieja, usa la zona por defecto y deja escrito el motivo en el ajuste "zone_last"
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

    /**
     * Decide la zona de la recogida (baja, media o alta) con la ubicacion f (puede ser null): primero la zona forzada en Ajustes, despues las zonas
     * dibujadas (si cae en varias manda la alta, luego la media y luego la baja) y, si no cae en ninguna o no hay ubicacion, la zona por defecto.
     * Deja el resultado en c.zoneKind / c.zoneName / c.zoneSrc ("forced" | "area" | "default"). Nunca falla.
     */
    public static void resolve(OfferAnalyzer.BoltCfg c, Fix f) {
        c.zoneKind = c.zoneDef; c.zoneName = ""; c.zoneSrc = "default";
        try {
            if ("low".equals(c.zoneForce)) { c.zoneKind = OfferAnalyzer.Z_LOW; c.zoneSrc = "forced"; return; }
            if ("mid".equals(c.zoneForce)) { c.zoneKind = OfferAnalyzer.Z_MID; c.zoneSrc = "forced"; return; }
            if ("high".equals(c.zoneForce)) { c.zoneKind = OfferAnalyzer.Z_HIGH; c.zoneSrc = "forced"; return; }
            if (f != null) {
                OfferAnalyzer.Area a = OfferAnalyzer.areaAt(c.zone, f.lat, f.lon);
                if (a != null) { c.zoneKind = a.kind; c.zoneName = a.name == null ? "" : a.name; c.zoneSrc = "area"; }
            }
        } catch (Exception e) { c.zoneKind = c.zoneDef; c.zoneName = ""; c.zoneSrc = "default"; }
    }

    /** Pone en la configuracion la zona de la recogida segun el movil (zoneKind / zoneName / zoneSrc). Nunca falla: ante cualquier problema, la zona por defecto. */
    public static int apply(Context ctx, OfferAnalyzer.BoltCfg c, long now) {
        try {
            Fix f = null;
            if (!"low".equals(c.zoneForce) && !"mid".equals(c.zoneForce) && !"high".equals(c.zoneForce)) f = lastFix(ctx, now);
            resolve(c, f);
            diag(ctx, f, c, now);
        } catch (Exception e) { c.zoneKind = c.zoneDef; c.zoneName = ""; c.zoneSrc = "default"; }
        return c.zoneKind;
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

    /** JSON con lo que se ve ahora mismo: {"t":ms,"ok":bool,"lat":..,"lon":..,"age":seg,"prov":"..","kind":"high|mid|low","src":"area|default|forced","name":"zona dibujada o vacio","why":"motivo"} */
    public static String json(Fix f, OfferAnalyzer.BoltCfg c, long now) {
        StringBuilder b = new StringBuilder("{\"t\":").append(now);
        if (f != null) {
            b.append(",\"ok\":true,\"lat\":").append(String.format(java.util.Locale.ROOT, "%.5f", f.lat)).append(",\"lon\":").append(String.format(java.util.Locale.ROOT, "%.5f", f.lon))
             .append(",\"age\":").append(f.ageMs / 1000).append(",\"prov\":").append(q(f.provider)).append(",\"why\":\"\"");
        } else b.append(",\"ok\":false,\"why\":").append(q(cacheWhy));
        String kind = c == null ? "mid" : (c.zoneKind == OfferAnalyzer.Z_HIGH ? "high" : (c.zoneKind == OfferAnalyzer.Z_LOW ? "low" : "mid"));
        b.append(",\"kind\":\"").append(kind).append("\",\"src\":").append(q(c == null ? "default" : c.zoneSrc)).append(",\"name\":").append(q(c == null ? "" : c.zoneName)).append('}');
        return b.toString();
    }

    /** Deja escrito el ultimo resultado para que Ajustes lo muestre (como mucho una vez cada 3 s). */
    private static void diag(Context ctx, Fix f, OfferAnalyzer.BoltCfg c, long now) {
        try {
            String key = (f != null) + "|" + c.zoneKind + "|" + c.zoneName + "|" + c.zoneSrc + "|" + cacheWhy;
            if (key.equals(lastDiag) && now - lastDiagAt < 60000L) return;
            if (!key.equals(lastDiag) && lastDiagAt > 0 && now - lastDiagAt < 3000L) return;
            SharedPreferences sp = ctx.getSharedPreferences("portal", Context.MODE_PRIVATE);
            sp.edit().putString("zone_last", json(f, c, now)).apply();
            lastDiag = key; lastDiagAt = now;
        } catch (Exception e) { }
    }
}
