package com.portal.conductor;

import java.math.BigDecimal;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Lee el texto de una oferta (Bolt/Uber/Cabify) y calcula si compensa. Sin dependencias de Android. */
public class OfferAnalyzer {

    public static class Params {
        public double minHour = 15, minKm = 1.0, maxPickup = 5.0, commission = 0, tolPct = 15, tolPickup = 1.0;
        public boolean includePickup = true;
        public BoltCfg bolt = new BoltCfg();     // estimacion de Bolt cuando la oferta no trae precio
        public boolean weekendNow = false;       // v3.15h: \u00abahora es hora punta\u00bb para la zona actual (lo decide quien llama con isWeekend)
    }

    public static class Result {
        public boolean offer;
        public String verdict = "DATA";           // OK, NO, DATA
        public double price = -1, tripKm = -1, tripMin = -1, pickupKm = -1, pickupMin = -1, perHour = -1, perKm = -1;
        public String reason = "";
        public boolean orderAssumed;
        public String why = "";
        public boolean acceptSeen, unreadable;
        public int stH = -1, stK = -1, stP = -1;   // 0 verde, 1 naranja, 2 rojo, -1 sin dato
        // ---- estimacion de Bolt (solo si la oferta no trae precio) ----
        public boolean isBolt, estimated, estWeekend, estMinApplied;   // estWeekend = franja de hora punta ahora
        public double estGross = -1, estComm = -1, estNet = -1, estMult = 1, estOfferMult = -1;
        public double estNetLo = -1, estNetHi = -1;                     // rango (viajes cortos con demanda); -1 si no hay rango
        public boolean estRange;
        public double estAlt = -1;                                      // neto si la hora punta contara (solo si hay franja punta y NO se aplica); -1 si no
        public boolean estPeakUsed;                                     // la tarjeta de punta se uso de verdad en el calculo
        public double estFine = 0;                                      // ajuste fino de demanda aplicado (%)
        public double estCommPct = -1;
        public String estAirport = "";              // "" | "pickup" (recogida en el aeropuerto) | "dest" (viaje hacia el aeropuerto)
        public double estFee = 0;                   // tasa del aeropuerto restada antes de la comision
        public int estZone = 1;                     // zona de la recogida: 0 baja, 1 media, 2 alta
        public String estArea = "";                 // nombre de la zona dibujada donde se detecto la ubicacion
        public String estZoneSrc = "";              // "area" (dibujada) | "default" (fuera de tus zonas) | "forced" (forzada en Ajustes)
    }

    // =====================================================================
    //  Estimacion del precio de Bolt cuando la oferta NO muestra el precio (v3.15h).
    //  Todos los valores son ESTIMACIONES editables por el conductor, NO son tarifas oficiales de Bolt.
    //  Ocho tarjetas: zona baja / media / alta (de la RECOGIDA, nunca del destino) x valle / punta, mas las dos del aeropuerto (recogidas).
    //  La demanda de la oferta multiplica todo. Las franjas de hora punta las define el conductor (una lista para media y baja, otra para alta).
    // =====================================================================

    /** Zonas: 0 baja, 1 media, 2 alta. */
    public static final int Z_LOW = 0, Z_MID = 1, Z_HIGH = 2;

    public static String zoneName(int k) { return k == Z_HIGH ? "alta" : (k == Z_LOW ? "baja" : "media"); }

    /** Una tarjeta de precios: inicial + km * precioKm + min * precioMin, nunca menos que la minima (0 = sin minima). */
    public static class Card {
        public double base, perKm, perMin, minFare;
        public Card() { }
        public Card(double base, double perKm, double perMin, double minFare) { this.base = base; this.perKm = perKm; this.perMin = perMin; this.minFare = minFare; }
        public Card copy() { return new Card(base, perKm, perMin, minFare); }
    }

    /** Minutos de una semana (de lunes 00:00 a domingo 24:00). */
    public static final int WEEK_MIN = 10080;

    /**
     * Franja de hora punta: unos dias de la semana (days: bit 0 = lunes ... bit 6 = domingo) desde la hora "a" hasta la hora "b" (minutos del dia, 0..1440).
     * Si "b" es menor o igual que "a", la franja acaba al dia siguiente (por ejemplo jueves 17:00 -> 02:00 del viernes). a = 0 y b = 1440 es el dia entero.
     */
    public static class Slot {
        public boolean on = true;
        public int days, a, b;
        public Slot() { }
        public Slot(int days, int a, int b) { this.days = days; this.a = a; this.b = b; }
        public Slot copy() { Slot s = new Slot(days, a, b); s.on = on; return s; }
        public int length() { return b > a ? b - a : b + 1440 - a; }
        /** true si el minuto de la semana w (0..10079) cae dentro: el principio cuenta, el final no. */
        public boolean contains(int w) {
            int len = length();
            for (int d = 0; d < 7; d++) {
                if ((days & (1 << d)) == 0) continue;
                int st = d * 1440 + a;
                int x = w - st;
                if (x < 0) x += WEEK_MIN;
                if (x >= 0 && x < len) return true;
            }
            return false;
        }
    }

    private static final int WEEKDAYS = 31, WEEKEND = 96;     // lunes a viernes / sabado y domingo

