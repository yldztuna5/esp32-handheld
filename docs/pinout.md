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
| GPIO3 | Boş bırakılır (JTAG kaynağı seçimi). |
| GPIO45 | **Boş bırakılır, asla HIGH'a çekilmez.** HIGH olursa flash 1.8V'a ayarlanır ve modül açılmaz. |
| GPIO46 | Boş bırakılır. |

## Pin atamaları

### Ekran (Waveshare Pico-ResTouch-LCD-2.8, ST7789)
LCD, ESP32-S3'ün FSPI pinlerinde (IO_MUX doğrudan bağlantı; 80 MHz SPI'ya kadar).

| Sinyal | ESP32-S3 | Ekran kartı (Pico pini) | Not |
|---|---|---|---|
| LCD_CS | GPIO10 | GP9 | |
| LCD_MOSI | GPIO11 | GP11 | |
| LCD_CLK | GPIO12 | GP10 | |
| LCD_DC | GPIO9 | GP8 | |
| LCD_RST | GPIO8 | GP15 | |
| LCD_BL | GPIO14 | GP13 | PWM ile parlaklık (karttaki 8050 transistörünü sürer) |
| MISO | bağlı değil | GP12 | LCD'den okuma gerekmiyor |
| TP_CS | 3V3'e 10k | GP16 | Dokunmatik kullanılmıyor; çip kapalı tutulur |
| TP_IRQ | bağlı değil | GP17 | |
| VSYS | 3V3 hattı | VSYS | Ekran kartının LDO'su bu hattan beslenir |

### microSD (ekran kartının üzerindeki yuva)
SD kart LCD ile aynı SPI hattında **değil**; kendi SDIO pinleri var. ESP32-S3'ün SDMMC birimi 1-bit modda kullanılır.

| Sinyal | ESP32-S3 | Ekran kartı (Pico pini) | Not |
|---|---|---|---|
| SD_CLK | GPIO39 | GP5 | |
| SD_CMD | GPIO38 | GP18 | 10k pull-up |
| SD_D0 | GPIO40 | GP19 | 10k pull-up |
| SD_D3 | GPIO41 | GP22 | 10k pull-up (SD modunu seçer) |
| SD_D1, SD_D2 | bağlı değil, 10k pull-up | GP20, GP21 | 4-bit mod gerekirse GPIO42 ve GPIO13'e alınabilir |

### Kontroller
Butonlar ve joystick düğmesi GND'ye çeker; ESP32'nin dahili pull-up'ları kullanılır.

| Sinyal | ESP32-S3 | Not |
|---|---|---|
| JOY_X | GPIO1 | ADC1_CH0 |
| JOY_Y | GPIO2 | ADC1_CH1 |
| JOY_SW | GPIO4 | Joystick basma = menü |
| BTN_A | GPIO5 | |
| BTN_B | GPIO6 | |
| BTN_START | GPIO7 | |
| BTN_SELECT | GPIO15 | |

Joystick potansiyometreleri 3V3 ile beslenir. ADC2 Wi-Fi açıkken çalışmadığı için analog girişler ADC1'de (GPIO1-10).

### Ses (PAM8403)
| Sinyal | ESP32-S3 | Not |
|---|---|---|
| AUDIO_PDM | GPIO17 | I2S PDM TX çıkışı → RC filtre (1k + 10nF, iki kademe) → 1µF kuplaj → PAM8403 L girişi |
| AMP_EN | GPIO18 | P-MOSFET ile PAM8403 beslemesini açar/kapar (sessizken akım sıfır) |

Hoparlör PAM8403'ün **L+ ve L- çıkışları arasına** bağlanır; çıkışlar asla GND'ye bağlanmaz.

### Güç yönetimi
| Sinyal | ESP32-S3 | Not |
|---|---|---|
| I2C_SDA | GPIO47 | MAX17048 (pil yüzdesi); 4.7k pull-up |
| I2C_SCL | GPIO48 | 4.7k pull-up |
| FG_ALRT | GPIO21 | MAX17048 düşük pil uyarısı (açık-drain, pull-up) |
| CHG_STAT | GPIO16 | BQ24074 /CHG: şarj oluyor (açık-drain, LED ile paylaşılır) |
| PGOOD | GPIO42 | BQ24074 /PGOOD: USB takılı (açık-drain) |

### Sistem
| Sinyal | ESP32-S3 | Not |
|---|---|---|
| BOOT | GPIO0 | SMD buton GND'ye + 10k pull-up |
| RESET | EN | SMD buton GND'ye; 10k pull-up + 1µF (açılış gecikmesi) |
| USB_D- / USB_D+ | GPIO19 / GPIO20 | USBLC6 üzerinden USB-C'ye |
| UART TX / RX | GPIO43 / GPIO44 | Test noktaları |

## Boş kalan pinler
GPIO3, GPIO13, GPIO45, GPIO46 (strapping kısıtları olan pinler dahil). İleride titreşim motoru, ikinci joystick ekseni veya 4-bit SD için kullanılabilir.
