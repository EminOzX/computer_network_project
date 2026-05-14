from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QLineEdit, QPushButton,
                              QFrame, QGraphicsDropShadowEffect,
                              QStackedWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush

SERVER_IP   = "18.184.13.71"
SERVER_PORT = 5555


# ─────────────────────────────────────────────────────────────────────────────
# Dalgalı arka plan
# ─────────────────────────────────────────────────────────────────────────────
class WaveBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(30)

    def _tick(self):
        self._offset = (self._offset + 1) % 200
        self.update()

    def paintEvent(self, event):
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#050d1a"))
        grad.setColorAt(0.6, QColor("#080f1e"))
        grad.setColorAt(1.0, QColor("#0a1628"))
        p.fillRect(self.rect(), QBrush(grad))

        p.setOpacity(0.05)
        from PyQt5.QtGui import QPen
        p.setPen(QPen(QColor("#00d4ff"), 1.5))
        for wi in range(6):
            y_base = self.height() * 0.55 + wi * 28
            pts = [(x, y_base + 12 * math.sin((x + self._offset * (1 + wi * 0.3)) * 0.025))
                   for x in range(0, self.width() + 10, 4)]
            for i in range(len(pts) - 1):
                p.drawLine(int(pts[i][0]), int(pts[i][1]), int(pts[i+1][0]), int(pts[i+1][1]))

        p.setOpacity(0.035)
        p.setPen(QPen(QColor("#00d4ff"), 1))
        for gx in range(0, self.width(), 30):
            for gy in range(0, self.height(), 30):
                p.drawPoint(gx, gy)


