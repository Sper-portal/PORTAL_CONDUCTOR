package com.portal.conductor;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

@CapacitorPlugin(
    name = "GpsOdometer",
    permissions = {
        @Permission(alias = "location", strings = { Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION }),
        @Permission(alias = "notifications", strings = { "android.permission.POST_NOTIFICATIONS" })
    }
)
public class GpsOdometerPlugin extends Plugin {

    @PluginMethod
    public void start(PluginCall call) {
        if (getPermissionState("location") != PermissionState.GRANTED) {
            requestPermissionForAlias("location", call, "locCb");
            return;
        }
        afterLocation(call);
    }

    @PermissionCallback
    private void locCb(PluginCall call) {
        if (getPermissionState("location") == PermissionState.GRANTED) {
            afterLocation(call);
        } else {
            JSObject r = new JSObject();
            r.put("ok", false);
            r.put("reason", "denied");
            call.resolve(r);
        }
    }

    private void afterLocation(PluginCall call) {
        if (Build.VERSION.SDK_INT >= 33 && getPermissionState("notifications") != PermissionState.GRANTED) {
            requestPermissionForAlias("notifications", call, "notifCb");
            return;
        }
        begin(call);
    }

    @PermissionCallback
    private void notifCb(PluginCall call) {
        begin(call);
    }

    private void begin(PluginCall call) {
        boolean reset = call.getBoolean("reset", true);
        String session = call.getString("session", "");
        Intent i = new Intent(getContext(), GpsService.class);
        i.putExtra("reset", reset);
        i.putExtra("session", session);
        try {
            if (Build.VERSION.SDK_INT >= 26) getContext().startForegroundService(i);
            else getContext().startService(i);
            JSObject r = new JSObject();
            r.put("ok", true);
            call.resolve(r);
        } catch (Exception e) {
            JSObject r = new JSObject();
            r.put("ok", false);
            r.put("reason", "error");
            call.resolve(r);
        }
    }

    @PluginMethod
    public void stop(PluginCall call) {
        float m = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).getFloat("gps_m", 0f);
        getContext().stopService(new Intent(getContext(), GpsService.class));
        JSObject r = new JSObject();
        r.put("meters", (double) m);
        call.resolve(r);
    }

    @PluginMethod
    public void status(PluginCall call) {
        float m = getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).getFloat("gps_m", 0f);
        JSObject r = new JSObject();
        r.put("active", GpsService.running);
        r.put("meters", (double) m);
        long age = GpsService.lastFix == 0 ? -1 : (System.currentTimeMillis() - GpsService.lastFix) / 1000;
        r.put("fixAgeSec", (double) age);
        call.resolve(r);
    }
}
