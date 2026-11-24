package android.content.res;
import java.io.*;
import java.util.*;
public class Resources {
    public static class NotFoundException extends RuntimeException {public NotFoundException(String s){super(s);}}
    private final Map<Integer,String[]> entries=new HashMap<Integer,String[]>();
    public Resources(){try(InputStream in=getClass().getClassLoader().getResourceAsStream("padbridge/resources.tsv")){if(in!=null){BufferedReader reader=new BufferedReader(new InputStreamReader(in,"UTF-8"));String line;while((line=reader.readLine())!=null){String[] parts=line.split("\t",-1);if(parts.length!=4)throw new IOException("Invalid resource table");String[] value=new String[3];for(int i=0;i<3;i++)value[i]=new String(Base64.getDecoder().decode(parts[i+1]),"UTF-8");entries.put((int)Long.parseLong(parts[0]),value);}}}catch(IOException e){throw new NotFoundException(e.toString());}}
    public String[] bridgeEntry(int id){String[] e=entries.get(id);if(e==null)throw new NotFoundException("Resource 0x"+Integer.toHexString(id));return e;}
    public String bridgeValue(int id){Set<Integer> visited=new HashSet<Integer>();while(true){if(!visited.add(id))throw new NotFoundException("Resource reference cycle");String v=bridgeEntry(id)[2];if(v.startsWith("!unsupported"))throw new NotFoundException(v);if(!v.startsWith("@0x"))return v;id=(int)Long.parseLong(v.substring(3),16);}}
    public int getIdentifier(String name,String type,String pkg){if(name.startsWith("@"))name=name.substring(1);if(name.startsWith("0x"))return (int)Long.parseLong(name.substring(2),16);int colon=name.indexOf(':');if(colon>=0)name=name.substring(colon+1);int slash=name.indexOf('/');if(slash>=0){type=name.substring(0,slash);name=name.substring(slash+1);}for(Map.Entry<Integer,String[]> e:entries.entrySet())if(e.getValue()[0].equals(type)&&e.getValue()[1].equals(name))return e.getKey();return 0;}
    public String getString(int id){return bridgeValue(id);}public String getString(int id,Object... args){return String.format(getString(id),args);}public CharSequence getText(int id){return getString(id);}
    public int getInteger(int id){return Integer.decode(bridgeValue(id));}public boolean getBoolean(int id){return Boolean.parseBoolean(bridgeValue(id));}
    public InputStream openRawResource(int id){try{return AssetManager.bridgeOpen(bridgeValue(id));}catch(IOException e){throw new NotFoundException(e.toString());}}
    public String getResourceEntryName(int id){return bridgeEntry(id)[1];}public String getResourceTypeName(int id){return bridgeEntry(id)[0];}
    public InputStream bridgeLayout(int id){String path=bridgeValue(id);InputStream in=getClass().getClassLoader().getResourceAsStream("padbridge/xml/"+path);if(in==null)throw new NotFoundException("Unsupported or missing compiled layout: "+path);return in;}
}
