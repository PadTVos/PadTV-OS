package android.graphics;
import java.io.*;
public final class BitmapFactory {
    public static Bitmap decodeStream(InputStream stream){
        if(stream==null)return null;
        try{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[8192];int n;
            while((n=stream.read(buf))!=-1){out.write(buf,0,n);if(out.size()>4*1024*1024)throw new IllegalArgumentException("Image exceeds 4 MiB");}
            return new Bitmap(out.toByteArray());
        }catch(IOException error){return null;}
    }
}
