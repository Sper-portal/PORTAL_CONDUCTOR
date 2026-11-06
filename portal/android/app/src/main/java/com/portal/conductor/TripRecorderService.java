package com.portal.conductor;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.MediaRecorder;
import android.annotation.SuppressLint;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.PowerManager;
import android.os.StatFs;
import android.os.SystemClock;
import android.util.Size;
import android.view.Surface;
import java.io.File;
import java.util.Collections;

/**
 * Trip recorder (v3.42): records video (Full HD when the camera allows it) into a file in the app's private folder.
 * Started by the driver from the portal; it never records on its own and nothing is uploaded anywhere.
 * Camera2 feeds a MediaRecorder surface; no preview is shown. Runs as a foreground service (camera, optionally microphone).
 * All camera work happens on one background thread (h).
 */
public class TripRecorderService extends Service {
    public static final String ACTION_START = "com.portal.conductor.REC_START";
    public static final String ACTION_STOP = "com.portal.conductor.REC_STOP";
    static final String CHANNEL = "trip_rec";
    static final int NOTIF_ID = 78;
    static final long MAX_BYTES = 2500000000L;
    static final long MIN_FREE_BYTES = 80L * 1024L * 1024L;

    // shared with the plugin (same process)
    static volatile TripRecorderService inst;
    static volatile boolean busy = false;
    static volatile boolean recording = false;
    static volatile long startElapsed = 0L;
    static volatile long plannedMs = 0L;
    static volatile boolean withAudio = false;
    static volatile String curPath = "";

    private HandlerThread ht;
    private Handler h;
    private SharedPreferences sp;
    private CameraDevice cam;
    private CameraCaptureSession sess;
    private CaptureRequest req;
    private MediaRecorder rec;
    private PowerManager.WakeLock wl;
    private File outFile;
    private int[][] sizes = new int[][] { { 1280, 720 } };
    private int sizeIdx = 0;
    private int sensor = 90;
    private int rotation = 0;
    private int wantFacing = CameraCharacteristics.LENS_FACING_FRONT;
    private boolean wantAudio = false;
    private long planned = 0L;
    private boolean started = false;
    private boolean finishing = false;
    private long lastBeatEl = 0L;

    static File recDir(Context c) {
        File d = new File(c.getFilesDir(), "grabaciones");
        d.mkdirs();
        return d;
    }

    /** Free bytes in the folder, or -1 when it cannot be known. */
    static long freeBytes(File dir) {
        try {
            return new StatFs(dir.getAbsolutePath()).getAvailableBytes();
        } catch (Exception e) {
            return -1L;
        }
    }

