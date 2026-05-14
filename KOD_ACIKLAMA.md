# 📡 server.py — Satır Satır Açıklama

> **Bu projenin asıl amacı:** TCP/IP soket programlamayı öğretmek.
> İki bilgisayarın birbiriyle nasıl konuştuğunu, verinin nasıl gittiğini,
> çoklu kullanıcıların nasıl yönetildiğini görmek.

---

## Önce Temel Kavramlar

### Python'da Fonksiyon nedir?
```python
def merhaba(isim):
    print("Merhaba " + isim)

merhaba("Ali")  # → "Merhaba Ali"
```
`def` ile tanımlanır. Parantez içindekiler **parametre** (giriş verisi).

### Python'da Class nedir?
Class = bir şablondur. O şablondan istediğin kadar nesne (object) üretirsin.

```python
class Araba:
    def __init__(self, renk):   # __init__ = nesne oluşturulunca çalışır
        self.renk = renk        # self = "bu nesnenin" verisi

    def bilgi_ver(self):
        print("Renk:", self.renk)

bmw = Araba("kırmızı")   # yeni bir Araba nesnesi
bmw.bilgi_ver()           # → "Renk: kırmızı"
```

`self` her zaman o anki nesneyi temsil eder. Class'ı tarif, `Araba(...)` ile nesneyi üretirsin.

---

## server.py — Bölüm 1: Import ve Global Değişkenler

```python
import socket      # TCP bağlantı kurma
import threading   # Aynı anda birden fazla iş yapma
import json        # Veriyi metin formatına çevirme
import random      # Rastgele kod üretme
import string      # Harf/rakam listeleri

HOST = "0.0.0.0"   # Tüm ağ arayüzlerinden bağlantı kabul et
PORT = 5555        # Hangi kapıdan dinleyeceğiz

rooms = {}         # Oda kodları burada tutulur: {"A3K7": {conn, addr}}
rooms_lock = threading.Lock()  # İki thread aynı anda rooms'a dokunmasın
```

### `"0.0.0.0"` ne demek?
Sunucu birden fazla ağ arayüzüne sahip olabilir (WiFi, Ethernet, loopback...).
`"0.0.0.0"` = "hepsinden bağlantı kabul et". `"127.0.0.1"` yazsaydık sadece
aynı makineden bağlanılabilirdi.

### `threading.Lock()` neden gerekli?
İki kullanıcı aynı anda bağlanırsa, iki ayrı thread aynı anda `rooms` sözlüğünü
değiştirmeye çalışır. Bu veri bozulmasına yol açar (race condition).
Lock, "bu an sadece bir kişi değiştirebilir" der.

```python
with rooms_lock:          # Kilidi al
    rooms[code] = {...}   # Güvenle yaz
# with bloğu bitince kilit otomatik bırakılır
```

---

## server.py — Bölüm 2: send_msg Fonksiyonu

```python
def send_msg(conn, msg: dict):
    try:
        conn.sendall((json.dumps(msg) + "\n").encode())
    except Exception as e:
        print(f"[GÖNDERME HATASI] {e}")
```

### Satır satır:

| Satır | Ne yapar? |
|-------|-----------|
| `json.dumps(msg)` | `{"type": "start", "player": 1}` → `'{"type": "start", "player": 1}'` |
| `+ "\n"` | Sonuna satır sonu ekle (alıcı bunu bekliyor) |
| `.encode()` | Python string → byte dizisi (TCP sadece byte gönderir) |
| `conn.sendall(...)` | Tüm byte'ları gönder (sendall = hepsi gidene kadar dur) |
| `try/except` | Bağlantı kopuksa hata vermeden devam et |

---

## server.py — Bölüm 3: recv_line Fonksiyonu

```python
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
```

### TCP'nin Önemli Özelliği: Akış Protokolü

TCP bir **boru** gibidir. Gönderilen paketler karşı tarafta birleşebilir ya da bölünebilir:

```
Gönderilen:  {"type":"start"}\n{"type":"waiting"}\n
Alınan (1):  {"type":"sta
Alınan (2):  rt"}\n{"type":"waiting"}\n
```

Bu yüzden **buffer (tampon)** kullanırız:

```
buf = ""
buf += '{"type":"sta'          → buf = '{"type":"sta'
buf += 'rt"}\n{"type":"w...'   → buf = '{"type":"start"}\n{"type":"w...'
"\n" var mı? EVET → ilk satırı ayır → parse et
```

### `buf.split("\n", 1)` ne yapar?
```python
buf = '{"type":"start"}\n{"type":"waiting"}\n'
line, _ = buf.split("\n", 1)
# line = '{"type":"start"}'
# _    = '{"type":"waiting"}\n'   (geri kalanı)
```
`1` parametresi: "sadece ilk `\n`'de kes, daha fazla kesme."

### `finally` bloğu ne zaman çalışır?
Her zaman — `try` başarılı olsa da, `except` çalışsa da.
Burada timeout'u sıfırlıyoruz: `conn.settimeout(None)` = sonsuz bekle (timeout yok).

---

## server.py — Bölüm 4: gen_code (Oda Kodu Üretme)

```python
def gen_code(length=6) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        with rooms_lock:
            if code not in rooms:
                return code
```

### Adım adım:
```python
string.ascii_uppercase  # → "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
string.digits           # → "0123456789"
chars = "ABCDE...Z0123456789"   # 36 karakter

random.choices(chars, k=6)
# → ["A", "3", "K", "7", "P", "2"]

"".join(["A", "3", "K", "7", "P", "2"])
# → "A3K7P2"
```

