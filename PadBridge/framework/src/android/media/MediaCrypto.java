package android.media;
/** Licensed DRM providers are not present. Never accepts a secure decoder request. */
public final class MediaCrypto {
 public MediaCrypto(java.util.UUID id,byte[] data){throw new UnsupportedOperationException("No licensed MediaCrypto provider");}
 public static boolean isCryptoSchemeSupported(java.util.UUID id){return false;}
 public void release(){}
}
