import argparse
import os
from pathlib import Path
import sys
import tempfile

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .ui import HomeWindow


def main():
    parser = argparse.ArgumentParser(description="PadTV — televizní prostředí")
    parser.add_argument("--preview", action="store_true", help="Nespouštět aplikace ani systémové příkazy")
    parser.add_argument("--windowed", action="store_true", help="Spustit v okně")
    parser.add_argument('--page', choices=('home','apps','store','settings','android','manage'), default='home')
    parser.add_argument("--settings", choices=("network", "bluetooth", "audio", "display", "system"), help="Otevřít nastavení")
    parser.add_argument("--screenshot", type=Path, help="Uložit PNG náhledu a skončit")
    args = parser.parse_args()
    if args.screenshot:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication([sys.argv[0]])
    app.setApplicationName("PadTV")
    app.setDesktopFileName("padtv")
    app.setStyle("Fusion")
    preview = args.preview or not sys.platform.startswith("linux") or bool(args.screenshot)
    # Screenshots use an isolated app library, never alter the user's installed apps.
    temporary = tempfile.TemporaryDirectory(prefix="padtv-preview-") if args.screenshot else None
    splash = None
    if not preview and not args.windowed:
        from .splash import StartupScreen
        splash = StartupScreen()
        splash.showFullScreen()
        app.processEvents()
    window = HomeWindow(preview=preview, apps_dir=temporary.name if temporary else None)
    window.resize(1600, 900)
    window.set_page(args.page)
    if args.windowed or args.screenshot or preview:
        window.show()
    else:
        window.showFullScreen()
    if splash:
        # Close after the home screen is mapped, without an artificial boot delay.
        QTimer.singleShot(0, splash.close)
    if args.settings:
        QTimer.singleShot(0, lambda: window.open_settings(args.settings))
    if args.screenshot:
        def capture():
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            target = window.settings_window if args.settings else window
            success = target.grab().save(str(args.screenshot))
            app.exit(0 if success else 1)
        QTimer.singleShot(200, capture)
    result = app.exec()
    if temporary:
        temporary.cleanup()
    return result


if __name__ == "__main__":
    sys.exit(main())
