package android.graphics;
public class LinearGradient extends Shader {
 private final java.awt.LinearGradientPaint paint;
 public LinearGradient(float x0,float y0,float x1,float y1,int a,int b,TileMode mode){this(x0,y0,x1,y1,new int[]{a,b},new float[]{0,1},mode);}
 public LinearGradient(float x0,float y0,float x1,float y1,int[] colors,float[] stops,TileMode mode){java.awt.Color[] c=new java.awt.Color[colors.length];for(int i=0;i<c.length;i++)c[i]=new java.awt.Color(colors[i],true);if(stops==null){stops=new float[c.length];for(int i=0;i<c.length;i++)stops[i]=(float)i/(c.length-1);}paint=new java.awt.LinearGradientPaint(x0,y0,x1,y1,stops,c,mode==TileMode.CLAMP?java.awt.MultipleGradientPaint.CycleMethod.NO_CYCLE:mode==TileMode.REPEAT?java.awt.MultipleGradientPaint.CycleMethod.REPEAT:java.awt.MultipleGradientPaint.CycleMethod.REFLECT);}
 public java.awt.Paint bridgePaint(){return paint;}
}
