from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QGridLayout,
                              QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QTime
from PyQt5.QtGui import QFont, QPalette, QColor
from game.board import Board
from game.ship import Ship, SHIPS

CELL_SIZE = 42

# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı: Kart widget
# ─────────────────────────────────────────────────────────────────────────────
class StatCard(QWidget):
    def __init__(self, icon, title, value="0", accent="#00d4ff"):
        super().__init__()
        self.accent = accent
        self.setFixedSize(110, 72)
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0d1f3c, stop:1 #0a1628);
                border: 1px solid {accent}44;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("background:transparent; border:none; font-size:13px;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"background:transparent; border:none; color:#8899aa; font-size:9px;")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()
        layout.addLayout(top)

        self.value_lbl = QLabel(value)
        self.value_lbl.setAlignment(Qt.AlignCenter)
        self.value_lbl.setFont(QFont("Arial", 18, QFont.Bold))
        self.value_lbl.setStyleSheet(f"background:transparent; border:none; color:{accent};")
        layout.addWidget(self.value_lbl)

    def set_value(self, v):
        self.value_lbl.setText(str(v))


# ─────────────────────────────────────────────────────────────────────────────
# Tahta widget
# ─────────────────────────────────────────────────────────────────────────────
class BoardWidget(QWidget):
    cell_clicked  = pyqtSignal(int, int)
    cell_hovered  = pyqtSignal(int, int)  # hover önizleme için
    cell_unhovered = pyqtSignal()         # hover çıkış için

    def __init__(self, title, clickable=False):
        super().__init__()
        self.clickable   = clickable
        self.buttons     = {}
        self.cell_states = {}  # (row,col) -> state string
        self.init_ui(title)

    def init_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 11, QFont.Bold))
        label.setStyleSheet("color: #00d4ff; background: transparent;")
        layout.addWidget(label)

        grid = QGridLayout()
        grid.setSpacing(2)

        for col in range(10):
            lbl = QLabel(chr(65 + col))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #556677; font-size: 10px; background:transparent;")
            grid.addWidget(lbl, 0, col + 1)

        for row in range(10):
            lbl = QLabel(str(row + 1))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #556677; font-size: 10px; background:transparent;")
            grid.addWidget(lbl, row + 1, 0)

            for col in range(10):
                btn = QPushButton()
                btn.setFixedSize(CELL_SIZE, CELL_SIZE)
                btn.setStyleSheet(self.cell_style("empty"))
                btn.setCursor(Qt.PointingHandCursor if self.clickable else Qt.ArrowCursor)
                self.cell_states[(row, col)] = "empty"
                if self.clickable:
                    btn.clicked.connect(lambda _, r=row, c=col: self.cell_clicked.emit(r, c))
                    btn.enterEvent = lambda e, r=row, c=col: self.cell_hovered.emit(r, c)
                    btn.leaveEvent = lambda e: self.cell_unhovered.emit()
                else:
                    btn.setEnabled(False)
                self.buttons[(row, col)] = btn
                grid.addWidget(btn, row + 1, col + 1)

        layout.addLayout(grid)

    def cell_style(self, state):
        styles = {
            "empty": """
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #112240, stop:1 #0d1b33);
                    border: 1px solid #1e3a5f;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background: #1a3a6a;
                    border: 1px solid #00d4ff;
                }
            """,
            "ship": """
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #1e4d7a, stop:1 #163d63);
                    border: 1px solid #00aacc;
                    border-radius: 3px;
                }
            """,
            "hit": """
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #cc2200, stop:1 #991a00);
                    border: 1px solid #ff4422;
                    border-radius: 3px;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }
            """,
            "miss": """
                QPushButton {
                    background: #1a2533;
                    border: 1px solid #334455;
                    border-radius: 3px;
                    color: #556677;
                    font-size: 14px;
                }
            """,
            "sunk": """
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #880000, stop:1 #550000);
                    border: 1px solid #ff0000;
                    border-radius: 3px;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }
            """,
            "preview_ok": """
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #1a6633, stop:1 #134d26);
                    border: 1px solid #00ff88;
                    border-radius: 3px;
                }
            """,
            "preview_bad": """
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #6e1a1a, stop:1 #4d1010);
                    border: 1px solid #ff4444;
                    border-radius: 3px;
                }
            """,
        }
        return styles.get(state, styles["empty"])

    def set_cell(self, row, col, state):
        btn = self.buttons.get((row, col))
        if btn:
            self.cell_states[(row, col)] = state
            btn.setStyleSheet(self.cell_style(state))
            if state == "hit":
                btn.setText("✕")
                btn.setEnabled(False)
            elif state == "sunk":
                btn.setText("💀")
                btn.setEnabled(False)
            elif state == "miss":
                btn.setText("•")
                btn.setEnabled(False)

    def set_preview(self, row, col, preview_state):
        """Sadece görsel önizleme — cell_states'i değiştirmez."""
        btn = self.buttons.get((row, col))
        if btn:
            btn.setStyleSheet(self.cell_style(preview_state))

    def restore_cell(self, row, col):
        """Önceki kalıcı durumuna döndür."""
        btn = self.buttons.get((row, col))
        if btn:
            state = self.cell_states.get((row, col), "empty")
            btn.setStyleSheet(self.cell_style(state))

    def set_clickable(self, enabled):
        for (r, c), btn in self.buttons.items():
            text = btn.text()
            if text not in ("✕", "💀", "•"):
                btn.setEnabled(enabled)
                btn.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)


