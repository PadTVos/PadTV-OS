package android.content.res;
import java.io.*;
import java.util.zip.*;
public final class AssetManager {
    public InputStream open(String name) throws IOException {
        if(name.startsWith("/")||name.contains("..")||name.contains("\\"))throw new IOException("Invalid asset path");
        return bridgeOpen("assets/"+name);
    }
    public static InputStream bridgeOpen(String name) throws IOException {
        if(name.startsWith("/")||name.contains("..")||name.contains("\\"))throw new IOException("Invalid APK resource path");
        java.util.List<File> files=new java.util.ArrayList<File>();files.add(new File("/app/original.apk"));
        File[] splits=new File("/app/splits").listFiles();if(splits!=null){java.util.Arrays.sort(splits);for(File f:splits)if(f.getName().endsWith(".apk"))files.add(f);}
        for(File file:files)try(ZipFile apk=new ZipFile(file)) {
            ZipEntry e=apk.getEntry(name);
            if(e==null)continue;
            if(e.getSize()>4*1024*1024)throw new IOException("Asset size exceeds 4 MiB");
            try(InputStream s=apk.getInputStream(e);ByteArrayOutputStream out=new ByteArrayOutputStream()) {
                byte[] buf=new byte[8192];int n;
                while((n=s.read(buf))!=-1) { out.write(buf,0,n);if(out.size()>4*1024*1024)throw new IOException("Asset exceeds limit"); }
                return new ByteArrayInputStream(out.toByteArray());
            }
        }
        throw new FileNotFoundException(name);
    }
}
