# Donanım kararları

| Bölüm | Karar | Not |
|---|---|---|
| MCU | ESP32-S3-WROOM-1 **N16R8** | 16MB flash, 8MB PSRAM, native USB. Prototipte aynı modülü taşıyan DevKitC-1 N16R8. |
| Ekran | Waveshare Pico-ResTouch-LCD-2.8: 2.8" IPS, 320x240, ST7789, SPI | Kartta 3.3V LDO (VSYS girişi), arka ışık transistörü, microSD ve rezistif dokunmatik var. Pico düzeninde header ile PCB'ye takılır (~11 mm yığın); batarya bu yüzden ekranın arkasında değil, alttaki çıkıntıda. |
| Batarya | 18650, 3000-3500 mAh, tırnaklı (puntalı) | Samsung 35E / LG MJ1 / Panasonic NCR18650B / Samsung 30Q. Orijinal hücre. |
| Şarj | TI BQ24074 | NTC, güvenlik zamanlayıcısı, power path. Şarj akımı 1A. |
| Batarya koruması | DW01A + FS8205A (PCB üzerinde) | Aşırı şarj, aşırı deşarj, kısa devre. |
| USB girişi | USB-C, CC'lerde 2x 5.1k, PTC sigorta, TVS | 5.1k dirençler olmadan C-to-C şarj çalışmaz. |
| Regülatör | TPS63020 buck-boost, 3.3V | Bataryanın tamamını kullanır, ses tepe akımlarını karşılar. |
| Pil göstergesi | MAX17048 (I2C) | Doğru yüzde, düşük pilde kayıt + kapanma. |
| Ses | PAM8403 modülü (analog, class-D) + 8Ω 1.5W hoparlör (20x30 mm) | ESP32-S3'te DAC yok: tek pinden PDM çıkışı, RC filtre ile analoğa çevrilir. Modül finalde pin deliklerinden PCB'ye lehimlenir. Beslemesi P-MOSFET ile kesilir (sessizken akım sıfır). Hoparlör L+ ve L- arasına bağlanır, GND'ye asla. MAX98357'ye göre biraz cızırtılı ama yarı fiyatından ucuz. |
| Depolama | microSD (SDMMC, 1-bit) | Ekran kartının üzerindeki yuva. LCD ile aynı SPI hattında değil; kendi SDIO pinleri var (bkz. [pin planı](pinout.md)). |
| Kontroller | PS2 tipi analog joystick (XY joystick modülünden) + A, B, Start, Select (6x6 tact) | Joystick ADC1 pinlerine (GPIO1-2). Joystick basma = menü. PCB'de çıplak joystick footprint'i var: yedek modülden sökülüp lehimlenir. Ucuz potansiyometreler için yazılımda merkez kalibrasyonu ve ölü bölge. |
| Güç anahtarı | Gerçek açma/kapama anahtarı | Kapalıyken akım çekmez. |
| Kasa | PETG veya ASA | PLA değil (55-60°C'de yumuşar). Altta batarya çıkıntısı, gövde ~20 mm. |
| Ekran koruması | 1-1,5 mm şeffaf akrilik lens + koruyucu film | Lens kasaya oturur, ekrana değmez (0,3-0,5 mm boşluk). Ekran kartı köpük conta üstünde, 4 köşeden M2 vidayla kasaya bağlı. Ön çerçeve ekrandan yüksek. |
| Buton hissi | Prototipte tact switch; finalde kapak + silikon katman | Gerçek konsol tipi silikon zar Türkiye'de bulunamadı; PCB'ye ileride karbon pad seçeneği eklenebilir. |

## Yazılım
- PlatformIO + Arduino framework
- LovyanGFX (oyunlar), LVGL (menü/arayüz)
- Launcher + ortak API (ekran, tuş, ses, kayıt, pil) + uygulamalar (`init / update / draw / exit`)
- İleride: SD karttan Lua scriptleri

## Taşınabilirlik ilkesi
Prototipte kullanılan her parça finaldeki parçayla aynı olacak (aynı ekran paneli, aynı modül, aynı joystick). Böylece breadboard'da doğrulanan pinler ve kod PCB'ye birebir geçer. Küçük SMD çipler JLCPCB dizgi hizmetiyle lehimlenecek.
