package android.content.res;
import java.io.*;
import java.util.*;
public class Resources {
    public static class NotFoundException extends RuntimeException {public NotFoundException(String s){super(s);}}
    private final Map<Integer,String[]> entries=new HashMap<Integer,String[]>();
    public Resources(){try(InputStream in=getClass().getClassLoader().getResourceAsStream("padbridge/resources.tsv")){if(in!=null){BufferedReader reader=new BufferedReader(new InputStreamReader(in,"UTF-8"));String line;while((line=reader.readLine())!=null){String[] parts=line.split("\t",-1);if(parts.length!=4)throw new IOException("Invalid resource table");String[] value=new String[3];for(int i=0;i<3;i++)value[i]=new String(Base64.getDecoder().decode(parts[i+1]),"UTF-8");entries.put((int)Long.parseLong(parts[0]),value);}}}catch(IOException e){throw new NotFoundException(e.toString());}}
    public String[] bridgeEntry(int id){String[] e=entries.get(id);if(e==null)throw new NotFoundException("Resource 0x"+Integer.toHexString(id));return e;}
    public Configuration getConfiguration(){return new Configuration();}
    public android.util.DisplayMetrics getDisplayMetrics(){android.util.DisplayMetrics m=new android.util.DisplayMetrics();new android.view.Display().getMetrics(m);return m;}
    static String[] typed(String value){return value.startsWith("!typed|")?value.split("\\|",4):null;}
    static String text(String[] parts){return new String(Base64.getDecoder().decode(parts[3]),java.nio.charset.StandardCharsets.UTF_8);}
    public String bridgeValue(int id){Set<Integer> visited=new HashSet<Integer>();while(true){if(!visited.add(id))throw new NotFoundException("Resource reference cycle");String v=bridgeEntry(id)[2];String[] encoded=typed(v);if(encoded!=null){int kind=Integer.parseInt(encoded[1]);v=text(encoded);if(kind==1){id=(int)Long.parseLong(encoded[2]);continue;}if(kind==2||v.startsWith("!unsupported"))throw new NotFoundException("Not a resolved scalar resource: "+id);return v;}if(v.startsWith("!"))throw new NotFoundException("Not a scalar resource: "+id);if(!v.startsWith("@0x"))return v;id=(int)Long.parseLong(v.substring(3),16);}}
    public int getIdentifier(String name,String type,String pkg){if(name.startsWith("@"))name=name.substring(1);if(name.startsWith("0x"))return (int)Long.parseLong(name.substring(2),16);int colon=name.indexOf(':');if(colon>=0)name=name.substring(colon+1);int slash=name.indexOf('/');if(slash>=0){type=name.substring(0,slash);name=name.substring(slash+1);}for(Map.Entry<Integer,String[]> e:entries.entrySet())if(e.getValue()[0].equals(type)&&e.getValue()[1].equals(name))return e.getKey();return 0;}
    public String getString(int id){return bridgeValue(id);}public String getString(int id,Object... args){return String.format(getString(id),args);}public CharSequence getText(int id){return getString(id);}
    public int getInteger(int id){return Integer.decode(bridgeValue(id));}public boolean getBoolean(int id){return Boolean.parseBoolean(bridgeValue(id));}
    public int getColor(int id){return android.graphics.Color.parseColor(bridgeValue(id));}
    public float getDimension(int id){return dimension(bridgeValue(id));}
    public int getDimensionPixelOffset(int id){return (int)getDimension(id);}
    public int getDimensionPixelSize(int id){float v=getDimension(id);int n=(int)(v+(v>=0?0.5f:-0.5f));return n!=0?n:v==0?0:v>0?1:-1;}
    float dimension(String text){String[] units={"px","dp","sp","pt","in","mm"};for(int i=0;i<units.length;i++)if(text.endsWith(units[i]))return android.util.TypedValue.applyDimension(i,Float.parseFloat(text.substring(0,text.length()-units[i].length())),getDisplayMetrics());throw new NotFoundException("Not a dimension: "+text);}
    public void getValue(int id,android.util.TypedValue out,boolean resolve){fill(bridgeEntry(id)[2],out,resolve,null,new HashSet<String>());out.resourceId=id;}
    void fill(String value,android.util.TypedValue out,boolean resolve,Theme theme,Set<String> visited){
        out.type=android.util.TypedValue.TYPE_NULL;out.data=0;out.string=null;out.resourceId=0;
        if(value==null||value.isEmpty())return;
        String[] encoded=typed(value);
        if(encoded!=null){int kind=Integer.parseInt(encoded[1]),data=(int)Long.parseLong(encoded[2]);String scalar=text(encoded);if(kind==1||kind==2)value=(kind==1?"@0x":"?0x")+Integer.toHexString(data);else{if(!(kind>=0&&kind<=6||kind>=16&&kind<=31))throw new NotFoundException("Unsupported resource value type: "+kind);out.type=kind;out.data=data;if(kind==3)out.string=scalar;return;}}
        if(value.startsWith("@0x")||value.startsWith("?0x")){int id=(int)Long.parseLong(value.substring(3),16);if(resolve){if(!visited.add(value))throw new NotFoundException("Resource/theme cycle");String next=value.charAt(0)=='@'?bridgeEntry(id)[2]:theme==null?null:theme.attributes.get(id);if(next==null)throw new NotFoundException("Unresolved theme attribute "+value);fill(next,out,true,theme,visited);if(value.charAt(0)=='@')out.resourceId=id;}else{out.type=value.charAt(0)=='@'?1:2;out.data=id;}return;}
        if(value.startsWith("!"))throw new NotFoundException("Not a scalar resource: "+value);
        if(value.startsWith("#")){out.type=28;out.data=android.graphics.Color.parseColor(value);return;}
        if(value.equals("true")||value.equals("false")){out.type=18;out.data=value.equals("true")?1:0;return;}
        String[] units={"px","dp","sp","pt","in","mm"};for(int i=0;i<units.length;i++)if(value.endsWith(units[i])){try{out.data=android.util.TypedValue.createComplexDimension(Float.parseFloat(value.substring(0,value.length()-units[i].length())),i);out.type=5;return;}catch(NumberFormatException ignored){}}
        try{out.data=Integer.decode(value);out.type=16;return;}catch(NumberFormatException ignored){}
        try{out.data=Float.floatToIntBits(Float.parseFloat(value));out.type=4;return;}catch(NumberFormatException ignored){}
        out.type=3;out.string=value;
    }
    public Theme newTheme(){return new Theme();}
    public final class Theme {
        final Map<Integer,String> attributes=new HashMap<Integer,String>();
        private void style(int id,Map<Integer,String> values,Set<Integer> visited){if(!visited.add(id)||visited.size()>64)throw new NotFoundException("Theme inheritance cycle/depth");String text=bridgeEntry(id)[2];if(!text.startsWith("!bag|"))throw new NotFoundException("Not a style: "+id);String[] fields=text.split("\\|",-1);int parent=(int)Long.parseLong(fields[1]);if(parent!=0)style(parent,values,visited);for(int i=2;i<fields.length;i++){if(fields[i].isEmpty())continue;String[] pair=fields[i].split(",",2);values.put((int)Long.parseLong(pair[0]),new String(Base64.getDecoder().decode(pair[1]),java.nio.charset.StandardCharsets.UTF_8));}}
        public void applyStyle(int id,boolean force){Map<Integer,String> values=new HashMap<Integer,String>();style(id,values,new HashSet<Integer>());for(Map.Entry<Integer,String> e:values.entrySet())if(force||!attributes.containsKey(e.getKey()))attributes.put(e.getKey(),e.getValue());}
        public boolean resolveAttribute(int id,android.util.TypedValue out,boolean refs){String value=attributes.get(id);if(value==null)return false;fill(value,out,refs,this,new HashSet<String>());return true;}
        public void setTo(Theme other){attributes.clear();attributes.putAll(other.attributes);}
        public Resources getResources(){return Resources.this;}
        public TypedArray obtainStyledAttributes(int[] attrs){return obtainStyledAttributes(null,attrs,0,0);}
        public TypedArray obtainStyledAttributes(int style,int[] attrs){Theme copy=newTheme();copy.setTo(this);copy.applyStyle(style,true);return copy.obtainStyledAttributes(attrs);}
        public TypedArray obtainStyledAttributes(android.util.AttributeSet set,int[] attrs,int defAttr,int defRes){
            Theme merged=newTheme();merged.setTo(this);int defaultStyle=defRes;
            if(defAttr!=0){android.util.TypedValue v=new android.util.TypedValue();if(resolveAttribute(defAttr,v,false)&&v.type==1)defaultStyle=v.data;}
            if(defaultStyle!=0)merged.applyStyle(defaultStyle,true);if(set!=null&&set.getStyleAttribute()!=0)merged.applyStyle(set.getStyleAttribute(),true);
            String[] values=new String[attrs.length];for(int i=0;i<attrs.length;i++){values[i]=merged.attributes.get(attrs[i]);if(set!=null){String name=bridgeEntry(attrs[i])[1];String direct=set.getAttributeValue(null,name);if(direct!=null)values[i]=direct;}}
            return new TypedArray(Resources.this,merged,values);
        }
    }
    public InputStream openRawResource(int id){try{return AssetManager.bridgeOpen(bridgeValue(id));}catch(IOException e){throw new NotFoundException(e.toString());}}
    public String getResourceEntryName(int id){return bridgeEntry(id)[1];}public String getResourceTypeName(int id){return bridgeEntry(id)[0];}
    public InputStream bridgeLayout(int id){String path=bridgeValue(id);InputStream in=getClass().getClassLoader().getResourceAsStream("padbridge/xml/"+path);if(in==null)throw new NotFoundException("Unsupported or missing compiled layout: "+path);return in;}
}
