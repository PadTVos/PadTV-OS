package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.Bundle;import android.view.*;import android.widget.Button;
public class MenuActivity extends Activity {
    public void onCreate(Bundle state){super.onCreate(state);Button button=new Button(this);button.setText("Original menu owner");registerForContextMenu(button);setContentView(button);}
    public void onCreateContextMenu(ContextMenu menu,View view,ContextMenu.ContextMenuInfo info){super.onCreateContextMenu(menu,view,info);menu.setHeaderTitle("Playback options");menu.add(4,10,1,"Dismiss");menu.add(4,20,2,"Play clip").setOnMenuItemClickListener(new MenuItem.OnMenuItemClickListener(){public boolean onMenuItemClick(MenuItem item){try(java.io.FileOutputStream out=openFileOutput("selected.txt",0)){out.write(("ORIGINAL_MENU_CALLBACK_"+item.getItemId()).getBytes("UTF-8"));}catch(Exception e){throw new IllegalStateException(e);}System.out.println("ORIGINAL_MENU_CALLBACK_"+item.getItemId());return true;}});if(menu.size()!=2||menu.findItem(20).getOrder()!=2)throw new AssertionError("Menu model");System.out.println("ORIGINAL_CONTEXT_MENU_CREATED");}
    public void onContextMenuClosed(Menu menu){System.out.println("ORIGINAL_CONTEXT_MENU_CLOSED");}
}