# ─────────────────────────────────────────────────────────────────────────────
# Styled input
# ─────────────────────────────────────────────────────────────────────────────
class StyledInput(QLineEdit):
    def __init__(self, placeholder="", default=""):
        super().__init__(default)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(46)
        self.setFont(QFont("Arial", 12))
        self._update_style(False)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._update_style(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._update_style(False)

    def _update_style(self, focused):
        border = "#00d4ff" if focused else "#1e3a5f"
        self.setStyleSheet(f"""
            QLineEdit {{
                background: #0d1f3c;
                color: #e0f0ff;
                border: 1.5px solid {border};
                border-radius: 10px;
                padding: 0 14px;
                selection-background-color: #00d4ff44;
            }}
        """)


def _btn(text, primary=True, height=50):
    b = QPushButton(text)
    b.setFixedHeight(height)
    b.setFont(QFont("Arial", 13, QFont.Bold))
    b.setCursor(Qt.PointingHandCursor)
    if primary:
        b.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0077cc, stop:1 #00aaff);
                color: white; border: none; border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0088ee, stop:1 #00ccff);
            }
            QPushButton:pressed  { background: #005599; }
            QPushButton:disabled { background: #1a2a3a; color: #3a5a7a; }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(18); sh.setColor(QColor("#00aaff88")); sh.setOffset(0, 4)
        b.setGraphicsEffect(sh)
    else:
        b.setStyleSheet("""
            QPushButton {
                background: #0d1f3c;
                color: #00d4ff;
                border: 1.5px solid #1e3a5f;
                border-radius: 12px;
            }
            QPushButton:hover { background: #112240; border-color: #00d4ff; }
        """)
    return b


# ─────────────────────────────────────────────────────────────────────────────
# Başlangıç Ekranı
# ─────────────────────────────────────────────────────────────────────────────
class StartScreen(QWidget):
    connect_requested = pyqtSignal(str, int)   # host, port  (bağlan butonundan)
    create_room       = pyqtSignal(str, int)   # host, port  (oda oluştur)
    join_room         = pyqtSignal(str, int, str)  # host, port, code

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Amiral Battı")
        self.setMinimumSize(540, 640)
        self.setStyleSheet("background: transparent;")

        self.bg = WaveBackground(self)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)
        root.setContentsMargins(60, 40, 60, 40)

        # Kart
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(8, 15, 30, 0.90);
                border: 1px solid #1e3a5f;
                border-radius: 20px;
            }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(50); sh.setColor(QColor("#00d4ff33")); sh.setOffset(0, 0)
        card.setGraphicsEffect(sh)

        card_lay = QVBoxLayout(card)
        card_lay.setSpacing(14)
        card_lay.setContentsMargins(40, 32, 40, 32)

        # Başlık
        anchor = QLabel("⚓")
        anchor.setAlignment(Qt.AlignCenter)
        anchor.setFont(QFont("Segoe UI Emoji", 36))
        anchor.setStyleSheet("background:transparent; border:none;")
        card_lay.addWidget(anchor)

        title = QLabel("AMİRAL BATTI")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: #00d4ff; background:transparent; border:none;")
        card_lay.addWidget(title)

        subtitle = QLabel("Çok Oyunculu Deniz Savaşı")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: #4a6a8a; background:transparent; border:none;")
        card_lay.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#1e3a5f; border:none; max-height:1px;")
        card_lay.addWidget(sep)

        # Sunucu satırı
        srv_row = QHBoxLayout()
        srv_row.setSpacing(8)
        self.ip_input   = StyledInput("Sunucu IP", SERVER_IP)
        self.port_input = StyledInput("Port", str(SERVER_PORT))
        self.port_input.setFixedWidth(100)
        srv_row.addWidget(self.ip_input)
        srv_row.addWidget(self.port_input)
        card_lay.addLayout(srv_row)

        # ── Sayfa yığını (ana menü / oda oluştur / odaya katıl)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_menu_page())   # 0
        self.pages.addWidget(self._build_create_page()) # 1
        self.pages.addWidget(self._build_join_page())   # 2
        card_lay.addWidget(self.pages)

        # Durum
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setFixedHeight(26)
        self.status_label.setStyleSheet("color:#ffaa00; background:transparent; border:none;")
        card_lay.addWidget(self.status_label)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background:#1e3a5f; border:none; max-height:1px;")
        card_lay.addWidget(sep2)

        hint = QLabel("💡  2 oyuncu bağlanmalıdır — IP ve port değiştirilebilir")
        hint.setAlignment(Qt.AlignCenter)
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color:#2a4a6a; background:transparent; border:none;")
        card_lay.addWidget(hint)

        root.addWidget(card)

    # ── Alt sayfalar ──────────────────────────────────────────────────────────
    def _build_menu_page(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setSpacing(12)
        lay.setContentsMargins(0, 4, 0, 4)

        self.create_btn = _btn("🏠  ODA OLUŞTUR")
        self.join_btn   = _btn("🔑  ODAYA KATIL", primary=False)
        self.create_btn.clicked.connect(lambda: self._go_create())
        self.join_btn.clicked.connect(lambda: self.pages.setCurrentIndex(2))

        lay.addWidget(self.create_btn)
        lay.addWidget(self.join_btn)
        return w

    def _build_create_page(self):
        """Oda oluşturulunca gösterilen kod ekranı."""
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(0, 4, 0, 4)

        lbl = QLabel("Oda Kodu")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFont(QFont("Arial", 11))
        lbl.setStyleSheet("color:#4a6a8a; background:transparent; border:none;")
        lay.addWidget(lbl)

        self.code_display = QLabel("------")
        self.code_display.setAlignment(Qt.AlignCenter)
        self.code_display.setFont(QFont("Courier New", 32, QFont.Bold))
        self.code_display.setStyleSheet("""
            color: #00ff88;
            background: #0d1f3c;
            border: 1.5px solid #00ff8844;
            border-radius: 12px;
            padding: 10px 20px;
            letter-spacing: 8px;
        """)
        lay.addWidget(self.code_display)

        self.waiting_lbl = QLabel("⏳  Rakip bekleniyor...")
        self.waiting_lbl.setAlignment(Qt.AlignCenter)
        self.waiting_lbl.setStyleSheet("color:#ffaa00; font-size:12px; background:transparent; border:none;")
        lay.addWidget(self.waiting_lbl)

        back = _btn("← Geri", primary=False, height=38)
        back.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        lay.addWidget(back)
        return w

    def _build_join_page(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(0, 4, 0, 4)

        lbl = QLabel("Oda kodunu gir:")
        lbl.setStyleSheet("color:#aaaaaa; font-size:12px; background:transparent; border:none;")
        lay.addWidget(lbl)

        self.code_input = StyledInput("Örn: A3K7P2")
        self.code_input.setAlignment(Qt.AlignCenter)
        self.code_input.setFont(QFont("Courier New", 18, QFont.Bold))
        self.code_input.setMaxLength(6)
        self.code_input.textChanged.connect(
            lambda t: self.code_input.setText(t.upper())
        )
        lay.addWidget(self.code_input)

        self.join_confirm_btn = _btn("🔑  KATIL")
        self.join_confirm_btn.clicked.connect(self._go_join)
        lay.addWidget(self.join_confirm_btn)

        back = _btn("← Geri", primary=False, height=38)
        back.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        lay.addWidget(back)
        return w

    # ── Aksiyon metodları ─────────────────────────────────────────────────────
    def _host_port(self):
        host = self.ip_input.text().strip()
        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            self.set_status("❌ Geçersiz port!", "#ff4444")
            return None, None
        return host, port

    def _go_create(self):
        host, port = self._host_port()
        if host is None:
            return
        self.pages.setCurrentIndex(1)
        self.code_display.setText("······")
        self.waiting_lbl.setText("⏳ Bağlanılıyor...")
        self.create_room.emit(host, port)

    def _go_join(self):
        code = self.code_input.text().strip().upper()
        if len(code) != 6:
            self.set_status("❌ 6 haneli kod gir!", "#ff4444")
            return
        host, port = self._host_port()
        if host is None:
            return
        self.join_confirm_btn.setEnabled(False)
        self.set_status("⏳ Odaya bağlanılıyor...", "#ffaa00")
        self.join_room.emit(host, port, code)

    def show_room_code(self, code: str):
        self.code_display.setText(code)
        self.waiting_lbl.setText("⏳  Rakip bekleniyor... Kodu paylaş!")

    def set_status(self, text, color="#ffaa00"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color:{color}; background:transparent; border:none; font-size:11px;"
        )

    def reset(self):
        self.pages.setCurrentIndex(0)
        self.code_input.clear()
        self.join_confirm_btn.setEnabled(True)
        self.status_label.setText("")

    def resizeEvent(self, event):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)