package org.padtv.frameworkprobe;
public final class BuildActivity extends android.app.Activity {
    protected void onCreate(android.os.Bundle state){super.onCreate(state);
        if(!android.os.Build.MANUFACTURER.equals("PadTV")||!android.os.Build.MODEL.contains("Linux"))throw new AssertionError("Host identity");
        if(!android.os.Build.FINGERPRINT.equals(android.os.Build.UNKNOWN)||!android.os.Build.VERSION.SECURITY_PATCH.isEmpty())throw new AssertionError("False certification/patch claim");
        if(android.os.Build.SUPPORTED_32_BIT_ABIS.length!=0||!android.os.Build.SUPPORTED_ABIS[0].equals("x86_64"))throw new AssertionError("Unsupported ABI advertised");
        try{android.os.Build.getSerial();throw new AssertionError("Hardware identifier exposed");}catch(SecurityException expected){}
        System.out.println("PADBRIDGE_BUILD_IDENTITY_NO_DEVICE_ATTESTATION_OK");
    }
}
