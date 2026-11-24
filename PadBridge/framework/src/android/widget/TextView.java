package android.widget;
import android.content.Context;
import android.view.View;
public class TextView extends View {
    private CharSequence text="";
    public TextView(Context context){this(context,1);}
    protected TextView(Context context,int kind){super(context,kind);}
    public void setText(CharSequence value){text=value==null?"":value;org.padtv.bridge.Native.text(bridgeId,text.toString());}
    public CharSequence getText(){return text;}
    public void setText(int resource){setText(context.getText(resource));}
}
