package android.util;
public final class Base64 {
 public static final int DEFAULT=0,NO_PADDING=1,NO_WRAP=2,CRLF=4,URL_SAFE=8,NO_CLOSE=16;
 private static void flags(int flags){if((flags&~31)!=0)throw new IllegalArgumentException("Unknown Base64 flags");}
 public static byte[] decode(String value,int flags){flags(flags);String clean=value.replaceAll("[\\t\\n\\r ]","");return ((flags&URL_SAFE)!=0?java.util.Base64.getUrlDecoder():java.util.Base64.getDecoder()).decode(clean);}
 public static byte[] decode(byte[] value,int flags){return decode(new String(value,java.nio.charset.StandardCharsets.US_ASCII),flags);}
 public static byte[] decode(byte[] value,int offset,int len,int flags){if(offset<0||len<0||offset>value.length-len)throw new IllegalArgumentException();return decode(java.util.Arrays.copyOfRange(value,offset,offset+len),flags);}
 public static String encodeToString(byte[] value,int flags){return encodeToString(value,0,value.length,flags);}
 public static String encodeToString(byte[] value,int offset,int len,int flags){flags(flags);if(offset<0||len<0||offset>value.length-len)throw new IllegalArgumentException();java.util.Base64.Encoder encoder=(flags&URL_SAFE)!=0?java.util.Base64.getUrlEncoder():java.util.Base64.getEncoder();if((flags&NO_PADDING)!=0)encoder=encoder.withoutPadding();String s=encoder.encodeToString(java.util.Arrays.copyOfRange(value,offset,offset+len));if((flags&NO_WRAP)!=0||s.isEmpty())return s;StringBuilder out=new StringBuilder();String newline=(flags&CRLF)!=0?"\r\n":"\n";for(int i=0;i<s.length();i+=76)out.append(s.substring(i,Math.min(i+76,s.length()))).append(newline);return out.toString();}
 public static byte[] encode(byte[] value,int flags){return encodeToString(value,flags).getBytes(java.nio.charset.StandardCharsets.US_ASCII);}public static byte[] encode(byte[] value,int offset,int len,int flags){return encodeToString(value,offset,len,flags).getBytes(java.nio.charset.StandardCharsets.US_ASCII);}
}
