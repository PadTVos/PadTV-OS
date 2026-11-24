package android.content;
import android.database.Cursor;
import android.net.Uri;
public abstract class ContentProvider {private Context context;public Context getContext(){return context;}public final void bridgeAttach(Context c){context=c;if(!onCreate())throw new IllegalStateException("Provider initialization failed");}public abstract boolean onCreate();public abstract Cursor query(Uri uri,String[] projection,String selection,String[] args,String sort);public abstract String getType(Uri uri);public abstract Uri insert(Uri uri,ContentValues values);public abstract int delete(Uri uri,String selection,String[] args);public abstract int update(Uri uri,ContentValues values,String selection,String[] args);}
