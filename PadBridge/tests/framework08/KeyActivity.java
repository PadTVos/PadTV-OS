package org.padtv.frameworkprobe;
import android.app.Activity;import android.os.Bundle;import android.view.*;import android.widget.*;
public class KeyActivity extends Activity {
    final StringBuilder events=new StringBuilder();boolean selected;
    public void onCreate(Bundle state){super.onCreate(state);LinearLayout root=new LinearLayout(this);root.setOrientation(0);Button first=new Button(this);first.setText("Intercept right");Button second=new Button(this);second.setText("Must not receive selection");
        first.setOnKeyListener(new View.OnKeyListener(){public boolean onKey(View view,int key,KeyEvent event){events.append(key).append(':').append(event.getAction()).append(',');return key==KeyEvent.KEYCODE_DPAD_RIGHT;}});
        first.setOnClickListener(new View.OnClickListener(){public void onClick(View view){if(!events.toString().equals("22:0,22:1,23:0,23:1,"))throw new AssertionError("Key order or click before key up: "+events);selected=true;System.out.println("ORIGINAL_KEY_LISTENER_DOWN_UP_CONSUMPTION_OK");}});
        second.setOnClickListener(new View.OnClickListener(){public void onClick(View view){throw new AssertionError("Consumed direction moved focus");}});root.addView(first);root.addView(second);setContentView(root);
    }
    protected void onDestroy(){super.onDestroy();if(!selected)throw new AssertionError("No original key callback");}
}
