/* Freestanding Android-target ELF. No libc, TLS, or host helper dependencies. */
#include <jni.h>
static int loaded;
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *vm, void *reserved) {
    (void)vm; (void)reserved; loaded=1;return JNI_VERSION_1_6;
}
JNIEXPORT jint JNICALL Java_org_padtv_nativeprobe_NativeActivity_multiply(JNIEnv *env,jclass cls,jint a,jint b) {
    (void)env;(void)cls;return loaded ? a*b : -1;
}
static long open_readonly(const char *path) {
    long value;
    __asm__ volatile("syscall" : "=a"(value) : "a"(2L),"D"(path),"S"(0L),"d"(0L) : "rcx","r11","memory");
    return value;
}
JNIEXPORT jstring JNICALL Java_org_padtv_nativeprobe_NativeActivity_isolation(JNIEnv *env,jclass cls) {
    (void)cls;
    int hidden=open_readonly("/tmp/padbridge-native-host-secret")<0
        && open_readonly("/etc/shadow")<0
        && open_readonly("/home/padtv/.local/share/padbridge/data/other.app/files/secret")<0;
    return (*env)->NewStringUTF(env,hidden?"NATIVE_HOST_PATHS_HIDDEN_OK":"ISOLATION_FAILED");
}
