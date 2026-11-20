package com.portal.conductor;

import android.content.SharedPreferences;

/**
 * v3.62: la parte del cartel plegable de las ofertas (lengueta «Mas datos» y botones ✗ «No la hice» / ✓ «La acepte») que NO son vistas.
 * Solo usa las preferencias, asi que se puede probar sin movil.
 */
final class TabLogic {
    private TabLogic() {}

    /** tiempo que siguen los botones cuando la oferta ya ha desaparecido de la pantalla (p. ej. porque la has aceptado en Bolt) */
    static final long AFTER_MS = 15000L;
    /** una oferta solo se puede marcar si se leyo hace menos de esto (igual que en el Portal, que la suelta a los 90 s) */
    static final long VALID_MS = 90000L;

    /** el cartel sale plegado (veredicto, datos y neto) salvo que en Ajustes se ponga «completo» */
    static boolean fold(SharedPreferences sp) { return sp.getBoolean("tab_fold", true); }

    /** los botones solo salen si «Viajes guardados» esta activo (por defecto lo esta) */
    static boolean buttons(SharedPreferences sp) { return sp.getInt("trip_on", 1) == 1; }

    static long seq(SharedPreferences sp) { return sp.getLong("trip_seq", 0L); }

    // ------------------------------------------------------------------ v3.63: «Dejarla / Aceptarla» (lo que le pasa a la tasa de finalizacion de la semana)
    /** con menos de 20 ofertas que cuentan la cifra salta demasiado: se enseña sin color de aviso (igual que en el Portal) */
    static final int MIN_BASE = 20;

    /** la linea de la tasa: dos trozos, cada uno con su zona ('g' verde, 'o' naranja, 'r' roja, 'n' neutra) */
    static final class Rate {
        final String a, b;
        final char za, zb;
        Rate(String a, String b, char za, char zb) { this.a = a; this.b = b; this.za = za; this.zb = zb; }
        String text() { return b.length() == 0 ? a : a + "  \u00B7  " + b; }
    }

    /** verde / naranja (de 'orange' hacia abajo) / roja (por debajo de 'red') / neutra (sin datos o muy pocas ofertas) */
    static char zone(double rate, int den, double orange, double red) {
        if (den < MIN_BASE) return 'n';
        double r = Math.round(rate * 10.0) / 10.0;
        if (r < red) return 'r';
        if (r <= orange) return 'o';
        return 'g';
    }

    /** 87,3 % (con coma, como en el Portal) */
    static String pct(double v) { return String.format(java.util.Locale.US, "%.1f", v).replace('.', ',') + " %"; }

    /** las ✓ («la acepte») que el lector apunto en trip_decq DESPUES de que el Portal mandara la cuenta (ts > since): son hechas que la cuenta todavia no trae */
    static int acceptedSince(SharedPreferences sp, long since) {
        if (since <= 0) return 0;
        String q = sp.getString("trip_decq", "");
        if (q == null || q.length() == 0) return 0;
        int n = 0;
        for (String ln : q.split("\n")) {
            if (ln.indexOf("\"dec\":1,") < 0) continue;
            int i = ln.indexOf("\"ts\":");
            if (i < 0) continue;
            int j = i + 5, k = j;
            while (k < ln.length() && Character.isDigit(ln.charAt(k))) k++;
            try { if (k > j && Long.parseLong(ln.substring(j, k)) > since) n++; } catch (Exception e) { }
        }
        return Math.min(n, 20);
    }

