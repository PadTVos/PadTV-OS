package android.util;
public interface AttributeSet {
    int getAttributeCount();String getAttributeName(int index);String getAttributeValue(int index);String getAttributeValue(String namespace,String name);String getPositionDescription();int getAttributeNameResource(int index);
    int getAttributeListValue(String namespace,String attribute,String[] options,int fallback);boolean getAttributeBooleanValue(String namespace,String attribute,boolean fallback);int getAttributeResourceValue(String namespace,String attribute,int fallback);int getAttributeIntValue(String namespace,String attribute,int fallback);int getAttributeUnsignedIntValue(String namespace,String attribute,int fallback);float getAttributeFloatValue(String namespace,String attribute,float fallback);
    int getAttributeListValue(int index,String[] options,int fallback);boolean getAttributeBooleanValue(int index,boolean fallback);int getAttributeResourceValue(int index,int fallback);int getAttributeIntValue(int index,int fallback);int getAttributeUnsignedIntValue(int index,int fallback);float getAttributeFloatValue(int index,float fallback);
    String getIdAttribute();String getClassAttribute();int getIdAttributeResourceValue(int fallback);int getStyleAttribute();
}
