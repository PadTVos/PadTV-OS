package android.widget;
import android.content.Context;
public class CompoundButton extends Button implements Checkable {
    public interface OnCheckedChangeListener{void onCheckedChanged(CompoundButton button,boolean checked);}
    private boolean checked,notifying;private OnCheckedChangeListener listener;
    public CompoundButton(Context c){super(c);}
    public boolean isChecked(){return checked;}public void toggle(){setChecked(!checked);}
    public void setChecked(boolean value){if(checked==value)return;checked=value;draw();if(listener!=null&&!notifying){notifying=true;try{listener.onCheckedChanged(this,checked);}finally{notifying=false;}}}
    public void setOnCheckedChangeListener(OnCheckedChangeListener value){listener=value;}
    public boolean performClick(){toggle();super.performClick();return true;}
    public void setText(CharSequence value){super.setText(value);draw();}
    private void draw(){org.padtv.bridge.Native.text(bridgeId,(checked?"[✓] ":"[ ] ")+getText());}
}
