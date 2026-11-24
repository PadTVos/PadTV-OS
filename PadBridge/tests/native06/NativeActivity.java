package org.padtv.nativeprobe;
public class NativeActivity extends android.app.Activity {
    static { System.loadLibrary("nativeprobe"); }
    private static native int multiply(int a,int b);
    private static native String isolation();
    private void dormantApi() { getPreferences(0); }
    protected void onCreate(android.os.Bundle saved) {
        super.onCreate(saved);
        if(multiply(6,7)!=42)throw new AssertionError("Native code did not execute");
        String result=isolation();
        if(!"NATIVE_HOST_PATHS_HIDDEN_OK".equals(result))throw new AssertionError(result);
        android.widget.TextView label=new android.widget.TextView(this);
        label.setText("Native JNI: 42");setContentView(label);
        System.out.println("ORIGINAL_DEX_NATIVE_X86_64_JNI_OK "+result);
    }
}
