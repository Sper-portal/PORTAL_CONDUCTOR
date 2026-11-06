package com.portal.conductor;

import android.content.SharedPreferences;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * Pure logic of the trip recorder (v3.42): video sizes, bitrates and the saved state of a recording.
 * It does not touch the camera, so it can be tested without a phone.
 * State lives in SharedPreferences "portal": one "active" recording (being made) and one "pending" recording
 * (finished, waiting for the driver to save it or delete it). Only one of each at a time.
 */
final class TripRecorderStore {
    private TripRecorderStore() {}

    static final String PREFS = "portal";
    static final int AUDIO_BITRATE = 96000;
    static final long MIN_USABLE_BYTES = 200L * 1024L;

    private static final String A_PATH = "rec_a_path", A_START = "rec_a_start", A_PLAN = "rec_a_plan", A_AUDIO = "rec_a_audio", A_BEAT = "rec_a_beat";
    private static final String P_PATH = "rec_p_path", P_MS = "rec_p_ms", P_AUDIO = "rec_p_audio", P_AT = "rec_p_at", P_CUT = "rec_p_cut", P_WHY = "rec_p_why";
    private static final String E_CODE = "rec_err", E_AT = "rec_err_at";

    /** A finished recording waiting to be saved or deleted. */
    static final class Pending {
        String path = "";
        long durationMs;
        long sizeBytes;
        boolean audio;
        long at;
        boolean cut;
        String why = "";
    }

    // ------------------------------------------------------------------ numbers

    static int clampMinutes(int m) {
        if (m < 1) return 1;
        if (m > 60) return 60;
        return m;
    }

    /** Video bitrate for a size: Full HD 6 Mbps, HD 3.5 Mbps, less 1.8 Mbps. */
    static int videoBitrate(int w, int h) {
        long px = (long) w * (long) h;
        if (px >= 1920L * 1080L) return 6000000;
        if (px >= 1280L * 720L) return 3500000;
        return 1800000;
    }

    /** Approximate file size in bytes of a recording of ms milliseconds. */
    static long estimateBytes(int videoBps, boolean audio, long ms) {
        long bps = (long) videoBps + (audio ? AUDIO_BITRATE : 0);
        return bps * ms / 8000L;
    }

    /** Sizes to try, best first: 1920x1080, then 1280x720, then 640x480; if the camera offers none of them, one fallback. */
    static int[][] candidates(int[] ws, int[] hs) {
        int n = (ws == null || hs == null) ? 0 : Math.min(ws.length, hs.length);
        int[][] tiers = { { 1920, 1080 }, { 1280, 720 }, { 640, 480 } };
        List<int[]> out = new ArrayList<int[]>();
        for (int t = 0; t < tiers.length; t++) {
            for (int i = 0; i < n; i++) {
                if (ws[i] == tiers[t][0] && hs[i] == tiers[t][1]) {
                    out.add(new int[] { tiers[t][0], tiers[t][1] });
                    break;
                }
            }
        }
        if (out.isEmpty()) {
            int best = -1;
            for (int i = 0; i < n; i++) {
                if (hs[i] <= 1080 && (best < 0 || (long) ws[i] * hs[i] > (long) ws[best] * hs[best])) best = i;
            }
            if (best < 0) {
                for (int i = 0; i < n; i++) {
                    if (best < 0 || (long) ws[i] * hs[i] < (long) ws[best] * hs[best]) best = i;
                }
            }
            if (best >= 0) out.add(new int[] { ws[best], hs[best] });
        }
        if (out.isEmpty()) out.add(new int[] { 1280, 720 });
        return out.toArray(new int[out.size()][]);
    }

    /** Orientation hint for the MP4: sensor orientation minus the display rotation (0..3 quarter turns). */
    static int orientationHint(int sensor, int rotation) {
        int r = ((rotation % 4) + 4) % 4;
        return (((sensor - r * 90) % 360) + 360) % 360;
    }

    static String fileName(long now) {
        return "viaje_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date(now)) + ".mp4";
    }

    // ------------------------------------------------------------------ active recording (being made)

    static void markActive(SharedPreferences sp, String path, long startWall, long plannedMs, boolean audio) {
        sp.edit().putString(A_PATH, path).putLong(A_START, startWall).putLong(A_PLAN, plannedMs)
                .putBoolean(A_AUDIO, audio).putLong(A_BEAT, 0L).commit();
    }

    /** Remembers how many milliseconds have been recorded so far (written every few seconds, used if the app is killed). */
    static void beat(SharedPreferences sp, long elapsedMs) {
        String p = sp.getString(A_PATH, "");
        if (p != null && p.length() > 0) sp.edit().putLong(A_BEAT, elapsedMs).apply();
    }

