package android.media;
import java.io.IOException;
import java.nio.ByteBuffer;
import org.padtv.bridge.MediaNative;
public final class MediaCodec {
 public static final int BUFFER_FLAG_KEY_FRAME=1,BUFFER_FLAG_CODEC_CONFIG=2,BUFFER_FLAG_END_OF_STREAM=4,INFO_TRY_AGAIN_LATER=-1,INFO_OUTPUT_FORMAT_CHANGED=-2,INFO_OUTPUT_BUFFERS_CHANGED=-3,CONFIGURE_FLAG_ENCODE=1;
 public static final class BufferInfo {public int offset,size,flags;public long presentationTimeUs;public void set(int o,int s,long p,int f){offset=o;size=s;presentationTimeUs=p;flags=f;}}
 private final String mime;private MediaFormat format,output;private android.view.Surface surface;private long handle;private int state;private ByteBuffer input,decoded;private boolean inputOwned,outputOwned,formatSent,eosSent,eosOutput,pendingEOS;private byte[] pending;private long pendingTime;private long[] frame;
 private MediaCodec(String m){mime=m;}
 public static MediaCodec createDecoderByType(String type)throws IOException{if(MediaNative.codecId(type)==0)throw new IOException("Decoder unavailable: "+type);return new MediaCodec(type);}
 public static MediaCodec createByCodecName(String name)throws IOException{if(!name.startsWith("padbridge.ffmpeg."))throw new IOException("Unknown decoder: "+name);return createDecoderByType(name.substring(17));}
 public String getName(){return "padbridge.ffmpeg."+mime;}
 public void configure(MediaFormat f,android.view.Surface s,MediaCrypto crypto,int flags){if(state!=0)throw new IllegalStateException();if(crypto!=null||flags!=0)throw new UnsupportedOperationException("Secure codecs and encoders are unavailable");if(!mime.equals(f.getString("mime")))throw new IllegalArgumentException("MIME mismatch");format=f.copy();surface=s;state=1;}
 private byte[] extra(){ByteBuffer b=format.getByteBuffer("padbridge-ffmpeg-extradata");if(b!=null){byte[] a=new byte[b.remaining()];b.get(a);return a;}java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();for(int i=0;i<3;i++){b=format.getByteBuffer("csd-"+i);if(b!=null){byte[] a=new byte[b.remaining()];b.get(a);out.write(a,0,a.length);}}return out.toByteArray();}
 public void start(){if(state!=1)throw new IllegalStateException();int size=format.getInteger("max-input-size",4*1024*1024);if(size<1||size>32*1024*1024)throw new IllegalArgumentException("Input size limit");try{handle=MediaNative.decoder(MediaNative.codecId(mime),format.getInteger("width",0),format.getInteger("height",0),format.getInteger("sample-rate",0),format.getInteger("channel-count",0),extra());}catch(IOException e){throw new IllegalStateException("Decoder open failed",e);}input=ByteBuffer.allocateDirect(size);state=2;resetQueues();}
 private void started(){if(state!=2)throw new IllegalStateException("Codec is not started");}
 private void resetQueues(){inputOwned=false;outputOwned=false;formatSent=false;eosSent=false;eosOutput=false;pending=null;decoded=null;pendingEOS=false;}
 public int dequeueInputBuffer(long timeoutUs){started();if(inputOwned||pending!=null||pendingEOS||eosSent)return -1;input.clear();inputOwned=true;return 0;}
 public ByteBuffer getInputBuffer(int index){started();if(index!=0||!inputOwned)throw new IllegalStateException("Input buffer not owned");return input;}
 public ByteBuffer[] getInputBuffers(){started();return new ByteBuffer[]{input};}
 public void queueInputBuffer(int index,int offset,int size,long timeUs,int flags){getInputBuffer(index);if(offset<0||size<0||offset>input.capacity()-size)throw new IllegalArgumentException();if((flags&~7)!=0)throw new UnsupportedOperationException("Unsupported codec buffer flags");if((flags&BUFFER_FLAG_CODEC_CONFIG)!=0)throw new UnsupportedOperationException("Provide codec initialization data in MediaFormat before start");pending=new byte[size];ByteBuffer b=input.duplicate();b.clear();b.position(offset);b.get(pending);pendingTime=timeUs;pendingEOS=(flags&4)!=0;inputOwned=false;}
 public int dequeueOutputBuffer(BufferInfo info,long timeoutUs){started();if(outputOwned)return -1;if(eosOutput)return -1;
  if(decoded==null){if(pending!=null){if(pending.length==0||MediaNative.send(handle,pending,pendingTime)==1)pending=null;}if(pending==null&&pendingEOS&&!eosSent){if(MediaNative.send(handle,null,0)==1){eosSent=true;pendingEOS=false;}}
   byte[] b=MediaNative.receive(handle);frame=MediaNative.frameInfo(handle);if(b!=null){decoded=ByteBuffer.wrap(b);output=new MediaFormat();if(mime.startsWith("video/")){output.setString("mime","video/raw");output.setInteger("width",(int)frame[1]);output.setInteger("height",(int)frame[2]);output.setInteger("color-format",16);}else{output.setString("mime","audio/raw");output.setInteger("sample-rate",(int)frame[3]);output.setInteger("channel-count",(int)frame[4]);output.setInteger("pcm-encoding",2);}}
   else if(frame[5]==1&&eosSent){decoded=ByteBuffer.allocate(0);eosOutput=true;}else return -1;
  }
  if(!formatSent&&output!=null){formatSent=true;return INFO_OUTPUT_FORMAT_CHANGED;}outputOwned=true;info.set(0,decoded.remaining(),frame[0],eosOutput?4:0);return 0;
 }
 public ByteBuffer getOutputBuffer(int index){started();if(index!=0||!outputOwned)throw new IllegalStateException("Output buffer not owned");return decoded.asReadOnlyBuffer();}
 public MediaFormat getOutputFormat(){started();if(output==null)throw new IllegalStateException("No output format yet");return output.copy();}public MediaFormat getOutputFormat(int index){return getOutputFormat();}
 public void releaseOutputBuffer(int index,boolean render){getOutputBuffer(index);if(render&&decoded.hasRemaining()){if(surface==null)throw new IllegalStateException("No output surface");if(!mime.startsWith("video/"))throw new IllegalStateException("Audio cannot render to Surface");surface.bridgeRGBA(decoded.duplicate(),(int)frame[1],(int)frame[2]);}outputOwned=false;decoded=null;}
 public void releaseOutputBuffer(int index,long renderTimeNs){long wait=renderTimeNs-System.nanoTime();if(wait>0)java.util.concurrent.locks.LockSupport.parkNanos(Math.min(wait,1000000000L));releaseOutputBuffer(index,true);}
 public void flush(){started();MediaNative.flushDecoder(handle);resetQueues();}
 public void stop(){started();MediaNative.close(handle,2);handle=0;state=1;resetQueues();}
 public void release(){if(handle!=0)MediaNative.close(handle,2);handle=0;state=3;resetQueues();}
}
