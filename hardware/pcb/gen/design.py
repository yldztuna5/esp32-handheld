"""ESP32-S3 handheld console - circuit definition (single source of truth).

Plain data + small helpers, no side effects on import.  Consumed by
gen_sch.py (schematic), check_netlist.py, bom.py and, later, the PCB generator.

Each part is a dict:
    ref        reference designator
    value      value / part name shown on the schematic
    symbol     "Lib:Name" (KiCad library, or the project library "handheld")
    footprint  "Lib:Name"
    lcsc       LCSC / JLCPCB part number ("" if none)
    assembly   "jlc"  = placed by JLCPCB
               "hand" = hand-soldered later, not in the JLCPCB BOM
               "none" = no component (test pad, mounting hole)
    group      functional block on the schematic
    pins       {pin number: net name or None (= intentionally unconnected)}
               every pin of the symbol must be listed
"""

PROJECT = "handheld"
TITLE = "ESP32-S3 Handheld Console"
REVISION = "0.1"

# ---------------------------------------------------------------- passives --
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"

# value -> LCSC (0603 1 % thick film, all JLCPCB basic unless noted)
RES_LCSC = {
    "100R": "C22775",
    "1k": "C21190",
    "1.5k": "C22843",
    "1.78k": "C13118",   # extended
    "2.2k": "C4190",
    "4.7k": "C23162",
    "5.1k": "C23186",
    "10k": "C25804",
    "68k": "C23231",
    "100k": "C25803",
    "180k": "C22827",    # extended (preferred)
    "1M": "C22935",
}
# value -> (LCSC, footprint, description)
CAP_LCSC = {
    "100nF": ("C14663", C0603, "100nF 50V X7R 0603"),
    "1uF": ("C15849", C0603, "1uF 50V X5R 0603"),
    "10uF": ("C96446", C0603, "10uF 25V X5R 0603"),
    "22uF": ("C45783", C0805, "22uF 25V X5R 0805"),
}

PARTS = []


def _part(ref, value, symbol, footprint, lcsc, pins, group, assembly="jlc", desc=""):
    PARTS.append({
        "ref": ref, "value": value, "symbol": symbol, "footprint": footprint,
        "lcsc": lcsc, "assembly": assembly, "group": group, "desc": desc,
        "pins": {str(k): v for k, v in pins.items()},
    })


def _r(ref, value, a, b, group):
    _part(ref, value, "Device:R", R0603, RES_LCSC[value], {1: a, 2: b}, group,
          desc=value + " 1% 0603")


def _c(ref, value, a, b, group):
    lcsc, fp, desc = CAP_LCSC[value]
    _part(ref, value, "Device:C", fp, lcsc, {1: a, 2: b}, group, desc=desc)


# -------------------------------------------------------------- USB input --
G = "usb"
_part("J1", "USB-C 16P", "Connector:USB_C_Receptacle_USB2.0_16P",
      "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948", {
          "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
          "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
          "A5": "CC1", "B5": "CC2",
          "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN",
          "A8": None, "B8": None,
      }, G, desc="HRO TYPE-C-31-M-12")
_r("R1", "5.1k", "CC1", "GND", G)
_r("R2", "5.1k", "CC2", "GND", G)
_part("F1", "PTC 0.75A", "Device:Polyfuse", "Fuse:Fuse_1206_3216Metric", "C20987",
      {1: "VBUS", 2: "VBUS_F"}, G, desc="SMD1206P075TF 0.75A hold 6V")
_part("D1", "SMF5.0A", "Diode:SMF5V0A", "Diode_SMD:D_SOD-123F", "C193402",
      {1: "VBUS_F", 2: "GND"}, G, desc="TVS 5V unidirectional, pin 1 = cathode")
_part("U1", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
      "C7519", {1: "USB_DN", 6: "USB_DN", 3: "USB_DP", 4: "USB_DP", 5: "VBUS_F", 2: "GND"}, G)

