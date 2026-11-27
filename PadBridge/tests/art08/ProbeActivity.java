package org.padtv.artprobe;
public final class ProbeActivity extends android.app.Activity {
    protected void onCreate(android.os.Bundle state){super.onCreate(state);try{RuntimeProbe.main(new String[0]);}catch(Exception e){throw new IllegalStateException(e);}
        android.widget.LinearLayout root=new android.widget.LinearLayout(this);root.setOrientation(1);
        android.widget.TextView title=new android.widget.TextView(this);title.setText("Original DEX on AOSP ART");root.addView(title);
        android.widget.Button first=new android.widget.Button(this);first.setText("First");root.addView(first);
        final android.widget.Button next=new android.widget.Button(this);next.setText("Select with D-pad");root.addView(next);
        next.setOnClickListener(new android.view.View.OnClickListener(){public void onClick(android.view.View view){next.setText("ORIGINAL_ART_DPAD_CLICK");try(java.io.FileOutputStream out=openFileOutput("input.txt",MODE_PRIVATE)){out.write("ORIGINAL_ART_DPAD_CLICK".getBytes("UTF-8"));}catch(Exception e){throw new IllegalStateException(e);}}});
        setContentView(root);
        new android.os.Handler(getMainLooper()).postDelayed(new Runnable(){public void run(){System.out.println("ORIGINAL_ART_MAIN_LOOPER_CALLBACK");}},25);
    }
}
