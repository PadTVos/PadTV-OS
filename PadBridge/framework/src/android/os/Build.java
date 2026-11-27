package android.os;

/** PadBridge compatibility-profile metadata, not an Android device attestation.
 * SDK_INT selects Android 14 API behaviour; individual API availability remains
 * an explicitly incomplete subset. Never impersonate a certified device.
 */
public final class Build {
    private Build() {}
    public static final String UNKNOWN="unknown";
    public static final String ID="PadBridge",DISPLAY="PadBridge 0.5 experimental",
        PRODUCT="PadTV",DEVICE="linux",BOARD=UNKNOWN,MANUFACTURER="PadTV",
        BRAND="PadTV",MODEL="PadBridge on Linux",BOOTLOADER=UNKNOWN,
        HARDWARE="x86_64",FINGERPRINT=UNKNOWN,SERIAL=UNKNOWN,
        TYPE="userdebug",TAGS="experimental",HOST=UNKNOWN,USER=UNKNOWN,
        CPU_ABI="x86_64",CPU_ABI2="";
    public static final String[] SUPPORTED_ABIS={"x86_64"},SUPPORTED_64_BIT_ABIS={"x86_64"},SUPPORTED_32_BIT_ABIS={};
    public static String getSerial(){throw new SecurityException("PadBridge does not expose host hardware identifiers");}
    public static final class VERSION {
        private VERSION() {}
        public static final int SDK_INT=34,PREVIEW_SDK_INT=0;
        public static final String SDK="34",CODENAME="REL",RELEASE="PadBridge 0.5",INCREMENTAL="0.5.0",SECURITY_PATCH="";
    }
}
