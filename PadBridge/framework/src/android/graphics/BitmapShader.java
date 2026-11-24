package android.graphics;
public class BitmapShader extends Shader {
 private final java.awt.TexturePaint paint;
 public BitmapShader(Bitmap bitmap,TileMode x,TileMode y){if(x!=TileMode.REPEAT||y!=TileMode.REPEAT)throw new UnsupportedOperationException("Bitmap shader requires repeat mode");paint=new java.awt.TexturePaint(bitmap.bridgeImage,new java.awt.Rectangle(0,0,bitmap.getWidth(),bitmap.getHeight()));}
 public java.awt.Paint bridgePaint(){return paint;}
}
