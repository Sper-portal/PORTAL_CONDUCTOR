package com.portal.conductor;

import android.content.ContentValues;
import android.content.Intent;
import android.os.Environment;
import android.provider.MediaStore;
import com.getcapacitor.JSObject;
import java.io.OutputStream;
import android.net.Uri;
import android.util.Base64;
import androidx.core.content.FileProvider;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;

@CapacitorPlugin(name = "ShareFile")
public class ShareFilePlugin extends Plugin {
    @PluginMethod
    public void shareFile(PluginCall call) {
        try {
            String b64 = call.getString("base64");
            String name = call.getString("filename", "informe.pdf");
            String mime = call.getString("mime", "application/pdf");
            String title = call.getString("title", "Compartir");
            if (b64 == null) { call.reject("Sin datos"); return; }
            name = name.replaceAll("[^A-Za-z0-9._-]", "_");
            File dir = new File(getContext().getCacheDir(), "shared");
            dir.mkdirs();
            File f = new File(dir, name);
            FileOutputStream o = new FileOutputStream(f);
            o.write(Base64.decode(b64, Base64.DEFAULT));
            o.close();
            Uri uri = FileProvider.getUriForFile(getContext(), getContext().getPackageName() + ".shareprovider", f);
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType(mime);
            i.putExtra(Intent.EXTRA_STREAM, uri);
            i.putExtra(Intent.EXTRA_SUBJECT, title);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            Intent ch = Intent.createChooser(i, title);
            ch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(ch);
            call.resolve();
        } catch (Exception e) {
            call.reject("No se pudo compartir: " + e.getMessage());
        }
    }

    @PluginMethod
    public void saveFile(PluginCall call) {
        try {
            String b64 = call.getString("base64");
            String name = call.getString("filename", "archivo");
            String mime = call.getString("mime", "application/octet-stream");
            if (b64 == null) { call.reject("Sin datos"); return; }
            if (android.os.Build.VERSION.SDK_INT < 29) { call.reject("Android antiguo"); return; }
            name = name.replaceAll("[^A-Za-z0-9._-]", "_");
            ContentValues v = new ContentValues();
            v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
            v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
            v.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/Portal del Conductor");
            Uri uri = getContext().getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
            if (uri == null) { call.reject("No se pudo crear el archivo"); return; }
            OutputStream o = getContext().getContentResolver().openOutputStream(uri);
            o.write(Base64.decode(b64, Base64.DEFAULT));
            o.close();
            JSObject r = new JSObject();
            r.put("path", "Descargas/Portal del Conductor/" + name);
            call.resolve(r);
        } catch (Exception e) {
            call.reject("No se pudo guardar: " + e.getMessage());
        }
    }

    @PluginMethod
    public void openUrl(PluginCall call) {
        try {
            String u = call.getString("url");
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(u));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(i);
            call.resolve();
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }
}
