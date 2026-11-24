package android.widget;
import android.content.Context;
import android.view.View;
import android.graphics.Bitmap;
public class ImageView extends View {
    public ImageView(Context context){super(context,3);}
    public void setImageBitmap(Bitmap bitmap){org.padtv.bridge.Native.image(bridgeId,bitmap==null?new byte[0]:bitmap.bridgeBytes());}
}
