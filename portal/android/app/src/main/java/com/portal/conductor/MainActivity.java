package com.portal.conductor;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ScreenReaderPlugin.class);
        registerPlugin(GpsOdometerPlugin.class);
        registerPlugin(ShareFilePlugin.class);
        registerPlugin(TripRecorderPlugin.class);
        registerPlugin(SosNotifyPlugin.class);
        registerPlugin(SpeakPlugin.class);
        super.onCreate(savedInstanceState);
        try { SosNotifyPlugin.ensure(this); } catch (Throwable t) { /* los canales del SOS se crean tambien al activar los avisos */ }
    }
}
