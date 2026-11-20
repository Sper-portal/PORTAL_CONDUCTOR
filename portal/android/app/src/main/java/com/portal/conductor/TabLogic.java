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