# ---------------------------------------------------------------- charger --
G = "charger"
_part("U2", "BQ24074RGTR", "Battery_Management:BQ24074RGT",
      "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm", "C54313", {
          1: "NTC",                 # TS
          2: "VBAT", 3: "VBAT",     # BAT
          4: "GND",                 # /CE
          5: "GND",                 # EN2
          6: "CHG_EN1",             # EN1
          7: "PGOOD_N",             # /PGOOD
          8: "GND", 17: "GND",      # VSS + pad
          9: "CHG_K",               # /CHG
          10: "SYS", 11: "SYS",     # OUT
          12: "CHG_ILIM", 13: "VBUS_F", 14: "CHG_TMR",
          15: None,                 # ITERM open = default 10 % termination
          16: "CHG_ISET",
      }, G)
_c("C1", "1uF", "VBUS_F", "GND", G)
_c("C2", "10uF", "SYS", "GND", G)
_c("C3", "10uF", "VBAT", "GND", G)
_r("R3", "1.78k", "CHG_ISET", "GND", G)
_r("R4", "1.5k", "CHG_ILIM", "GND", G)
_r("R5", "68k", "CHG_TMR", "GND", G)
_r("R6", "10k", "SYS", "CHG_EN1", G)
_part("J3", "NTC (XH-2)", "Connector_Generic:Conn_01x02",
      "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", "",
      {1: "NTC", 2: "GND"}, G, assembly="hand", desc="JST B2B-XH-A")
_r("R8", "100k", "3V3", "PGOOD_N", G)
_r("R9", "2.2k", "SYS", "LED_A", G)
_part("D2", "RED", "Device:LED", "LED_SMD:LED_0603_1608Metric", "C2286",
      {1: "CHG_K", 2: "LED_A"}, G, desc="KT-0603R red LED, pin 1 = cathode")
_part("D3", "BAT54", "handheld:BAT54", "Package_TO_SOT_SMD:SOT-23", "C8590",
      {1: "CHG_STAT", 2: None, 3: "CHG_K"}, G, desc="single Schottky SOT-23: 1 A, 2 NC, 3 K")
_r("R10", "100k", "3V3", "CHG_STAT", G)

# --------------------------------------------------- battery + protection --
G = "battery"
_part("J2", "BATT (PH-2)", "Connector_Generic:Conn_01x02",
      "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", "",
      {1: "BATT_P", 2: "BATT_N"}, G, assembly="hand", desc="JST S2B-PH-K")
_part("F2", "2A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", "C3105",
      {1: "BATT_P", 2: "BATT_PF"}, G, desc="Littelfuse 0466002.NRHF 2A fast 1206")
_part("Q1", "AO3401A", "Transistor_FET:AO3401A", "Package_TO_SOT_SMD:SOT-23", "C15127",
      {1: "Q1_G", 2: "VBAT", 3: "BATT_PF"}, G, desc="P-MOSFET: 1 G, 2 S, 3 D")
_r("R11", "10k", "Q1_G", "GND", G)
_part("U3", "DW01A", "Battery_Management:DW01A", "Package_TO_SOT_SMD:SOT-23-6", "C351410",
      {1: "DW_OD", 2: "DW_CS", 3: "DW_OC", 4: None, 5: "DW_VCC", 6: "BATT_N"}, G)
_r("R13", "100R", "VBAT", "DW_VCC", G)
_c("C4", "100nF", "DW_VCC", "BATT_N", G)
_r("R14", "1k", "DW_CS", "GND", G)
_part("Q2", "8205A", "handheld:Q_8205_Dual_NMOS", "Package_TO_SOT_SMD:SOT-23-6", "C351449",
      {1: "BATT_N", 2: "FET_D", 3: "GND", 4: "DW_OC", 5: "FET_D", 6: "DW_OD"}, G,
      desc="UMW 8205A dual N-MOSFET: 1 S1, 2 D12, 3 S2, 4 G2, 5 D12, 6 G1")

