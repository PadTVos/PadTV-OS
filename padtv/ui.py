"""Native TV interface using the user's wallpaper and logo."""

from datetime import datetime
import getpass
import json
import os
from pathlib import Path
import sys

from PyQt6 import sip
from PyQt6.QtCore import QEvent, QPointF, QProcess, QProcessEnvironment, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from . import __version__, RELEASE_NAME
from .actions import ACTIONS, POWER_COMMANDS, command_for, executable_available
from .apps import AppLibrary, UserApp, YOUTUBE, default_data_dir
from .navigation import next_in_direction
from .store_ui import StoreMixin
from .padbridge_ui import PadBridgeMixin

WHITE = QColor("#f1f5f6")
MUTED = QColor("#9daab9")
MINT = QColor("#eff5ff")
ASSETS = Path(__file__).parent / "assets"


def font(size, bold=False):
    result = QFont("Segoe UI" if sys.platform == "win32" else "DejaVu Sans")
    result.setPixelSize(size)
    result.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    return result


def label(painter, rect, text, size=20, color=WHITE, bold=False, align=Qt.AlignmentFlag.AlignLeft):
    painter.setFont(font(size, bold))
    painter.setPen(color)
    painter.drawText(QRectF(*rect), align | Qt.AlignmentFlag.AlignVCenter, text)


def rounded(painter, rect, fill, radius=20, border=None):
    painter.setBrush(fill)
    painter.setPen(QPen(border, 1.5) if border else QPen(Qt.PenStyle.NoPen))
    painter.drawRoundedRect(QRectF(*rect), radius, radius)


