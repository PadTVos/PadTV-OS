package android.widget;
import android.content.Context;
import android.view.ViewGroup;
public class LinearLayout extends ViewGroup {
    public static final int HORIZONTAL=0,VERTICAL=1;
    private int orientation=HORIZONTAL;
    public LinearLayout(Context context){super(context);org.padtv.bridge.Native.layout(bridgeId,HORIZONTAL);}
    public void setOrientation(int value){if(value!=VERTICAL&&value!=HORIZONTAL)throw new IllegalArgumentException("Invalid orientation");orientation=value;org.padtv.bridge.Native.layout(bridgeId,value);}
    public int getOrientation(){return orientation;}
    public static class LayoutParams extends ViewGroup.LayoutParams {public LayoutParams(int w,int h){super(w,h);}}
}