# ------------------------------------------------------------- fuel gauge --
G = "gauge"
_part("U4", "MAX17048G+T10", "handheld:MAX17048",
      "Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm", "C2682616", {
          1: "GND",       # CTG
          2: "VBAT",      # CELL
          3: "VBAT",      # VDD
          4: "GND",
          5: "FG_ALRT",   # /ALRT
          6: "GND",       # QSTRT
          7: "I2C_SCL", 8: "I2C_SDA",
          9: "GND",       # EP
      }, G)
_c("C5", "100nF", "VBAT", "GND", G)
_r("R15", "4.7k", "3V3", "I2C_SDA", G)
_r("R16", "4.7k", "3V3", "I2C_SCL", G)
_r("R17", "10k", "3V3", "FG_ALRT", G)

# -------------------------------------------------------------- regulator --
G = "regulator"
_part("U5", "TPS63020DSJR", "handheld:TPS63020DSJ",
      "handheld:TPS63020_DSJ", "C15483", {
          1: "VIN_REG",                 # VINA
          2: "GND",
          3: "FB",
          4: "VOUT_REG", 5: "VOUT_REG",
          6: "SW_L2", 7: "SW_L2",
          8: "SW_L1", 9: "SW_L1",
          10: "VIN_REG", 11: "VIN_REG",
          12: "EN_SW",
          13: "GND",                    # PS/SYNC
          14: None,                     # PG
          15: "GND",                    # thermal pad / PGND
      }, G)
SOLDER_JUMPER_FP = "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm"
_part("JP1", "SYS-VIN", "Jumper:SolderJumper_2_Bridged", SOLDER_JUMPER_FP, "",
      {1: "SYS", 2: "VIN_REG"}, G, assembly="none", desc="bridged by copper, cut to isolate")
_c("C6", "10uF", "VIN_REG", "GND", G)
_c("C7", "10uF", "VIN_REG", "GND", G)
_c("C8", "100nF", "VIN_REG", "GND", G)
_part("L1", "1.5uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4020S", "C167824",
      {1: "SW_L1", 2: "SW_L2"}, G, desc="FNR4020S1R5MT 1.5uH 3A sat 4.9A")
_c("C9", "22uF", "VOUT_REG", "GND", G)
_c("C10", "22uF", "VOUT_REG", "GND", G)
_c("C11", "22uF", "VOUT_REG", "GND", G)
_r("R18", "1M", "VOUT_REG", "FB", G)
_r("R19", "180k", "FB", "GND", G)
_part("JP2", "VOUT-3V3", "Jumper:SolderJumper_2_Bridged", SOLDER_JUMPER_FP, "",
      {1: "VOUT_REG", 2: "3V3"}, G, assembly="none", desc="bridged by copper, cut to isolate")
_r("R20", "1M", "EN_SW", "GND", G)
_part("SW1", "MSK12C02", "Switch:SW_SPDT", "Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02",
      "C431540", {2: "EN_SW", 1: "EN_PU", 3: "GND"}, G, desc="power slide switch, 2 = common")
_r("R21", "10k", "VIN_REG", "EN_PU", G)

