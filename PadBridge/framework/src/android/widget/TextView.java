package android.widget;
import android.content.Context;
import android.view.View;
public class TextView extends View {
    private CharSequence text="";
    private final android.graphics.Paint paint=new android.graphics.Paint(1);
    public TextView(Context context){this(context,1);}
    protected TextView(Context context,int kind){super(context,kind);paint.setColor(0xffeff7f4);paint.setTextSize(25);}
    public void setText(CharSequence value){text=value==null?"":value;org.padtv.bridge.Native.text(bridgeId,text.toString());invalidate();}
    public CharSequence getText(){return text;}
    public void setText(int resource){setText(context.getText(resource));}
    public void setTextSize(float size){setTextSize(2,size);}public void setTextSize(int unit,float size){paint.setTextSize(android.util.TypedValue.applyDimension(unit,size,new android.util.DisplayMetrics()));canvasDrawing=true;invalidate();}
    public float getTextSize(){return paint.getTextSize();}public void setTextColor(int c){paint.setColor(c);canvasDrawing=true;invalidate();}
    protected void onDraw(android.graphics.Canvas c){float y=getPaddingTop()+paint.getTextSize();for(String line:text.toString().split("\n")){c.drawText(line,getPaddingLeft(),y,paint);y+=paint.getTextSize()*1.2f;}}
}
