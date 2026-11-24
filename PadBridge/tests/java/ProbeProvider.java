package org.padtv.runtimeprobe;
public class ProbeProvider extends android.content.ContentProvider {
    public boolean onCreate(){return true;}
    public android.database.Cursor query(android.net.Uri u,String[] p,String s,String[] a,String sort){android.database.MatrixCursor c=new android.database.MatrixCursor(new String[]{"value"});c.addRow(new Object[]{42});return c;}
    public String getType(android.net.Uri u){return "vnd.android.cursor.item/probe";}
    public android.net.Uri insert(android.net.Uri u,android.content.ContentValues v){throw new UnsupportedOperationException("Read-only test provider");}public int delete(android.net.Uri u,String s,String[] a){throw new UnsupportedOperationException("Read-only test provider");}public int update(android.net.Uri u,android.content.ContentValues v,String s,String[] a){throw new UnsupportedOperationException("Read-only test provider");}
}