# -------------------------------------------------------------------- MCU --
G = "mcu"
_part("U6", "ESP32-S3-WROOM-1-N16R8", "RF_Module:ESP32-S3-WROOM-1",
      "RF_Module:ESP32-S3-WROOM-1", "C2913202", {
          1: "GND", 40: "GND", 41: "GND",
          2: "3V3",
          3: "ESP_EN",
          4: "BTN_UP",        # IO4
          5: "BTN_DOWN",      # IO5
          6: "BTN_LEFT",      # IO6
          7: "BTN_RIGHT",     # IO7
          8: "BTN_A",         # IO15
          9: "BTN_B",         # IO16
          10: "BTN_START",    # IO17
          11: "BTN_SELECT",   # IO18
          12: "LCD_RST",      # IO8
          13: "USB_DN",       # IO19
          14: "USB_DP",       # IO20
          15: "FG_ALRT",      # IO3
          16: None,           # IO46
          17: "LCD_DC",       # IO9
          18: "LCD_CS",       # IO10
          19: "SPI_MOSI",     # IO11
          20: "SPI_CLK",      # IO12
          21: "SPI_MISO",     # IO13
          22: "LCD_BL",       # IO14
          23: "SD_CS",        # IO21
          24: "I2C_SDA",      # IO47
          25: "I2C_SCL",      # IO48
          26: None,           # IO45
          27: "ESP_IO0",      # IO0
          28: None,           # IO35 (octal PSRAM on N16R8)
          29: None,           # IO36
          30: None,           # IO37
          31: "CHG_STAT",     # IO38
          32: "I2S_DOUT",     # IO39
          33: "I2S_BCLK",     # IO40
          34: "I2S_LRCLK",    # IO41
          35: "PGOOD_N",      # IO42
          36: "UART_RX",      # RXD0 / IO44
          37: "UART_TX",      # TXD0 / IO43
          38: "JOY_Y",        # IO2
          39: "JOY_X",        # IO1
      }, G)
_c("C12", "10uF", "3V3", "GND", G)
_c("C13", "100nF", "3V3", "GND", G)
_r("R22", "10k", "3V3", "ESP_EN", G)
_c("C14", "1uF", "ESP_EN", "GND", G)
TACT_FP = "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A"
_part("SW2", "RESET", "Switch:SW_Push", TACT_FP, "C318884",
      {1: "ESP_EN", 2: "GND"}, G, desc="XKB TS-1187A-B-A-B")
_r("R23", "10k", "3V3", "ESP_IO0", G)
_part("SW3", "BOOT", "Switch:SW_Push", TACT_FP, "C318884",
      {1: "ESP_IO0", 2: "GND"}, G, desc="XKB TS-1187A-B-A-B")
_r("R24", "100k", "LCD_BL", "GND", G)
_r("R25", "10k", "3V3", "SD_CS", G)
_c("C15", "100nF", "JOY_X", "GND", G)
_c("C16", "100nF", "JOY_Y", "GND", G)
_part("J9", "UART", "Connector_Generic:Conn_01x04",
      "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "",
      {1: "3V3", 2: "UART_TX", 3: "UART_RX", 4: "GND"}, G, assembly="hand")

# ----------------------------------------------------------- display + SD --
G = "display"
_part("J4", "LCD (MSP2807)", "Connector_Generic:Conn_01x14",
      "Connector_PinSocket_2.54mm:PinSocket_1x14_P2.54mm_Vertical", "", {
          1: "3V3", 2: "GND", 3: "LCD_CS", 4: "LCD_RST", 5: "LCD_DC",
          6: "SPI_MOSI", 7: "SPI_CLK", 8: "LCD_BL",
          9: None, 10: None, 11: None, 12: None, 13: None, 14: None,
      }, G, assembly="hand")
_part("J5", "SD", "Connector_Generic:Conn_01x04",
      "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical", "",
      {1: "SD_CS", 2: "SPI_MOSI", 3: "SPI_MISO", 4: "SPI_CLK"}, G, assembly="hand")

