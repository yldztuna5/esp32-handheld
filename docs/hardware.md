# Donanım kararları

| Bölüm | Karar | Not |
|---|---|---|
| MCU | ESP32-S3-WROOM-1 **N16R8** | 16MB flash, 8MB PSRAM, native USB. Prototipte aynı modülü taşıyan DevKitC-1 N16R8. |
| Ekran | 2.8" SPI TFT modülü (MSP2807 tipi): TN, 320x240, ILI9341 | Bütçe nedeniyle Waveshare IPS (963 TL) yerine. Renkler daha soluk, görüş açısı dar. Kart 50 x 86 mm; üstünde microSD yuvası ve rezistif dokunmatik (kullanılmıyor) var. 14'lü başlıkla PCB'ye takılır. PCB, ileride IPS panele geçilebilecek şekilde çizilir. |
| Batarya | 18650, 3000-3500 mAh, tırnaklı (puntalı) | Samsung 35E / LG MJ1 / Panasonic NCR18650B / Samsung 30Q. Orijinal hücre. |
| Şarj | TI BQ24074 | NTC, güvenlik zamanlayıcısı, power path. Şarj akımı 500 mA, giriş sınırı USB500 (bkz. [güç ve güvenlik](power-safety.md)). |
| Batarya koruması | DW01A + FS8205A (PCB üzerinde) + sigorta + ters takma koruması | Aşırı şarj, aşırı deşarj, kısa devre, ters bağlantı. |
| USB girişi | USB-C, CC'lerde 2x 5.1k, PTC sigorta, TVS | 5.1k dirençler olmadan C-to-C şarj çalışmaz. |
| Regülatör | TPS63020 buck-boost, 3.3V | Bataryanın tamamını kullanır, ses tepe akımlarını karşılar. Sabit çıkışlı TPS63021 JLCPCB stokunda olmadığı için ayarlanabilir sürüm; çıkış iki dirençle 3.3V'a ayarlı. |
| Pil göstergesi | MAX17048 (I2C) | Doğru yüzde, düşük pilde kayıt + kapanma. |
| Ses | PCB'de I2S amfi çipi (MAX98357A veya NS4168) + 8Ω 1.5W hoparlör (20x30 mm) | Çip dizgide 0,4-1,4 dolar; modülü pahalıydı, çipi değil. Batarya hattından beslenir, saat kesilince kendini kapatır. Breadboard'da PAM8403 modülü kullanılır: PDM çıkışı + RC filtre + 10k/1k bölücü. Hoparlör çıkışları GND'ye asla bağlanmaz. |
| Depolama | microSD (SPI) | Ekran modülünün üzerindeki yuva. LCD ile aynı SPI hattında, ayrı CS pini (bkz. [pin planı](pinout.md)). |
| Kontroller | Yön tuşu (4x 6x6 tact) + A, B, Start, Select | Menü ve 2D oyunlar için yön tuşu ana kontrol. PS2 tipi analog joystick isteğe bağlı: PCB'de footprint bırakılır (ADC1, GPIO1-2), kasadan ~10 mm taşar. |
| Güç anahtarı | Sürgülü anahtar, regülatörün EN pininde | Anahtar akım taşımaz (50 mA'lik). Kapalıyken kaçak ~35 µA. |
| Kasa | PETG veya ASA, yaklaşık 94 x 130 x 20 mm | PLA değil (55-60°C'de yumuşar). Dikey düzen: üstte ekran, altında butonlar, en altta pil bölmesi. Kart 90 x 100 mm ve kasanın üst 100 mm'sinde durur; alttaki ~28 mm'lik bölmeye 18650 yatay girer (pil 18,5 mm çap + boşluk + duvarlar ≈ 24 mm). Yön tuşu merkezi alt kenardan ~48 mm (Gameboy'a yakın). Hoparlör (20x30 mm) pilin yanına. Ölçüler tahmini; kasa çizilince kesinleşir. |
| Ekran koruması | 1-1,5 mm şeffaf akrilik lens + koruyucu film | Lens kasaya oturur, ekrana değmez (0,3-0,5 mm boşluk). Ekran kartı köpük conta üstünde, 4 köşeden M2 vidayla kasaya bağlı. Ön çerçeve ekrandan yüksek. |
| Buton hissi | Prototipte tact switch; finalde kapak + silikon katman | Gerçek konsol tipi silikon zar Türkiye'de bulunamadı; PCB'ye ileride karbon pad seçeneği eklenebilir. |

## Yazılım
- PlatformIO + Arduino framework
- LovyanGFX (oyunlar), LVGL (menü/arayüz)
- Launcher + ortak API (ekran, tuş, ses, kayıt, pil) + uygulamalar (`init / update / draw / exit`)
- İleride: SD karttan Lua scriptleri

## Taşınabilirlik ilkesi
Prototipte kullanılan her parça finaldeki parçayla aynı olacak (aynı ekran modülü, aynı ESP32 modülü, aynı butonlar). Böylece breadboard'da doğrulanan pinler ve kod PCB'ye birebir geçer. Tek istisna ses: breadboard'da PAM8403 modülü, PCB'de I2S amfi çipi (firmware'de tek ayar değişir). Küçük SMD çipler JLCPCB dizgi hizmetiyle lehimlenecek.
