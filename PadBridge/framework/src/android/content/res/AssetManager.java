package android.content.res;
import java.io.*;
import java.util.zip.*;
public final class AssetManager {
    public InputStream open(String name) throws IOException {
        if(name.startsWith("/")||name.contains("..")||name.contains("\\"))throw new IOException("Invalid asset path");
        try(ZipFile apk=new ZipFile("/app/original.apk")) {
            ZipEntry e=apk.getEntry("assets/"+name);
            if(e==null||e.getSize()>4*1024*1024)throw new IOException("Missing asset or size exceeds 4 MiB");
            try(InputStream s=apk.getInputStream(e);ByteArrayOutputStream out=new ByteArrayOutputStream()) {
                byte[] buf=new byte[8192];int n;
                while((n=s.read(buf))!=-1) { out.write(buf,0,n);if(out.size()>4*1024*1024)throw new IOException("Asset exceeds limit"); }
                return new ByteArrayInputStream(out.toByteArray());
            }
        }
    }
}
