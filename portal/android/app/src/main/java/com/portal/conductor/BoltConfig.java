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

    private static boolean sameCard(OfferAnalyzer.Card a, double base, double km, double min, double minFare) {
        return Math.abs(a.base - base) < 1e-9 && Math.abs(a.perKm - km) < 1e-9 && Math.abs(a.perMin - min) < 1e-9 && Math.abs(a.minFare - minFare) < 1e-9;
    }

    /** Nombre de zona: sin caracteres de control, recortado y de hasta 40 caracteres. */
    private static String areaName(Object o) {
        if (!(o instanceof String)) return "";
        String s = ((String) o).replaceAll("[\\u0000-\\u001F\\u007F]", " ").trim();
        return s.length() > 40 ? s.substring(0, 40).trim() : s;
    }

    private static int kindOf(Object o, int def) {
        if ("h".equals(o)) return OfferAnalyzer.Z_HIGH;
        if ("m".equals(o)) return OfferAnalyzer.Z_MID;
        if ("l".equals(o)) return OfferAnalyzer.Z_LOW;
        return def;
    }

    private static String kindKey(int k) { return k == OfferAnalyzer.Z_HIGH ? "h" : (k == OfferAnalyzer.Z_LOW ? "l" : "m"); }

    private static int kindWord(Object o, int def) {
        if ("high".equals(o)) return OfferAnalyzer.Z_HIGH;
        if ("mid".equals(o)) return OfferAnalyzer.Z_MID;
        if ("low".equals(o)) return OfferAnalyzer.Z_LOW;
        return def;
    }

    private static String kindWordKey(int k) { return k == OfferAnalyzer.Z_HIGH ? "high" : (k == OfferAnalyzer.Z_LOW ? "low" : "mid"); }

    /** Zonas dibujadas: poligonos [latitud, longitud] con su tipo (k: h alta, m media, l baja; las de la v3.15g no traen tipo y eran zonas buenas = altas). */
    private static OfferAnalyzer.Zone zone(Object o, OfferAnalyzer.Zone def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Zone z = def.copy();
        if (m == null) return z;
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
                if (pts.size() >= 3) l.add(new OfferAnalyzer.Area(areaName(am.get("n")), kindOf(am.get("k"), OfferAnalyzer.Z_HIGH), pts));
            }
            z.good = l;
        }
        return z;
    }

    private static final int MAX_ZONES = 40, MAX_PTS = 200, MAX_SLOTS = 30;

    /** Franjas de hora punta: [{on, d (dias, bit 0 = lunes), a (desde, minutos del dia), b (hasta)}]. Lo no valido se descarta; las de la v3.15g (con from/to) no valen y se sustituyen por las de fabrica. */
    private static List<OfferAnalyzer.Slot> slots(Object o, List<OfferAnalyzer.Slot> def) {
        if (!(o instanceof List)) return def;
        List<OfferAnalyzer.Slot> l = new ArrayList<OfferAnalyzer.Slot>();
        for (Object x : (List<?>) o) {
            Map<String, Object> sm = map(x);
            if (sm == null) continue;
            if (sm.containsKey("from") || sm.containsKey("to")) return def;       // formato de la v3.15g: se vuelve a las franjas de fabrica
            if (l.size() >= MAX_SLOTS) continue;
            double d = dbl(sm.get("d"), -1, 1, 127), a = dbl(sm.get("a"), -1, 0, 1439), b = dbl(sm.get("b"), -1, 1, 1440);
            if (d < 0 || a < 0 || b < 0 || d != Math.floor(d) || a != Math.floor(a) || b != Math.floor(b) || a == b) continue;
            OfferAnalyzer.Slot s = new OfferAnalyzer.Slot((int) d, (int) a, (int) b);
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
            c.peakApplies = bool(m.get("peakApplies"), c.peakApplies);
            c.round5 = bool(m.get("round5"), c.round5);
            c.fine = dbl(m.get("fine"), c.fine, -50, 100);
            Object zf = m.get("zoneForce");
            if (zf instanceof String && ("auto".equals(zf) || "low".equals(zf) || "mid".equals(zf) || "high".equals(zf))) c.zoneForce = (String) zf;
            c.zoneDef = kindWord(m.get("zoneDef"), c.zoneDef);
            Map<String, Object> sh = map(m.get("short"));
            if (sh != null) {
                double sk = dbl(sh.get("km"), c.shortKm, 0, 50), sf = dbl(sh.get("from"), c.shortFrom, 1, 10);
                double lo = dbl(sh.get("lo"), c.bumpLo, 0, 20), hi = dbl(sh.get("hi"), c.bumpHi, 0, 20);
                c.shortKm = sk; c.shortFrom = sf;
                if (lo <= hi) { c.bumpLo = lo; c.bumpHi = hi; }
            }
            c.airOn = bool(m.get("airOn"), c.airOn);
            c.airFee = dbl(m.get("airFee"), c.airFee, 0, 50);
            c.airFlatKm = dbl(m.get("airFlatKm"), c.airFlatKm, 0, 100);
            c.holidaysWe = bool(m.get("holidaysWe"), c.holidaysWe);
            c.slots = slots(m.get("slots"), c.slots);
            c.slotsH = slots(m.get("slotsH"), c.slotsH);
            Map<String, Object> cm = map(m.get("cards"));
            if (cm != null) {
                c.lowV = card(cm.get("lv"), c.lowV); c.lowP = card(cm.get("lp"), c.lowP);
                c.midV = card(cm.get("mv"), c.midV); c.midP = card(cm.get("mp"), c.midP);
                c.highV = card(cm.get("hv"), c.highV); c.highP = card(cm.get("hp"), c.highP);
                c.airV = card(cm.get("av"), c.airV); c.airP = card(cm.get("ap"), c.airP);
                // v3.15g: tarjetas normal / aeropuerto x entre semana / fin de semana. Solo se aprovecha lo que el conductor habia cambiado de fabrica.
                if (cm.get("nwd") != null) { OfferAnalyzer.Card x = card(cm.get("nwd"), c.midV); if (!sameCard(x, 2.10, 0.77, 0.15, 6.75)) c.midV = x; }
                if (cm.get("nwe") != null) { OfferAnalyzer.Card x = card(cm.get("nwe"), c.midP); if (!sameCard(x, 2.10, 0.77, 0.15, 6.75)) c.midP = x; }
                if (cm.get("awd") != null) { OfferAnalyzer.Card x = card(cm.get("awd"), c.airV); if (!sameCard(x, 2.89, 0.82, 0.15, 13.5)) c.airV = x; }
                if (cm.get("awe") != null) { OfferAnalyzer.Card x = card(cm.get("awe"), c.airP); if (!sameCard(x, 2.89, 0.82, 0.15, 13.5)) c.airP = x; }
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
        StringBuilder b = new StringBuilder("{\"zones\":[");
        boolean first = true;
        if (z.good != null) for (OfferAnalyzer.Area a : z.good) {
            if (a == null || a.pts == null || a.pts.size() < 3) continue;
            if (!first) b.append(',');
            b.append("{\"n\":").append(q(a.name == null ? "" : a.name)).append(",\"k\":\"").append(kindKey(a.kind)).append("\",\"pts\":[");
            for (int i = 0; i < a.pts.size(); i++) {
                if (i > 0) b.append(',');
                b.append('[').append(n(a.pts.get(i)[0])).append(',').append(n(a.pts.get(i)[1])).append(']');
            }
            b.append("]}");
            first = false;
        }
        return b.append("]}").toString();
    }

    private static void slotsJson(StringBuilder b, List<OfferAnalyzer.Slot> l) {
        b.append('[');
        boolean first = true;
        if (l != null) for (OfferAnalyzer.Slot s : l) {
            if (s == null) continue;
            if (!first) b.append(',');
            b.append("{\"on\":").append(s.on).append(",\"d\":").append(s.days).append(",\"a\":").append(s.a).append(",\"b\":").append(s.b).append('}');
            first = false;
        }
        b.append(']');
    }

    public static String toJson(OfferAnalyzer.BoltCfg c) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"on\":").append(c.on).append(",\"mode\":\"").append(c.mode).append("\",\"comm\":").append(n(c.comm));
        b.append(",\"peakApplies\":").append(c.peakApplies).append(",\"round5\":").append(c.round5).append(",\"fine\":").append(n(c.fine));
        b.append(",\"zoneForce\":\"").append(c.zoneForce).append("\",\"zoneDef\":\"").append(kindWordKey(c.zoneDef)).append('"');
        b.append(",\"short\":{\"km\":").append(n(c.shortKm)).append(",\"from\":").append(n(c.shortFrom)).append(",\"lo\":").append(n(c.bumpLo)).append(",\"hi\":").append(n(c.bumpHi)).append('}');
        b.append(",\"airOn\":").append(c.airOn).append(",\"airFee\":").append(n(c.airFee)).append(",\"airFlatKm\":").append(n(c.airFlatKm));
        b.append(",\"holidaysWe\":").append(c.holidaysWe).append(",\"holidays\":[");
        boolean first = true;
        if (c.holidays != null) for (String h : c.holidays) {
            if (h == null || !h.matches("\\d{4}-\\d{2}-\\d{2}|\\d{2}-\\d{2}")) continue;
            if (!first) b.append(',');
            b.append('"').append(h).append('"');
            first = false;
        }
        b.append("],\"slots\":");
        slotsJson(b, c.slots);
        b.append(",\"slotsH\":");
        slotsJson(b, c.slotsH);
        b.append(",\"cards\":{\"lv\":").append(cardJson(c.lowV)).append(",\"lp\":").append(cardJson(c.lowP))
         .append(",\"mv\":").append(cardJson(c.midV)).append(",\"mp\":").append(cardJson(c.midP))
         .append(",\"hv\":").append(cardJson(c.highV)).append(",\"hp\":").append(cardJson(c.highP))
         .append(",\"av\":").append(cardJson(c.airV)).append(",\"ap\":").append(cardJson(c.airP))
         .append("},\"zone\":").append(zoneJson(c.zone)).append('}');
        return b.toString();
    }

    /** Configuracion inicial (la unica fuente de verdad de los valores por defecto; la pantalla de ajustes la pide aqui). */
    public static String defaultsJson() { return toJson(new OfferAnalyzer.BoltCfg()); }
}
