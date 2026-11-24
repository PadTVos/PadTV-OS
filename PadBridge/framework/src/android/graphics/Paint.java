package android.graphics;
public class Paint {
 public static final int ANTI_ALIAS_FLAG=1,FILTER_BITMAP_FLAG=2,DITHER_FLAG=4;
 public enum Style {FILL,STROKE,FILL_AND_STROKE}public enum Align {LEFT,CENTER,RIGHT}
 private int color=Color.BLACK,flags;private float width=1,size=16;private Style style=Style.FILL;private Align align=Align.LEFT;private Shader shader;private boolean subpixel;
 public Paint(){}public Paint(int f){flags=f;}public Paint(Paint p){color=p.color;flags=p.flags;width=p.width;size=p.size;style=p.style;align=p.align;shader=p.shader;subpixel=p.subpixel;}
 public void setColor(int c){color=c;}public int getColor(){return color;}public void setAlpha(int a){color=(color&0xffffff)|(a&255)<<24;}public int getAlpha(){return color>>>24;}
 public void setStyle(Style s){style=s;}public Style getStyle(){return style;}public void setStrokeWidth(float w){if(w<0)throw new IllegalArgumentException();width=w;}public float getStrokeWidth(){return width;}
 public void setTextSize(float s){if(!Float.isFinite(s)||s<0||s>4096)throw new IllegalArgumentException();size=s;}public float getTextSize(){return size;}
 public void setTextAlign(Align a){align=a;}public Align getTextAlign(){return align;}
 private void flag(int f,boolean v){flags=v?flags|f:flags&~f;}
 public void setAntiAlias(boolean v){flag(1,v);}public void setFilterBitmap(boolean v){flag(2,v);}public void setDither(boolean v){flag(4,v);}public void setSubpixelText(boolean v){subpixel=v;}
 public int getFlags(){return flags;}public void setFlags(int f){flags=f;}public Shader setShader(Shader s){Shader old=shader;shader=s;return old;}
 public java.awt.Font bridgeFont(){return new java.awt.Font("SansSerif",java.awt.Font.PLAIN,1).deriveFont(Math.max(1,size));}
 public float measureText(String s){return (float)bridgeFont().getStringBounds(s,new java.awt.font.FontRenderContext(null,(flags&1)!=0,subpixel)).getWidth();}
 void apply(java.awt.Graphics2D g,int clear,int set){int f=(flags&~clear)|set;g.setPaint(shader==null?new java.awt.Color(color,true):shader.bridgePaint());g.setStroke(new java.awt.BasicStroke(Math.max(.01f,width)));g.setFont(bridgeFont());g.setRenderingHint(java.awt.RenderingHints.KEY_ANTIALIASING,(f&1)!=0?java.awt.RenderingHints.VALUE_ANTIALIAS_ON:java.awt.RenderingHints.VALUE_ANTIALIAS_OFF);g.setRenderingHint(java.awt.RenderingHints.KEY_TEXT_ANTIALIASING,(f&1)!=0?java.awt.RenderingHints.VALUE_TEXT_ANTIALIAS_ON:java.awt.RenderingHints.VALUE_TEXT_ANTIALIAS_OFF);g.setRenderingHint(java.awt.RenderingHints.KEY_FRACTIONALMETRICS,subpixel?java.awt.RenderingHints.VALUE_FRACTIONALMETRICS_ON:java.awt.RenderingHints.VALUE_FRACTIONALMETRICS_OFF);g.setRenderingHint(java.awt.RenderingHints.KEY_DITHERING,(f&4)!=0?java.awt.RenderingHints.VALUE_DITHER_ENABLE:java.awt.RenderingHints.VALUE_DITHER_DISABLE);g.setRenderingHint(java.awt.RenderingHints.KEY_INTERPOLATION,(f&2)!=0?java.awt.RenderingHints.VALUE_INTERPOLATION_BILINEAR:java.awt.RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR);}
}
