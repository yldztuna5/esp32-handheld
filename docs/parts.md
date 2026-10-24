# Parça listesi

Üç grup var:
1. **Prototip siparişi:** Şimdi alınacaklar. Çoğu final parça; prototipte kullanılır, sonra aynen PCB'ye takılır veya bağlanır.
2. **PCB'ye dahil edilecekler:** JLCPCB (veya yerli dizgi firması) tarafından karta lehimlenir; şimdi alınmaz.
3. **PCB aşamasında ayrıca alınacaklar.**

Tüm alışveriş Türkiye'den (2026 itibarıyla yurt dışı gönderilerde gümrük muafiyeti yok). Fiyatlar KDV dahil, Ekim 2026'da sitelerden alındı; değişebilir.

---

## 1. Prototip siparişi

### Robotistan (963,42 TL)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| [Waveshare Pico-ResTouch-LCD-2.8](https://www.robotistan.com/28inch-touch-display-module-for-raspberry-pi-pico-262k-colors-320240-spi) | 1 | 963,42 TL | Evet | 2.8" IPS, 320x240, ST7789, SPI. Kartta microSD yuvası, rezistif dokunmatik (XPT2046) ve arka ışık transistörü var. [Wiki](https://www.waveshare.com/wiki/Pico-ResTouch-LCD-2.8), [şema](https://files.waveshare.com/upload/d/dc/Pico-ResTouch-LCD-2.8_Sch.pdf). Sipariş anında stokta 1 adet vardı. |

### Direnc.net (~870 TL + kargo; yedek hoparlörle ~1.080 TL)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| [ESP32 S3 N16R8 WiFi Bluetooth Board](https://www.direnc.net/esp32-s3-n16r8-wifi-bluetooth-board) | 1 | 610,23 TL | Geliştirme kartı | Üzerinde ESP32-S3-WROOM-1-N16R8; PCB'deki modülle aynı (aynı kod, aynı pinler). |
| [Mini Oval Hoparlör 8Ω 1W](https://www.direnc.net/mini-oval-hoparlor-8ohm-1w) | 1 (yedek isteğe bağlı) | 209,66 TL/adet | Evet | 30x20x5 mm, Molex 1.25 mm konnektörlü. |
| [6x6 5mm Tact Buton (4 bacak)](https://www.direnc.net/6x6-4mm-tach-buton--4-bacak) | 10 | 1,51 TL/adet | Evet | |
| [6x6 7mm Tact Buton (4 bacak)](https://www.direnc.net/6x6-9mm-tach-buton--4-bacak) | 10 | 3,60 TL/adet | Evet | Yükseklik kasa tasarımında seçilecek. |

### Trendyol
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| MAX98357 I2S amfi modülü, ör. [ROBİZ](https://www.trendyol.com/robiz/max98357-i2s-5v-3w-ses-yukseltici-amfi-class-d-dijital-ses-muzik-kuvvetlendirici-amfilikator-dac-p-406603487) | 1 | ~270-310 TL | Evet | ESP32-S3'te DAC yok, I2S amfi şart. Modül finalde kısa pinlerle PCB'ye lehimlenir. |
| [PS4 Analog Motoru x2 (POPKONSOL)](https://www.trendyol.com/popkonsol/ps4-analog-motoru-tum-playstation-4-kollarina-uyumlu-turuncu-seri-kaliteli-ps4-yedek-parca-x2-adet-p-127921128) | 1 paket | Kontrol edilmedi | Evet | 3D analog, bacakları doğrudan PCB'ye lehimlenir. PSP joystick Türkiye'de bulunamadı. |
| [PS4 Analog Topuz (POPKONSOL)](https://www.trendyol.com/popkonsol/2-adet-ps4-analog-topuz-orjinal-yedek-parca-ps-v1-v2-tum-ps4-kollara-uyumlu-ps4-analog-thumb-stick-p-194605501) | 1 paket | Kontrol edilmedi | Evet | |

### Elde olanlar
- Breadboard, jumper kablolar
- **Veri aktarabilen** USB-C kablo (sadece şarj kablosu ile kart programlanamaz)

---

## 2. PCB'ye dahil edilecekler (şimdi alınmaz)

Parça numaraları KiCad aşamasında JLCPCB/LCSC stok durumuna göre kesinleşecek.

### İşlemci
| Parça | Not |
|---|---|
| ESP32-S3-WROOM-1-N16R8 | Ana modül |
| 2x küçük SMD buton | BOOT ve RESET (yazılım bozulursa kurtarma için şart) |

### USB-C ve giriş koruması
| Parça | Not |
|---|---|
| USB-C 16 pin dişi konnektör | Şarj + programlama |
| 2x 5.1kΩ direnç | CC1/CC2; C-to-C şarj için şart |
| USBLC6-2SC6 | D+/D- ESD koruması |
| TVS diyot (5V, ör. SMAJ5.0A) | VBUS ani gerilim koruması |
| PTC sigorta (~1.5A) | Aşırı akım koruması |

### Şarj ve batarya
| Parça | Not |
|---|---|
| BQ24074 | Şarj çipi: NTC, zamanlayıcı, power path. 1A şarj. |
| DW01A + FS8205A | Hücre koruması (aşırı şarj/deşarj, kısa devre) |
| 10k NTC termistör (kablolu, B=3435) | Hücreye bantlanır, BQ24074'e bağlanır |
| JST-PH konnektör (batarya + NTC) | |
| 2x LED | Şarj oluyor / güç var |
| MAX17048 | Pil yüzdesi (I2C) |

### Güç
| Parça | Not |
|---|---|
| TPS63020 + 1.5µH bobin + kondansatörler | 3.3V buck-boost. Ekran kartının VSYS pinini de bu hat besler. |
| Yan sürgülü güç anahtarı (ör. MSK-12C02) | Gerçek açma/kapama |

### Ekran, ses, kontroller
| Parça | Not |
|---|---|
| 2x 1x20 erkek pin header (Pico düzeni) | Ekran kartı üstüne takılır; sadece gereken pinler bağlanır. |
| MAX98357 modülü için pin delikleri | Prototipteki modül lehimlenir; SD pini ESP32'ye bağlı |
| Molex 1.25 mm (PicoBlade) 2 pin konnektör | Hoparlör |
| PS4 analog joystick footprint | Doğrudan lehim |
| 4x 6x6 tact switch | A, B, Start, Select |

Ekran kartında zaten olduğu için PCB'de **microSD yuvası** ve **arka ışık MOSFET'i** gerekmiyor.

### Diğer
- Dekuplaj kondansatörleri, pull-up dirençleri
- Güç bölümünde test noktaları ve kesilebilir köprüler (ilk test bataryasız yapılacak)

---

## 3. PCB aşamasında ayrıca alınacak
| Parça | Not |
|---|---|
| 18650 hücre, **tırnaklı (puntalı)**, 3000-3500 mAh | Samsung 35E / LG MJ1 / Panasonic NCR18650B / Samsung 30Q. Güvenilir pil satıcısından, orijinal. Güç devresi test edilene kadar bağlanmayacak. |
