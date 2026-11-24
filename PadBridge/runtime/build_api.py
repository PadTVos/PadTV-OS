"""Record the actual OpenJDK base signatures used by the host framework."""
import json,shutil,sys,zipfile
from pathlib import Path
from analyze import class_info
jdk=Path(shutil.which('javac')).resolve().parent.parent
api={}
with zipfile.ZipFile(jdk/'jmods/java.base.jmod') as z:
    for name in z.namelist():
        if name.startswith('classes/') and name.endswith('.class'):
            key,value=class_info(z.read(name));value['methods']=sorted(value['methods']);api[key]=value
Path(sys.argv[1]).write_text(json.dumps(api),encoding='utf-8')
