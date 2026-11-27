package org.padtv.webprobe;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.*;
import java.io.*;
public class WebActivity extends Activity {
 private WebView view;
 protected void onCreate(Bundle state){super.onCreate(state);view=new WebView(this);view.setLayoutParams(new android.view.ViewGroup.LayoutParams(-1,-1));view.getSettings().setJavaScriptEnabled(true);view.setWebViewClient(new WebViewClient(){public void onPageFinished(WebView v,String url){v.evaluateJavascript("document.querySelector('button').focus();document.querySelector('button').click();document.title+':'+document.body.style.backgroundColor",new ValueCallback<String>(){public void onReceiveValue(String value){System.out.println("CHROMIUM_DOM_RESULT="+value);try(FileOutputStream out=openFileOutput("webview-result.txt",0)){out.write(value.getBytes("UTF-8"));}catch(Exception e){throw new IllegalStateException(e);}}});}public void onReceivedError(WebView v,int code,String text,String url){System.out.println("WEBVIEW_FAILURE="+text);try(FileOutputStream out=openFileOutput("webview-error.txt",0)){out.write(text.getBytes("UTF-8"));}catch(Exception e){throw new IllegalStateException(e);}}});setContentView(view);view.loadData("<html><title>Before</title><body style='background:rgb(20,30,40);color:white;font:48px sans-serif'><button onclick=\"document.title='ORIGINAL_WEBVIEW_JS';document.body.style.backgroundColor='rgb(10, 200, 30)'\">Execute original page JS</button></body></html>","text/html","UTF-8");}
 protected void onDestroy(){view.destroy();super.onDestroy();}
}
