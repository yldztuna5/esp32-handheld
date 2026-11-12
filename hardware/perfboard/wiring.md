# Delikli Pertinaks Noktadan Noktaya Kablolama ve Lehimleme Rehberi

Bu belge `layout.py` tarafından otomatik üretilmiştir. Bakır yol çizimi yerine tüm bağlantılar noktadan noktaya (point-to-point) izole tellerle yapılır.

## 1. Önemli Güvenlik ve Lehimleme Sırası (Önce Güç Zinciri!)

> **KRİTİK UYARI:** `ESP32-S3` geliştirme kartını dişi header yuvalarına **kesinlikle takmayın!** `MT3608` yükseltici modül fabrikadan 12 V – 28 V aralığında ayarlı gelebilir; ayarlanmadan `ESP32-S3` veya `PAM8403` bağlanırsa kartlar anında yanar.

1. **Güç Zincirini Lehimleyin (`ARKA` Kart):**
   - `FUSE1` (5x20 mm sigorta yuvası), `PAD_BAT` (18650 pil yuvası uçları), `PAD_THERM` (pile bantlanan 50 °C KSD301 termostat uçları), `TP4056` şarj modülü, `SW_PWR` açma/kapama anahtarı ve `MT3608` yükseltici modülü lehimleyin.
   - **Dikkat:** `TP4056` üzerindeki `B-` (`B_M`) pini **yalnızca** pil yuvasının eksi (`PAD_BAT.BAT_M`) ucuna gider; sistem şasesi (`GND`) ise `TP4056.OUT_M` pininden alınır (DW01 aşırı deşarj ve kısa devre korumasının çalışması için şarttır).
