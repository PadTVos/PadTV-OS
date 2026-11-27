package android.webkit;
public class WebViewClient {
 public void onPageStarted(WebView view,String url,android.graphics.Bitmap favicon){}
 public void onPageFinished(WebView view,String url){}
 public void onReceivedError(WebView view,int errorCode,String description,String failingUrl){}
 public boolean shouldOverrideUrlLoading(WebView view,String url){return false;}
}
