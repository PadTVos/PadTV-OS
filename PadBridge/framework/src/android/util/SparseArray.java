package android.util;
/** Sorted integer keys, Android identity-based value search and independent clone. */
public class SparseArray<E> implements Cloneable {
    private final java.util.TreeMap<Integer,E> values=new java.util.TreeMap<Integer,E>();
    public SparseArray(){}public SparseArray(int capacity){if(capacity<0)throw new IllegalArgumentException();}
    public E get(int key){return get(key,null);}public E get(int key,E fallback){return values.containsKey(key)?values.get(key):fallback;}
    public void put(int key,E value){values.put(key,value);}public void append(int key,E value){put(key,value);}
    public void delete(int key){values.remove(key);}public void remove(int key){delete(key);}
    public void removeAt(int index){delete(keyAt(index));}
    public void removeAtRange(int index,int count){for(int n=0;n<count&&index<size();n++)removeAt(index);}
    public int size(){return values.size();}public void clear(){values.clear();}
    public int keyAt(int index){return new java.util.ArrayList<Integer>(values.keySet()).get(index);}
    public E valueAt(int index){return get(keyAt(index));}public void setValueAt(int index,E value){put(keyAt(index),value);}
    public int indexOfKey(int key){return java.util.Collections.binarySearch(new java.util.ArrayList<Integer>(values.keySet()),key);}
    public int indexOfValue(E value){int i=0;for(E v:values.values()){if(v==value)return i;i++;}return -1;}
    public SparseArray<E> clone(){SparseArray<E> copy=new SparseArray<E>();copy.values.putAll(values);return copy;}
    public String toString(){return values.toString();}
}
