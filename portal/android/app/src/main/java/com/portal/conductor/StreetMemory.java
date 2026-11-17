package com.portal.conductor;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * v3.57: memoria de «calles limitrofes».
 * Solo guarda las direcciones de recogida en las que el conductor ELIGIO la zona en el aviso (cuando habia duda entre dos zonas)
 * o que apunto a mano en la lista de Rentabilidad. La proxima vez que sale la misma calle con el mismo numero, el aviso usa esa zona.
 * No cambia ninguna formula: solo decide QUE zona (baja, media o alta) se usa para la recogida.
 * Maximo 300 direcciones vivas (si se llena, se olvida la que lleva mas tiempo sin usarse). Una direccion = calle + numero + codigo postal.
 */
public final class StreetMemory {
    private StreetMemory() { }

    public static final int MAX = 300;                         // direcciones vivas
    public static final int MAX_ALL = 600;                     // con las borradas (que se recuerdan un tiempo para que el borrado llegue a tus otros moviles)
    public static final long TOMB_MS = 60L * 24L * 3600L * 1000L;
    public static final long TOUCH_MS = 12L * 3600L * 1000L;   // el «ultimo uso» se anota como mucho cada 12 horas

    /** direccion leida de la tarjeta (o escrita a mano) */
    public static class Addr {
        public String street = "";   // como se ve («Calle San Joaquin»), sin el numero
        public String num = "";      // «2», «12b»; vacio si no hay
        public String cp = "";       // 28xxx; vacio si no hay
        public String core = "";     // nombre sin el tipo de via ni articulos, en minusculas y sin acentos («san joaquin»)
    }

    public static class Entry {
        public String street = "", num = "", cp = "", core = "";
        public int zone = 1;           // 0 baja, 1 media, 2 alta
        public char origin = 'u';      // 'u' = lo elegiste en un aviso, 'm' = lo apuntaste a mano, 'd' = tramo dudoso (sin numero)
        public long t = 0;             // ultimo cambio (segundos)
        public long l = 0;             // ultimo uso (segundos)
        public boolean del;            // borrada
        public String key() { return StreetMemory.key(core, num, cp); }
    }

    public static String key(String core, String num, String cp) { return core + "|" + num + "|" + cp; }

    // ------------------------------------------------------------------ lectura de la direccion

    private static final Pattern POSTAL = Pattern.compile("(?<![\\d.,])(28\\d{3})(?!\\d|[.,]\\d)");
    private static final Pattern NUMTOK = Pattern.compile("^\\d{1,4}[a-z]?$");
    private static final Pattern NOISE = Pattern.compile("(?s).*(\\d\\s*(min|km|eur)\\b|\\u2605|\\u20AC|x\\s?\\d+[.,]\\d).*");
    private static final String TYPES = " calle c cl avenida avda av paseo p po plaza pza pl camino carretera ctra travesia trv ronda glorieta bulevar via urbanizacion urb callejon cuesta pasaje costanilla autovia parque ";
    private static final String CONN = " de del la las los el ";

    /** minusculas, sin acentos, sin º/ª/°; todo lo que no sea letra o cifra pasa a espacio; espacios unidos. Igual que stNorm de la pantalla. */
    static String plain(String s) {
        if (s == null) return "";
        String x = Normalizer.normalize(s.toLowerCase(java.util.Locale.ROOT), Normalizer.Form.NFD);
        x = x.replaceAll("\\p{M}+", "");
        x = x.replaceAll("[\\u00BA\\u00B0\\u00AA]", "");
        x = x.replaceAll("[^a-z0-9]+", " ").trim();
        return x;
    }

    /** nombre de la calle sin el tipo de via («calle», «avda»...) ni los articulos del principio («de la»): «Calle de la Princesa» -> «princesa» */
    public static String coreOf(String street) {
        String[] tk = plain(street).split(" ");
        int i = 0;
        if (tk.length > 0 && tk[0].length() > 0 && TYPES.contains(" " + tk[0] + " ")) i = 1;
        while (i < tk.length - 1 && CONN.contains(" " + tk[i] + " ")) i++;
        StringBuilder b = new StringBuilder();
        for (; i < tk.length; i++) { if (tk[i].length() == 0) continue; if (b.length() > 0) b.append(' '); b.append(tk[i]); }
        String c = b.toString();
        return c.length() > 60 ? c.substring(0, 60).trim() : c;
    }

