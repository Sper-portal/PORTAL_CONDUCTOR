package com.portal.conductor;

import android.content.Context;
import android.media.AudioAttributes;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.util.Locale;

/**
 * v3.61 · «Botones con voz» (cinturon / gracias por viajar): dice en voz alta el texto que le pase la pagina, con la voz de texto a voz del movil.
 *  - Usa el volumen de MULTIMEDIA (el que se sube y baja con los botones del movil), para que el pasajero lo oiga.
 *  - El idioma de la voz lo elige la pagina («es-ES», «en-GB»…); si el movil no tiene esa voz, usa la del movil.
 *  - Todo va en el hilo principal. Si el motor de voz no arranca, rechaza con «sin_motor» y la pagina prueba la voz del navegador.
 */
@CapacitorPlugin(name = "Speak")
public class SpeakPlugin extends Plugin {
    private final Handler main = new Handler(Looper.getMainLooper());
    private TextToSpeech tts = null;
    private boolean ready = false;
    private PluginCall waiting = null;
    private String waitText = null, waitLang = null;
    private float waitVol = 1f;

    @PluginMethod
    public void speak(final PluginCall call) {
        String t = call.getString("text", "");
        if (t == null || t.trim().length() == 0) { call.reject("vacio"); return; }
        t = t.trim();
        if (t.length() > 400) t = t.substring(0, 400);
        final String text = t;
        String l = call.getString("lang", "es-ES");
        final String lang = (l == null || l.trim().length() == 0) ? "es-ES" : l.trim();
        Double v = call.getDouble("volume", 1.0);
        final float vol = (float) Math.max(0.1, Math.min(1.0, v == null ? 1.0 : v.doubleValue()));
        main.post(new Runnable() {
            @Override public void run() {
                try {
                    if (ready && tts != null) { say(text, lang, vol); call.resolve(ok()); return; }
                    if (waiting != null) { try { waiting.reject("otra"); } catch (Throwable e) { } }
                    waiting = call; waitText = text; waitLang = lang; waitVol = vol;
                    if (tts == null) start();
                } catch (Throwable e) { waiting = null; call.reject("error"); }
            }
        });
    }

    @PluginMethod
    public void stop(final PluginCall call) {
        main.post(new Runnable() {
            @Override public void run() {
                try { if (tts != null) tts.stop(); } catch (Throwable e) { }
                call.resolve();
            }
        });
    }

    private JSObject ok() { JSObject r = new JSObject(); r.put("ok", true); return r; }

    private void start() {
        Context c = getContext();
        if (c == null) { failWaiting(); return; }
        try {
            tts = new TextToSpeech(c.getApplicationContext(), new TextToSpeech.OnInitListener() {
                @Override public void onInit(final int status) {
                    main.post(new Runnable() {
                        @Override public void run() {
                            if (status != TextToSpeech.SUCCESS) { ready = false; tts = null; failWaiting(); return; }
                            ready = true;
                            PluginCall w = waiting; String t = waitText, l = waitLang; float v = waitVol;
                            waiting = null; waitText = null; waitLang = null;
                            if (w != null) {
                                try { say(t, l, v); w.resolve(ok()); } catch (Throwable e) { w.reject("error"); }
                            }
                        }
                    });
                }
            });
        } catch (Throwable e) { tts = null; ready = false; failWaiting(); }
    }

    private void failWaiting() {
        PluginCall w = waiting; waiting = null; waitText = null; waitLang = null;
        if (w != null) { try { w.reject("sin_motor"); } catch (Throwable e) { } }
    }

    private void say(String text, String lang, float vol) {
        try {
            int lr = tts.setLanguage(Locale.forLanguageTag(lang));
            if (lr == TextToSpeech.LANG_MISSING_DATA || lr == TextToSpeech.LANG_NOT_SUPPORTED) tts.setLanguage(Locale.getDefault());
        } catch (Throwable e) { }
        try {
            tts.setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build());
        } catch (Throwable e) { }
        Bundle b = new Bundle();
        b.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, vol);
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, b, "portal-voz");
    }
}
