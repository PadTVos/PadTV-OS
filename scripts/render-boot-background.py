"""Render the existing PadTV startup UI for the BIOS/UEFI boot menu."""
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PyQt6.QtGui import QFont, QFontDatabase, QImage
from PyQt6.QtWidgets import QApplication
from padtv.splash import StartupScreen

app = QApplication([])
if sys.platform == "win32":
    QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR']) / 'Fonts' / 'segoeui.ttf'))
    QFont.insertSubstitution("DejaVu Sans", "Segoe UI")
screen = StartupScreen()
screen.resize(640, 480)
screen.show()
app.processEvents()
frame = screen.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
for loader in ("isolinux", "grub-pc"):
    path = ROOT / "live" / "config" / "bootloaders" / loader / "splash.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not frame.save(str(path)):
        raise RuntimeError(f"Cannot write {path}")
screen.close()