    /** Franjas de hora punta iniciales de zona media y baja: lunes a viernes 07:00-10:00 y 17:00-20:00, sabado y domingo todo el dia. */
    public static List<Slot> defaultSlots() {
        List<Slot> l = new ArrayList<Slot>();
        l.add(new Slot(WEEKDAYS, 7 * 60, 10 * 60));
        l.add(new Slot(WEEKDAYS, 17 * 60, 20 * 60));
        l.add(new Slot(WEEKEND, 0, 1440));
        return l;
    }

    /** Zona alta: igual, pero por la manana empieza a las 08:00 (visto el 29-10; sin confirmar). */
    public static List<Slot> defaultSlotsHigh() {
        List<Slot> l = new ArrayList<Slot>();
        l.add(new Slot(WEEKDAYS, 8 * 60, 10 * 60));
        l.add(new Slot(WEEKDAYS, 17 * 60, 20 * 60));
        l.add(new Slot(WEEKEND, 0, 1440));
        return l;
    }

    /** Una zona dibujada a mano: un poligono (puntos [latitud, longitud] en orden) de zona alta, media o baja. */
    public static class Area {
        public String name = "";
        public int kind = Z_HIGH;
        public List<double[]> pts = new ArrayList<double[]>();
        public Area() { }
        public Area(String name, List<double[]> pts) { this.name = name; this.pts = pts; }
        public Area(String name, int kind, List<double[]> pts) { this.name = name; this.kind = kind; this.pts = pts; }
        public Area copy() {
            List<double[]> p = new ArrayList<double[]>();
            for (double[] q : pts) p.add(new double[]{q[0], q[1]});
            return new Area(name, kind, p);
        }
        /** Punto dentro del poligono (regla par-impar; la orilla puede salir en cualquiera de los dos lados). */
        public boolean contains(double lat, double lon) {
            boolean in = false;
            for (int i = 0, j = pts.size() - 1; i < pts.size(); j = i++) {
                double yi = pts.get(i)[0], xi = pts.get(i)[1], yj = pts.get(j)[0], xj = pts.get(j)[1];
                if (((yi > lat) != (yj > lat)) && (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) in = !in;
            }
            return in;
        }
    }

    /** Las zonas dibujadas. Fuera de todas ellas vale la zona por defecto de Ajustes (media de fabrica). */
    public static class Zone {
        public List<Area> good = new ArrayList<Area>();   // sin zonas al principio
        public Zone copy() {
            Zone z = new Zone();
            z.good = new ArrayList<Area>();
            for (Area a : good) z.good.add(a.copy());
            return z;
        }
    }

