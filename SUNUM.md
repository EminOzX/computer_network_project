# ⚓ Amiral Battı — Sunum Rehberi

## İçindekiler
1. [Projeye Genel Bakış](#1-projeye-genel-bakış)
2. [Kullanılan Teknolojiler ve Kütüphaneler](#2-kullanılan-teknolojiler)
3. [AWS Nedir? EC2 Nedir?](#3-aws-nedir-ec2-nedir)
4. [Mimari: Neyin Nerede Çalıştığı](#4-mimari)
5. [Ağ Protokolü](#5-ağ-protokolü)
6. [Kodu Server'a Nasıl Yükledik?](#6-kodu-servera-nasıl-yükledik)
7. [Karşılaşılan Sorunlar](#7-karşılaşılan-sorunlar)
8. [Farklı Ağlardan Bağlanabilir mi?](#8-farklı-ağlardan-bağlanabilir-mi)
9. [İyi Yönler](#9-i̇yi-yönler)
10. [Eksik Yönler](#10-eksik-yönler)
11. [Python Kullanmanın Artıları](#11-python-artıları)
12. [Sunumda Vurgulanacaklar](#12-sunumda-vurgulanacaklar)

---

## 1. Projeye Genel Bakış

İki oyunculu, gerçek zamanlı, ağ üzerinden oynanan Amiral Battı oyunu.

- **İstemci (Client):** Oyuncunun bilgisayarında çalışan PyQt5 masaüstü uygulaması
- **Sunucu (Server):** AWS EC2 bulut sunucusunda 7/24 çalışan Python TCP sunucusu
- **Bağlantı:** Standart TCP/IP soketleri + JSON mesajlaşma protokolü

### Oyun Akışı:
```
P1 → Oda Oluştur → 6 haneli KOD alır → Rakibini bekler
P2 → Odaya Katıl → KOD girer        → Eşleşme sağlanır
         ↓
   Her iki oyuncu gemilerini yerleştirir (hover önizleme ile)
         ↓
   Sıra tabanlı atış döngüsü: hit / miss / sunk
         ↓
   Tüm gemiler batınca → Kazandın / Kaybettin ekranı
         ↓
   Tekrar Oyna → Başa döner (yeni oda kodu ile)
```

---

## 2. Kullanılan Teknolojiler

| Kütüphane | Neden Kullandık |
|-----------|----------------|
| **PyQt5** | Çok platformlu, profesyonel GUI framework. Qt sinyaline dayalı event sistemi ağ + UI entegrasyonunu kolaylaştırdı. |
| **socket** (stdlib) | Python'un yerleşik TCP soket kütüphanesi. Harici bağımlılık yok. |
| **threading** (stdlib) | Server'da her oyun kendi thread'inde. Client'ta ağ okuma arka planda çalışır. |
| **json** (stdlib) | İnsan okunabilir mesaj formatı. Debug etmesi kolay. |
| **QThread** | `ClientSocket`, Qt event loop'una entegre — ana thread (UI) hiç bloklanmaz. |

### Neden harici ağ kütüphanesi kullanmadık?
Raw socket ile kendi protokolümüzü yazdık: tampon yönetimi, çoklu thread, JSON serialization. Bu, **ağ programlamasının temelini** elle göstermek demek.

---

## 3. AWS Nedir? EC2 Nedir?

### AWS (Amazon Web Services)
Amazon'un bulut bilişim platformu. 200+ hizmet sunar. Biz sunucu kiralamak için kullandık.

### EC2 (Elastic Compute Cloud)
AWS'nin sanal makine hizmetidir. Fiziksel sunucu satın almak yerine bulutta dakikalar içinde Linux makinesi başlatabilirsin.

### Free Tier Kullanımımız
```
Instance Tipi  : t2.micro (1 vCPU, 1 GB RAM)
İşletim Sistemi: Ubuntu 22.04 LTS
Bölge          : Frankfurt (eu-central-1)
Ücretsiz kullanım: Ayda 750 saat (= her zaman açık)
```

**Security Group (güvenlik duvarı) ayarları:**
| Port | Protokol | Amaç |
|------|----------|------|
| 22 | SSH/TCP | Sunucuya terminal erişimi |
| 5555 | TCP | Oyun trafiği (tüm IP'lere açık) |

---

## 4. Mimari

```
┌──────────────────────────────────────────────┐
│           OYUNCUNUN BİLGİSAYARI              │
│                                              │
│  client/                                     │
│  ├── main.py          ← Giriş + sinyal yön.  │
│  ├── ui/                                     │
│  │   ├── start_screen.py  ← Oda kodu ekranı  │
│  │   ├── game_screen.py   ← Tahtalar + stat  │
│  │   └── end_screen.py    ← Oyun sonu        │
│  ├── game/                                   │
│  │   ├── ship.py      ← Gemi mantığı         │
│  │   └── board.py     ← 10×10 tahta          │
│  └── network/                                │
│      └── client_socket.py ← TCP (QThread)    │
└────────────────┬─────────────────────────────┘
                 │  TCP/IP  port 5555  (JSON)
┌────────────────▼─────────────────────────────┐
│         AWS EC2 — 18.184.13.71               │
│                                              │
│  server.py                                   │
│  ├── handle_client()  ← Thread/bağlantı      │
│  ├── create_room()    ← 6 haneli kod üret    │
│  ├── join_room()      ← Eşleştir + başlat   │
│  └── handle_game()    ← Atış mantığı         │
└──────────────────────────────────────────────┘
```

### Lokalde vs Server'da Ne Çalışıyor?

| Lokalde (Client) | Server'da |
|---|---|
| Arayüz çizimi, animasyon | Oda kodu üretimi |
| Gemi yerleştirme mantığı | İki oyuncuyu eşleştirme |
| Hover önizleme | Atış sonucunu hesaplama |
| Tıklama olayları | Sıra yönetimi |
| İstatistik gösterimi | Oyun sonu tespiti |

---

## 5. Ağ Protokolü

Her mesaj: **JSON satırı + `\n`** karakteri

```json
{"type": "shoot", "row": 3, "col": 5}
{"type": "shot_result", "result": "hit", "next_turn": 1}
```

### Mesaj Akışı:
```
CLIENT-1                    SERVER                   CLIENT-2
  │                           │                          │
  │── create_room ───────────►│                          │
  │◄─ room_created {code} ────│                          │
  │                           │◄──── join_room {code} ───│
  │◄─ start {player:1} ───────│───── start {player:2} ──►│
  │── ships_placed ──────────►│◄──── ships_placed ────────│
  │◄─ opponent_ready {turn:1}─│───── opponent_ready ─────►│
  │── shoot {row,col} ───────►│                          │
  │◄─ shot_result {hit} ──────│───── incoming_shot ──────►│
  │◄─ game_over {winner:1} ───│───── game_over ──────────►│
```

### TCP Tampon Yönetimi:
TCP bir akış protokolüdür — paketler birleşebilir. Her iki taraf da buffer tutar:
```python
buffer += conn.recv(4096).decode()
while "\n" in buffer:
    line, buffer = buffer.split("\n", 1)
    msg = json.loads(line)
    # işle...
```

---

## 6. Kodu Server'a Nasıl Yükledik?

### Adım 1: EC2 Instance Başlatma
AWS Console → EC2 → Launch Instance → Ubuntu 22.04 → t2.micro → Key Pair oluştur → Security Group'ta 5555 portunu aç

### Adım 2: PEM Dosyası İzni (Windows)
```powershell
icacls "amiral-batti-server.pem" /inheritance:r /grant:r "$($env:USERNAME):R"
```
SSH, özel anahtar dosyası başkaları tarafından okunabilirse bağlantıyı reddeder.

### Adım 3: Dosyayı SCP ile Yükleme
```bash
scp -i amiral-batti-server.pem server.py ubuntu@18.184.13.71:/home/ubuntu/
```

### Adım 4: Server'ı Arka Planda Başlatma
```bash
ssh -i amiral-batti-server.pem ubuntu@18.184.13.71 \
  "nohup python3 server.py > server.log 2>&1 &"
```
`nohup` = SSH kapansa bile process çalışmaya devam eder.

### Güncelleme Döngüsü:
```
Kodu düzenle → scp ile gönder → eski PID'i kill et → yeniden başlat
```

---

## 7. Karşılaşılan Sorunlar

### Sorun 1: Ghost Connection (Hayalet Bağlantı)
**Problem:** Orijinal server sıralı `accept()` yapıyordu. Bir oyuncu bağlanıp bağlantıyı kesip tekrar bağlanınca, server onu ikinci oyuncu sanıp kendiyle oyun başlatıyordu.

**Çözüm:** Oda kodu sistemi. Her bağlantı `create_room` veya `join_room` gönderiyor. Sadece aynı kodu paylaşan iki bağlantı eşleşiyor.

---

### Sorun 2: Sıra Geçişi Çalışmıyordu
**Problem:** `incoming_shot` mesajı `next_turn` bilgisi taşımıyordu. Player 2 sırasının kendisine geçtiğini öğrenemiyordu — iki ekran da "Rakip bekleniyor" yazıyordu.

**Çözüm:** Server `incoming_shot` mesajına `next_turn` eklendi. Client bu değeri okuyup `set_turn()` çağırıyor.

---

### Sorun 3: PEM Dosyası İzin Hatası
**Problem:** Windows'ta dosya başka kullanıcılar tarafından okunabilir durumdaydı. SSH "bad permissions" hatası verdi.

**Çözüm:** `icacls` ile dosya izinleri sadece mevcut kullanıcıya verildi.

---

### Sorun 4: UI Donması
**Problem:** Ağ okuma işlemi ana thread'de yapılsaydı `recv()` bloke olur, pencere donardı.

**Çözüm:** `ClientSocket`, `QThread`'den türetildi. Ağ okuma arka planda çalışır, mesajlar `pyqtSignal` ile UI thread'ine iletilir.

---

## 8. Farklı Ağlardan Bağlanabilir mi?

**EVET.** Bu projenin en güçlü özelliği.

Server **AWS public IP**'de çalışıyor. İnternet erişimi olan herkes bağlanabilir:

```
[Oyuncu A — Ev WiFi]          [Oyuncu B — Okul Ağı]
        │                               │
        └──────── internet ─────────────┘
                       │
                [AWS Frankfurt]
                18.184.13.71:5555
```

Lokal sunucu kullansaydık sadece aynı WiFi'daki cihazlar bağlanabilirdi.

---

## 9. İyi Yönler

### ✅ Gerçek Ağ Programlama
Ham TCP soket, kendi tampon yönetimi, kendi protokol tasarımı. WebSocket kütüphanesi ya da oyun motoru kullanmadık.

### ✅ Bulut Sunucu
AWS EC2 üzerinde, 7/24 erişilebilir, gerçek public IP ile. Proje gereksinimini tam karşılıyor.

### ✅ Oda Kodu Sistemi
Birden fazla oyun aynı anda bağımsız çalışabilir. Ghost connection sorunu çözüldü.

### ✅ Kullanıcı Deneyimi
- Hover önizleme (yeşil = geçerli, kırmızı = geçersiz)
- Canlı istatistik kartları (atış, isabet, süre, kalan gemi)
- Animasyonlu giriş ekranı (dalga efekti)
- Oyun sonu + tekrar oyna

### ✅ Temiz Mimari
`game/` oyun mantığını, `network/` bağlantıyı, `ui/` görünümü bilir. Birbirinden bağımsız.

---

## 10. Eksik Yönler

### ❌ Server Taraflı Doğrulama Yok
Server, client'tan gelen koordinatları körce kabul ediyor. Hile yapılabilir.

### ❌ Yeniden Bağlanma Yok
Bağlantı koparsa oyun kayboluyor. Oturum ID + durum kaydetme gerekir.

### ❌ Şifreleme Yok
Mesajlar düz metin TCP üzerinden gidiyor. Gerçek üründe TLS şart.

### ❌ Ölçekleme Yok
t2.micro (1 vCPU, 1 GB RAM). Çok sayıda eş zamanlı oyunda performans düşer.

### ❌ Veri Kalıcılığı Yok
Skor tablosu, kullanıcı hesabı, oyun geçmişi yok.

### ❌ Mobil / Web Desteği Yok
Sadece masaüstü PyQt5 uygulaması.

### ❌ Server Otomatik Yeniden Başlatma Yok
Server çökerse elle müdahale gerekiyor. `systemd` veya `supervisor` ile otomatik restart eklenebilir.

---

## 11. Python Artıları

| Avantaj | Açıklama |
|---------|----------|
| **Hızlı geliştirme** | C++ ile aynı proje 3-5 kat daha uzun sürerdi |
| **stdlib zenginliği** | `socket`, `threading`, `json` harici bağımlılık gerektirmez |
| **PyQt5** | Qt'nun tüm gücü Python'dan |
| **AWS uyumu** | Ubuntu'da Python3 hazır kurulu, ek adım yok |
| **Okunabilirlik** | Ağ + UI + mantık aynı dilde, takip edilebilir |
| **Cross-platform** | Windows/Mac/Linux'ta aynı client çalışır |

---

## 12. Sunumda Vurgulanacaklar

### Sık Sorulabilecek Sorular

**"Sunucu ne yapıyor, client ne yapıyor?"**
> Client sadece ekrana çizer ve tıklamayı server'a iletir. Kimin vurduğu, sıranın kime geçtiği, oyunun bitip bitmediğini server hesaplar.

**"Neden AWS?"**
> Lokal sunucu kullansaydık aynı WiFi zorunlu olurdu. AWS ile internet bağlantısı olan herkes, dünyanın herhangi bir yerinden bağlanabilir.

**"Thread neden gerekli?"**
> `recv()` veri gelene kadar bloke olur. Bunu ana thread'de yapsaydık pencere donardı. QThread ile arka planda çalışır, pyqtSignal ile UI'ye mesaj iletilir.

**"Protokol nedir?"**
> Her mesaj JSON + satır sonu. Tek bağlantıda çok mesaj gideceği için buffer tutuyoruz, tam satır gelince parse ediyoruz.

---

### Demo Sırası (Önerilen)

1. İki `python main.py` penceresi aç
2. P1: **Oda Oluştur** → 6 haneli kodu göster
3. P2: **Odaya Katıl** → kodu gir
4. Gemi yerleştirme → hover önizlemesini göster
5. Birkaç atış → istatistik kartlarının değiştiğini göster
6. AWS Console'u göster → server hâlâ çalışıyor

---

## Dosya Yapısı

```
amiral-batti/
├── server.py              ← AWS EC2'de çalışan sunucu
├── SUNUM.md               ← Bu dosya
└── client/
    ├── main.py            ← Uygulama giriş noktası
    ├── game/
    │   ├── ship.py        ← Ship sınıfı
    │   └── board.py       ← Board sınıfı
    ├── network/
    │   └── client_socket.py  ← QThread tabanlı TCP istemci
    └── ui/
        ├── start_screen.py   ← Giriş + oda kodu
        ├── game_screen.py    ← Tahtalar + stat kartları
        └── end_screen.py     ← Oyun sonu
```

*Sunucu IP: 18.184.13.71 | Port: 5555 | Son teslim: 14 Mayıs 2026*
