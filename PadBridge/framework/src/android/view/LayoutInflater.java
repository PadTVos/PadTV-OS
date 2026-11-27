package android.view;
import android.content.Context;
import android.widget.*;
import org.w3c.dom.*;
import javax.xml.parsers.*;
import java.io.*;
public class LayoutInflater {
    public interface Factory{View onCreateView(String name,Context context,android.util.AttributeSet attrs);}
    public interface Factory2 extends Factory{View onCreateView(View parent,String name,Context context,android.util.AttributeSet attrs);}
    private Factory factory;private Factory2 factory2;
    public void setFactory(Factory f){if(factory!=null)throw new IllegalStateException("Factory already set");factory=f;}
    public void setFactory2(Factory2 f){setFactory(f);factory2=f;}public Factory getFactory(){return factory;}public Factory2 getFactory2(){return factory2;}public Context getContext(){return context;}
    private final Context context;public LayoutInflater(Context c){context=c;}public static LayoutInflater from(Context c){return new LayoutInflater(c);}
    public View inflate(int resource,ViewGroup root){return inflate(resource,root,root!=null);}
    public View inflate(int resource,ViewGroup root,boolean attach){try(InputStream input=context.getResources().bridgeLayout(resource)){View view=element(org.padtv.bridge.Xml.parse(input).getDocumentElement(),0,root);if(attach){if(root==null)throw new IllegalArgumentException("Attach requires root");root.addView(view);return root;}return view;}catch(RuntimeException e){throw e;}catch(Exception e){throw new IllegalStateException("Layout inflation failed",e);}}
    private int id(String value){return context.getResources().getIdentifier(value,null,context.getPackageName());}
    private String resolve(String value){return value.startsWith("@")?context.getString(id(value)):value;}
    private int size(String value){if(value.isEmpty()||value.equals("wrap_content")||value.equals("-2"))return -2;if(value.equals("match_parent")||value.equals("fill_parent")||value.equals("-1"))return -1;return Math.round(Float.parseFloat(resolve(value).replaceAll("(dp|dip|px|sp)$","")));}
    private View element(Element e,int depth,View parent)throws Exception{
        if(depth>64)throw new IllegalArgumentException("Layout nesting limit");String tag=e.getTagName();if(tag.equals("view"))tag=e.getAttribute("class");
        if(tag.equals("include"))return inflate(id(e.getAttribute("layout")),null,false);
        String cls=tag.contains(".")?tag:(tag.equals("View")?"android.view.View":"android.widget."+tag);
        android.util.AttributeSet attrs=new org.padtv.bridge.XmlAttributes(e,context.getResources());
        View v=factory2!=null?factory2.onCreateView(parent,tag,context,attrs):factory==null?null:factory.onCreateView(tag,context,attrs);
        if(v==null){Class<?> type=Class.forName(cls);try{v=(View)type.getConstructor(Context.class,android.util.AttributeSet.class).newInstance(context,attrs);}catch(NoSuchMethodException missing){v=(View)type.getConstructor(Context.class).newInstance(context);}}
        if(e.hasAttribute("id"))v.setId(id(e.getAttribute("id")));
        int w=size(e.getAttribute("layout_width")),h=size(e.getAttribute("layout_height"));
        ViewGroup.MarginLayoutParams params=parent instanceof LinearLayout?new LinearLayout.LayoutParams(w,h):parent instanceof FrameLayout?new FrameLayout.LayoutParams(w,h):new ViewGroup.MarginLayoutParams(w,h);
        int margin=e.hasAttribute("layout_margin")?size(e.getAttribute("layout_margin")):0;
        params.setMargins(e.hasAttribute("layout_marginLeft")?size(e.getAttribute("layout_marginLeft")):margin,e.hasAttribute("layout_marginTop")?size(e.getAttribute("layout_marginTop")):margin,e.hasAttribute("layout_marginRight")?size(e.getAttribute("layout_marginRight")):margin,e.hasAttribute("layout_marginBottom")?size(e.getAttribute("layout_marginBottom")):margin);
        if(e.hasAttribute("layout_marginStart"))params.setMarginStart(size(e.getAttribute("layout_marginStart")));if(e.hasAttribute("layout_marginEnd"))params.setMarginEnd(size(e.getAttribute("layout_marginEnd")));
        v.setLayoutParams(params);
        int pad=e.hasAttribute("padding")?size(e.getAttribute("padding")):0;
        v.setPadding(e.hasAttribute("paddingLeft")?size(e.getAttribute("paddingLeft")):pad,e.hasAttribute("paddingTop")?size(e.getAttribute("paddingTop")):pad,e.hasAttribute("paddingRight")?size(e.getAttribute("paddingRight")):pad,e.hasAttribute("paddingBottom")?size(e.getAttribute("paddingBottom")):pad);
        if(v instanceof LinearLayout){String o=e.getAttribute("orientation");((LinearLayout)v).setOrientation(o.equals("vertical")||o.equals("1")?1:0);}
        if(e.hasAttribute("text")){if(!(v instanceof TextView))throw new UnsupportedOperationException("text on non TextView");((TextView)v).setText(resolve(e.getAttribute("text")));}
        if(e.hasAttribute("src")&&v instanceof ImageView)((ImageView)v).setImageResource(id(e.getAttribute("src")));
        if(e.hasAttribute("onClick")){final String method=e.getAttribute("onClick");v.setOnClickListener(new View.OnClickListener(){public void onClick(View view){try{context.getClass().getMethod(method,View.class).invoke(context,view);}catch(Exception ex){throw new IllegalStateException(ex);}}});}
        if(e.hasAttribute("visibility")){String value=e.getAttribute("visibility");v.setVisibility(value.equals("gone")||value.equals("8")?8:value.equals("invisible")||value.equals("4")?4:0);}
        if(e.hasAttribute("background")&&e.getAttribute("background").startsWith("#"))v.setBackgroundColor(android.graphics.Color.parseColor(e.getAttribute("background")));
        if(v instanceof TextView){if(e.hasAttribute("textColor")&&e.getAttribute("textColor").startsWith("#"))((TextView)v).setTextColor(android.graphics.Color.parseColor(e.getAttribute("textColor")));if(e.hasAttribute("textSize"))((TextView)v).setTextSize(size(e.getAttribute("textSize")));}
        NodeList children=e.getChildNodes();for(int i=0;i<children.getLength();i++)if(children.item(i) instanceof Element){if(!(v instanceof ViewGroup))throw new IllegalArgumentException("Child on leaf view");((ViewGroup)v).addView(element((Element)children.item(i),depth+1,v));}
        return v;
    }
}
