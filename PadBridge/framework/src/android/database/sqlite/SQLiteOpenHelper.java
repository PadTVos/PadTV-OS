package android.database.sqlite;
import android.content.Context;
public abstract class SQLiteOpenHelper implements java.io.Closeable {
    private final Context context;private final String name;private final int version;private final SQLiteDatabase.CursorFactory factory;private SQLiteDatabase db;
    public SQLiteOpenHelper(Context c,String n,SQLiteDatabase.CursorFactory f,int v){if(v<1)throw new IllegalArgumentException("Version must be positive");context=c;name=n;version=v;factory=f;}
    public synchronized SQLiteDatabase getWritableDatabase(){if(db!=null&&db.isOpen())return db;db=SQLiteDatabase.openOrCreateDatabase(name==null?":memory:":context.getDatabasePath(name).toString(),factory);onConfigure(db);int old=db.getVersion();if(old!=version){db.beginTransaction();try{if(old==0)onCreate(db);else if(old<version)onUpgrade(db,old,version);else onDowngrade(db,old,version);db.setVersion(version);db.setTransactionSuccessful();}finally{db.endTransaction();}}onOpen(db);return db;}
    public SQLiteDatabase getReadableDatabase(){return getWritableDatabase();}public synchronized void close(){if(db!=null)db.close();db=null;}
    public abstract void onCreate(SQLiteDatabase db);public abstract void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion);public void onConfigure(SQLiteDatabase db){}public void onOpen(SQLiteDatabase db){}public void onDowngrade(SQLiteDatabase db,int oldVersion,int newVersion){throw new SQLiteException("Database downgrade unsupported");}
}
