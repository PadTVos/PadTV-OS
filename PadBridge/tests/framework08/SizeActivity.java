package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.*;import android.util.*;
public class SizeActivity extends Activity {
    protected void onCreate(Bundle state){super.onCreate(state);
        if(!Size.parseSize("1920x1080").equals(new Size(1920,1080)))throw new AssertionError("Size parser");
        SizeF size=SizeF.parseSizeF("12.5*30.25");Parcel p=Parcel.obtain();size.writeToParcel(p,0);p.writeDouble(123456.75);p.setDataPosition(0);
        if(!SizeF.CREATOR.createFromParcel(p).equals(size)||p.readDouble()!=123456.75)throw new AssertionError("SizeF binary parcel");p.recycle();
        for(float f:new float[]{Float.NaN,Float.POSITIVE_INFINITY,Float.NEGATIVE_INFINITY}){try{new SizeF(f,1);throw new AssertionError("Nonfinite accepted");}catch(IllegalArgumentException expected){}}
        try{Size.parseSize("1080bad");throw new AssertionError("Malformed accepted");}catch(NumberFormatException expected){}
        System.out.println("ORIGINAL_AOSP_SIZE_PARSE_PARCEL_FINITE_OK");
    }
}
