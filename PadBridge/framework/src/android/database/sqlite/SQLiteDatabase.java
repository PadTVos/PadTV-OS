package android.database.sqlite;
import java.io.*;
import java.sql.*;
import android.database.*;
public final class SQLiteDatabase implements java.io.Closeable {
    public interface CursorFactory {} private final Connection connection;private boolean success,transaction;
    private SQLiteDatabase(String path){try{Class.forName("org.sqlite.JDBC");connection=DriverManager.getConnection("jdbc:sqlite:"+path);}catch(Exception e){throw new SQLiteException("SQLite host driver unavailable",e);}}
    public static SQLiteDatabase openOrCreateDatabase(File file,CursorFactory factory){return openOrCreateDatabase(file.toString(),factory);}
    public static SQLiteDatabase openOrCreateDatabase(String path,CursorFactory factory){if(factory!=null)throw new UnsupportedOperationException("Custom CursorFactory unsupported");try{if(!path.equals(":memory:")){File f=new File(path).getCanonicalFile();if(!f.toPath().startsWith(new File("/data").toPath()))throw new SecurityException("Database must be private to this app");File parent=f.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("Cannot create database directory");path=f.toString();}return new SQLiteDatabase(path);}catch(IOException e){throw new SQLiteException(e.toString(),e);}}
    private PreparedStatement prepare(String sql,Object[] args)throws SQLException {PreparedStatement s=connection.prepareStatement(sql);if(args!=null)for(int i=0;i<args.length;i++)s.setObject(i+1,args[i]);return s;}
    public synchronized void execSQL(String sql){execSQL(sql,null);}public synchronized void execSQL(String sql,Object[] args){try(PreparedStatement s=prepare(sql,args)){s.execute();}catch(SQLException e){throw new SQLiteException(e.toString(),e);}}
    public synchronized Cursor rawQuery(String sql,String[] args){try(PreparedStatement s=prepare(sql,args);ResultSet r=s.executeQuery()){ResultSetMetaData m=r.getMetaData();String[] names=new String[m.getColumnCount()];for(int i=0;i<names.length;i++)names[i]=m.getColumnLabel(i+1);MatrixCursor c=new MatrixCursor(names);int count=0;while(r.next()){if(++count>100000)throw new SQLiteException("Result exceeds cursor limit");Object[] row=new Object[names.length];for(int i=0;i<row.length;i++)row[i]=r.getObject(i+1);c.addRow(row);}return c;}catch(SQLException e){throw new SQLiteException(e.toString(),e);}}
    public synchronized void beginTransaction(){if(transaction)throw new UnsupportedOperationException("Nested SQLite transactions not supported");try{connection.setAutoCommit(false);transaction=true;success=false;}catch(SQLException e){throw new SQLiteException(e.toString(),e);}}
    public synchronized void setTransactionSuccessful(){if(!transaction)throw new IllegalStateException("No transaction");success=true;}
    public synchronized void endTransaction(){if(!transaction)throw new IllegalStateException("No transaction");try{if(success)connection.commit();else connection.rollback();connection.setAutoCommit(true);transaction=false;}catch(SQLException e){throw new SQLiteException(e.toString(),e);}}
    public int getVersion(){try(Cursor c=rawQuery("PRAGMA user_version",null)){c.moveToFirst();return c.getInt(0);}}public void setVersion(int v){if(v<0)throw new IllegalArgumentException();execSQL("PRAGMA user_version="+v);}
    public boolean isOpen(){try{return !connection.isClosed();}catch(SQLException e){return false;}}public synchronized void close(){try{connection.close();}catch(SQLException e){throw new SQLiteException(e.toString(),e);}}
}
