package android.webkit;
public final class WebSettings {
 private final WebView view;private boolean javascript;
 WebSettings(WebView v){view=v;}
 public void setJavaScriptEnabled(boolean enabled){javascript=enabled;view.bridgeSetting(enabled);}public boolean getJavaScriptEnabled(){return javascript;}
 public void setAllowFileAccess(boolean enabled){if(enabled)throw new UnsupportedOperationException("WebView file access is unavailable");}public boolean getAllowFileAccess(){return false;}
 public void setDomStorageEnabled(boolean enabled){if(!enabled)throw new UnsupportedOperationException("Disabling Chromium DOM storage is not implemented");}
}
