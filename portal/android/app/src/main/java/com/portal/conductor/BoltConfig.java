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

    private static OfferAnalyzer.Tier tier(Object o, OfferAnalyzer.Tier def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Tier t = def.copy();
        if (m == null) return t;
        t.base = dbl(m.get("base"), def.base, 0, 100);
        t.perKm = dbl(m.get("km"), def.perKm, 0, 20);
        t.perMin = dbl(m.get("min"), def.perMin, 0, 10);
        t.mult = dbl(m.get("mult"), def.mult, 0.1, 10);
        Object md = m.get("mode");
        t.mode = md instanceof String && "B".equalsIgnoreCase(((String) md).trim()) ? "B" : "A";
        return t;
    }

    private static OfferAnalyzer.Air air(Object o, OfferAnalyzer.Air def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Air a = def.copy();
        if (m == null) return a;
        a.on = bool(m.get("on"), def.on);
        a.base = dbl(m.get("base"), def.base, 0, 200);
        a.ref = dbl(m.get("ref"), def.ref, 1, 200);
        a.min = bool(m.get("min"), def.min);
        a.fee = dbl(m.get("fee"), def.fee, 0, 50);
        a.mult = dbl(m.get("mult"), def.mult, 0.1, 10);
        return a;
    }

    /** Los limites validos: n-1 numeros positivos y estrictamente crecientes. Si no, null. */
    private static double[] limits(Object bp, int n) {
        if (!(bp instanceof List) || ((List<?>) bp).size() != n - 1) return null;
        List<?> l = (List<?>) bp;
        double[] r = new double[n - 1];
        double prev = 0;
        for (int i = 0; i < r.length; i++) {
            double v = dbl(l.get(i), -1, 0.01, 1000);
            if (!(v > prev)) return null;
            r[i] = v; prev = v;
        }
        return r;
    }

    private static OfferAnalyzer.Profile profile(Object o, OfferAnalyzer.Profile def) {
        Map<String, Object> m = map(o);
        OfferAnalyzer.Profile p = def.copy();
        if (m == null) return p;
        p.minFare = dbl(m.get("minFare"), def.minFare, 0, 200);
        p.offerMult = bool(m.get("offerMult"), def.offerMult);
        p.air = air(m.get("air"), def.air);
        // numero de tramos: 1..MAX_TIERS. Solo se acepta un numero distinto del inicial si la lista de tramos y la de limites
        // son coherentes (n tramos y n-1 limites); los ajustes antiguos traen siempre 4 tramos y 3 limites.
        Object ts = m.get("t");
        int n = def.t.length;
        if (ts instanceof List && m.get("bp") instanceof List) {
            int tn = ((List<?>) ts).size(), bn = ((List<?>) m.get("bp")).size();
            if (tn >= 1 && tn <= OfferAnalyzer.MAX_TIERS && bn == tn - 1) n = tn;
        }
        OfferAnalyzer.Tier[] t = new OfferAnalyzer.Tier[n];
        for (int i = 0; i < n; i++) {
            OfferAnalyzer.Tier d = i < def.t.length ? def.t[i] : (i > 0 ? t[i - 1] : def.t[def.t.length - 1]);
            t[i] = ts instanceof List && i < ((List<?>) ts).size() ? tier(((List<?>) ts).get(i), d) : d.copy();
        }
        p.t = t;
        double[] bp = limits(m.get("bp"), n);
        if (bp != null) p.bp = bp;                                   // si no son validos se conservan los de antes (o 5, 10, 15, 20...)
        else p.bp = n == def.t.length ? def.bp.clone() : OfferAnalyzer.defaultBp(n);
        return p;
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
            c.wd = profile(m.get("wd"), c.wd);
            c.we = profile(m.get("we"), c.we);
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
            return c;
        } catch (Exception e) {
            return new OfferAnalyzer.BoltCfg();
        }
    }

    // ------------------------------------------------------------------ escritura
    private static String n(double v) { return BigDecimal.valueOf(v).stripTrailingZeros().toPlainString(); }

    private static String prof(OfferAnalyzer.Profile p) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"minFare\":").append(n(p.minFare)).append(",\"offerMult\":").append(p.offerMult);
        b.append(",\"bp\":[");
        for (int i = 0; i < p.bp.length; i++) { if (i > 0) b.append(','); b.append(n(p.bp[i])); }
        b.append("],\"t\":[");
        for (int i = 0; i < p.t.length; i++) {
            OfferAnalyzer.Tier t = p.t[i];
            if (i > 0) b.append(',');
            b.append("{\"base\":").append(n(t.base)).append(",\"km\":").append(n(t.perKm)).append(",\"min\":").append(n(t.perMin))
             .append(",\"mult\":").append(n(t.mult)).append(",\"mode\":\"").append("B".equals(t.mode) ? "B" : "A").append("\"}");
        }
        OfferAnalyzer.Air a = p.air;
        b.append("],\"air\":{\"on\":").append(a.on).append(",\"base\":").append(n(a.base)).append(",\"ref\":").append(n(a.ref))
         .append(",\"min\":").append(a.min).append(",\"fee\":").append(n(a.fee)).append(",\"mult\":").append(n(a.mult)).append("}");
        return b.append('}').toString();
    }

    public static String toJson(OfferAnalyzer.BoltCfg c) {
        StringBuilder b = new StringBuilder("{");
        b.append("\"on\":").append(c.on).append(",\"mode\":\"").append(c.mode).append("\",\"comm\":").append(n(c.comm));
        b.append(",\"holidays\":[");
        boolean first = true;
        if (c.holidays != null) for (String h : c.holidays) {
            if (h == null || !h.matches("\\d{4}-\\d{2}-\\d{2}|\\d{2}-\\d{2}")) continue;
            if (!first) b.append(',');
            b.append('"').append(h).append('"');
            first = false;
        }
        b.append("],\"wd\":").append(prof(c.wd)).append(",\"we\":").append(prof(c.we)).append('}');
        return b.toString();
    }

    /** Configuracion inicial (la unica fuente de verdad de los valores por defecto; la pantalla de ajustes la pide aqui). */
    public static String defaultsJson() { return toJson(new OfferAnalyzer.BoltCfg()); }
}
