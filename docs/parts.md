# Parça listesi

Üç grup var:
1. **Prototip siparişi:** Şimdi alınacaklar. Çoğu final parça; prototipte kullanılır, sonra aynen PCB'ye takılır veya bağlanır.
2. **PCB'ye dahil edilecekler:** JLCPCB (veya yerli dizgi firması) tarafından karta lehimlenir; şimdi alınmaz.
3. **PCB aşamasında ayrıca alınacaklar.**

Tüm alışveriş Türkiye'den (2026 itibarıyla yurt dışı gönderilerde gümrük muafiyeti yok). Fiyatlar KDV dahil, Ekim-Kasım 2026'da sitelerden alındı; değişebilir.

---

## 1. Prototip siparişi

Toplam ≈ 1.781 TL (kargolar dahil). Sepetler 11 Kasım 2026'da güncellendi; henüz sipariş verilmedi.

### Robotistan (725,56 TL, 149 TL kargo dahil)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| [2.8" 240x320 SPI TFT LCD Ekran](https://www.robotistan.com/28inc-240x320-spi-tft-lcd-ekran) | 1 | 554,55 TL | Evet | TN, 320x240, ILI9341, SPI, **dokunmatiksiz**, microSD yuvalı. Dokunmatikli sürümü 582,68 TL; dokunmatik katmanı olmadığı için görüntü biraz daha net. Waveshare 2.8" IPS (963,42 TL) yerine, bütçe nedeniyle. Kart ölçüsü ve pin sırası ilanda yazmıyor; gelince doğrulanacak. |
| [2x3W Mini Amfi Devresi, PAM8403](https://www.robotistan.com/23w-mini-amfi-devresi-pam8403) | 1 | 22,01 TL | Sadece prototip | Analog class-D. ESP32'den PDM + RC filtre + 10k/1k bölücü ile sürülür. PCB'de yerini I2S amfi çipi alır. Trendyol'daki aynı modül 82,40 TL idi. |

### Direnc.net (897,41 TL, 144 TL kargo dahil)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| [ESP32 S3 N16R8 WiFi Bluetooth Board](https://www.direnc.net/esp32-s3-n16r8-wifi-bluetooth-board) | 1 | 635,17 TL | Geliştirme kartı | ESP32-S3-WROOM-1-N16R8, çift USB Type-C. PCB'deki modülle aynı (aynı kod, aynı pinler). |
| [6x6 5mm Tact Buton (4 bacak)](https://www.direnc.net/6x6-4mm-tach-buton--4-bacak) | 10 | 14,94 TL | Evet | Yön tuşu (4) + A, B, Start, Select (4) |
| [6x6 7mm Tact Buton (4 bacak)](https://www.direnc.net/6x6-9mm-tach-buton--4-bacak) | 10 | 35,63 TL | Evet | Yükseklik kasa tasarımında seçilecek. |
| [Arduino XY Joystick Modül](https://www.direnc.net/arduino-xy-joystick-modul-1) | 1 | 33,27 TL | İsteğe bağlı | PS2 tipi joystick + topuz. Ana kontrol yön tuşu; joystick denemek için. |
| [1K 1/4W Direnç](https://www.direnc.net/1k-14w-direnc) | 50 | 11,19 TL | Prototip | PDM ses filtresi ve ses bölücü |
| [10K 1/4W Direnç](https://www.direnc.net/10k-14w-direnc) | 50 | 9,07 TL | Prototip | Ses bölücü (10k/1k) ve pull-up'lar |
| [10nF 63V Seramik Kondansatör](https://www.direnc.net/10nf-63v-seramik) | 10 | 4,60 TL | Prototip | PDM ses filtresi |
| [1uF 50V Kondansatör](https://www.direnc.net/1uf-50v-kondansator) | 5 | 4,31 TL | Prototip | Amfi girişi kuplaj |
| [1x11 Erkek Pin Header](https://www.direnc.net/1160mm-11-pin-1x11-254mm-erkek-pin-header) | 2 | 5,23 TL | Prototip | PAM8403 modülünü breadboard'a takmak için |

### Trendyol, ROBİZ (157,78 TL, 59,99 TL kargo dahil)
| Parça | Adet | Fiyat | Final mi? | Not |
|---|---|---|---|---|
| ROBİZ Hoparlör 1.5W 8Ω 20x30 mm, kablolu | 1 | 97,79 TL | Evet | Konnektör tipi parça gelince ölçülecek; PCB'ye uygun soket konacak. |

### Elde olanlar
- Breadboard, jumper kablolar
- Havya ve lehim
- Multimetre
- **Veri aktarabilen** USB-C kablo (sadece şarj kablosu ile kart programlanamaz)

---

## 2. PCB'ye dahil edilecekler (şimdi alınmaz)

Parça numaraları KiCad aşamasında JLCPCB/LCSC stok durumuna göre kesinleşecek. Kaba maliyet tahmini: 5 kart dizgili ~75 dolar + kargo; vergilerle ~160-180 dolar (kesin fiyat dosyalar yüklenince).

### İşlemci
| Parça | Not |
|---|---|
| ESP32-S3-WROOM-1-N16R8 (LCSC C2913202) | Ana modül. Anten çevresinde ~15 mm bakırsız alan. |
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
| BQ24074 (LCSC C54313) | Şarj çipi: NTC, zamanlayıcı, power path. 500 mA şarj (RISET 1.78k), USB500 giriş sınırı (EN1 HIGH, EN2 LOW), RTMR 71.5k. |
| DW01A + FS8205A | Hücre koruması (aşırı şarj/deşarj, kısa devre) |
| 10k NTC termistör (kablolu, **B≈3950**) | Hücreye bantlanır, BQ24074'e bağlanır. B=3435 değil: sıcak eşiği 50°C'ye çıkarıyor. |
| JST-PH konnektör (batarya + NTC) | |
| 2x LED | Şarj oluyor / güç var |
| MAX17048 (LCSC C2682616) | Pil yüzdesi (I2C) |
| Batarya sigortası (~2A) + P-MOSFET | Kısa devre ve ters takma koruması |

### Güç
| Parça | Not |
|---|---|
| TPS63021 + 1.5µH bobin + kondansatörler | Sabit 3.3V buck-boost. |
| Yan sürgülü güç anahtarı (ör. MSK-12C02) | Regülatörün EN pinini kontrol eder; akım taşımaz. |

### Ekran, ses, kontroller
| Parça | Not |
|---|---|
| 1x14 + 1x4 dişi/erkek pin header | Ekran modülünün başlıkları (LCD + SD). |
| I2S amfi çipi: MAX98357AETE+T (LCSC C910544) veya NS4168 (C910588) | Batarya hattından beslenir; saat kesilince kendini kapatır. |
| LCD_BL için 100k pull-down | Açılışta ekran karanlık kalır. Gerekirse arka ışık MOSFET'i (breadboard ölçümüne göre). |
| Joystick uçlarına 2x 100nF | Sadece joystick takılırsa |
| 2 pin hoparlör soketi | Tipi hoparlör kablosuna göre seçilecek |
| PS2 tipi joystick footprint | İsteğe bağlı; modülden sökülen joystick lehimlenir |
| 8x 6x6 tact switch | Yön tuşu (4) + A, B, Start, Select |
| SD_CS için 10k pull-up | |

Ekran modülünde zaten olduğu için PCB'de **microSD yuvası** gerekmiyor. Pin bağlantıları için bkz. [pin planı](pinout.md).

### Diğer
- Dekuplaj kondansatörleri, pull-up dirençleri
- Güç bölümünde test noktaları ve kesilebilir köprüler (ilk test bataryasız yapılacak)

---

## 3. PCB aşamasında ayrıca alınacak
| Parça | Not |
|---|---|
| 18650 hücre, **tırnaklı (puntalı)**, 3000-3500 mAh | Samsung 35E / LG MJ1 / Panasonic NCR18650B / Samsung 30Q. Güvenilir pil satıcısından, orijinal. Güç devresi test edilene kadar bağlanmayacak. |
