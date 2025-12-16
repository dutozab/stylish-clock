import math
from datetime import datetime
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QConicalGradient
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QPixmap,
    QPainterPath
)

from .config_loader import load_config


class AnalogClock(QWidget):
    """
    アナログ時計ウィジェット
    - config.json で見た目を変更可能
    - 枠なし・半透明・ドラッグ移動対応
    """

    def __init__(self):
        super().__init__()

        # ===== 設定読み込み =====
        self.config = load_config("config/config.json")

        # ===== ウィンドウ設定 =====
        size = self.config["window"]["size"]
        self.resize(size, size)

        flags = Qt.FramelessWindowHint
        if self.config["window"].get("always_on_top", False):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.setWindowOpacity(self.config["window"].get("opacity", 1.0))
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ===== 背景画像 =====
        bg_image = self.config["background"].get("image")
        self.bg_pixmap = QPixmap(bg_image) if bg_image else None

        # ===== タイマー =====
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    # --------------------------------------------------
    # 描画処理
    # --------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)

        # ===== 背景描画 =====
        self.draw_background(painter)

        # ===== 時刻取得 =====
        now = datetime.now()

        # ===== 針描画 =====
        self.draw_hand(
            painter,
            angle=(now.hour % 12) * 30 + now.minute / 2,
            cfg=self.config["hands"]["hour"]
        )
        self.draw_hand(
            painter,
            angle=now.minute * 6,
            cfg=self.config["hands"]["minute"]
        )
        self.draw_hand(
            painter,
            angle=now.second * 6,
            cfg=self.config["hands"]["second"]
        )

    # --------------------------------------------------
    # 背景
    # --------------------------------------------------

    def draw_background(self, painter: QPainter):
        painter.save()

        path = QPainterPath()
        path.addEllipse(-100, -100, 200, 200)
        painter.setClipPath(path)

        painter.save()

        # 円形クリップ
        path = QPainterPath()
        path.addEllipse(-100, -100, 200, 200)
        painter.setClipPath(path)

        # ===== 虹色グラデーション =====
        gradient = QConicalGradient(0, 0, 0)
        gradient.setColorAt(0.00, QColor("#ff0000"))  # 赤
        gradient.setColorAt(0.17, QColor("#ff7f00"))  # 橙
        gradient.setColorAt(0.33, QColor("#ffff00"))  # 黄
        gradient.setColorAt(0.50, QColor("#00ff00"))  # 緑
        gradient.setColorAt(0.67, QColor("#0000ff"))  # 青
        gradient.setColorAt(0.83, QColor("#4b0082"))  # 藍
        gradient.setColorAt(1.00, QColor("#ff0000"))  # 赤（閉じる）

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-100, -100, 200, 200)

        painter.restore()

        # 背景画像
        if self.bg_pixmap:
            scale = self.config["background"].get("image_scale", 1.0)

            size = int(200 * scale)
            offset = size // 2

            painter.setOpacity(
                self.config["background"].get("image_opacity", 1.0)
            )
            painter.drawPixmap(
                -offset, -offset,
                size, size,
                self.bg_pixmap
            )

        painter.restore()
        painter.setOpacity(1.0)

    # --------------------------------------------------
    # 針
    # --------------------------------------------------
    def draw_hand(self, painter: QPainter, angle: float, cfg: dict):
        painter.save()

        pen = QPen(QColor(cfg["color"]), cfg["width"])
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        length = cfg["length"]
        painter.drawLine(
            0, 0,
            int(length * math.sin(math.radians(angle))),
            int(-length * math.cos(math.radians(angle)))
        )

        painter.restore()

    # --------------------------------------------------
    # ドラッグ移動
    # --------------------------------------------------
    def mousePressEvent(self, event):
        self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = event.globalPosition().toPoint() - self._drag_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self._drag_pos = event.globalPosition().toPoint()
