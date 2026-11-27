package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.Bundle;import java.io.*;
public class XmlActivity extends Activity {
    protected void onCreate(Bundle state){super.onCreate(state);try{
        java.lang.reflect.Method parse=Class.forName("org.padtv.bridge.Xml").getMethod("parse",InputStream.class);
        org.w3c.dom.Document normal=(org.w3c.dom.Document)parse.invoke(null,new ByteArrayInputStream("<root>český &amp; text</root>".getBytes("UTF-8")));if(!normal.getDocumentElement().getTextContent().equals("český & text"))throw new AssertionError("UTF-8/entity decoding");
        String[] forbidden={"<!DOCTYPE root SYSTEM 'file:///etc/passwd'><root/>","<!DOCTYPE root [<!ENTITY x SYSTEM 'http://127.0.0.1:9/private'>]><root>&x;</root>","<!DOCTYPE root [<!ENTITY a 'bomb'><!ENTITY b '&a;&a;'>]><root>&b;</root>"};
        for(String xml:forbidden){try{parse.invoke(null,new ByteArrayInputStream(xml.getBytes("UTF-8")));throw new AssertionError("Unsafe XML accepted");}catch(java.lang.reflect.InvocationTargetException expected){if(!(expected.getCause() instanceof org.xml.sax.SAXException))throw expected;}}
        try{parse.invoke(null,new ByteArrayInputStream(new byte[]{(byte)0xff,(byte)0xfe,60,0,97,0,47,0,62,0}));throw new AssertionError("Non UTF-8 input accepted");}catch(java.lang.reflect.InvocationTargetException expected){if(!(expected.getCause() instanceof java.nio.charset.CharacterCodingException))throw expected;}
        System.out.println("XML_UTF8_DTD_EXTERNAL_ENTITIES_REJECTED_OK");
    }catch(Exception e){throw new IllegalStateException(e);}}
}