def icon(p, symbol, rect, color):
    from .symbols import symbol_pixmap
    if not symbol.startswith('padbridge-icon:'):
        supplied = symbol_pixmap(symbol)
        if not supplied.isNull():
            p.drawPixmap(QRectF(*rect), supplied, QRectF(supplied.rect()))
            return
    if symbol.startswith('padbridge-icon:'):
        bitmap = QPixmap(symbol.removeprefix('padbridge-icon:'))
        if not bitmap.isNull():
            p.drawPixmap(QRectF(*rect), bitmap, QRectF(bitmap.rect()))
            return
        symbol = 'android'
    p.save()
    p.translate(rect[0], rect[1])
    p.scale(rect[2] / 48, rect[3] / 48)
    p.setPen(QPen(color, 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    if symbol == "play":
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(1, 8, 46, 32), 9, 9)
        p.setBrush(QColor("#151922"))
        path = QPainterPath(QPointF(20, 16))
        path.lineTo(32, 24)
        path.lineTo(20, 32)
        path.closeSubpath()
        p.drawPath(path)
    elif symbol == "kodi":
        p.translate(24, 24)
        p.rotate(45)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        for x, y, w, h in [(-15, -15, 13, 13), (2, -15, 13, 13), (-15, 2, 13, 13), (2, 2, 13, 13)]:
            p.drawRoundedRect(QRectF(x, y, w, h), 2, 2)
    elif symbol == "globe":
        p.drawEllipse(QRectF(4, 4, 40, 40))
        p.drawEllipse(QRectF(15, 4, 18, 40))
        p.drawLine(QPointF(5, 24), QPointF(43, 24))
        p.drawLine(QPointF(9, 13), QPointF(39, 13))
        p.drawLine(QPointF(9, 35), QPointF(39, 35))
    elif symbol == "folder":
        path = QPainterPath(QPointF(4, 14))
        for x, y in [(4, 10), (19, 10), (23, 15), (44, 15), (44, 39), (4, 39), (4, 14)]:
            path.lineTo(x, y)
        p.drawPath(path)
        p.drawLine(QPointF(5, 22), QPointF(43, 22))
    elif symbol == "audio":
        for x, h in [(7, 10), (16, 25), (25, 38), (34, 22), (43, 12)]:
            p.drawLine(QPointF(x, 24-h/2), QPointF(x, 24+h/2))
    elif symbol == "network":
        for size in [16, 30, 44]:
            p.drawArc(QRectF(24-size/2, 36-size/2, size, size), 40*16, 100*16)
        p.setBrush(color)
        p.drawEllipse(QRectF(22, 34, 4, 4))
    elif symbol == "display":
        p.drawRoundedRect(QRectF(3, 6, 42, 29), 4, 4)
        p.drawLine(QPointF(24, 35), QPointF(24, 42))
        p.drawLine(QPointF(14, 42), QPointF(34, 42))
    elif symbol == "search":
        p.drawEllipse(QRectF(7, 6, 26, 26))
        p.drawLine(QPointF(30, 30), QPointF(42, 42))
    elif symbol == "apps" or symbol == "manage":
        for x in (6, 28):
            for y in (6, 28):
                p.drawRoundedRect(QRectF(x, y, 14, 14), 3, 3)
    elif symbol == "user":
        p.drawEllipse(QRectF(4, 4, 40, 40))
        p.drawEllipse(QRectF(16, 11, 16, 16))
        p.drawArc(QRectF(11, 29, 26, 22), 0, 180*16)
    elif symbol == "settings":
        p.drawEllipse(QRectF(8, 8, 32, 32))
        p.drawEllipse(QRectF(18, 18, 12, 12))
        for x1, y1, x2, y2 in [(24, 2, 24, 9), (24, 39, 24, 46), (2, 24, 9, 24), (39, 24, 46, 24),
                                (8, 8, 13, 13), (35, 35, 40, 40), (8, 40, 13, 35), (35, 13, 40, 8)]:
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    elif symbol == "android":
        p.drawArc(QRectF(8, 10, 32, 30), 0, 180*16)
        p.drawLine(QPointF(8, 25), QPointF(40, 25))
        p.drawLine(QPointF(15, 12), QPointF(11, 5))
        p.drawLine(QPointF(33, 12), QPointF(37, 5))
        p.drawPoint(QPointF(17, 20))
        p.drawPoint(QPointF(31, 20))
        p.drawRoundedRect(QRectF(9, 29, 30, 13), 3, 3)
    elif symbol == "download":
        p.drawLine(QPointF(24, 5), QPointF(24, 31))
        p.drawLine(QPointF(13, 22), QPointF(24, 33))
        p.drawLine(QPointF(24, 33), QPointF(35, 22))
        p.drawLine(QPointF(6, 41), QPointF(42, 41))
    elif symbol == "store":
        p.setBrush(QColor('#168bf5'))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(2, 2, 44, 44), 11, 11)
        p.setPen(QPen(WHITE, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for x1,y1,x2,y2 in [(14,35,29,9),(24,9,39,35),(9,30,30,30)]:
            p.drawLine(QPointF(x1,y1), QPointF(x2,y2))
    elif symbol == "netflix":
        p.setPen(QPen(color, 8))
        for x1,y1,x2,y2 in [(14,5,14,43),(34,5,34,43),(14,5,34,43)]:
            p.drawLine(QPointF(x1,y1), QPointF(x2,y2))
    elif symbol == "video":
        p.drawRoundedRect(QRectF(3,7,42,34), 7, 7)
        path = QPainterPath(QPointF(20,16))
        path.lineTo(32,24); path.lineTo(20,32); path.closeSubpath()
        p.drawPath(path)
    elif symbol == "jellyfin":
        path = QPainterPath(QPointF(13, 5))
        path.lineTo(42, 24)
        path.lineTo(13, 43)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(21, 18), QPointF(31, 24))
        p.drawLine(QPointF(31, 24), QPointF(21, 30))
    elif symbol == "power":
        p.drawArc(QRectF(8, 8, 32, 32), 130*16, 280*16)
        p.drawLine(QPointF(24, 4), QPointF(24, 23))
    else:
        p.drawEllipse(QRectF(5, 5, 38, 38))
        label(p, (5, 5, 38, 38), "i", 30, color, True, Qt.AlignmentFlag.AlignCenter)
    p.restore()


class TVButton(QPushButton):
    def __init__(self, owner, title, rect, callback, kind="nav", subtitle="", symbol="", color="#9bf1cc"):
        super().__init__(title, owner)
        self.owner, self.design_rect = owner, rect
        self.kind, self.subtitle, self.symbol = kind, subtitle, symbol
        self.color = QColor(color)
        self.setAccessibleName(title)
        self.setAccessibleDescription(subtitle)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda checked=False: callback())
        self.installEventFilter(owner)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.design_rect[2:]
        p.scale(self.width()/w, self.height()/h)
        focused = self.hasFocus()
        active = self.text() == {"home": "Home", "apps": "Aplikace", "store": "Store", "settings": "Nastavení", "android": "Android", "manage": "Správa"}.get(self.owner.page)
        active = active or (self.kind == 'filter' and self.text() == self.owner.store_category)
        if self.kind in ("card", "dock", "store"):
            # Sample a cached blurred wallpaper beneath the translucent surface.
            # This costs no repeated blur work while moving remote focus.
            self.owner.cached_background()
            p.save()
            clip=QPainterPath()
            clip.addRoundedRect(QRectF(8,8,w-16,h-16),24,24)
            p.setClipPath(clip)
            ratio=self.owner.devicePixelRatioF()
            p.drawPixmap(QRectF(0,0,w,h),self.owner.glass_cache,
                QRectF(self.x()*ratio,self.y()*ratio,self.width()*ratio,self.height()*ratio))
            p.restore()
            fill = QLinearGradient(0, 0, 0, h)
            fill.setColorAt(0, QColor(230, 250, 255, 85 if focused else 43))
            fill.setColorAt(1, QColor(110, 145, 150, 65 if focused else 38))
            rounded(p, (8, 8, w-16, h-16), fill, 24, WHITE if focused else QColor(223, 244, 247, 65))
            if focused:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(WHITE, 3))
                p.drawRoundedRect(QRectF(5,5,w-10,h-10), 27,27)
            if self.kind == "dock":
                icon(p, self.symbol, (w/2-27, 29, 54, 54), self.color)
                label(p, (16, 96, w-32, 35), self.text(), 23, WHITE, True, Qt.AlignmentFlag.AlignCenter)
            elif self.kind == 'store':
                icon(p, self.symbol, (28,24,50,50), self.color)
                label(p, (28,84,w-56,32), self.text(), 24, WHITE, True)
                label(p, (28,120,w-56,24), self.subtitle, 15, QColor('#d0d8df'))
                rounded(p, (28,158,132,29), QColor(255,255,255,35), 14)
                label(p, (28,158,132,29), getattr(self,'store_state','Získat'), 15, WHITE, False, Qt.AlignmentFlag.AlignCenter)
            else:
                icon(p, self.symbol, (28, 28, 48, 48), self.color)
                label(p, (28, 98, w-56, 38), self.text(), 23, WHITE, True)
                label(p, (28, 145, w-56, 30), self.subtitle, 15, QColor("#d4dcde"))
        elif self.kind == "primary":
            rounded(p, (3, 3, w-6, h-6), MINT if not focused else QColor("#c7ffe6"), 29, WHITE if focused else None)
            label(p, (22, 0, w-44, h), self.text(), 19, QColor("#132b28"), True, Qt.AlignmentFlag.AlignCenter)
        elif self.kind == "power" or self.kind == "tool":
            rounded(p, (3, 3, w-6, h-6), QColor(33, 56, 48, 200), 27, MINT if focused else QColor(210, 238, 220, 50))
            icon(p, self.symbol or "power", (15, 15, w-30, h-30), MINT if focused else WHITE)
        else:
            if focused or active:
                rounded(p, (3, 3, w-6, h-6), QColor(255,255,255,45 if focused else 30), 24, WHITE if focused else QColor(255,255,255,50))
            label(p, (0, 0, w, h), self.text(), 18, MINT if active else WHITE, active, Qt.AlignmentFlag.AlignCenter)

    def contextMenuEvent(self, event):
        if getattr(self, "user_app", None):
            self.owner.app_details(self.user_app)
        else:
            super().contextMenuEvent(event)


