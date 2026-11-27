"""Probe real Debian AOSP ART dependencies and optional isolated VM creation.
A loaded shared library is not a functioning DEX backend. No APK is modified.
"""
import ctypes,ctypes.util,json,os,resource,subprocess,sys
from pathlib import Path
root=Path('/usr/lib/x86_64-linux-gnu/android')
report={'probe':'Debian AOSP host ART','dex_executed':False,'backend_available':False,'libraries':[]}
handles=[];art=None
names=[ctypes.util.find_library(n) for n in ['tinyxml2','lz4','lzma','z','icuuc','icui18n','expat']]+[str(root/n) for n in ['liblog.so.0','libbase.so.0','libcutils.so.0','libziparchive.so.0','libbacktrace.so.0','libsigchain.so.0','libnativebridge.so.0','libnativeloader.so.0','libnativehelper.so.0','libcpu_features.so.0','libart.so.0']]
for name in names:
    if name is None:continue
    try:
        lib=ctypes.CDLL(name,mode=ctypes.RTLD_GLOBAL);handles.append(lib)
        report['libraries'].append({'name':name,'loaded':True,'JNI_CreateJavaVM':hasattr(lib,'JNI_CreateJavaVM')})
        if name.endswith('/libart.so.0'):art=lib
    except OSError as error:report['libraries'].append({'name':name,'loaded':False,'error':str(error)})
if '--child-create' in sys.argv:
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    if art is None:raise SystemExit('ART cannot load')
    class Option(ctypes.Structure):_fields_=[('optionString',ctypes.c_char_p),('extraInfo',ctypes.c_void_p)]
    class Args(ctypes.Structure):_fields_=[('version',ctypes.c_int),('nOptions',ctypes.c_int),('options',ctypes.POINTER(Option)),('ignoreUnrecognized',ctypes.c_ubyte)]
    options=(Option*2)(Option(b'-Xbootclasspath:/usr/share/padbridge/art/core-oj.jar:/usr/share/padbridge/art/core-libart.jar',None),Option(b'-Xnoimage-dex2oat',None))
    args=Args(0x10006,2,options,0);vm=ctypes.c_void_p();env=ctypes.c_void_p()
    fn=art.JNI_CreateJavaVM;fn.argtypes=[ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p),ctypes.c_void_p];fn.restype=ctypes.c_int
    result=fn(ctypes.byref(vm),ctypes.byref(env),ctypes.byref(args));print(json.dumps({'JNI_CreateJavaVM_result':result,'vm_created':bool(vm.value),'dex_executed':False}),flush=True);raise SystemExit(0 if result==0 else 1)
if '--create-vm-probe' in sys.argv:
    try:
        process=subprocess.run([sys.executable,__file__,'--child-create'],capture_output=True,text=True,timeout=15)
        report['vm_probe']={'exit_code':process.returncode,'stdout':process.stdout[-4000:],'stderr':process.stderr[-8000:],'dex_executed':False}
    except subprocess.TimeoutExpired:report['vm_probe']={'timeout':True,'dex_executed':False}
report['boot_files']={n:(Path('/usr/share/padbridge/art')/n).is_file() for n in ['core-oj.jar','core-libart.jar','boot.art']}
report['next_required']=['Build matching AOSP host ART/libcore boot DEX and JNI libraries','Create VM and execute original DEX in bubblewrap','Validate GC, reflection, threads and media/framework JNI against ART']
print(json.dumps(report,indent=2))
