"""Original signed APK with a standalone main and an Android Activity entry."""
from pathlib import Path
import subprocess,hashlib
from build_runtime_fixtures import ROOT,package,TOOLS,OUT

def build():
    out=ROOT/'build/fixtures/art08';out.mkdir(exist_ok=True);classes=out/'classes';classes.mkdir(exist_ok=True)
    subprocess.run(['javac','--release','8','-cp',str(TOOLS/'android35.jar'),'-d',str(classes),*map(str,(ROOT/'tests/art08').glob('*.java'))],check=True)
    subprocess.run(['java','-cp',str(TOOLS/'r8.jar'),'com.android.tools.r8.D8','--min-api','26','--lib',str(TOOLS/'android35.jar'),'--output',str(out),*map(str,classes.rglob('*.class'))],check=True)
    package(out,'art08','org.padtv.artprobe','org.padtv.artprobe.ProbeActivity',[('classes.dex',out/'classes.dex')])
    print('ORIGINAL_PROBE_DEX_SHA256',hashlib.sha256((out/'classes.dex').read_bytes()).hexdigest())
    main=out/'main';aux=out/'secondary';main.mkdir(exist_ok=True);aux.mkdir(exist_ok=True)
    for destination,name in [(main,'SplitActivity'),(aux,'Secondary')]:
        subprocess.run(['java','-cp',str(TOOLS/'r8.jar'),'com.android.tools.r8.D8','--min-api','26','--lib',str(TOOLS/'android35.jar'),'--output',str(destination),str(classes/'org/padtv/artprobe'/(name+'.class'))],check=True)
    package(main,'art-multidex','org.padtv.artmulti','org.padtv.artprobe.SplitActivity',[('classes.dex',main/'classes.dex'),('classes2.dex',aux/'classes.dex')])
    package(main,'art-split-base','org.padtv.artsplit','org.padtv.artprobe.SplitActivity',[('classes.dex',main/'classes.dex')])
    package(aux,'art-split-feature','org.padtv.artsplit','',[('classes.dex',aux/'classes.dex')],split='feature.code')
if __name__=='__main__':build()
