package com.portal.conductor;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ScreenReaderPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
