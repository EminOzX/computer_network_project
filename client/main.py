import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from ui.start_screen   import StartScreen
from ui.game_screen    import GameScreen, PlacementWidget
from ui.end_screen     import EndScreen
from network.client_socket import ClientSocket


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚓ Amiral Battı")
        self.setMinimumSize(940, 720)
        self.setStyleSheet("background-color: #080f1e;")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_screen     = StartScreen()
        self.placement_widget = PlacementWidget()
        self.game_screen      = GameScreen()
        self.end_screen       = EndScreen()

        self.stack.addWidget(self.start_screen)      # 0
        self.stack.addWidget(self.placement_widget)  # 1
        self.stack.addWidget(self.game_screen)       # 2
        self.stack.addWidget(self.end_screen)        # 3

        self.socket     = None
        self.player_no  = None
        self.ships_data = None

        # Sinyaller
        self.start_screen.create_room.connect(self.on_create_room)
        self.start_screen.join_room.connect(self.on_join_room)
        self.placement_widget.placement_done.connect(self.on_placement_done)
        self.game_screen.shot_fired.connect(self.on_shot_fired)
        self.end_screen.play_again.connect(self.on_play_again)
        self.end_screen.quit_game.connect(self.close)

        self.stack.setCurrentIndex(0)

    # ── Soket oluştur ─────────────────────────────────────────────────────────
    def _make_socket(self, host, port) -> bool:
        self.socket = ClientSocket(host, port)
        if not self.socket.connect_to_server():
            self.start_screen.set_status("❌ Sunucuya bağlanılamadı!", "#ff4444")
            self.start_screen.reset()
            return False
        self.socket.message_received.connect(self.on_message)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.start()
        return True

    # ── Oda oluştur ───────────────────────────────────────────────────────────
    def on_create_room(self, host: str, port: int):
        if not self._make_socket(host, port):
            return
        self.socket.send({"type": "create_room"})

    # ── Odaya katıl ───────────────────────────────────────────────────────────
    def on_join_room(self, host: str, port: int, code: str):
        if not self._make_socket(host, port):
            return
        self.socket.send({"type": "join_room", "code": code})

    # ── Sunucudan mesaj ───────────────────────────────────────────────────────
    def on_message(self, msg: dict):
        t = msg.get("type")

        if t == "room_created":
            code = msg.get("code", "???")
            self.start_screen.show_room_code(code)

        elif t == "room_not_found":
            self.start_screen.set_status("❌ Oda bulunamadı! Kodu kontrol et.", "#ff4444")
            self.start_screen.reset()

        elif t == "start":
            self.player_no = msg.get("player")
            self.stack.setCurrentIndex(1)  # Gemi yerleştirme

        elif t == "opponent_ready":
            turn = msg.get("turn")
            self.stack.setCurrentIndex(2)
            self.game_screen.setup(self.player_no, self.ships_data)
            self.game_screen.set_turn(turn == self.player_no)

        elif t == "shot_result":
            row, col, result = msg["row"], msg["col"], msg["result"]
            self.game_screen.mark_enemy_shot(row, col, result)
            next_turn = msg.get("next_turn")
            if next_turn is not None:
                self.game_screen.set_turn(next_turn == self.player_no)

        elif t == "incoming_shot":
            row, col, result = msg["row"], msg["col"], msg["result"]
            self.game_screen.mark_my_board(row, col, result)
            next_turn = msg.get("next_turn")
            if next_turn is not None:
                self.game_screen.set_turn(next_turn == self.player_no)

        elif t == "game_over":
            won = msg.get("winner") == self.player_no
            self.stack.setCurrentIndex(3)
            self.end_screen.show_result(won)

        elif t == "opponent_disconnected":
            self.game_screen.update_status("⚠️ Rakip bağlantısı kesildi!", "#ff4444")
            self.stack.setCurrentIndex(3)
            self.end_screen.show_result(True)

    # ── Gemi yerleştirme tamamlandı ───────────────────────────────────────────
    def on_placement_done(self, ships_data: list):
        self.ships_data = ships_data
        self.socket.send({"type": "ships_placed", "ships": ships_data})

    # ── Atış ──────────────────────────────────────────────────────────────────
    def on_shot_fired(self, row: int, col: int):
        self.socket.send({"type": "shoot", "row": row, "col": col})
        self.game_screen.update_status("🎯 Atış yapıldı, sonuç bekleniyor...", "#ffaa00")

    # ── Bağlantı kesildi ──────────────────────────────────────────────────────
    def on_disconnected(self):
        print("[CLIENT] Bağlantı kesildi.")

    # ── Tekrar oyna ───────────────────────────────────────────────────────────
    def on_play_again(self):
        if self.socket:
            self.socket.disconnect()
            self.socket = None

        self.stack.removeWidget(self.placement_widget)
        self.placement_widget = PlacementWidget()
        self.placement_widget.placement_done.connect(self.on_placement_done)
        self.stack.insertWidget(1, self.placement_widget)

        self.stack.removeWidget(self.game_screen)
        self.game_screen = GameScreen()
        self.game_screen.shot_fired.connect(self.on_shot_fired)
        self.stack.insertWidget(2, self.game_screen)

        self.start_screen.reset()
        self.stack.setCurrentIndex(0)

    def closeEvent(self, event):
        if self.socket:
            self.socket.disconnect()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Amiral Battı")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