### Neden `while True`?
Çok düşük ihtimalle üretilen kod zaten kullanımda olabilir.
Böyle olursa tekrar dener. `if code not in rooms: return` der ki
"bu kod yoksa kullan ve çık, varsa tekrar üret."

---

## server.py — Bölüm 5: handle_client (Her Bağlantının Karşılanması)

```python
def handle_client(conn, addr):
    print(f"[+] Bağlantı: {addr}")

    msg = recv_line(conn, timeout=20)
    if not msg:
        conn.close()
        return

    action = msg.get("type")

    if action == "create_room":
        code = gen_code()
        with rooms_lock:
            rooms[code] = {"host_conn": conn, "host_addr": addr}
        send_msg(conn, {"type": "room_created", "code": code})
        return

    elif action == "join_room":
        code = msg.get("code", "").strip().upper()
        with rooms_lock:
            room = rooms.pop(code, None)

        if room is None:
            send_msg(conn, {"type": "room_not_found"})
            conn.close()
            return

        host_conn = room["host_conn"]
        t = threading.Thread(
            target=handle_game, args=(host_conn, conn), daemon=True
        )
        t.start()
```

### Bu fonksiyon nasıl çağrılıyor?

`main()` fonksiyonunda her bağlantı için ayrı thread başlatılıyor:
```python
conn, addr = server.accept()
threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
```

Yani 10 kişi aynı anda bağlansa → 10 ayrı thread → 10 ayrı `handle_client`.
Birbirini bloklamıyorlar.

### `msg.get("type")` neden `.get()` kullanıyor?
```python
msg = {"type": "create_room"}

msg["type"]      # → "create_room"  (key yoksa: KeyError — hata!)
msg.get("type")  # → "create_room"  (key yoksa: None — güvenli)
```

### `rooms.pop(code, None)` ne yapar?
```python
rooms = {"A3K7": {...}, "B9X2": {...}}
rooms.pop("A3K7", None)
# → {"host_conn": ..., "host_addr": ...}  (siler ve döndürür)
# rooms artık sadece {"B9X2": {...}}

rooms.pop("XXXX", None)
# → None  (bulamadı, hata vermedi)
```

`pop` ile hem siliyoruz hem alıyoruz — iki kişinin aynı odaya girememesini garantileyiz.

---

## server.py — Bölüm 6: main() — Server'ı Başlatma

```python
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(20)
    print(f"[SERVER] {PORT} portunda dinleniyor...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
```

### Soket kurulum adımları:

```
socket()   → "Bir telefon al"
bind()     → "Bu numaraya bağla (IP:Port)"
listen()   → "Çalmaya başla, 20 kişi kuyrukta bekleyebilir"
accept()   → "Telefonu aç — birisi var!" (bloke eder, bağlantı gelene kadar bekler)
```

### `AF_INET` ve `SOCK_STREAM` ne demek?
```
AF_INET      = IPv4 kullan (192.168.x.x tarzı adresler)
SOCK_STREAM  = TCP kullan (güvenilir, sıralı, bağlantı tabanlı)
```
`SOCK_DGRAM` olsaydı UDP olurdu (güvenilmez ama hızlı — video streaming gibi).

### `SO_REUSEADDR` neden var?
Server kapandıktan hemen sonra aynı porta tekrar bind etmeye çalışırsan
işletim sistemi "bu port hâlâ meşgul" diyebilir (birkaç saniye bekletir).
`SO_REUSEADDR = 1` bu beklemeyi devre dışı bırakır.
Geliştirme sırasında server'ı sık sık yeniden başlatırken çok işe yarar.

### `daemon=True` ne demek?
Ana program (main thread) kapandığında, daemon thread'ler otomatik ölür.
`daemon=False` olsaydı, oyun thread'leri çalışırken programı kapatamayabilirdin.

---

## Tüm Akışın Özeti (Sunumda Anlatacağın)

```
1. server.py başlatılır → port 5555'te dinler

2. P1 bağlanır
   → handle_client thread'i başlar
   → "create_room" mesajı gelir
   → Rastgele "A3K7P2" kodu üretilir
   → rooms["A3K7P2"] = P1'in bağlantısı
   → P1'e kod gönderilir, thread biter (ama bağlantı açık!)

3. P2 bağlanır
   → handle_client thread'i başlar
   → "join_room" + {"code": "A3K7P2"} gelir
   → rooms'tan "A3K7P2" alınır (ve silinir)
   → P1 ve P2 bağlantıları handle_game'e verilir

4. handle_game çalışır:
   → Her ikisine "start" gönderilir
   → Her ikisinden "ships_placed" beklenir (ayrı thread)
   → Her ikisine "opponent_ready" gönderilir
   → Atış döngüsü başlar: shoot → hesapla → shot_result + incoming_shot
   → Tüm gemiler batınca → "game_over" → bağlantılar kapatılır
```

---

## Sonraki Adım

Bir sonraki dosyayı hangisini açıklamamı istersin?

- **`client_socket.py`** → Client'ın ağ kısmı, QThread nedir, nasıl çalışır
- **`board.py` + `ship.py`** → Oyun mantığı, class kullanımı detaylı
- **`game_screen.py`** → UI, sinyal sistemi (signal/slot), hover önizleme