    /** Distancia en km entre dos puntos (formula de haversine). */
    public static double distKm(double lat1, double lon1, double lat2, double lon2) {
        double rad = Math.PI / 180.0, dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return 6371.0 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    /** La zona dibujada que contiene el punto (si cae en varias, manda la alta, luego la media y luego la baja), o null. */
    public static Area areaAt(Zone z, double lat, double lon) {
        if (z == null || z.good == null) return null;
        Area best = null;
        for (Area a : z.good) {
            if (a == null || !a.contains(lat, lon)) continue;
            if (best == null || a.kind > best.kind) best = a;
        }
        return best;
    }

    /** Nombre de la zona dibujada que contiene el punto, o null si no esta en ninguna. */
    public static String goodAreaAt(Zone z, double lat, double lon) {
        Area a = areaAt(z, lat, lon);
        return a == null ? null : a.name;
    }

    public static class BoltCfg {
        public Zone zone = new Zone();
        // lo pone el servicio en cada lectura segun la ubicacion y la zona forzada (no se guarda)
        public int zoneKind = Z_MID;
        public String zoneName = "", zoneSrc = "default";
        public String zoneForce = "auto";    // auto (por tus zonas dibujadas) | low | mid | high
        public int zoneDef = Z_MID;          // zona de la recogida cuando no cae en ninguna zona dibujada
        public boolean on = true;
        public String mode = "auto";         // auto (por las franjas) | week (siempre valle) | weekend (siempre punta)
        public double comm = 25;             // comision de Bolt, %
        public boolean peakApplies = false;  // la tarjeta de punta SUBE el precio estimado (apagado: se calcula con la de valle y se avisa de lo que saldria)
        public boolean round5 = true;        // el bruto se redondea a 5 centimos (como hace Bolt); el neto nunca se redondea
        public double fine = 0;              // ajuste fino (%) que se suma al calculo cuando hay demanda
        public double shortKm = 6, shortFrom = 1.2, bumpLo = 0, bumpHi = 2.5;   // viajes cortos con demanda: rango (menos de shortKm km y demanda desde shortFrom; el inicial real sube entre bumpLo y bumpHi euros)
        // zona baja / media / alta x valle / punta
        public Card lowV = new Card(2.02, 0.79, 0.13, 6.30), lowP = new Card(3.03, 0.80, 0.16, 8.85);
        public Card midV = new Card(2.10, 0.77, 0.15, 6.75), midP = new Card(2.68, 0.84, 0.20, 7.65);
        public Card highV = new Card(2.39, 0.85, 0.16, 6.70), highP = new Card(3.56, 0.91, 0.21, 8.35);
        // aeropuerto (solo las RECOGIDAS en el aeropuerto): valle / punta
        public Card airV = new Card(2.89, 0.82, 0.15, 13.50), airP = new Card(2.89, 0.82, 0.15, 13.50);
        public boolean airOn = true;         // usar la tarjeta del aeropuerto en las recogidas
        public double airFee = 2.57;         // tasa del aeropuerto (recogidas y viajes hacia el aeropuerto): se resta del bruto ANTES de la comision
        public double airFlatKm = 11;        // recogida en el aeropuerto: hasta estos km solo vale la minima
        public List<Slot> slots = defaultSlots();         // hora punta de zona media y baja
        public List<Slot> slotsH = defaultSlotsHigh();    // hora punta de zona alta
        public boolean holidaysWe = true;    // los festivos cuentan como hora punta todo el dia
        public List<String> holidays = defaultHolidays();   // "yyyy-MM-dd" o "MM-dd"
    }

    /** La tarjeta de la zona dada, de punta o de valle. */
    public static Card zoneCard(BoltCfg c, int kind, boolean peak) {
        if (kind == Z_HIGH) return peak ? c.highP : c.highV;
        if (kind == Z_LOW) return peak ? c.lowP : c.lowV;
        return peak ? c.midP : c.midV;
    }

    /** Festivos nacionales fijos y el de la Comunidad de Madrid. Los que cambian cada ano (Semana Santa) se anaden a mano con aaaa-mm-dd. */
    public static List<String> defaultHolidays() {
        List<String> l = new ArrayList<String>();
        for (String s : new String[]{"01-01", "01-06", "05-01", "05-02", "08-15", "10-12", "11-01", "12-06", "12-08", "12-25"}) l.add(s);
        return l;
    }

    /** true si el dia del calendario es uno de los festivos de la lista. */
    public static boolean isHoliday(BoltCfg c, java.util.Calendar cal) {
        int mo = cal.get(java.util.Calendar.MONTH) + 1, dd = cal.get(java.util.Calendar.DAY_OF_MONTH), yy = cal.get(java.util.Calendar.YEAR);
        String full = String.format(Locale.ROOT, "%04d-%02d-%02d", yy, mo, dd), md = String.format(Locale.ROOT, "%02d-%02d", mo, dd);
        if (c.holidays != null) for (String h : c.holidays) if (full.equals(h) || md.equals(h)) return true;
        return false;
    }

    /** Minuto de la semana (0 = lunes 00:00 ... 10079 = domingo 23:59) de un instante. */
    public static int weekMinute(java.util.Calendar cal) {
        int dow = (cal.get(java.util.Calendar.DAY_OF_WEEK) + 5) % 7;       // lunes = 0 ... domingo = 6
        return dow * 1440 + cal.get(java.util.Calendar.HOUR_OF_DAY) * 60 + cal.get(java.util.Calendar.MINUTE);
    }

    /** true si ahora es hora punta en la zona actual (c.zoneKind): lo decide la franja en la que cae la hora (o un festivo), no el dia del calendario. */
    public static boolean isWeekend(BoltCfg c, java.util.Calendar cal) { return isPeak(c, c.zoneKind, cal); }

    /** true si en la zona dada es hora punta a ese instante. */
    public static boolean isPeak(BoltCfg c, int kind, java.util.Calendar cal) {
        if ("week".equals(c.mode)) return false;
        if ("weekend".equals(c.mode)) return true;
        if (c.holidaysWe && isHoliday(c, cal)) return true;
        int w = weekMinute(cal);
        List<Slot> l = kind == Z_HIGH ? c.slotsH : c.slots;
        if (l != null) for (Slot s : l) if (s != null && s.on && s.contains(w)) return true;
        return false;
    }

    public static class Est {
        public double gross, comm, net, mult, fee;
        public double grossLo, grossHi, netLo, netHi;   // rango (solo si range)
        public boolean range;
        public double alt = -1;                          // neto con la tarjeta de punta si hay franja punta y no se aplica
        public String airport = "";          // "" | "pickup" | "dest"
        public boolean minApplied, weekend, peakUsed;    // weekend = franja de hora punta ahora
        public int zone = Z_MID;
        public double fine = 0;
    }

    // ---- aeropuerto: se detecta por el texto de la oferta ----
    // recogida: "parking P1 de la T1", "parking express T2", "parking modulo D planta 4 de la T4"
    private static final Pattern AIR_PICK_HINT = Pattern.compile("\\b(t\\s?[1-4]|p\\s?1|express|modulo\\s?d|terminal|aeropuerto|barajas)\\b");
    // destino: "Terminal 1..4", "Aeropuerto ..." (el barrio de Barajas o la Avenida de la Hispanidad NO cuentan)
    private static final Pattern AIR_DEST = Pattern.compile("terminal\\s?[1-4]|aeropuerto");

    /** "pickup" si se recoge en el aeropuerto, "dest" si el viaje va al aeropuerto, "" si no tiene que ver con el aeropuerto. */
    public static String detectAirport(List<String> nodes) {
        boolean pick = false, dest = false;
        if (nodes == null) return "";
        for (String raw : nodes) {
            if (raw == null || raw.length() > 120) continue;          // los textos largos (avisos, condiciones) no son direcciones
            String n = norm(raw);
            if (n.contains("parking") && AIR_PICK_HINT.matcher(n).find()) pick = true;
            else if (AIR_DEST.matcher(n).find()) dest = true;
        }
        return pick ? "pickup" : (dest ? "dest" : "");
    }

    /** Redondeo del bruto a 5 centimos (medio hacia arriba), sin ruido de coma flotante. */
    static double r5(BoltCfg c, double x) {
        if (!c.round5) return x;
        double v = Math.round(x * 1e6) / 1e6;
        return Math.floor(v * 20 + 0.5 + 1e-7) / 20.0;
    }

    public static Est estimate(BoltCfg c, boolean peak, double km, double min, double offerMult) { return estimate(c, peak, km, min, offerMult, ""); }

    /**
     * Bruto = (inicial + km*precioKm + min*precioMin, nunca menos que la minima) de la tarjeta que toca, x la demanda de la oferta (x1 si no hay), redondeado a 5 centimos.
     *  - Tarjeta: la de la ZONA de la recogida (c.zoneKind) y de valle o punta; solo las recogidas en el aeropuerto usan la del aeropuerto.
     *  - Punta: la tarjeta de punta solo cuenta si peak (franja) y c.peakApplies; si no, se calcula con valle y se guarda en alt lo que saldria con punta.
     *  - Aeropuerto (recogida o viaje hacia alli): se resta la tasa del bruto y despues se calcula la comision. Recogida: hasta airFlatKm solo vale la minima.
     *  - Viajes cortos con demanda: rango entre inicial + bumpLo e inicial + bumpHi (el calculo usa el punto medio).
     */
    public static Est estimate(BoltCfg c, boolean peak, double km, double min, double offerMult, String airKind) {
        boolean air = c.airOn && ("pickup".equals(airKind) || "dest".equals(airKind));
        String ak = air ? airKind : "";
        boolean up = peak && c.peakApplies;
        Est e = calc(c, up, km, min, offerMult, ak);
        e.weekend = peak; e.peakUsed = up; e.zone = c.zoneKind;
        if (peak && !c.peakApplies) e.alt = calc(c, true, km, min, offerMult, ak).net;
        return e;
    }

    private static Est calc(BoltCfg c, boolean up, double km, double min, double offerMult, String ak) {
        boolean pickup = "pickup".equals(ak);
        boolean air = ak.length() > 0;
        Card card = pickup ? (up ? c.airP : c.airV) : zoneCard(c, c.zoneKind, up);
        double raw = card.base + km * card.perKm + min * card.perMin;
        boolean ma = false;
        if (pickup && c.airFlatKm > 0 && km <= c.airFlatKm && card.minFare > 0) { raw = card.minFare; ma = true; }
        else if (card.minFare > 0 && raw < card.minFare) { raw = card.minFare; ma = true; }
        double m = offerMult > 1.0 ? Math.min(10.0, offerMult) : 1.0;
        double fm = m > 1.0 + 1e-9 ? 1 + c.fine / 100.0 : 1.0;
        boolean range = !pickup && m > 1.0 + 1e-9 && m >= c.shortFrom - 1e-9 && km < c.shortKm && c.bumpHi > c.bumpLo;
        double mid = range ? raw + (c.bumpLo + c.bumpHi) / 2.0 : raw;
        double gross = r5(c, mid * m * fm);
        double pct = Math.max(0, Math.min(90, c.comm));
        double fee = air ? c.airFee : 0;
        Est e = new Est();
        e.gross = gross; e.fee = fee;
        double after = fee > 0 ? Math.max(0, gross - fee) : gross;
        e.comm = after * pct / 100.0; e.net = after - e.comm;
        e.mult = m; e.fine = m > 1.0 + 1e-9 ? c.fine : 0; e.airport = ak; e.minApplied = ma; e.range = range;
        e.grossLo = e.gross; e.grossHi = e.gross; e.netLo = e.net; e.netHi = e.net;
        if (range) {
            e.grossLo = r5(c, (raw + c.bumpLo) * m * fm);
            e.grossHi = r5(c, (raw + c.bumpHi) * m * fm);
            double aLo = fee > 0 ? Math.max(0, e.grossLo - fee) : e.grossLo, aHi = fee > 0 ? Math.max(0, e.grossHi - fee) : e.grossHi;
            e.netLo = aLo * (1 - pct / 100.0); e.netHi = aHi * (1 - pct / 100.0);
        }
        return e;
    }


    // multiplicador de demanda que a veces muestra la oferta: "x1.7", "x1,4", "1.5x"
    private static final Pattern DEM1 = Pattern.compile("(?<![A-Za-z0-9])[x\u00d7]\\s?(\\d{1,2}(?:[.,]\\d{1,2})?)(?![\\d%A-Za-z])", Pattern.CASE_INSENSITIVE);
    private static final Pattern DEM2 = Pattern.compile("(?<![\\d.,])(\\d{1,2}(?:[.,]\\d{1,2})?)\\s?[x\u00d7](?![A-Za-z0-9])", Pattern.CASE_INSENSITIVE);

    static double detectDemand(List<String> nodes) {
        for (String t : nodes) {
            String s = t.trim(), n = norm(s);
            boolean dem = n.contains("demanda") || n.contains("surge") || n.contains("multiplicador");
            if (!dem && s.length() > 14) continue;
            Matcher m = DEM1.matcher(s);
            if (!m.find()) { m = DEM2.matcher(s); if (!m.find()) continue; }
            double v = num(m.group(1));
            if (v >= 1.0 && v <= 6.0) return v;
        }
        return -1;
    }

    /** Importe con 2 decimales y coma, sin ruido de coma flotante. */
    public static String money(double v) {
        return java.math.BigDecimal.valueOf(Math.round(v * 1e6) / 1e6).setScale(2, java.math.RoundingMode.HALF_UP).toPlainString().replace('.', ',');
    }

    /** Numero para la voz: coma decimal, sin ceros sobrantes (8,3 / 8 / 1,45). */
    private static String spokenNum(double v, int dec) {
        return java.math.BigDecimal.valueOf(v).setScale(dec, java.math.RoundingMode.HALF_UP).stripTrailingZeros().toPlainString().replace('.', ',');
    }


    /** Frase para el aviso por voz (con los valores reales de la oferta). null si no hay nada que decir. */
    public static String voiceText(Result r) {
        if (r == null || !r.isBolt || !r.offer) return null;
        if (r.estimated) {
            long min = Math.round(r.tripMin);
            String km = spokenNum(r.tripKm, 1);
            StringBuilder b = new StringBuilder("Bolt. ");
            if ("pickup".equals(r.estAirport)) b.append("Recogida en el aeropuerto. ");
            else if ("dest".equals(r.estAirport)) b.append("Hacia el aeropuerto. ");
            b.append("Viaje de ").append(km).append("1".equals(km) ? " kil\u00F3metro y " : " kil\u00F3metros y ").append(min).append(min == 1 ? " minuto" : " minutos");
            if (r.estZone == Z_HIGH) b.append(", zona alta");
            else if (r.estZone == Z_LOW) b.append(", zona baja");
            if (r.estPeakUsed) b.append(", tarifa de hora punta");
            if (Math.abs(r.estMult - 1.0) > 1e-9) b.append(", demanda por ").append(spokenNum(r.estMult, 2));
            b.append(". Bruto estimado: ").append(money(r.estGross)).append(" euros. ");
            if (r.estFee > 0) b.append("Tasa del aeropuerto: ").append(money(r.estFee)).append(" euros. ");
            b.append("Comisi\u00F3n estimada: ").append(money(r.estComm)).append(" euros. Neto estimado: ").append(money(r.estNet)).append(" euros");
            if (r.estRange && r.estNetLo >= 0 && r.estNetHi > r.estNetLo + 1e-9) b.append(", entre ").append(money(r.estNetLo)).append(" y ").append(money(r.estNetHi));
            b.append(".");
            return b.toString();
        }
        if (r.price > 0) return "Bolt. Precio de la oferta: " + money(r.price) + " euros.";
        return null;
    }


    private static class Item { int node; char kind; double v; boolean used; }
    private static class Seg { double km = -1, min = -1; String ctx = ""; int first = 99; }

    private static final Pattern EUR1 = Pattern.compile("(\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}[.,]\\d{1,2})\\s*(?:\u20AC|eur\\b)", Pattern.CASE_INSENSITIVE);
    private static final Pattern EUR2 = Pattern.compile("\u20AC\\s*(\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}[.,]\\d{1,2})", Pattern.CASE_INSENSITIVE);
    private static final Pattern KM = Pattern.compile("(\\d+(?:[.,]\\d+)?)\\s*km\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern MET = Pattern.compile("(?<![\\d.,])(\\d{2,4})\\s*m(?![a-zA-Z])");
    private static final Pattern MIN = Pattern.compile("(?:(\\d+)\\s*h(?:ora)?s?\\s*)?(\\d+)\\s*min", Pattern.CASE_INSENSITIVE);
    private static final Pattern HOURS = Pattern.compile("(?<![\\d.,])(\\d+)\\s*h(?:ora)?s?\\b(?!\\s*\\d+\\s*min)", Pattern.CASE_INSENSITIVE);
    private static final String[] PICK = {"recog", "recoj", "pasajero", "away", "de distancia", "cliente", "pickup", "hasta el"};
    private static final String[] TRIP = {"viaje", "trayecto", "recorrido", "destino", "trip", "total", "duracion", "drop"};
    private static final String[] ACCEPT = {"aceptar", "accept", "seleccionar", "rechazar", "reject", "declinar", "decline", "emparejar", "match"};

    public static String norm(String s) {
        String n = Normalizer.normalize(s == null ? "" : s, Normalizer.Form.NFD).replaceAll("\\p{M}", "");
        return n.toLowerCase(Locale.ROOT);
    }

    private static double num(String s) {
        String t = s.trim();
        if (t.contains(",") && t.contains(".")) t = t.replace(".", "").replace(",", ".");
        else t = t.replace(",", ".");
        try { return Double.parseDouble(t); } catch (Exception e) { return -1; }
    }

    private static boolean has(String s, String[] kws) { for (String k : kws) if (s.contains(k)) return true; return false; }

    private static String clean(String t) {
        String x = t == null ? "" : t.replace('\u00A0', ' ').replace('\u202F', ' ').replace('\u2009', ' ').replace('\u200A', ' ').replace('\u2007', ' ');
        x = x.replaceAll("(?i)\\bkil[o\u00F3]metros?\\b", "km").replaceAll("(?i)\\bminutos?\\b", "min").replaceAll("(?i)\\bmins\\b", "min");
        x = x.replaceAll("(?i)\\beuros?\\b", "\u20AC").replaceAll("(?i)(\\d)\\s*metros?\\b", "$1 m");
        return x;
    }

    /** el boton de aceptar de la oferta (no vale cualquier texto que contenga la palabra) */
    private static boolean isAcceptNode(String raw) {
        String n = norm(raw).replaceAll("[^a-z ]", " ").replaceAll("\\s+", " ").trim();
        if (n.length() == 0 || n.length() > 28) return false;
        return n.startsWith("aceptar") || n.startsWith("emparejar") || n.equals("accept") || n.equals("match");
    }

    // ---- peajes: un importe junto a la palabra \u00abpeaje\u00bb NO es el precio del viaje (se ignora al buscar el precio) ----
    private static final String AMT_RE = "(?:\\d{1,3}(?:\\.\\d{3})+,\\d{2}|\\d{1,4}(?:[.,]\\d{1,2})?)";
    private static final String TOLL_W = "(?<![\\p{L}])(?:peajes?|tolls?)(?![\\p{L}])";
    /** \u00abPeaje incluido 2,50 \u20ac\u00bb, \u00abPeajes: \u20ac2,50\u00bb, \u00abToll 2.50 EUR\u00bb (la palabra primero y el importe detras, con la moneda a un lado) */
    private static final Pattern TOLL_AFTER = Pattern.compile("(?i)" + TOLL_W + "[^\\d\u20AC]{0,25}?(?:\u20AC\\s*" + AMT_RE + "|" + AMT_RE + "\\s*(?:\u20AC|eur\\b))");
    /** \u00abIncluye 2,50 \u20ac de peajes\u00bb, \u00ab+2,50 \u20ac peaje\u00bb, \u00ab2,50 \u20ac de peaje\u00bb (importe con un nexo claro de peaje; \u00ab12,50 \u20ac Peaje incluido\u00bb NO se toca: ahi el importe es el precio) */
    private static final Pattern TOLL_BEFORE = Pattern.compile("(?i)(?:(?:incluy\\w*|incluid\\w*|incl\\.?|con|m[a\u00E1]s|\\+)\\s*" + AMT_RE + "\\s*(?:\u20AC|eur\\b)\\s*(?:(?:de|en|por)\\s+)?"
            + "|" + AMT_RE + "\\s*(?:\u20AC|eur\\b)\\s*(?:de|en|por)\\s+)" + TOLL_W);
    private static final Pattern TOLL_WORD = Pattern.compile("(?i)" + TOLL_W);
    private static final Pattern TOLL_LONE = Pattern.compile("^[+\\-]?\\s*(?:\u20AC\\s*)?" + AMT_RE + "\\s*(?:\u20AC|eur)?$", Pattern.CASE_INSENSITIVE);

    /**
     * Copia de los nodos SIN los importes de peaje, solo para buscar el precio. Los km, los minutos, el aviso del aeropuerto y todo lo demas
     * siguen leyendo los nodos originales. Si ninguno nombra el peaje, devuelve la misma lista (Uber y Cabify no cambian).
     */
    static List<String> withoutTolls(List<String> nodes) {
        boolean any = false;
        for (String s : nodes) if (TOLL_WORD.matcher(s).find()) { any = true; break; }
        if (!any) return nodes;
        List<String> out = new ArrayList<String>();
        boolean priceBefore = false;               // ya se vio un importe en euros antes (el precio suele ir arriba)
        for (int i = 0; i < nodes.size(); i++) {
            String s = nodes.get(i);
            if (TOLL_WORD.matcher(s).find()) {
                String c = TOLL_AFTER.matcher(s).replaceAll(" ");
                c = TOLL_BEFORE.matcher(c).replaceAll(" ");
                boolean hadAmount = !c.equals(s);
                boolean stillEur = EUR1.matcher(c).find() || EUR2.matcher(c).find();
                out.add(c.trim());
                // \u00abPeajes:\u00bb / \u00abPeaje incluido\u00bb en un nodo y el importe en el siguiente
                if (!hadAmount && !stillEur && i + 1 < nodes.size() && TOLL_LONE.matcher(nodes.get(i + 1).trim()).find()
                        && (s.trim().endsWith(":") || priceBefore)) { out.add(""); i++; }
                if (stillEur) priceBefore = true;
            } else {
                out.add(s);
                if (EUR1.matcher(s).find() || EUR2.matcher(s).find()) priceBefore = true;
            }
        }
        return out;
    }

    private static final Pattern LONEPRICE = Pattern.compile("^\\D{0,3}(\\d{1,3}[.,]\\d{2})\\s*\\S{0,2}$");

    private static int stMin(double v, double min, double tolPct) {
        if (v >= min) return 0;
        return v >= min * (1 - tolPct / 100.0) ? 1 : 2;
    }

    public static Result analyze(List<String> rawNodes, Params p) { return analyze(rawNodes, p, false); }

    public static Result analyze(List<String> rawNodes, Params p, boolean lenient) { return analyze(rawNodes, p, lenient, false); }

    /** isBolt: la oferta viene de Bolt (paquete bolt/mtakso). Solo en ese caso, y sin precio visible, se estima el precio. */
    public static Result analyze(List<String> rawNodes, Params p, boolean lenient, boolean isBolt) {
        List<String> nodes = new ArrayList<String>();
        for (String x : rawNodes) for (String line : clean(x).split("\\n")) if (line.trim().length() > 0) nodes.add(line.trim());
        Result r = new Result();
        // ---- precio: primer importe en euros razonable (sin contar los importes de peaje)
        List<String> priceNodes = withoutTolls(nodes);
        for (String t : priceNodes) {
            Matcher m = EUR1.matcher(t); double v = -1;
            if (m.find()) v = num(m.group(1)); else { Matcher m2 = EUR2.matcher(t); if (m2.find()) v = num(m2.group(1)); }
            if (v >= 1.0 && v < 1000) { r.price = v; break; }
        }
        if (r.price <= 0 && lenient) {
            for (String t : priceNodes) { Matcher m = LONEPRICE.matcher(t.trim()); if (m.find()) { double v = num(m.group(1)); if (v >= 1.0 && v < 1000) { r.price = v; break; } } }
        }
        // ---- elementos km / min por nodo
        List<Item> items = new ArrayList<Item>();
        StringBuilder all = new StringBuilder();
        for (int i = 0; i < nodes.size(); i++) {
            String t = nodes.get(i); all.append(norm(t)).append('\n');
            Matcher k = KM.matcher(t);
            while (k.find()) { Item it = new Item(); it.node = i; it.kind = 'k'; it.v = num(k.group(1)); items.add(it); }
            String rest = KM.matcher(t).replaceAll(" ");
            Matcher mt = MET.matcher(rest);
            while (mt.find()) { Item it = new Item(); it.node = i; it.kind = 'k'; it.v = num(mt.group(1)) / 1000.0; items.add(it); }
            Matcher mi = MIN.matcher(t);
            while (mi.find()) { Item it = new Item(); it.node = i; it.kind = 'm'; it.v = (mi.group(1) != null ? num(mi.group(1)) * 60 : 0) + num(mi.group(2)); items.add(it); }
        }
        boolean accept = false;
        for (String nd : nodes) if (isAcceptNode(nd)) { accept = true; break; }
        r.acceptSeen = accept;
        int kmCount = 0, minCount = 0;
        for (Item it : items) { if (it.kind == 'k') kmCount++; else minCount++; }
        r.offer = accept && kmCount >= 1 && minCount >= 1 && (r.price > 0 || (kmCount >= 2 && minCount >= 2));
        if (!r.offer) { r.why = "precio=" + r.price + " km=" + kmCount + " min=" + minCount + " aceptar=" + accept; return r; }
        // ---- emparejar km con minutos: 1) mismo nodo, 2) nodos contiguos
        List<Seg> segs = new ArrayList<Seg>();
        List<Item[]> pairs = new ArrayList<Item[]>();
        // fase A: km y minutos en el mismo nodo
        for (Item a : items) {
            if (a.kind != 'k' || a.used) continue;
            for (Item b : items) {
                if (b.kind == 'm' && !b.used && b.node == a.node) { a.used = true; b.used = true; pairs.add(new Item[]{a, b}); break; }
            }
        }
        // fase B: el minuto va justo antes del km (tambien con un "\u2022" entre medias) o, si no, justo despues
        for (Item a : items) {
            if (a.kind != 'k' || a.used) continue;
            Item best = null;
            for (int d = 1; d <= 2 && best == null; d++) {
                if (d == 2 && (a.node < 1 || nodes.get(a.node - 1).trim().length() > 2)) break;
                for (Item b : items) if (b.kind == 'm' && !b.used && b.node == a.node - d) { best = b; break; }
            }
            if (best == null) for (Item b : items) if (b.kind == 'm' && !b.used && b.node == a.node + 1) { best = b; break; }
            if (best != null) { a.used = true; best.used = true; pairs.add(new Item[]{a, best}); }
        }
        for (Item a : items) if (a.kind == 'k' && !a.used) { a.used = true; pairs.add(new Item[]{a, null}); }
        for (Item[] pr : pairs) {
            Seg s = new Seg(); s.km = pr[0].v; s.first = pr[0].node;
            StringBuilder own = new StringBuilder(norm(nodes.get(pr[0].node)));
            int firstNode = pr[0].node;
            if (pr[1] != null) { s.min = pr[1].v; firstNode = Math.min(firstNode, pr[1].node); s.first = firstNode; if (pr[1].node != pr[0].node) own.append(' ').append(norm(nodes.get(pr[1].node))); }
            String ownS = own.toString();
            // si el propio texto no trae pistas, se mira la l\u00EDnea anterior (etiqueta encima del valor)
            String prevS = firstNode > 0 ? norm(nodes.get(firstNode - 1)).trim() : "";
            boolean prevIsLabel = prevS.length() > 0 && prevS.length() <= 22 && !prevS.matches(".*\\d.*");
            s.ctx = (has(ownS, PICK) || has(ownS, TRIP) || !prevIsLabel) ? ownS : ownS + " " + prevS;
            segs.add(s);
        }
        for (Item b : items) {
            if (b.kind == 'm' && !b.used) { Seg s = new Seg(); s.min = b.v; s.first = b.node; s.ctx = norm(nodes.get(b.node)) + (b.node > 0 ? " " + norm(nodes.get(b.node - 1)) : ""); segs.add(s); }
        }
        java.util.Collections.sort(segs, new java.util.Comparator<Seg>() { public int compare(Seg x, Seg y) { return x.first - y.first; } });
        // ---- recogida o viaje
        Seg pick = null, trip = null;
        for (Seg s : segs) {
            boolean ip = has(s.ctx, PICK), it = has(s.ctx, TRIP);
            if (ip && !it && pick == null) pick = s; else if (it && !ip && trip == null) trip = s;
        }
        List<Seg> rest = new ArrayList<Seg>();
        for (Seg s : segs) if (s != pick && s != trip) rest.add(s);
        if (pick == null && trip == null && rest.size() >= 2) { pick = rest.get(0); trip = rest.get(1); r.orderAssumed = true; }
        else if (trip == null && !rest.isEmpty()) { trip = rest.get(rest.size() - 1); if (pick == null && rest.size() >= 2) pick = rest.get(0); r.orderAssumed = true; }
        else if (pick == null && !rest.isEmpty() && trip != null) { pick = rest.get(0); r.orderAssumed = true; }
        if (trip != null) { r.tripKm = trip.km; r.tripMin = trip.min; }
        if (pick != null) { r.pickupKm = pick.km; r.pickupMin = pick.min; }
        // ---- Bolt sin precio visible: estimacion con los km y minutos del viaje con pasajero (nunca los de recogida)
        r.isBolt = isBolt;
        boolean useEstimate = false;
        boolean boltEst = isBolt && p.bolt != null && p.bolt.on;
        if (r.price <= 0 && boltEst) {
            boolean tripSure = !(r.orderAssumed && pick == null);   // un unico bloque sin etiqueta no se da por viaje
            if (tripSure && r.tripKm > 0 && r.tripMin > 0) {
                double om = detectDemand(nodes);
                Est e = estimate(p.bolt, p.weekendNow, r.tripKm, r.tripMin, om, detectAirport(nodes));
                r.estimated = true; r.estGross = e.gross; r.estComm = e.comm; r.estNet = e.net; r.estMult = e.mult;
                r.estOfferMult = om;
                r.estAirport = e.airport; r.estFee = e.fee;
                r.estZone = e.zone; r.estArea = p.bolt.zoneName; r.estZoneSrc = p.bolt.zoneSrc;
                r.estRange = e.range; r.estNetLo = e.range ? e.netLo : -1; r.estNetHi = e.range ? e.netHi : -1;
                r.estAlt = e.alt; r.estPeakUsed = e.peakUsed; r.estFine = e.fine;
                r.estMinApplied = e.minApplied; r.estWeekend = e.weekend; r.estCommPct = Math.max(0, Math.min(90, p.bolt.comm));
                r.price = e.net;          // el semaforo se juzga sobre el NETO estimado; no se vuelve a descontar comision
                useEstimate = true;
            }
        }
        // ---- oferta sin precio visible: solo se puede juzgar la distancia de recogida
        if (r.price <= 0) {
            r.stP = r.pickupKm > 0 ? (r.pickupKm <= p.maxPickup ? 0 : (r.pickupKm <= p.maxPickup + p.tolPickup ? 1 : 2)) : -1;
            if (r.stP == 2) { r.verdict = "NO"; r.reason = String.format(Locale.GERMANY, "recogida %.1f km (m\u00E1x. %.1f)", r.pickupKm, p.maxPickup); }
            else { r.verdict = "DATA"; r.reason = boltEst ? "No se pudo estimar el precio de Bolt: faltan los km o los minutos del viaje con pasajero." : "Esta oferta no muestra el precio."; }
            return r;
        }
        // ---- datos suficientes
        if (r.tripKm <= 0 || r.tripMin <= 0) { r.verdict = "DATA"; r.reason = r.tripMin <= 0 ? "No se pudo leer el tiempo del viaje." : "No se pudo leer la distancia del viaje."; return r; }
        double net = useEstimate ? r.price : r.price * (1 - Math.max(0, Math.min(90, p.commission)) / 100.0);
        double km = r.tripKm + (p.includePickup && r.pickupKm > 0 ? r.pickupKm : 0);
        double min = r.tripMin + (p.includePickup && r.pickupMin > 0 ? r.pickupMin : 0);
        r.perKm = net / km; r.perHour = net / (min / 60.0);
        List<String> bad = new ArrayList<String>();
        r.stH = stMin(r.perHour, p.minHour, p.tolPct);
        r.stK = stMin(r.perKm, p.minKm, p.tolPct);
        r.stP = r.pickupKm > 0 ? (r.pickupKm <= p.maxPickup ? 0 : (r.pickupKm <= p.maxPickup + p.tolPickup ? 1 : 2)) : -1;
        if (r.stH > 0) bad.add(String.format(Locale.GERMANY, "\u20AC/h %.1f (m\u00EDn. %.2f)", r.perHour, p.minHour));
        if (r.stK > 0) bad.add(String.format(Locale.GERMANY, "\u20AC/km %.2f (m\u00EDn. %.2f)", r.perKm, p.minKm));
        if (r.stP > 0) bad.add(String.format(Locale.GERMANY, "recogida %.1f km (m\u00E1x. %.1f)", r.pickupKm, p.maxPickup));
        int worst = Math.max(r.stH, Math.max(r.stK, r.stP));
        r.verdict = worst >= 2 ? "NO" : (worst == 1 ? "WARN" : "OK");
        r.reason = bad.isEmpty() ? "Cumple tus objetivos." : join(bad);
        return r;
    }

    private static String join(List<String> l) { StringBuilder b = new StringBuilder(); for (int i = 0; i < l.size(); i++) { if (i > 0) b.append(" \u00B7 "); b.append(l.get(i)); } return b.toString(); }
}
