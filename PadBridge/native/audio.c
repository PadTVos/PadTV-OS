/* Output-only IPC. No PulseAudio, PipeWire or microphone socket enters the APK. */
#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/time.h>
#define JNI(n) Java_org_padtv_bridge_MediaNative_##n
static void failure(JNIEnv *e,const char *m){if(!(*e)->ExceptionCheck(e))(*e)->ThrowNew(e,(*e)->FindClass(e,"java/lang/IllegalStateException"),m);}
static int transfer(int fd,void *data,size_t n,int write_data){char *p=data;while(n){ssize_t count=write_data?send(fd,p,n,MSG_NOSIGNAL):recv(fd,p,n,0);if(count<=0)return -1;p+=count;n-=count;}return 0;}
static jlong request(JNIEnv *e,uint32_t op,jlong handle,int a,int b,const void *data,uint32_t n){
 const char *path=getenv("PADBRIDGE_AUDIO_SOCKET");if(!path){failure(e,"Playback broker is unavailable");return -1;}
 if(handle<0||handle>UINT32_MAX||n>4*1024*1024){failure(e,"Invalid audio request");return -1;}
 struct sockaddr_un address={.sun_family=AF_UNIX};if(strlen(path)>=sizeof(address.sun_path)){failure(e,"Invalid broker socket");return -1;}strcpy(address.sun_path,path);
 int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);if(fd<0){failure(e,"Audio socket failed");return -1;}struct timeval timeout={.tv_sec=6};setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
 uint32_t header[5]={op,(uint32_t)handle,(uint32_t)a,(uint32_t)b,n};uint8_t response[12];jlong value=-1;int status=-1;
 if(connect(fd,(struct sockaddr*)&address,sizeof(address))==0&&transfer(fd,header,20,1)==0&&(!n||transfer(fd,(void*)data,n,1)==0)&&transfer(fd,response,12,0)==0){memcpy(&status,response,4);memcpy(&value,response+4,8);}
 close(fd);if(status!=0){failure(e,"Playback broker rejected request or output server failed");return -1;}return value;
}
JNIEXPORT jlong JNICALL JNI(audioOpen)(JNIEnv *e,jclass c,jint rate,jint channels){return request(e,1,0,rate,channels,NULL,0);}
JNIEXPORT void JNICALL JNI(audioWrite)(JNIEnv *e,jclass c,jlong h,jbyteArray data){int n=(*e)->GetArrayLength(e,data);if(n>4*1024*1024){failure(e,"PCM request limit exceeded");return;}jbyte *p=(*e)->GetByteArrayElements(e,data,NULL);if(p){request(e,2,h,0,0,p,n);(*e)->ReleaseByteArrayElements(e,data,p,JNI_ABORT);}}
JNIEXPORT jlong JNICALL JNI(audioLatency)(JNIEnv *e,jclass c,jlong h){return request(e,3,h,0,0,NULL,0);}
JNIEXPORT void JNICALL JNI(audioControl)(JNIEnv *e,jclass c,jlong h,jboolean drain){request(e,4,h,drain,0,NULL,0);}
JNIEXPORT void JNICALL JNI(audioPause)(JNIEnv *e,jclass c,jlong h,jboolean paused){request(e,5,h,paused,0,NULL,0);}
JNIEXPORT void JNICALL JNI(audioClose)(JNIEnv *e,jclass c,jlong h){request(e,6,h,0,0,NULL,0);}
