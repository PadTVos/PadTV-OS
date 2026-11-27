/* Standalone JNI invocation probe. Execute only inside the mandatory sandbox.
 * Uses the selected ART bundle's libart; never substitutes an OpenJDK VM. */
#include <jni.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv) {
    if(argc<2||argc>66){fputs("Expected main class and JNI VM options\n",stderr);return 64;}
    if(strlen(argv[1])>512){fputs("Class name exceeds limit\n",stderr);return 64;}
    void *sigchain=dlopen("libsigchain.so",RTLD_NOW|RTLD_GLOBAL);
    if(!sigchain){fprintf(stderr,"libsigchain: %s\n",dlerror());return 69;}
    void *library=dlopen("libart.so",RTLD_NOW|RTLD_GLOBAL);
    if(!library){fprintf(stderr,"libart: %s\n",dlerror());return 69;}
    typedef jint (*CreateVM)(JavaVM **,void **,void *);
    CreateVM create=(CreateVM)dlsym(library,"JNI_CreateJavaVM");
    if(!create){fprintf(stderr,"JNI_CreateJavaVM symbol: %s\n",dlerror());return 69;}
    JavaVMOption options[64];memset(options,0,sizeof(options));
    for(int i=2;i<argc;i++)options[i-2].optionString=argv[i];
    JavaVMInitArgs args={JNI_VERSION_1_6,argc-2,options,JNI_FALSE};JavaVM *vm=NULL;JNIEnv *env=NULL;
    jint result=create(&vm,(void **)&env,&args);
    printf("{\"JNI_CreateJavaVM_result\":%d,\"vm_created\":%s}\n",result,vm&&env?"true":"false");fflush(stdout);
    if(result!=JNI_OK||!vm||!env)return 70;
    jclass main_class=(*env)->FindClass(env,argv[1]);
    jmethodID method=main_class?(*env)->GetStaticMethodID(env,main_class,"main","([Ljava/lang/String;)V"):NULL;
    if(method&&!(*env)->ExceptionCheck(env)){
        jclass string_class=(*env)->FindClass(env,"java/lang/String");
        jobjectArray strings=string_class?(*env)->NewObjectArray(env,0,string_class,NULL):NULL;
        if(strings&&!(*env)->ExceptionCheck(env))(*env)->CallStaticVoidMethod(env,main_class,method,strings);
    }
    int failed=(*env)->ExceptionCheck(env)||!method;
    if((*env)->ExceptionCheck(env)){(*env)->ExceptionDescribe(env);(*env)->ExceptionClear(env);}
    jint destroyed=(*vm)->DestroyJavaVM(vm);
    printf("{\"DestroyJavaVM_result\":%d,\"original_main_completed\":%s}\n",destroyed,failed?"false":"true");
    return failed||destroyed!=JNI_OK?78:0;
}
