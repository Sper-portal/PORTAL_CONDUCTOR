package com.portal.conductor;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ScreenReaderPlugin.class);
        registerPlugin(GpsOdometerPlugin.class);
        registerPlugin(ShareFilePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
