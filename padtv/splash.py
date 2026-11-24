from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QWidget


class StartupScreen(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self.logo = QPixmap(str(Path(__file__).parent / "assets" / "logo.png"))
        self.tick = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(350)

    def advance(self):
        self.tick = (self.tick + 1) % 3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#061719"))
        logo = self.logo.scaled(round(min(self.width() * .42, 620)), 210,
                                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap((self.width()-logo.width())//2, round(self.height()*.32), logo)
        painter.setPen(QColor("#e0ebef"))
        painter.setFont(QFont("DejaVu Sans", 22))
        painter.drawText(0, round(self.height()*.64), self.width(), 50, Qt.AlignmentFlag.AlignCenter, "Spouštím PadTV…")
        painter.setPen(Qt.PenStyle.NoPen)
        for index in range(3):
            painter.setBrush(QColor("#ac65ff") if self.tick == index else QColor("#44314c"))
            painter.drawEllipse(self.width()//2 + (index-1)*28 - 6, round(self.height()*.73), 12, 12)
