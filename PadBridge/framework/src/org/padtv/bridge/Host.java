package org.padtv.bridge;

import android.app.Activity;
import android.view.View;
import android.view.KeyEvent;
import java.util.ArrayList;
import java.util.List;

public final class Host {
    public static String packageName;
    private static Activity activity;
    private static final List<View> buttons = new ArrayList<View>();
    private static int focused;
    public static void setContent(View root) {
        buttons.clear(); collect(root); focused=0;
        Native.root(root.bridgeId);
        if (!buttons.isEmpty()) Native.focus(buttons.get(0).bridgeId);
    }
    private static void collect(View view) {
        if (view instanceof android.widget.Button) buttons.add(view);
        if (view instanceof android.view.ViewGroup)
            for (View child: ((android.view.ViewGroup)view).children) collect(child);
    }
    public static void handleKey(int key) {
        if (activity.onKeyDown(key,new KeyEvent(KeyEvent.ACTION_DOWN,key))) return;
        if (buttons.isEmpty()) return;
        if (key == KeyEvent.KEYCODE_DPAD_DOWN || key == KeyEvent.KEYCODE_DPAD_RIGHT) focused=(focused+1)%buttons.size();
        else if (key == KeyEvent.KEYCODE_DPAD_UP || key == KeyEvent.KEYCODE_DPAD_LEFT) focused=(focused+buttons.size()-1)%buttons.size();
        else if (key == KeyEvent.KEYCODE_DPAD_CENTER || key == KeyEvent.KEYCODE_ENTER) buttons.get(focused).performClick();
        Native.focus(buttons.get(focused).bridgeId);
    }
    public static void click(int id) {
        for (int i=0;i<buttons.size();i++) if (buttons.get(i).bridgeId==id) {
            focused=i; Native.focus(id); buttons.get(i).performClick(); return;
        }
    }
    public static void main(String[] args) {
        try {
            packageName=args[1];
            activity=(Activity)Class.forName(args[0]).getDeclaredConstructor().newInstance();
            activity.bridgeStart();
            if (args[2].equals("headless")) {
                // Explicit test mode: runs the same Java input dispatcher without a compositor.
                java.io.File keys=new java.io.File("/data/test-keys.txt");
                if (keys.isFile()) for(String key:new String(java.nio.file.Files.readAllBytes(keys.toPath()),"UTF-8").trim().split(","))
                    if (!key.isEmpty()) handleKey(Integer.parseInt(key));
                System.out.println("PADBRIDGE_SCENE="+Native.snapshot());
            } else Native.run();
            activity.bridgeStop();
        } catch (Throwable error) {
            System.err.println("PADBRIDGE_UNSUPPORTED_OR_FAILURE: "+error);
            error.printStackTrace(System.err);
            System.exit(78);
        }
    }
}
