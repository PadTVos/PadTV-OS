package android.view;
public interface WindowManager {
 Display getDefaultDisplay();
 class LayoutParams extends ViewGroup.LayoutParams {
  public static final int FLAG_FULLSCREEN=1024,FLAG_KEEP_SCREEN_ON=128;public int flags,type,gravity;public float alpha=1;
  public LayoutParams(){super(-1,-1);}public LayoutParams(int w,int h){super(w,h);}
 }
}
