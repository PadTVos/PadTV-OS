package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.Bundle;import android.view.*;import android.widget.FrameLayout;
public class ScrollActivity extends Activity {
    int scrolls,attached,detached,focusGained,focusLost;boolean geometryChecked;
    public void onCreate(Bundle state){super.onCreate(state);
        final FrameLayout root=new FrameLayout(this);
        final View child=new View(this){protected void onDraw(android.graphics.Canvas canvas){android.graphics.Paint paint=new android.graphics.Paint();paint.setColor(0xff00ff00);canvas.drawRect(20,0,35,30,paint);}};
        child.setBackgroundColor(0xff101010);FrameLayout.LayoutParams params=new FrameLayout.LayoutParams(80,50);params.setMargins(30,20,0,0);root.addView(child,params);
        root.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){public void onViewAttachedToWindow(View v){attached++;}public void onViewDetachedFromWindow(View v){detached++;}});
        root.getViewTreeObserver().addOnScrollChangedListener(new ViewTreeObserver.OnScrollChangedListener(){public void onScrollChanged(){scrolls++;}});
        root.getViewTreeObserver().addOnWindowFocusChangeListener(new ViewTreeObserver.OnWindowFocusChangeListener(){public void onWindowFocusChanged(boolean value){if(value)focusGained++;else focusLost++;}});
        setContentView(root);
        root.postDelayed(new Runnable(){public void run(){
            final int[] before=new int[2];child.getLocationInWindow(before);root.scrollTo(20,10);child.scrollTo(10,0);
            root.postDelayed(new Runnable(){public void run(){int[] after=new int[2];child.getLocationInWindow(after);if(child.getLeft()!=30||child.getTop()!=20||after[0]!=before[0]-20||after[1]!=before[1]-10||scrolls!=1)throw new AssertionError("Scroll geometry/callback "+scrolls);if(!hasWindowFocus()||focusGained!=1||attached!=1)throw new AssertionError("Window focus/attachment");geometryChecked=true;}},100);
        }},80);
    }
    protected void onDestroy(){super.onDestroy();if(!geometryChecked||attached!=1||detached!=1||focusGained!=1||focusLost!=1)throw new AssertionError("Detach/focus order");System.out.println("SCROLL_GEOMETRY_CANVAS_WINDOW_LIFECYCLE_OK");}
}
