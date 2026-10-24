# Parça listesi

Üç grup var:
1. **Prototip siparişi:** Şimdi alınacaklar. Çoğu final parça; prototipte kullanılır, sonra aynen PCB'ye takılır veya bağlanır.
2. **PCB'ye dahil edilecekler:** JLCPCB (veya yerli dizgi firması) tarafından karta lehimlenir; şimdi alınmaz.
3. **PCB aşamasında ayrıca alınacaklar.**

Tüm alışveriş Türkiye'den (2026 itibarıyla yurt dışı gönderilerde gümrük muafiyeti yok). Fiyatlar KDV dahil, Ekim 2026'da sitelerden alındı; değişebilir.

---

## 1. Prototip siparişi

Toplam ≈ 2.241 TL (kargolar dahil).

### Robotistan (1.112,42 TL, 149 TL kargo dahil)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| [Waveshare Pico-ResTouch-LCD-2.8](https://www.robotistan.com/28inch-touch-display-module-for-raspberry-pi-pico-262k-colors-320240-spi) | 1 | 963,42 TL | Evet | 2.8" IPS, 320x240, ST7789, SPI. Kartta microSD yuvası (SDIO pinleri), rezistif dokunmatik (XPT2046, kullanılmıyor) ve arka ışık transistörü var. [Wiki](https://www.waveshare.com/wiki/Pico-ResTouch-LCD-2.8), [şema](https://files.waveshare.com/upload/d/dc/Pico-ResTouch-LCD-2.8_Sch.pdf). Türkiye'de (Amazon.com.tr dahil) dokunmatiksiz 2.8" IPS bulunamadı; TN alternatifler (ILI9341) renk ve görüş açısı yüzünden elendi. |

### Direnc.net (888,81 TL, 144 TL kargo dahil)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| [ESP32 S3 N16R8 WiFi Bluetooth Board](https://www.direnc.net/esp32-s3-n16r8-wifi-bluetooth-board) | 1 | 610,23 TL | Geliştirme kartı | ESP32-S3-WROOM-1-N16R8, çift USB Type-C. PCB'deki modülle aynı (aynı kod, aynı pinler). |
| [6x6 5mm Tact Buton (4 bacak)](https://www.direnc.net/6x6-4mm-tach-buton--4-bacak) | 10 | 14,36 TL | Evet | |
| [6x6 7mm Tact Buton (4 bacak)](https://www.direnc.net/6x6-9mm-tach-buton--4-bacak) | 10 | 34,23 TL | Evet | Yükseklik kasa tasarımında seçilecek. |
| [Arduino XY Joystick Modül](https://www.direnc.net/arduino-xy-joystick-modul-1) | 2 | 63,93 TL | Joystick'i evet | PS2 tipi joystick + topuz. PCB'ye modülden sökülüp lehimlenir; ikincisi yedek. PS4 joystick + topuz (405 TL) yerine. |
| [1K 1/4W Direnç](https://www.direnc.net/1k-14w-direnc) | paket | 8,72 TL | Prototip | PDM ses filtresi |
| [10nF 63V Seramik Kondansatör](https://www.direnc.net/10nf-63v-seramik) | 10 | 4,07 TL | Prototip | PDM ses filtresi |
| [1uF 50V Kondansatör](https://www.direnc.net/1uf-50v-kondansator) | 5 | 4,07 TL | Prototip | Amfi girişi kuplaj |
| [1x11 Erkek Pin Header](https://www.direnc.net/1160mm-11-pin-1x11-254mm-erkek-pin-header) | 2 | 5,21 TL | Prototip | PAM8403 modülünü breadboard'a takmak için |

### Trendyol, ROBİZ (240,18 TL, 59,99 TL kargo dahil)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| [ROBİZ PAM8403 Mini 2x3W Amfi](https://www.trendyol.com/robiz/pam8403-mini-2x3w-stereo-ses-amfilikatoru-d-class-amfi-yukseltici-p-330624448) | 1 | 82,40 TL | Evet | Analog class-D. MAX98357 (~300 TL) yerine; ESP32'den PDM + RC filtre ile sürülür. Finalde PCB'ye lehimlenir. |
| ROBİZ Hoparlör 1.5W 8Ω 20x30 mm, kablolu | 1 | 97,79 TL | Evet | Konnektör tipi parça gelince ölçülecek; PCB'ye uygun soket konacak. |

### Elde olanlar
- Breadboard, jumper kablolar
- Havya ve lehim
- Multimetre
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
| PAM8403 modülü için pin delikleri | Prototipteki modül lehimlenir |
| P-MOSFET (ör. AO3401) + gate direnci | Amfi beslemesini GPIO18 ile açar/kapar |
| PDM filtre: 2x 1k + 2x 10nF, 1µF kuplaj | GPIO17 → PAM8403 L girişi |
| 2 pin hoparlör soketi | Tipi hoparlör kablosuna göre seçilecek |
| PS2 tipi joystick footprint | Modülden sökülen joystick doğrudan lehimlenir |
| 4x 6x6 tact switch | A, B, Start, Select |
| SD hatları için 10k pull-up'lar | CMD, D0, D1, D2, D3 |
| TP_CS için 10k pull-up | Dokunmatik çipi kapalı tutar |

Ekran kartında zaten olduğu için PCB'de **microSD yuvası** ve **arka ışık MOSFET'i** gerekmiyor. Pin bağlantıları için bkz. [pin planı](pinout.md).

### Diğer
- Dekuplaj kondansatörleri, pull-up dirençleri
- Güç bölümünde test noktaları ve kesilebilir köprüler (ilk test bataryasız yapılacak)

---

## 3. PCB aşamasında ayrıca alınacak
| Parça | Not |
|---|---|
| 18650 hücre, **tırnaklı (puntalı)**, 3000-3500 mAh | Samsung 35E / LG MJ1 / Panasonic NCR18650B / Samsung 30Q. Güvenilir pil satıcısından, orijinal. Güç devresi test edilene kadar bağlanmayacak. |