    /** ¿la calle empieza por un tipo de via («Calle», «Avda.», «C/»...)? */
    public static boolean hasType(String street) {
        String[] tk = plain(street).split(" ");
        return tk.length > 0 && tk[0].length() > 0 && TYPES.contains(" " + tk[0] + " ");
    }

    private static String numNorm(String s) {
        String x = plain(s).replace(" ", "");
        return NUMTOK.matcher(x).matches() ? x : "";
    }

    /** direccion a partir de lo escrito a mano o ya separado (calle, numero, codigo postal); null si no vale */
    public static Addr addrOf(String street, String num, String cp) {
        if (street == null) return null;
        String st = street.trim().replaceAll("\\s+", " ");
        if (st.length() > 60) st = st.substring(0, 60).trim();
        Addr a = new Addr();
        a.street = st;
        a.core = coreOf(st);
        if (a.core.length() < 2) return null;
        a.num = num == null ? "" : numNorm(num);
        String c = cp == null ? "" : cp.trim();
        a.cp = POSTAL.matcher(c).matches() ? c : "";
        return a;
    }

    /** direccion de UNA linea de la tarjeta («Calle Goya 12, Madrid 28001»); null si la linea no parece una direccion */
    public static Addr parse(String raw) {
        if (raw == null) return null;
        String s = raw.replace(' ', ' ').trim();
        if (s.length() < 5 || s.length() > 160) return null;
        if (NOISE.matcher(s.toLowerCase(java.util.Locale.ROOT)).matches()) return null;
        String cp = "";
        int cut = s.length();
        Matcher pm = POSTAL.matcher(s);
        if (pm.find()) { cp = pm.group(1); cut = pm.start(); }
        String head = s.substring(0, cut).trim().replaceAll("[\\s,;\\-\\u2013]+$", "");
        if (head.length() < 3) return null;
        String[] parts = head.split(",");
        String first = parts[0].trim();
        String[] tk = first.split("\\s+");
        int n = tk.length;
        String num = "";
        while (n >= 3 && (tk[n - 1].indexOf('\u00BA') >= 0 || tk[n - 1].indexOf('\u00B0') >= 0 || tk[n - 1].indexOf('\u00AA') >= 0)) n--;   // «2º» al final es un piso, no el numero
        if (n >= 2) {
            String last = plain(tk[n - 1]).replace(" ", "");
            if (NUMTOK.matcher(last).matches()) {
                num = last; n--;
                if (n >= 2) { String w = plain(tk[n - 1]); if (w.equals("n") || w.equals("no") || w.equals("num") || w.equals("numero")) n--; }
            } else if (tk[n - 1].equalsIgnoreCase("s/n")) { n--; }
        }
        if (num.length() == 0 && parts.length >= 2) {
            String p1 = plain(parts[1]);
            p1 = p1.replaceFirst("^(n|no|num|numero) ", "");
            p1 = p1.replace(" ", "");
            if (NUMTOK.matcher(p1).matches()) num = p1;
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) { if (i > 0) sb.append(' '); sb.append(tk[i]); }
        String street = sb.toString().trim();
        if (street.length() < 3) return null;
        boolean typed = hasType(street);
        if (!typed && !(cp.length() > 0 && num.length() > 0)) return null;     // sin «Calle», «Avenida»... solo vale si trae numero y codigo postal
        Addr a = addrOf(street, num, cp);
        return a;
    }

    /**
     * direccion de la RECOGIDA: la linea con direccion mas cercana ANTES del bloque km/min del viaje con pasajero (en la tarjeta la recogida va antes que el destino).
     * Si la linea no trae codigo postal se usa el que dice OfferAnalyzer.pickupPostal. null si no se sabe cual es el viaje o no hay direccion.
     */
    public static Addr pickupAddress(List<String> nodes, int tripFirst) {
        if (nodes == null || tripFirst <= 0) return null;
        int stop = Math.max(0, Math.min(tripFirst, nodes.size()) - 5);
        for (int i = Math.min(tripFirst, nodes.size()) - 1; i >= stop; i--) {
            Addr a = parse(nodes.get(i));
            if (a == null) continue;
            if (a.cp.length() == 0) { String cp = OfferAnalyzer.pickupPostal(nodes, tripFirst); if (cp != null) a.cp = cp; }
            return a;
        }
        return null;
    }

