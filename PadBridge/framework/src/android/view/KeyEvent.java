package android.view;
public class KeyEvent {
    public static final int ACTION_DOWN=0,ACTION_UP=1,KEYCODE_DPAD_UP=19,KEYCODE_DPAD_DOWN=20,KEYCODE_DPAD_LEFT=21,KEYCODE_DPAD_RIGHT=22,KEYCODE_DPAD_CENTER=23,KEYCODE_ENTER=66,KEYCODE_BACK=4;
    private final int action,key;
    public KeyEvent(int a,int k){action=a;key=k;}
    public int getKeyCode(){return key;}
    public int getAction(){return action;}
}
