package org.padtv.bridge;
/** Observed in-process diagnostics; application output is not a security attestation. */
public final class Startup {
    private static String phase="vm.entry";
    public static void phase(String name){phase=name;System.err.println("PADBRIDGE_PHASE="+name);}
    public static void failure(Throwable error){System.err.println("PADBRIDGE_FAILED_PHASE="+phase);}
}
