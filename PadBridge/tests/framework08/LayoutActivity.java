package org.padtv.frameworkprobe;
import android.app.Activity;
import android.os.Bundle;
import android.view.*;
import android.widget.FrameLayout;

public class LayoutActivity extends Activity {
    int layouts,late,pre,draws,changes; boolean cancelled;
    public void onCreate(Bundle state){super.onCreate(state);
        final FrameLayout root=new FrameLayout(this);root.setPadding(16,18,20,22);
        final View child=new View(this);child.setBackgroundColor(0xff0ac81e);
        FrameLayout.LayoutParams params=new FrameLayout.LayoutParams(160,90);params.setMargins(24,36,40,0);root.addView(child,params);
        child.addOnLayoutChangeListener(new View.OnLayoutChangeListener(){public void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob){changes++;}});
        final ViewTreeObserver observer=root.getViewTreeObserver();
        final ViewTreeObserver.OnGlobalLayoutListener second=new ViewTreeObserver.OnGlobalLayoutListener(){public void onGlobalLayout(){late++;}};
        observer.addOnGlobalLayoutListener(new ViewTreeObserver.OnGlobalLayoutListener(){public void onGlobalLayout(){layouts++;if(layouts==1){if(child.getLeft()!=40||child.getTop()!=54)throw new AssertionError("initial padding/margins");observer.addOnGlobalLayoutListener(second);FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)child.getLayoutParams();p.leftMargin=44;child.setLayoutParams(p);}}});
        observer.addOnPreDrawListener(new ViewTreeObserver.OnPreDrawListener(){public boolean onPreDraw(){pre++;if(pre==1){if(draws!=0)throw new AssertionError("draw before pre-draw");cancelled=true;return false;}return true;}});
        observer.addOnDrawListener(new ViewTreeObserver.OnDrawListener(){public void onDraw(){if(pre<=1)throw new AssertionError("cancelled frame was drawn");draws++;}});
        setContentView(root);
        root.postDelayed(new Runnable(){public void run(){
            if(layouts!=2||late!=1||changes!=2||!cancelled||draws==0)throw new AssertionError("events "+layouts+"/"+late+"/"+changes+"/"+draws);
            if(child.getLeft()!=60||child.getTop()!=54||child.getWidth()!=160||child.getHeight()!=90)throw new AssertionError("final geometry");
            observer.removeOnGlobalLayoutListener(second);
            ViewGroup.MarginLayoutParams rtl=new ViewGroup.MarginLayoutParams(100,50);rtl.setMargins(1,2,3,4);rtl.setMarginStart(20);rtl.setMarginEnd(30);rtl.resolveLayoutDirection(View.LAYOUT_DIRECTION_RTL);
            ViewGroup.MarginLayoutParams copy=new ViewGroup.MarginLayoutParams(rtl);if(copy.leftMargin!=30||copy.rightMargin!=20||copy.getMarginStart()!=20)throw new AssertionError("RTL/copy");
            System.out.println("REAL_LAYOUT_EVENTS_MARGINS_PREDRAW_OK");
        }},250);
    }
}
