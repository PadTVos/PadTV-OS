package android.content.pm;
public class ApplicationInfo extends PackageItemInfo {public String className,sourceDir,publicSourceDir,dataDir;public int flags,uid;public static final int FLAG_SYSTEM=1;public CharSequence loadLabel(PackageManager pm){return pm.getApplicationLabel(this);}}
