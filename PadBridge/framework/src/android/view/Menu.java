package android.view;
public interface Menu {
    MenuItem add(CharSequence title);MenuItem add(int title);MenuItem add(int group,int id,int order,CharSequence title);MenuItem add(int group,int id,int order,int title);
    int size();MenuItem getItem(int index);MenuItem findItem(int id);void removeItem(int id);void removeGroup(int group);void clear();void close();
    void setGroupVisible(int group,boolean visible);void setGroupEnabled(int group,boolean enabled);void setGroupCheckable(int group,boolean checkable,boolean exclusive);boolean hasVisibleItems();boolean performIdentifierAction(int id,int flags);
}