    @Override public IBinder onBind(Intent i) { return null; }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent != null ? intent.getAction() : null;
        if (ACTION_STOP.equals(action)) {
            TripRecorderService s = inst;
            if (s != null) s.requestStop();
            else stopSelf();
            return START_NOT_STICKY;
        }
        if (!ACTION_START.equals(action)) {
            // restarted by the system with no request: there is nothing to record
            stopSelf();
            return START_NOT_STICKY;
        }
        if (inst != null) {
            // a recording is already running: ignore this second request (but keep the foreground promise)
            if (inst == this) {
                try { goForeground(); } catch (RuntimeException e) { }
            } else {
                stopSelf();
            }
            return START_NOT_STICKY;
        }
        sp = getSharedPreferences(TripRecorderStore.PREFS, Context.MODE_PRIVATE);
        wantAudio = intent.getBooleanExtra("audio", false) && hasPerm("android.permission.RECORD_AUDIO");
        wantFacing = "back".equals(intent.getStringExtra("camera")) ? CameraCharacteristics.LENS_FACING_BACK : CameraCharacteristics.LENS_FACING_FRONT;
        rotation = intent.getIntExtra("rotation", 0);
        planned = TripRecorderStore.clampMinutes(intent.getIntExtra("minutes", 30)) * 60000L;
        inst = this;
        busy = true;
        recording = false;
        withAudio = wantAudio;
        plannedMs = planned;
        try {
            goForeground();
        } catch (RuntimeException e) {
            failEarly("fgs");
            return START_NOT_STICKY;
        }
        if (!hasPerm("android.permission.CAMERA")) {
            failEarly("camera_denied");
            return START_NOT_STICKY;
        }
        ht = new HandlerThread("TripRec");
        ht.start();
        h = new Handler(ht.getLooper());
        h.post(new Runnable() { @Override public void run() { begin(); } });
        return START_NOT_STICKY;
    }

    private boolean hasPerm(String p) {
        return checkSelfPermission(p) == PackageManager.PERMISSION_GRANTED;
    }

    // ------------------------------------------------------------------ foreground notification

    private Notification buildNotif(long remainingMs, boolean countdown) {
        NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(new NotificationChannel(CHANNEL, "Grabación de viaje", NotificationManager.IMPORTANCE_LOW));
        }
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Intent stop = new Intent(this, TripRecorderService.class);
        stop.setAction(ACTION_STOP);
        PendingIntent ps = PendingIntent.getService(this, 1, stop, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        b.setContentTitle("Portal: grabando el viaje");
        b.setContentText(wantAudio ? "Con audio. Toca para abrir." : "Sin audio. Toca para abrir.");
        b.setSmallIcon(android.R.drawable.ic_menu_camera);
        b.setOngoing(true);
        b.setContentIntent(pi);
        b.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Parar", ps);
        if (countdown) {
            b.setWhen(System.currentTimeMillis() + Math.max(0L, remainingMs));
            b.setUsesChronometer(true);
            b.setChronometerCountDown(true);
        }
        return b.build();
    }

    private void goForeground() {
        Notification n = buildNotif(0L, false);
        if (Build.VERSION.SDK_INT >= 30) {
            int t = ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA | (wantAudio ? ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE : 0);
            startForeground(NOTIF_ID, n, t);
        } else {
            startForeground(NOTIF_ID, n);
        }
    }

    private void refreshNotif() {
        try {
            long left = planned - (SystemClock.elapsedRealtime() - startElapsed);
            NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            nm.notify(NOTIF_ID, buildNotif(left, true));
        } catch (Exception e) {
            // the notification is only informative
        }
    }

    // ------------------------------------------------------------------ opening the camera

    @SuppressLint("MissingPermission")
    private void begin() {
        try {
            acquireWake();
            sp = getSharedPreferences(TripRecorderStore.PREFS, Context.MODE_PRIVATE);
            File dir = recDir(this);
            long free = freeBytes(dir);
            if (free >= 0 && free < MIN_FREE_BYTES) {
                finish("space");
                return;
            }
            outFile = new File(dir, TripRecorderStore.fileName(System.currentTimeMillis()));
            CameraManager cm = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
            String camId = null;
            String anyId = null;
            String[] ids = cm.getCameraIdList();
            for (int i = 0; i < ids.length; i++) {
                CameraCharacteristics ch = cm.getCameraCharacteristics(ids[i]);
                Integer facing = ch.get(CameraCharacteristics.LENS_FACING);
                if (anyId == null) anyId = ids[i];
                if (facing != null && facing.intValue() == wantFacing) {
                    camId = ids[i];
                    break;
                }
            }
            if (camId == null) camId = anyId;
            if (camId == null) {
                finish("no_camera");
                return;
            }
            CameraCharacteristics cc = cm.getCameraCharacteristics(camId);
            Integer so = cc.get(CameraCharacteristics.SENSOR_ORIENTATION);
            sensor = so != null ? so.intValue() : 90;
            StreamConfigurationMap map = cc.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            Size[] ss = map != null ? map.getOutputSizes(MediaRecorder.class) : null;
            int n = ss != null ? ss.length : 0;
            int[] ws = new int[n];
            int[] hs = new int[n];
            for (int i = 0; i < n; i++) {
                ws[i] = ss[i].getWidth();
                hs[i] = ss[i].getHeight();
            }
            sizes = TripRecorderStore.candidates(ws, hs);
            sizeIdx = 0;
            cm.openCamera(camId, camCb, h);
        } catch (Exception e) {
            finish("no_camera");
        }
    }

    private final CameraDevice.StateCallback camCb = new CameraDevice.StateCallback() {
        @Override public void onOpened(CameraDevice c) {
            cam = c;
            if (finishing) {
                try { c.close(); } catch (Exception e) { }
                return;
            }
            startSession();
        }
        @Override public void onDisconnected(CameraDevice c) {
            cam = c;
            finish("cam_lost");
        }
        @Override public void onError(CameraDevice c, int error) {
            cam = c;
            finish(error == CameraDevice.StateCallback.ERROR_CAMERA_IN_USE ? "cam_busy" : "cam_error");
        }
    };

    private final CameraCaptureSession.StateCallback sessCb = new CameraCaptureSession.StateCallback() {
        @Override public void onConfigured(CameraCaptureSession s) {
            if (finishing) {
                try { s.close(); } catch (Exception e) { }
                return;
            }
            sess = s;
            try {
                s.setRepeatingRequest(req, null, h);
                rec.start();
                onStarted();
            } catch (Exception e) {
                retryOrFail("start");
            }
        }
        @Override public void onConfigureFailed(CameraCaptureSession s) {
            retryOrFail("config");
        }
    };

    private void startSession() {
        if (finishing || cam == null) return;
        try {
            int[] sz = sizes[sizeIdx];
            prepareRecorder(sz[0], sz[1]);
            Surface surf = rec.getSurface();
            CaptureRequest.Builder rb = cam.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
            rb.addTarget(surf);
            req = rb.build();
            cam.createCaptureSession(Collections.singletonList(surf), sessCb, h);
        } catch (Exception e) {
            retryOrFail("session");
        }
    }

    private void prepareRecorder(int w, int hgt) throws java.io.IOException {
        rec = Build.VERSION.SDK_INT >= 31 ? new MediaRecorder(this) : new MediaRecorder();
        if (wantAudio) rec.setAudioSource(MediaRecorder.AudioSource.MIC);
        rec.setVideoSource(MediaRecorder.VideoSource.SURFACE);
        rec.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
        rec.setOutputFile(outFile.getAbsolutePath());
        rec.setVideoEncodingBitRate(TripRecorderStore.videoBitrate(w, hgt));
        rec.setVideoFrameRate(30);
        rec.setVideoSize(w, hgt);
        rec.setVideoEncoder(MediaRecorder.VideoEncoder.H264);
        if (wantAudio) {
            rec.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            rec.setAudioEncodingBitRate(TripRecorderStore.AUDIO_BITRATE);
            rec.setAudioSamplingRate(44100);
        }
        rec.setOrientationHint(TripRecorderStore.orientationHint(sensor, rotation));
        rec.setMaxDuration((int) planned);
        rec.setMaxFileSize(MAX_BYTES);
        rec.setOnInfoListener(new MediaRecorder.OnInfoListener() {
            @Override public void onInfo(MediaRecorder mr, int what, int extra) {
                if (what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED || what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_FILESIZE_REACHED) {
                    h.post(new Runnable() { @Override public void run() { finish(null); } });
                }
            }
        });
        rec.setOnErrorListener(new MediaRecorder.OnErrorListener() {
            @Override public void onError(MediaRecorder mr, int what, int extra) {
                h.post(new Runnable() { @Override public void run() { finish("rec_error"); } });
            }
        });
        rec.prepare();
    }

    /** The first attempt failed before recording: try the next smaller size, else give up. */
    private void retryOrFail(String reason) {
        if (finishing) return;
        if (!started && sizeIdx + 1 < sizes.length) {
            sizeIdx++;
            dropSessionAndRecorder();
            if (outFile != null) outFile.delete();
            startSession();
        } else {
            finish(reason);
        }
    }

    private void dropSessionAndRecorder() {
        if (sess != null) {
            try { sess.close(); } catch (Exception e) { }
            sess = null;
        }
        if (rec != null) {
            try { rec.reset(); } catch (Exception e) { }
            try { rec.release(); } catch (Exception e) { }
            rec = null;
        }
    }

    // ------------------------------------------------------------------ recording

    private void onStarted() {
        started = true;
        startElapsed = SystemClock.elapsedRealtime();
        curPath = outFile.getAbsolutePath();
        lastBeatEl = 0L;
        TripRecorderStore.markActive(sp, curPath, System.currentTimeMillis(), planned, wantAudio);
        recording = true;
        refreshNotif();
        h.postDelayed(tick, 1000L);
    }

    private final Runnable tick = new Runnable() {
        @Override public void run() {
            if (finishing) return;
            long el = SystemClock.elapsedRealtime() - startElapsed;
            if (el >= planned + 1500L) {
                finish(null);
                return;
            }
            if (el - lastBeatEl >= 15000L) {
                lastBeatEl = el;
                TripRecorderStore.beat(sp, el);
                long free = freeBytes(outFile.getParentFile());
                if (free >= 0 && free < MIN_FREE_BYTES) {
                    finish("space");
                    return;
                }
            }
            h.postDelayed(this, 1000L);
        }
    };

    void requestStop() {
        Handler hh = h;
        if (hh == null) {
            stopSelf();
            return;
        }
        hh.post(new Runnable() { @Override public void run() { finish(null); } });
    }

    private void acquireWake() {
        try {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "portal:triprec");
            wl.setReferenceCounted(false);
            wl.acquire(planned + 120000L);
        } catch (Exception e) {
            wl = null;
        }
    }

    private void releaseWake() {
        try {
            if (wl != null && wl.isHeld()) wl.release();
        } catch (Exception e) {
            // nothing to do
        }
        wl = null;
    }

    /**
     * Ends the recording (normal stop when err is null, otherwise because of that error), keeps the file when it is useful
     * and leaves it as the pending recording. Safe to call more than once.
     */
    private void finish(String err) {
        if (finishing) return;
        finishing = true;
        if (h != null) h.removeCallbacks(tick);
        long durMs = started ? Math.min(SystemClock.elapsedRealtime() - startElapsed, planned) : 0L;
        boolean stopOk = true;
        if (sess != null) {
            try { sess.stopRepeating(); } catch (Exception e) { }
            try { sess.abortCaptures(); } catch (Exception e) { }
        }
        if (rec != null) {
            if (started) {
                try { rec.stop(); } catch (Exception e) { stopOk = false; }
            }
            try { rec.reset(); } catch (Exception e) { }
            try { rec.release(); } catch (Exception e) { }
            rec = null;
        }
        if (sess != null) {
            try { sess.close(); } catch (Exception e) { }
            sess = null;
        }
        if (cam != null) {
            try { cam.close(); } catch (Exception e) { }
            cam = null;
        }
        recording = false;
        long now = System.currentTimeMillis();
        File f = outFile;
        if (sp == null) sp = getSharedPreferences(TripRecorderStore.PREFS, Context.MODE_PRIVATE);
        boolean usable = started && f != null && f.isFile() && f.length() >= TripRecorderStore.MIN_USABLE_BYTES;
        if (usable) {
            TripRecorderStore.setPending(sp, f, durMs, wantAudio, !stopOk, err == null ? "" : err, now);
        } else {
            if (f != null && f.isFile()) f.delete();
            TripRecorderStore.clearActive(sp);
            TripRecorderStore.setError(sp, err == null ? "short" : err, now);
        }
        releaseWake();
        curPath = "";
        busy = false;
        inst = null;
        try { stopForeground(Service.STOP_FOREGROUND_REMOVE); } catch (Exception e) { }
        stopSelf();
        if (ht != null) ht.quitSafely();
    }

    /** Failure before the worker thread exists. */
    private void failEarly(String code) {
        finishing = true;
        busy = false;
        recording = false;
        inst = null;
        if (sp == null) sp = getSharedPreferences(TripRecorderStore.PREFS, Context.MODE_PRIVATE);
        TripRecorderStore.setError(sp, code, System.currentTimeMillis());
        try { stopForeground(Service.STOP_FOREGROUND_REMOVE); } catch (Exception e) { }
        stopSelf();
    }

    @Override public void onDestroy() {
        if (!finishing && (cam != null || rec != null)) {
            finish("destroyed");
        }
        if (inst == this) {
            inst = null;
            busy = false;
            recording = false;
        }
        releaseWake();
        super.onDestroy();
    }
}
