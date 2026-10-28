package com.portal.conductor;

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
