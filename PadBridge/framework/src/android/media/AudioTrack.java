package android.media;
import org.padtv.bridge.MediaNative;
import java.nio.ByteBuffer;
import java.util.Arrays;
public class AudioTrack {
 public static final int MODE_STATIC=0,MODE_STREAM=1,STATE_UNINITIALIZED=0,STATE_INITIALIZED=1,PLAYSTATE_STOPPED=1,PLAYSTATE_PAUSED=2,PLAYSTATE_PLAYING=3,WRITE_BLOCKING=0,WRITE_NON_BLOCKING=1,SUCCESS=0,ERROR=-1,ERROR_BAD_VALUE=-2,ERROR_INVALID_OPERATION=-3;
 private long handle,written;private final int rate,channels;private int play=PLAYSTATE_STOPPED;private float volume=1f;
 public AudioTrack(int stream,int rate,int mask,int encoding,int bytes,int mode){if(stream!=3||encoding!=2||mode!=1||bytes<1||(mask!=4&&mask!=12))throw new UnsupportedOperationException("AudioTrack supports music, PCM16 mono/stereo streaming");this.rate=rate;channels=mask==4?1:2;handle=MediaNative.audioOpen(rate,channels);}
 public AudioTrack(AudioAttributes attributes,AudioFormat format,int size,int mode,int session){this(3,format.getSampleRate(),format.getChannelMask(),format.getEncoding(),size,mode);if(session!=0){release();throw new UnsupportedOperationException("Shared audio sessions unavailable");}}
 public static int getMinBufferSize(int rate,int mask,int encoding){return rate>=8000&&rate<=192000&&(mask==4||mask==12)&&encoding==2?rate*(mask==4?1:2)*2/10:ERROR_BAD_VALUE;}
 private void ready(){if(handle==0)throw new IllegalStateException("AudioTrack released");}
 public int getState(){return handle==0?0:1;}public int getPlayState(){return play;}public int getSampleRate(){return rate;}public int getChannelCount(){return channels;}
 public synchronized void play(){ready();MediaNative.audioPause(handle,false);play=3;}public synchronized void pause(){ready();MediaNative.audioPause(handle,true);play=2;}public synchronized void stop(){ready();MediaNative.audioPause(handle,false);MediaNative.audioControl(handle,true);MediaNative.audioPause(handle,true);play=1;}
 public synchronized void flush(){ready();if(play==3)throw new IllegalStateException("Pause before flushing");MediaNative.audioControl(handle,false);written=0;}
 public synchronized int write(byte[] data,int offset,int size){ready();if(offset<0||size<0||offset>data.length-size||size%(channels*2)!=0)return ERROR_BAD_VALUE;if(play!=3)return ERROR_INVALID_OPERATION;byte[] b=Arrays.copyOfRange(data,offset,offset+size);if(volume!=1f)for(int i=0;i<b.length;i+=2){short s=(short)((b[i]&255)|(b[i+1]<<8));int v=Math.round(s*volume);b[i]=(byte)v;b[i+1]=(byte)(v>>8);}MediaNative.audioWrite(handle,b);written+=size/(channels*2);return size;}
 public int write(byte[] data,int offset,int size,int mode){if(mode!=0)throw new UnsupportedOperationException("Nonblocking AudioTrack writes unavailable");return write(data,offset,size);}
 public int write(short[] data,int offset,int size){if(offset<0||size<0||offset>data.length-size)return ERROR_BAD_VALUE;byte[] b=new byte[size*2];for(int i=0;i<size;i++){b[2*i]=(byte)data[offset+i];b[2*i+1]=(byte)(data[offset+i]>>8);}int n=write(b,0,b.length);return n<0?n:n/2;}
 public int write(ByteBuffer data,int size,int mode){if(mode!=0)throw new UnsupportedOperationException("Nonblocking writes unavailable");if(size<0||size>data.remaining())return ERROR_BAD_VALUE;byte[] b=new byte[size];ByteBuffer view=data.duplicate();view.get(b);int n=write(b,0,size);if(n>0)data.position(data.position()+n);return n;}
 public synchronized int getPlaybackHeadPosition(){ready();return (int)Math.max(0,written-MediaNative.audioLatency(handle)*rate/1000000);}
 public synchronized int setVolume(float v){if(Float.isNaN(v)||v<0||v>1)return ERROR_BAD_VALUE;volume=v;return SUCCESS;}
 public synchronized void release(){if(handle!=0){MediaNative.audioClose(handle);handle=0;}play=1;}
 public static final class Builder {private AudioFormat format=new AudioFormat.Builder().build();private AudioAttributes attributes=new AudioAttributes.Builder().build();private int size=19200,mode=1,session;public Builder setAudioFormat(AudioFormat f){format=f;return this;}public Builder setAudioAttributes(AudioAttributes a){attributes=a;return this;}public Builder setBufferSizeInBytes(int s){size=s;return this;}public Builder setTransferMode(int m){mode=m;return this;}public Builder setSessionId(int s){session=s;return this;}public AudioTrack build(){return new AudioTrack(attributes,format,size,mode,session);}}
}
