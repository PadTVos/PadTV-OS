/* PadBridge FFmpeg/PulseAudio JNI transport. No Android binaries are substituted.
 * Handles are generation-checked and all entry points are serialized by MediaNative.
 * PulseAudio's protocol also supports the PipeWire pulse compatibility service. */
#include <jni.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavutil/imgutils.h>
#include <libswscale/swscale.h>
#include <libswresample/swresample.h>

#define JNI(name) Java_org_padtv_bridge_MediaNative_##name
#define LIMIT (32*1024*1024)
typedef struct { uint32_t generation; int kind; void *value; } Slot;
static Slot slots[128];
typedef struct { AVFormatContext *ctx; AVPacket *packet; int valid; } Demux;
typedef struct { AVCodecContext *ctx; AVFrame *frame; struct SwsContext *scale; SwrContext *resample; int64_t info[6]; } Decoder;
static void error(JNIEnv *e,const char *type,const char *message) { if(!(*e)->ExceptionCheck(e)) (*e)->ThrowNew(e,(*e)->FindClass(e,type),message); }
static void av_error(JNIEnv *e,int code) { char msg[256]; av_strerror(code,msg,sizeof(msg)); error(e,"java/io/IOException",msg); }
static jlong put(JNIEnv *e,int kind,void *value) {
 for(int i=1;i<128;i++) if(!slots[i].value) { slots[i].generation++; slots[i].kind=kind; slots[i].value=value; return ((jlong)slots[i].generation<<32)|i; }
 error(e,"java/lang/IllegalStateException","Media handle limit exceeded"); return 0;
}
static void *get(JNIEnv *e,jlong h,int kind) {
 uint32_t i=(uint32_t)h;
 if(i==0||i>=128||!slots[i].value||slots[i].kind!=kind||slots[i].generation!=(uint32_t)(h>>32)) { error(e,"java/lang/IllegalStateException","Invalid or released media handle"); return NULL; }
 return slots[i].value;
}
static jbyteArray bytes(JNIEnv *e,const uint8_t *p,int n) {
 if(n<0||n>LIMIT) { error(e,"java/lang/IllegalArgumentException","Media buffer exceeds limit");return NULL; }
 jbyteArray a=(*e)->NewByteArray(e,n);if(a&&n)(*e)->SetByteArrayRegion(e,a,0,n,(const jbyte*)p);return a;
}
static jlongArray longs(JNIEnv *e,const int64_t *v,int n) { jlongArray a=(*e)->NewLongArray(e,n);if(a)(*e)->SetLongArrayRegion(e,a,0,n,(const jlong*)v);return a; }
static const char *mime(enum AVCodecID id) {
 switch(id) { case AV_CODEC_ID_H264:return "video/avc";case AV_CODEC_ID_HEVC:return "video/hevc";case AV_CODEC_ID_VP9:return "video/x-vnd.on2.vp9";case AV_CODEC_ID_VP8:return "video/x-vnd.on2.vp8";case AV_CODEC_ID_AV1:return "video/av01";case AV_CODEC_ID_MPEG4:return "video/mp4v-es";case AV_CODEC_ID_AAC:return "audio/mp4a-latm";case AV_CODEC_ID_MP3:return "audio/mpeg";case AV_CODEC_ID_OPUS:return "audio/opus";case AV_CODEC_ID_VORBIS:return "audio/vorbis";case AV_CODEC_ID_FLAC:return "audio/flac";case AV_CODEC_ID_PCM_S16LE:return "audio/raw";default:return "application/octet-stream"; }
}
JNIEXPORT jint JNICALL JNI(codecId)(JNIEnv *e,jclass c,jstring type) {
 const char *s=(*e)->GetStringUTFChars(e,type,0);if(!s)return 0;
 enum AVCodecID ids[]={AV_CODEC_ID_H264,AV_CODEC_ID_HEVC,AV_CODEC_ID_VP9,AV_CODEC_ID_VP8,AV_CODEC_ID_AV1,AV_CODEC_ID_MPEG4,AV_CODEC_ID_AAC,AV_CODEC_ID_MP3,AV_CODEC_ID_OPUS,AV_CODEC_ID_VORBIS,AV_CODEC_ID_FLAC,AV_CODEC_ID_PCM_S16LE};int result=0;
 for(unsigned i=0;i<sizeof(ids)/sizeof(ids[0]);i++)if(!strcmp(s,mime(ids[i]))&&avcodec_find_decoder(ids[i])){result=ids[i];break;}
 (*e)->ReleaseStringUTFChars(e,type,s);return result;
}
JNIEXPORT jlong JNICALL JNI(open)(JNIEnv *e,jclass c,jstring source) {
 const char *s=(*e)->GetStringUTFChars(e,source,0);if(!s)return 0;
 av_max_alloc(64*1024*1024);
 Demux *d=av_mallocz(sizeof(*d));if(!d){(*e)->ReleaseStringUTFChars(e,source,s);error(e,"java/lang/OutOfMemoryError","demux");return 0;}
 AVDictionary *opts=NULL;av_dict_set(&opts,"max_streams","64",0);av_dict_set(&opts,"probesize","5000000",0);av_dict_set(&opts,"analyzeduration","5000000",0);av_dict_set(&opts,"protocol_whitelist","file,http,https,tcp,tls",0);av_dict_set(&opts,"rw_timeout","5000000",0);av_dict_set(&opts,"tls_verify","1",0);const char *ca=getenv("PADBRIDGE_CA_BUNDLE");av_dict_set(&opts,"ca_file",ca?ca:"/etc/ssl/certs/ca-certificates.crt",0);
 int r=avformat_open_input(&d->ctx,s,NULL,&opts);av_dict_free(&opts);(*e)->ReleaseStringUTFChars(e,source,s);
 if(r>=0)r=avformat_find_stream_info(d->ctx,NULL);
 if(r<0||d->ctx->nb_streams>64) { if(r<0)av_error(e,r);else error(e,"java/io/IOException","Too many tracks");avformat_close_input(&d->ctx);av_free(d);return 0; }
 d->packet=av_packet_alloc();if(!d->packet){avformat_close_input(&d->ctx);av_free(d);error(e,"java/lang/OutOfMemoryError","packet");return 0;}
 jlong h=put(e,1,d);if(!h){av_packet_free(&d->packet);avformat_close_input(&d->ctx);av_free(d);}return h;
}
JNIEXPORT jint JNICALL JNI(trackCount)(JNIEnv *e,jclass c,jlong h) { Demux *d=get(e,h,1);return d?d->ctx->nb_streams:0; }
JNIEXPORT jobjectArray JNICALL JNI(trackFormat)(JNIEnv *e,jclass c,jlong h,jint track) {
 Demux *d=get(e,h,1);if(!d)return NULL;
 if(track<0||(unsigned)track>=d->ctx->nb_streams){error(e,"java/lang/IllegalArgumentException","Invalid track");return NULL;}
 AVStream *s=d->ctx->streams[track];AVCodecParameters *p=s->codecpar;
 char values[7][64];snprintf(values[0],64,"%s",mime(p->codec_id));snprintf(values[1],64,"%d",p->width);snprintf(values[2],64,"%d",p->height);snprintf(values[3],64,"%d",p->sample_rate);snprintf(values[4],64,"%d",p->ch_layout.nb_channels);
 int64_t duration=s->duration==AV_NOPTS_VALUE?d->ctx->duration:av_rescale_q(s->duration,s->time_base,AV_TIME_BASE_Q);
 snprintf(values[5],64,"%lld",(long long)(duration==AV_NOPTS_VALUE?-1:duration));snprintf(values[6],64,"%d",p->codec_id);
 jobjectArray a=(*e)->NewObjectArray(e,7,(*e)->FindClass(e,"java/lang/String"),NULL);if(a)for(int i=0;i<7;i++){jstring str=(*e)->NewStringUTF(e,values[i]);(*e)->SetObjectArrayElement(e,a,i,str);(*e)->DeleteLocalRef(e,str);}return a;
}
JNIEXPORT jbyteArray JNICALL JNI(extra)(JNIEnv *e,jclass c,jlong h,jint track) {
 Demux *d=get(e,h,1);if(!d)return NULL;if(track<0||(unsigned)track>=d->ctx->nb_streams){error(e,"java/lang/IllegalArgumentException","Invalid track");return NULL;}AVCodecParameters *p=d->ctx->streams[track]->codecpar;return bytes(e,p->extradata,p->extradata_size);
}
JNIEXPORT jboolean JNICALL JNI(next)(JNIEnv *e,jclass c,jlong h) {
 Demux *d=get(e,h,1);if(!d)return 0;av_packet_unref(d->packet);d->valid=0;int r=av_read_frame(d->ctx,d->packet);if(r==AVERROR_EOF)return 0;if(r<0){av_error(e,r);return 0;}if(d->packet->size>LIMIT){error(e,"java/io/IOException","Packet exceeds limit");return 0;}d->valid=1;return 1;
}
JNIEXPORT jbyteArray JNICALL JNI(packet)(JNIEnv *e,jclass c,jlong h) { Demux *d=get(e,h,1);return d&&d->valid?bytes(e,d->packet->data,d->packet->size):NULL; }
JNIEXPORT jlongArray JNICALL JNI(packetInfo)(JNIEnv *e,jclass c,jlong h) {
 Demux *d=get(e,h,1);if(!d)return NULL;int64_t v[3]={-1,-1,0};if(d->valid){AVPacket *p=d->packet;v[0]=p->stream_index;v[1]=p->pts==AV_NOPTS_VALUE?-1:av_rescale_q(p->pts,d->ctx->streams[p->stream_index]->time_base,AV_TIME_BASE_Q);v[2]=(p->flags&AV_PKT_FLAG_KEY)?1:0;}return longs(e,v,3);
}
JNIEXPORT void JNICALL JNI(seek)(JNIEnv *e,jclass c,jlong h,jlong us,jint mode) { Demux *d=get(e,h,1);if(!d)return;int r=av_seek_frame(d->ctx,-1,us,mode==0?AVSEEK_FLAG_BACKWARD:0);if(r<0)av_error(e,r);else{av_packet_unref(d->packet);d->valid=0;} }
JNIEXPORT jlong JNICALL JNI(decoder)(JNIEnv *e,jclass c,jint codec,jint w,jint height,jint rate,jint channels,jbyteArray extra) {
 const AVCodec *impl=avcodec_find_decoder(codec);if(!impl){error(e,"java/io/IOException","Decoder unavailable");return 0;}
 if(w<0||height<0||w>4096||height>2160||rate<0||rate>192000||channels<0||channels>8){error(e,"java/lang/IllegalArgumentException","Unsupported media dimensions");return 0;}
 Decoder *d=av_mallocz(sizeof(*d));if(!d){error(e,"java/lang/OutOfMemoryError","decoder");return 0;}d->ctx=avcodec_alloc_context3(impl);d->frame=av_frame_alloc();if(!d->ctx||!d->frame)goto oom;
 d->ctx->width=w;d->ctx->height=height;d->ctx->sample_rate=rate;av_channel_layout_default(&d->ctx->ch_layout,channels);d->ctx->pkt_timebase=AV_TIME_BASE_Q;d->ctx->thread_count=2;
 if(extra){int n=(*e)->GetArrayLength(e,extra);if(n>1048576){error(e,"java/lang/IllegalArgumentException","Extradata exceeds limit");goto fail;}d->ctx->extradata=av_mallocz(n+AV_INPUT_BUFFER_PADDING_SIZE);if(!d->ctx->extradata)goto oom;d->ctx->extradata_size=n;(*e)->GetByteArrayRegion(e,extra,0,n,(jbyte*)d->ctx->extradata);}
 int r=avcodec_open2(d->ctx,impl,NULL);if(r<0){av_error(e,r);goto fail;}jlong h=put(e,2,d);if(h)return h;goto fail;
 oom:error(e,"java/lang/OutOfMemoryError","codec");
 fail:avcodec_free_context(&d->ctx);av_frame_free(&d->frame);av_free(d);return 0;
}
JNIEXPORT jint JNICALL JNI(send)(JNIEnv *e,jclass c,jlong h,jbyteArray data,jlong pts) {
 Decoder *d=get(e,h,2);if(!d)return -1;AVPacket *p=NULL;int r;
 if(data){int n=(*e)->GetArrayLength(e,data);if(n>LIMIT){error(e,"java/lang/IllegalArgumentException","Packet exceeds limit");return -1;}p=av_packet_alloc();if(!p||(r=av_new_packet(p,n))<0){av_packet_free(&p);error(e,"java/lang/OutOfMemoryError","packet");return -1;}(*e)->GetByteArrayRegion(e,data,0,n,(jbyte*)p->data);p->pts=pts;p->dts=AV_NOPTS_VALUE;}
 r=avcodec_send_packet(d->ctx,p);av_packet_free(&p);if(r==AVERROR(EAGAIN))return 0;if(r<0&&r!=AVERROR_EOF){av_error(e,r);return -1;}return 1;
}
JNIEXPORT jbyteArray JNICALL JNI(receive)(JNIEnv *e,jclass c,jlong h) {
 Decoder *d=get(e,h,2);if(!d)return NULL;int r=avcodec_receive_frame(d->ctx,d->frame);d->info[5]=r==AVERROR_EOF?1:0;if(r==AVERROR(EAGAIN)||r==AVERROR_EOF)return NULL;if(r<0){av_error(e,r);return NULL;}
 AVFrame *f=d->frame;uint8_t *out=NULL;int n=0;d->info[0]=f->pts==AV_NOPTS_VALUE?0:f->pts;
 if(d->ctx->codec_type==AVMEDIA_TYPE_VIDEO){if(f->width<=0||f->height<=0||f->width>4096||f->height>2160){error(e,"java/io/IOException","Decoded frame exceeds limit");return NULL;}n=f->width*f->height*4;if(n>LIMIT){error(e,"java/io/IOException","RGBA frame exceeds limit");return NULL;}out=av_malloc(n);if(!out)goto oom;d->scale=sws_getCachedContext(d->scale,f->width,f->height,f->format,f->width,f->height,AV_PIX_FMT_RGBA,SWS_BILINEAR,NULL,NULL,NULL);if(!d->scale)goto oom;uint8_t *planes[]={out,NULL,NULL,NULL};int strides[]={f->width*4,0,0,0};sws_scale(d->scale,(const uint8_t *const*)f->data,f->linesize,0,f->height,planes,strides);d->info[1]=f->width;d->info[2]=f->height;d->info[3]=0;d->info[4]=0;
 }else if(d->ctx->codec_type==AVMEDIA_TYPE_AUDIO){if(f->ch_layout.nb_channels<1||f->ch_layout.nb_channels>8||f->sample_rate<1||f->sample_rate>192000){error(e,"java/io/IOException","Invalid decoded audio format");return NULL;}swr_free(&d->resample);r=swr_alloc_set_opts2(&d->resample,&f->ch_layout,AV_SAMPLE_FMT_S16,f->sample_rate,&f->ch_layout,f->format,f->sample_rate,0,NULL);if(r<0||swr_init(d->resample)<0){error(e,"java/io/IOException","Audio converter failed");return NULL;}int count=swr_get_out_samples(d->resample,f->nb_samples);if(count<0||count>1048576){error(e,"java/io/IOException","Audio buffer exceeds limit");return NULL;}n=count*f->ch_layout.nb_channels*2;out=av_malloc(n);if(!out)goto oom;r=swr_convert(d->resample,&out,count,(const uint8_t**)f->extended_data,f->nb_samples);if(r<0){av_free(out);av_error(e,r);return NULL;}n=r*f->ch_layout.nb_channels*2;d->info[1]=0;d->info[2]=0;d->info[3]=f->sample_rate;d->info[4]=f->ch_layout.nb_channels;
 }else{error(e,"java/io/IOException","Unsupported decoded media type");return NULL;}
 jbyteArray a=bytes(e,out,n);av_free(out);av_frame_unref(f);return a;
 oom:av_free(out);error(e,"java/lang/OutOfMemoryError","frame");return NULL;
}
JNIEXPORT jlongArray JNICALL JNI(frameInfo)(JNIEnv *e,jclass c,jlong h) { Decoder *d=get(e,h,2);return d?longs(e,d->info,6):NULL; }
JNIEXPORT void JNICALL JNI(flushDecoder)(JNIEnv *e,jclass c,jlong h) { Decoder *d=get(e,h,2);if(d){avcodec_flush_buffers(d->ctx);av_frame_unref(d->frame);memset(d->info,0,sizeof(d->info));} }
JNIEXPORT void JNICALL JNI(close)(JNIEnv *e,jclass c,jlong h,jint kind) {
 void *v=get(e,h,kind);if(!v)return;
 if(kind==1){Demux *d=v;av_packet_free(&d->packet);avformat_close_input(&d->ctx);av_free(d);}
 else if(kind==2){Decoder *d=v;avcodec_free_context(&d->ctx);av_frame_free(&d->frame);sws_freeContext(d->scale);swr_free(&d->resample);av_free(d);}
 slots[(uint32_t)h].value=NULL;
}
