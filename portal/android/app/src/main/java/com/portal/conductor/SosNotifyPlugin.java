package com.portal.conductor;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * v3.55 · SOS completo: canales de notificacion para los avisos de ayuda de los contactos de confianza.
 *  - «sos_alarma»: suena como ALARMA (USAGE_ALARM), asi se oye aunque el movil este en silencio y pasa por «No molestar» (modo prioritario con alarmas).
 *    Tambien pide «Anular No molestar»: Android solo lo concede si el usuario lo activa en los ajustes del canal (el boton «Sonido y No molestar» lo abre).
 *  - «sos_aviso»: avisos normales (p. ej. «ya esta bien»).
 * El servidor manda los avisos con channel_id = sos_alarma: el canal tiene que existir ANTES de que llegue el primero (se crea al abrir la app).
 */
@CapacitorPlugin(name = "SosNotify")
public class SosNotifyPlugin extends Plugin {
    static final String CH_ALARM = "sos_alarma", CH_INFO = "sos_aviso";

    /** Crea los canales si no existen (si ya existen no se tocan: Android no deja cambiar el sonido de un canal ya creado). */
    static void ensure(Context ctx) {
        try {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
            NotificationManager nm = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm == null) return;
            if (nm.getNotificationChannel(CH_ALARM) == null) {
                NotificationChannel c = new NotificationChannel(CH_ALARM, "Avisos SOS (alarma)", NotificationManager.IMPORTANCE_HIGH);
                c.setDescription("Avisos de ayuda de tus contactos de confianza. Suenan como una alarma.");
                Uri snd = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
                if (snd == null) snd = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
                AudioAttributes aa = new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build();
                c.setSound(snd, aa);
                c.enableVibration(true);
                c.setVibrationPattern(new long[]{0, 600, 250, 600, 250, 900});
                c.enableLights(true);
                c.setLightColor(0xFFFF0000);
                c.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
                c.setShowBadge(true);
                c.setBypassDnd(true);
                nm.createNotificationChannel(c);
            }
            if (nm.getNotificationChannel(CH_INFO) == null) {
                NotificationChannel c = new NotificationChannel(CH_INFO, "Avisos SOS (información)", NotificationManager.IMPORTANCE_DEFAULT);
                c.setDescription("Avisos de que un contacto ya está bien.");
                c.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
                nm.createNotificationChannel(c);
            }
        } catch (Exception e) {
            // sin canal el aviso sigue llegando (con el canal por defecto de Firebase); no se rompe nada
        }
    }

    static JSObject statusOf(Context ctx) {
        JSObject r = new JSObject();
        try {
            NotificationManager nm = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            r.put("sdk", Build.VERSION.SDK_INT);
            r.put("notifications", nm != null && nm.areNotificationsEnabled());
            r.put("dndAccess", nm != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && nm.isNotificationPolicyAccessGranted());
            boolean exists = false, bypass = false, alarm = false;
            int imp = 0;
            if (nm != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                NotificationChannel c = nm.getNotificationChannel(CH_ALARM);
                if (c != null) {
                    exists = true;
                    bypass = c.canBypassDnd();
                    imp = c.getImportance();
                    AudioAttributes a = c.getAudioAttributes();
                    alarm = a != null && a.getUsage() == AudioAttributes.USAGE_ALARM && c.getSound() != null;
                }
            }
            r.put("channelExists", exists);
            r.put("bypassDnd", bypass);
            r.put("alarmSound", alarm);
            r.put("importance", imp);
        } catch (Exception e) {
            r.put("error", String.valueOf(e.getMessage()));
        }
        return r;
    }

    @PluginMethod
    public void ensureChannels(PluginCall call) {
        ensure(getContext());
        call.resolve(statusOf(getContext()));
    }

    @PluginMethod
    public void status(PluginCall call) {
        call.resolve(statusOf(getContext()));
    }

    /** what = channel (ajustes del canal de alarma: aqui se activa «Anular No molestar»), dnd (acceso a No molestar) o app (notificaciones de la app). */
    @PluginMethod
    public void openSettings(PluginCall call) {
        try {
            String what = call.getString("what", "channel");
            String pkg = getContext().getPackageName();
            Intent i;
            if ("dnd".equals(what)) {
                i = new Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS);
            } else if ("channel".equals(what) && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                ensure(getContext());
                i = new Intent(Settings.ACTION_CHANNEL_NOTIFICATION_SETTINGS);
                i.putExtra(Settings.EXTRA_APP_PACKAGE, pkg);
                i.putExtra(Settings.EXTRA_CHANNEL_ID, CH_ALARM);
            } else {
                i = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS);
                i.putExtra(Settings.EXTRA_APP_PACKAGE, pkg);
            }
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(i);
            call.resolve();
        } catch (Exception e) {
            call.reject("No se pudieron abrir los ajustes: " + e.getMessage());
        }
    }
}
