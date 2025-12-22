import math
from datetime import datetime
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
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

        # オーバーレイ画像
        overlay_cfg = self.config.get("overlay", {})
        overlay_img = overlay_cfg.get("image")
        self.overlay_pixmap = QPixmap(overlay_img) if overlay_img else None

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
        if not self.config.get("overlay",{}).get("above_hands",False):
            self.draw_overlay(painter)
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
        # オーバーレイ（針の上）
        if self.config.get("overlay", {}).get("above_hands", False):
            self.draw_overlay(painter)

    # --------------------------------------------------
    # 背景
    # --------------------------------------------------
    def draw_background(self, painter: QPainter):
        painter.save()

        path = QPainterPath()
        path.addEllipse(-100, -100, 200, 200)
        painter.setClipPath(path)

        # 背景色
        bg_color = QColor(self.config["background"]["color"])
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-100, -100, 200, 200)

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

    def draw_overlay(self, painter: QPainter):
        cfg = self.config.get("overlay", {})
        if not self.overlay_pixmap:
            return

        scale = cfg.get("scale", 1.0)
        x = cfg.get("x", 0)
        y = cfg.get("y", 0)
        opacity = cfg.get("opacity", 1.0)

        size = int(200 * scale)
        half = size // 2

        painter.save()
        painter.setOpacity(opacity)

        painter.drawPixmap(
            -half + x,
            -half + y,
            size,
            size,
            self.overlay_pixmap
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
