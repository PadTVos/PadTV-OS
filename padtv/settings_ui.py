"""TV-sized native settings. No desktop configuration applications or fake devices."""
import json
import shutil
from pathlib import Path
import sys

from . import RELEASE_NAME

from PyQt6.QtCore import QEvent, QProcess, QTimer, Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget)

STYLE = """
QDialog {background:#081e21;color:#f6f6ff;}
QWidget {color:#f6f6ff;font-family:'DejaVu Sans';font-size:20px;}
QLabel {background:transparent;}
QPushButton {text-align:left;background:rgba(220,240,245,22);border:1px solid rgba(255,255,255,55);
 border-radius:15px;padding:14px 20px;min-height:28px;}
QPushButton:focus {background:rgba(235,245,255,55);border:2px solid white;}
QPushButton:disabled {color:#829499;background:#172e32;border-color:#253f44;}
QLineEdit {background:#142c32;border:2px solid #a48ad5;border-radius:10px;padding:12px;}
QScrollArea {background:transparent;border:0;}
QScrollArea > QWidget > QWidget {background:transparent;}
QScrollBar:vertical {background:#122b31;width:10px;}
QScrollBar::handle:vertical {background:#8671b0;min-height:30px;}
"""


class RemoteDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(STYLE)
        self.setModal(True)
        self.controls = []

    def button(self, title, callback, layout):
        button = QPushButton(title)
        button.setAutoDefault(False)
        button.clicked.connect(callback)
        button.installEventFilter(self)
        self.controls.append(button)
        layout.addWidget(button)
        return button

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Escape, Qt.Key.Key_Back):
                self.close()
                return True
            if key in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Select) and isinstance(obj, QPushButton):
                obj.click()
                return True
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
                # Text fields keep left/right for cursor movement.
                if isinstance(obj, QLineEdit) and key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                    return False
                from .navigation import next_in_direction
                buttons = [b for b in self.controls if b.isVisible() and b.isEnabled()]
                if obj in buttons:
                    points = [(b.mapTo(self, b.rect().center()).x(), b.mapTo(self, b.rect().center()).y()) for b in buttons]
                    direction = {Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down", Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right"}[key]
                    target = buttons[next_in_direction(buttons.index(obj), points, direction)]
                    target.setFocus()
                    if hasattr(self, "scroll") and self.scroll.isAncestorOf(target):
                        self.scroll.ensureWidgetVisible(target)
                    return True
        return super().eventFilter(obj, event)


