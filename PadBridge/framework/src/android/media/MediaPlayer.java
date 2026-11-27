package android.media;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.os.Handler;
import android.os.Looper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.*;
/** Unencrypted software playback. Original APK calls these Android APIs. */
public class MediaPlayer {
 public interface OnPreparedListener{void onPrepared(MediaPlayer p);}public interface OnCompletionListener{void onCompletion(MediaPlayer p);}public interface OnErrorListener{boolean onError(MediaPlayer p,int what,int extra);}public interface OnVideoSizeChangedListener{void onVideoSizeChanged(MediaPlayer p,int w,int h);}public interface OnSeekCompleteListener{void onSeekComplete(MediaPlayer p);}
 public static final int MEDIA_ERROR_UNKNOWN=1,MEDIA_ERROR_IO=-1004,MEDIA_ERROR_UNSUPPORTED=-1010;
 private enum State{IDLE,INITIALIZED,PREPARING,PREPARED,STARTED,PAUSED,STOPPED,COMPLETED,ERROR,RELEASED}
 private volatile State state=State.IDLE;private String source;private Surface surface;private MediaExtractor extractor;private final Map<Integer,MediaCodec> codecs=new LinkedHashMap<Integer,MediaCodec>();private final Map<Integer,AudioTrack> audio=new java.util.concurrent.ConcurrentHashMap<Integer,AudioTrack>();private final Handler events;private Thread worker;private volatile boolean cancel,looping;private volatile long seek=-1,position,pausedTime;private long pauseStart,duration;private int width,height;private float volume=1;
 private OnPreparedListener prepared;private OnCompletionListener completion;private OnErrorListener error;private OnVideoSizeChangedListener videoSize;private OnSeekCompleteListener seekComplete;
 public MediaPlayer(){events=new Handler(Looper.myLooper()!=null?Looper.myLooper():Looper.getMainLooper());}
 public void setOnPreparedListener(OnPreparedListener l){prepared=l;}public void setOnCompletionListener(OnCompletionListener l){completion=l;}public void setOnErrorListener(OnErrorListener l){error=l;}public void setOnVideoSizeChangedListener(OnVideoSizeChangedListener l){videoSize=l;}public void setOnSeekCompleteListener(OnSeekCompleteListener l){seekComplete=l;}
 public synchronized void setDataSource(String path)throws IOException{require(State.IDLE);if(path==null||path.isEmpty())throw new IllegalArgumentException("Empty media source");source=path;state=State.INITIALIZED;}
 public void setDataSource(android.content.Context c,android.net.Uri uri)throws IOException{setDataSource(uri.toString());}
 public synchronized void setSurface(Surface s){if(state==State.STARTED||state==State.PAUSED)throw new UnsupportedOperationException("Change Surface before preparing playback");surface=s;}
 public void setDisplay(SurfaceHolder holder){setSurface(holder==null?null:holder.getSurface());}
 public void setAudioStreamType(int type){if(type!=3)throw new UnsupportedOperationException("Only media stream supported");}
 public void setAudioAttributes(AudioAttributes a){if(a.getUsage()!=AudioAttributes.USAGE_MEDIA&&a.getUsage()!=AudioAttributes.USAGE_GAME)throw new UnsupportedOperationException("Unsupported audio usage");}
 private synchronized void require(State... states){for(State s:states)if(state==s)return;throw new IllegalStateException("MediaPlayer state: "+state);}
 public void prepare()throws IOException{require(State.INITIALIZED,State.STOPPED);state=State.PREPARING;try{open();state=State.PREPARED;}catch(Exception e){closeMedia();state=State.ERROR;throw new IOException("Media prepare failed",e);}}
 public void prepareAsync(){require(State.INITIALIZED,State.STOPPED);state=State.PREPARING;cancel=false;worker=new Thread(new Runnable(){public void run(){try{open();if(cancel){closeMedia();return;}state=State.PREPARED;events.post(new Runnable(){public void run(){if(prepared!=null&&state==State.PREPARED)prepared.onPrepared(MediaPlayer.this);}});}catch(Exception e){failure(e);}}},"MediaPlayer-prepare");worker.start();}
 private void open()throws IOException{closeMedia();extractor=new MediaExtractor();extractor.setDataSource(source);boolean video=false,sound=false;duration=0;for(int i=0;i<extractor.getTrackCount();i++){MediaFormat f=extractor.getTrackFormat(i);String mime=f.getString("mime");boolean isVideo=mime.startsWith("video/"),isAudio=mime.startsWith("audio/");if((!isVideo&&!isAudio)||(isVideo&&video)||(isAudio&&sound))continue;if(isVideo&&surface==null)throw new IOException("Video requires a valid Surface");MediaCodec codec=MediaCodec.createDecoderByType(mime);try{codec.configure(f,isVideo?surface:null,null,0);codec.start();}catch(RuntimeException e){codec.release();throw e;}codecs.put(i,codec);extractor.selectTrack(i);duration=Math.max(duration,f.getLong("durationUs"));if(isVideo){video=true;width=f.getInteger("width");height=f.getInteger("height");events.post(new Runnable(){public void run(){if(videoSize!=null)videoSize.onVideoSizeChanged(MediaPlayer.this,width,height);}});}else sound=true;}if(codecs.isEmpty())throw new IOException("No playable tracks");}
 public synchronized void start(){require(State.PREPARED,State.PAUSED,State.COMPLETED);boolean fresh=state!=State.PAUSED;if(state==State.COMPLETED){seek=0;}if(state==State.PAUSED){pausedTime+=System.nanoTime()-pauseStart;for(AudioTrack a:audio.values())a.play();}state=State.STARTED;notifyAll();if(fresh||worker==null||!worker.isAlive()){cancel=false;worker=new Thread(new Runnable(){public void run(){playback();}},"MediaPlayer-playback");worker.start();}}
 public synchronized void pause(){require(State.STARTED);state=State.PAUSED;pauseStart=System.nanoTime();for(AudioTrack a:audio.values())a.pause();}
 private synchronized boolean gate()throws InterruptedException{while(state==State.PAUSED&&!cancel)wait();return !cancel;}
 private void playback(){long anchor=System.nanoTime()-position*1000-pausedTime;boolean eof=false;Set<Integer> ended=new HashSet<Integer>();try{
  while(!cancel){if(!gate())break;
   long target=seek;if(target>=0){seek=-1;extractor.seekTo(target,MediaExtractor.SEEK_TO_PREVIOUS_SYNC);for(MediaCodec c:codecs.values())c.flush();for(AudioTrack a:audio.values()){a.pause();a.flush();a.play();}position=target;anchor=System.nanoTime()-target*1000-pausedTime;eof=false;ended.clear();events.post(new Runnable(){public void run(){if(seekComplete!=null)seekComplete.onSeekComplete(MediaPlayer.this);}});}
   boolean progress=false;int track=extractor.getSampleTrackIndex();if(track<0)eof=true;
   for(Map.Entry<Integer,MediaCodec> entry:codecs.entrySet()){int id=entry.getKey();MediaCodec codec=entry.getValue();if(ended.contains(id))continue;
    if(eof||track==id){int index=codec.dequeueInputBuffer(0);if(index>=0){ByteBuffer input=codec.getInputBuffer(index);int n=eof?-1:extractor.readSampleData(input,0);long pts=eof?0:extractor.getSampleTime();codec.queueInputBuffer(index,0,Math.max(0,n),Math.max(0,pts),n<0?4:0);if(!eof)extractor.advance();progress=true;}}
    MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();int out;
    while((out=codec.dequeueOutputBuffer(info,0))!=-1){progress=true;if(out==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED){MediaFormat f=codec.getOutputFormat();if(f.getString("mime").startsWith("audio/")){int channels=f.getInteger("channel-count");if(channels!=1&&channels!=2)throw new UnsupportedOperationException("MediaPlayer output supports mono/stereo PCM");AudioTrack a=new AudioTrack(3,f.getInteger("sample-rate"),channels==1?4:12,2,Math.max(4096,f.getInteger("sample-rate")*channels/5),1);a.setVolume(volume);a.play();AudioTrack old=audio.put(id,a);if(old!=null)old.release();}continue;}if(out<0)continue;
     if(info.size>0){AudioTrack a=audio.get(id);if(a!=null){synchronized(this){if(!gate())break;ByteBuffer pcm=codec.getOutputBuffer(out);int n=a.write(pcm,pcm.remaining(),0);if(n!=info.size)throw new IllegalStateException("PCM write failed: "+n);}codec.releaseOutputBuffer(out,false);}else{while(!cancel){if(!gate())break;long due=anchor+pausedTime+info.presentationTimeUs*1000;if(System.nanoTime()>=due)break;Thread.sleep(1);}synchronized(this){if(!gate())break;codec.releaseOutputBuffer(out,true);}}position=Math.max(position,info.presentationTimeUs);}
     else codec.releaseOutputBuffer(out,false);if((info.flags&4)!=0){ended.add(id);break;}
    }
   }
   if(ended.size()==codecs.size()){for(AudioTrack a:audio.values())a.stop();if(looping){seek=0;continue;}state=State.COMPLETED;events.post(new Runnable(){public void run(){if(completion!=null&&state==State.COMPLETED)completion.onCompletion(MediaPlayer.this);}});break;}
   if(!progress)Thread.sleep(1);
  }
 }catch(Exception e){if(!cancel)failure(e);}}
 private void failure(final Exception e){state=State.ERROR;System.err.println("PADBRIDGE_MEDIA_ERROR: "+e);e.printStackTrace();events.post(new Runnable(){public void run(){if(error!=null)error.onError(MediaPlayer.this,MEDIA_ERROR_UNKNOWN,e instanceof UnsupportedOperationException?MEDIA_ERROR_UNSUPPORTED:MEDIA_ERROR_IO);}});}
 private void joinWorker(){cancel=true;synchronized(this){notifyAll();}Thread w=worker;if(w!=null&&w!=Thread.currentThread())try{w.join(7000);if(w.isAlive())throw new IllegalStateException("Media worker did not stop");}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IllegalStateException(e);}worker=null;}
 private synchronized void closeMedia(){for(AudioTrack a:audio.values())a.release();audio.clear();for(MediaCodec c:codecs.values())c.release();codecs.clear();if(extractor!=null){extractor.release();extractor=null;}}
 public void stop(){require(State.STARTED,State.PAUSED,State.PREPARED,State.COMPLETED);joinWorker();closeMedia();state=State.STOPPED;position=0;}
 public void reset(){if(state==State.RELEASED)throw new IllegalStateException();joinWorker();closeMedia();state=State.IDLE;source=null;position=0;seek=-1;}
 public void release(){joinWorker();closeMedia();state=State.RELEASED;}
 public boolean isPlaying(){return state==State.STARTED;}public int getDuration(){require(State.PREPARED,State.STARTED,State.PAUSED,State.COMPLETED,State.STOPPED);return (int)Math.min(Integer.MAX_VALUE,duration/1000);}public int getCurrentPosition(){return (int)(position/1000);}public int getVideoWidth(){return width;}public int getVideoHeight(){return height;}
 public void seekTo(int milliseconds){require(State.STARTED,State.PAUSED,State.COMPLETED);if(milliseconds<0)throw new IllegalArgumentException();seek=(long)milliseconds*1000;}
 public void setLooping(boolean value){looping=value;}public boolean isLooping(){return looping;}public synchronized void setVolume(float left,float right){if(left!=right||Float.isNaN(left)||left<0||left>1)throw new UnsupportedOperationException("Equal normalized channel volume required");volume=left;for(AudioTrack a:audio.values())a.setVolume(volume);}
}