2. **Zorunlu Test Adımı — `MT3608 5.0 V` Ayarı (`ESP32` Takılı Değilken):**
   - `ESP32-S3` dişi soketine henüz takılı değilken (ve `MT3608.VOUT_P` telini `ESP32` / `PAM8403`'e lehimlemeden önce veya soket boşken) 2 A sigortayı ve 18650 pili kutuplarına dikkat ederek takın.
   - `SW_PWR` anahtarını açın. Multimetreyi DC voltaj kademesine alıp `MT3608.VOUT_P` `(ARKA 12,27)` ile `MT3608.VOUT_M` `(ARKA 18,27)` arasını ölçün.
   - Multimetrede tam **`5.0 V`** (`4.95 V – 5.05 V`) okuyana kadar `MT3608` üzerindeki trimpotu küçük düz tornavidayla (genellikle saat yönünün tersine birçok tur) çevirin.
   - Anahtarı kapatıp pili çıkarın.
3. **Pasif Elemanlar ve Ses Amfisini Lehimleyin (`ARKA` Kart):**
   - Pil bölücü (`R_BAT1` 10k, `R_BAT2` 10k, `C_BAT` 1 µF), ses 2 kademeli RC filtresi ve bölücüsü (`R_AUD1` 1k, `C_AUD1` 10 nF, `R_AUD2` 1k, `C_AUD2` 10 nF, `R_AUD3` 10k, `R_AUD4` 1k, `C_AUD3` 1 µF), `R_SD` (10k pull-up), `R_BL` (10k pull-down) ve `PAM8403` modülünü lehimleyin.
   - Hoparlör kablolarını `PAD_SPK` (`SPK_P` ve `SPK_M`) padlerine bağlayın (`PAM8403` `L+` ve `L-` çıkışları **asla** `GND`'ye bağlanmaz).
4. **Dişi Header ve Konnektörleri Lehimleyin (`ARKA` ve `ÖN` Kart):**
   - `ARKA` kartta `ESP32` için iki adet `1x22` dişi header (`J1` sütun 1, `J3` sütun 10), `J_LINK_R` (`2x9` header) ve isteğe bağlı `J_JOY` (`1x5` header) lehimleyin.
   - `ÖN` kartta `J_LCD` (`1x14` dişi header, satır 34, sütun 5..18), sekiz adet `6x6 mm` tact switch (`SW_UP`, `SW_DOWN`, `SW_LEFT`, `SW_RIGHT`, `SW_A`, `SW_B`, `SW_START`, `SW_SELECT`) ve `J_LINK_F` (`2x9` header, satır 48..49, sütun 7..15) lehimleyin.
5. **Son Kontroller ve Modüllerin Takılması:**
   - Multimetrenin kısa devre (buzzer) kademesiyle `5V` – `GND`, `3V3` – `GND` ve `BAT+` – `BAT-` arasında kısa devre olmadığını doğrulayın.
   - `ESP32-S3` kartını ve `2.8" ILI9341` ekran modülünü dişi soketlerine yerleştirin.

## 2. Noktadan Noktaya Kablolama Tablosu (Tüm Hatlar)

| Hat Adı (Net) | Nereden (`Bileşen.Pin @ KART Sütun,Satır`) | Nereye (`Bileşen.Pin @ KART Sütun,Satır`) | Önerilen Tel Rengi | Açıklama |
|---|---|---|---|---|
| `BAT_RAW_P` | `PAD_BAT.BAT_P` @ ARKA (9,32) | `FUSE1.IN` @ ARKA (9,29) | Kırmızı (Kalın 22-24 AWG) | 18650 pil (+) çıkışından 2A cam sigorta girişine |
| `BAT_FUSED` | `FUSE1.OUT` @ ARKA (18,29) | `PAD_THERM.T_IN` @ ARKA (17,13) | Kırmızı (Kalın 22-24 AWG) | Sigorta çıkışından 50°C KSD301 termostat girişine |
| `BAT_P` | `PAD_THERM.T_OUT` @ ARKA (16,13) | `TP4056.B_P` @ ARKA (16,10) | Kırmızı (Kalın 22-24 AWG) | Termostat çıkışından TP4056 B+ pil girişine |
| `BAT_M` | `PAD_BAT.BAT_M` @ ARKA (10,32) | `TP4056.B_M` @ ARKA (14,10) | Siyah (Kalın 22-24 AWG) | 18650 pil (-) çıkışından TP4056 B- koruma girişine |
| `BAT_PROT_P` | `TP4056.OUT_P` @ ARKA (18,10) | `SW_PWR.IN_BAT` @ ARKA (18,11) | Turuncu (Kalın) | TP4056 korumalı OUT+ çıkışından güç anahtarı girişine |
| `VSYS` | `SW_PWR.OUT_VSYS` @ ARKA (18,12) | `MT3608.VIN_P` @ ARKA (18,14) | Turuncu | Anahtarlanmış pil hattı (MT3608 VIN+ ve pil bölücü üst ucu) |
| `VSYS` | `MT3608.VIN_P` @ ARKA (18,14) | `R_BAT1.VSYS` @ ARKA (16,11) | Turuncu | Anahtarlanmış pil hattı (MT3608 VIN+ ve pil bölücü üst ucu) |
| `5V` | `MT3608.VOUT_P` @ ARKA (12,27) | `PAM8403.VCC` @ ARKA (8,26) | Kırmızı | MT3608 5.0V çıkışı -> PAM8403 VCC ve ESP32 5V pini |
| `5V` | `PAM8403.VCC` @ ARKA (8,26) | `ESP32.J1_21_5V` @ ARKA (1,22) | Kırmızı | MT3608 5.0V çıkışı -> PAM8403 VCC ve ESP32 5V pini |
| `3V3` | `ESP32.J1_1_3V3` @ ARKA (1,2) | `R_SD.3V3` @ ARKA (12,32) | Kırmızı/Beyaz | ESP32 3.3V regüle çıkışı -> Ekran VCC, SD pull-up ve Joystick |
| `3V3` | `R_SD.3V3` @ ARKA (12,32) | `J_JOY.3V3` @ ARKA (12,34) | Kırmızı/Beyaz | ESP32 3.3V regüle çıkışı -> Ekran VCC, SD pull-up ve Joystick |
| `3V3` | `J_JOY.3V3` @ ARKA (12,34) | `J_LINK_R.P1_3V3` @ ARKA (1,36) | Kırmızı/Beyaz | ESP32 3.3V regüle çıkışı -> Ekran VCC, SD pull-up ve Joystick |
| `3V3` | `J_LINK_R.P1_3V3` @ ARKA (1,36) | `J_LINK_F.P1_3V3` @ ÖN (7,48) | Kırmızı/Beyaz | ESP32 3.3V regüle çıkışı -> Ekran VCC, SD pull-up ve Joystick (Kartlar arası 2x9 şerit kablo) |
| `3V3` | `J_LINK_F.P1_3V3` @ ÖN (7,48) | `J_LCD.VCC` @ ÖN (5,34) | Kırmızı/Beyaz | ESP32 3.3V regüle çıkışı -> Ekran VCC, SD pull-up ve Joystick |
| `GND` | `TP4056.OUT_M` @ ARKA (12,10) | `R_BAT2.GND` @ ARKA (13,11) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `R_BAT2.GND` @ ARKA (13,11) | `C_BAT.GND` @ ARKA (13,12) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `C_BAT.GND` @ ARKA (13,12) | `MT3608.VIN_M` @ ARKA (12,14) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `MT3608.VIN_M` @ ARKA (12,14) | `MT3608.VOUT_M` @ ARKA (18,27) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `MT3608.VOUT_M` @ ARKA (18,27) | `ESP32.J1_22_GND` @ ARKA (1,23) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `ESP32.J1_22_GND` @ ARKA (1,23) | `ESP32.J3_22_GND` @ ARKA (10,23) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `ESP32.J3_22_GND` @ ARKA (10,23) | `PAM8403.GND_PWR` @ ARKA (8,27) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `PAM8403.GND_PWR` @ ARKA (8,27) | `PAM8403.GND_AUD` @ ARKA (8,30) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `PAM8403.GND_AUD` @ ARKA (8,30) | `R_BL.GND` @ ARKA (14,32) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `R_BL.GND` @ ARKA (14,32) | `C_AUD1.GND` @ ARKA (6,33) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `C_AUD1.GND` @ ARKA (6,33) | `C_AUD2.GND` @ ARKA (6,34) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `C_AUD2.GND` @ ARKA (6,34) | `R_AUD4.GND` @ ARKA (8,34) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `R_AUD4.GND` @ ARKA (8,34) | `J_JOY.GND` @ ARKA (13,34) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `J_JOY.GND` @ ARKA (13,34) | `J_LINK_R.P2_GND1` @ ARKA (2,36) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `J_LINK_R.P2_GND1` @ ARKA (2,36) | `J_LINK_R.P10_GND2` @ ARKA (1,37) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `J_LINK_R.P10_GND2` @ ARKA (1,37) | `J_LINK_F.P2_GND1` @ ÖN (8,48) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) (Kartlar arası 2x9 şerit kablo) |
| `GND` | `J_LINK_F.P2_GND1` @ ÖN (8,48) | `J_LINK_F.P10_GND2` @ ÖN (7,49) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `J_LINK_F.P10_GND2` @ ÖN (7,49) | `J_LCD.GND` @ ÖN (6,34) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `J_LCD.GND` @ ÖN (6,34) | `SW_UP.GND` @ ÖN (7,36) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `SW_UP.GND` @ ÖN (7,36) | `SW_DOWN.GND` @ ÖN (7,42) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `SW_DOWN.GND` @ ÖN (7,42) | `SW_LEFT.GND` @ ÖN (4,39) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `SW_LEFT.GND` @ ÖN (4,39) | `SW_RIGHT.GND` @ ÖN (10,39) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `SW_RIGHT.GND` @ ÖN (10,39) | `SW_A.GND` @ ÖN (20,37) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `SW_A.GND` @ ÖN (20,37) | `SW_B.GND` @ ÖN (16,40) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `SW_B.GND` @ ÖN (16,40) | `SW_START.GND` @ ÖN (15,45) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `GND` | `SW_START.GND` @ ÖN (15,45) | `SW_SELECT.GND` @ ÖN (10,45) | Siyah | Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar) |
| `LCD_CS` | `ESP32.J1_16_10` @ ARKA (1,17) | `J_LINK_R.P3_LCD_CS` @ ARKA (3,36) | Mavi | ILI9341 Chip Select (GPIO10) |
| `LCD_CS` | `J_LINK_R.P3_LCD_CS` @ ARKA (3,36) | `J_LINK_F.P3_LCD_CS` @ ÖN (9,48) | Mavi | ILI9341 Chip Select (GPIO10) (Kartlar arası 2x9 şerit kablo) |
| `LCD_CS` | `J_LINK_F.P3_LCD_CS` @ ÖN (9,48) | `J_LCD.CS` @ ÖN (7,34) | Mavi | ILI9341 Chip Select (GPIO10) |
| `LCD_RST` | `ESP32.J1_12_8` @ ARKA (1,13) | `J_LINK_R.P4_LCD_RST` @ ARKA (4,36) | Beyaz | ILI9341 Reset (GPIO8) |
| `LCD_RST` | `J_LINK_R.P4_LCD_RST` @ ARKA (4,36) | `J_LINK_F.P4_LCD_RST` @ ÖN (10,48) | Beyaz | ILI9341 Reset (GPIO8) (Kartlar arası 2x9 şerit kablo) |
| `LCD_RST` | `J_LINK_F.P4_LCD_RST` @ ÖN (10,48) | `J_LCD.RESET` @ ÖN (8,34) | Beyaz | ILI9341 Reset (GPIO8) |
| `LCD_DC` | `ESP32.J1_15_9` @ ARKA (1,16) | `J_LINK_R.P5_LCD_DC` @ ARKA (5,36) | Yeşil | ILI9341 Data/Command (GPIO9) |
| `LCD_DC` | `J_LINK_R.P5_LCD_DC` @ ARKA (5,36) | `J_LINK_F.P5_LCD_DC` @ ÖN (11,48) | Yeşil | ILI9341 Data/Command (GPIO9) (Kartlar arası 2x9 şerit kablo) |
| `LCD_DC` | `J_LINK_F.P5_LCD_DC` @ ÖN (11,48) | `J_LCD.DC` @ ÖN (9,34) | Yeşil | ILI9341 Data/Command (GPIO9) |
| `SPI_MOSI` | `ESP32.J1_17_11` @ ARKA (1,18) | `PAD_SD.SD_MOSI` @ ARKA (10,26) | Sarı | Ortak SPI MOSI: LCD SDI + microSD SD_MOSI (GPIO11) |
| `SPI_MOSI` | `PAD_SD.SD_MOSI` @ ARKA (10,26) | `J_LINK_R.P6_SPI_MOSI` @ ARKA (6,36) | Sarı | Ortak SPI MOSI: LCD SDI + microSD SD_MOSI (GPIO11) |
| `SPI_MOSI` | `J_LINK_R.P6_SPI_MOSI` @ ARKA (6,36) | `J_LINK_F.P6_SPI_MOSI` @ ÖN (12,48) | Sarı | Ortak SPI MOSI: LCD SDI + microSD SD_MOSI (GPIO11) (Kartlar arası 2x9 şerit kablo) |
| `SPI_MOSI` | `J_LINK_F.P6_SPI_MOSI` @ ÖN (12,48) | `J_LCD.SDI_MOSI` @ ÖN (10,34) | Sarı | Ortak SPI MOSI: LCD SDI + microSD SD_MOSI (GPIO11) |
| `SPI_SCK` | `ESP32.J1_18_12` @ ARKA (1,19) | `PAD_SD.SD_SCK` @ ARKA (10,27) | Mor | Ortak SPI SCK: LCD SCK + microSD SD_SCK (GPIO12) |
| `SPI_SCK` | `PAD_SD.SD_SCK` @ ARKA (10,27) | `J_LINK_R.P7_SPI_SCK` @ ARKA (7,36) | Mor | Ortak SPI SCK: LCD SCK + microSD SD_SCK (GPIO12) |
| `SPI_SCK` | `J_LINK_R.P7_SPI_SCK` @ ARKA (7,36) | `J_LINK_F.P7_SPI_SCK` @ ÖN (13,48) | Mor | Ortak SPI SCK: LCD SCK + microSD SD_SCK (GPIO12) (Kartlar arası 2x9 şerit kablo) |
| `SPI_SCK` | `J_LINK_F.P7_SPI_SCK` @ ÖN (13,48) | `J_LCD.SCK` @ ÖN (11,34) | Mor | Ortak SPI SCK: LCD SCK + microSD SD_SCK (GPIO12) |
| `LCD_BL` | `ESP32.J1_20_14` @ ARKA (1,21) | `R_BL.LCD_BL` @ ARKA (13,32) | Kahverengi | LCD Arka Işık PWM (GPIO14) + Pull-Down |
| `LCD_BL` | `R_BL.LCD_BL` @ ARKA (13,32) | `J_LINK_R.P8_LCD_BL` @ ARKA (8,36) | Kahverengi | LCD Arka Işık PWM (GPIO14) + Pull-Down |
| `LCD_BL` | `J_LINK_R.P8_LCD_BL` @ ARKA (8,36) | `J_LINK_F.P8_LCD_BL` @ ÖN (14,48) | Kahverengi | LCD Arka Işık PWM (GPIO14) + Pull-Down (Kartlar arası 2x9 şerit kablo) |
| `LCD_BL` | `J_LINK_F.P8_LCD_BL` @ ÖN (14,48) | `J_LCD.LED` @ ÖN (12,34) | Kahverengi | LCD Arka Işık PWM (GPIO14) + Pull-Down |
| `SPI_MISO` | `ESP32.J1_19_13` @ ARKA (1,20) | `PAD_SD.SD_MISO` @ ARKA (9,27) | Gri | Ortak SPI MISO: microSD SD_MISO + LCD SDO (GPIO13) |
| `SPI_MISO` | `PAD_SD.SD_MISO` @ ARKA (9,27) | `J_LINK_R.P9_SPI_MISO` @ ARKA (9,36) | Gri | Ortak SPI MISO: microSD SD_MISO + LCD SDO (GPIO13) |
| `SPI_MISO` | `J_LINK_R.P9_SPI_MISO` @ ARKA (9,36) | `J_LINK_F.P9_SPI_MISO` @ ÖN (15,48) | Gri | Ortak SPI MISO: microSD SD_MISO + LCD SDO (GPIO13) (Kartlar arası 2x9 şerit kablo) |
| `SPI_MISO` | `J_LINK_F.P9_SPI_MISO` @ ÖN (15,48) | `J_LCD.SDO_MISO` @ ÖN (13,34) | Gri | Ortak SPI MISO: microSD SD_MISO + LCD SDO (GPIO13) |
| `SD_CS` | `ESP32.J3_18_21` @ ARKA (10,19) | `PAD_SD.SD_CS` @ ARKA (9,26) | Turkuaz | microSD Chip Select (GPIO21) + 10k Pull-Up |
| `SD_CS` | `PAD_SD.SD_CS` @ ARKA (9,26) | `R_SD.SD_CS` @ ARKA (11,32) | Turkuaz | microSD Chip Select (GPIO21) + 10k Pull-Up |
| `DPAD_UP` | `SW_UP.SIG` @ ÖN (5,36) | `J_LINK_F.P11_DPAD_UP` @ ÖN (8,49) | Yeşil | Yön Tuşu YUKARI (GPIO4, dahili pull-up) |
| `DPAD_UP` | `J_LINK_F.P11_DPAD_UP` @ ÖN (8,49) | `J_LINK_R.P11_DPAD_UP` @ ARKA (2,37) | Yeşil | Yön Tuşu YUKARI (GPIO4, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `DPAD_UP` | `J_LINK_R.P11_DPAD_UP` @ ARKA (2,37) | `ESP32.J1_4_4` @ ARKA (1,5) | Yeşil | Yön Tuşu YUKARI (GPIO4, dahili pull-up) |
| `DPAD_DOWN` | `SW_DOWN.SIG` @ ÖN (5,42) | `J_LINK_F.P12_DPAD_DOWN` @ ÖN (9,49) | Sarı | Yön Tuşu AŞAĞI (GPIO5, dahili pull-up) |
| `DPAD_DOWN` | `J_LINK_F.P12_DPAD_DOWN` @ ÖN (9,49) | `J_LINK_R.P12_DPAD_DOWN` @ ARKA (3,37) | Sarı | Yön Tuşu AŞAĞI (GPIO5, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `DPAD_DOWN` | `J_LINK_R.P12_DPAD_DOWN` @ ARKA (3,37) | `ESP32.J1_5_5` @ ARKA (1,6) | Sarı | Yön Tuşu AŞAĞI (GPIO5, dahili pull-up) |
| `DPAD_LEFT` | `SW_LEFT.SIG` @ ÖN (2,39) | `J_LINK_F.P13_DPAD_LEFT` @ ÖN (10,49) | Mavi | Yön Tuşu SOL (GPIO6, dahili pull-up) |
| `DPAD_LEFT` | `J_LINK_F.P13_DPAD_LEFT` @ ÖN (10,49) | `J_LINK_R.P13_DPAD_LEFT` @ ARKA (4,37) | Mavi | Yön Tuşu SOL (GPIO6, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `DPAD_LEFT` | `J_LINK_R.P13_DPAD_LEFT` @ ARKA (4,37) | `ESP32.J1_6_6` @ ARKA (1,7) | Mavi | Yön Tuşu SOL (GPIO6, dahili pull-up) |
| `DPAD_RIGHT` | `SW_RIGHT.SIG` @ ÖN (8,39) | `J_LINK_F.P14_DPAD_RIGHT` @ ÖN (11,49) | Beyaz | Yön Tuşu SAĞ (GPIO7, dahili pull-up) |
| `DPAD_RIGHT` | `J_LINK_F.P14_DPAD_RIGHT` @ ÖN (11,49) | `J_LINK_R.P14_DPAD_RIGHT` @ ARKA (5,37) | Beyaz | Yön Tuşu SAĞ (GPIO7, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `DPAD_RIGHT` | `J_LINK_R.P14_DPAD_RIGHT` @ ARKA (5,37) | `ESP32.J1_7_7` @ ARKA (1,8) | Beyaz | Yön Tuşu SAĞ (GPIO7, dahili pull-up) |
| `BTN_A` | `SW_A.SIG` @ ÖN (18,37) | `J_LINK_F.P15_BTN_A` @ ÖN (12,49) | Mor | Aksiyon Butonu A (GPIO15, dahili pull-up) |
| `BTN_A` | `J_LINK_F.P15_BTN_A` @ ÖN (12,49) | `J_LINK_R.P15_BTN_A` @ ARKA (6,37) | Mor | Aksiyon Butonu A (GPIO15, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `BTN_A` | `J_LINK_R.P15_BTN_A` @ ARKA (6,37) | `ESP32.J1_8_15` @ ARKA (1,9) | Mor | Aksiyon Butonu A (GPIO15, dahili pull-up) |
| `BTN_B` | `SW_B.SIG` @ ÖN (14,40) | `J_LINK_F.P16_BTN_B` @ ÖN (13,49) | Kahverengi | Aksiyon Butonu B (GPIO16, dahili pull-up) |
| `BTN_B` | `J_LINK_F.P16_BTN_B` @ ÖN (13,49) | `J_LINK_R.P16_BTN_B` @ ARKA (7,37) | Kahverengi | Aksiyon Butonu B (GPIO16, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `BTN_B` | `J_LINK_R.P16_BTN_B` @ ARKA (7,37) | `ESP32.J1_9_16` @ ARKA (1,10) | Kahverengi | Aksiyon Butonu B (GPIO16, dahili pull-up) |
| `BTN_START` | `SW_START.SIG` @ ÖN (13,45) | `J_LINK_F.P17_BTN_START` @ ÖN (14,49) | Gri | START Butonu (GPIO17, dahili pull-up) |
| `BTN_START` | `J_LINK_F.P17_BTN_START` @ ÖN (14,49) | `J_LINK_R.P17_BTN_START` @ ARKA (8,37) | Gri | START Butonu (GPIO17, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `BTN_START` | `J_LINK_R.P17_BTN_START` @ ARKA (8,37) | `ESP32.J1_10_17` @ ARKA (1,11) | Gri | START Butonu (GPIO17, dahili pull-up) |
| `BTN_SELECT` | `SW_SELECT.SIG` @ ÖN (8,45) | `J_LINK_F.P18_BTN_SELECT` @ ÖN (15,49) | Turuncu | SELECT Butonu (GPIO18, dahili pull-up) |
| `BTN_SELECT` | `J_LINK_F.P18_BTN_SELECT` @ ÖN (15,49) | `J_LINK_R.P18_BTN_SELECT` @ ARKA (9,37) | Turuncu | SELECT Butonu (GPIO18, dahili pull-up) (Kartlar arası 2x9 şerit kablo) |
| `BTN_SELECT` | `J_LINK_R.P18_BTN_SELECT` @ ARKA (9,37) | `ESP32.J1_11_18` @ ARKA (1,12) | Turuncu | SELECT Butonu (GPIO18, dahili pull-up) |
| `JOY_X` | `ESP32.J3_4_1` @ ARKA (10,5) | `J_JOY.X` @ ARKA (14,34) | Yeşil/Beyaz | İsteğe Bağlı Analog Joystick X Ekseni (GPIO1 / ADC1_CH0) |
| `JOY_Y` | `ESP32.J3_5_2` @ ARKA (10,6) | `J_JOY.Y` @ ARKA (15,34) | Mavi/Beyaz | İsteğe Bağlı Analog Joystick Y Ekseni (GPIO2 / ADC1_CH1) |
| `AUDIO_OUT` | `ESP32.J3_9_39` @ ARKA (10,10) | `R_AUD1.IN` @ ARKA (3,33) | Sarı | ESP32 PDM Ses Çıkışı (GPIO39) -> 1. RC Filtre Girişi |
| `AUD_FILT1` | `R_AUD1.OUT` @ ARKA (4,33) | `C_AUD1.FILT1` @ ARKA (5,33) | Sarı | Ses RC Filtre 1. Kademe Ara Düğümü (1k + 10nF) |
| `AUD_FILT1` | `C_AUD1.FILT1` @ ARKA (5,33) | `R_AUD2.IN` @ ARKA (3,34) | Sarı | Ses RC Filtre 1. Kademe Ara Düğümü (1k + 10nF) |
| `AUD_FILT2` | `R_AUD2.OUT` @ ARKA (4,34) | `C_AUD2.FILT2` @ ARKA (5,34) | Sarı | Ses RC Filtre 2. Kademe Çıkışı -> 10k/1k Bölücü Girişi |
| `AUD_FILT2` | `C_AUD2.FILT2` @ ARKA (5,34) | `R_AUD3.FILT2` @ ARKA (7,33) | Sarı | Ses RC Filtre 2. Kademe Çıkışı -> 10k/1k Bölücü Girişi |
| `AUD_DIV` | `R_AUD3.DIV` @ ARKA (8,33) | `R_AUD4.DIV` @ ARKA (7,34) | Turuncu | 10k/1k Ses Gerilim Bölücü Çıkışı -> 1µF Kuplaj Kondansatörü |
| `AUD_DIV` | `R_AUD4.DIV` @ ARKA (7,34) | `C_AUD3.DIV` @ ARKA (9,33) | Turuncu | 10k/1k Ses Gerilim Bölücü Çıkışı -> 1µF Kuplaj Kondansatörü |
| `PAM_LIN` | `C_AUD3.LIN` @ ARKA (10,33) | `PAM8403.L_IN` @ ARKA (8,29) | Turuncu | 1µF Kuplaj Kondansatörü Çıkışı -> PAM8403 Sol Giriş (L_IN) |
| `SPK_P` | `PAM8403.L_P` @ ARKA (1,27) | `PAD_SPK.SPK_P` @ ARKA (1,33) | Kırmızı (Hoparlör) | PAM8403 L+ Çıkışından Hoparlör (+) Padine (Asla GND'ye bağlanmaz) |
| `SPK_M` | `PAM8403.L_M` @ ARKA (1,28) | `PAD_SPK.SPK_M` @ ARKA (2,33) | Siyah (Hoparlör) | PAM8403 L- Çıkışından Hoparlör (-) Padine (Asla GND'ye bağlanmaz) |
| `BAT_ADC` | `R_BAT1.ADC` @ ARKA (15,11) | `R_BAT2.ADC` @ ARKA (14,11) | Mor | Pil Gerilim Bölücü Orta Noktası (10k/10k + 1µF) -> GPIO3 |
| `BAT_ADC` | `R_BAT2.ADC` @ ARKA (14,11) | `C_BAT.ADC` @ ARKA (14,12) | Mor | Pil Gerilim Bölücü Orta Noktası (10k/10k + 1µF) -> GPIO3 |
| `BAT_ADC` | `C_BAT.ADC` @ ARKA (14,12) | `ESP32.J1_13_3` @ ARKA (1,14) | Mor | Pil Gerilim Bölücü Orta Noktası (10k/10k + 1µF) -> GPIO3 |

## 3. Kartlar Arası Bağlantı Header Pin Tablosu (`J_LINK_F` ↔ `J_LINK_R`, 2x9 = 18 Pin)

`ÖN` kartın alt kenarındaki `J_LINK_F` (`sütun 7..15, satır 48..49`) ile `ARKA` kartın alt kenarındaki `J_LINK_R` (`sütun 1..9, satır 36..37`) birebir aynı pin sırasıyla bağlanır:

| Pin No | Hat Adı (Net) | `J_LINK_F` (`ÖN` Kart Sütun,Satır) | `J_LINK_R` (`ARKA` Kart Sütun,Satır) | ESP32 Karşılığı | Önerilen Tel Rengi |
|---|---|---|---|---|---|
| 1 | `3V3` | `(7,48)` | `(1,36)` | `J1_1_3V3` | Kırmızı/Beyaz |
| 2 | `GND` | `(8,48)` | `(2,36)` | `J1_22_GND`, `J3_22_GND` | Siyah |
| 3 | `LCD_CS` | `(9,48)` | `(3,36)` | `J1_16_10` | Mavi |
| 4 | `LCD_RST` | `(10,48)` | `(4,36)` | `J1_12_8` | Beyaz |
| 5 | `LCD_DC` | `(11,48)` | `(5,36)` | `J1_15_9` | Yeşil |
| 6 | `SPI_MOSI` | `(12,48)` | `(6,36)` | `J1_17_11` | Sarı |
| 7 | `SPI_SCK` | `(13,48)` | `(7,36)` | `J1_18_12` | Mor |
| 8 | `LCD_BL` | `(14,48)` | `(8,36)` | `J1_20_14` | Kahverengi |
| 9 | `SPI_MISO` | `(15,48)` | `(9,36)` | `J1_19_13` | Gri |
| 10 | `GND` | `(7,49)` | `(1,37)` | `J1_22_GND`, `J3_22_GND` | Siyah |
| 11 | `DPAD_UP` | `(8,49)` | `(2,37)` | `J1_4_4` | Yeşil |
| 12 | `DPAD_DOWN` | `(9,49)` | `(3,37)` | `J1_5_5` | Sarı |
| 13 | `DPAD_LEFT` | `(10,49)` | `(4,37)` | `J1_6_6` | Mavi |
| 14 | `DPAD_RIGHT` | `(11,49)` | `(5,37)` | `J1_7_7` | Beyaz |
| 15 | `BTN_A` | `(12,49)` | `(6,37)` | `J1_8_15` | Mor |
| 16 | `BTN_B` | `(13,49)` | `(7,37)` | `J1_9_16` | Kahverengi |
| 17 | `BTN_START` | `(14,49)` | `(8,37)` | `J1_10_17` | Gri |
| 18 | `BTN_SELECT` | `(15,49)` | `(9,37)` | `J1_11_18` | Turuncu |

## 4. Ekran Modülü Üst `1x4` microSD Başlığı Uçan Kabloları (`PAD_SD`)

Ekran modülünün üst kenarındaki `1x4` SD erkek pin başlığı için delikli kartta soket kullanılmaz; 4 adet esnek kablo doğrudan ekranın üst kenarından arkadaki `ARKA` kart üzerindeki `PAD_SD` lehim padlerine (`sütun 9..10, satır 26..27`) bağlanır:

| Ekran Üst SD Pini | Hat Adı (Net) | `ARKA` Kart Lehim Padi (`PAD_SD`) | ESP32 Pini | Ek Eleman / Not |
|---|---|---|---|---|
| `SD_CS` | `SD_CS` | `PAD_SD.SD_CS` @ ARKA (9,26) | `GPIO21` (`J3_18_21` @ 10,19) | `R_SD` (10k pull-up -> `3V3`) |
| `SD_MOSI` | `SPI_MOSI` | `PAD_SD.SD_MOSI` @ ARKA (10,26) | `GPIO11` (`J1_17_11` @ 1,18) | `LCD_MOSI` ile ortak SPI hattı |
| `SD_MISO` | `SPI_MISO` | `PAD_SD.SD_MISO` @ ARKA (9,27) | `GPIO13` (`J1_19_13` @ 1,20) | `LCD_MISO` ile ortak SPI hattı |
| `SD_SCK` | `SPI_SCK` | `PAD_SD.SD_SCK` @ ARKA (10,27) | `GPIO12` (`J1_18_12` @ 1,19) | `LCD_SCK` ile ortak SPI hattı |