class Prompt(RemoteDialog):
    def __init__(self, parent, title, message, text=False, secret=False, seconds=0):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(min(860, parent.width() - 60))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        heading = QLabel(title)
        heading.setStyleSheet("font-size:28px;font-weight:bold;")
        layout.addWidget(heading)
        self.body = QLabel(message)
        self.body.setTextFormat(Qt.TextFormat.PlainText)
        self.body.setWordWrap(True)
        layout.addWidget(self.body)
        self.input = None
        if text:
            self.input = QLineEdit()
            self.input.setMaxLength(256)
            self.input.setEchoMode(QLineEdit.EchoMode.Password if secret else QLineEdit.EchoMode.Normal)
            self.input.installEventFilter(self)
            self.controls.append(self.input)
            layout.addWidget(self.input)
            grid = QGridLayout()
            self.letters = []
            for index, character in enumerate("1234567890qwertyuiopasdfghjkl-zxcvbnm@._"):
                button = QPushButton(character)
                button.setAutoDefault(False)
                button.setStyleSheet("text-align:center;padding:3px;min-height:30px;")
                button.clicked.connect(lambda checked=False, b=button: self.input.insert(b.text()))
                button.installEventFilter(self)
                self.controls.append(button)
                self.letters.append(button)
                grid.addWidget(button, index // 10, index % 10)
            layout.addLayout(grid)
            edit = QHBoxLayout()
            self.button("⇧ ABC", self.shift, edit)
            self.symbols = 0
            self.button("ABC / ?! / Č", self.toggle_symbols, edit)
            self.button("Mezera", lambda: self.input.insert(" "), edit)
            self.button("⌫ Smazat", self.input.backspace, edit)
            layout.addLayout(edit)
        row = QHBoxLayout()
        cancel = self.button("Zpět", self.reject, row)
        self.button("Potvrdit", self.accept, row)
        layout.addLayout(row)
        if self.input:
            self.input.setFocus()
        else:
            cancel.setFocus()
        if seconds:
            self.remaining = seconds
            self.timer = QTimer(self)
            def tick():
                self.remaining -= 1
                self.body.setText(f"Ponechat toto rozlišení? Automatický návrat za {self.remaining} s.")
                if self.remaining <= 0:
                    self.reject()
            self.timer.timeout.connect(tick)
            self.timer.start(1000)

    def shift(self):
        upper = self.letters[10].text().islower()
        for button in self.letters:
            button.setText(button.text().upper() if upper else button.text().lower())

    def toggle_symbols(self):
        self.symbols = (self.symbols + 1) % 3
        chars = ["1234567890qwertyuiopasdfghjkl-zxcvbnm@._",
                 "!@#$%^&*()_+-=[]{};:'\"\\|<>/?,.~`€£§°",
                 "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"][self.symbols]
        for index, button in enumerate(self.letters):
            button.setText(chars[index] if index < len(chars) else " ")


class SettingsWindow(RemoteDialog):
    def __init__(self, parent, category="network", preview=False):
        super().__init__(parent)
        self.preview, self.category = preview, category
        self.process, self.pending_prompt = None, None
        self.setWindowTitle("Nastavení PadTV")
        self.resize(parent.size())
        self.wallpaper = QPixmap(str(Path(__file__).parent / "assets" / "waterfall.png"))
        root = QVBoxLayout(self)
        root.setContentsMargins(44, 30, 44, 30)
        title = QLabel("Nastavení")
        title.setStyleSheet("font-size:34px;font-weight:bold;")
        root.addWidget(title)
        body = QHBoxLayout()
        body.setSpacing(30)
        root.addLayout(body, 1)
        sidebar = QVBoxLayout()
        sidebar.setSpacing(12)
        self.categories = []
        for key, name in [("network", "Síť a Wi-Fi"), ("bluetooth", "Bluetooth"), ("audio", "Zvuk"),
                          ("display", "Obraz"), ("system", "Systém")]:
            button = self.button(name, lambda checked=False, k=key: self.load(k), sidebar)
            button.setFixedWidth(230)
            self.categories.append(button)
        sidebar.addStretch()
        self.button("← Domů", self.close, sidebar)
        body.addLayout(sidebar)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        body.addWidget(self.scroll, 1)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setStyleSheet("font-size:17px;color:#c2d3d5;")
        root.addWidget(self.status)
        self.clear()
        QTimer.singleShot(0, lambda: self.load(category))

    def paintEvent(self, event):
        painter = QPainter(self)
        scaled = self.wallpaper.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap((self.width()-scaled.width())//2, (self.height()-scaled.height())//2, scaled)
        painter.fillRect(self.rect(), QColor(3, 17, 23, 195))

    def clear(self):
        old = self.scroll.takeWidget()
        if old:
            self.controls = [b for b in self.controls if not old.isAncestorOf(b)]
            old.deleteLater()
        self.content = QWidget()
        self.rows = QVBoxLayout(self.content)
        self.rows.setContentsMargins(4, 4, 16, 8)
        self.rows.setSpacing(12)
        self.rows.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.content)

    def note(self, text):
        label = QLabel(text)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setStyleSheet("padding:8px 4px;line-height:140%;")
        self.rows.addWidget(label)

    def row(self, text, action=None, **data):
        return self.button(text, lambda: self.request(action, **data) if action else None, self.rows)

    def load(self, category):
        if self.process:
            return
        self.category = category
        self.clear()
        if self.preview:
            self.note("Toto je náhled prostředí ve Windows. Skutečné adaptéry a nastavení jsou dostupné ve spuštěném systému PadTV.")
            self.status.setText("Náhled nemění nastavení počítače.")
            return
        self.request(category + "-status")

    def request(self, action, **data):
        if self.process or self.preview:
            return
        self.status.setText("Hledám zařízení…" if action.endswith("scan") else "Provádím nastavení…")
        focused = self.focusWidget()
        self.focus_title = focused.text() if isinstance(focused, QPushButton) else ""
        for button in self.controls:
            button.setEnabled(False)
        process = QProcess(self)
        self.process = process
        self.result = None
        process.setProgram(sys.executable)
        process.setArguments(["-m", "padtv.system"])
        process.setStandardErrorFile(QProcess.nullDevice())
        process.readyReadStandardOutput.connect(self.read_events)
        process.started.connect(lambda: process.write((json.dumps({"action": action, **data}) + "\n").encode()))
        process.finished.connect(self.finished)
        process.errorOccurred.connect(lambda error: self.failed_start() if error == QProcess.ProcessError.FailedToStart else None)
        process.start()

    def failed_start(self):
        self.result = {"ok": False, "error": "Službu nastavení nelze spustit."}
        self.finished()

    def read_events(self):
        while self.process and self.process.canReadLine():
            try:
                event = json.loads(bytes(self.process.readLine()).decode())
            except (ValueError, UnicodeError):
                continue
            if "event" not in event:
                self.result = event
            else:
                self.handle_event(event)

    def handle_event(self, event):
        kind = event["event"]
        if kind == "bluetooth-display":
            self.status.setText(f"Na párovaném zařízení zadejte kód {event['value']} a potvrďte Enterem.")
            return
        if kind == "bluetooth-cancel":
            if self.pending_prompt:
                self.pending_prompt.reject()
            return
        if kind == "display-confirm":
            prompt = Prompt(self, "Obraz", "Ponechat toto rozlišení? Automatický návrat za 15 s.", seconds=14)
        else:
            text = kind in ("bluetooth-pin", "bluetooth-passkey")
            message = "Zadejte kód z párovaného zařízení." if text else f"Potvrďte stejný kód na obou zařízeních: {event.get('value', '')}"
            prompt = Prompt(self, "Párování Bluetooth", message, text=text)
        self.pending_prompt = prompt
        answer = {"confirm": prompt.exec() == QDialog.DialogCode.Accepted}
        if prompt.input:
            answer["value"] = prompt.input.text()
            prompt.input.clear()
        self.pending_prompt = None
        if self.process:
            self.process.write((json.dumps(answer) + "\n").encode())
        prompt.deleteLater()

    def finished(self, *args):
        if self.process is None:
            return
        self.read_events()
        process, self.process = self.process, None
        process.deleteLater()
        if self.pending_prompt:
            self.pending_prompt.reject()
        for button in self.controls:
            button.setEnabled(True)
        if self.result and self.result.get("ok"):
            self.clear()
            self.render(self.result["data"])
            self.status.setText("Šipky: pohyb   •   OK / Enter: vybrat   •   Zpět / Esc: domů")
        else:
            self.status.setText("Nastavení se nepodařilo: " + (self.result or {}).get("error", "Služba neodpověděla."))
            if self.rows.count() == 0:
                self.row("Zkusit znovu", self.category + "-status")
        fallback = self.categories[("network", "bluetooth", "audio", "display", "system").index(self.category)]
        target = next((b for b in self.controls if isinstance(b, QPushButton) and b.text() == self.focus_title), fallback)
        target.setFocus(Qt.FocusReason.OtherFocusReason)

    def render(self, data):
        category = self.category
        if category == "network":
            devices = data["devices"]
            if not devices:
                self.note("Síťový adaptér nebyl nalezen. Připojte síťový kabel nebo podporovaný USB Wi-Fi adaptér.")
            for device in devices:
                if device["type"] != 1:
                    continue
                connected = device["connected"]
                self.note(f"Kabelová síť · {device['name']}\n" + ("Připojeno · " + ", ".join(device["addresses"]) if connected else "Nepřipojeno"))
                self.row("Odpojit kabelovou síť" if connected else "Připojit kabelovou síť",
                         "network-disconnect" if connected else "network-connect", device=device["path"])
            if not any(d["type"] == 2 for d in devices):
                self.note("Wi-Fi adaptér není dostupný." + (" Ve virtuálním PC internet používá připojení Windows přes virtuální kabel. Seznam Wi-Fi sítí vyžaduje předání USB Wi-Fi adaptéru do virtuálního PC." if data["vm"] else " Zkontrolujte připojení adaptéru a podporu ovladače."))
            else:
                self.row("Vypnout Wi-Fi" if data["wifi"] else "Zapnout Wi-Fi", "wifi-power", enabled=not data["wifi"])
                if not data["hardware"]:
                    self.note("Wi-Fi je vypnutá hardwarovým přepínačem nebo v BIOSu.")
                if data["wifi"] and data["hardware"]:
                    self.row("Vyhledat sítě", "network-scan")
                    if not data["aps"]:
                        self.note("Zatím nebyla nalezena žádná Wi-Fi síť. Zapněte router a zkuste vyhledat sítě znovu.")
                    seen = set()
                    for ap in data["aps"]:
                        key = (ap["device"], ap["name"], ap["security"])
                        if key in seen:
                            continue
                        seen.add(key)
                        title = f"{ap['name']}   ·   {ap['strength']} %   ·   " + ("Připojeno" if ap["connected"] else ("Otevřená" if ap["security"] == "open" else "Zabezpečená"))
                        self.button(title, lambda checked=False, a=ap: self.connect_wifi(a), self.rows)
            self.row("Obnovit stav sítě", "network-status")
            for saved in data.get("saved", []):
                self.button("Zapomenout uloženou Wi-Fi: " + saved["name"],
                            lambda checked=False, s=saved: self.forget_wifi(s), self.rows)
        elif category == "bluetooth":
            if not data["adapters"]:
                self.note("Bluetooth adaptér nebyl nalezen. Na PC jej zapněte nebo připojte USB Bluetooth adaptér. Ve virtuálním PC musí být adaptér předaný přímo do PadTV.")
            for adapter in data["adapters"]:
                self.row(adapter["name"] + (" · Vypnout" if adapter["powered"] else " · Zapnout"), "bluetooth-power", adapter=adapter["path"], enabled=not adapter["powered"])
                if adapter["powered"]:
                    self.row("Vyhledat Bluetooth zařízení", "bluetooth-scan", adapter=adapter["path"])
            for device in sorted(data["devices"], key=lambda d: (not d["paired"], d["name"])):
                state = "Připojeno" if device["connected"] else "Spárováno" if device["paired"] else "Spárovat"
                self.row(f"{device['name']} · {state}" + (" · Odpojit" if device["connected"] else ""),
                         "bluetooth-disconnect" if device["connected"] else "bluetooth-connect", device=device["path"])
                if device["paired"]:
                    self.button("Zapomenout: " + device["name"], lambda checked=False, d=device: self.forget(d), self.rows)
            self.row("Obnovit stav Bluetooth", "bluetooth-status")
        elif category == "audio":
            self.note(f"Hlasitost {data['volume']} %" + (" · Ztlumeno" if data["mute"] else ""))
            if data["sinks"]:
                self.row("− Ztišit", "audio-volume", volume=max(0, min(100, data["volume"] - 5)))
                self.row("+ Zesílit", "audio-volume", volume=min(100, data["volume"] + 5))
                self.row("Zapnout zvuk" if data["mute"] else "Ztlumit", "audio-mute")
                for sink in data["sinks"]:
                    self.row(("✓ " if sink["name"] == data["default"] else "") + sink["description"], "audio-output", sink=sink["name"])
            else:
                self.note("Žádný zvukový výstup. Připojte HDMI, sluchátka nebo Bluetooth reproduktor.")
            self.row("Obnovit zvukové výstupy", "audio-status")
        elif category == "display":
            for output in data["displays"]:
                self.note(output["name"] + " · " + (output["current"] or "Vypnutá obrazovka"))
                for mode in output["modes"]:
                    self.row(("✓ " if mode == output["current"] else "") + mode, "display-set", output=output["name"], mode=mode)
            self.row("Obnovit obrazovky", "display-status")
        else:
            self.note(f"{RELEASE_NAME}\nSestavení {data['version']} · Debian 13\nZařízení: {data['hostname']}\nJádro: {data['kernel']}")
            if data["vm"]:
                self.note("Prostředí: virtuální PC (" + data["vm"] + ")")
            if data.get("persistent"):
                self.note("Trvalé úložiště je připojené. Aplikace a nastavení zůstávají uložené i po vypnutí.")
            elif data["live"]:
                self.note("Spuštěno jako Live systém. Bez nastaveného trvalého úložiště se aplikace a nastavení po vypnutí neuchovají.")
            self.note("Start je automatický, bez přihlašovacího hesla. Hesla k Wi-Fi a účtům v aplikacích zadáváte pouze pro tyto služby.")
            if data['live'] and shutil.which('padtv-installer'):
                self.button('Nainstalovat PadTV na disk', self.install_system, self.rows)
            names = {'network': 'Síť', 'bluetooth': 'Bluetooth', 'android': 'Android'}
            for service in data.get('services', []):
                self.note(names[service['id']] + ' · ' + service['state'])
                if service['state'] != 'unavailable':
                    self.button('Restartovat službu ' + names[service['id']],
                                lambda checked=False, s=service: self.restart_service(s), self.rows)

    def restart_service(self, service):
        prompt = Prompt(self, 'Restart služby', 'Služba se na chvíli odpojí. Pokračovat?')
        accepted = prompt.exec() == QDialog.DialogCode.Accepted
        prompt.deleteLater()
        if accepted:
            self.request('system-service', service=service['id'], operation='restart')

    def install_system(self):
        if self.preview:
            return
        # Disk selection and destructive confirmation belong to the installer.
        started, _ = QProcess.startDetached('padtv-installer', [])
        if not started:
            self.status.setText('Instalátor se nepodařilo otevřít.')

    def connect_wifi(self, ap):
        if ap["connected"]:
            self.request("network-disconnect", device=ap["device"])
            return
        password = ""
        if ap["security"] in ("wpa-psk", "sae"):
            prompt = Prompt(self, "Připojit k Wi-Fi", f"Síť: {ap['name']}\nZadejte heslo. Pro uloženou síť můžete ponechat prázdné.", text=True, secret=True)
            if prompt.exec() != QDialog.DialogCode.Accepted:
                prompt.deleteLater()
                return
            password = prompt.input.text()
            prompt.input.clear()
            prompt.deleteLater()
        self.request("network-connect", device=ap["device"], ap=ap["path"], password=password)

    def forget(self, device):
        prompt = Prompt(self, "Zapomenout zařízení", f"Odstranit párování zařízení {device['name']}?")
        if prompt.exec() == QDialog.DialogCode.Accepted:
            self.request("bluetooth-forget", device=device["path"])
        prompt.deleteLater()

    def forget_wifi(self, connection):
        prompt = Prompt(self, "Zapomenout Wi-Fi", f"Odstranit uložené připojení a heslo k síti {connection['name']}?")
        if prompt.exec() == QDialog.DialogCode.Accepted:
            self.request("network-forget", connection=connection["path"])
        prompt.deleteLater()

    def closeEvent(self, event):
        if self.process:
            self.process.closeWriteChannel()
            self.status.setText("Dokončuji operaci… Párování se zruší a nepotvrzené rozlišení se vrátí zpět.")
            event.ignore()
        else:
            super().closeEvent(event)
