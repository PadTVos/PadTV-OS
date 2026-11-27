package android.media;
public final class AudioFormat {
 public static final int ENCODING_PCM_16BIT=2,ENCODING_PCM_8BIT=3,ENCODING_PCM_FLOAT=4,CHANNEL_OUT_MONO=4,CHANNEL_OUT_STEREO=12;
 private int encoding=2,rate=48000,mask=12;private AudioFormat(){}public int getEncoding(){return encoding;}public int getSampleRate(){return rate;}public int getChannelMask(){return mask;}public int getChannelCount(){return mask==4?1:mask==12?2:Integer.bitCount(mask);}
 public static final class Builder {private final AudioFormat f=new AudioFormat();public Builder setEncoding(int v){f.encoding=v;return this;}public Builder setSampleRate(int v){f.rate=v;return this;}public Builder setChannelMask(int v){f.mask=v;return this;}public AudioFormat build(){AudioFormat copy=new AudioFormat();copy.encoding=f.encoding;copy.rate=f.rate;copy.mask=f.mask;return copy;}}
}
