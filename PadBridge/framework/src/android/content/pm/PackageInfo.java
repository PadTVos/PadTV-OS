package android.content.pm;
public class PackageInfo {public String packageName,versionName;public int versionCode;public ApplicationInfo applicationInfo;public ActivityInfo[] activities;public String[] requestedPermissions;public long getLongVersionCode(){return versionCode;}}
