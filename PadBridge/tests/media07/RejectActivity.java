package org.padtv.rejectprobe;
public class RejectActivity extends android.app.Activity {
 protected void onCreate(android.os.Bundle b){super.onCreate(b);try{System.loadLibrary("hostbad");throw new AssertionError("Unsupported host library loaded");}catch(UnsatisfiedLinkError expected){System.out.println("UNSUPPORTED_NATIVE_LOAD_REJECTED");}}
}
