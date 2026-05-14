from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class EndScreen(QWidget):
    play_again = pyqtSignal()
    quit_game  = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #0a1628;")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)

        # Sonuç başlığı
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(QFont("Arial", 32, QFont.Bold))
        layout.addWidget(self.result_label)

        # Alt açıklama
        self.sub_label = QLabel("")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setFont(QFont("Arial", 14))
        self.sub_label.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(self.sub_label)

        layout.addSpacing(20)

        # Tekrar Oyna butonu
        self.play_btn = QPushButton("🔄 Tekrar Oyna")
        self.play_btn.setFixedSize(220, 50)
        self.play_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #0a1628;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #00ffff; }
        """)
        self.play_btn.clicked.connect(self.play_again.emit)
        layout.addWidget(self.play_btn, alignment=Qt.AlignCenter)

        # Çıkış butonu
        self.quit_btn = QPushButton("🚪 Çıkış")
        self.quit_btn.setFixedSize(220, 50)
        self.quit_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a2a4a;
                color: #ff4444;
                border: 1px solid #ff4444;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #2a1a1a; }
        """)
        self.quit_btn.clicked.connect(self.quit_game.emit)
        layout.addWidget(self.quit_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def show_result(self, won: bool):
        if won:
            self.result_label.setText("🏆 KAZANDIN!")
            self.result_label.setStyleSheet("color: #00ff88;")
            self.sub_label.setText("Tüm düşman gemilerini batırdın!\nTebrikler, Amiral!")
        else:
            self.result_label.setText("💀 KAYBETTİN!")
            self.result_label.setStyleSheet("color: #ff4444;")
            self.sub_label.setText("Gemilerin battı...\nBir dahaki sefere daha dikkatli ol!")
