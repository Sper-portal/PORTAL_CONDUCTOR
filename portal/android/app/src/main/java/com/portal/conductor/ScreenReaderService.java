package com.portal.conductor;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.List;

public class ScreenReaderService extends AccessibilityService {
    public static ScreenReaderService instance;

    @Override protected void onServiceConnected() { instance = this; }
    @Override public boolean onUnbind(android.content.Intent i) { instance = null; return super.onUnbind(i); }
    @Override public void onAccessibilityEvent(AccessibilityEvent e) { }
    @Override public void onInterrupt() { }

    public JSONArray readAll(String ownPkg) {
        JSONArray out = new JSONArray();
        try {
            List<AccessibilityWindowInfo> ws = getWindows();
            if (ws != null) {
                for (AccessibilityWindowInfo w : ws) {
                    AccessibilityNodeInfo root = w.getRoot();
                    if (root == null) continue;
                    addWindow(out, root, ownPkg);
                }
            }
            if (out.length() == 0) {
                AccessibilityNodeInfo root = getRootInActiveWindow();
                if (root != null) addWindow(out, root, ownPkg);
            }
        } catch (Exception e) { }
        return out;
    }

    private void addWindow(JSONArray out, AccessibilityNodeInfo root, String ownPkg) throws Exception {
        String pkg = String.valueOf(root.getPackageName());
        if (pkg.equals(ownPkg) || pkg.equals("com.android.systemui")) return;
        JSONArray texts = new JSONArray();
        collect(root, texts, 0);
        JSONObject o = new JSONObject();
        o.put("pkg", pkg);
        o.put("texts", texts);
        out.put(o);
    }

    private void collect(AccessibilityNodeInfo n, JSONArray out, int depth) {
        if (n == null || depth > 80) return;
        CharSequence t = n.getText();
        CharSequence d = n.getContentDescription();
        if (t != null && t.length() > 0) out.put(t.toString());
        else if (d != null && d.length() > 0) out.put(d.toString());
        int c = n.getChildCount();
        for (int i = 0; i < c; i++) collect(n.getChild(i), out, depth + 1);
    }
}
