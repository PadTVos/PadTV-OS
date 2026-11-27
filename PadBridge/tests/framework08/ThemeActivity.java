package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.Bundle;import android.content.res.*;import android.util.TypedValue;import android.widget.TextView;
public class ThemeActivity extends Activity {
    int id(String name,String type){return getResources().getIdentifier(name,type,getPackageName());}
    public void onCreate(Bundle state){super.onCreate(state);
        int gap=id("tileGap","attr"),color=id("headlineColor","attr"),caption=id("caption","attr"),missing=id("missing","attr");
        setTheme(id("Child","style"));TypedValue v=new TypedValue();
        if(!getTheme().resolveAttribute(gap,v,true)||v.type!=TypedValue.TYPE_DIMENSION||v.getDimension(getResources().getDisplayMetrics())!=24)throw new AssertionError("dimension resolution");
        if(getTheme().resolveAttribute(missing,v,true))throw new AssertionError("missing attribute fabricated");
        TypedArray a=obtainStyledAttributes(new int[]{gap,color,caption,missing});
        if(a.getDimensionPixelSize(0,-1)!=24||a.getColor(1,0)!=0xffabcdef||!"Original resource text".equals(a.getString(2))||a.getIndexCount()!=3||a.hasValue(3))throw new AssertionError("typed attributes");
        a.recycle();try{a.getString(0);throw new AssertionError("recycled array accepted");}catch(IllegalStateException expected){}
        Resources.Theme copy=getResources().newTheme();copy.setTo(getTheme());copy.applyStyle(id("Base","style"),false);
        copy.resolveAttribute(gap,v,true);if(v.getDimension(getResources().getDisplayMetrics())!=24)throw new AssertionError("force false");
        copy.applyStyle(id("Base","style"),true);copy.resolveAttribute(gap,v,true);if(v.getDimension(getResources().getDisplayMetrics())!=12)throw new AssertionError("force true");
        getTheme().resolveAttribute(gap,v,true);if(v.getDimension(getResources().getDisplayMetrics())!=24)throw new AssertionError("theme copy isolation");
        for(String name:new String[]{"numeric","boolean_text","dimension_text","marker_text"}){getResources().getValue(id(name,"string"),v,true);if(v.type!=TypedValue.TYPE_STRING)throw new AssertionError("String type was guessed: "+name);}
        copy.applyStyle(id("Literal","style"),true);copy.resolveAttribute(caption,v,true);if(v.type!=TypedValue.TYPE_STRING||!"false".contentEquals(v.string))throw new AssertionError("Style string became boolean");
        if(!"!bag|1|bad".equals(getString(id("marker_text","string"))))throw new AssertionError("Literal value interpreted as metadata");
        try{getString(id("Base","style"));throw new AssertionError("Style accepted as scalar");}catch(Resources.NotFoundException expected){}
        TypedArray references=obtainStyledAttributes(new int[]{caption});if(references.getResourceId(0,0)!=id("title","string"))throw new AssertionError("Reference ID lost");references.recycle();
        TextView text=new TextView(this);text.setText("AOSP typed values and original style resources");setContentView(text);
        System.out.println("ORIGINAL_STYLE_THEME_TYPED_ARRAY_OK");
    }
}
