package android.media;
import java.nio.ByteBuffer;
import java.util.*;
public final class MediaFormat {
 public static final String KEY_MIME="mime",KEY_WIDTH="width",KEY_HEIGHT="height",KEY_SAMPLE_RATE="sample-rate",KEY_CHANNEL_COUNT="channel-count",KEY_DURATION="durationUs",KEY_MAX_INPUT_SIZE="max-input-size",KEY_COLOR_FORMAT="color-format",KEY_PCM_ENCODING="pcm-encoding",KEY_FRAME_RATE="frame-rate",KEY_BIT_RATE="bitrate";
 private final Map<String,Object> values=new LinkedHashMap<String,Object>();
 public MediaFormat(){}
 public static MediaFormat createVideoFormat(String mime,int width,int height){MediaFormat f=new MediaFormat();f.setString(KEY_MIME,mime);f.setInteger(KEY_WIDTH,width);f.setInteger(KEY_HEIGHT,height);return f;}
 public static MediaFormat createAudioFormat(String mime,int rate,int channels){MediaFormat f=new MediaFormat();f.setString(KEY_MIME,mime);f.setInteger(KEY_SAMPLE_RATE,rate);f.setInteger(KEY_CHANNEL_COUNT,channels);return f;}
 public boolean containsKey(String key){return values.containsKey(key);}public int getInteger(String key){return ((Number)required(key)).intValue();}public int getInteger(String key,int fallback){return containsKey(key)?getInteger(key):fallback;}
 public long getLong(String key){return ((Number)required(key)).longValue();}public float getFloat(String key){return ((Number)required(key)).floatValue();}public String getString(String key){return (String)required(key);}public ByteBuffer getByteBuffer(String key){ByteBuffer b=(ByteBuffer)values.get(key);return b==null?null:b.duplicate();}
 private Object required(String key){if(!values.containsKey(key))throw new IllegalArgumentException("Missing MediaFormat key: "+key);return values.get(key);}
 public void setInteger(String k,int v){values.put(k,v);}public void setLong(String k,long v){values.put(k,v);}public void setFloat(String k,float v){values.put(k,v);}public void setString(String k,String v){values.put(k,v);}public void setByteBuffer(String k,ByteBuffer v){ByteBuffer copy=v.duplicate();byte[] data=new byte[copy.remaining()];copy.get(data);values.put(k,ByteBuffer.wrap(data));}
 MediaFormat copy(){MediaFormat f=new MediaFormat();f.values.putAll(values);return f;}
 public String toString(){return values.toString();}
}
