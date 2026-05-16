# ⚓ Amiral Battı (Battleship) Multiplayer Oyunu

Bilgisayar Ağları dersi kapsamında geliştirilmiş, iki oyunculu, gerçek zamanlı ve bulut sunucu (AWS) üzerinden TCP/IP soketleri ile haberleşen Amiral Battı masaüstü oyunudur.

## 🏗️ Proje Mimarisi

Proje **İstemci-Sunucu (Client-Server)** mimarisine tam uygun olarak tasarlanmıştır.

- **Sunucu (Server):** AWS EC2 (Ubuntu) üzerinde 7/24 çalışan, arayüzü olmayan (konsol tabanlı) bir Python uygulamasıdır. `socket` ve `threading` kullanılarak her oyuncu bağlantısı eş zamanlı (paralel) yönetilir. Oyunun tüm karar mekanizması, hile koruması, eşleştirmeler ve atış hesaplamaları tamamen sunucuda gerçekleşir.
- **İstemci (Client):** Oyuncuların kendi bilgisayarlarında çalışan `PyQt5` tabanlı masaüstü uygulamasıdır. Kullanıcıya görsel arayüz (GUI) sunar. Oyun arayüzünün donmasını engellemek için ağ üzerinden gelen verileri dinleme işlemi arka planda `QThread` (İş parçacığı) kullanılarak yapılmıştır.

## 🚀 Kurulum ve Çalıştırma

### Sistem Gereksinimleri
- Python 3.8 veya üzeri
- PyQt5 kütüphanesi

```bash
pip install PyQt5
```

### Sunucu (AWS) Tarafı
Oyunun sunucu kısmı hali hazırda AWS EC2 üzerinde kesintisiz çalışmaktadır. Eğer projeyi geliştirme amacıyla kendi bilgisayarınızda (lokalde) çalıştırmak isterseniz:
```bash
python server.py
```
*(Sunucu varsayılan olarak `0.0.0.0:5555` portunu dinlemeye başlar.)*

### İstemci (Oyuncu) Tarafı
Oynamak isteyen her oyuncunun bilgisayarında aşağıdaki komutla istemci uygulamasını başlatması gerekir:
```bash
cd client
python main.py
```

## 🎮 Nasıl Oynanır?

1. **Oda Kurma:** Birinci oyuncu oyunu açıp "Oda Oluştur" butonuna tıklar. Sunucu ona benzersiz 6 haneli bir "Oda Kodu" verir (Örn: `A1B2C3`).
2. **Odaya Katılma:** İkinci oyuncu oyunu açıp "Odaya Katıl" butonuna tıklar ve arkadaşının verdiği 6 haneli kodu girer.
3. **Gemi Yerleştirme:** İki oyuncu da kendi tahtalarına 5 adet gemiyi tıklayarak (yatay/dikey seçimiyle) yerleştirir.
4. **Savaş Aşaması:** Tüm gemiler yerleştiğinde Savaş Ekranı açılır. Sırası gelen oyuncu rakibin tahtasına tıklayarak atış yapar.
5. Tüm gemileri batan ilk oyuncu oyunu kaybeder.

## 📡 Ağ Protokolü ve Haberleşme

İstemci ve sunucu arasındaki iletişim, hazır/yüksek seviye kütüphaneler (WebSocket vb.) kullanılmadan, saf **TCP Soketleri** üzerinden özel bir JSON formatı ile sağlanmaktadır. 

TCP'nin akışkan (stream) yapısından kaynaklı paket birleşme/bölünme ihtimaline karşı özel bir **Tampon (Buffer)** mekanizması geliştirilmiştir. Her JSON mesajının sonuna `\n` karakteri eklenerek mesajlar tampon içinde kusursuzca ayrıştırılır.

### Örnek Protokol Mesajları:
- **İstemciden Sunucuya:** `{"type": "shoot", "row": 3, "col": 5}`
- **Sunucudan İstemciye:** `{"type": "shot_result", "row": 3, "col": 5, "result": "hit", "next_turn": 2}`

---

## 📝 Proje Raporu (Değerlendirme Kriterleri)

Bu bölüm, "Bilgisayar Ağları" dersi proje gereksinimleri doğrultusunda hazırlanmıştır.

1. **Gereksinimlerin Karşılanması:**
   - Tüm geliştirme süreci istenildiği gibi **Python** programlama dili ile yapılmıştır.
   - Grafik arayüz için dış kütüphane olarak **PyQt5** kullanılmıştır. Uygulama son kullanıcı odaklı ve görsel olarak tatmin edicidir.
   - Sunucu uygulaması grafik arayüze sahip olmayan bir konsol uygulamasıdır ve AWS EC2 üzerinde çalıştırılmaktadır.
   - İstemci (Client) uygulaması `18.184.13.71` (AWS IP adresi) üzerinden sunucuyla iletişim kurmaktadır.

2. **Geliştirilen Çözümler ve Algoritmalar:**
   - **Çoklu İşlem (Multi-threading):** Sunucunun aynı anda yüzlerce bağlantıyı tıkanmadan kabul edebilmesi için `server.accept()` metodu ile içeri alınan her oyuncu `threading.Thread` içerisine paslanmıştır.
   - **UI Donmasının (Freeze) Engellenmesi:** İstemci tarafında `socket.recv()` ağ dinleme komutu "bloklayıcı" bir komuttur. Bu komutun oyunu dondurmasını engellemek için, dinleme işlemi `PyQt5.QtCore.QThread` sınıfından miras alınan bir iş parçacığına aktarılmıştır. Arayüz güncellemeleri Thread içerisinden `pyqtSignal` ile ana arayüze güvenle iletilmektedir.
   - **Oda ve Eşleşme (Room Matchmaking):** İstemcilerin birbirine karışmasını ("Ghost Connection") engellemek için 6 haneli kod üreten bir sistem yazılmış ve `threading.Lock()` mekanizması kullanılarak eşzamanlılıktan doğabilecek *Race Condition* problemleri tamamen engellenmiştir.

3. **Çalışmayan Kısımlar ve Eksiklikler:**
   - Projenin temel işlevleri (bağlantı, eşleşme, yerleştirme, atış validasyonu ve kazanma kontrolü) **tamamen ve sorunsuz çalışmaktadır.**
   - **Bilinen Eksiklik:** Oyuncuların oyun esnasında internet bağlantılarının kopması veya uygulamayı aniden kapatmaları durumunda, sunucu durumu başarıyla tespit edip diğer oyuncuya "Rakip oyundan ayrıldı" bilgisini ileterek tüneli güvenle kapatmaktadır. Ancak kopan oyuncunun tekrar bağlanıp odaya ve eski tahtasına geri dönme (Session Persistence / Reconnection) özelliği bulunmamaktadır.
   - Sunucu AWS'de kapatılıp açıldığında aktif odalar sıfırlanmaktadır (Kalıcı bir veritabanı entegre edilmemiştir).

4. **Bağımlılıklar (Platform Bağımsızlığı):**
   - Projede sadece yerleşik Python modülleri (`socket`, `json`, `threading`) ve PyQt5 kullanılmıştır. Dosya/klasör mimarisi izole edildiği için Windows, macOS ve Linux işletim sistemlerinde hiçbir yol (path) hatası olmadan "Tak-Çalıştır" mantığıyla çalışmaktadır.
