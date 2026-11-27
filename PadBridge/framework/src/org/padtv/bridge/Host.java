package org.padtv.bridge;

import android.app.Activity;
import android.view.View;
import android.view.KeyEvent;
import java.util.ArrayList;
import java.util.List;

public final class Host {
    public static String packageName;
    public static android.app.Application application;
    private static final class AppContext extends android.content.Context {}
    private static Activity activity;
    private static final java.util.ArrayDeque<Activity> stack=new java.util.ArrayDeque<Activity>();
    public static boolean finished;
    private static final List<View> buttons = new ArrayList<View>();
    private static int focused;
    private static View focusView;
    private static View contentRoot;
    private static ContextMenuModel contextMenu;private static View savedContent,savedFocus;
    public static boolean showContextMenu(View view){closeContextMenu(null);ContextMenuModel menu=new ContextMenuModel(view.getContext(),activity);view.createContextMenu(menu);if(!menu.hasVisibleItems())return false;View panel=menu.render();savedContent=contentRoot;savedFocus=focusView;contextMenu=menu;contentRoot=panel;Native.root(panel.bridgeId);refreshFocus();if(!buttons.isEmpty())focusView(buttons.get(0));return true;}
    public static void closeContextMenu(ContextMenuModel expected){if(contextMenu==null||expected!=null&&expected!=contextMenu)return;ContextMenuModel old=contextMenu;contextMenu=null;View.bridgeDetach(contentRoot);contentRoot=savedContent;Native.root(contentRoot.bridgeId);refreshFocus();if(savedFocus!=null)focusView(savedFocus);savedContent=null;savedFocus=null;activity.onContextMenuClosed(old);}
    private static boolean firstDraw;
    private static boolean touchMode;
    private static View pressedView;private static boolean windowHasFocus;
    public static void windowFocus(boolean value){windowHasFocus=value;if(!value)pressedView=null;if(activity!=null)activity.bridgeWindowFocus(value);}
    public static boolean isInTouchMode(){return touchMode;}
    private static void touchMode(boolean value){if(touchMode==value)return;touchMode=value;if(contentRoot!=null)contentRoot.getViewTreeObserver().dispatchOnTouchModeChanged(value);}
    private static void refreshFocus(){buttons.clear();if(contentRoot!=null)collect(contentRoot);int pos=buttons.indexOf(focusView);focused=pos<0?0:pos;}
    public static void focusView(View view){View old=focusView;if(old!=null&&old!=view)old.bridgeFocus(false);focusView=view;view.bridgeFocus(true);Native.focus(view.bridgeId);if(old!=view)view.getViewTreeObserver().bridgeFocus(old,view);}
    public static void setContent(View root) {
        closeContextMenu(null);
        if(contentRoot!=null&&contentRoot!=root)View.bridgeDetach(contentRoot);
        contentRoot=root;buttons.clear(); collect(root); focused=0;
        Native.root(root.bridgeId);
        if (!buttons.isEmpty()) focusView(buttons.get(0));
    }
    private static void collect(View view) {
        if(view.getVisibility()!=View.VISIBLE||!view.isEnabled())return;
        if (view.isFocusable()) buttons.add(view);
        if (view instanceof android.view.ViewGroup)
            for (View child: ((android.view.ViewGroup)view).children) collect(child);
    }
    public static void handleKey(int key){handleKeyAction(key,KeyEvent.ACTION_DOWN);handleKeyAction(key,KeyEvent.ACTION_UP);}
    public static void handleKeyAction(int key,int action) {
        touchMode(false);
        KeyEvent event=new KeyEvent(action,key);
        if (activity.dispatchKeyEvent(event)||focusView!=null&&focusView.dispatchKeyEvent(event)){pressedView=null;return;}
        if(action==KeyEvent.ACTION_UP){View pressed=pressedView;pressedView=null;if((key==23||key==66)&&pressed!=null&&pressed==focusView)pressed.performClick();return;}
        if(action!=KeyEvent.ACTION_DOWN)throw new IllegalArgumentException("Unsupported key action");
        if(contextMenu!=null&&key==KeyEvent.KEYCODE_BACK){closeContextMenu(null);return;}
        if(key==82&&focusView!=null){focusView.showContextMenu();return;}
        if(key==KeyEvent.KEYCODE_BACK){activity.onBackPressed();return;}
        refreshFocus();
        if (buttons.isEmpty()) return;
        if (key == KeyEvent.KEYCODE_DPAD_DOWN || key == KeyEvent.KEYCODE_DPAD_RIGHT) focused=(focused+1)%buttons.size();
        else if (key == KeyEvent.KEYCODE_DPAD_UP || key == KeyEvent.KEYCODE_DPAD_LEFT) focused=(focused+buttons.size()-1)%buttons.size();
        else if (key == KeyEvent.KEYCODE_DPAD_CENTER || key == KeyEvent.KEYCODE_ENTER) pressedView=buttons.get(focused);
        focusView(buttons.get(focused));
    }
    public static void click(int id) {
        touchMode(true);
        refreshFocus();
        for (int i=0;i<buttons.size();i++) if (buttons.get(i).bridgeId==id) {
            focused=i; focusView(buttons.get(i)); buttons.get(i).performClick(); return;
        }
    }
    public static void main(String[] args) {
        try {
            Startup.phase("vm.entry");
            android.os.Looper.prepareMainLooper();
            if(args[2].equals("headless"))System.setProperty("padbridge.headless","true");
            packageName=args[1];
            org.w3c.dom.Element appNode=(org.w3c.dom.Element)Manifest.get().getElementsByTagName("application").item(0);
            String appClass=appNode==null?"":appNode.getAttribute("name");
            Startup.phase("application.construct");
            application=appClass.isEmpty()?new android.app.Application():(android.app.Application)Class.forName(Manifest.className(appClass)).getDeclaredConstructor().newInstance();
            Startup.phase("application.attach");
            application.bridgeAttach(new AppContext());
            Startup.phase("providers.initialize");
            Providers.initialize(application);
            Startup.phase("application.create");
            application.onCreate();
            Startup.phase("activity.construct");
            activity=(Activity)Class.forName(args[0]).getDeclaredConstructor().newInstance();
            Startup.phase("activity.start");
            activity.bridgeStart();
            Startup.phase("window.layout");
            if (args[2].equals("headless")) {
                Native.layoutScene(1280,720);windowFocus(true);pump();
                // Explicit test mode: runs the same Java input dispatcher without a compositor.
                java.io.File keys=new java.io.File("/data/test-keys.txt");
                if (keys.isFile()) for(String key:new String(java.nio.file.Files.readAllBytes(keys.toPath()),"UTF-8").trim().split(","))
                    if (!key.isEmpty()) handleKey(Integer.parseInt(key));
                long testDuration=500;
                java.nio.file.Path durationFile=java.nio.file.Paths.get("/data/test-duration-ms.txt");
                if(java.nio.file.Files.isRegularFile(durationFile))testDuration=Long.parseLong(new String(java.nio.file.Files.readAllBytes(durationFile),"UTF-8").trim());
                if(testDuration<500||testDuration>10000)throw new IllegalArgumentException("Headless test duration limit");
                long deadline=android.os.SystemClock.uptimeMillis()+testDuration;
                do { Native.layoutScene(1280,720);pump();Thread.sleep(5); } while(android.os.SystemClock.uptimeMillis()<deadline);
                System.out.println("PADBRIDGE_SCENE="+Native.snapshot());
            } else Native.run();
            Startup.phase("activity.stop");closeContextMenu(null);activity.bridgeStop();Startup.phase("runtime.exit");
        } catch (Throwable error) {
            Startup.failure(error);
            System.err.println("PADBRIDGE_UNSUPPORTED_OR_FAILURE: "+error);
            error.printStackTrace(System.err);
            System.exit(78);
        }
    }
    public static void pump(){android.os.Looper.getMainLooper().bridgePump();}
    public static void layout(int id,int x,int y,int width,int height){View.bridgeLayout(id,x,y,width,height);}
    public static void endLayout(){View.bridgeEndLayout(contentRoot);}
    public static boolean drawFrame(){if(contentRoot==null)return true;android.view.ViewTreeObserver o=contentRoot.getViewTreeObserver();if(o.dispatchOnPreDraw())return false;o.dispatchOnDraw();View.bridgeDraw();if(!firstDraw){firstDraw=true;Startup.phase("window.draw");}return true;}
    public static void launch(android.content.Context context,final android.content.Intent intent){final String name=Components.target(context,intent);Manifest.require("activity",name);new android.os.Handler(android.os.Looper.getMainLooper()).post(new Runnable(){public void run(){try{Activity next=(Activity)Class.forName(name).getDeclaredConstructor().newInstance();next.setIntent(intent);closeContextMenu(null);activity.bridgeWindowFocus(false);activity.bridgePause();stack.push(activity);activity=next;next.bridgeStart();windowFocus(windowHasFocus);}catch(Exception e){throw new IllegalStateException(e);}}});}
    public static void finish(final Activity current){new android.os.Handler(android.os.Looper.getMainLooper()).post(new Runnable(){public void run(){if(current!=activity)throw new UnsupportedOperationException("Finishing background Activity is unavailable");activity.bridgeStop();if(stack.isEmpty()){finished=true;}else{activity=stack.pop();activity.bridgeResume();windowFocus(windowHasFocus);}}});}
    public static boolean isFinished(){return finished;}
}