    // ------------------------------------------------------------------ busqueda y cambios

    /** la direccion guardada que coincide; null si no hay. Con codigo postal en los dos lados tiene que ser el mismo; si a uno le falta, vale si solo hay una candidata */
    public static Entry find(List<Entry> l, Addr a) {
        if (l == null || a == null || a.core.length() == 0) return null;
        Entry cand = null;
        int cnt = 0;
        for (Entry e : l) {
            if (e == null || e.del) continue;
            if (!e.core.equals(a.core) || !e.num.equals(a.num)) continue;
            if (a.cp.length() > 0 && e.cp.length() > 0) { if (e.cp.equals(a.cp)) return e; continue; }
            cand = e; cnt++;
        }
        return cnt == 1 ? cand : null;
    }

    private static Entry findAny(List<Entry> l, Addr a) {
        for (Entry e : l) if (e.core.equals(a.core) && e.num.equals(a.num) && e.cp.equals(a.cp)) return e;
        return null;
    }

    public static int live(List<Entry> l) {
        int c = 0;
        if (l != null) for (Entry e : l) if (e != null && !e.del) c++;
        return c;
    }

    /** apunta la zona de una direccion (nueva o cambia la que habia). origin: 'u' elegida en el aviso, 'm' a mano; sin numero queda como 'd' (tramo dudoso). Devuelve la entrada. */
    public static Entry put(List<Entry> l, Addr a, int zone, char origin, long nowMs) {
        if (l == null || a == null || zone < 0 || zone > 2) return null;
        long ts = nowMs / 1000L;
        Entry e = find(l, a);
        if (e == null) e = findAny(l, a);
        if (e == null) { e = new Entry(); l.add(e); }
        e.street = a.street; e.core = a.core; e.num = a.num;
        if (a.cp.length() > 0) e.cp = a.cp;
        e.zone = zone;
        e.origin = a.num.length() == 0 ? 'd' : (origin == 'm' ? 'm' : 'u');
        e.t = ts; e.l = ts; e.del = false;
        prune(l, nowMs);
        return e;
    }

    /** borra una direccion (queda marcada como borrada un tiempo para que el borrado llegue a tus otros moviles) */
    public static boolean remove(List<Entry> l, Addr a, long nowMs) {
        Entry e = find(l, a);
        if (e == null) return false;
        e.del = true; e.t = nowMs / 1000L;
        return true;
    }

    /** anota que se ha usado (como mucho una vez cada 12 horas); true si cambia algo */
    public static boolean touch(Entry e, long nowMs) {
        if (e == null || e.del) return false;
        long ts = nowMs / 1000L;
        if (ts - e.l < TOUCH_MS / 1000L) return false;
        e.l = ts;
        return true;
    }

    /** limpia: quita las borradas viejas; si hay mas de MAX vivas se olvidan las que llevan mas tiempo sin usarse; tope total MAX_ALL */
    public static void prune(List<Entry> l, long nowMs) {
        if (l == null) return;
        long ts = nowMs / 1000L;
        for (int i = l.size() - 1; i >= 0; i--) { Entry e = l.get(i); if (e == null || (e.del && ts - e.t > TOMB_MS / 1000L)) l.remove(i); }
        while (live(l) > MAX) {
            Entry old = null;
            for (Entry e : l) if (!e.del && (old == null || e.l < old.l || (e.l == old.l && e.t < old.t))) old = e;
            if (old == null) break;
            old.del = true; old.t = ts;
        }
        while (l.size() > MAX_ALL) {
            Entry old = null;
            for (Entry e : l) if (e.del && (old == null || e.t < old.t)) old = e;
            if (old == null) break;
            l.remove(old);
        }
    }

    // ------------------------------------------------------------------ guardado (texto JSON compacto: [{"s":"Calle X","n":"2","c":"28001","k":"x","z":0,"o":"u","t":1763380000,"l":1763380000}])

