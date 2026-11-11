# PCB

Kart, kodla üretilir. Tek kaynak `gen/design.py` (parçalar ve bağlantılar); şema ve kart bundan çıkar.

| Dosya | İçerik |
|---|---|
| `gen/design.py` | Devre tanımı: parçalar, pinler, LCSC kodları |
| `gen/gen_sch.py` | Şemayı üretir (`handheld/handheld.kicad_sch`) |
| `gen/gen_pcb.py`, `pcb_plan.py`, `pcb_route.py` | Kart yerleşimi ve yollar (`handheld/handheld.kicad_pcb`) |
| `gen/check_netlist.py`, `gen/check_pcb.py` | Şema ve kartın `design.py` ile birebir uyduğunu denetler |
| `gen/fab.py` | Üretim dosyaları (`handheld/fab/`) |
| `handheld/handheld-schematic.pdf` | Şemanın PDF'i |
| `handheld/render-top.png`, `render-bottom.png` | Kartın ön ve arka görüntüsü |
| `handheld/fab/gerbers.zip`, `bom-jlcpcb.csv`, `cpl-jlcpcb.csv` | Fiyat teklifi ve sipariş için yüklenecek dosyalar |

Yeniden üretmek için `gen/` içinde `run.ps1` (KiCad 9 gerekir), sonra `check_pcb.py` ve `fab.py`.

## Durum (v1 taslak)
- 90 x 100 mm, 2 katman. Bütün SMD parçalar arka yüzde (tek yüz dizgi); ön yüzde ekran başlıkları ve butonlar.
- ERC: 0 hata. DRC: 0 hata, 0 bağlanmamış uç, şema ile uyumlu.
- **Sipariş öncesi yapılacaklar:**
  - Güç yollarında 0,25 mm'ye inen kısımları genişletmek (özellikle batarya hattı).
  - JLCPCB dizgi dosyasındaki parça yönlerini (rotation) önizlemede tek tek kontrol etmek.
  - Gerber'leri bir görüntüleyicide açıp bakmak.
  - Ekran modülü gelince delik ve başlık konumlarını cetvelle doğrulamak.
  - Pinleri breadboard'da denemek.
