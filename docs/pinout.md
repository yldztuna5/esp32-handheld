# Pin planı

ESP32-S3-WROOM-1-N16R8 için. Breadboard prototipi ve PCB aynı planı kullanır; firmware'deki pin tanımları buradan alınır.

## Kullanılamayan pinler
| Pin | Neden |
|---|---|
| GPIO26-32 | Modül içinde flash'a bağlı |
| GPIO33-37 | Octal PSRAM'e bağlı (R8 modellerde) |
| GPIO19, GPIO20 | USB D-/D+ (programlama ve seri port) |
| GPIO43, GPIO44 | UART0 TX/RX; PCB'de test noktası olarak bırakılır (hata ayıklama) |

## Strapping pinleri
| Pin | Kural |
|---|---|
| GPIO0 | BOOT butonu. Açılışta LOW ise indirme moduna girer. |
| GPIO3 | Sadece isteğe bağlı FG_ALRT (pull-up'lı). Varsayılan ayarlarda açılışı etkilemez. |
| GPIO45 | **Boş bırakılır, asla HIGH'a çekilmez.** HIGH olursa flash 1.8V'a ayarlanır ve modül açılmaz. |
| GPIO46 | Boş bırakılır. |

## Pin atamaları

### Ekran (2.8" SPI TFT modülü, ILI9341, MSP2807 tipi)
LCD, ESP32-S3'ün FSPI pinlerinde (IO_MUX doğrudan bağlantı). ILI9341 için 40 MHz ile başlanır.

| Sinyal | ESP32-S3 | Modül pini | Not |
|---|---|---|---|
| LCD_CS | GPIO10 | CS | |
| LCD_MOSI | GPIO11 | SDI (MOSI) | |
| LCD_CLK | GPIO12 | SCK | |
| LCD_DC | GPIO9 | DC | |
| LCD_RST | GPIO8 | RESET | |
| LCD_BL | GPIO14 | LED | PWM ile parlaklık. 100k pull-down (açılışta ekran karanlık kalsın). Pinin çektiği akım breadboard'da ölçülecek; birkaç mA'den fazlaysa PCB'ye MOSFET eklenir. |
| MISO | GPIO13 | SDO (MISO) bağlı değil | LCD'den okuma gerekmiyor; hat SD kart için kullanılır |
| VCC | 3V3 | VCC | Modüldeki J1 lehim köprüsü kapatılır (3.3V regülatörü atlanır). Kapatılmazsa arka ışık sönük kalır. |
| T_CLK, T_CS, T_DIN, T_DO, T_IRQ | bağlı değil | | Dokunmatik kullanılmıyor |

### microSD (ekran modülünün üzerindeki yuva)
Modülde SD kartın pinleri ayrı bir 4'lü başlıkta. LCD ile aynı SPI hattına bağlanır; sadece bir ek pin (SD_CS) harcar.

| Sinyal | ESP32-S3 | Modül pini | Not |
|---|---|---|---|
| SD_CLK | GPIO12 | SD_SCK | LCD_CLK ile ortak |
| SD_MOSI | GPIO11 | SD_MOSI | LCD_MOSI ile ortak |
| SD_MISO | GPIO13 | SD_MISO | |
| SD_CS | GPIO21 | SD_CS | 10k pull-up |

### Kontroller
Butonlar GND'ye çeker; ESP32'nin dahili pull-up'ları kullanılır.

| Sinyal | ESP32-S3 | Not |
|---|---|---|
| DPAD_UP | GPIO4 | Ana kontrol: 4 tact switch'li yön tuşu |
| DPAD_DOWN | GPIO5 | |
| DPAD_LEFT | GPIO6 | |
| DPAD_RIGHT | GPIO7 | |
| BTN_A | GPIO15 | |
| BTN_B | GPIO16 | |
| BTN_START | GPIO17 | |
| BTN_SELECT | GPIO18 | |
| JOY_X | GPIO1 | ADC1_CH0. Joystick isteğe bağlı; PCB'de footprint bırakılır. Uca 100nF. |
| JOY_Y | GPIO2 | ADC1_CH1. Uca 100nF. |

Joystick potansiyometreleri 3V3 ile beslenir. ADC2 Wi-Fi açıkken çalışmadığı için analog girişler ADC1'de.

### Ses
Aynı pin iki aşamada farklı kullanılır; firmware'de tek satır değişir.

| Sinyal | ESP32-S3 | Breadboard (PAM8403) | PCB (I2S amfi çipi) |
|---|---|---|---|
| AUDIO_OUT | GPIO39 | I2S PDM TX → RC filtre (1k + 4.7nF veya 10nF, iki kademe) → 10k/1k bölücü → 1µF → PAM8403 L girişi | I2S DIN |
| I2S_BCLK | GPIO40 | kullanılmıyor | BCLK |
| I2S_LRCLK | GPIO41 | kullanılmıyor | LRCLK |

- PAM8403 kazancı sabit ve yüksek; 10k/1k bölücü olmadan ses kırpılır.
- Hoparlör PAM8403'ün **L+ ve L- çıkışları arasına** bağlanır; çıkışlar asla GND'ye bağlanmaz.
- PCB'deki I2S amfi (MAX98357A veya NS4168) saat sinyali kesilince kendini kapatır; ayrı AMP_EN pini gerekmez.

### Güç yönetimi
Açık-drain sinyallerin pull-up'ları **3V3'e** gider (batarya ya da USB hattına değil).

| Sinyal | ESP32-S3 | Not |
|---|---|---|
| I2C_SDA | GPIO47 | MAX17048 (pil yüzdesi); 4.7k pull-up |
| I2C_SCL | GPIO48 | 4.7k pull-up. Bazı geliştirme kartlarında RGB LED bu pinde; I2C sadece PCB'de kullanıldığı için sorun değil. |
| CHG_STAT | GPIO38 | BQ24074 /CHG: şarj oluyor (LED ile paylaşılır) |
| PGOOD | GPIO42 | BQ24074 /PGOOD: USB takılı |
| FG_ALRT | GPIO3 | MAX17048 düşük pil uyarısı. İsteğe bağlı; yüzde I2C'den de okunur. |

### Sistem
| Sinyal | ESP32-S3 | Not |
|---|---|---|
| BOOT | GPIO0 | SMD buton GND'ye + 10k pull-up |
| RESET | EN | SMD buton GND'ye; 10k pull-up + 1µF (açılış gecikmesi) |
| USB_D- / USB_D+ | GPIO19 / GPIO20 | USBLC6 üzerinden USB-C'ye |
| UART TX / RX | GPIO43 / GPIO44 | Test noktaları |

## Boş kalan pinler
GPIO45 ve GPIO46 (strapping, boş bırakılır). Joystick takılmazsa GPIO1 ve GPIO2 de boşalır (titreşim motoru vb. için).

## Doğrulanacaklar (ekran modülü gelince)
Modülün şeması satıcı sayfasında yok; aşağıdakiler bu modül tipinin (MSP2807) bilinen düzenine dayanıyor ve breadboard'da kontrol edilecek:
- 14'lü başlık sırası ve SD başlığının sırası (kartın üstündeki yazılardan).
- J1 köprüsünün yeri ve 3.3V ile parlaklık.
- LED pininin çektiği akım.
- SD kartın LCD ile aynı hatta sorunsuz çalıştığı.
