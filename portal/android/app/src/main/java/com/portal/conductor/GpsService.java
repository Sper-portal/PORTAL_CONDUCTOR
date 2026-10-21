package com.portal.conductor;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ServiceInfo;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.os.Looper;

public class GpsService extends Service implements LocationListener {
    public static volatile boolean running = false;
    public static volatile long lastFix = 0;

    private LocationManager lm;
    private Location last;
    private double meters = 0;
    private SharedPreferences sp;

    @Override public IBinder onBind(Intent i) { return null; }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        sp = getSharedPreferences("portal", Context.MODE_PRIVATE);
        boolean reset = intent != null && intent.getBooleanExtra("reset", false);
        String session = intent != null ? intent.getStringExtra("session") : null;
        if (session == null) session = "";
        if (reset || (intent != null && !session.equals(sp.getString("gps_session", "")))) {
            meters = 0;
            last = null;
            sp.edit().putFloat("gps_m", 0f).putString("gps_session", session).apply();
        } else {
            meters = sp.getFloat("gps_m", 0f);
        }
        startAsForeground();
        if (!running) {
            try {
                lm = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
                lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 3000L, 5f, this, Looper.getMainLooper());
                running = true;
            } catch (SecurityException e) {
                stopSelf();
            }
        }
        return START_STICKY;
    }

    private void startAsForeground() {
        NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(new NotificationChannel("gps_odo", "Kil\u00f3metros de jornada", NotificationManager.IMPORTANCE_LOW));
        }
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, "gps_odo") : new Notification.Builder(this);
        b.setContentTitle("Portal: contando kil\u00f3metros");
        b.setContentText("Jornada en curso");
        b.setSmallIcon(android.R.drawable.ic_menu_mylocation);
        b.setOngoing(true);
        b.setContentIntent(pi);
        Notification n = b.build();
        if (Build.VERSION.SDK_INT >= 29) startForeground(77, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION);
        else startForeground(77, n);
    }

    @Override public void onLocationChanged(Location loc) {
        lastFix = System.currentTimeMillis();
        if (loc.hasAccuracy() && loc.getAccuracy() > 30f) return;
        if (last != null) {
            float d = last.distanceTo(loc);
            double dt = (loc.getTime() - last.getTime()) / 1000.0;
            if (dt > 0) {
                double v = d / dt;
                double speed = loc.hasSpeed() ? loc.getSpeed() : v;
                if (speed >= 0.7 && d >= 3f && v < 70) {
                    meters += d;
                    sp.edit().putFloat("gps_m", (float) meters).apply();
                }
            }
        }
        last = loc;
    }

    @Override public void onProviderEnabled(String p) { }
    @Override public void onProviderDisabled(String p) { }
    @Override public void onStatusChanged(String p, int s, Bundle b) { }

    @Override public void onDestroy() {
        try { if (lm != null) lm.removeUpdates(this); } catch (Exception e) { }
        running = false;
        super.onDestroy();
    }
}
