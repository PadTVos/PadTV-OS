package android.widget;
import android.content.Context;
import android.view.ViewGroup;
public class LinearLayout extends ViewGroup {
    public static final int HORIZONTAL=0,VERTICAL=1;
    public LinearLayout(Context context){super(context);}
    public void setOrientation(int value){if(value!=VERTICAL)throw new UnsupportedOperationException("Only vertical LinearLayout is implemented");}
    public int getOrientation(){return VERTICAL;}
}