    /**
     * Lo que le pasa a la tasa de la semana si dejas pasar la oferta o si la aceptas. Lo calcula el lector con la cuenta que le manda el Portal:
     * rate_num (hechas) y rate_den (ofertas que cuentan) sin las ofertas que el Portal aun no ha recogido, rate_seq (hasta que oferta esta contada)
     * y rate_until (cuando acaba la semana); rate_ts = cuando llego esa cuenta (las ✓ apuntadas despues se suman a las hechas). nx = la oferta trae el aviso «fuera de radio» (o es una «Asignar» que aun no cuenta): dejarla no cuenta.
     * null si el Portal todavia no ha mandado nada.
     */
    static Rate rate(SharedPreferences sp, long now, long seq, boolean nx, boolean asg, int asgSec) {
        if (!sp.getBoolean("rate_has", false)) return null;
        boolean fresh = now < sp.getLong("rate_until", 0L);
        int num = fresh ? sp.getInt("rate_num", 0) + acceptedSince(sp, sp.getLong("rate_ts", 0L)) : 0;
        int den = fresh ? sp.getInt("rate_den", 0) : 0;
        double orange = sp.getFloat("rate_orange", 90f), red = sp.getFloat("rate_red", 85f);
        long snap = fresh ? sp.getLong("rate_seq", 0L) : 0L;
        long pend = (snap > 0 && seq >= snap) ? seq - snap : 1L;          // ofertas leidas que el Portal aun no ha contado (la de ahora entre ellas)
        int base = den + (pend > 0 ? (int) Math.min(pend - 1, 200L) : 0);  // las otras se cuentan como ofertas normales
        if (!nx) {
            int dc = Math.max(pend > 0 ? base + 1 : base, num);               // ofertas que cuentan, con esta
            if (dc < MIN_BASE) return new Rate("Pocas ofertas esta semana para calcular", "", 'n', 'n');
            double leave = (double) num / dc * 100.0;
            double doit = Math.min(100.0, (num + 1.0) / Math.max(dc, num + 1) * 100.0);
            char zl = zone(leave, dc, orange, red);
            return new Rate((zl == 'r' ? "\u26A0 " : zl == 'o' ? "\u25B2 " : "") + "Dejarla: " + pct(leave), "Aceptarla: " + pct(doit), zl, zone(doit, dc, orange, red));
        }
        int dn = Math.max(base + 1, num + 1);                                  // con aviso: dejarla no cuenta; aceptarla suma una hecha y una que cuenta
        double doit = Math.min(100.0, (num + 1.0) / dn * 100.0);
        String a = asg ? "\u00ABAsignar\u00BB: solo cuenta si pasa de " + asgSec + " s" : "Fuera de radio: dejarla no cuenta";
        return new Rate(a, "Aceptarla: " + pct(doit), 'n', 'n');
    }

    /** esta oferta ya se marco (con ✗ o con ✓) */
    static boolean decided(SharedPreferences sp, long seq) { return seq > 0 && sp.getLong("trip_dec_seq", 0L) == seq; }

    /** 1 = la acepte, 0 = no la hice, -1 = sin marcar */
    static int decision(SharedPreferences sp, long seq) { return decided(sp, seq) ? sp.getInt("trip_dec", -1) : -1; }

    /** hay una oferta apuntada, se leyo hace poco y todavia no se ha marcado */
    static boolean canMark(SharedPreferences sp, long now) {
        long seq = seq(sp);
        if (!buttons(sp) || seq <= 0 || decided(sp, seq)) return false;
        long ts = sp.getLong("trip_ts", 0L);
        return ts > 0 && now - ts >= 0 && now - ts <= VALID_MS;
    }

    /** las marcas que se guardan para el Portal (una por oferta; el Portal las recoge con tripCur, este abierto o no) */
    static final int MAX_Q = 20;

    /** deja la marca para el Portal. false si no hay nada que marcar */
    static boolean mark(SharedPreferences sp, boolean yes, long now) {
        if (!canMark(sp, now)) return false;
        long seq = seq(sp);
        SharedPreferences.Editor ed = sp.edit().putLong("trip_dec_seq", seq).putInt("trip_dec", yes ? 1 : 0).putLong("trip_dec_ts", now);
        String o = sp.getString("trip_cur", "");
        if (o != null && o.length() > 1 && o.charAt(0) == '{') {
            o = o.replace('\n', ' ').replace('\r', ' ');
            ed.putString("trip_decq", queue(sp.getString("trip_decq", ""), "{\"seq\":" + seq + ",\"dec\":" + (yes ? 1 : 0) + ",\"ts\":" + now + ",\"o\":" + o + "}"));
        }
        ed.apply();
        return true;
    }

    /** cola de marcas: una por linea, solo las ultimas MAX_Q */
    static String queue(String old, String line) {
        String all = (old == null || old.length() == 0) ? line : old + "\n" + line;
        int n = 0;
        for (int i = 0; i < all.length(); i++) if (all.charAt(i) == '\n') n++;
        while (n >= MAX_Q) { all = all.substring(all.indexOf('\n') + 1); n--; }
        return all;
    }
}
