package org.padtv.bridge;
import java.io.*;import java.nio.*;import java.nio.charset.*;import javax.xml.parsers.*;import org.xml.sax.*;
/** Bounded UTF-8 XML shared by libcore/Harmony and OpenJDK/Xerces. */
public final class Xml {
    public static org.w3c.dom.Document parse(InputStream input)throws Exception {
        if(input==null)throw new IOException("XML resource missing");
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] block=new byte[8192];int n;
        while((n=input.read(block))!=-1){if(bytes.size()+n>8*1024*1024)throw new IOException("XML exceeds 8 MiB");bytes.write(block,0,n);}
        String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes.toByteArray())).toString();
        String upper=text.toUpperCase(java.util.Locale.ROOT);
        if(upper.contains("<!DOCTYPE")||upper.contains("<!ENTITY"))throw new SAXException("DTD and entity declarations are forbidden");
        if(text.startsWith("\ufeff"))text=text.substring(1);
        DocumentBuilderFactory factory=DocumentBuilderFactory.newInstance();
        // Harmony does not recognize Xerces features. The mandatory UTF-8 DTD
        // rejection above and rejecting resolver below apply with either parser.
        feature(factory,"http://apache.org/xml/features/disallow-doctype-decl",true);
        feature(factory,"http://xml.org/sax/features/external-general-entities",false);
        feature(factory,"http://xml.org/sax/features/external-parameter-entities",false);
        DocumentBuilder builder=factory.newDocumentBuilder();
        builder.setEntityResolver(new EntityResolver(){public InputSource resolveEntity(String publicId,String systemId)throws SAXException{throw new SAXException("External XML entities are forbidden");}});
        return builder.parse(new InputSource(new StringReader(text)));
    }
    private static void feature(DocumentBuilderFactory factory,String name,boolean value){try{factory.setFeature(name,value);}catch(ParserConfigurationException unsupported){/* Provider-independent mandatory protections above. */}}
}
