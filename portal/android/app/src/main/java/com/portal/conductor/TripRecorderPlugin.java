package com.portal.conductor;

import android.Manifest;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.SystemClock;
import android.provider.MediaStore;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Bridge between the portal (JavaScript) and the trip recorder service (v3.42).
 * start({minutes, audio, camera}) -> {ok, reason?}   stop()   status()   save()   discard()   ackError()
 * The video stays on the phone: save() copies it to Movies/Portal del Conductor, nothing is uploaded.
 */
@CapacitorPlugin(
    name = "TripRecorder",
    permissions = {
        @Permission(alias = "camera", strings = { Manifest.permission.CAMERA }),
        @Permission(alias = "mic", strings = { Manifest.permission.RECORD_AUDIO }),
        @Permission(alias = "notifications", strings = { "android.permission.POST_NOTIFICATIONS" })
    }
)
public class TripRecorderPlugin extends Plugin {

    private SharedPreferences prefs() {
        return getContext().getSharedPreferences(TripRecorderStore.PREFS, Context.MODE_PRIVATE);
    }

    private void refuse(PluginCall call, String reason) {
        JSObject r = new JSObject();
        r.put("ok", false);
        r.put("reason", reason);
        call.resolve(r);
    }

    private void sync() {
        TripRecorderStore.reconcile(prefs(), TripRecorderService.inst != null, System.currentTimeMillis());
    }

    // ------------------------------------------------------------------ start (permissions first)

    @PluginMethod
    public void start(PluginCall call) {
        sync();
        if (TripRecorderService.busy) { refuse(call, "busy"); return; }
        if (TripRecorderStore.readPending(prefs()) != null) { refuse(call, "pending"); return; }
        TripRecorderStore.clearError(prefs());
        if (getPermissionState("camera") != PermissionState.GRANTED) {
            requestPermissionForAlias("camera", call, "camCb");
            return;
        }
        afterCamera(call);
    }

    @PermissionCallback
    private void camCb(PluginCall call) {
        if (getPermissionState("camera") == PermissionState.GRANTED) afterCamera(call);
        else refuse(call, "camera_denied");
    }

    private void afterCamera(PluginCall call) {
        boolean audio = call.getBoolean("audio", false);
        if (audio && getPermissionState("mic") != PermissionState.GRANTED) {
            requestPermissionForAlias("mic", call, "micCb");
            return;
        }
        afterMic(call);
    }

    @PermissionCallback
    private void micCb(PluginCall call) {
        if (getPermissionState("mic") == PermissionState.GRANTED) afterMic(call);
        else refuse(call, "mic_denied");
    }

    private void afterMic(PluginCall call) {
        if (Build.VERSION.SDK_INT >= 33 && getPermissionState("notifications") != PermissionState.GRANTED) {
            requestPermissionForAlias("notifications", call, "notifCb");
            return;
        }
        begin(call);
    }

    @PermissionCallback
    private void notifCb(PluginCall call) {
        // without the notification permission the recording still works (the system still lists the service)
        begin(call);
    }

    private int displayRotation() {
        try {
            if (Build.VERSION.SDK_INT >= 30) return getActivity().getDisplay().getRotation();
            return getActivity().getWindowManager().getDefaultDisplay().getRotation();
        } catch (Exception e) {
            return 0;
        }
    }

    private void begin(PluginCall call) {
        int minutes = TripRecorderStore.clampMinutes(call.getInt("minutes", 30));
        boolean audio = call.getBoolean("audio", false);
        String camera = "back".equals(call.getString("camera", "front")) ? "back" : "front";
        long ms = minutes * 60000L;
        File dir = TripRecorderService.recDir(getContext());
        TripRecorderStore.cleanOrphans(dir, prefs());
        long need = TripRecorderStore.estimateBytes(TripRecorderStore.videoBitrate(1920, 1080), audio, ms) + 300L * 1024L * 1024L;
        long free = TripRecorderService.freeBytes(dir);
        if (free >= 0 && free < need) {
            JSObject r = new JSObject();
            r.put("ok", false);
            r.put("reason", "space");
            r.put("freeBytes", free);
            r.put("needBytes", need);
            call.resolve(r);
            return;
        }
        Intent i = new Intent(getContext(), TripRecorderService.class);
        i.setAction(TripRecorderService.ACTION_START);
        i.putExtra("minutes", minutes);
        i.putExtra("audio", audio);
        i.putExtra("camera", camera);
        i.putExtra("rotation", displayRotation());
        TripRecorderService.busy = true;
        try {
            if (Build.VERSION.SDK_INT >= 26) getContext().startForegroundService(i);
            else getContext().startService(i);
            JSObject r = new JSObject();
            r.put("ok", true);
            r.put("plannedMs", ms);
            call.resolve(r);
        } catch (Exception e) {
            TripRecorderService.busy = false;
            refuse(call, "fgs");
        }
    }

    // ------------------------------------------------------------------ stop / status

