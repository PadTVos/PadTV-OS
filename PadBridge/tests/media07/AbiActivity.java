package org.padtv.abiprobe;
public class AbiActivity extends android.app.Activity {
 static {System.loadLibrary("abiprobe");}
 private static native String roundtrip();
 protected void onCreate(android.os.Bundle b){super.onCreate(b);String value=roundtrip();if(!value.equals("JNI_REGISTER_MEMORY_ABI_OK"))throw new AssertionError(value);System.out.println(value);}
}
