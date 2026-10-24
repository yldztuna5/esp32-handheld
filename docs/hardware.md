# Donanım kararları

| Bölüm | Karar | Not |
|---|---|---|
| MCU | ESP32-S3-WROOM-1 **N16R8** | 16MB flash, 8MB PSRAM, native USB. Prototipte aynı modülü taşıyan DevKitC-1 N16R8. |
| Ekran | 2.8" IPS, 320x240, ST7789V, SPI | Çıplak FPC panel; prototipte FPC-to-DIP adaptörle. Datasheet'i olan panel alınacak. |
| Batarya | 18650, 3000-3500 mAh, tırnaklı (puntalı) | Samsung 35E / LG MJ1 / Panasonic NCR18650B / Samsung 30Q. Orijinal hücre. |
| Şarj | TI BQ24074 | NTC, güvenlik zamanlayıcısı, power path. Şarj akımı 1A. |
| Batarya koruması | DW01A + FS8205A (PCB üzerinde) | Aşırı şarj, aşırı deşarj, kısa devre. |
| USB girişi | USB-C, CC'lerde 2x 5.1k, PTC sigorta, TVS | 5.1k dirençler olmadan C-to-C şarj çalışmaz. |
| Regülatör | TPS63020 buck-boost, 3.3V | Bataryanın tamamını kullanır, ses tepe akımlarını karşılar. |
| Pil göstergesi | MAX17048 (I2C) | Doğru yüzde, düşük pilde kayıt + kapanma. |
| Ses | MAX98357A (I2S) + 8Ω/4Ω ~1W kutulu mikro hoparlör | SD pini ESP32'ye bağlı, sessizken amfi kapalı. |
| Depolama | microSD (SPI) | |
| Kontroller | PSP tipi analog joystick + A, B, Start, Select (6x6 tact) | Joystick ADC1 pinlerine (GPIO1-10). Joystick basma = menü. |
| Güç anahtarı | Gerçek açma/kapama anahtarı | Kapalıyken akım çekmez. |
| Kasa | PETG veya ASA | PLA değil (55-60°C'de yumuşar). Altta batarya çıkıntısı, gövde ~20 mm. |

## Yazılım
- PlatformIO + Arduino framework
- LovyanGFX (oyunlar), LVGL (menü/arayüz)
- Launcher + ortak API (ekran, tuş, ses, kayıt, pil) + uygulamalar (`init / update / draw / exit`)
- İleride: SD karttan Lua scriptleri

## Taşınabilirlik ilkesi
Prototipte kullanılan her parça finaldeki parçayla aynı olacak (aynı ekran paneli, aynı modül, aynı joystick). Böylece breadboard'da doğrulanan pinler ve kod PCB'ye birebir geçer. Küçük SMD çipler JLCPCB dizgi hizmetiyle lehimlenecek.
