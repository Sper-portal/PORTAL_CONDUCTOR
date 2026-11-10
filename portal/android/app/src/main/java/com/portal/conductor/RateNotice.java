package com.portal.conductor;

import java.text.Normalizer;
import java.util.List;

/**
 * v3.43: reads the notice Bolt puts on the offers that do NOT count for the acceptance rate:
 * the tag "Fuera del radio" and the sentence "Rechazar no afectara tu tasa de aceptacion".
 * Bookings (tag "Reservado") never carry that notice, but Bolt does not count them either when the pickup is farther than 2 km, so those count as "no effect" too.
 * Pure text logic (no Android classes), so it can be tested without a phone.
 */
final class RateNotice {
    private RateNotice() {}

    /** lower case, no accents, single spaces (non-breaking spaces count as spaces) */
    static String norm(String s) {
        if (s == null) return "";
        String t = Normalizer.normalize(s, Normalizer.Form.NFD);
        StringBuilder b = new StringBuilder(t.length());
        boolean sp = false;
        for (int i = 0; i < t.length(); i++) {
            char c = t.charAt(i);
            if (Character.getType(c) == Character.NON_SPACING_MARK) continue;
            if (Character.isWhitespace(c) || c == ' ' || c == ' ') { sp = true; continue; }
            if (sp && b.length() > 0) b.append(' ');
            sp = false;
            b.append(Character.toLowerCase(c));
        }
        return b.toString();
    }

    /** t must already be normalised */
    static boolean hasNotice(String t) {
        if (t.contains("fuera del radio")) return true;
        return t.contains("tasa de aceptacion") && (t.contains("no afectara") || t.contains("no te afectara"));
    }

    /** a booking farther away than this (km to the pickup) does not touch the acceptance rate when it is not accepted */
    static final double BOOKING_FAR_KM = 2.0;

    /** t must already be normalised: the chip "Reservado" (alone in its node) */
    static boolean isBookingTag(String t) {
        if (!t.startsWith("reservado")) return false;
        for (int i = "reservado".length(); i < t.length(); i++) {
            char c = t.charAt(i);
            if (c != ' ' && c != '.' && c != ',' && c != ':' && c != ';') return false;
        }
        return true;
    }

    /** true when the offer card carries the chip "Reservado" (a booking) */
    static boolean booking(List<String> nodes) {
        if (nodes == null) return false;
        for (int i = 0; i < nodes.size(); i++) if (isBookingTag(norm(nodes.get(i)))) return true;
        return false;
    }

    /** true for a booking whose pickup is farther than 2 km (pickupKm <= 0 means "unknown": then it counts as a normal offer) */
    static boolean farBooking(List<String> nodes, double pickupKm) {
        return pickupKm > BOOKING_FAR_KM && booking(nodes);
    }

    /** true when the offer card says it is outside the radius or that rejecting it will not change the acceptance rate */
    static boolean noEffect(List<String> nodes) {
        if (nodes == null) return false;
        StringBuilder all = new StringBuilder();
        for (int i = 0; i < nodes.size(); i++) {
            String t = norm(nodes.get(i));
            if (t.length() == 0) continue;
            if (hasNotice(t)) return true;
            all.append(t).append(' ');
        }
        return hasNotice(all.toString());
    }
}
