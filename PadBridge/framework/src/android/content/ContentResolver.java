package android.content;
import android.database.Cursor;
import android.net.Uri;
import org.padtv.bridge.Manifest;
import org.w3c.dom.*;
public class ContentResolver {
    private final Context context;public ContentResolver(Context c){context=c;}
    private ContentProvider provider(Uri uri){if(!"content".equals(uri.getScheme()))throw new IllegalArgumentException("Expected content URI");return org.padtv.bridge.Providers.resolve(context,uri.getAuthority());}
    public Cursor query(Uri u,String[] p,String s,String[] a,String sort){return provider(u).query(u,p,s,a,sort);}public String getType(Uri u){return provider(u).getType(u);}public Uri insert(Uri u,ContentValues v){return provider(u).insert(u,v);}public int delete(Uri u,String s,String[] a){return provider(u).delete(u,s,a);}public int update(Uri u,ContentValues v,String s,String[] a){return provider(u).update(u,v,s,a);}
}