    static String activePath(SharedPreferences sp) {
        String p = sp.getString(A_PATH, "");
        return p == null ? "" : p;
    }

    static void clearActive(SharedPreferences sp) {
        sp.edit().remove(A_PATH).remove(A_START).remove(A_PLAN).remove(A_AUDIO).remove(A_BEAT).commit();
    }

    // ------------------------------------------------------------------ pending recording (finished)

    static void setPending(SharedPreferences sp, File f, long durationMs, boolean audio, boolean cut, String why, long at) {
        sp.edit().putString(P_PATH, f.getAbsolutePath()).putLong(P_MS, durationMs).putBoolean(P_AUDIO, audio)
                .putLong(P_AT, at).putBoolean(P_CUT, cut).putString(P_WHY, why == null ? "" : why).commit();
        clearActive(sp);
    }

    static Pending readPending(SharedPreferences sp) {
        String p = sp.getString(P_PATH, "");
        if (p == null || p.length() == 0) return null;
        File f = new File(p);
        if (!f.isFile()) {
            clearPendingKeys(sp);
            return null;
        }
        Pending r = new Pending();
        r.path = p;
        r.durationMs = sp.getLong(P_MS, 0L);
        r.sizeBytes = f.length();
        r.audio = sp.getBoolean(P_AUDIO, false);
        r.at = sp.getLong(P_AT, 0L);
        r.cut = sp.getBoolean(P_CUT, false);
        String w = sp.getString(P_WHY, "");
        r.why = w == null ? "" : w;
        return r;
    }

    private static void clearPendingKeys(SharedPreferences sp) {
        sp.edit().remove(P_PATH).remove(P_MS).remove(P_AUDIO).remove(P_AT).remove(P_CUT).remove(P_WHY).commit();
    }

    /** Deletes the pending file (if any) and forgets it. */
    static void discardPending(SharedPreferences sp) {
        String p = sp.getString(P_PATH, "");
        if (p != null && p.length() > 0) {
            File f = new File(p);
            if (f.isFile()) f.delete();
        }
        clearPendingKeys(sp);
    }

    /** Forgets the pending recording without touching the file (it was already copied somewhere else). */
    static void forgetPending(SharedPreferences sp) {
        clearPendingKeys(sp);
    }

    // ------------------------------------------------------------------ errors

    static void setError(SharedPreferences sp, String code, long at) {
        sp.edit().putString(E_CODE, code).putLong(E_AT, at).commit();
    }

    static String readError(SharedPreferences sp) {
        String e = sp.getString(E_CODE, "");
        return e == null ? "" : e;
    }

    static long readErrorAt(SharedPreferences sp) {
        return sp.getLong(E_AT, 0L);
    }

    static void clearError(SharedPreferences sp) {
        sp.edit().remove(E_CODE).remove(E_AT).commit();
    }

    // ------------------------------------------------------------------ recovery

    /**
     * If a recording was "active" but the service is not running (the phone killed the app), turn what is on disk
     * into a pending recording marked as cut, or report it as lost when there is nothing useful.
     * Returns true when something changed.
     */
    static boolean reconcile(SharedPreferences sp, boolean serviceRunning, long now) {
        String p = activePath(sp);
        if (p.length() == 0 || serviceRunning) return false;
        File f = new File(p);
        long beat = sp.getLong(A_BEAT, 0L);
        long plan = sp.getLong(A_PLAN, 0L);
        boolean audio = sp.getBoolean(A_AUDIO, false);
        long dur = Math.max(0L, beat);
        if (plan > 0 && dur > plan) dur = plan;
        if (f.isFile() && f.length() >= MIN_USABLE_BYTES) {
            setPending(sp, f, dur, audio, true, "killed", now);
        } else {
            if (f.isFile()) f.delete();
            clearActive(sp);
            setError(sp, "lost", now);
        }
        return true;
    }

    /** Deletes recordings in dir that nobody refers to (leftovers of failed attempts). Never touches the active or pending one. */
    static int cleanOrphans(File dir, SharedPreferences sp) {
        File[] fs = dir.listFiles();
        if (fs == null) return 0;
        String a = activePath(sp);
        String q = sp.getString(P_PATH, "");
        int n = 0;
        for (int i = 0; i < fs.length; i++) {
            File f = fs[i];
            if (!f.isFile() || !f.getName().endsWith(".mp4")) continue;
            String ap = f.getAbsolutePath();
            if (ap.equals(a) || ap.equals(q)) continue;
            if (f.delete()) n++;
        }
        return n;
    }
}
