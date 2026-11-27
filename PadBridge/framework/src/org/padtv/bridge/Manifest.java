package org.padtv.bridge;
import org.w3c.dom.*;
public final class Manifest {
    private static Document document;
    public static synchronized Document get(){if(document==null)try(java.io.InputStream in=Manifest.class.getClassLoader().getResourceAsStream("padbridge/xml/AndroidManifest.xml")){if(in==null)throw new IllegalStateException("Decoded manifest missing");document=Xml.parse(in);}catch(Exception e){throw new IllegalStateException("Manifest parse failed",e);}return document;}
    public static String className(String n){return n.startsWith(".")?Host.packageName+n:n.contains(".")?n:Host.packageName+"."+n;}
    public static void require(String type,String name){NodeList nodes=get().getElementsByTagName(type);for(int i=0;i<nodes.getLength();i++)if(className(((Element)nodes.item(i)).getAttribute("name")).equals(name))return;throw new SecurityException("Undeclared "+type+": "+name);}
}
