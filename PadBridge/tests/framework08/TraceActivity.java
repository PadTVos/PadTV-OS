package org.padtv.frameworkprobe;
public final class TraceActivity extends android.app.Activity {
    protected void onCreate(android.os.Bundle state){super.onCreate(state);
        if(android.os.Trace.isEnabled())throw new AssertionError("Tracing must be opt in");System.setProperty("padbridge.trace","true");
        android.os.Trace.beginSection("Original 📺");android.os.Trace.setCounter("frames",42);android.os.Trace.endSection();
        android.os.Trace.beginAsyncSection("decode",123);android.os.Trace.endAsyncSection("decode",123);
        try{android.os.Trace.endSection();throw new AssertionError("Unbalanced trace accepted");}catch(IllegalStateException expected){}
        System.setProperty("padbridge.trace","false");System.out.println("ORIGINAL_PRIVATE_TRACE_WRITTEN_OK");
    }
}
