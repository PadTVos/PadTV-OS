package android.content;
import android.database.Cursor;
import android.net.Uri;
import org.padtv.bridge.Manifest;
import org.w3c.dom.*;
public class ContentResolver {
    private final Context context;private static final java.util.Map<String,ContentProvider> providers=new java.util.HashMap<String,ContentProvider>();public ContentResolver(Context c){context=c;}
    private ContentProvider provider(Uri uri){if(!"content".equals(uri.getScheme()))throw new IllegalArgumentException("Expected content URI");synchronized(providers){ContentProvider p=providers.get(uri.getAuthority());if(p!=null)return p;NodeList list=Manifest.get().getElementsByTagName("provider");for(int i=0;i<list.getLength();i++){Element e=(Element)list.item(i);if(java.util.Arrays.asList(e.getAttribute("authorities").split(";")).contains(uri.getAuthority()))try{p=(ContentProvider)Class.forName(Manifest.className(e.getAttribute("name"))).getDeclaredConstructor().newInstance();p.bridgeAttach(context);providers.put(uri.getAuthority(),p);return p;}catch(Exception ex){throw new IllegalStateException(ex);}}throw new UnsupportedOperationException("External provider unavailable: "+uri.getAuthority());}}
    public Cursor query(Uri u,String[] p,String s,String[] a,String sort){return provider(u).query(u,p,s,a,sort);}public String getType(Uri u){return provider(u).getType(u);}public Uri insert(Uri u,ContentValues v){return provider(u).insert(u,v);}public int delete(Uri u,String s,String[] a){return provider(u).delete(u,s,a);}public int update(Uri u,ContentValues v,String s,String[] a){return provider(u).update(u,v,s,a);}
}
