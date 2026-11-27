/* Real Mesa EGL/GLES2 pbuffer path. Window presentation is an explicit CPU copy. */
#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES2/gl2.h>
#define E(n) Java_org_padtv_bridge_EGLNative_##n
#define G(n) Java_android_opengl_GLES20_##n
typedef struct {void *ptr;int kind;uint32_t generation;} GLHandle;
static GLHandle handles[256];
static void fail(JNIEnv *e,const char *m){if(!(*e)->ExceptionCheck(e))(*e)->ThrowNew(e,(*e)->FindClass(e,"java/lang/IllegalArgumentException"),m);}
static jlong save(JNIEnv *e,void *p,int kind){if(!p)return 0;for(int i=1;i<256;i++)if(handles[i].ptr==p&&handles[i].kind==kind)return ((jlong)handles[i].generation<<32)|i;for(int i=1;i<256;i++)if(!handles[i].ptr){handles[i].generation++;handles[i].ptr=p;handles[i].kind=kind;return ((jlong)handles[i].generation<<32)|i;}fail(e,"EGL handle limit");return 0;}
static void *find(JNIEnv *e,jlong h,int kind){if(h==0)return NULL;uint32_t i=(uint32_t)h;if(i>=256||i==0||handles[i].kind!=kind||handles[i].generation!=(uint32_t)(h>>32)||!handles[i].ptr){fail(e,"Invalid EGL handle");return NULL;}return handles[i].ptr;}
static EGLint *attrs(JNIEnv *e,jintArray array,jint offset){static EGLint none[]={EGL_NONE};if(!array)return none;int n=(*e)->GetArrayLength(e,array);if(offset<0||offset>=n||n-offset>257){fail(e,"EGL attribute bounds");return NULL;}static EGLint data[257];(*e)->GetIntArrayRegion(e,array,offset,n-offset,data);for(int i=0;i<n-offset;i+=2)if(data[i]==EGL_NONE)return data;fail(e,"Unterminated EGL attributes");return NULL;}
JNIEXPORT jlong JNICALL E(display)(JNIEnv *e,jclass c){PFNEGLGETPLATFORMDISPLAYEXTPROC get=(PFNEGLGETPLATFORMDISPLAYEXTPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");return save(e,get?get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,NULL):eglGetDisplay(EGL_DEFAULT_DISPLAY),1);}
JNIEXPORT jintArray JNICALL E(initialize)(JNIEnv *e,jclass c,jlong h){EGLDisplay d=find(e,h,1);if(!d)return NULL;EGLint v[2];if(!eglInitialize(d,&v[0],&v[1]))return NULL;jintArray a=(*e)->NewIntArray(e,2);if(a)(*e)->SetIntArrayRegion(e,a,0,2,v);return a;}
JNIEXPORT jlongArray JNICALL E(configs)(JNIEnv *e,jclass c,jlong display,jintArray array,jint offset,jint limit){EGLDisplay d=find(e,display,1);EGLint *a=attrs(e,array,offset);if(!d||!a||limit<0||limit>128){fail(e,"EGL config bounds");return NULL;}EGLConfig configs[128];EGLint count;if(!eglChooseConfig(d,a,configs,limit,&count))return NULL;jlong ids[128];for(int i=0;i<count&&i<limit;i++)ids[i]=save(e,configs[i],2);if(count>limit)count=limit;jlongArray result=(*e)->NewLongArray(e,count);if(result)(*e)->SetLongArrayRegion(e,result,0,count,ids);return result;}
JNIEXPORT jlong JNICALL E(context)(JNIEnv *e,jclass c,jlong display,jlong config,jlong share,jintArray array,jint offset){EGLDisplay d=find(e,display,1);EGLConfig cfg=find(e,config,2);EGLContext parent=find(e,share,3);EGLint *a=attrs(e,array,offset);if((*e)->ExceptionCheck(e)||!d||!cfg||!a)return 0;if(!eglBindAPI(EGL_OPENGL_ES_API))return 0;return save(e,eglCreateContext(d,cfg,parent,a),3);}
JNIEXPORT jlong JNICALL E(pbuffer)(JNIEnv *e,jclass c,jlong display,jlong config,jintArray array,jint offset){EGLDisplay d=find(e,display,1);EGLConfig cfg=find(e,config,2);EGLint *a=attrs(e,array,offset);if((*e)->ExceptionCheck(e)||!d||!cfg||!a)return 0;int w=0,h=0;for(int i=0;a[i]!=EGL_NONE;i+=2){if(a[i]==EGL_WIDTH)w=a[i+1];if(a[i]==EGL_HEIGHT)h=a[i+1];}if(w<1||h<1||(int64_t)w*h>8388608){fail(e,"EGL pbuffer size limit");return 0;}return save(e,eglCreatePbufferSurface(d,cfg,a),4);}
JNIEXPORT jboolean JNICALL E(current)(JNIEnv *e,jclass c,jlong display,jlong draw,jlong read,jlong context){EGLDisplay d=find(e,display,1);EGLSurface a=find(e,draw,4),b=find(e,read,4);EGLContext ctx=find(e,context,3);if((*e)->ExceptionCheck(e)||!d)return 0;return eglMakeCurrent(d,a,b,ctx);}
JNIEXPORT jboolean JNICALL E(swap)(JNIEnv *e,jclass c,jlong display,jlong surface){EGLDisplay d=find(e,display,1);EGLSurface s=find(e,surface,4);return d&&s?eglSwapBuffers(d,s):0;}
JNIEXPORT jboolean JNICALL E(destroy)(JNIEnv *e,jclass c,jlong display,jlong value,jint kind){EGLDisplay d=find(e,display,1);void *p=find(e,value,kind);if(!d||!p||(*e)->ExceptionCheck(e))return 0;EGLBoolean ok=kind==3?eglDestroyContext(d,p):kind==4?eglDestroySurface(d,p):EGL_FALSE;if(ok)handles[(uint32_t)value].ptr=NULL;return ok;}
JNIEXPORT jboolean JNICALL E(terminate)(JNIEnv *e,jclass c,jlong display){EGLDisplay d=find(e,display,1);if(!d)return 0;EGLBoolean ok=eglTerminate(d);if(ok)handles[(uint32_t)display].ptr=NULL;return ok;}
JNIEXPORT jint JNICALL E(error)(JNIEnv *e,jclass c){return eglGetError();}
JNIEXPORT jstring JNICALL E(query)(JNIEnv *e,jclass c,jlong display,jint name){EGLDisplay d=find(e,display,1);if(!d)return NULL;const char *s=eglQueryString(d,name);return s?(*e)->NewStringUTF(e,s):NULL;}
JNIEXPORT jbyteArray JNICALL E(pixels)(JNIEnv *e,jclass c,jint width,jint height){if(width<1||height<1||(int64_t)width*height>8388608){fail(e,"GL image size limit");return NULL;}size_t n=(size_t)width*height*4;uint8_t *pixels=malloc(n),*flipped=malloc(n);if(!pixels||!flipped){free(pixels);free(flipped);fail(e,"GL allocation failed");return NULL;}glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels);if(glGetError()!=GL_NO_ERROR){free(pixels);free(flipped);fail(e,"GL pixel read failed");return NULL;}for(int y=0;y<height;y++)memcpy(flipped+(size_t)y*width*4,pixels+(size_t)(height-y-1)*width*4,width*4);jbyteArray a=(*e)->NewByteArray(e,n);if(a)(*e)->SetByteArrayRegion(e,a,0,n,(jbyte*)flipped);free(pixels);free(flipped);return a;}
JNIEXPORT void JNICALL G(glClearColor)(JNIEnv *e,jclass c,jfloat r,jfloat g,jfloat b,jfloat a){glClearColor(r,g,b,a);}
JNIEXPORT void JNICALL G(glClear)(JNIEnv *e,jclass c,jint mask){glClear(mask);}
JNIEXPORT void JNICALL G(glViewport)(JNIEnv *e,jclass c,jint x,jint y,jint w,jint h){glViewport(x,y,w,h);}
JNIEXPORT jint JNICALL G(glGetError)(JNIEnv *e,jclass c){return glGetError();}
JNIEXPORT jstring JNICALL G(glGetString)(JNIEnv *e,jclass c,jint name){const GLubyte *s=glGetString(name);return s?(*e)->NewStringUTF(e,(const char*)s):NULL;}
JNIEXPORT jint JNICALL G(glCreateShader)(JNIEnv *e,jclass c,jint type){return glCreateShader(type);}
JNIEXPORT void JNICALL G(glShaderSource)(JNIEnv *e,jclass c,jint shader,jstring code){const char *s=(*e)->GetStringUTFChars(e,code,NULL);if(s){glShaderSource(shader,1,&s,NULL);(*e)->ReleaseStringUTFChars(e,code,s);}}
JNIEXPORT void JNICALL G(glCompileShader)(JNIEnv *e,jclass c,jint shader){glCompileShader(shader);}
JNIEXPORT jint JNICALL G(glCreateProgram)(JNIEnv *e,jclass c){return glCreateProgram();}
JNIEXPORT void JNICALL G(glAttachShader)(JNIEnv *e,jclass c,jint program,jint shader){glAttachShader(program,shader);}
JNIEXPORT void JNICALL G(glLinkProgram)(JNIEnv *e,jclass c,jint program){glLinkProgram(program);}
JNIEXPORT void JNICALL G(glUseProgram)(JNIEnv *e,jclass c,jint program){glUseProgram(program);}
JNIEXPORT jint JNICALL G(glGetAttribLocation)(JNIEnv *e,jclass c,jint program,jstring name){const char *s=(*e)->GetStringUTFChars(e,name,NULL);if(!s)return -1;int result=glGetAttribLocation(program,s);(*e)->ReleaseStringUTFChars(e,name,s);return result;}
static void integer_result(JNIEnv *e,jintArray out,int offset,int value){if(!out||offset<0||offset>=(*e)->GetArrayLength(e,out)){fail(e,"GL integer output bounds");return;}(*e)->SetIntArrayRegion(e,out,offset,1,&value);}
JNIEXPORT void JNICALL G(glGetShaderiv)(JNIEnv *e,jclass c,jint shader,jint name,jintArray out,jint offset){GLint value=0;glGetShaderiv(shader,name,&value);integer_result(e,out,offset,value);}
JNIEXPORT void JNICALL G(glGetProgramiv)(JNIEnv *e,jclass c,jint program,jint name,jintArray out,jint offset){GLint value=0;glGetProgramiv(program,name,&value);integer_result(e,out,offset,value);}
JNIEXPORT jstring JNICALL G(glGetShaderInfoLog)(JNIEnv *e,jclass c,jint shader){char log[8192]={0};GLsizei n;glGetShaderInfoLog(shader,sizeof(log),&n,log);return (*e)->NewStringUTF(e,log);}
JNIEXPORT jstring JNICALL G(glGetProgramInfoLog)(JNIEnv *e,jclass c,jint program){char log[8192]={0};GLsizei n;glGetProgramInfoLog(program,sizeof(log),&n,log);return (*e)->NewStringUTF(e,log);}
JNIEXPORT void JNICALL G(glGenBuffers)(JNIEnv *e,jclass c,jint count,jintArray out,jint offset){if(count<0||count>128||offset<0||!out||offset>(*e)->GetArrayLength(e,out)-count){fail(e,"GL buffer output bounds");return;}GLuint names[128];glGenBuffers(count,names);(*e)->SetIntArrayRegion(e,out,offset,count,(jint*)names);}
JNIEXPORT void JNICALL G(glBindBuffer)(JNIEnv *e,jclass c,jint target,jint buffer){glBindBuffer(target,buffer);}
static void *direct(JNIEnv *e,jobject b,jint size){if(size<0||size>32*1024*1024){fail(e,"GL byte size limit");return NULL;}void *p=(*e)->GetDirectBufferAddress(e,b);jlong n=(*e)->GetDirectBufferCapacity(e,b);int unit=1;if((*e)->IsInstanceOf(e,b,(*e)->FindClass(e,"java/nio/FloatBuffer"))||(*e)->IsInstanceOf(e,b,(*e)->FindClass(e,"java/nio/IntBuffer")))unit=4;else if(!(*e)->IsInstanceOf(e,b,(*e)->FindClass(e,"java/nio/ByteBuffer")))n=-1;jclass cls=(*e)->FindClass(e,"java/nio/Buffer");int pos=(*e)->CallIntMethod(e,b,(*e)->GetMethodID(e,cls,"position","()I"));int limit=(*e)->CallIntMethod(e,b,(*e)->GetMethodID(e,cls,"limit","()I"));if(!p||n<0||pos<0||limit<pos||limit>n||(jlong)(limit-pos)*unit<size){fail(e,"Direct GL buffer too small or unsupported");return NULL;}return (uint8_t*)p+(size_t)pos*unit;}
JNIEXPORT void JNICALL G(glBufferData)(JNIEnv *e,jclass c,jint target,jint size,jobject data,jint usage){if(!data){if(size<0||size>32*1024*1024){fail(e,"GL allocation limit");return;}glBufferData(target,size,NULL,usage);return;}void *p=direct(e,data,size);if(p)glBufferData(target,size,p,usage);}
JNIEXPORT void JNICALL G(glVertexAttribPointer)(JNIEnv *e,jclass c,jint index,jint size,jint type,jboolean normalized,jint stride,jint offset){GLint binding=0;glGetIntegerv(GL_ARRAY_BUFFER_BINDING,&binding);if(!binding||offset<0){fail(e,"Vertex attributes require a bound VBO");return;}glVertexAttribPointer(index,size,type,normalized,stride,(void*)(uintptr_t)offset);}
JNIEXPORT void JNICALL G(glEnableVertexAttribArray)(JNIEnv *e,jclass c,jint index){glEnableVertexAttribArray(index);}
JNIEXPORT void JNICALL G(glDrawArrays)(JNIEnv *e,jclass c,jint mode,jint first,jint count){glDrawArrays(mode,first,count);}
JNIEXPORT void JNICALL G(glReadPixels)(JNIEnv *e,jclass c,jint x,jint y,jint w,jint h,jint format,jint type,jobject pixels){if(w<0||h<0||(int64_t)w*h>8388608||format!=GL_RGBA||type!=GL_UNSIGNED_BYTE){fail(e,"Only bounded RGBA8 reads supported");return;}void *p=direct(e,pixels,w*h*4);if(p)glReadPixels(x,y,w,h,format,type,p);}
JNIEXPORT void JNICALL G(glFinish)(JNIEnv *e,jclass c){glFinish();}
JNIEXPORT void JNICALL G(glDeleteShader)(JNIEnv *e,jclass c,jint id){glDeleteShader(id);}
JNIEXPORT void JNICALL G(glDeleteProgram)(JNIEnv *e,jclass c,jint id){glDeleteProgram(id);}
