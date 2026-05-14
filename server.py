import socket
import threading
import json
import random
import string

HOST = "0.0.0.0"
PORT = 5555

rooms = {}       # code → {"host_conn": conn, "host_addr": addr}
rooms_lock = threading.Lock()


def send_msg(conn, msg: dict):
    try:
        conn.sendall((json.dumps(msg) + "\n").encode())
    except Exception as e:
        print(f"[GÖNDERME HATASI] {e}")


def recv_line(conn, timeout=30) -> dict | None:
    conn.settimeout(timeout)
    buf = ""
    try:
        while True:
            chunk = conn.recv(4096).decode()
            if not chunk:
                return None
            buf += chunk
            if "\n" in buf:
                line, _ = buf.split("\n", 1)
                line = line.strip()
                if line:
                    return json.loads(line)
    except Exception:
        return None
    finally:
        conn.settimeout(None)


def gen_code(length=6) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        with rooms_lock:
            if code not in rooms:
                return code


def handle_client(conn, addr):
    """Her bağlantı için giriş akışı."""
    print(f"[+] Bağlantı: {addr}")

    # İlk mesajı oku (create veya join)
    msg = recv_line(conn, timeout=20)
    if not msg:
        conn.close()
        return

    action = msg.get("type")

    # ── ODA OLUŞTUR ──────────────────────────────────────────────────────
    if action == "create_room":
        code = gen_code()
        with rooms_lock:
            rooms[code] = {"host_conn": conn, "host_addr": addr}
        send_msg(conn, {"type": "room_created", "code": code})
        print(f"[ODA] Oluşturuldu: {code}  ({addr})")

        # Rakip bağlanana kadar bekle (başka thread handle eder)
        return  # Bu thread bitti, oda join edilince game thread başlıyor

    # ── ODAYA KATIL ──────────────────────────────────────────────────────
    elif action == "join_room":
        code = msg.get("code", "").strip().upper()

        with rooms_lock:
            room = rooms.pop(code, None)

        if room is None:
            send_msg(conn, {"type": "room_not_found", "msg": "Oda bulunamadı!"})
            conn.close()
            print(f"[ODA] Geçersiz kod: {code}  ({addr})")
            return

        host_conn = room["host_conn"]
        print(f"[ODA] {code} odasına katılındı: {addr}")

        # İkisini eşleştir
        t = threading.Thread(
            target=handle_game, args=(host_conn, conn), daemon=True
        )
        t.start()

    else:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Oyun Mantığı
# ─────────────────────────────────────────────────────────────────────────────
def handle_game(conn1, conn2):
    send_msg(conn1, {"type": "start", "player": 1})
    send_msg(conn2, {"type": "start", "player": 2})
    print("[SERVER] Oyun başladı!")

    # ── Gemi yerleştirme ──────────────────────────────────────────────────
    ships  = {}
    boards = {}

    def recv_placement(conn, player_no):
        buf = ""
        while True:
            try:
                chunk = conn.recv(4096).decode()
            except Exception:
                return
            if not chunk:
                return
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                msg = json.loads(line)
                if msg.get("type") == "ships_placed":
                    grid     = [[None] * 10 for _ in range(10)]
                    ship_hp  = {}
                    for ship in msg["ships"]:
                        name      = ship["name"]
                        positions = [tuple(p) for p in ship["positions"]]
                        ship_hp[name] = [len(positions), set()]
                        for r, c in positions:
                            grid[r][c] = name
                    boards[player_no] = {"grid": grid, "ship_hp": ship_hp}
                    return

    t1 = threading.Thread(target=recv_placement, args=(conn1, 1))
    t2 = threading.Thread(target=recv_placement, args=(conn2, 2))
    t1.start(); t2.start()
    t1.join();  t2.join()

    if 1 not in boards or 2 not in boards:
        print("[SERVER] Yerleştirme sırasında bağlantı kesildi.")
        return

    send_msg(conn1, {"type": "opponent_ready", "turn": 1})
    send_msg(conn2, {"type": "opponent_ready", "turn": 1})

    # ── Atış döngüsü ──────────────────────────────────────────────────────
    conns   = {1: conn1, 2: conn2}
    current = 1

    def recv_shot(conn) -> dict | None:
        buf = ""
        while True:
            try:
                chunk = conn.recv(4096).decode()
            except Exception:
                return None
            if not chunk:
                return None
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                msg = json.loads(line)
                if msg.get("type") == "shoot":
                    return msg

    while True:
        opponent      = 2 if current == 1 else 1
        shooter_conn  = conns[current]
        opponent_conn = conns[opponent]

        shot = recv_shot(shooter_conn)
        if shot is None:
            send_msg(opponent_conn, {"type": "opponent_disconnected"})
            print(f"[SERVER] P{current} bağlantısı kesildi.")
            break

        row, col = shot["row"], shot["col"]
        opp_board = boards[opponent]
        cell      = opp_board["grid"][row][col]

        if cell is None:
            result = "miss"
        else:
            opp_board["grid"][row][col] = None
            total, hit_set = opp_board["ship_hp"][cell]
            hit_set.add((row, col))
            result = "sunk" if len(hit_set) == total else "hit"

        all_sunk = all(len(hs) == tot for tot, hs in opp_board["ship_hp"].values())
        if all_sunk:
            send_msg(shooter_conn,  {"type": "game_over", "winner": current})
            send_msg(opponent_conn, {"type": "game_over", "winner": current})
            print(f"[SERVER] P{current} KAZANDI!")
            break

        next_turn = opponent if result == "miss" else current
        send_msg(shooter_conn,  {"type": "shot_result",   "row": row, "col": col, "result": result, "next_turn": next_turn})
        send_msg(opponent_conn, {"type": "incoming_shot", "row": row, "col": col, "result": result, "next_turn": next_turn})
        current = next_turn
        print(f"[P{current}→({row},{col})] {result} | Sıra: P{next_turn}")

    conn1.close()
    conn2.close()
    print("[SERVER] Oyun bitti.")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(20)
    print(f"[SERVER] {PORT} portunda dinleniyor...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()