# ---------------------------------------------------------------- buttons --
G = "buttons"
for _i, _name in enumerate(["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "START", "SELECT"]):
    _part("SW%d" % (4 + _i), _name, "Switch:SW_Push", "Button_Switch_THT:SW_PUSH_6mm", "",
          {1: "BTN_" + _name, 2: "GND"}, G, assembly="hand", desc="6 mm THT tact switch")
_part("J6", "JOYSTICK", "Connector_Generic:Conn_01x05",
      "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", "",
      {1: "GND", 2: "3V3", 3: "JOY_X", 4: "JOY_Y", 5: None}, G, assembly="hand")

# ------------------------------------------------------------------ audio --
G = "audio"
_part("U7", "MAX98357AETE+T", "Audio:MAX98357A",
      "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm", "C910544", {
          1: "I2S_DOUT",      # DIN
          2: None,            # GAIN_SLOT open = 9 dB
          3: "GND", 11: "GND", 15: "GND", 17: "GND",
          4: "AMP_SD",        # /SD_MODE
          5: None, 6: None, 12: None, 13: None,   # NC
          7: "SYS", 8: "SYS",
          9: "SPK_P", 10: "SPK_N",
          14: "I2S_LRCLK", 16: "I2S_BCLK",
      }, G)
_c("C17", "10uF", "SYS", "GND", G)
_c("C18", "100nF", "SYS", "GND", G)
_r("R26", "10k", "3V3", "AMP_SD", G)
_part("J7", "SPEAKER", "Connector_Generic:Conn_01x02",
      "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "",
      {1: "SPK_P", 2: "SPK_N"}, G, assembly="hand")

# ------------------------------------------------------------------- misc --
G = "misc"
for _i, _net in enumerate(["VBUS_F", "SYS", "VBAT", "3V3", "GND", "VOUT_REG"]):
    _part("TP%d" % (_i + 1), _net, "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "",
          {1: _net}, G, assembly="none")
for _i in range(8):
    _m3 = _i < 4
    _part("H%d" % (_i + 1), "M3" if _m3 else "M2.5", "Mechanical:MountingHole",
          "MountingHole:MountingHole_3.2mm_M3" if _m3 else "MountingHole:MountingHole_2.7mm_M2.5",
          "", {}, G, assembly="none")

# ------------------------------------------------------------ net classes --
NET_CLASSES = {
    "Power": {
        "track_width": 0.5,
        "clearance": 0.2,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "nets": [
            "GND", "VBUS", "VBUS_F", "SYS", "VBAT", "BATT_P", "BATT_PF", "BATT_N",
            "FET_D", "VIN_REG", "SW_L1", "SW_L2", "VOUT_REG", "3V3", "SPK_P", "SPK_N",
        ],
    },
}
POWER_NETS = NET_CLASSES["Power"]["nets"]

# Nets that need a PWR_FLAG on the schematic (power-input pins with no
# power-output pin on the net).  Schematic/ERC only, no electrical meaning.
PWR_FLAG_NETS = ["GND", "VBUS_F", "3V3", "VIN_REG", "DW_VCC", "BATT_N"]

# Display names of the schematic blocks (key = part["group"]).
GROUPS = {
    "usb": "USB INPUT",
    "charger": "CHARGER / POWER PATH (BQ24074)",
    "battery": "BATTERY + PROTECTION (DW01A / 8205A)",
    "gauge": "FUEL GAUGE (MAX17048)",
    "regulator": "3V3 BUCK-BOOST (TPS63020)",
    "mcu": "MCU (ESP32-S3-WROOM-1-N16R8)",
    "display": "DISPLAY + SD",
    "buttons": "BUTTONS + JOYSTICK",
    "audio": "AUDIO (MAX98357A)",
    "misc": "MISC",
}


# ---------------------------------------------------------------- helpers --
def part(ref):
    for p in PARTS:
        if p["ref"] == ref:
            return p
    raise KeyError(ref)


def nets():
    """{net name: sorted list of (ref, pin)} for all connected pins."""
    out = {}
    for p in PARTS:
        for pin, net in p["pins"].items():
            if net is not None:
                out.setdefault(net, []).append((p["ref"], pin))
    return {k: sorted(v) for k, v in out.items()}


def net_class(net):
    for name, nc in NET_CLASSES.items():
        if net in nc["nets"]:
            return name
    return "Default"


def assembled_parts():
    return [p for p in PARTS if p["assembly"] == "jlc"]
