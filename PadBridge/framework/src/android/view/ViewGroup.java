package android.view;
import android.content.Context;
import java.util.ArrayList;
import java.util.List;
public class ViewGroup extends View implements ViewParent {
    public final List<View> children=new ArrayList<View>();
    public ViewGroup(Context context){super(context,0);}
    public void addView(View view,LayoutParams params){view.setLayoutParams(params);addView(view);}
    public int getChildCount(){return children.size();}public View getChildAt(int i){return children.get(i);}
    public View findViewById(int id){View result=super.findViewById(id);if(result!=null)return result;for(View child:children){result=child.findViewById(id);if(result!=null)return result;}return null;}
    public void addView(View view){if(view==this||view==getRootView()||children.contains(view)||view.getParent()!=null)throw new IllegalArgumentException("Duplicate child or cycle");org.padtv.bridge.Native.child(bridgeId,view.bridgeId);view.bridgeParent(this);children.add(view);requestLayout();}
    public static class LayoutParams {
        public static final int MATCH_PARENT=-1, WRAP_CONTENT=-2;
        public int width,height;
        public LayoutParams(int w,int h){width=w;height=h;}
        public LayoutParams(LayoutParams p){this(p.width,p.height);}
    }
    public static class MarginLayoutParams extends LayoutParams {
        public int leftMargin,topMargin,rightMargin,bottomMargin;
        private int start=Integer.MIN_VALUE,end=Integer.MIN_VALUE,direction;
        public MarginLayoutParams(int w,int h){super(w,h);}
        public MarginLayoutParams(LayoutParams p){super(p);if(p instanceof MarginLayoutParams)copy((MarginLayoutParams)p);}
        public MarginLayoutParams(MarginLayoutParams p){super(p);copy(p);}
        private void copy(MarginLayoutParams p){leftMargin=p.leftMargin;rightMargin=p.rightMargin;topMargin=p.topMargin;bottomMargin=p.bottomMargin;start=p.start;end=p.end;direction=p.direction;}
        public void setMargins(int l,int t,int r,int b){leftMargin=l;topMargin=t;rightMargin=r;bottomMargin=b;}
        public void setMarginStart(int v){start=v;}public void setMarginEnd(int v){end=v;}
        public int getMarginStart(){return start!=Integer.MIN_VALUE?start:direction==1?rightMargin:leftMargin;}
        public int getMarginEnd(){return end!=Integer.MIN_VALUE?end:direction==1?leftMargin:rightMargin;}
        public boolean isMarginRelative(){return start!=Integer.MIN_VALUE||end!=Integer.MIN_VALUE;}
        public void setLayoutDirection(int d){direction=d;}public int getLayoutDirection(){return direction;}
        public void resolveLayoutDirection(int d){if(d!=0&&d!=1)throw new IllegalArgumentException("Invalid layout direction");direction=d;if(start!=Integer.MIN_VALUE){if(d==1)rightMargin=start;else leftMargin=start;}if(end!=Integer.MIN_VALUE){if(d==1)leftMargin=end;else rightMargin=end;}}
    }
}
