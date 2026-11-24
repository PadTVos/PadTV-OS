import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
metadata=json.loads(subprocess.check_output(['cargo','metadata','--locked','--format-version','1'],cwd=root))
print(json.dumps([{'name':p['name'],'version':p['version'],'license':p['license'],'repository':p['repository']}
                 for p in metadata['packages']],indent=2))