class ChoiceDialog(QDialog):
    """Keyboard-friendly modal. Cancel is always the initial power selection."""
    def __init__(self, parent, title, message, choices):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(min(630, max(420, parent.width() - 80)))
        self.setStyleSheet("QDialog { background:#17242e; } QLabel {color:#edf4f4;font-size:20px;} "
                           "QPushButton {background:#283d43;color:#edf4f4;padding:17px 22px;border:2px solid transparent;border-radius:12px;font-size:18px;} "
                           "QPushButton:focus {border-color:#9bf1cc;background:#34534f;}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(24)
        heading = QLabel(title)
        heading.setStyleSheet("font-size:28px;font-weight:bold;color:#9bf1cc")
        layout.addWidget(heading)
        body = QLabel(message)
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(body)
        row = QHBoxLayout()
        self.buttons = []
        for title, result in choices:
            button = QPushButton(title)
            button.setAutoDefault(False)
            button.clicked.connect(lambda checked=False, value=result: self.done(value))
            button.installEventFilter(self)
            row.addWidget(button)
            self.buttons.append(button)
        layout.addLayout(row)
        self.buttons[0].setFocus()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and obj in self.buttons:
            key = event.key()
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                step = -1 if key in (Qt.Key.Key_Left, Qt.Key.Key_Up) else 1
                self.buttons[(self.buttons.index(obj)+step) % len(self.buttons)].setFocus()
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Select):
                obj.click()
                return True
            if key == Qt.Key.Key_Back:
                self.reject()
                return True
        return super().eventFilter(obj, event)


