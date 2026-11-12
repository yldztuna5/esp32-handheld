# Modüllü sürüm (delikli kart)

Özel PCB'nin dizgi maliyeti yüksek çıktığı için ilk cihaz hazır modüllerle,
delikli karta lehimlenerek yapılacak. Özel PCB tasarımı
[`hardware/pcb/`](../hardware/pcb/) altında duruyor, ileride kullanılabilir.

Pin planı aynı: [pinout.md](pinout.md). Bu belge yalnızca güç kısmını ve
farkları anlatır.

## Güç zinciri

```
18650 pil (yuvada)
   │  B+ / B-
TP4056 Type-C şarj modülü (DW01 korumalı)
   │  OUT+ ── açma/kapama anahtarı ──┐
   │  OUT- ─────────────── GND      │
                                     ▼
                         MT3608 yükseltici (5,0 V'a ayarlı)
                                     │ OUT+
                                     ▼
                     ESP32-S3 kartı "5V" pini ── PAM8403 VCC
                     ESP32-S3 kartı "3V3" pini ── ekran VCC
```

Bütün GND'ler ortaktır.

| Bağlantı | Nereden | Nereye |
|---|---|---|
| Pil | yuva + / − | TP4056 B+ / B− |
| Anahtar | TP4056 OUT+ | MT3608 VIN+ (anahtar üzerinden) |
| Şase | TP4056 OUT− | MT3608 VIN−, ESP32 GND |
| 5 V | MT3608 VOUT+ | ESP32 kartı 5V pini, PAM8403 VCC |
| 3,3 V | ESP32 kartı 3V3 pini | ekran VCC |
| Pil ölçümü | anahtardan sonraki pil hattı → 100k → GPIO3 → 100k → GND | GPIO3'e 100 nF (GND'ye) |

Pil ölçümü anahtardan sonra alınır, böylece cihaz kapalıyken bölücü pili
tüketmez. GPIO3'te okunan gerilim pil geriliminin yarısıdır.

## Kurulum sırası

1. **MT3608'i ESP32'ye bağlamadan önce ayarla.** Modül fabrikadan yüksek
   gerilime ayarlı gelebilir (28 V'a kadar çıkar) ve bu ESP32'yi yakar.
   Girişine pili ya da 5 V'u bağla, çıkışı multimetreyle ölç, trimpotu
   çıkış 5,0 V olana kadar çevir (genelde saat yönünün tersine, çok tur).
2. Pili yuvaya takmadan önce yuvanın + ve − uçlarını TP4056 üzerindeki
   B+ / B− yazılarıyla karşılaştır. Ters bağlantı modülü bozar.
3. Önce güç zincirini tek başına kur ve ölç (5 V pininde 5,0 V), sonra
   ESP32 ve diğer parçaları bağla.

## Kullanım kuralları

- **İki USB-C girişi olur.** Şarj, TP4056 modülünün girişinden yapılır;
  kod yükleme ESP32 kartının kendi USB-C girişinden yapılır. Şarj
  modülünde veri hattı yoktur.
- Kod yüklerken anahtarı kapalı tut; kart o sırada bilgisayardan beslenir.
- Cihaz kapalıyken şarj kendiliğinden biter: akım 100 mA'in altına düşünce
  modül şarjı keser ve ışık renk değiştirir. Pil yaklaşık 4,05 V'un altına
  inmedikçe yeniden başlamaz. Gece şarjı için cihazı kapalı bırak.
- Cihaz açıkken de şarj edilebilir ama bu modülde güç yolu yok; cihazın
  çektiği akım yüzünden şarj "doldu" durumuna geçemeyebilir ve pil sürekli
  4,2 V'ta tutulur. Tamamen boşalmış pili cihaz kapalıyken şarj et.
- Şarj akımı 1 A (modülün varsayılanı). 3200 mAh pil için uygundur.
  Bilgisayar portu yerine telefon şarj adaptörü kullan. USB-C'den USB-C'ye
  kabloyla şarj başlamazsa USB-A'dan USB-C'ye kablo kullan.
- Şarj olurken cihazı gözetimsiz bırakma, yanıcı bir şeyin üstünde şarj etme.

## Koruma durumu

Var:

- Aşırı şarj kesmesi (4,28 V)
- Aşırı deşarj kesmesi (yaklaşık 3,0 V)
- Aşırı akım ve kısa devre kesmesi (yaklaşık 3 A)
- Şarj çipinin kendi sıcaklığına göre akımı kısması

Yok:

- Pil sıcaklığına göre şarj kesme (NTC)
- Şarj süresi sınırı
- Güç yolu (şarj sırasında cihazı ayrıca besleme)
- Sigorta ve ters pil koruması

Özel PCB sürümünde bunların hepsi vardır: [power-safety.md](power-safety.md).

## Parçalar

Bkz. [parts.md](parts.md), "Modüllü sürüm ekleri".

## Kasa etkisi

Modüller üst üste geldiği için kasa kalınlığı yaklaşık 30 mm olur. Yükseklik
planı aynı (yaklaşık 130 mm, pil kartın altındaki bölmede).
