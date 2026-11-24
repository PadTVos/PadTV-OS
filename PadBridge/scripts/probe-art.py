"""Read-only host ART dependency probe; NEVER claims that DEX execution works.

Run in an isolated development environment with Debian android-libart. This is
not an execution backend and is not used to enable aosp-art in the Store.
"""
import ctypes, json
from pathlib import Path
root=Path('/usr/lib/x86_64-linux-gnu/android')
report={'probe':'Debian host ART shared library','dex_executed':False,'backend_available':False,'libraries':[]}
for name in ['liblog.so.0','libbase.so.0','libcutils.so.0','libziparchive.so.0','libbacktrace.so.0','libsigchain.so.0','libart.so.0']:
    try:
        lib=ctypes.CDLL(str(root/name),mode=ctypes.RTLD_GLOBAL)
        report['libraries'].append({'name':name,'loaded':True,'JNI_CreateJavaVM':hasattr(lib,'JNI_CreateJavaVM')})
    except OSError as error:report['libraries'].append({'name':name,'loaded':False,'error':str(error)})
report['next_required']=['Matching host ART/libbase/ICU build','AOSP host libcore boot class path and JNI libraries','JNI VM creation and direct DEX test in bubblewrap','GC/reflection/thread/native and Wayland framework integration tests']
print(json.dumps(report,indent=2))
