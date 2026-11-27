package android.content.res;
import android.util.TypedValue;
public final class TypedArray {
    private final Resources resources;private final Resources.Theme theme;private final String[] values;private boolean recycled;
    TypedArray(Resources r,Resources.Theme t,String[] v){resources=r;theme=t;values=v;}
    private String raw(int i){if(recycled)throw new IllegalStateException("Recycled TypedArray");return values[i];}
    private TypedValue value(int i){String s=raw(i);if(s==null)return null;TypedValue out=new TypedValue();resources.fill(s,out,true,theme,new java.util.HashSet<String>());return out;}
    public int length(){return values.length;}public Resources getResources(){return resources;}
    public void recycle(){if(recycled)throw new IllegalStateException("Already recycled");recycled=true;}
    public boolean hasValue(int i){String s=raw(i);return s!=null&&!s.isEmpty();}
    public int getIndexCount(){int count=0;for(int i=0;i<length();i++)if(hasValue(i))count++;return count;}
    public int getIndex(int at){for(int i=0;i<length();i++)if(hasValue(i)&&at--==0)return i;throw new IndexOutOfBoundsException();}
    public int getType(int i){TypedValue v=value(i);return v==null?0:v.type;}
    public boolean getValue(int i,TypedValue out){if(raw(i)==null)return false;resources.fill(raw(i),out,true,theme,new java.util.HashSet<String>());return true;}
    public TypedValue peekValue(int i){return value(i);}
    public int getResourceId(int i,int fallback){String s=raw(i);if(s==null)return fallback;TypedValue v=new TypedValue();resources.fill(s,v,false,theme,new java.util.HashSet<String>());if(v.type==1)return v.data;if(v.type==2){v=value(i);if(v.resourceId!=0)return v.resourceId;}return fallback;}
    public int getInt(int i,int fallback){TypedValue v=value(i);if(v==null)return fallback;if(v.type>=16&&v.type<=31)return v.data;throw new Resources.NotFoundException("Expected integer attribute");}
    public int getInteger(int i,int fallback){return getInt(i,fallback);}
    public boolean getBoolean(int i,boolean fallback){return getInt(i,fallback?1:0)!=0;}
    public int getColor(int i,int fallback){return getInt(i,fallback);}
    public float getFloat(int i,float fallback){TypedValue v=value(i);if(v==null)return fallback;if(v.type==4)return v.getFloat();if(v.type>=16&&v.type<=31)return v.data;throw new Resources.NotFoundException("Expected float attribute");}
    public String getString(int i){TypedValue v=value(i);return v==null?null:String.valueOf(v.coerceToString());}
    public CharSequence getText(int i){return getString(i);}
    public float getDimension(int i,float fallback){TypedValue v=value(i);if(v==null)return fallback;if(v.type!=5)throw new Resources.NotFoundException("Expected dimension attribute");return v.getDimension(resources.getDisplayMetrics());}
    public int getDimensionPixelOffset(int i,int fallback){return (int)getDimension(i,fallback);}
    public int getDimensionPixelSize(int i,int fallback){TypedValue v=value(i);if(v==null)return fallback;if(v.type!=5)throw new Resources.NotFoundException("Expected dimension attribute");return TypedValue.complexToDimensionPixelSize(v.data,resources.getDisplayMetrics());}
    public int getLayoutDimension(int i,int fallback){TypedValue v=value(i);return v==null?fallback:v.type==5?getDimensionPixelSize(i,fallback):getInt(i,fallback);}
}