# ─────────────────────────────────────────────────────────────────────────────
# Gemi Yerleştirme Ekranı
# ─────────────────────────────────────────────────────────────────────────────
class PlacementWidget(QWidget):
    placement_done = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.board = Board()
        self.ships_to_place = [Ship(s["name"], s["size"]) for s in SHIPS]
        self.current_idx = 0
        self.horizontal   = True
        self._preview_cells = []  # şu anda önizlenen hücreler
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #0a1628;")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("⚓ GEMİLERİNİ YERLEŞTİR")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #00d4ff;")
        layout.addWidget(title)

        self.ship_list_lbl = QLabel()
        self.ship_list_lbl.setAlignment(Qt.AlignCenter)
        self.ship_list_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        layout.addWidget(self.ship_list_lbl)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(
            "color: #ffaa00; font-size: 13px; "
            "background: #1a2a4a; border-radius: 8px; padding: 8px;"
        )
        layout.addWidget(self.info_label)

        self.dir_btn = QPushButton("↔ Yatay")
        self.dir_btn.setFixedHeight(40)
        self.dir_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.dir_btn.setStyleSheet("""
            QPushButton {
                background: #1a2a4a; color: #00d4ff;
                border: 1px solid #00d4ff; border-radius: 8px; padding: 6px 20px;
            }
            QPushButton:hover { background: #2a3a6a; }
        """)
        self.dir_btn.clicked.connect(self.toggle_direction)
        layout.addWidget(self.dir_btn, alignment=Qt.AlignCenter)

        self.board_widget = BoardWidget("📍 Kendi Tahtanız", clickable=True)
        self.board_widget.cell_clicked.connect(self.place_ship)
        self.board_widget.cell_hovered.connect(self.on_hover)
        self.board_widget.cell_unhovered.connect(self.clear_preview)
        layout.addWidget(self.board_widget, alignment=Qt.AlignCenter)

        self.update_info()

    # ── Hover önizleme ────────────────────────────────────────────────────────
    def _calc_positions(self, row, col):
        """Mevcut gemi için hesaplanan pozisyon listesi."""
        if self.current_idx >= len(self.ships_to_place):
            return []
        size = self.ships_to_place[self.current_idx].size
        positions = []
        for i in range(size):
            r = row if self.horizontal else row + i
            c = col + i if self.horizontal else col
            positions.append((r, c))
        return positions

    def on_hover(self, row, col):
        if self.current_idx >= len(self.ships_to_place):
            return
        self.clear_preview()
        positions = self._calc_positions(row, col)
        SIZE = 10
        # Geçerlilik kontrolü
        valid = True
        for r, c in positions:
            if not (0 <= r < SIZE and 0 <= c < SIZE):
                valid = False
                break
            if self.board_widget.cell_states.get((r, c)) == "ship":
                valid = False
                break
        style = "preview_ok" if valid else "preview_bad"
        for r, c in positions:
            if 0 <= r < SIZE and 0 <= c < SIZE:
                self.board_widget.set_preview(r, c, style)
                self._preview_cells.append((r, c))

    def clear_preview(self):
        for r, c in self._preview_cells:
            self.board_widget.restore_cell(r, c)
        self._preview_cells.clear()

    # ── Diğer metodlar ────────────────────────────────────────────────────────
    def update_info(self):
        items = []
        for i, s in enumerate(self.ships_to_place):
            prefix = "▶ " if i == self.current_idx else ("✅ " if i < self.current_idx else "  ")
            items.append(f"{prefix}{s.name} ({'█' * s.size}) [{s.size}]")
        self.ship_list_lbl.setText("   |   ".join(items))

        if self.current_idx < len(self.ships_to_place):
            ship = self.ships_to_place[self.current_idx]
            self.info_label.setText(
                f"Yerleştiriliyor: {ship.name} (Boyut: {ship.size}) "
                f"— {'↔ Yatay' if self.horizontal else '↕ Dikey'}"
            )
        else:
            self.info_label.setText("✅ Tüm gemiler yerleştirildi! Rakip bekleniyor...")

    def toggle_direction(self):
        self.horizontal = not self.horizontal
        self.dir_btn.setText("↔ Yatay" if self.horizontal else "↕ Dikey")
        self.update_info()

    def place_ship(self, row, col):
        if self.current_idx >= len(self.ships_to_place):
            return
        self.clear_preview()
        ship = self.ships_to_place[self.current_idx]
        success = self.board.place_ship(ship, row, col, self.horizontal)
        if success:
            for r, c in ship.positions:
                self.board_widget.set_cell(r, c, "ship")
            self.current_idx += 1
            self.update_info()
            if self.current_idx == len(self.ships_to_place):
                self.placement_done.emit(self.board.get_ships_data())
        else:
            self.info_label.setText("⚠️ Buraya yerleştirilemez, başka yer dene!")


