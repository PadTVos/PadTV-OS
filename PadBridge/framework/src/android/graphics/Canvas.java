package android.graphics;
import java.awt.geom.*;
public class Canvas {
 private java.awt.Graphics2D graphics;private final Bitmap bitmap;private DrawFilter filter;
 private final java.util.ArrayDeque<java.awt.Graphics2D> saves=new java.util.ArrayDeque<java.awt.Graphics2D>();
 public Canvas(Bitmap b){bitmap=b;graphics=b.bridgeImage.createGraphics();}
 public int getWidth(){return bitmap.getWidth();}public int getHeight(){return bitmap.getHeight();}
 public void setDrawFilter(DrawFilter f){filter=f;}
 public void drawColor(int color){java.awt.Composite old=graphics.getComposite();graphics.setComposite(java.awt.AlphaComposite.SrcOver);graphics.setColor(new java.awt.Color(color,true));graphics.fillRect(0,0,getWidth(),getHeight());graphics.setComposite(old);}
 private void shape(java.awt.Shape s,Paint p){p.apply(graphics,filter==null?0:filter.clear,filter==null?0:filter.set);if(p.getStyle()!=Paint.Style.STROKE)graphics.fill(s);if(p.getStyle()!=Paint.Style.FILL)graphics.draw(s);}
 public void drawRect(float l,float t,float r,float b,Paint p){shape(new Rectangle2D.Float(l,t,r-l,b-t),p);}
 public void drawCircle(float x,float y,float radius,Paint p){shape(new Ellipse2D.Float(x-radius,y-radius,2*radius,2*radius),p);}
 public void drawLine(float x,float y,float x1,float y1,Paint p){p.apply(graphics,filter==null?0:filter.clear,filter==null?0:filter.set);graphics.draw(new Line2D.Float(x,y,x1,y1));}
 public void drawText(String s,float x,float y,Paint p){p.apply(graphics,filter==null?0:filter.clear,filter==null?0:filter.set);float w=p.measureText(s);graphics.drawString(s,x-(p.getTextAlign()==Paint.Align.CENTER?w/2:p.getTextAlign()==Paint.Align.RIGHT?w:0),y);}
 public int save(){saves.push(graphics);graphics=(java.awt.Graphics2D)graphics.create();return saves.size();}
 public void restore(){if(saves.isEmpty())throw new IllegalStateException("Unbalanced Canvas restore");graphics.dispose();graphics=saves.pop();}
 public void restoreToCount(int count){while(saves.size()>=count)restore();}
 public void translate(float x,float y){graphics.translate(x,y);}public void scale(float x,float y){graphics.scale(x,y);}public void rotate(float degrees){graphics.rotate(Math.toRadians(degrees));}
 public boolean clipRect(float l,float t,float r,float b){graphics.clip(new Rectangle2D.Float(l,t,r-l,b-t));return !graphics.getClipBounds().isEmpty();}
 public void drawBitmap(Bitmap b,float x,float y,Paint p){if(p!=null)p.apply(graphics,0,0);graphics.drawImage(b.bridgeImage,Math.round(x),Math.round(y),null);}
 public void bridgeDispose(){graphics.dispose();while(!saves.isEmpty())saves.pop().dispose();}
}
