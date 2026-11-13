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
        Map<String, Object> pm = map(m.get("postal"));
        if (pm != null) {
            z.postH = postalList(pm.get("h"), z.postH);
            z.postM = postalList(pm.get("m"), z.postM);
            z.postL = postalList(pm.get("l"), z.postL);
        }
        return z;
    }

    /** Lista de codigos postales: solo de cinco cifras, sin repetir y hasta 400; si no es una lista se queda la que habia. */
    /** v3.37: codigos postales de Madrid que faltaban de fabrica (baja: 28011 28017 28024 28027 28051 28052 28053; media: 28040 28046 28048). Solo se anade el que no esta en NINGUNA lista. */
    static void addCpv337(OfferAnalyzer.Zone z) {
        String[] low = {"28011", "28017", "28024", "28027", "28051", "28052", "28053"};
        String[] mid = {"28040", "28046", "28048"};
        for (String c : low) if (!z.postH.contains(c) && !z.postM.contains(c) && !z.postL.contains(c) && z.postL.size() < 400) z.postL.add(c);
        for (String c : mid) if (!z.postH.contains(c) && !z.postM.contains(c) && !z.postL.contains(c) && z.postM.size() < 400) z.postM.add(c);
    }

    private static List<String> postalList(Object o, List<String> def) {
        if (!(o instanceof List)) return def;
        List<String> l = new ArrayList<String>();
        for (Object x : (List<?>) o) {
            if (!(x instanceof String)) continue;
            String s = ((String) x).trim();
            if (s.matches("\\d{5}") && !l.contains(s) && l.size() < 400) l.add(s);
        }
        return l;
    }

    private static final int MAX_ZONES = 40, MAX_PTS = 200, MAX_SLOTS = 30;

    /** v3.34: version de los ajustes (los guardados con una menor se migran a las reglas nuevas). */
    static final int CFG_VER = 334;

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

    /** v3.49: zonas de fabrica (las que midio Juan). Se ponen una sola vez a quien no tiene ninguna zona dibujada (marca cpv menor de 349). */
    static List<OfferAnalyzer.Area> defaultAreas() {
        final String[] src = {
            "Zona 1|h|40.417079,-3.722302;40.416161,-3.742153;40.409065,-3.754317;40.401372,-3.769423;40.399601,-3.768703;40.393027,-3.775373;40.381073,-3.785182;40.369565,-3.80382;40.35641,-3.825008;40.347888,-3.85267;40.334131,-3.88661;40.30227,-3.902697;40.301821,-3.953901;40.342484,-4.007434;40.377337,-4.071219;40.421112,-4.085541;40.454314,-4.050202;40.486924,-4.057853;40.593822,-4.199302;40.700995,-4.113177;40.760907,-4.069036;40.839023,-3.779468;40.784084,-3.572886;40.706795,-3.516581;40.587118,-3.441638;40.50781,-3.496672;40.472449,-3.497849;40.470957,-3.53944;40.487969,-3.557881;40.540171,-3.554546;40.52869,-3.587113;40.505162,-3.59876;40.480619,-3.601702;40.478604,-3.581593;40.472038,-3.573942;40.46465,-3.574629;40.45129,-3.587087;40.451066,-3.601997;40.460322,-3.617397;40.469277,-3.626912;40.469212,-3.642606;40.47257,-3.649374;40.471078,-3.656977;40.471431,-3.658372;40.471694,-3.667288;40.478912,-3.666748;40.484826,-3.663511;40.484306,-3.676144;40.48384,-3.682409;40.48281,-3.687113;40.485645,-3.693882;40.486913,-3.69707;40.489435,-3.697785;40.482665,-3.715141;40.476882,-3.732381;40.476957,-3.737666;40.476957,-3.739616;40.476929,-3.741026;40.477022,-3.74181;40.476882,-3.742779;40.476525,-3.743739;40.475381,-3.747573;40.474597,-3.750491;40.473767,-3.753483;40.47358,-3.753066;40.470017,-3.750271;40.467583,-3.749793;40.464318,-3.749063;40.462191,-3.746911;40.456938,-3.744422;40.45385,-3.743368;40.45246,-3.74262;40.450892,-3.742583;40.442242,-3.739346;40.4371,-3.738022;40.430773,-3.737396;40.42829,-3.735949;40.427385,-3.734564;40.423856,-3.730383;40.422036,-3.724473;40.421327,-3.722817;40.419926,-3.722229;40.419338,-3.72115",
            "Zona 2|m|40.472328,-3.667091;40.471563,-3.666895;40.465626,-3.667559;40.462383,-3.665947;40.459301,-3.663831;40.455703,-3.663347;40.449657,-3.661974;40.444597,-3.660079;40.442693,-3.659049;40.440345,-3.658639;40.43407,-3.659663;40.431391,-3.660349;40.429226,-3.660227;40.428031,-3.659785;40.426725,-3.659932;40.425823,-3.659914;40.422132,-3.658534;40.419873,-3.658436;40.416027,-3.658951;40.412903,-3.661484;40.404724,-3.66526;40.397889,-3.669527;40.394562,-3.672439;40.391016,-3.677571;40.387922,-3.680164;40.383719,-3.68166;40.381178,-3.686172;40.380967,-3.688042;40.381571,-3.690414;40.384516,-3.693584;40.39012,-3.699617;40.394565,-3.704031;40.396429,-3.710499;40.399309,-3.715312;40.399869,-3.720903;40.401266,-3.722417;40.403806,-3.722834;40.405748,-3.722981;40.409094,-3.722031;40.41303,-3.72406;40.41908,-3.721313;40.421417,-3.723159;40.422798,-3.726494;40.424139,-3.730387;40.428937,-3.736322;40.431998,-3.737768;40.436067,-3.737818;40.44195,-3.739246;40.448646,-3.741864;40.452923,-3.742876;40.462402,-3.746897;40.464264,-3.749049;40.469753,-3.750134;40.473798,-3.75312;40.476916,-3.742238;40.476805,-3.7326;40.481956,-3.717146;40.489525,-3.698121;40.487406,-3.69742;40.485951,-3.694796;40.484039,-3.689806;40.482864,-3.684533;40.482986,-3.683319;40.483759,-3.682175;40.484427,-3.671864;40.48464,-3.664002;40.479193,-3.666209;40.475388,-3.66768"
        };
        List<OfferAnalyzer.Area> l = new ArrayList<OfferAnalyzer.Area>();
        for (String s : src) {
            String[] f = s.split("\\|");
            List<double[]> pts = new ArrayList<double[]>();
            for (String pr : f[2].split(";")) { String[] ll = pr.split(","); pts.add(new double[]{Double.parseDouble(ll[0]), Double.parseDouble(ll[1])}); }
            l.add(new OfferAnalyzer.Area(f[0], kindOf(f[1], OfferAnalyzer.Z_HIGH), pts));
        }
        return l;
    }

    private static OfferAnalyzer.BoltCfg withDefaultZones(OfferAnalyzer.BoltCfg c) { c.zone.good = defaultAreas(); c.zoneDef = OfferAnalyzer.Z_LOW; return c; }

    /** Lee la configuracion. Cualquier dato ausente o no valido vuelve a su valor inicial; un JSON roto devuelve todo por defecto. */
    public static OfferAnalyzer.BoltCfg parse(String json) {
        OfferAnalyzer.BoltCfg c = withDefaultZones(new OfferAnalyzer.BoltCfg());   // v3.49: la base son los valores de fabrica (zonas de fabrica y zona por defecto baja), igual que la pagina
        if (json == null || json.trim().length() == 0) return c;
        try {
            Map<String, Object> m = map(new P(json).val());
            if (m == null) return withDefaultZones(c);
            c.on = bool(m.get("on"), c.on);
            Object md = m.get("mode");
            if (md instanceof String && ("auto".equals(md) || "week".equals(md) || "weekend".equals(md))) c.mode = (String) md;
            c.comm = dbl(m.get("comm"), c.comm, 0, 90);
            c.peakApplies = bool(m.get("peakApplies"), c.peakApplies);
            c.round5 = bool(m.get("round5"), c.round5);
            c.fine = dbl(m.get("fine"), c.fine, -50, 100);
            c.peakKm = dbl(m.get("peakKm"), c.peakKm, 0, 50);
            c.longKm = dbl(m.get("longKm"), c.longKm, 0, 100);
            c.longDisc = dbl(m.get("longDisc"), c.longDisc, 0, 50);
            c.eventOn = bool(m.get("eventOn"), c.eventOn);
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
            c.slotsL = slots(m.get("slotsL"), OfferAnalyzer.copySlots(c.slots));   // v3.51: la baja tiene su lista; si no la habia, empieza como la que tenias para media y baja
            c.slotsH = slots(m.get("slotsH"), c.slotsH);
            if (dbl(m.get("cpv"), 0, 0, 100000) < 351 && OfferAnalyzer.sameSlots(c.slotsH, OfferAnalyzer.defaultSlotsHighOld())) c.slotsH = OfferAnalyzer.defaultSlotsHigh();   // v3.51: la alta de fabrica de antes pasa a la nueva; si la habias cambiado, se respeta
            Map<String, Object> cm = map(m.get("cards"));
            if (cm != null) {
                c.lowV = card(cm.get("lv"), c.lowV); c.lowP = card(cm.get("lp"), c.lowP);
                c.midV = card(cm.get("mv"), c.midV); c.midP = card(cm.get("mp"), c.midP);
                c.highV = card(cm.get("hv"), c.highV); c.highP = card(cm.get("hp"), c.highP);
                c.airV = card(cm.get("av"), c.airV); c.airP = card(cm.get("ap"), c.airP);
                // v3.47: la tarjeta del aeropuerto de fabrica de antes (2,89 / 0,82 / 0,15 / 13,50) pasa a la nueva (tarifa de pasajero de Bolt); si la habia cambiado, se respeta
                if (sameCard(c.airV, 2.89, 0.82, 0.15, 13.5)) c.airV = new OfferAnalyzer.Card(3.04, 0.86, 0.15, 13.70);
                if (sameCard(c.airP, 2.89, 0.82, 0.15, 13.5)) c.airP = new OfferAnalyzer.Card(3.04, 0.86, 0.15, 13.70);
                // v3.47: tarjetas del aeropuerto de las categorias (1 Comfort, 2 XL, 3 Premium): av1 ap1 av2 ap2 av3 ap3
                for (int ci = 0; ci < 4; ci++) {
                    c.airCatV[ci] = card(cm.get("av" + (ci + 1)), c.airCatV[ci]);
                    c.airCatP[ci] = card(cm.get("ap" + (ci + 1)), c.airCatP[ci]);
                }
                // v3.46: tarjetas de las categorias (1 Comfort, 2 XL, 3 Premium) por zona y valle / punta: lv1 lp1 mv1 mp1 hv1 hp1 ... hp3
                for (int ci = 0; ci < 4; ci++) for (int zi = 0; zi < 3; zi++) {   // v3.47: 4 categorias (la 4 = Child Seat / Booster Seat)
                    String zl = zi == 0 ? "l" : (zi == 1 ? "m" : "h");
                    c.catV[ci][zi] = card(cm.get(zl + "v" + (ci + 1)), c.catV[ci][zi]);
                    c.catP[ci][zi] = card(cm.get(zl + "p" + (ci + 1)), c.catP[ci][zi]);
                }
                // v3.47: hora punta de las categorias con los precios reales de Bolt: si tenias guardados los de fabrica de antes (aproximados) pasan a los nuevos; si los cambiaste, se respetan
                {
                    final double[][][] oldP = {
                        { {4.88, 0.93, 0.18, 9.90}, {2.93, 0.97, 0.23, 8.80}, {3.97, 1.05, 0.23, 9.50} },
                        { {2.91, 1.36, 0.25, 13.30}, {4.54, 1.39, 0.31, 12.45}, {5.26, 1.51, 0.32, 13.15} },
                        { {6.44, 1.16, 0.21, 11.65}, {3.95, 1.19, 0.27, 10.70}, {4.64, 1.29, 0.28, 11.40} }
                    };
                    OfferAnalyzer.Card[][] newP = OfferAnalyzer.defaultCat(true);
                    for (int ci = 0; ci < 3; ci++) for (int zi = 0; zi < 3; zi++)
                        if (sameCard(c.catP[ci][zi], oldP[ci][zi][0], oldP[ci][zi][1], oldP[ci][zi][2], oldP[ci][zi][3])) c.catP[ci][zi] = newP[ci][zi];
                }
                // v3.48: valle de Child Seat con los precios reales de Bolt (antes iba igual que la punta) y minuto de la zona media de valle de Comfort, XL y Premium (0,17 / 0,25 / 0,21):
                // si tenias guardados los de fabrica de antes pasan a los nuevos; si los cambiaste, se respetan
                {
                    final double[][] oldChildV = { {3.44, 0.93, 0.18, 10.25}, {3.50, 0.97, 0.23, 8.90}, {4.13, 1.06, 0.24, 9.70} };
                    final double[][] oldMidV = { {2.35, 0.90, 0.18, 7.90}, {3.96, 1.32, 0.26, 11.55}, {3.37, 1.12, 0.22, 9.80} };
                    OfferAnalyzer.Card[][] newV = OfferAnalyzer.defaultCat(false);
                    for (int zi = 0; zi < 3; zi++)
                        if (sameCard(c.catV[3][zi], oldChildV[zi][0], oldChildV[zi][1], oldChildV[zi][2], oldChildV[zi][3])) c.catV[3][zi] = newV[3][zi];
                    for (int ci = 0; ci < 3; ci++)
                        if (sameCard(c.catV[ci][1], oldMidV[ci][0], oldMidV[ci][1], oldMidV[ci][2], oldMidV[ci][3])) c.catV[ci][1] = newV[ci][1];
                }
                // v3.49: el Inicial de valle (baja y media) de Comfort, XL y Premium pasa a ser el literal de la pantalla de tarifas de Bolt:
                // si tenias guardados los de fabrica de antes pasan a los nuevos; si los cambiaste, se respetan
                {
                    final double[][][] oldIni = { { {3.87, 0.92, 0.15, 7.35}, {2.35, 0.90, 0.17, 7.90} }, { {1.90, 1.35, 0.22, 10.75}, {3.96, 1.32, 0.25, 11.55} }, { {5.43, 1.15, 0.18, 9.10}, {3.37, 1.12, 0.21, 9.80} } };
                    OfferAnalyzer.Card[][] newIni = OfferAnalyzer.defaultCat(false);
                    for (int ci = 0; ci < 3; ci++) for (int zi = 0; zi < 2; zi++)
                        if (sameCard(c.catV[ci][zi], oldIni[ci][zi][0], oldIni[ci][zi][1], oldIni[ci][zi][2], oldIni[ci][zi][3])) c.catV[ci][zi] = newIni[ci][zi];
                }
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
            if (dbl(m.get("cpv"), 0, 0, 100000) < 349 && c.zone.good.isEmpty()) { c.zone.good = defaultAreas(); if (c.zoneDef == OfferAnalyzer.Z_MID) c.zoneDef = OfferAnalyzer.Z_LOW; }   // v3.49: zonas de fabrica (y la zona por defecto de fabrica), una sola vez, a quien no tiene ninguna
            if (dbl(m.get("cpv"), 0, 0, 100000) < 337) addCpv337(c.zone);   // v3.37: los ajustes guardados antes de la v3.37 reciben los codigos que faltaban (la marca cpv la escribe Java al guardar los ajustes)
            // v3.34: los ajustes guardados con las reglas anteriores pasan a las nuevas (la punta sube el precio en viajes cortos; sin el extra de cortos de fabrica)
            if (dbl(m.get("v"), 0, 0, 100000) < CFG_VER) {
                c.peakApplies = true;
                if (c.shortKm == 6 && c.shortFrom == 1.2 && c.bumpLo == 0 && c.bumpHi == 2.5) c.bumpHi = 0;
            }
            return c;
        } catch (Exception e) {
            return withDefaultZones(new OfferAnalyzer.BoltCfg());
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
        b.append("],\"postal\":{\"h\":");
        postalJson(b, z.postH);
        b.append(",\"m\":");
        postalJson(b, z.postM);
        b.append(",\"l\":");
        postalJson(b, z.postL);
        return b.append("}}").toString();
    }

    private static void postalJson(StringBuilder b, List<String> l) {
        b.append('[');
        boolean first = true;
        if (l != null) for (String s : l) {
            if (s == null || !s.matches("\\d{5}")) continue;
            if (!first) b.append(',');
            b.append('"').append(s).append('"');
            first = false;
        }
        b.append(']');
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
        b.append(",\"peakKm\":").append(n(c.peakKm)).append(",\"longKm\":").append(n(c.longKm)).append(",\"longDisc\":").append(n(c.longDisc)).append(",\"eventOn\":").append(c.eventOn).append(",\"v\":").append(CFG_VER).append(",\"cpv\":351");
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
        b.append(",\"slotsL\":");
        slotsJson(b, c.slotsL);
        b.append(",\"slotsH\":");
        slotsJson(b, c.slotsH);
        b.append(",\"cards\":{\"lv\":").append(cardJson(c.lowV)).append(",\"lp\":").append(cardJson(c.lowP))
         .append(",\"mv\":").append(cardJson(c.midV)).append(",\"mp\":").append(cardJson(c.midP))
         .append(",\"hv\":").append(cardJson(c.highV)).append(",\"hp\":").append(cardJson(c.highP))
         .append(",\"av\":").append(cardJson(c.airV)).append(",\"ap\":").append(cardJson(c.airP));
        for (int ci = 0; ci < 4; ci++) for (int zi = 0; zi < 3; zi++) {   // v3.46: tarjetas de las categorias (v3.47: 4)
            String zl = zi == 0 ? "l" : (zi == 1 ? "m" : "h");
            b.append(",\"").append(zl).append("v").append(ci + 1).append("\":").append(cardJson(c.catV[ci][zi]));
            b.append(",\"").append(zl).append("p").append(ci + 1).append("\":").append(cardJson(c.catP[ci][zi]));
        }
        for (int ci = 0; ci < 4; ci++) {   // v3.47: tarjetas del aeropuerto de las categorias
            b.append(",\"av").append(ci + 1).append("\":").append(cardJson(c.airCatV[ci]));
            b.append(",\"ap").append(ci + 1).append("\":").append(cardJson(c.airCatP[ci]));
        }
        b.append("},\"zone\":").append(zoneJson(c.zone)).append('}');
        return b.toString();
    }

    /** Configuracion inicial (la unica fuente de verdad de los valores por defecto; la pantalla de ajustes la pide aqui). */
    public static String defaultsJson() { return toJson(withDefaultZones(new OfferAnalyzer.BoltCfg())); }
}
