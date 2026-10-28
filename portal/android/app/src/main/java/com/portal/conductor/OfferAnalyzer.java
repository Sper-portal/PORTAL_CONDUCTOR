package com.portal.conductor;

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
        public boolean weekendNow = false;       // perfil de fin de semana/festivo (lo decide quien llama con isWeekend)
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
        public boolean isBolt, estimated, estWeekend, estMinApplied;
        public double estGross = -1, estComm = -1, estNet = -1, estMult = 1, estOfferMult = -1, estLo = -1, estHi = -1;
        public int estTier = -1;
        public double estCommPct = -1;
        public String estMode = "";
        public String estAirport = "";              // "" | "pickup" (recogida en el aeropuerto) | "dest" (viaje hacia el aeropuerto)
        public double estFee = 0;                   // tasa del aeropuerto restada antes de la comision
        // ---- ajuste por zona (v3.15f/g) ----
        public int estZone = 0;                     // 0 = sin ajuste de zona (aeropuerto, o ajuste apagado) | 1 = fuera de zona buena (M30 y sur) | 2 = zona buena
        public double estAdj = 0;                   // % de ajuste aplicado al calculo con la tarifa de Bolt (-8 fuera con poca demanda, 0 con x1,2 o mas, +12 en zona buena)
        public double estEff = 1;                   // demanda realmente aplicada (la curva de la demanda, no solo el xN de la oferta)
        public String estArea = "";                 // nombre de la zona buena donde se detecto la ubicacion
        public boolean estFromOffer = false;        // true si el calculo uso la demanda que muestra la oferta (false: la de Ajustes)
    }

    // =====================================================================
    //  Estimacion del precio de Bolt cuando la oferta NO muestra el precio (v3.15g).
    //  Todos los valores son ESTIMACIONES editables por el conductor, NO son tarifas oficiales de Bolt.
    //  Cuatro tarjetas de precios: normal y aeropuerto, cada una para entre semana y para fin de semana.
    //  Que tarjeta se usa lo deciden las franjas de fin de semana que define el conductor (y los festivos), no el dia del calendario.
    // =====================================================================

    /** Una tarjeta de precios: inicial + km * precioKm + min * precioMin, nunca menos que la minima (0 = sin minima). */
    public static class Card {
        public double base, perKm, perMin, minFare;
        public Card() { }
        public Card(double base, double perKm, double perMin, double minFare) { this.base = base; this.perKm = perKm; this.perMin = perMin; this.minFare = minFare; }
        public Card copy() { return new Card(base, perKm, perMin, minFare); }
    }

    /** Minutos de una semana (de lunes 00:00 a domingo 24:00). */
    public static final int WEEK_MIN = 10080;

    /** Franja de fin de semana: de "from" a "to" en minutos desde el lunes 00:00 (0..10079); si "to" es menor que "from" da la vuelta al domingo. */
    public static class Slot {
        public boolean on = true;
        public int from, to;
        public Slot() { }
        public Slot(int from, int to) { this.from = from; this.to = to; }
        public Slot copy() { Slot s = new Slot(from, to); s.on = on; return s; }
        /** true si el minuto de la semana w (0..10079) cae dentro: el principio cuenta, el final no. */
        public boolean contains(int w) { return from < to ? (w >= from && w < to) : (w >= from || w < to); }
    }

    /** Franjas iniciales: de viernes 18:00 a domingo 06:00. */
    public static List<Slot> defaultSlots() {
        List<Slot> l = new ArrayList<Slot>();
        l.add(new Slot(4 * 1440 + 18 * 60, 6 * 1440 + 6 * 60));
        return l;
    }

    /** Una zona buena: un poligono dibujado a mano (puntos [latitud, longitud] en orden). */
    public static class Area {
        public String name = "";
        public List<double[]> pts = new ArrayList<double[]>();
        public Area() { }
        public Area(String name, List<double[]> pts) { this.name = name; this.pts = pts; }
        public Area copy() {
            List<double[]> p = new ArrayList<double[]>();
            for (double[] q : pts) p.add(new double[]{q[0], q[1]});
            return new Area(name, p);
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

    /**
     * Ajuste por zona y por demanda (solo viajes normales; el aeropuerto no lo usa). Se aplica a la tarjeta normal:
     *   calculo = inicial + km * precio_km + min * precio_min  (nunca menos que la minima)
     * FUERA de zona buena (M30, sur...), segun la demanda m que muestra la oferta:
     *   m menor que realFrom (x1,2) ........ calculo * (1 + adj/100)            (por defecto -8 %)
     *   de realFrom a dFrom (x1,2 a x1,3) .. calculo * 1                         (tarifa real, sin demanda)
     *   desde dFrom (x1,4) ................. calculo * m * (1 + extra/100)       (extra: desde dA1 dP1 %, desde dA2 dP2 %, desde dA3 dP3 %; cada escalon sustituye al anterior)
     * EN zona buena: calculo * (1 + adjGood/100) * m   (por defecto +12 %; el multiplicador tal como sale, sin escalones)
     * Las zonas buenas son poligonos que dibuja el conductor y se detectan con la ubicacion del movil (sin ubicacion reciente: fuera de zona buena).
     * Con "on" apagado no hay ajustes: tarjeta * demanda tal como sale.
     */
    public static class Zone {
        public boolean on = true;
        public double adj = -8, adjGood = 12;
        public double mult = 1.0;                         // demanda a mano si la oferta no muestra ninguna (se trata como si la mostrara)
        public double realFrom = 1.2;
        public double dFrom = 1.4, dA1 = 1.5, dP1 = 5, dA2 = 2.0, dP2 = 8, dA3 = 2.5, dP3 = 10;
        public List<Area> good = new ArrayList<Area>();   // sin zonas al principio
        public Zone copy() {
            Zone z = new Zone();
            z.on = on; z.adj = adj; z.adjGood = adjGood; z.mult = mult;
            z.realFrom = realFrom; z.dFrom = dFrom; z.dA1 = dA1; z.dP1 = dP1; z.dA2 = dA2; z.dP2 = dP2; z.dA3 = dA3; z.dP3 = dP3;
            z.good = new ArrayList<Area>();
            for (Area a : good) z.good.add(a.copy());
            return z;
        }
        /** Demanda realmente aplicada para el xN que muestra la oferta. */
        public double demand(double m, boolean goodZone) {
            if (goodZone) return m;
            if (m < dFrom) return 1.0;
            double extra = m >= dA3 ? dP3 : (m >= dA2 ? dP2 : (m >= dA1 ? dP1 : 0));
            return m * (1 + extra / 100.0);
        }
        /** Ajuste (%) sobre el calculo de la tarjeta: -8 fuera si hay poca demanda, 0 fuera con x1,2 o mas, +12 en zona buena. */
        public double adjust(double m, boolean goodZone) {
            if (goodZone) return adjGood;
            return m < realFrom ? adj : 0;
        }
    }

    /** Distancia en km entre dos puntos (formula de haversine). */
    public static double distKm(double lat1, double lon1, double lat2, double lon2) {
        double rad = Math.PI / 180.0, dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return 6371.0 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    /** Nombre de la zona buena que contiene el punto, o null si no esta en ninguna. */
    public static String goodAreaAt(Zone z, double lat, double lon) {
        if (z == null || z.good == null) return null;
        for (Area a : z.good) if (a != null && a.contains(lat, lon)) return a.name;
        return null;
    }

    public static class BoltCfg {
        public Zone zone = new Zone();
        public boolean goodZone = false;     // lo pone el servicio en cada lectura segun la ubicacion (no se guarda)
        public String goodName = "";
        public boolean on = true;
        public String mode = "auto";         // auto (por las franjas) | week (siempre entre semana) | weekend (siempre fin de semana)
        public double comm = 25;             // comision de Bolt, %
        public boolean offerMult = true;     // usar el xN que muestre la oferta, si aparece
        // las cuatro tarjetas: normal / aeropuerto, entre semana (wd) / fin de semana (we)
        public Card nWd = new Card(2.10, 0.77, 0.15, 6.75), nWe = new Card(2.10, 0.77, 0.15, 6.75);
        public Card aWd = new Card(2.89, 0.82, 0.15, 13.50), aWe = new Card(2.89, 0.82, 0.15, 13.50);
        public boolean airOn = true;         // usar la tarjeta del aeropuerto (recogidas y viajes hacia el aeropuerto)
        public double airFee = 2.57;         // tasa del aeropuerto: se resta del bruto ANTES de la comision
        public List<Slot> slots = defaultSlots();
        public boolean holidaysWe = true;    // los festivos cuentan como fin de semana
        public List<String> holidays = defaultHolidays();   // "yyyy-MM-dd" o "MM-dd"
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

    /** true si ahora se usa la tarjeta de fin de semana: lo decide la franja en la que cae la hora (o un festivo), no el dia del calendario. */
    public static boolean isWeekend(BoltCfg c, java.util.Calendar cal) {
        if ("week".equals(c.mode)) return false;
        if ("weekend".equals(c.mode)) return true;
        if (c.holidaysWe && isHoliday(c, cal)) return true;
        int w = weekMinute(cal);
        if (c.slots != null) for (Slot s : c.slots) if (s != null && s.on && s.contains(w)) return true;
        return false;
    }

    public static class Est {
        public double gross, comm, net, mult, lo, hi, fee;
        public int tier;                     // siempre 0 (ya no hay tramos; se deja para no cambiar el resto del codigo)
        public String mode = "";             // "Z" = ajuste por zona y demanda | "" = tarjeta por la demanda tal como sale
        public String airport = "";          // "" | "pickup" | "dest"
        public boolean minApplied, weekend, fromOffer;
        public int zone = 0;                 // 0 = sin ajuste de zona | 1 = fuera de zona buena | 2 = zona buena
        public double adj = 0, eff = 1;      // % de ajuste aplicado y demanda realmente aplicada
    }

    // ---- aeropuerto: se detecta por el texto de la oferta ----
    // recogida: "parking P1 de la T1", "parking express T2", "parking modulo D planta 4 de la T4"
    private static final Pattern AIR_PICK_HINT = Pattern.compile("\\b(t\\s?[1-4]|p\\s?1|express|modulo\\s?d|terminal|aeropuerto|barajas)\\b");
    // destino: "Terminal 1..4", "Aeropuerto ...", "Avenida de la Hispanidad"
    private static final Pattern AIR_DEST = Pattern.compile("terminal\\s?[1-4]|aeropuerto|barajas|hispanidad");

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

    public static Est estimate(BoltCfg c, boolean weekend, double km, double min, double offerMult) { return estimate(c, weekend, km, min, offerMult, ""); }

    /**
     * Bruto = (inicial + km*precioKm + min*precioMin, nunca menos que la minima) de la tarjeta que toca, sin redondeos intermedios.
     *  - Tarjeta: la del aeropuerto (recogidas Y viajes hacia el aeropuerto) o la normal; la de entre semana o la de fin de semana segun "weekend".
     *  - Aeropuerto: la demanda multiplica todo (minima incluida), sin ajustes de zona; despues se resta la tasa del aeropuerto y sobre el resto se calcula la comision.
     *  - Normal con el ajuste por zona activado: ver Zone. Con el ajuste apagado: tarjeta * demanda tal como sale.
     */
    public static Est estimate(BoltCfg c, boolean weekend, double km, double min, double offerMult, String airKind) {
        boolean air = c.airOn && ("pickup".equals(airKind) || "dest".equals(airKind));
        String ak = air ? airKind : "";
        Card card = air ? (weekend ? c.aWe : c.aWd) : (weekend ? c.nWe : c.nWd);
        boolean fromOffer = c.offerMult && offerMult > 0;
        Est e = new Est();
        double raw = card.base + km * card.perKm + min * card.perMin;
        boolean ma = false;
        if (card.minFare > 0 && raw < card.minFare) { raw = card.minFare; ma = true; }
        Zone z = c.zone;
        double m = Math.max(0.1, Math.min(10.0, fromOffer ? offerMult : z.mult));
        double gross, mult;
        if (!air && z.on) {
            double adj = z.adjust(m, c.goodZone), eff = z.demand(m, c.goodZone);
            mult = eff > 1.0 + 1e-9 || c.goodZone ? m : 1.0;       // lo que se dice en voz alta: solo la demanda que de verdad se aplica
            gross = raw * (1 + adj / 100.0) * eff;
            e.lo = z.realFrom; e.hi = z.dFrom; e.mode = "Z";       // en modo zona: lo = desde que demanda se acaba el descuento, hi = desde que demanda se aplica
            e.zone = c.goodZone ? 2 : 1; e.adj = adj; e.eff = eff;
        } else {
            mult = m;
            gross = raw * m;
            e.eff = m;
        }
        double pct = Math.max(0, Math.min(90, c.comm));
        double fee = air ? c.airFee : 0;
        double after = fee > 0 ? Math.max(0, gross - fee) : gross;
        e.gross = gross; e.fee = fee; e.comm = after * pct / 100.0; e.net = after - e.comm;
        e.mult = mult; e.airport = ak; e.tier = 0;
        e.minApplied = ma; e.weekend = weekend; e.fromOffer = fromOffer;
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
            if (r.estZone == 2) b.append(", zona buena");
            if (r.estWeekend) b.append(", tarifa de fin de semana");
            if (Math.abs(r.estMult - 1.0) > 1e-9) b.append(", demanda por ").append(spokenNum(r.estMult, 2));
            b.append(". Bruto estimado: ").append(money(r.estGross)).append(" euros. ");
            if (r.estFee > 0) b.append("Tasa del aeropuerto: ").append(money(r.estFee)).append(" euros. ");
            b.append("Comisi\u00f3n estimada: ").append(money(r.estComm)).append(" euros. Neto estimado: ").append(money(r.estNet)).append(" euros.");
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
                r.estOfferMult = om; r.estMode = e.mode; r.estTier = e.tier; r.estLo = e.lo; r.estHi = e.hi;
                r.estAirport = e.airport; r.estFee = e.fee;
                r.estZone = e.zone; r.estAdj = e.adj; r.estEff = e.eff; r.estFromOffer = e.fromOffer; r.estArea = p.bolt.goodZone ? p.bolt.goodName : "";
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
