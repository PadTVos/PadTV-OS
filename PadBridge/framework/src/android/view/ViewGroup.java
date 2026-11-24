package android.view;
import android.content.Context;
import java.util.ArrayList;
import java.util.List;
public class ViewGroup extends View {
    public final List<View> children=new ArrayList<View>();
    public ViewGroup(Context context){super(context,0);}
    public void addView(View view,LayoutParams params){view.setLayoutParams(params);addView(view);}
    public int getChildCount(){return children.size();}public View getChildAt(int i){return children.get(i);}
    public View findViewById(int id){View result=super.findViewById(id);if(result!=null)return result;for(View child:children){result=child.findViewById(id);if(result!=null)return result;}return null;}
    public void addView(View view){if(view==this||children.contains(view))throw new IllegalArgumentException("Duplicate child");children.add(view);org.padtv.bridge.Native.child(bridgeId,view.bridgeId);}
    public static class LayoutParams {
        public static final int MATCH_PARENT=-1, WRAP_CONTENT=-2;
        public int width,height;
        public LayoutParams(int w,int h){width=w;height=h;}
    }
}
