package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.*;
public class BundleActivity extends Activity {
    protected void onCreate(Bundle state){super.onCreate(state);Bundle original=new Bundle();BaseBundle base=original;base.putString("title","original");base.putInt("count",23);base.putLong("position",9000000000L);base.putBoolean("paused",true);base.putDoubleArray("points",new double[]{1.5,2.5});
        if(base.getInt("missing",7)!=7||base.getInt("title",8)!=8||base.getBoolean("missing",true)!=true||base.getLong("position")!=9000000000L)throw new AssertionError("Typed defaults");
        Bundle copy=new Bundle(original);copy.putString("title","copy");copy.remove("count");if(!original.getString("title").equals("original")||!original.containsKey("count")||copy.containsKey("count"))throw new AssertionError("Bundle map copy isolation");
        if(copy.getDoubleArray("points")!=original.getDoubleArray("points"))throw new AssertionError("Copy should preserve shallow value identity");
        Bundle nested=new Bundle();nested.putString("server","local");original.putBundle("nested",nested);if(original.getBundle("nested")!=nested)throw new AssertionError("Nested bundle");
        Bundle cloned=(Bundle)original.clone();cloned.clear();if(original.isEmpty()||!cloned.isEmpty()||!original.keySet().contains("paused"))throw new AssertionError("Clone and key set");
        try{Bundle.EMPTY.putString("bad","mutation");throw new AssertionError("EMPTY mutable");}catch(UnsupportedOperationException expected){}
        System.out.println("ORIGINAL_BASEBUNDLE_TYPES_COPY_DEFAULTS_OK");
    }
}
