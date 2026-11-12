# ESP32-S3 El Konsolu — Delikli Pertinaks (Perfboard) Yerleşimi

Bu klasör, el lehimlemesiyle üretilecek iki katlı (distanslarla üst üste monte edilen) delikli pertinaks prototipinin yerleşim ve kablolama tasarımını içerir.

## Dosyalar

- **`layout.py`**: Tek doğruluk kaynağı (single source of truth). `FRONT` (ÖN, 60×130 mm, `22×49` kullanılabilir delik) ve `REAR` (ARKA, 50×100 mm, `18×37` kullanılabilir delik) kart ızgaralarını, tüm bileşen ayak izlerini (pin koordinatları + gövde sınır dikdörtgenleri), bağlantı listesini (netlist) ve tasarım/pinout doğrulama testlerini tanımlar.
- **`front.svg`**: ÖN kartın bileşen yüzünden (üstten) görünümü. 2.8" ILI9341 ekran soketi (`J_LCD`), ekran montaj delikleri, üstteki `1x4` SD başlığı bilgisi, 8 adet `6x6 mm` yön/aksiyon butonu ve alt kenardaki `2x9` kartlar arası bağlantı başlığını (`J_LINK_F`) gösterir.
- **`rear.svg`**: ARKA kartın bileşen yüzünden görünümü. `ESP32-S3-DevKitC-1`, `TP4056` şarj modülü, `SW_PWR` sürgülü güç anahtarı, `MT3608` yükseltici modül, `FUSE1` 5×20 mm sigorta yuvası, `PAM8403` ses amfisi, 2 kademeli ses RC filtresi + bölücü, pil gerilim bölücüsü (`10k + 10k + 1 µF`) ve kablo bağlantı padlerini gösterir.
- **`wiring.md`**: Güç zincirinden başlayan adım adım lehimleme sırası (**`ESP32` takılmadan önce `MT3608 5.0 V` ayar adımı dahil**), noktadan noktaya tel bağlantı tablosu, `2x9` kartlar arası başlığın pin-pin tablosu ve ekranın üstündeki `1x4` SD başlığından gelen 4 uçan kablonun listesi.

## Yeniden Üretme

Standart Python 3 kütüphanesi dışında hiçbir ek paket gerekmez. Tüm doğrulama kontrollerini çalıştırmak ve `front.svg`, `rear.svg`, `wiring.md` dosyalarını yeniden üretmek için:

```bash
python hardware/perfboard/layout.py
```

Betik herhangi bir delik çakışması, gövde üst üste binmesi, kart sınırı aşımı, ekran montaj deliği ihlali veya `docs/pinout.md` uyuşmazlığı bulursa sıfırdan farklı çıkış koduyla (`exit 1`) sonlanır.

## Parçalar Geldiğinde Ölçülerek Doğrulanması Gereken Varsayımlar

1. **`ESP32-S3` Satır Aralığı ve Pin Sırası (Serigrafi Kontrolü Şart!):**
   - `layout.py` başında `ESP32_ROW_SPACING = 9` (22.86 mm, `J1` sütun 1 ve `J3` sütun 10) varsayılan olarak ayarlanmıştır. Piyasada satılan bazı klon `ESP32-S3-WROOM-1-N16R8` kartlarında iki header dizisi arası **10 delik (25.40 mm)** olabilir; böyle bir kart gelirse `ESP32_ROW_SPACING = 10` yapılıp betik yeniden çalıştırılmalıdır.
   - Header pin dizilimi resmi `ESP32-S3-DevKitC-1` sırasına (`J1` ve `J3`, 2×22 pin) göre kodlanmıştır. **Lehimlemeden önce gelen kartın üzerindeki serigrafi (silk) yazılarıyla bu pin sırası tek tek karşılaştırılmalıdır.**
2. **Gerçek Delikli Pertinaks Delik Sayıları:**
   - 6×13 cm (`FRONT`) kartta kenarlardan 1'er delik boşluk bırakılarak `22×49` kullanılabilir delik, 5×10 cm (`REAR`) kartta ise `18×37` kullanılabilir delik varsayılmıştır. Satın alınan pertinaksların kesim toleransına göre gerçek delik sayısı kumpasla veya sayılarak kontrol edilmelidir (ör. Robotistan'daki 6×13 cm ilanının başlığında 7×12 cm geçmektedir).
