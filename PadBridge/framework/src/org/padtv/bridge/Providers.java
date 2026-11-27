package org.padtv.bridge;
import android.content.*;import android.content.pm.*;import android.os.Bundle;
import org.w3c.dom.*;import java.util.*;

/** Real same-process manifest provider lifecycle, before Application.onCreate. */
public final class Providers {
    private static final Map<String,ContentProvider> instances=new HashMap<String,ContentProvider>();
    public static Bundle metadata(Element owner){
        Bundle result=null;
        for(Node node=owner.getFirstChild();node!=null;node=node.getNextSibling())if(node instanceof Element&&"meta-data".equals(node.getNodeName())){
            Element item=(Element)node;String name=item.getAttribute("name");if(name.isEmpty())throw new IllegalArgumentException("Metadata name missing");if(result==null)result=new Bundle();
            if(item.hasAttribute("resource")){String value=item.getAttribute("resource");result.putInt(name,(int)Long.parseLong(value.replace("@0x",""),16));continue;}
            String value=item.getAttribute("value"),type=item.getAttribute("padbridge-type-value");
            if("18".equals(type))result.putBoolean(name,Boolean.parseBoolean(value));
            else if("16".equals(type)||"17".equals(type))result.putInt(name,(int)Long.decode(value).longValue());
            else if("4".equals(type))result.putFloat(name,Float.parseFloat(value));
            else if("1".equals(type)&&value.startsWith("@0x"))result.putString(name,new android.content.res.Resources().getString((int)Long.parseLong(value.substring(3),16)));
            else result.putString(name,value);
        }return result;
    }
    public static void initialize(Context context){
        NodeList nodes=Manifest.get().getElementsByTagName("provider");List<ProviderInfo> list=new ArrayList<ProviderInfo>();
        try{for(int i=0;i<nodes.getLength();i++){Element e=(Element)nodes.item(i);ProviderInfo info=context.getPackageManager().getProviderInfo(new ComponentName(context.getPackageName(),Manifest.className(e.getAttribute("name"))),PackageManager.GET_META_DATA);if(info.enabled&&info.processName.equals(context.getPackageName()))list.add(info);}}
        catch(PackageManager.NameNotFoundException impossible){throw new IllegalStateException(impossible);}
        Collections.sort(list,new Comparator<ProviderInfo>(){public int compare(ProviderInfo a,ProviderInfo b){return Integer.compare(b.initOrder,a.initOrder);}});
        for(ProviderInfo info:list)create(context,info);
    }
    private static synchronized ContentProvider create(Context context,ProviderInfo info){
        ContentProvider existing=instances.get(info.name);if(existing!=null)return existing;
        try{ContentProvider provider=(ContentProvider)Class.forName(info.name).getDeclaredConstructor().newInstance();instances.put(info.name,provider);provider.attachInfo(context,info);if(provider.getContext()==null)throw new IllegalStateException("Provider did not attach its context: "+info.name);return provider;}
        catch(RuntimeException error){instances.remove(info.name);throw error;}catch(Exception error){instances.remove(info.name);throw new IllegalStateException("Provider initialization failed: "+info.name,error);}
    }
    public static ContentProvider resolve(Context context,String authority){
        NodeList nodes=Manifest.get().getElementsByTagName("provider");
        for(int i=0;i<nodes.getLength();i++){Element e=(Element)nodes.item(i);if(!Arrays.asList(e.getAttribute("authorities").split(";")).contains(authority))continue;
            try{ProviderInfo info=context.getPackageManager().getProviderInfo(new ComponentName(context.getPackageName(),Manifest.className(e.getAttribute("name"))),PackageManager.GET_META_DATA);
                if(!info.enabled||!info.processName.equals(context.getPackageName()))throw new UnsupportedOperationException("Disabled or remote-process provider: "+authority);return create(context.getApplicationContext(),info);
            }catch(PackageManager.NameNotFoundException impossible){throw new IllegalStateException(impossible);}
        }throw new UnsupportedOperationException("External provider unavailable: "+authority);
    }
}
