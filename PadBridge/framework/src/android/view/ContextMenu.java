package android.view;
public interface ContextMenu extends Menu {
    interface ContextMenuInfo {}
    ContextMenu setHeaderTitle(CharSequence title);ContextMenu setHeaderTitle(int title);ContextMenu setHeaderView(View view);void clearHeader();
}
