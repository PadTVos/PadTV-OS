package android.widget;
import android.content.Context;
public class FrameLayout extends android.view.ViewGroup {
    public FrameLayout(Context c){super(c);org.padtv.bridge.Native.layout(bridgeId,2);}
    public static class LayoutParams extends android.view.ViewGroup.MarginLayoutParams {public int gravity;public LayoutParams(int w,int h){super(w,h);}public LayoutParams(int w,int h,int g){super(w,h);gravity=g;}}
}
