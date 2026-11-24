package android.graphics;
import java.awt.image.BufferedImage;
public class Bitmap {
 public enum Config {ALPHA_8,RGB_565,ARGB_4444,ARGB_8888}
 public enum CompressFormat {JPEG,PNG,WEBP}
 public final BufferedImage bridgeImage;
 public Bitmap(byte[] bytes){
  if(bytes.length>8388608)throw new IllegalArgumentException("Bitmap byte limit");
  try(javax.imageio.stream.ImageInputStream input=javax.imageio.ImageIO.createImageInputStream(new java.io.ByteArrayInputStream(bytes))){
   java.util.Iterator<javax.imageio.ImageReader> readers=javax.imageio.ImageIO.getImageReaders(input);
   if(!readers.hasNext())throw new IllegalArgumentException("Unsupported bitmap");
   javax.imageio.ImageReader reader=readers.next();
   try{reader.setInput(input);int w=reader.getWidth(0),h=reader.getHeight(0);if(w<1||h<1||(long)w*h>16777216)throw new IllegalArgumentException("Bitmap dimension limit");bridgeImage=reader.read(0);}
   finally{reader.dispose();}
  }catch(java.io.IOException e){throw new IllegalArgumentException("Invalid bitmap",e);}
 }
 public byte[] bridgeBytes(){java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();if(!compress(CompressFormat.PNG,100,bytes))throw new IllegalStateException("Image encoding failed");return bytes.toByteArray();}
 private Bitmap(int w,int h){if(w<1||h<1||(long)w*h>16777216)throw new IllegalArgumentException("Bitmap limit");bridgeImage=new BufferedImage(w,h,BufferedImage.TYPE_INT_ARGB);}
 public static Bitmap createBitmap(int w,int h,Config c){if(c!=Config.ARGB_8888)throw new UnsupportedOperationException("Bitmap config "+c);return new Bitmap(w,h);}
 public int getWidth(){return bridgeImage.getWidth();}public int getHeight(){return bridgeImage.getHeight();}
 public void setPixel(int x,int y,int c){bridgeImage.setRGB(x,y,c);}public int getPixel(int x,int y){return bridgeImage.getRGB(x,y);}
 public void eraseColor(int color){java.awt.Graphics2D g=bridgeImage.createGraphics();g.setComposite(java.awt.AlphaComposite.Src);g.setColor(new java.awt.Color(color,true));g.fillRect(0,0,getWidth(),getHeight());g.dispose();}
 public void setHasAlpha(boolean alpha){if(!alpha)for(int y=0;y<getHeight();y++)for(int x=0;x<getWidth();x++)setPixel(x,y,getPixel(x,y)|0xff000000);}
 public boolean hasAlpha(){return bridgeImage.getColorModel().hasAlpha();}
 public boolean compress(CompressFormat f,int quality,java.io.OutputStream out){if(f!=CompressFormat.PNG)throw new UnsupportedOperationException("Only PNG compression");try{return javax.imageio.ImageIO.write(bridgeImage,"png",out);}catch(java.io.IOException e){return false;}}
}
