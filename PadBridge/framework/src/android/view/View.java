package android.view;
import android.content.Context;
import org.padtv.bridge.Native;
public class View {
    public final int bridgeId;
    protected final Context context;
    private OnClickListener listener;
    private int id=-1;private ViewGroup.LayoutParams layoutParams=new ViewGroup.LayoutParams(-2,-2);
    public View(Context ctx){this(ctx,0);}
    protected View(Context ctx,int kind){context=ctx;bridgeId=Native.create(kind);}
    public interface OnClickListener{void onClick(View view);}
    public void setOnClickListener(OnClickListener value){listener=value;}
    public boolean performClick(){if(listener==null)return false;listener.onClick(this);return true;}
    public Context getContext(){return context;}
    public void setId(int value){id=value;}public int getId(){return id;}
    public View findViewById(int value){return value==id?this:null;}
    public void setLayoutParams(ViewGroup.LayoutParams p){layoutParams=p;Native.size(bridgeId,p.width,p.height);}public ViewGroup.LayoutParams getLayoutParams(){return layoutParams;}
    public boolean post(Runnable r){return new android.os.Handler(android.os.Looper.getMainLooper()).post(r);}
    public boolean postDelayed(Runnable r,long ms){return new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(r,ms);}
}
