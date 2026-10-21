package com.portal.conductor;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.provider.Settings;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import org.json.JSONObject;

@CapacitorPlugin(name = "ScreenReader")
public class ScreenReaderPlugin extends Plugin {

    @PluginMethod
    public void status(PluginCall call) {
        JSObject r = new JSObject();
        r.put("enabled", ScreenReaderService.instance != null);
        call.resolve(r);
    }

    @PluginMethod
    public void openSettings(PluginCall call) {
        Intent i = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(i);
        call.resolve();
    }

    @PluginMethod
    public void openAppInfo(PluginCall call) {
        Intent i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getContext().getPackageName()));
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(i);
        call.resolve();
    }

    @PluginMethod
    public void read(PluginCall call) {
        ScreenReaderService s = ScreenReaderService.instance;
        if (s == null) { call.reject("not_enabled"); return; }
        JSObject r = new JSObject();
        r.put("windows", s.readAll(getContext().getPackageName()));
        call.resolve(r);
    }

    @PluginMethod
    public void takePending(PluginCall call) {
        JSObject r = new JSObject();
        String p = ScreenReaderService.pendingJson;
        if (p == null) {
            r.put("has", false);
        } else {
            ScreenReaderService.pendingJson = null;
            try {
                JSONObject o = new JSONObject(p);
                r.put("has", true);
                r.put("amount", o.getDouble("amount"));
                r.put("label", o.optString("label"));
                r.put("hint", o.optString("hint"));
            } catch (Exception e) {
                r.put("has", false);
            }
        }
        call.resolve(r);
    }

    @PluginMethod
    public void getBubble(PluginCall call) {
        JSObject r = new JSObject();
        r.put("enabled", ScreenReaderService.bubbleOn(getContext()));
        call.resolve(r);
    }

    @PluginMethod
    public void setBubble(PluginCall call) {
        boolean en = call.getBoolean("enabled", true);
        getContext().getSharedPreferences("portal", Context.MODE_PRIVATE).edit().putInt("bubble", en ? 1 : 0).apply();
        ScreenReaderService s = ScreenReaderService.instance;
        if (s != null) s.postRefresh();
        call.resolve();
    }
}
