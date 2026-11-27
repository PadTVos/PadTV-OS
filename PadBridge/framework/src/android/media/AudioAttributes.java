package android.media;
public final class AudioAttributes {
 public static final int USAGE_MEDIA=1,USAGE_GAME=14,CONTENT_TYPE_MOVIE=3,CONTENT_TYPE_MUSIC=2;
 private int usage=USAGE_MEDIA,content=CONTENT_TYPE_MUSIC;private AudioAttributes(){}public int getUsage(){return usage;}public int getContentType(){return content;}
 public static final class Builder {private final AudioAttributes a=new AudioAttributes();public Builder setUsage(int v){a.usage=v;return this;}public Builder setContentType(int v){a.content=v;return this;}public AudioAttributes build(){AudioAttributes c=new AudioAttributes();c.usage=a.usage;c.content=a.content;return c;}}
}