# ─────────────────────────────────────────────────────────────────────────────
# Ana Oyun Ekranı
# ─────────────────────────────────────────────────────────────────────────────
class GameScreen(QWidget):
    shot_fired = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.my_board = Board()
        self.player_no = None
        self.my_turn = False

        # İstatistikler
        self.total_shots  = 0
        self.hits         = 0
        self.misses       = 0
        self.my_ships_left    = len(SHIPS)
        self.enemy_ships_left = len(SHIPS)

        # Zamanlayıcı
        self.elapsed = QTime(0, 0, 0)
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #080f1e;")
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── ÜST INFO PANELİ ─────────────────────────────────────────────────
        top_panel = QFrame()
        top_panel.setFixedHeight(100)
        top_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0a1628, stop:0.5 #0d1f3c, stop:1 #0a1628);
                border-bottom: 1px solid #1e3a5f;
            }
        """)
        panel_layout = QHBoxLayout(top_panel)
        panel_layout.setContentsMargins(16, 10, 16, 10)
        panel_layout.setSpacing(10)

        # Oyuncu rozeti
        self.player_badge = QLabel("P?")
        self.player_badge.setFixedSize(70, 70)
        self.player_badge.setAlignment(Qt.AlignCenter)
        self.player_badge.setFont(QFont("Arial", 22, QFont.Bold))
        self.player_badge.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #0d2a4a, stop:1 #0a1a33);
            color: #00d4ff;
            border: 2px solid #00d4ff;
            border-radius: 35px;
        """)
        panel_layout.addWidget(self.player_badge)

        # Durum etiketi (ortada büyük)
        status_block = QVBoxLayout()
        status_block.setSpacing(4)
        self.status_label = QLabel("Oyun yükleniyor...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.status_label.setStyleSheet("color: #ffaa00; background:transparent;")
        status_block.addWidget(self.status_label)

        self.sub_status = QLabel("")
        self.sub_status.setAlignment(Qt.AlignCenter)
        self.sub_status.setStyleSheet("color: #556677; font-size: 11px; background:transparent;")
        status_block.addWidget(self.sub_status)
        panel_layout.addLayout(status_block, stretch=1)

        # Stat kartları
        self.card_shots  = StatCard("🎯", "ATIŞ",    "0",  "#00d4ff")
        self.card_hits   = StatCard("💥", "İSABET",  "0",  "#ff4422")
        self.card_misses = StatCard("💨", "ISKALA",  "0",  "#556677")
        self.card_timer  = StatCard("⏱️", "SÜRE",   "0:00", "#ffaa00")
        self.card_my_ships    = StatCard("🛡️", "GEMİLERİM", str(len(SHIPS)), "#00ff88")
        self.card_enemy_ships = StatCard("☠️", "RAKİP",    str(len(SHIPS)), "#ff4422")

        for card in (self.card_shots, self.card_hits, self.card_misses,
                     self.card_timer, self.card_my_ships, self.card_enemy_ships):
            panel_layout.addWidget(card)

        root.addWidget(top_panel)

        # ── TAHTALAR ─────────────────────────────────────────────────────────
        boards_frame = QFrame()
        boards_frame.setStyleSheet("background: transparent;")
        boards_layout = QHBoxLayout(boards_frame)
        boards_layout.setContentsMargins(20, 16, 20, 16)
        boards_layout.setSpacing(40)

        self.my_board_widget    = BoardWidget("🛡️  Kendi Tahtanız", clickable=False)
        self.enemy_board_widget = BoardWidget("🎯  Rakip Tahtası",  clickable=True)
        self.enemy_board_widget.cell_clicked.connect(self.on_cell_clicked)

        boards_layout.addWidget(self.my_board_widget,    alignment=Qt.AlignCenter)

        # Orta ayırıcı
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #1e3a5f;")
        boards_layout.addWidget(sep)

        boards_layout.addWidget(self.enemy_board_widget, alignment=Qt.AlignCenter)
        root.addWidget(boards_frame, stretch=1)

    # ── Timer ────────────────────────────────────────────────────────────────
    def _tick(self):
        self.elapsed = self.elapsed.addSecs(1)
        self.card_timer.set_value(self.elapsed.toString("m:ss"))

    # ── Setup ────────────────────────────────────────────────────────────────
    def setup(self, player_no, ships_data):
        self.player_no = player_no
        badge_color = "#00d4ff" if player_no == 1 else "#ff8800"
        self.player_badge.setText(f"P{player_no}")
        self.player_badge.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #0d2a4a, stop:1 #0a1a33);
            color: {badge_color};
            border: 2px solid {badge_color};
            border-radius: 35px;
        """)
        self.sub_status.setText(f"Oyuncu {player_no} olarak oynuyorsunuz")

        for s in ships_data:
            for r, c in s["positions"]:
                self.my_board_widget.set_cell(r, c, "ship")

        self.timer.start(1000)

    # ── Sıra ─────────────────────────────────────────────────────────────────
    def set_turn(self, my_turn):
        self.my_turn = my_turn
        self.enemy_board_widget.set_clickable(my_turn)
        if my_turn:
            self.status_label.setText("🎯  Senin sıran!  Hedefe ateş et.")
            self.status_label.setStyleSheet("color: #00ff88; font-size:14px; font-weight:bold; background:transparent;")
        else:
            self.status_label.setText("⏳  Rakip hamlesi bekleniyor...")
            self.status_label.setStyleSheet("color: #ffaa00; font-size:14px; font-weight:bold; background:transparent;")

    # ── Tıklama ──────────────────────────────────────────────────────────────
    def on_cell_clicked(self, row, col):
        if self.my_turn:
            self.my_turn = False
            self.enemy_board_widget.set_clickable(False)
            self.shot_fired.emit(row, col)

    # ── Atış sonuçları ───────────────────────────────────────────────────────
    def mark_enemy_shot(self, row, col, result):
        """Bizim attığımız atışın sonucu"""
        state = "sunk" if result == "sunk" else result
        self.enemy_board_widget.set_cell(row, col, state)

        self.total_shots += 1
        self.card_shots.set_value(self.total_shots)

        if result in ("hit", "sunk"):
            self.hits += 1
            self.card_hits.set_value(self.hits)
            if result == "sunk":
                self.enemy_ships_left -= 1
                self.card_enemy_ships.set_value(self.enemy_ships_left)
                self.update_status(f"💥 Gemi battı! Rakipte {self.enemy_ships_left} gemi kaldı.", "#ff4422")
        else:
            self.misses += 1
            self.card_misses.set_value(self.misses)

    def mark_my_board(self, row, col, result):
        """Rakibin bize attığı atışın sonucu"""
        state = "sunk" if result == "sunk" else result
        self.my_board_widget.set_cell(row, col, state)

        if result == "sunk":
            self.my_ships_left -= 1
            self.card_my_ships.set_value(self.my_ships_left)
            self.update_status(f"💀 Bir gemimiz battı! {self.my_ships_left} gemi kaldı.", "#ff4422")

    def update_status(self, text, color="#ffaa00"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size:14px; font-weight:bold; background:transparent;"
        )