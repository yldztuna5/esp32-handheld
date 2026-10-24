# Prototip parça listesi

İlk aşama: breadboard'da ESP32-S3 + ekran + butonlar + joystick + ses. Güç ve şarj devresi breadboard'da kurulmayacak; PCB'de ayrıca test edilecek.

| Parça | Prototipte | Final PCB'de | Nereden |
|---|---|---|---|
| İşlemci | ESP32-S3 DevKitC-1 N16R8 | ESP32-S3-WROOM-1 N16R8 | Türkiye |
| Ekran | 2.8" IPS ST7789V çıplak panel + FPC-to-DIP adaptör | Aynı panel, PCB'de FPC konnektör | AliExpress |
| Joystick | PSP tipi analog joystick + adaptör kartı | Aynı joystick | AliExpress |
| Butonlar | 6x6 mm tact switch | Aynı tip / ince SMD | Türkiye |
| Ses | MAX98357A modülü + kutulu mikro hoparlör (8Ω/4Ω, ~1W) | MAX98357A çipi + aynı hoparlör | Türkiye |
| SD kart | microSD modülü | microSD yuvası | Türkiye |
| Diğer | Breadboard, jumper kablolar, USB-C kablo | — | Türkiye |

## Notlar
- Ekran paneli almadan önce satıcıdan datasheet (pin listesi) istenmeli.
- AliExpress siparişleri 2-3 hafta sürer, önce verilmeli. Beklerken geçici bir ST7789 modülü ile yazılıma başlanabilir.