class HomeWindow(PadBridgeMixin, StoreMixin, QWidget):
    fonts_loaded = False

    def __init__(self, preview=False, apps_dir=None):
        super().__init__()
        if sys.platform == "win32" and not self.fonts_loaded:
            # The offscreen Qt plugin on Windows does not discover system fonts.
            for name in ("segoeui.ttf", "segoeuib.ttf", "seguisym.ttf"):
                QFontDatabase.addApplicationFont(str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name))
            HomeWindow.fonts_loaded = True
        self.preview, self.page = preview, "home"
        self.buttons, self.processes, self.activations = [], {}, {}
        self.app_windows_seen = set()
        self.background_cache = None
        self.background_key = None
        self.android_pending_launch = None
        self.library = AppLibrary(apps_dir if apps_dir is not None else default_data_dir(preview))
        self.init_store()
        self.wallpaper = QPixmap(str(ASSETS / "waterfall.png"))
        self.logo = QPixmap(str(ASSETS / "logo.png"))
        self.setWindowIcon(QIcon(str(ASSETS / "logo.png")))
        self.android_apps = []
        self.android_message = "Android aplikace přes Waydroid · APK pro x86 / x86_64"
        self.search_text = ""
        self.grid_page = 0
        self.notice = ""
        self.scale, self.offset = 1.0, (0.0, 0.0)
        self.setWindowTitle("PadTV")
        self.setMinimumSize(960, 540)
        self.clock = QTimer(self)
        self.clock.setSingleShot(True)
        self.clock.timeout.connect(self.refresh_clock)
        self.refresh_clock()
        self.notice_timer = QTimer(self)
        self.notice_timer.setSingleShot(True)
        self.notice_timer.timeout.connect(self.clear_notice)
        self.set_page("home")

    def refresh_clock(self):
        now = datetime.now()
        # The clock displays minutes. Repaint only its bounds at the next minute.
        if self.isActiveWindow():
            self.update(round(self.offset[0] + 1424*self.scale), round(self.offset[1] + 36*self.scale),
                        round(132*self.scale)+2, round(58*self.scale)+2)
        self.clock.start(max(1, 60000-now.second*1000-now.microsecond//1000))

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and hasattr(self, "clock"):
            if self.isActiveWindow():
                self.refresh_clock()
                if hasattr(self, 'store_process') and not self.preview:
                    QTimer.singleShot(0, self.refresh_store)
            else:
                self.clock.stop()
        super().changeEvent(event)

    def clear_notice(self):
        self.notice = ""
        self.update()

    def toast(self, message):
        self.notice = message
        self.notice_timer.start(6000)
        self.update()

    def add_button(self, title, rect, callback, **kwargs):
        button = TVButton(self, title, rect, callback, **kwargs)
        self.buttons.append(button)
        button.show()
        return button

    def set_page(self, page, grid_page=0):
        for button in self.buttons:
            button.hide()
            button.deleteLater()
        self.buttons = []
        self.page = page
        if page != "apps":
            self.search_text = ""
        for i, (title, symbol, callback) in enumerate([
            ("Hledat", "search", self.search), ("Profil", "user", self.profile),
            ("Nastavení", "settings", lambda: self.set_page("settings")), ("Napájení", "power", self.power_menu)
        ]):
            self.add_button(title, (1130+i*69, 35, 58, 58), callback, kind="tool", symbol=symbol)
        for i, (key, title) in enumerate([('home', 'Home'), ('apps', 'Aplikace'), ('store', 'Store'), ('settings', 'Nastavení')]):
            self.add_button(title, (280+i*160, 37, 155, 54), lambda selected=key: self.set_page(selected))
        if page in ('apps', 'android', 'manage'):
            for i, (key, title) in enumerate([('apps','Vše'), ('android','Android / APK'), ('manage','Správa')]):
                self.add_button(title, (66+i*200,252,190,48), lambda selected=key:self.set_page(selected))

        def system_entry(key):
            action = ACTIONS[key]
            return (action.title, action.description, action.symbol, action.color, lambda: self.launch(key), None)

        def user_entry(app, details=False):
            subtitle = {'android':'Waydroid', 'padbridge':'PadBridge · experimentální', 'flatpak':'Flathub', 'web':'Webová aplikace'}[app.kind]
            callback = (lambda: self.app_details(app)) if details else (lambda: self.launch_user(app))
            symbol = 'padbridge-icon:' + app.icon_path if app.kind == 'padbridge' and app.icon_path else app.symbol
            return (app.title, subtitle, symbol, app.color, callback, app)

        android_entry = ("Android", "Aplikace a instalace APK", "android", "#c2e5cc", lambda: self.set_page("android"), None)
        manage_entry = ("Správa aplikací", "Instalace a odinstalace", "manage", "#d5c3fa", lambda: self.set_page("manage"), None)
        installed = self.library.list()
        if page == "home":
            first = next((app for app in installed if app.target == 'com.google.android.youtube.tv'), None)
            first = first or next((app for app in installed if app.id == 'youtube'), None)
            entries = [user_entry(first)] if first else []
            netflix = next((app for app in installed if app.target == 'com.netflix.ninja'), None)
            if netflix:
                entries.append(user_entry(netflix))
            entries += [user_entry(app) for app in installed if app.kind == 'padbridge' and app not in (first, netflix)][:3]
            entries += [system_entry('browser')]
            entries += [('Store','','store','#e2e8e6',lambda:self.set_page('store'),None),
                        ('Nastavení','','settings','#e2e8e6',lambda:self.set_page('settings'),None)]
        elif page == 'store':
            categories = ['Vše','Filmy a TV','Hudba','Zábava','Nástroje','Systém','Získané']
            for i, name in enumerate(categories):
                self.add_button(name, (64+i*168,240,158,48), lambda c=name:self.select_store_category(c), kind='filter')
            self.add_button('Zdroje', (1360,145,160,48), self.store_sources)
            self.add_button('Instalovat APK', (1150,145,200,48), self.install_apk)
            self.add_button('Ukázka PadBridge', (920,145,220,48), self.install_bridge_demo)
            products = self.store_items()
            self.grid_page = min(grid_page, max(0,(len(products)-1)//8))
            for i, product in enumerate(products[self.grid_page*8:self.grid_page*8+8]):
                button = self.add_button(product.title, (64+(i%4)*370,305+(i//4)*210,354,203),
                    lambda p=product:self.store_detail(p), kind='store', subtitle=product.category + ' · ' + {'web':'Web','flatpak':'Flathub','apt':'APT','android':'Google Play','padbridge':'GitHub'}[product.kind],
                    symbol=product.symbol, color=product.color)
                button.store_state = ('Součást OS' if product.kind == 'apt' else 'Získáno' if self.product_installed(product) else 'Google Play' if product.kind == 'android' else 'Získat')
            first_card = len(self.buttons)-min(8,len(products)-self.grid_page*8)
            if self.grid_page:
                self.add_button('← Předchozí',(1110,838,180,45),lambda:self.set_page('store',self.grid_page-1))
            if (self.grid_page+1)*8<len(products):
                self.add_button('Další →',(1310,838,180,45),lambda:self.set_page('store',self.grid_page+1))
            self.position_buttons()
            if products:
                self.buttons[first_card].setFocus()
            self.update()
            if self.store_native is None and not self.store_process:
                QTimer.singleShot(0,self.refresh_store)
            return
        elif page == "apps":
            entries = [user_entry(app) for app in installed]
            entries += [system_entry(key) for key in ("browser", "files")]
            entries += [android_entry, manage_entry]
            if self.search_text:
                entries = [entry for entry in entries if self.search_text.casefold() in entry[0].casefold()]
        elif page == "settings":
            entries = [system_entry(key) for key in ("network", "audio", "display")]
            entries += [("Bluetooth", "Sluchátka, ovladače a klávesnice", "network", "#aba7ff", lambda: self.open_settings("bluetooth"), None)]
            entries += [manage_entry, android_entry, ("O systému", "Verze a zařízení", "info", "#e4d3ff", lambda: self.open_settings("system"), None)]
        elif page == "manage":
            entries = [user_entry(app, details=True) for app in installed]
            if not any(app.id == "youtube" for app in installed):
                entries.append(("Přidat YouTube", "Nainstalovat webovou aplikaci", "play", "#ff424c", self.install_youtube, None))
            entries += [("Instalovat APK", "Běžná Android aplikace", "download", "#b9d9f8", self.install_apk, None), android_entry]
        else:
            entries = [
                ("Instalovat APK", "PadBridge · experimentální runtime", "download", "#d2b9fa", self.install_apk, None),
                ("Obnovit PadBridge", "Načíst nainstalovaná APK", "apps", "#b1dace", self.refresh_bridge, None),
                ("Spustit Waydroid", "Dočasná záložní možnost", "android", "#a3e5b8", lambda: self.android_task("open"), None),
                ("Připravit Waydroid", "Záloha pro další aplikace", "settings", "#b6c5f8", self.prepare_android, None),
                ("Google Play", "Připravit oficiální obchod", "store", "#c2e5cc", lambda: self.prepare_android(google_play=True), None),
                ("APK do Waydroidu", "Instalace do záložního runtime", "download", "#d2b9fa", self.install_waydroid_apk, None),
                ("Obnovit seznam", "Načíst nainstalované aplikace", "apps", "#b1dace", self.refresh_android, None),
            ]
            entries += [user_entry(app) for app in self.android_apps]

        first_card = len(self.buttons)
        if page == "home":
            width = 1480 / len(entries)
            visible = entries
        else:
            self.grid_page = min(grid_page, max(0, (len(entries)-1)//8))
            visible = entries[self.grid_page*8:self.grid_page*8+8]
            if self.grid_page:
                self.add_button("← Předchozí", (1110, 806, 180, 45), lambda: self.set_page(page, self.grid_page-1))
            if (self.grid_page+1)*8 < len(entries):
                self.add_button("Další →", (1310, 806, 180, 45), lambda: self.set_page(page, self.grid_page+1))
            first_card = len(self.buttons)
        for i, (title, subtitle, symbol, color, callback, app) in enumerate(visible):
            rect = (60+i*width, 594, width-8, 156) if page == "home" else (64+(i % 4)*370, 325+(i//4)*229, 354, 205)
            button = self.add_button(title, rect, callback, kind="dock" if page == "home" else "card", subtitle=subtitle, symbol=symbol, color=color)
            button.user_app = app
        self.position_buttons()
        self.buttons[min(first_card, len(self.buttons)-1)].setFocus(Qt.FocusReason.OtherFocusReason)
        self.update()

    def position_buttons(self):
        self.scale = min(self.width()/1600, self.height()/900)
        self.offset = ((self.width()-1600*self.scale)/2, (self.height()-900*self.scale)/2)
        for button in self.buttons:
            x, y, w, h = button.design_rect
            button.setGeometry(round(self.offset[0]+x*self.scale), round(self.offset[1]+y*self.scale),
                               round(w*self.scale), round(h*self.scale))

    def resizeEvent(self, event):
        self.position_buttons()
        super().resizeEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and obj in self.buttons:
            key = event.key()
            directions = {Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right", Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down"}
            if key in directions:
                points = [(b.design_rect[0]+b.design_rect[2]/2, b.design_rect[1]+b.design_rect[3]/2) for b in self.buttons]
                index = next_in_direction(self.buttons.index(obj), points, directions[key])
                self.buttons[index].setFocus(Qt.FocusReason.OtherFocusReason)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Select):
                obj.click()
                return True
            if key in (Qt.Key.Key_Escape, Qt.Key.Key_Back, Qt.Key.Key_Home):
                self.set_page("home")
                return True
            if key == Qt.Key.Key_F11:
                self.showNormal() if self.isFullScreen() else self.showFullScreen()
                return True
            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Menu) and getattr(obj, "user_app", None):
                self.app_details(obj.user_app)
                return True
        return super().eventFilter(obj, event)

    def launch(self, key):
        if key in ("audio", "network", "display"):
            self.open_settings(key)
            return
        # YouTube is a removable user app, not an immutable system action.
        if key == "youtube":
            app = next((app for app in self.library.list() if app.id == "youtube"), None)
            if app:
                self.launch_user(app)
            else:
                self.toast("YouTube není nainstalované. Najdete ho ve Správě aplikací.")
            return
        command = command_for(key)
        title = ACTIONS[key].title if key in ACTIONS else "Napájení"
        self.start_application(key, title, command)

    def open_settings(self, category):
        from .settings_ui import SettingsWindow
        if getattr(self, "settings_window", None):
            self.settings_window.load(category)
            if self.isFullScreen():
                self.settings_window.showFullScreen()
            else:
                self.settings_window.show()
            self.settings_window.raise_()
            return
        self.settings_window = SettingsWindow(self, category=category, preview=self.preview)
        if self.isFullScreen():
            self.settings_window.showFullScreen()
        else:
            self.settings_window.show()

    def launch_user(self, app):
        if app.kind == "android":
            self.android_task("launch", app.target)
        else:
            self.start_application("user:"+app.id, app.title, self.library.command(app))

    def start_application(self, key, title, command):
        if self.preview:
            self.toast(f"Náhled · {title} se spustí až v systému PadTV.")
            return
        if key in self.activations or "handoff:" + key in self.processes:
            return
        import shutil
        available = executable_available(key) if key in ACTIONS or key in POWER_COMMANDS else bool(shutil.which(command[0]))
        if not available and key not in self.processes:
            self.toast(f"{title}: aplikace není nainstalovaná ({command[0]}).")
            return
        if key in POWER_COMMANDS:
            if key not in self.processes:
                self.spawn_application(key, title, command)
            return
        running = self.processes.get(key)
        def missing():
            if key in self.processes:
                if key in self.app_windows_seen and command[0] in ("chromium", "thunar"):
                    # A single-instance app can keep a background process after
                    # its last window closes. Ask that instance for a new window.
                    self.spawn_application("handoff:" + key, title, command, focus_key=key)
                else:
                    self.toast(f"Okno aplikace {title} se nepodařilo zobrazit.")
            else:
                self.spawn_application(key, title, command)
        self.activate_application(key, command, pid=int(running.processId()) if running else 0,
                                  wait=12 if running and key not in self.app_windows_seen else 0, on_missing=missing)

    def activate_application(self, key, command, pid=0, wait=0, on_missing=None):
        if self.preview or key in self.activations:
            return
        process = QProcess(self)
        self.activations[key] = process
        process.setProgram(sys.executable)
        process.setArguments(["-m", "padtv.windows"])
        process.setStandardErrorFile(QProcess.nullDevice())
        request = json.dumps({"key": key, "command": command, "pid": pid, "wait": wait}) + "\n"
        process.started.connect(lambda: (process.write(request.encode()), process.closeWriteChannel()))
        def finished(*args):
            if sip.isdeleted(self) or sip.isdeleted(process):
                return
            if self.activations.get(key) is not process:
                return
            self.activations.pop(key, None)
            try:
                result = json.loads(bytes(process.readAllStandardOutput()).decode())
            except (ValueError, UnicodeError):
                result = {}
            process.deleteLater()
            if result.get("ok") and result.get("found"):
                self.app_windows_seen.add(key)
                self.clear_notice()
            elif on_missing:
                on_missing()
        process.finished.connect(finished)
        process.errorOccurred.connect(lambda error: finished() if error == QProcess.ProcessError.FailedToStart else None)
        process.start()

    def spawn_application(self, key, title, command, focus_key=None):
        from .session import application_command
        launch_command = application_command(focus_key or key, command) if key not in POWER_COMMANDS else command
        process = QProcess(self)
        process.setProgram(launch_command[0])
        process.setArguments(list(launch_command[1:]))
        # Drain output to keep long media sessions bounded in memory.
        if key not in POWER_COMMANDS:
            process.setStandardOutputFile(QProcess.nullDevice())
        process.setStandardErrorFile(QProcess.nullDevice())
        self.processes[key] = process
        def finished(code, status):
            if sip.isdeleted(self) or sip.isdeleted(process):
                return
            self.processes.pop(key, None)
            self.app_windows_seen.discard(key)
            process.deleteLater()
            if code != 0 or status == QProcess.ExitStatus.CrashExit:
                detail = f"{title} se nepodařilo dokončit (kód {code})."
                if key in POWER_COMMANDS or command[0] == 'padbridge':
                    try:
                        detail = json.loads(bytes(process.readAllStandardOutput()).decode()).get('error', detail)
                    except (ValueError, UnicodeError):
                        pass
                self.toast(detail)
                self.raise_()
                self.activateWindow()
            # Chromium may successfully hand off to an existing browser process.
            # Let the window manager retain focus on that new browser window.
        def failed(error):
            if sip.isdeleted(self) or sip.isdeleted(process):
                return
            if error == QProcess.ProcessError.FailedToStart:
                self.processes.pop(key, None)
                process.deleteLater()
                self.toast(f"{title} se nepodařilo spustit.")
        process.finished.connect(finished)
        process.errorOccurred.connect(failed)
        if key not in POWER_COMMANDS:
            process.started.connect(lambda: self.activate_application(focus_key or key, command,
                                                                       pid=int(process.processId()), wait=12))
        process.start()

    def about(self):
        mode = "Náhled rozhraní; systémové akce jsou vypnuté." if self.preview else "Samostatná televizní distribuce založená na Debianu 13."
        dialog = ChoiceDialog(self, RELEASE_NAME, mode + f"\nSestavení {__version__}" + "\n\nŠipky: pohyb · Enter: otevřít · Esc: domov\nDelete: správa vybrané aplikace · F11: celá obrazovka\nWin + Home vrátí PadTV, Alt + Tab přepíná aplikace.", [("Zavřít", 0)])
        dialog.exec()
        dialog.deleteLater()

    def power_menu(self):
        dialog = ChoiceDialog(self, "Napájení", "Co má PadTV udělat?", [("Zpět", 0), ("Uspat", 3), ("Restartovat", 2), ("Vypnout", 1)])
        choice = dialog.exec()
        dialog.deleteLater()
        if choice:
            self.launch({1: "poweroff", 2: "reboot", 3: "suspend"}[choice])

    def search(self):
        text, accepted = QInputDialog.getText(self, "Hledat aplikaci", "Název aplikace:")
        if accepted:
            self.search_text = text.strip()
            self.set_page("apps")

    def profile(self):
        dialog = ChoiceDialog(self, "Váš profil", f"{getpass.getuser()}\nAplikace a jejich nastavení patří tomuto uživateli.", [("Zavřít", 0), ("Správa aplikací", 1)])
        result = dialog.exec()
        dialog.deleteLater()
        if result:
            self.set_page("manage")

    def install_youtube(self):
        try:
            self.library.install(YOUTUBE)
            self.set_page("manage")
            self.toast("YouTube je nainstalované jako běžná webová aplikace.")
        except (OSError, ValueError) as error:
            self.toast(str(error))

    def app_details(self, app):
        if app.kind == 'padbridge':
            self.bridge_details(app)
            return
        if app.kind == 'flatpak':
            product = next((p for p in self.products if p.id == app.id), None)
            if product:
                self.store_detail(product)
            else:
                self.toast('Aplikace není v aktuálním katalogu.')
            return
        kind = "Android aplikace" if app.kind == "android" else "Webová aplikace"
        managed = any(item.id == app.id for item in self.library.list())
        message = f"{kind}.\n" + ("Můžete ji odinstalovat včetně místních dat. Při dalším spuštění se sama nevrátí." if managed else "Aplikaci můžete spravovat v nastavení Androidu.")
        if managed and app.kind == "android":
            message += " Android může zobrazit ještě vlastní potvrzení odinstalování."
        choices = [("Zpět", 0), ("Spustit", 1)] + ([("Odinstalovat", 2)] if managed else [])
        dialog = ChoiceDialog(self, app.title, message, choices)
        result = dialog.exec()
        dialog.deleteLater()
        if result == 1:
            self.launch_user(app)
        elif result == 2:
            if "user:"+app.id in self.processes:
                self.toast("Před odinstalováním aplikaci zavřete.")
                return
            if app.kind == "android":
                self.android_task("remove", app.target, lambda data: self.remove_record(app))
            else:
                self.remove_record(app)

    def remove_record(self, app):
        try:
            self.library.remove(app, remove_data=True)
            self.android_apps = [item for item in self.android_apps if item.target != app.target]
            self.set_page(self.page)
            self.toast(f"{app.title} je odinstalované.")
        except (OSError, ValueError) as error:
            self.toast(f"Odinstalování se nepodařilo: {error}")

    def prepare_android(self, google_play=False):
        if self.preview:
            self.toast("Příprava Androidu je dostupná v systému PadTV na Linuxu.")
            return
        message = ('Stáhne obraz Waydroid GAPPS s Google Play. Ukončí otevřené Android aplikace; jejich data zachová. '
                   'Potřebujete několik GB místa. Přihlášení dokončíte v Google Play. Obchod může vyžádat registraci zařízení; dostupnost aplikací a Netflix DRM není zaručená.'
                   if google_play else 'Stáhne Android a zapne podporu APK. Potřebujete internet a několik GB místa. Živé USB bez perzistence data po restartu ztratí. Google Play není součástí této přípravy.')
        dialog = ChoiceDialog(self, 'Připravit Google Play' if google_play else 'Připravit Android', message, [("Zpět", 0), ("Připravit", 1)])
        answer = dialog.exec()
        dialog.deleteLater()
        if answer:
            if google_play:
                def prepared(data):
                    self.refresh_store()
                    self.android_task('launch', 'com.android.vending')
                self.android_task('prepare-play', callback=prepared)
            else:
                self.android_task("prepare", callback=lambda data: self.toast("Android je připravený. Můžete instalovat APK."))

    def refresh_android(self):
        def loaded(data):
            saved = {app.target: app for app in self.library.list() if app.kind == "android"}
            self.android_apps = [saved.get(item["package"], UserApp("android."+item["package"], item["name"] or item["package"], "android", item["package"])) for item in data.get("apps", [])]
            self.android_message = f"Nainstalované aplikace: {len(self.android_apps)}"
            self.set_page("android")
        self.android_task("list", callback=loaded)

    def install_waydroid_apk(self):
        if self.preview:
            self.toast("APK se instalují v systému PadTV na Linuxu. Náhled Windows Android nespouští.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Instalovat Android aplikaci", str(Path.home()), "Android aplikace (*.apk)")
        if not path:
            return
        def inspected(info):
            dialog = ChoiceDialog(self, "Instalovat aplikaci", f"{info['name']}\n{info['package']}\n\nNainstalovat jako běžnou odinstalovatelnou aplikaci?", [("Zpět", 0), ("Instalovat", 1)])
            answer = dialog.exec()
            dialog.deleteLater()
            if answer:
                self.android_task("install", path, installed)
        def installed(info):
            package = info["package"]
            product = next((p for p in self.products if p.kind == 'android' and p.target == package), None)
            app = self.product_app(product) if product else UserApp("android."+package, info["name"], "android", package)
            self.library.install(app)
            self.set_page("apps")
            self.toast(f"{app.title} je nainstalované. Lze jej odinstalovat ve Správě aplikací.")
        self.android_task("inspect", path, inspected)

    def android_task(self, action, argument=None, callback=None):
        if self.preview:
            self.toast("Android aplikace jsou dostupné v systému PadTV na Linuxu.")
            return
        key = "android-task"
        if key in self.processes:
            if action in ("launch", "open"):
                self.android_pending_launch = (action, argument)
                return
            self.toast("Počkejte prosím na dokončení předchozí operace Androidu.")
            return
        process = QProcess(self)
        process.setProgram(sys.executable)
        process.setArguments(["-m", "padtv.android", action] + ([argument] if argument else []))
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONIOENCODING", "utf-8")
        process.setProcessEnvironment(environment)
        self.processes[key] = process
        buffer = bytearray()
        def read_output():
            buffer.extend(bytes(process.readAllStandardOutput()))
            if len(buffer) > 2_000_000:
                del buffer[:-2_000_000]
        process.readyReadStandardOutput.connect(read_output)
        process.setStandardErrorFile(QProcess.nullDevice())
        def finished(code, status):
            read_output()
            self.processes.pop(key, None)
            process.deleteLater()
            try:
                data = json.loads(buffer.decode("utf-8"))
                if code or not data.get("ok"):
                    raise ValueError(data.get("error", "Operace se nepodařila."))
                if callback:
                    callback(data)
                elif action in ("launch", "open"):
                    self.activate_application("android-shell", ["weston", "--socket=padtv-android"], wait=8)
                else:
                    self.toast("Operace Androidu dokončena.")
            except (ValueError, OSError, KeyError) as error:
                self.android_message = "Android vyžaduje kontrolu nebo první přípravu."
                self.toast(str(error)[:180])
            if self.android_pending_launch:
                pending, self.android_pending_launch = self.android_pending_launch, None
                QTimer.singleShot(0, lambda: self.android_task(*pending))
        def failed(error):
            if error == QProcess.ProcessError.FailedToStart:
                self.processes.pop(key, None)
                process.deleteLater()
                self.toast("Nepodařilo se spustit správu Androidu.")
        process.finished.connect(finished)
        process.errorOccurred.connect(failed)
        process.start()
        if action not in ("launch", "open"):
            self.toast("Android · probíhá operace…")

    def cached_background(self):
        ratio = self.devicePixelRatioF()
        key = (self.width(), self.height(), ratio, self.page == "home")
        if self.background_key == key and self.background_cache is not None:
            return self.background_cache
        canvas = QPixmap(round(self.width()*ratio), round(self.height()*ratio))
        canvas.setDevicePixelRatio(ratio)
        p = QPainter(canvas)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#0d141d"))
        p.translate(*self.offset)
        p.scale(self.scale, self.scale)
        if not self.wallpaper.isNull():
            p.drawPixmap(QRectF(0, 0, 1600, 900), self.wallpaper, QRectF(self.wallpaper.rect()))
        shade = QLinearGradient(0, 0, 0, 900)
        shade.setColorAt(0, QColor(0, 13, 16, 35))
        shade.setColorAt(0.55, QColor(0, 10, 20, 8))
        shade.setColorAt(1, QColor(3, 9, 18, 230))
        p.fillRect(QRectF(0, 0, 1600, 900), shade)
        if self.page != "home":
            p.fillRect(QRectF(0, 0, 1600, 900), QColor(4, 12, 20, 155))
        if not self.logo.isNull():
            p.drawPixmap(QRectF(43, 25, 205, 68), self.logo, QRectF(self.logo.rect()))
        p.setPen(QPen(QColor(255,255,255,60),1))
        p.drawLine(QPointF(265,41),QPointF(265,87))
        p.end()
        self.glass_cache = canvas.scaled(max(1,canvas.width()//24),max(1,canvas.height()//24),
            Qt.AspectRatioMode.IgnoreAspectRatio,Qt.TransformationMode.SmoothTransformation).scaled(
            canvas.size(),Qt.AspectRatioMode.IgnoreAspectRatio,Qt.TransformationMode.SmoothTransformation)
        self.glass_cache.setDevicePixelRatio(ratio)
        self.background_key, self.background_cache = key, canvas
        return canvas

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.cached_background())
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(*self.offset)
        p.scale(self.scale, self.scale)
        now = datetime.now()
        rounded(p, (1427, 39, 125, 50), QColor(23, 46, 40, 200), 25, QColor(207, 237, 218, 70))
        label(p, (1427, 39, 125, 50), now.strftime("%H:%M"), 25, WHITE, False, Qt.AlignmentFlag.AlignCenter)
        if self.page != "home":
            titles = {"apps": "Aplikace", "store":"Store", "settings": "Nastavení", "manage": "Správa aplikací", "android": "Android aplikace"}
            subtitles = {"apps": "", "settings": "Obraz, zvuk a připojení pro vaši televizi.",
                         "manage": "Předinstalované aplikace můžete běžně odinstalovat.", "android": self.android_message,
                         "store": ""}
            title = f"Hledání: {self.search_text}" if self.page == "apps" and self.search_text else titles[self.page]
            label(p, (72, 133, 1400, 69), title, 43, WHITE, True)
            label(p, (76, 206, 1400, 34), subtitles[self.page], 19, QColor("#d3dfdf"))
        if self.preview:
            label(p, (72,860,700,24), f'Vývojový náhled · {RELEASE_NAME}', 12, QColor(230,245,245,100))
        if self.notice:
            rounded(p, (200, 597, 1200, 67), QColor(26, 25, 48, 245), 20, MINT)
            label(p, (225, 597, 1150, 67), self.notice, 17, WHITE, False, Qt.AlignmentFlag.AlignCenter)
