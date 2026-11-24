package android.view;
import android.content.Context;
import org.padtv.bridge.Native;
public class View {
    public final int bridgeId;
    protected final Context context;
    private OnClickListener listener;
    public View(Context ctx){this(ctx,0);}
    protected View(Context ctx,int kind){context=ctx;bridgeId=Native.create(kind);}
    public interface OnClickListener{void onClick(View view);}
    public void setOnClickListener(OnClickListener value){listener=value;}
    public boolean performClick(){if(listener==null)return false;listener.onClick(this);return true;}
    public Context getContext(){return context;}
}
