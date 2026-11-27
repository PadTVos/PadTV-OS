package org.padtv.bridge;
import android.view.*;import android.content.Context;import java.util.*;
/** Text context menus rendered by the same native scene and D-pad dispatcher. */
public final class ContextMenuModel implements ContextMenu {
    private final Context context;private final android.app.Activity owner;private final ArrayList<Item> items=new ArrayList<Item>();private CharSequence title;private View header;
    public ContextMenuModel(Context c,android.app.Activity activity){context=c;owner=activity;}
    public MenuItem add(CharSequence text){return add(0,0,0,text);}public MenuItem add(int text){return add(context.getText(text));}
    public MenuItem add(int group,int id,int order,int text){return add(group,id,order,context.getText(text));}
    public MenuItem add(int group,int id,int order,CharSequence text){if(items.size()>=256)throw new IllegalStateException("Menu item limit");Item item=new Item(group,id,order,text);int at=0;while(at<items.size()&&items.get(at).order<=order)at++;items.add(at,item);return item;}
    public int size(){return items.size();}public MenuItem getItem(int index){return items.get(index);}public MenuItem findItem(int id){for(Item item:items)if(item.id==id)return item;return null;}
    public void removeItem(int id){for(int i=0;i<items.size();i++)if(items.get(i).id==id){items.remove(i);return;}}
    public void removeGroup(int group){for(Iterator<Item> it=items.iterator();it.hasNext();)if(it.next().group==group)it.remove();}public void clear(){items.clear();}
    public void close(){Host.closeContextMenu(this);}
    public void setGroupVisible(int group,boolean value){for(Item item:items)if(item.group==group)item.visible=value;}
    public void setGroupEnabled(int group,boolean value){for(Item item:items)if(item.group==group)item.enabled=value;}
    public void setGroupCheckable(int group,boolean value,boolean exclusive){for(Item item:items)if(item.group==group){item.checkable=value;item.exclusive=exclusive;}}
    public boolean hasVisibleItems(){for(Item item:items)if(item.visible)return true;return false;}
    public boolean performIdentifierAction(int id,int flags){if(flags!=0)throw new UnsupportedOperationException("Context menu action flags: "+flags);MenuItem item=findItem(id);return item!=null&&invoke((Item)item);}
    private boolean invoke(Item item){if(!item.enabled||!item.visible)return false;close();if(item.listener!=null&&item.listener.onMenuItemClick(item))return true;if(owner.onContextItemSelected(item))return true;if(item.intent!=null){context.startActivity(item.intent);return true;}return false;}
    public ContextMenu setHeaderTitle(CharSequence value){title=value;header=null;return this;}public ContextMenu setHeaderTitle(int value){return setHeaderTitle(context.getText(value));}public ContextMenu setHeaderView(View value){header=value;title=null;return this;}public void clearHeader(){title=null;header=null;}
    public View render(){android.widget.LinearLayout panel=new android.widget.LinearLayout(context);panel.setOrientation(1);panel.setPadding(32,32,32,32);panel.setBackgroundColor(0xff152329);if(header!=null)panel.addView(header);else if(title!=null){android.widget.TextView label=new android.widget.TextView(context);label.setText(title);panel.addView(label);}
        for(final Item item:items)if(item.visible){android.widget.Button button=new android.widget.Button(context);button.setText(item.title);button.setEnabled(item.enabled);button.setOnClickListener(new View.OnClickListener(){public void onClick(View view){invoke(item);}});panel.addView(button,new android.widget.LinearLayout.LayoutParams(-1,64));}return panel;}
    private final class Item implements MenuItem {
        final int group,id,order;CharSequence title;boolean enabled=true,visible=true,checkable,checked,exclusive;OnMenuItemClickListener listener;android.content.Intent intent;
        Item(int g,int i,int o,CharSequence t){group=g;id=i;order=o;title=t;}
        public int getItemId(){return id;}public int getGroupId(){return group;}public int getOrder(){return order;}public CharSequence getTitle(){return title;}public MenuItem setTitle(CharSequence value){title=value;return this;}public MenuItem setTitle(int value){return setTitle(context.getText(value));}
        public boolean isEnabled(){return enabled;}public MenuItem setEnabled(boolean value){enabled=value;return this;}public boolean isVisible(){return visible;}public MenuItem setVisible(boolean value){visible=value;return this;}public boolean isCheckable(){return checkable;}public MenuItem setCheckable(boolean value){checkable=value;return this;}public boolean isChecked(){return checked;}
        public MenuItem setChecked(boolean value){if(exclusive&&value)for(Item item:items)if(item.group==group)item.checked=false;checked=value;return this;}
        public MenuItem setOnMenuItemClickListener(OnMenuItemClickListener value){listener=value;return this;}public android.content.Intent getIntent(){return intent;}public MenuItem setIntent(android.content.Intent value){intent=value;return this;}public ContextMenuInfo getMenuInfo(){return null;}
    }
}
