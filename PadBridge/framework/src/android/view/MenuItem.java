package android.view;
public interface MenuItem {
    interface OnMenuItemClickListener {boolean onMenuItemClick(MenuItem item);}
    int getItemId();int getGroupId();int getOrder();CharSequence getTitle();MenuItem setTitle(CharSequence title);MenuItem setTitle(int title);
    boolean isEnabled();MenuItem setEnabled(boolean value);boolean isVisible();MenuItem setVisible(boolean value);boolean isCheckable();MenuItem setCheckable(boolean value);boolean isChecked();MenuItem setChecked(boolean value);
    MenuItem setOnMenuItemClickListener(OnMenuItemClickListener listener);android.content.Intent getIntent();MenuItem setIntent(android.content.Intent intent);ContextMenu.ContextMenuInfo getMenuInfo();
}
