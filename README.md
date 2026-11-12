# ESP32 Handheld

3D baskı kasalı, ESP32-S3 tabanlı, kendi arayüzü ve mini uygulamaları olan bir el konsolu.

## Hedefler
- **Güvenli batarya:** Şarjda unutulunca ısınmayan, sıcakta ve soğukta şarjı kendiliğinden durduran bir güç devresi.
- **Uzun pil ömrü:** 18650 hücre ile ~10-12 saat kullanım.
- **Ekran:** 2.8", 320x240 (bütçe nedeniyle TN; PCB ileride IPS'e geçişe uygun).
- **Kompakt yapı:** Özel PCB ile kasaya düzgünce sığan bir tasarım.
- **USB-C:** Şarj ve programlama aynı porttan.
- **Kendi yazılımı:** Launcher ve farklı oyunlar/mini uygulamalar.

## Klasörler
| Klasör | İçerik |
|---|---|
| [`docs/`](docs/) | Kararlar, güç/güvenlik tasarımı, parça listeleri |
| [`firmware/`](firmware/) | ESP32-S3 yazılımı (PlatformIO) |
| [`hardware/pcb/`](hardware/pcb/) | KiCad şema ve PCB dosyaları |
| [`hardware/case/`](hardware/case/) | 3D kasa tasarımı (STEP/STL) |

## Belgeler
- [Donanım kararları](docs/hardware.md)
- [Güç ve batarya güvenliği](docs/power-safety.md)
- [Parça listesi](docs/parts.md)
- [Pin planı](docs/pinout.md)
- [Modüllü sürüm (delikli kart)](docs/module-build.md)

## Yol haritası
- [x] Gereksinimler ve temel parça kararları
- [x] Pin planı
- [x] Tasarım incelemesi (güç, pinler, ses, mekanik) ve düzeltmeler
- [ ] Prototip parçalarını sipariş et
- [ ] Breadboard: ESP32-S3 + ekran + yön tuşu + butonlar + ses
- [ ] Firmware: launcher iskeleti ve ilk uygulama
- [x] KiCad şema (kod ile üretiliyor: `hardware/pcb/gen/`)
- [ ] Modüllü sürüm: delikli kartta montaj ([plan](docs/module-build.md))
- [ ] KiCad PCB yerleşimi (v1 taslak hazır, sipariş öncesi gözden geçirilecek)
- [ ] Kasa tasarımı (PCB ölçülerine göre)
- [ ] PCB v1 sipariş (dizgi maliyeti nedeniyle ertelendi) ve güç devresi testi (bataryasız)
- [ ] Montaj ve tam sistem testi
- [ ] PCB v2 (gerekirse)
