# Parça listesi

Üç grup var:
1. **Önden alınacak final parçalar:** Prototipte kullanılır, sonra aynen PCB'ye takılır veya bağlanır.
2. **Sadece geliştirme/test için:** Ucuz araçlar; PCB'ye girmez.
3. **PCB'ye dahil edilecekler:** JLCPCB (veya yerli dizgi firması) tarafından karta lehimlenir; şimdi alınmaz.

Tüm alışveriş Türkiye'den yapılacak (2026 itibarıyla yurt dışı gönderilerde muafiyet yok).

---

## 1. Önden alınacak final parçalar

| Parça | Adet | Ne aranmalı | PCB'ye nasıl geçer | Dikkat |
|---|---|---|---|---|
| 2.8" IPS ekran modülü | 1 (+1 yedek) | "2.8 IPS ST7789 SPI 240x320" | 2.54 mm dişi header ile PCB'ye takılır | İlanda **IPS** ve **ST7789** yazmalı. Dokunmatiksiz olanı al. Pin sırasının fotoğrafını sakla. |
| PSP analog joystick | 2 | "PSP 3000 analog" veya "PSP 1000 analog" yedek parça | Kendi FPC ucu PCB'deki FPC konnektörüne takılır | İkisi de aynı modelden olsun. Model bilgisini not et. |
| Tact switch 6x6 mm, 4 bacaklı (THT) | 10-20 | "6x6 tact switch" | Aynen PCB'ye lehimlenir | Farklı yüksekliklerden (5, 7, 9 mm) birkaç tane al, kasa tasarımında seçeriz. |
| Kutulu mikro hoparlör 8Ω (veya 4Ω), ~1W | 2 | "mikro hoparlör kutulu 8 ohm 1W" | Kablosu JST-PH ile PCB'ye bağlanır | Kablolu olsun. İnce (~5 mm) olanı tercih et. |
| JST-PH 2.0 mm 2 pin kablolu soket seti | 1 set | "JST PH 2.0 2 pin kablolu" | Hoparlör ve batarya bağlantısı | Erkek/dişi eşleşen set al. |

## 2. Sadece geliştirme/test için

| Parça | Adet | Neden |
|---|---|---|
| ESP32-S3-DevKitC-1 **N16R8** | 1 | Üzerindeki modül PCB'deki modülle aynı (aynı kod, aynı pinler). Sonra da geliştirme kartı olarak işe yarar. **N16R8 yazmayanı alma.** |
| MAX98357A I2S amfi modülü | 1 | Ses kodunu yazmak için. Finalde çipin kendisi PCB'de olacak. |
| microSD kart modülü (SPI, 3.3V) | 1 | SD kart kodunu yazmak için. Finalde yuva PCB'de olacak. |
| Breadboard (830 delik) | 1-2 | |
| Jumper kablo (erkek-erkek, erkek-dişi) | 1 set | |
| USB-C veri kablosu | 1 | Sadece şarj kablosu değil, veri kablosu olmalı. |
| İnce tel (30 AWG) | 1 makara | Prototipte joystick FPC'sine lehimlemek için. |

## 3. PCB'ye dahil edilecekler (şimdi alınmaz)

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
| TPS63020 + 1.5µH bobin + kondansatörler | 3.3V buck-boost |
| Yan sürgülü güç anahtarı (ör. MSK-12C02) | Gerçek açma/kapama |

### Ekran, ses, depolama, kontroller
| Parça | Not |
|---|---|
| 2.54 mm dişi header | Ekran modülü için |
| N-kanal MOSFET (ör. AO3400) | Ekran arka ışığı PWM parlaklık kontrolü |
| MAX98357A çipi | I2S amfi; SD pini ESP32'ye bağlı |
| JST-PH konnektör | Hoparlör |
| microSD yuvası (push-push) | |
| PSP joystick FPC konnektörü | Joystick modeline göre seçilecek |
| 4x 6x6 tact switch | A, B, Start, Select (önden alınanlar) |

### Diğer
- Dekuplaj kondansatörleri, pull-up dirençleri
- Güç bölümünde test noktaları ve kesilebilir köprüler (ilk test bataryasız yapılacak)

## PCB aşamasında ayrıca alınacak
| Parça | Not |
|---|---|
| 18650 hücre, **tırnaklı (puntalı)**, 3000-3500 mAh | Samsung 35E / LG MJ1 / Panasonic NCR18650B / Samsung 30Q. Güvenilir pil satıcısından, orijinal. Güç devresi test edilene kadar bağlanmayacak. |