    @PluginMethod
    public void stop(PluginCall call) {
        TripRecorderService s = TripRecorderService.inst;
        if (s != null) s.requestStop();
        JSObject r = new JSObject();
        r.put("ok", true);
        call.resolve(r);
    }

    @PluginMethod
    public void status(PluginCall call) {
        sync();
        SharedPreferences sp = prefs();
        JSObject r = new JSObject();
        if (TripRecorderService.recording) {
            long el = Math.max(0L, SystemClock.elapsedRealtime() - TripRecorderService.startElapsed);
            long planned = TripRecorderService.plannedMs;
            r.put("state", "recording");
            r.put("elapsedMs", el);
            r.put("plannedMs", planned);
            r.put("remainingMs", Math.max(0L, planned - el));
            r.put("audio", TripRecorderService.withAudio);
            String cp = TripRecorderService.curPath;
            r.put("sizeBytes", cp.length() > 0 ? new File(cp).length() : 0L);
        } else if (TripRecorderService.busy) {
            r.put("state", "starting");
            r.put("plannedMs", TripRecorderService.plannedMs);
        } else {
            TripRecorderStore.Pending p = TripRecorderStore.readPending(sp);
            if (p != null) {
                r.put("state", "pending");
                JSObject o = new JSObject();
                o.put("durationMs", p.durationMs);
                o.put("sizeBytes", p.sizeBytes);
                o.put("audio", p.audio);
                o.put("at", p.at);
                o.put("cut", p.cut);
                o.put("why", p.why);
                r.put("pending", o);
            } else {
                r.put("state", "idle");
            }
        }
        String err = TripRecorderStore.readError(sp);
        if (err.length() > 0) {
            r.put("error", err);
            r.put("errorAt", TripRecorderStore.readErrorAt(sp));
        }
        call.resolve(r);
    }

    @PluginMethod
    public void ackError(PluginCall call) {
        TripRecorderStore.clearError(prefs());
        JSObject r = new JSObject();
        r.put("ok", true);
        call.resolve(r);
    }

    // ------------------------------------------------------------------ save / discard

    @PluginMethod
    public void discard(PluginCall call) {
        sync();
        if (TripRecorderService.busy) { refuse(call, "busy"); return; }
        TripRecorderStore.discardPending(prefs());
        JSObject r = new JSObject();
        r.put("ok", true);
        call.resolve(r);
    }

    @PluginMethod
    public void save(final PluginCall call) {
        sync();
        if (TripRecorderService.busy) { refuse(call, "busy"); return; }
        final SharedPreferences sp = prefs();
        final TripRecorderStore.Pending p = TripRecorderStore.readPending(sp);
        if (p == null) { refuse(call, "nothing"); return; }
        if (Build.VERSION.SDK_INT < 29) { refuse(call, "old_android"); return; }
        final File dir = new File(p.path).getParentFile();
        long free = TripRecorderService.freeBytes(dir);
        if (free >= 0 && free < p.sizeBytes + 100L * 1024L * 1024L) {
            JSObject r = new JSObject();
            r.put("ok", false);
            r.put("reason", "space");
            r.put("freeBytes", free);
            r.put("needBytes", p.sizeBytes + 100L * 1024L * 1024L);
            call.resolve(r);
            return;
        }
        final Context ctx = getContext();
        Thread t = new Thread(new Runnable() {
            @Override public void run() {
                JSObject r = new JSObject();
                Uri uri = null;
                try {
                    File src = new File(p.path);
                    String name = src.getName();
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
                    v.put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4");
                    v.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_MOVIES + "/Portal del Conductor");
                    v.put(MediaStore.MediaColumns.IS_PENDING, 1);
                    uri = ctx.getContentResolver().insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, v);
                    if (uri == null) throw new java.io.IOException("insert");
                    OutputStream os = ctx.getContentResolver().openOutputStream(uri);
                    if (os == null) throw new java.io.IOException("open");
                    InputStream in = new FileInputStream(src);
                    try {
                        byte[] buf = new byte[1 << 20];
                        int n;
                        while ((n = in.read(buf)) > 0) os.write(buf, 0, n);
                        os.flush();
                    } finally {
                        try { in.close(); } catch (Exception e) { }
                        try { os.close(); } catch (Exception e) { }
                    }
                    ContentValues done = new ContentValues();
                    done.put(MediaStore.MediaColumns.IS_PENDING, 0);
                    ctx.getContentResolver().update(uri, done, null, null);
                    long size = p.sizeBytes;
                    src.delete();
                    TripRecorderStore.forgetPending(sp);
                    r.put("ok", true);
                    r.put("name", name);
                    r.put("folder", "Movies/Portal del Conductor");
                    r.put("sizeBytes", size);
                } catch (Exception e) {
                    if (uri != null) {
                        try { ctx.getContentResolver().delete(uri, null, null); } catch (Exception e2) { }
                    }
                    r = new JSObject();
                    r.put("ok", false);
                    r.put("reason", "copy");
                }
                call.resolve(r);
            }
        });
        t.start();
    }
}
