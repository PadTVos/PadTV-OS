package android.view;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.res.Resources;
public class ContextThemeWrapper extends ContextWrapper {
    private Resources.Theme theme;private int themeId;
    public ContextThemeWrapper(){super(null);}
    public ContextThemeWrapper(Context base,int id){super(base);themeId=id;}
    public ContextThemeWrapper(Context base,Resources.Theme value){super(base);if(value==null)throw new NullPointerException();theme=value;}
    public void setTheme(int id){if(themeId!=id){themeId=id;if(theme!=null)onApplyThemeResource(theme,id,false);}}
    public int getThemeResId(){return themeId;}
    public Resources.Theme getTheme(){if(theme==null){theme=getResources().newTheme();theme.setTo(getBaseContext().getTheme());if(themeId!=0)onApplyThemeResource(theme,themeId,true);}return theme;}
    protected void onApplyThemeResource(Resources.Theme value,int id,boolean first){value.applyStyle(id,true);}
}