3. **Ekran Modülü Boyutu, Başlık Konumu ve Montaj Delikleri:**
   - 2.8" SPI TFT modülünün `50.0 × 86.0 mm` (MSP2806/MSP2807 ölçüsü) olduğu, `1x14` erkek başlığın alt kısa kenardan 2 mm içeride ortalandığı (`satır 34, sütun 5..18`) ve montaj deliklerinin sol-üst köşeden `(3,3)`, `(47,3)`, `(3,79.08)`, `(47,79.08)` mm'de (`(3,2)`, `(20,2)`, `(3,32)`, `(20,32)` delikleri) bulunduğu varsayılmıştır. Ekran geldiğinde pin sırası (`VCC..T_IRQ`), üstteki `1x4` SD pin sırası ve `J1` 3.3V lehim köprüsü doğrulanmalıdır.
4. **Hazır Modül ve Bileşen Ölçüleri:**
   - `TP4056` (`25 × 16.5 mm` → `7×10` delik), `MT3608` (`36 × 17 mm` → `7×14` delik), `PAM8403` (`21 × 18 mm` → `8×7` delik), `5×20 mm` sigorta yuvası (`22 × 10 mm`, bacaklar arası ~22.5 mm → 9 delik aralığı = 22.86 mm) ve `IC125B` sürgülü anahtar (3 pin, 2.54 mm adım) ölçüleri standart modül çizimlerine göre alınmıştır.

## Yerleşimin Sıkışık Olduğu Noktalar

- **`ARKA` Kart Genişliği (Sütun 1..11 `ESP32` + Sütun 12..18 `TP4056`/`MT3608`):** `18` delik genişliğin tamamı kullanılmıştır (`11` sütun `ESP32` gövdesi + `7` sütun güç modülleri). `ESP32_ROW_SPACING = 10` olan geniş bir klon kullanılırsa `J3` header'ı sütun 11'e kayar ve sütun 12'deki `TP4056`/`MT3608` kenarıyla arasında boş delik kalmaz (modül kenarları birbirine sıfır oturur).
- **Üst Kenarda Çift USB-C Çıkışı (`ARKA` Satır 1):** Hem `ESP32-S3`'ün hem de `TP4056`'nın USB-C konnektörleri `ARKA` kartın üst kenarına (`satır 1`) bakmaktadır; USB kablo fişlerinin birbirine sürtmemesi için `TP4056` modülü karta lehimlenirken sağ kenara (`sütun 18`) mümkün olduğunca yakın hizalanmalıdır.
- **`ARKA` Kart Alt Bölgesi (`Satır 26..37`):** `PAM8403` (`sütun 1..8, satır 26..32`), `FUSE1` (`sütun 9..18, satır 28..31`), ses RC filtre elemanları (`satır 33..34`) ve `J_LINK_R` (`satır 36..37`) arasında yalnızca 1'er delik boşluk vardır; direnç ve kondansatörlerin dik (radyal/2 delik) lehimlenmesi önerilir.
- **`ÖN` Kart Alt Buton Bölgesi (`Satır 35..49`):** Ekranın alt kenarı (`satır 34`) ile `SW_UP` (`satır 36..37`) ve `SW_SELECT`/`SW_START` (`satır 45..46`) ile `J_LINK_F` (`satır 48..49`) arasında 1'er satır boşluk bulunmaktadır.

## İnceleme notları

Yerleşim bir Gemini ajanına çizdirildi; betiğin kontrolleri yeniden çalıştırıldı ve bağlantı tablosu [pin planı](../../docs/pinout.md) ile karşılaştırıldı.

- Dirençler çizimde iki komşu deliğe oturuyor; bu yüzden **dik** (ayakta) lehimlenir.
- `J_LINK_F` ön kartın ön yüzünde çizili ama oraya header takılmaz: 18 tel kartın arkasından doğrudan lehimlenir ve arka karttaki `J_LINK_R` noktalarına gider.
- TP4056, MT3608 ve PAM8403 modüllerinin lehim noktaları 2,54 mm ızgaraya tam oturmaz; çizimdeki pin yerleri yaklaşık, modüller kısa tellerle bağlanır.
- ESP32 kartının sıra aralığı 10 delik (25,4 mm) çıkarsa sağ sıra TP4056'ya çok yaklaşır; `layout.py` içindeki parametre değiştirilip yeniden üretilmelidir.
- Yukarı tuşu ekran modülünün alt kenarına bir delik mesafede; kasa çerçevesi bu aralığa göre tasarlanacak.
