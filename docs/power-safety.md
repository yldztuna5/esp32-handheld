# Güç ve batarya güvenliği

Güvenlik katmanlıdır: bir katman arızalanırsa bir sonraki devreye girer.

```
USB-C ──► PTC sigorta + TVS ──► BQ24074 (NTC + zamanlayıcı + power path)
                                     │
                              18650 + DW01A/FS8205A koruma ◄── NTC (hücreye bantlı)
                                     │
                              Güç anahtarı ──► TPS63020 3.3V ──► ESP32-S3, ekran, ses
```

## Katmanlar
1. **USB girişi:** PTC sigorta (aşırı akım), TVS diyot (ESD/ani gerilim), CC pinlerinde 5.1k.
2. **Şarj çipi (BQ24074):**
   - NTC ile 0°C altında ve 45°C üstünde şarjı durdurur.
   - Güvenlik zamanlayıcısı şarj bitmezse keser.
   - Power path: şarjdayken sistem USB'den beslenir.
   - Şarj akımı 1A (~0.3C).
3. **Hücre koruması (DW01A + FS8205A):** Aşırı şarj, aşırı deşarj, kısa devre.
4. **Yazılım:** MAX17048 ile voltaj/yüzde takibi; ~3.3V'ta kayıt + kapanma.
5. **Mekanik:**
   - Kasa PETG/ASA.
   - Batarya ayrı bölmede, ~1 mm boşluk, köpük bantla sabit.
   - Vida, sivri köşe veya sıcak parça bataryaya değmez; regülatör ve şarj çipi bataryadan uzakta.

## Hücre kuralları
- Sadece orijinal hücre, güvenilir satıcıdan. "9900 mAh", "UltraFire" vb. sahte.
- Hücreye asla doğrudan lehim yapılmaz; tırnaklı (puntalı) hücre + kablo + JST-PH konnektör.
- Koruma devreli hücre ~69 mm, korumasız ~65 mm.

## İlk PCB testi
- Güç bölümüne test noktaları ve kesilebilir köprüler.
- Önce **bataryasız**, akım sınırlamalı güç kaynağıyla sadece güç bölümü test edilir.
- Sonra ESP32'ye güç verilir, en son batarya bağlanır.

## Güç bütçesi (tahmini)
| Bileşen | Akım |
|---|---|
| ESP32-S3 (Wi-Fi kapalı) | ~100-130 mA |
| Ekran arka ışığı (orta) | ~40-60 mA |
| Ses (ortalama) | ~30-60 mA |
| **Toplam** | **~200-250 mA** |

3500 mAh hücre ile ~12 saat, 3000 mAh ile ~10 saat.
