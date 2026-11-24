package android.graphics;
public final class Bitmap {
    private final byte[] bytes;
    Bitmap(byte[] value){bytes=value.clone();}
    public byte[] bridgeBytes(){return bytes.clone();}
}
