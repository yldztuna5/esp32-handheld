# Güç ve batarya güvenliği

Güvenlik katmanlıdır: bir katman arızalanırsa bir sonraki devreye girer.

```
USB-C ──► PTC sigorta + TVS ──► BQ24074 (NTC + zamanlayıcı + power path)
                                     │
            18650 ── sigorta ── ters takma koruması ── DW01A/FS8205A ◄── NTC (hücreye bantlı)
                                     │
                              TPS63021 3.3V ──► ESP32-S3, ekran, ses
                                     ▲
                              Güç anahtarı (EN pini)
```

## Katmanlar
1. **USB girişi:** PTC sigorta (aşırı akım), TVS diyot (ESD/ani gerilim), CC pinlerinde 5.1k.
2. **Şarj çipi (BQ24074):**
   - **Şarj akımı 500 mA** (RISET = 1.78k). 1A'de çip kapalı kasada 2 W'a kadar ısınabiliyordu; 500 mA'de serin kalır. 3500 mAh hücre yaklaşık 7-8 saatte dolar.
   - **Giriş sınırı USB500** (EN1 = HIGH, EN2 = LOW). Sadece 5.1k dirençle 1A çekmek her USB kaynağında kurala uygun değil; 500 mA her kaynakta güvenli.
   - **Sıcaklık:** 10k, **B≈3950** NTC ile şarj yaklaşık 47°C üstünde durur. B=3435 ile eşik 50°C'ye (en kötü 55°C) çıkıyordu; hücrenin şarj sınırı 45°C. Soğuk eşik 0°C civarı. İki eşik de şema aşamasında seçilen NTC'nin tablosuyla yeniden hesaplanacak.
   - **Güvenlik zamanlayıcısı:** RTMR = 71.5k → yaklaşık 9,5 saat. Varsayılan 4-5 saat, 500 mA'de büyük hücre dolmadan hata verirdi.
   - Power path: şarjdayken sistem USB'den beslenir.
3. **Batarya hattı:** Sigorta (2A civarı) ve ters takma koruması (P-MOSFET). Konnektör ters takılırsa ya da kablo kısa devre olursa devreye girer.
4. **Hücre koruması (DW01A + FS8205A):** Aşırı şarj, aşırı deşarj, kısa devre.
5. **Yazılım:** MAX17048 ile voltaj/yüzde takibi; ~3.1V'ta kayıt + kapanma.
6. **Mekanik:**
   - Kasa PETG/ASA.
   - Batarya ayrı bölmede, ~1 mm boşluk, köpük bantla sabit.
   - Vida, sivri köşe veya sıcak parça bataryaya değmez; regülatör ve şarj çipi bataryadan uzakta.

## Güç anahtarı
Sürgülü anahtar (MSK-12C02) sadece 50 mA taşıyabilir; cihaz 200-300 mA çeker. Bu yüzden anahtar akım yolunda **değil**: TPS63021'in EN pinini batarya hattına ya da GND'ye bağlar. Regülatör kapalıyken yükü bataryadan ayırır; kapalı durumdaki toplam kaçak ~35 µA.

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

## Şemada gözden geçirilecekler
- MAX17048'in toprak bağlantısı (koruma MOSFET'inin hangi tarafında).
- BQ24074'ün boşta bırakılmaması gereken pinleri.
- Isı ve kalınlık değerleri hesap/tahmindir; PCB v1'de ölçülecek.