    private static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 0x20) b.append(' ');
            else b.append(c);
        }
        return b.append('"').toString();
    }

    public static String toJson(List<Entry> l) {
        StringBuilder b = new StringBuilder("[");
        boolean first = true;
        if (l != null) for (Entry e : l) {
            if (e == null || e.core.length() == 0) continue;
            if (!first) b.append(',');
            first = false;
            b.append("{\"s\":").append(q(e.street)).append(",\"n\":").append(q(e.num)).append(",\"c\":").append(q(e.cp)).append(",\"k\":").append(q(e.core));
            b.append(",\"z\":").append(e.zone).append(",\"o\":\"").append(e.origin).append("\",\"t\":").append(e.t).append(",\"l\":").append(e.l);
            if (e.del) b.append(",\"x\":1");
            b.append('}');
        }
        return b.append(']').toString();
    }

    /** lee el JSON de arriba; lo que no se entiende se salta (nunca lanza error) */
    public static List<Entry> parseJson(String js) {
        List<Entry> out = new ArrayList<Entry>();
        if (js == null) return out;
        try {
            int i = 0, n = js.length();
            while (i < n && js.charAt(i) != '[') i++;
            i++;
            while (i < n) {
                while (i < n && js.charAt(i) != '{' && js.charAt(i) != ']') i++;
                if (i >= n || js.charAt(i) == ']') break;
                i++;
                Entry e = new Entry();
                boolean ok = false;
                while (i < n) {
                    while (i < n && (js.charAt(i) == ' ' || js.charAt(i) == ',' || js.charAt(i) == '\n' || js.charAt(i) == '\r' || js.charAt(i) == '\t')) i++;
                    if (i >= n) break;
                    if (js.charAt(i) == '}') { i++; break; }
                    if (js.charAt(i) != '"') { i++; continue; }
                    int[] pos = {i};
                    String k = str(js, pos);
                    i = pos[0];
                    while (i < n && (js.charAt(i) == ' ' || js.charAt(i) == ':')) i++;
                    String v;
                    if (i < n && js.charAt(i) == '"') { pos[0] = i; v = str(js, pos); i = pos[0]; }
                    else { int j = i; while (j < n && js.charAt(j) != ',' && js.charAt(j) != '}') j++; v = js.substring(i, j).trim(); i = j; }
                    if (k == null || v == null) continue;
                    if (k.equals("s")) e.street = v.trim();
                    else if (k.equals("n")) e.num = numNorm(v);
                    else if (k.equals("c")) e.cp = POSTAL.matcher(v.trim()).matches() ? v.trim() : "";
                    else if (k.equals("k")) e.core = v.trim();
                    else if (k.equals("z")) { try { int z = Integer.parseInt(v); if (z >= 0 && z <= 2) { e.zone = z; ok = true; } } catch (Exception ex) { } }
                    else if (k.equals("o")) e.origin = v.equals("m") ? 'm' : (v.equals("d") ? 'd' : 'u');
                    else if (k.equals("t")) { try { e.t = Long.parseLong(v); } catch (Exception ex) { } }
                    else if (k.equals("l")) { try { e.l = Long.parseLong(v); } catch (Exception ex) { } }
                    else if (k.equals("x")) e.del = v.equals("1") || v.equals("true");
                }
                if (e.core.length() == 0 && e.street.length() > 0) e.core = coreOf(e.street);
                if (ok && e.core.length() >= 2) out.add(e);
            }
        } catch (Throwable t) { }
        return out;
    }

    private static String str(String s, int[] pos) {
        int i = pos[0], n = s.length();
        if (i >= n || s.charAt(i) != '"') return null;
        i++;
        StringBuilder b = new StringBuilder();
        while (i < n) {
            char c = s.charAt(i);
            if (c == '"') { pos[0] = i + 1; return b.toString(); }
            if (c == '\\' && i + 1 < n) {
                char d = s.charAt(i + 1);
                if (d == 'u' && i + 5 < n) { try { b.append((char) Integer.parseInt(s.substring(i + 2, i + 6), 16)); i += 6; continue; } catch (Exception ex) { } }
                b.append(d == 'n' || d == 't' || d == 'r' ? ' ' : d);
                i += 2;
                continue;
            }
            b.append(c);
            i++;
        }
        pos[0] = n;
        return b.toString();
    }
}
