#!/usr/bin/env python3
"""Single source of truth for the ESP32-S3 handheld perfboard layout.

Defines the FRONT (60x130 mm, 22x49 usable holes) and REAR (50x100 mm, 18x37
usable holes) single-sided perfboards, component footprints, netlist, design
rule / pinout self-checks, and generates `front.svg`, `rear.svg`, and `wiring.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import html
import sys
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Board grid parameters (2.54 mm pitch, 1 hole margin around edges)
# ---------------------------------------------------------------------------
PITCH_MM: float = 2.54
MARGIN_HOLES: int = 1

FRONT_WIDTH_MM: float = 60.0
FRONT_HEIGHT_MM: float = 130.0
FRONT_COLS: int = 22  # Usable columns: 1..22
FRONT_ROWS: int = 49  # Usable rows: 1..49

REAR_WIDTH_MM: float = 50.0
REAR_HEIGHT_MM: float = 100.0
REAR_COLS: int = 18   # Usable columns: 1..18
REAR_ROWS: int = 37   # Usable rows: 1..37

# Parameter for ESP32-S3-DevKitC-1 row spacing in pitch intervals:
# Default 9 intervals = 22.86 mm (J1 at col 1, J3 at col 10).
# A wider clone may use 10 intervals = 25.40 mm (J1 at col 1, J3 at col 11).
ESP32_ROW_SPACING: int = 9

# Display module physical specification (MSP2806 / MSP2807, 50.0 x 86.0 mm)
LCD_MOD_WIDTH_MM: float = 50.0
LCD_MOD_HEIGHT_MM: float = 86.0
LCD_MOD_TOP_LEFT_COL: int = 2
LCD_MOD_TOP_LEFT_ROW: int = 1
LCD_MOUNTING_HOLES_MM: List[Tuple[float, float]] = [
    (3.0, 3.0),
    (47.0, 3.0),
    (3.0, 79.08),
    (47.0, 79.08),
]
# Closest grid holes corresponding to the 4 display module mounting holes
LCD_MOUNTING_HOLES_GRID: List[Tuple[int, int]] = [
    (3, 2),
    (20, 2),
    (3, 32),
    (20, 32),
]

# ---------------------------------------------------------------------------
# Source-of-truth GPIO table encoded from docs/pinout.md and docs/module-build.md
# ---------------------------------------------------------------------------
PINOUT_GPIO_MAP: Dict[str, str] = {
    "GPIO10": "LCD_CS",
    "GPIO11": "SPI_MOSI",   # LCD_MOSI + SD_MOSI shared FSPI MOSI
    "GPIO12": "SPI_SCK",    # LCD_CLK + SD_CLK shared FSPI SCK
    "GPIO9": "LCD_DC",
    "GPIO8": "LCD_RST",
    "GPIO14": "LCD_BL",
    "GPIO13": "SPI_MISO",   # LCD_MISO + SD_MISO shared FSPI MISO
    "GPIO21": "SD_CS",
    "GPIO4": "DPAD_UP",
    "GPIO5": "DPAD_DOWN",
    "GPIO6": "DPAD_LEFT",
    "GPIO7": "DPAD_RIGHT",
    "GPIO15": "BTN_A",
    "GPIO16": "BTN_B",
    "GPIO17": "BTN_START",
    "GPIO18": "BTN_SELECT",
    "GPIO1": "JOY_X",
    "GPIO2": "JOY_Y",
    "GPIO39": "AUDIO_OUT",
    "GPIO3": "BAT_ADC",     # Battery voltage divider on perfboard (docs/module-build.md)
}

FORBIDDEN_OR_UNUSED_ESP32_PINS: Set[str] = {
    "RST",
    "GPIO46",   # Strapping pin (must remain unconnected)
    "TX(43)",   # UART0 TX debug
    "RX(44)",   # UART0 RX debug
    "GPIO42",   # PCB-only PGOOD
    "GPIO41",   # PCB-only I2S_LRCLK
    "GPIO40",   # PCB-only I2S_BCLK
    "GPIO38",   # PCB-only CHG_STAT
    "GPIO37",   # Octal PSRAM (unavailable on N16R8)
    "GPIO36",   # Octal PSRAM (unavailable on N16R8)
    "GPIO35",   # Octal PSRAM (unavailable on N16R8)
    "GPIO0",    # Strapping / onboard BOOT button
    "GPIO45",   # Strapping VDD_SPI (must NEVER be pulled high)
    "GPIO48",   # PCB-only I2C_SCL / onboard RGB LED
    "GPIO47",   # PCB-only I2C_SDA
    "GPIO20",   # USB D+
    "GPIO19",   # USB D-
}

# Exact ESP32-S3-DevKitC-1 header pin orders required by specification
ESP32_J1_ORDER: List[str] = [
    "3V3", "3V3", "RST", "4", "5", "6", "7", "15", "16", "17", "18",
    "8", "3", "46", "9", "10", "11", "12", "13", "14", "5V", "GND",
]

ESP32_J3_ORDER: List[str] = [
    "GND", "TX(43)", "RX(44)", "1", "2", "42", "41", "40", "39", "38",
    "37", "36", "35", "0", "45", "48", "47", "21", "20", "19", "GND", "GND",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Pin:
    name: str
    col: int
    row: int
    nc: bool = False
    esp32_signal: Optional[str] = None


@dataclass
class Component:
    ref: str
    board: str  # "FRONT" or "REAR"
    description: str
    body: Tuple[int, int, int, int]  # (col1, row1, col2, row2) inclusive in hole units
    pins: List[Pin] = field(default_factory=list)
    is_display_overlay: bool = False

    def pin_map(self) -> Dict[str, Pin]:
        return {p.name: p for p in self.pins}


@dataclass
class Net:
    name: str
    net_class: str  # "POWER", "GND", "DISPLAY", "CONTROL", "AUDIO", "SENSE"
    wire_color_tr: str
    description_tr: str
    nodes: List[Tuple[str, str]]  # List of (component_ref, pin_name)


# ---------------------------------------------------------------------------
# Helper constructors for components
# ---------------------------------------------------------------------------
def make_tact_switch(
    ref: str,
    description: str,
    col1: int,
    row1: int,
) -> Component:
    """Create a 6x6 mm 4-leg tact switch using a 3x2 holes span (7.62 x 5.08 mm)."""
    col2 = col1 + 2
    row2 = row1 + 1
    return Component(
        ref=ref,
        board="FRONT",
        description=description,
        body=(col1, row1, col2, row2),
        pins=[
            Pin("SIG", col1, row1, nc=False),
            Pin("GND", col2, row1, nc=False),
            Pin("NC1", col1, row2, nc=True),
            Pin("NC2", col2, row2, nc=True),
        ],
    )


def make_two_pin_passive(
    ref: str,
    board: str,
    description: str,
    col1: int,
    row1: int,
    col2: int,
    row2: int,
    p1_name: str = "P1",
    p2_name: str = "P2",
) -> Component:
    c_min, c_max = min(col1, col2), max(col1, col2)
    r_min, r_max = min(row1, row2), max(row1, row2)
    return Component(
        ref=ref,
        board=board,
        description=description,
        body=(c_min, r_min, c_max, r_max),
        pins=[
            Pin(p1_name, col1, row1, nc=False),
            Pin(p2_name, col2, row2, nc=False),
        ],
    )


# ---------------------------------------------------------------------------
# Build board components
# ---------------------------------------------------------------------------
def build_components() -> Dict[str, Component]:
    comps: List[Component] = []

    # =========================================================================
    # 1. FRONT BOARD (22 x 49 holes)
    # =========================================================================
    # Display module (50x86 mm -> cols 2..21, rows 1..34) with 1x14 female socket
    # centered at row 34 (cols 5..18), 2 mm above the module's bottom edge.
    lcd_pin_specs = [
        ("VCC", False),
        ("GND", False),
        ("CS", False),
        ("RESET", False),
        ("DC", False),
        ("SDI_MOSI", False),
        ("SCK", False),
        ("LED", False),
        ("SDO_MISO", False),
        ("T_CLK", True),
        ("T_CS", True),
        ("T_DIN", True),
        ("T_DO", True),
        ("T_IRQ", True),
    ]
    lcd_pins = [
        Pin(name=p_name, col=5 + idx, row=34, nc=is_nc)
        for idx, (p_name, is_nc) in enumerate(lcd_pin_specs)
    ]
    comps.append(
        Component(
            ref="J_LCD",
            board="FRONT",
            description="2.8\" ILI9341 TFT 1x14 Dişi Header ve Ekran Gövdesi (50x86 mm)",
            body=(2, 1, 21, 34),
            pins=lcd_pins,
            is_display_overlay=True,
        )
    )

    # Eight 6x6 mm tact switches (3x2 holes each) in lower ~40 mm (rows 36..46)
    comps.append(make_tact_switch("SW_UP", "D-Pad YUKARI (GPIO4)", 5, 36))
    comps.append(make_tact_switch("SW_LEFT", "D-Pad SOL (GPIO6)", 2, 39))
    comps.append(make_tact_switch("SW_RIGHT", "D-Pad SAĞ (GPIO7)", 8, 39))
    comps.append(make_tact_switch("SW_DOWN", "D-Pad AŞAĞI (GPIO5)", 5, 42))
    comps.append(make_tact_switch("SW_A", "Aksiyon Butonu A (GPIO15)", 18, 37))
    comps.append(make_tact_switch("SW_B", "Aksiyon Butonu B (GPIO16, A'nın sol-alt çaprazı)", 14, 40))
    comps.append(make_tact_switch("SW_SELECT", "SELECT Butonu (GPIO18)", 8, 45))
    comps.append(make_tact_switch("SW_START", "START Butonu (GPIO17)", 13, 45))

    # Inter-board 2x9 header at bottom edge of FRONT board (cols 7..15, rows 48..49)
    link_signal_names = [
        # Row 1 of header (9 pins): 3V3, GND1, and 7 display signals
        "3V3", "GND1", "LCD_CS", "LCD_RST", "LCD_DC",
        "SPI_MOSI", "SPI_SCK", "LCD_BL", "SPI_MISO",
        # Row 2 of header (9 pins): GND2 and 8 button signals
        "GND2", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
        "BTN_A", "BTN_B", "BTN_START", "BTN_SELECT",
    ]
    front_link_pins: List[Pin] = []
    for idx, sig in enumerate(link_signal_names):
        col = 7 + (idx % 9)
        row = 48 + (idx // 9)
        front_link_pins.append(Pin(name=f"P{idx + 1}_{sig}", col=col, row=row, nc=False))

    comps.append(
        Component(
            ref="J_LINK_F",
            board="FRONT",
            description="Kartlar Arası 2x9 Bağlantı Header (ÖN Kart Alt Kenar)",
            body=(7, 48, 15, 49),
            pins=front_link_pins,
        )
    )

    # =========================================================================
    # 2. REAR BOARD (18 x 37 holes)
    # =========================================================================
    # ESP32-S3-DevKitC-1 on two 1x22 female headers (J1 at col 1, J3 at col 1+ESP32_ROW_SPACING)
    # Board outline ~28x63 mm -> cols 1..11, rows 1..25; USB-C at top board edge (row 1).
    j1_col = 1
    j3_col = 1 + ESP32_ROW_SPACING
    esp32_pins: List[Pin] = []

    # Map J1 (22 pins, rows 2..23)
    for idx, raw_label in enumerate(ESP32_J1_ORDER):
        row = 2 + idx
        pin_id = f"J1_{idx + 1}_{raw_label}"
        esp_sig = f"GPIO{raw_label}" if raw_label.isdigit() else raw_label
        is_nc = (
            (idx == 1 and raw_label == "3V3")
            or (esp_sig in FORBIDDEN_OR_UNUSED_ESP32_PINS)
        )
        esp32_pins.append(Pin(name=pin_id, col=j1_col, row=row, nc=is_nc, esp32_signal=esp_sig))

    # Map J3 (22 pins, rows 2..23)
    for idx, raw_label in enumerate(ESP32_J3_ORDER):
        row = 2 + idx
        pin_id = f"J3_{idx + 1}_{raw_label}"
        esp_sig = f"GPIO{raw_label}" if raw_label.isdigit() else raw_label
        is_nc = (
            (raw_label == "GND" and idx in (0, 20))
            or (esp_sig in FORBIDDEN_OR_UNUSED_ESP32_PINS)
        )
        esp32_pins.append(Pin(name=pin_id, col=j3_col, row=row, nc=is_nc, esp32_signal=esp_sig))

    comps.append(
        Component(
            ref="ESP32",
            board="REAR",
            description="ESP32-S3-DevKitC-1 (2x 1x22 Dişi Header, USB-C Üst Kenarda)",
            body=(1, 1, max(11, j3_col), 25),
            pins=esp32_pins,
        )
    )

    # TP4056 Type-C Charger Module (25 x 16.5 mm -> 7 cols x 10 rows: cols 12..18, rows 1..10)
    # USB-C faces top board edge (row 1).
    comps.append(
        Component(
            ref="TP4056",
            board="REAR",
            description="TP4056 Type-C Korumalı Şarj Modülü (25x16.5 mm, USB-C Üst Kenarda)",
            body=(12, 1, 18, 10),
            pins=[
                Pin("IN_P", 12, 2, nc=True),
                Pin("IN_M", 18, 2, nc=True),
                Pin("OUT_M", 12, 10, nc=False),
                Pin("B_M", 14, 10, nc=False),
                Pin("B_P", 16, 10, nc=False),
                Pin("OUT_P", 18, 10, nc=False),
            ],
        )
    )

    # Slide Power Switch (3 pins, 2.54 mm pitch, at right board edge: col 18, rows 11..13)
    # Placed directly between TP4056.OUT_P (18,10) and MT3608.VIN_P (18,14) for a 1-2 hole power path.
    comps.append(
        Component(
            ref="SW_PWR",
            board="REAR",
            description="IC125B Sürgülü Açma/Kapama Anahtarı (Sağ Kenarda, 3 Pin)",
            body=(18, 11, 18, 13),
            pins=[
                Pin("IN_BAT", 18, 11, nc=False),
                Pin("OUT_VSYS", 18, 12, nc=False),
                Pin("NC_THROW", 18, 13, nc=True),
            ],
        )
    )

    # Battery Voltage Divider to GPIO3 (10k + 10k + 1uF replacement per specification)
    # Placed in rows 11..12 between SW_PWR (col 18) and ESP32 GPIO3 (col 1, row 14).
    comps.append(
        make_two_pin_passive(
            "R_BAT1", "REAR", "Pil Bölücü Üst Direnç 10k (VSYS -> GPIO3)",
            16, 11, 15, 11, "VSYS", "ADC"
        )
    )
    comps.append(
        make_two_pin_passive(
            "R_BAT2", "REAR", "Pil Bölücü Alt Direnç 10k (GPIO3 -> GND)",
            14, 11, 13, 11, "ADC", "GND"
        )
    )
    comps.append(
        make_two_pin_passive(
            "C_BAT", "REAR", "Pil Bölücü Filtre Kondansatörü 1µF (GPIO3 -> GND)",
            14, 12, 13, 12, "ADC", "GND"
        )
    )

    # Off-board Wire Pads: KSD301 50C Thermostat in series with BAT+ (placed next to TP4056.B_P)
    comps.append(
        make_two_pin_passive(
            "PAD_THERM", "REAR", "KSD301 50°C Termostat Kablo Padleri (BAT+ Seri)",
            17, 13, 16, 13, "T_IN", "T_OUT"
        )
    )

    # MT3608 Boost Converter Module (36 x 17 mm -> 7 cols x 14 rows: cols 12..18, rows 14..27)
    comps.append(
        Component(
            ref="MT3608",
            board="REAR",
            description="MT3608 5.0V Step-Up Yükseltici Modül (36x17 mm)",
            body=(12, 14, 18, 27),
            pins=[
                Pin("VIN_M", 12, 14, nc=False),
                Pin("VIN_P", 18, 14, nc=False),
                Pin("VOUT_P", 12, 27, nc=False),
                Pin("VOUT_M", 18, 27, nc=False),
            ],
        )
    )

    # SD Card 1x4 Flying Wire Landing Pads + 10k SD_CS Pull-up + 10k LCD_BL Pull-down
    # Placed at cols 9..11, rows 26..27 directly below ESP32 SPI pins (rows 18..21) and GPIO21 (row 19).
    comps.append(
        Component(
            ref="PAD_SD",
            board="REAR",
            description="Ekran Üst 1x4 SD Header Uçan Kablo Padleri (SD_CS, MOSI, MISO, SCK)",
            body=(9, 26, 10, 27),
            pins=[
                Pin("SD_CS", 9, 26, nc=False),
                Pin("SD_MOSI", 10, 26, nc=False),
                Pin("SD_MISO", 9, 27, nc=False),
                Pin("SD_SCK", 10, 27, nc=False),
            ],
        )
    )

    # 5x20 mm Fuse Holder (22 x 10 mm, 2 pins 9 intervals = 22.86 mm apart: cols 9..18, rows 28..31)
    comps.append(
        Component(
            ref="FUSE1",
            board="REAR",
            description="5x20 mm 2A Cam Sigorta Yuvası (22x10 mm, 9 Aralık)",
            body=(9, 28, 18, 31),
            pins=[
                Pin("IN", 9, 29, nc=False),
                Pin("OUT", 18, 29, nc=False),
            ],
        )
    )

    # Off-board Wire Pads: 18650 Battery Holder (BAT+, BAT-) right below FUSE1.IN
    comps.append(
        make_two_pin_passive(
            "PAD_BAT", "REAR", "18650 Pil Yuvası Kablo Lehim Padleri (BAT+ / BAT-)",
            9, 32, 10, 32, "BAT_P", "BAT_M"
        )
    )

    # SD_CS 10k Pull-up & LCD_BL 10k Pull-down
    comps.append(
        make_two_pin_passive(
            "R_SD", "REAR", "SD_CS 10k Pull-Up Direnci (SD_CS -> 3V3)",
            11, 32, 12, 32, "SD_CS", "3V3"
        )
    )
    comps.append(
        make_two_pin_passive(
            "R_BL", "REAR", "LCD_BL 10k Pull-Down Direnci (LCD_BL -> GND)",
            13, 32, 14, 32, "LCD_BL", "GND"
        )
    )

    # PAM8403 Audio Amplifier Module (21 x 18 mm -> 8 cols x 7 rows: cols 1..8, rows 26..32)
    comps.append(
        Component(
            ref="PAM8403",
            board="REAR",
            description="PAM8403 2x3W Sınıf-D Ses Amfisi (21x18 mm)",
            body=(1, 26, 8, 32),
            pins=[
                Pin("VCC", 8, 26, nc=False),
                Pin("GND_PWR", 8, 27, nc=False),
                Pin("L_IN", 8, 29, nc=False),
                Pin("GND_AUD", 8, 30, nc=False),
                Pin("R_IN", 8, 31, nc=True),
                Pin("L_P", 1, 27, nc=False),
                Pin("L_M", 1, 28, nc=False),
                Pin("R_P", 1, 30, nc=True),
                Pin("R_M", 1, 31, nc=True),
            ],
        )
    )

    # Off-board Wire Pads: Speaker (8 Ohm 1.5W) right below PAM8403 L_P / L_M
    comps.append(
        make_two_pin_passive(
            "PAD_SPK", "REAR", "Hoparlör Kablo Padleri (L+ / L-)",
            1, 33, 2, 33, "SPK_P", "SPK_M"
        )
    )

    # 2-Stage Audio PDM RC Filter (1k + 10nF x2) + 10k/1k Divider + 1uF Coupling Capacitor
    comps.append(
        make_two_pin_passive(
            "R_AUD1", "REAR", "Ses RC Filtre 1. Kademe Direnç 1k (GPIO39 -> FILT1)",
            3, 33, 4, 33, "IN", "OUT"
        )
    )
    comps.append(
        make_two_pin_passive(
            "C_AUD1", "REAR", "Ses RC Filtre 1. Kademe Kondansatör 10nF (FILT1 -> GND)",
            5, 33, 6, 33, "FILT1", "GND"
        )
    )
    comps.append(
        make_two_pin_passive(
            "R_AUD2", "REAR", "Ses RC Filtre 2. Kademe Direnç 1k (FILT1 -> FILT2)",
            3, 34, 4, 34, "IN", "OUT"
        )
    )
    comps.append(
        make_two_pin_passive(
            "C_AUD2", "REAR", "Ses RC Filtre 2. Kademe Kondansatör 10nF (FILT2 -> GND)",
            5, 34, 6, 34, "FILT2", "GND"
        )
    )
    comps.append(
        make_two_pin_passive(
            "R_AUD3", "REAR", "Ses Bölücü Üst Direnç 10k (FILT2 -> DIV)",
            7, 33, 8, 33, "FILT2", "DIV"
        )
    )
    comps.append(
        make_two_pin_passive(
            "R_AUD4", "REAR", "Ses Bölücü Alt Direnç 1k (DIV -> GND)",
            7, 34, 8, 34, "DIV", "GND"
        )
    )
    comps.append(
        make_two_pin_passive(
            "C_AUD3", "REAR", "Ses Amfi Giriş Kuplaj Kondansatörü 1µF (DIV -> PAM_LIN)",
            9, 33, 10, 33, "DIV", "LIN"
        )
    )

    # Optional 1x5 Joystick Header (3V3, GND, X, Y, SW not used)
    comps.append(
        Component(
            ref="J_JOY",
            board="REAR",
            description="İsteğe Bağlı Analog Joystick 1x5 Header (3V3, GND, X, Y, SW=NC)",
            body=(12, 34, 16, 34),
            pins=[
                Pin("3V3", 12, 34, nc=False),
                Pin("GND", 13, 34, nc=False),
                Pin("X", 14, 34, nc=False),
                Pin("Y", 15, 34, nc=False),
                Pin("SW", 16, 34, nc=True),
            ],
        )
    )

    # Matching 2x9 Inter-board Header at bottom edge of REAR board (cols 1..9, rows 36..37)
    rear_link_pins: List[Pin] = []
    for idx, sig in enumerate(link_signal_names):
        col = 1 + (idx % 9)
        row = 36 + (idx // 9)
        rear_link_pins.append(Pin(name=f"P{idx + 1}_{sig}", col=col, row=row, nc=False))

    comps.append(
        Component(
            ref="J_LINK_R",
            board="REAR",
            description="Kartlar Arası 2x9 Bağlantı Header Karşılığı (ARKA Kart Alt Kenar)",
            body=(1, 36, 9, 37),
            pins=rear_link_pins,
        )
    )

    return {c.ref: c for c in comps}


# ---------------------------------------------------------------------------
# Build complete Netlist
# ---------------------------------------------------------------------------
def build_nets() -> List[Net]:
    return [
        # --- POWER CHAIN NETS ---
        Net(
            name="BAT_RAW_P",
            net_class="POWER",
            wire_color_tr="Kırmızı (Kalın 22-24 AWG)",
            description_tr="18650 pil (+) çıkışından 2A cam sigorta girişine",
            nodes=[("PAD_BAT", "BAT_P"), ("FUSE1", "IN")],
        ),
        Net(
            name="BAT_FUSED",
            net_class="POWER",
            wire_color_tr="Kırmızı (Kalın 22-24 AWG)",
            description_tr="Sigorta çıkışından 50°C KSD301 termostat girişine",
            nodes=[("FUSE1", "OUT"), ("PAD_THERM", "T_IN")],
        ),
        Net(
            name="BAT_P",
            net_class="POWER",
            wire_color_tr="Kırmızı (Kalın 22-24 AWG)",
            description_tr="Termostat çıkışından TP4056 B+ pil girişine",
            nodes=[("PAD_THERM", "T_OUT"), ("TP4056", "B_P")],
        ),
        Net(
            name="BAT_M",
            net_class="GND",
            wire_color_tr="Siyah (Kalın 22-24 AWG)",
            description_tr="18650 pil (-) çıkışından TP4056 B- koruma girişine",
            nodes=[("PAD_BAT", "BAT_M"), ("TP4056", "B_M")],
        ),
        Net(
            name="BAT_PROT_P",
            net_class="POWER",
            wire_color_tr="Turuncu (Kalın)",
            description_tr="TP4056 korumalı OUT+ çıkışından güç anahtarı girişine",
            nodes=[("TP4056", "OUT_P"), ("SW_PWR", "IN_BAT")],
        ),
        Net(
            name="VSYS",
            net_class="POWER",
            wire_color_tr="Turuncu",
            description_tr="Anahtarlanmış pil hattı (MT3608 VIN+ ve pil bölücü üst ucu)",
            nodes=[("SW_PWR", "OUT_VSYS"), ("MT3608", "VIN_P"), ("R_BAT1", "VSYS")],
        ),
        Net(
            name="5V",
            net_class="POWER",
            wire_color_tr="Kırmızı",
            description_tr="MT3608 5.0V çıkışı -> PAM8403 VCC ve ESP32 5V pini",
            nodes=[("MT3608", "VOUT_P"), ("PAM8403", "VCC"), ("ESP32", "J1_21_5V")],
        ),
        Net(
            name="3V3",
            net_class="POWER",
            wire_color_tr="Kırmızı/Beyaz",
            description_tr="ESP32 3.3V regüle çıkışı -> Ekran VCC, SD pull-up ve Joystick",
            nodes=[
                ("ESP32", "J1_1_3V3"),
                ("R_SD", "3V3"),
                ("J_JOY", "3V3"),
                ("J_LINK_R", "P1_3V3"),
                ("J_LINK_F", "P1_3V3"),
                ("J_LCD", "VCC"),
            ],
        ),
        Net(
            name="GND",
            net_class="GND",
            wire_color_tr="Siyah",
            description_tr="Ortak şase (TP4056 OUT-, MT3608, ESP32, Amfi, Filtreler, Ekran ve Butonlar)",
            nodes=[
                # Rear board GND nodes
                ("TP4056", "OUT_M"),
                ("R_BAT2", "GND"),
                ("C_BAT", "GND"),
                ("MT3608", "VIN_M"),
                ("MT3608", "VOUT_M"),
                ("ESP32", "J1_22_GND"),
                ("ESP32", "J3_22_GND"),
                ("PAM8403", "GND_PWR"),
                ("PAM8403", "GND_AUD"),
                ("R_BL", "GND"),
                ("C_AUD1", "GND"),
                ("C_AUD2", "GND"),
                ("R_AUD4", "GND"),
                ("J_JOY", "GND"),
                ("J_LINK_R", "P2_GND1"),
                ("J_LINK_R", "P10_GND2"),
                # Front board GND nodes
                ("J_LINK_F", "P2_GND1"),
                ("J_LINK_F", "P10_GND2"),
                ("J_LCD", "GND"),
                ("SW_UP", "GND"),
                ("SW_DOWN", "GND"),
                ("SW_LEFT", "GND"),
                ("SW_RIGHT", "GND"),
                ("SW_A", "GND"),
                ("SW_B", "GND"),
                ("SW_START", "GND"),
                ("SW_SELECT", "GND"),
            ],
        ),

        # --- DISPLAY & SHARED SPI NETS ---
        Net(
            name="LCD_CS",
            net_class="DISPLAY",
            wire_color_tr="Mavi",
            description_tr="ILI9341 Chip Select (GPIO10)",
            nodes=[
                ("ESP32", "J1_16_10"),
                ("J_LINK_R", "P3_LCD_CS"),
                ("J_LINK_F", "P3_LCD_CS"),
                ("J_LCD", "CS"),
            ],
        ),
        Net(
            name="LCD_RST",
            net_class="DISPLAY",
            wire_color_tr="Beyaz",
            description_tr="ILI9341 Reset (GPIO8)",
            nodes=[
                ("ESP32", "J1_12_8"),
                ("J_LINK_R", "P4_LCD_RST"),
                ("J_LINK_F", "P4_LCD_RST"),
                ("J_LCD", "RESET"),
            ],
        ),
        Net(
            name="LCD_DC",
            net_class="DISPLAY",
            wire_color_tr="Yeşil",
            description_tr="ILI9341 Data/Command (GPIO9)",
            nodes=[
                ("ESP32", "J1_15_9"),
                ("J_LINK_R", "P5_LCD_DC"),
                ("J_LINK_F", "P5_LCD_DC"),
                ("J_LCD", "DC"),
            ],
        ),
        Net(
            name="SPI_MOSI",
            net_class="DISPLAY",
            wire_color_tr="Sarı",
            description_tr="Ortak SPI MOSI: LCD SDI + microSD SD_MOSI (GPIO11)",
            nodes=[
                ("ESP32", "J1_17_11"),
                ("PAD_SD", "SD_MOSI"),
                ("J_LINK_R", "P6_SPI_MOSI"),
                ("J_LINK_F", "P6_SPI_MOSI"),
                ("J_LCD", "SDI_MOSI"),
            ],
        ),
        Net(
            name="SPI_SCK",
            net_class="DISPLAY",
            wire_color_tr="Mor",
            description_tr="Ortak SPI SCK: LCD SCK + microSD SD_SCK (GPIO12)",
            nodes=[
                ("ESP32", "J1_18_12"),
                ("PAD_SD", "SD_SCK"),
                ("J_LINK_R", "P7_SPI_SCK"),
                ("J_LINK_F", "P7_SPI_SCK"),
                ("J_LCD", "SCK"),
            ],
        ),
        Net(
            name="LCD_BL",
            net_class="DISPLAY",
            wire_color_tr="Kahverengi",
            description_tr="LCD Arka Işık PWM (GPIO14) + Pull-Down",
            nodes=[
                ("ESP32", "J1_20_14"),
                ("R_BL", "LCD_BL"),
                ("J_LINK_R", "P8_LCD_BL"),
                ("J_LINK_F", "P8_LCD_BL"),
                ("J_LCD", "LED"),
            ],
        ),
        Net(
            name="SPI_MISO",
            net_class="DISPLAY",
            wire_color_tr="Gri",
            description_tr="Ortak SPI MISO: microSD SD_MISO + LCD SDO (GPIO13)",
            nodes=[
                ("ESP32", "J1_19_13"),
                ("PAD_SD", "SD_MISO"),
                ("J_LINK_R", "P9_SPI_MISO"),
                ("J_LINK_F", "P9_SPI_MISO"),
                ("J_LCD", "SDO_MISO"),
            ],
        ),
        Net(
            name="SD_CS",
            net_class="DISPLAY",
            wire_color_tr="Turkuaz",
            description_tr="microSD Chip Select (GPIO21) + 10k Pull-Up",
            nodes=[
                ("ESP32", "J3_18_21"),
                ("PAD_SD", "SD_CS"),
                ("R_SD", "SD_CS"),
            ],
        ),

        # --- BUTTONS & JOYSTICK NETS ---
        Net(
            name="DPAD_UP",
            net_class="CONTROL",
            wire_color_tr="Yeşil",
            description_tr="Yön Tuşu YUKARI (GPIO4, dahili pull-up)",
            nodes=[
                ("SW_UP", "SIG"),
                ("J_LINK_F", "P11_DPAD_UP"),
                ("J_LINK_R", "P11_DPAD_UP"),
                ("ESP32", "J1_4_4"),
            ],
        ),
        Net(
            name="DPAD_DOWN",
            net_class="CONTROL",
            wire_color_tr="Sarı",
            description_tr="Yön Tuşu AŞAĞI (GPIO5, dahili pull-up)",
            nodes=[
                ("SW_DOWN", "SIG"),
                ("J_LINK_F", "P12_DPAD_DOWN"),
                ("J_LINK_R", "P12_DPAD_DOWN"),
                ("ESP32", "J1_5_5"),
            ],
        ),
        Net(
            name="DPAD_LEFT",
            net_class="CONTROL",
            wire_color_tr="Mavi",
            description_tr="Yön Tuşu SOL (GPIO6, dahili pull-up)",
            nodes=[
                ("SW_LEFT", "SIG"),
                ("J_LINK_F", "P13_DPAD_LEFT"),
                ("J_LINK_R", "P13_DPAD_LEFT"),
                ("ESP32", "J1_6_6"),
            ],
        ),
        Net(
            name="DPAD_RIGHT",
            net_class="CONTROL",
            wire_color_tr="Beyaz",
            description_tr="Yön Tuşu SAĞ (GPIO7, dahili pull-up)",
            nodes=[
                ("SW_RIGHT", "SIG"),
                ("J_LINK_F", "P14_DPAD_RIGHT"),
                ("J_LINK_R", "P14_DPAD_RIGHT"),
                ("ESP32", "J1_7_7"),
            ],
        ),
        Net(
            name="BTN_A",
            net_class="CONTROL",
            wire_color_tr="Mor",
            description_tr="Aksiyon Butonu A (GPIO15, dahili pull-up)",
            nodes=[
                ("SW_A", "SIG"),
                ("J_LINK_F", "P15_BTN_A"),
                ("J_LINK_R", "P15_BTN_A"),
                ("ESP32", "J1_8_15"),
            ],
        ),
        Net(
            name="BTN_B",
            net_class="CONTROL",
            wire_color_tr="Kahverengi",
            description_tr="Aksiyon Butonu B (GPIO16, dahili pull-up)",
            nodes=[
                ("SW_B", "SIG"),
                ("J_LINK_F", "P16_BTN_B"),
                ("J_LINK_R", "P16_BTN_B"),
                ("ESP32", "J1_9_16"),
            ],
        ),
        Net(
            name="BTN_START",
            net_class="CONTROL",
            wire_color_tr="Gri",
            description_tr="START Butonu (GPIO17, dahili pull-up)",
            nodes=[
                ("SW_START", "SIG"),
                ("J_LINK_F", "P17_BTN_START"),
                ("J_LINK_R", "P17_BTN_START"),
                ("ESP32", "J1_10_17"),
            ],
        ),
        Net(
            name="BTN_SELECT",
            net_class="CONTROL",
            wire_color_tr="Turuncu",
            description_tr="SELECT Butonu (GPIO18, dahili pull-up)",
            nodes=[
                ("SW_SELECT", "SIG"),
                ("J_LINK_F", "P18_BTN_SELECT"),
                ("J_LINK_R", "P18_BTN_SELECT"),
                ("ESP32", "J1_11_18"),
            ],
        ),
        Net(
            name="JOY_X",
            net_class="CONTROL",
            wire_color_tr="Yeşil/Beyaz",
            description_tr="İsteğe Bağlı Analog Joystick X Ekseni (GPIO1 / ADC1_CH0)",
            nodes=[("ESP32", "J3_4_1"), ("J_JOY", "X")],
        ),
        Net(
            name="JOY_Y",
            net_class="CONTROL",
            wire_color_tr="Mavi/Beyaz",
            description_tr="İsteğe Bağlı Analog Joystick Y Ekseni (GPIO2 / ADC1_CH1)",
            nodes=[("ESP32", "J3_5_2"), ("J_JOY", "Y")],
        ),

        # --- AUDIO CHAIN NETS ---
        Net(
            name="AUDIO_OUT",
            net_class="AUDIO",
            wire_color_tr="Sarı",
            description_tr="ESP32 PDM Ses Çıkışı (GPIO39) -> 1. RC Filtre Girişi",
            nodes=[("ESP32", "J3_9_39"), ("R_AUD1", "IN")],
        ),
        Net(
            name="AUD_FILT1",
            net_class="AUDIO",
            wire_color_tr="Sarı",
            description_tr="Ses RC Filtre 1. Kademe Ara Düğümü (1k + 10nF)",
            nodes=[("R_AUD1", "OUT"), ("C_AUD1", "FILT1"), ("R_AUD2", "IN")],
        ),
        Net(
            name="AUD_FILT2",
            net_class="AUDIO",
            wire_color_tr="Sarı",
            description_tr="Ses RC Filtre 2. Kademe Çıkışı -> 10k/1k Bölücü Girişi",
            nodes=[("R_AUD2", "OUT"), ("C_AUD2", "FILT2"), ("R_AUD3", "FILT2")],
        ),
        Net(
            name="AUD_DIV",
            net_class="AUDIO",
            wire_color_tr="Turuncu",
            description_tr="10k/1k Ses Gerilim Bölücü Çıkışı -> 1µF Kuplaj Kondansatörü",
            nodes=[("R_AUD3", "DIV"), ("R_AUD4", "DIV"), ("C_AUD3", "DIV")],
        ),
        Net(
            name="PAM_LIN",
            net_class="AUDIO",
            wire_color_tr="Turuncu",
            description_tr="1µF Kuplaj Kondansatörü Çıkışı -> PAM8403 Sol Giriş (L_IN)",
            nodes=[("C_AUD3", "LIN"), ("PAM8403", "L_IN")],
        ),
        Net(
            name="SPK_P",
            net_class="AUDIO",
            wire_color_tr="Kırmızı (Hoparlör)",
            description_tr="PAM8403 L+ Çıkışından Hoparlör (+) Padine (Asla GND'ye bağlanmaz)",
            nodes=[("PAM8403", "L_P"), ("PAD_SPK", "SPK_P")],
        ),
        Net(
            name="SPK_M",
            net_class="AUDIO",
            wire_color_tr="Siyah (Hoparlör)",
            description_tr="PAM8403 L- Çıkışından Hoparlör (-) Padine (Asla GND'ye bağlanmaz)",
            nodes=[("PAM8403", "L_M"), ("PAD_SPK", "SPK_M")],
        ),

        # --- BATTERY SENSE NET ---
        Net(
            name="BAT_ADC",
            net_class="SENSE",
            wire_color_tr="Mor",
            description_tr="Pil Gerilim Bölücü Orta Noktası (10k/10k + 1µF) -> GPIO3",
            nodes=[
                ("R_BAT1", "ADC"),
                ("R_BAT2", "ADC"),
                ("C_BAT", "ADC"),
                ("ESP32", "J1_13_3"),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# Self-Checks
# ---------------------------------------------------------------------------
def rects_overlap(
    a: Tuple[int, int, int, int],
    b: Tuple[int, int, int, int],
) -> bool:
    ac1, ar1, ac2, ar2 = a
    bc1, br1, bc2, br2 = b
    return not (ac2 < bc1 or bc2 < ac1 or ar2 < br1 or br2 < ar1)


def run_self_checks(
    components: Dict[str, Component],
    nets: List[Net],
) -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    passed: List[str] = []

    board_limits = {
        "FRONT": (FRONT_COLS, FRONT_ROWS),
        "REAR": (REAR_COLS, REAR_ROWS),
    }

    # 1. Check board bounds for all component bodies and pins
    bounds_ok = True
    for comp in components.values():
        max_col, max_row = board_limits[comp.board]
        c1, r1, c2, r2 = comp.body
        if not (1 <= c1 <= c2 <= max_col and 1 <= r1 <= r2 <= max_row):
            errors.append(
                f"[BOUNDS] Component {comp.ref} body {comp.body} outside {comp.board} grid (1..{max_col}, 1..{max_row})"
            )
            bounds_ok = False
        for p in comp.pins:
            if not (1 <= p.col <= max_col and 1 <= p.row <= max_row):
                errors.append(
                    f"[BOUNDS] Pin {comp.ref}.{p.name} at ({p.col},{p.row}) outside {comp.board} grid"
                )
                bounds_ok = False
            if not (c1 <= p.col <= c2 and r1 <= p.row <= r2):
                errors.append(
                    f"[BOUNDS] Pin {comp.ref}.{p.name} at ({p.col},{p.row}) outside its own body {comp.body}"
                )
                bounds_ok = False
    if bounds_ok:
        passed.append(
            f"Board boundary check passed: all FRONT ({FRONT_COLS}x{FRONT_ROWS}) and REAR ({REAR_COLS}x{REAR_ROWS}) bodies and pins inside grid."
        )

    # 2. Check no two pins on the same hole on the same board
    hole_usage: Dict[Tuple[str, int, int], str] = {}
    holes_ok = True
    for comp in components.values():
        for p in comp.pins:
            key = (comp.board, p.col, p.row)
            label = f"{comp.ref}.{p.name}"
            if key in hole_usage:
                errors.append(
                    f"[HOLE_COLLISION] {comp.board} ({p.col},{p.row}) shared by {hole_usage[key]} and {label}"
                )
                holes_ok = False
            else:
                hole_usage[key] = label
    if holes_ok:
        passed.append(f"Unique pin-hole check passed: {len(hole_usage)} pins placed with 0 collisions.")

    # 3. Check no component bodies overlapping on the same board face
    overlap_ok = True
    comp_list = list(components.values())
    for i in range(len(comp_list)):
        for j in range(i + 1, len(comp_list)):
            ca, cb = comp_list[i], comp_list[j]
            if ca.board != cb.board:
                continue
            if rects_overlap(ca.body, cb.body):
                errors.append(
                    f"[BODY_OVERLAP] {ca.board}: {ca.ref} {ca.body} overlaps {cb.ref} {cb.body}"
                )
                overlap_ok = False
    if overlap_ok:
        passed.append("Component body overlap check passed: 0 overlapping bodies on FRONT and REAR.")

    # 4. Check display mounting holes clearance on FRONT board
    mount_ok = True
    for mh_col, mh_row in LCD_MOUNTING_HOLES_GRID:
        if ("FRONT", mh_col, mh_row) in hole_usage:
            errors.append(
                f"[DISPLAY_MOUNT] Pin {hole_usage[('FRONT', mh_col, mh_row)]} placed on display mounting hole ({mh_col},{mh_row})"
            )
            mount_ok = False
        for comp in components.values():
            if comp.board == "FRONT" and not comp.is_display_overlay:
                c1, r1, c2, r2 = comp.body
                if c1 <= mh_col <= c2 and r1 <= mh_row <= r2:
                    errors.append(
                        f"[DISPLAY_MOUNT] Component {comp.ref} body {comp.body} covers display mounting hole ({mh_col},{mh_row})"
                    )
                    mount_ok = False
    if mount_ok:
        passed.append(
            f"Display mounting holes check passed: {LCD_MOUNTING_HOLES_GRID} clear of all pins and non-display components."
        )

    # 5. Check ESP32-S3-DevKitC-1 exact pin order on J1 and J3
    esp_comp = components.get("ESP32")
    esp_order_ok = True
    if esp_comp is None:
        errors.append("[ESP32_ORDER] Missing ESP32 component")
        esp_order_ok = False
    else:
        j1_pins = [p for p in esp_comp.pins if p.name.startswith("J1_")]
        j3_pins = [p for p in esp_comp.pins if p.name.startswith("J3_")]
        j1_actual = [p.name.split("_", 2)[2] for p in j1_pins]
        j3_actual = [p.name.split("_", 2)[2] for p in j3_pins]
        if j1_actual != ESP32_J1_ORDER:
            errors.append(f"[ESP32_ORDER] J1 pin order mismatch: {j1_actual} != {ESP32_J1_ORDER}")
            esp_order_ok = False
        if j3_actual != ESP32_J3_ORDER:
            errors.append(f"[ESP32_ORDER] J3 pin order mismatch: {j3_actual} != {ESP32_J3_ORDER}")
            esp_order_ok = False
    if esp_order_ok:
        passed.append("ESP32-S3-DevKitC-1 J1 (22 pins) and J3 (22 pins) header order verified.")

    # 6. Check netlist completeness: every net >= 2 pins, every non-NC pin in exactly 1 net,
    #    no NC pin in any net.
    net_membership: Dict[Tuple[str, str], List[str]] = {}
    net_size_ok = True
    for net in nets:
        if len(net.nodes) < 2:
            errors.append(f"[NET_SIZE] Net {net.name} has fewer than 2 pins ({len(net.nodes)})")
            net_size_ok = False
        for ref, pin_name in net.nodes:
            if ref not in components:
                errors.append(f"[NET_REF] Net {net.name} references unknown component {ref}")
                net_size_ok = False
                continue
            pmap = components[ref].pin_map()
            if pin_name not in pmap:
                errors.append(f"[NET_PIN] Net {net.name} references unknown pin {ref}.{pin_name}")
                net_size_ok = False
                continue
            net_membership.setdefault((ref, pin_name), []).append(net.name)

    pin_net_ok = True
    for comp in components.values():
        for p in comp.pins:
            assigned_nets = net_membership.get((comp.ref, p.name), [])
            if p.nc:
                if assigned_nets:
                    errors.append(
                        f"[NC_PIN_CONNECTED] Pin {comp.ref}.{p.name} is marked NC but connected to {assigned_nets}"
                    )
                    pin_net_ok = False
            else:
                if len(assigned_nets) != 1:
                    errors.append(
                        f"[PIN_NET_COUNT] Non-NC pin {comp.ref}.{p.name} belongs to {len(assigned_nets)} nets: {assigned_nets}"
                    )
                    pin_net_ok = False
    if net_size_ok and pin_net_ok:
        passed.append(
            f"Netlist integrity check passed: {len(nets)} nets (all >=2 pins), all non-NC pins in exactly 1 net."
        )

    # 7. Cross-check every GPIO used against docs/pinout.md and ensure no GPIO is used twice
    gpio_used_by_net: Dict[str, str] = {}
    gpio_ok = True
    for net in nets:
        for ref, pin_name in net.nodes:
            if ref != "ESP32":
                continue
            p = components["ESP32"].pin_map()[pin_name]
            sig = p.esp32_signal or ""
            if sig in ("3V3", "5V", "GND"):
                continue
            if sig in FORBIDDEN_OR_UNUSED_ESP32_PINS:
                errors.append(
                    f"[GPIO_FORBIDDEN] Net {net.name} uses forbidden/reserved ESP32 pin {sig} ({pin_name})"
                )
                gpio_ok = False
                continue
            if sig not in PINOUT_GPIO_MAP:
                errors.append(
                    f"[GPIO_UNKNOWN] Net {net.name} uses ESP32 pin {sig} not present in docs/pinout.md"
                )
                gpio_ok = False
                continue
            expected_net = PINOUT_GPIO_MAP[sig]
            if expected_net != net.name:
                errors.append(
                    f"[GPIO_MISMATCH] ESP32 {sig} connected to net '{net.name}', expected '{expected_net}' per docs/pinout.md"
                )
                gpio_ok = False
            if sig in gpio_used_by_net:
                errors.append(
                    f"[GPIO_DUPLICATE] ESP32 {sig} used twice: in '{gpio_used_by_net[sig]}' and '{net.name}'"
                )
                gpio_ok = False
            else:
                gpio_used_by_net[sig] = net.name

    for expected_gpio, expected_net in PINOUT_GPIO_MAP.items():
        if expected_gpio not in gpio_used_by_net:
            errors.append(
                f"[GPIO_MISSING] GPIO {expected_gpio} ({expected_net}) from docs/pinout.md is not connected"
            )
            gpio_ok = False

    if gpio_ok:
        passed.append(
            f"GPIO cross-check against docs/pinout.md passed: {len(gpio_used_by_net)}/{len(PINOUT_GPIO_MAP)} GPIOs matched, 0 duplicates."
        )

    return (len(errors) == 0), passed, errors


# ---------------------------------------------------------------------------
# SVG Rendering
# ---------------------------------------------------------------------------
NET_CLASS_COLORS: Dict[str, str] = {
    "POWER": "#d32f2f",    # Red
    "GND": "#111111",      # Black
    "DISPLAY": "#1565c0",  # Blue
    "CONTROL": "#2e7d32",  # Green
    "AUDIO": "#ef6c00",    # Orange
    "SENSE": "#7b1fa2",    # Purple
    "NC": "#9e9e9e",       # Grey
}


def render_board_svg(
    board_name: str,
    title_tr: str,
    subtitle_tr: str,
    width_mm: float,
    height_mm: float,
    cols: int,
    rows: int,
    components: Dict[str, Component],
    nets: List[Net],
    out_path: Path,
) -> None:
    scale = 20.0  # pixels per hole pitch (2.54 mm)
    pad_left = 70.0
    pad_top = 80.0
    pad_right = 240.0
    pad_bottom = 60.0

    board_w_px = (cols + 1) * scale
    board_h_px = (rows + 1) * scale
    svg_w = int(pad_left + board_w_px + pad_right)
    svg_h = int(pad_top + board_h_px + pad_bottom)

    # Map (ref, pin_name) -> Net
    pin_to_net: Dict[Tuple[str, str], Net] = {}
    for net in nets:
        for ref, pin_name in net.nodes:
            pin_to_net[(ref, pin_name)] = net

    def hole_xy(col: int, row: int) -> Tuple[float, float]:
        return (pad_left + col * scale, pad_top + row * scale)

    lines: List[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}" font-family="Consolas, monospace">'
    )
    lines.append(f'<rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="#f8f9fa"/>')

    # Header text
    lines.append(
        f'<text x="{pad_left}" y="28" font-size="16" font-weight="bold" fill="#1a1a1a">'
        f'{html.escape(title_tr)}</text>'
    )
    lines.append(
        f'<text x="{pad_left}" y="48" font-size="11" fill="#444444">'
        f'{html.escape(subtitle_tr)}</text>'
    )

    # Perfboard phenolic base rectangle
    lines.append(
        f'<rect x="{pad_left}" y="{pad_top}" width="{board_w_px}" height="{board_h_px}" '
        f'rx="6" ry="6" fill="#f3e5ab" stroke="#8d6e63" stroke-width="2.5"/>'
    )

    # Column and row labels + copper pads + holes
    for c in range(1, cols + 1):
        cx, _ = hole_xy(c, 1)
        lines.append(
            f'<text x="{cx}" y="{pad_top - 8}" font-size="9" text-anchor="middle" fill="#333">{c}</text>'
        )
        lines.append(
            f'<text x="{cx}" y="{pad_top + board_h_px + 14}" font-size="9" text-anchor="middle" fill="#333">{c}</text>'
        )

    for r in range(1, rows + 1):
        _, ry = hole_xy(1, r)
        lines.append(
            f'<text x="{pad_left - 10}" y="{ry + 3}" font-size="9" text-anchor="end" fill="#333">{r}</text>'
        )
        lines.append(
            f'<text x="{pad_left + board_w_px + 10}" y="{ry + 3}" font-size="9" text-anchor="start" fill="#333">{r}</text>'
        )

    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            hx, hy = hole_xy(c, r)
            lines.append(
                f'<circle cx="{hx}" cy="{hy}" r="4.2" fill="#d4a359" opacity="0.45"/>'
            )
            lines.append(
                f'<circle cx="{hx}" cy="{hy}" r="1.8" fill="#ffffff" stroke="#8c6239" stroke-width="0.6"/>'
            )

    # Draw component bodies (display overlay first so socket remains clear)
    board_comps = [c for c in components.values() if c.board == board_name]
    board_comps.sort(key=lambda c: (0 if c.is_display_overlay else 1, c.ref))

    for comp in board_comps:
        c1, r1, c2, r2 = comp.body
        x1, y1 = hole_xy(c1, r1)
        x2, y2 = hole_xy(c2, r2)
        bx = x1 - scale * 0.42
        by = y1 - scale * 0.42
        bw = (x2 - x1) + scale * 0.84
        bh = (y2 - y1) + scale * 0.84

        if comp.is_display_overlay:
            # Display module outline (50x86 mm) + socket strip + SD flying wire header annotation
            lines.append(
                f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" '
                f'fill="#e3f2fd" fill-opacity="0.38" stroke="#1565c0" stroke-width="1.8" stroke-dasharray="6,3"/>'
            )
            lines.append(
                f'<rect x="{bx + 18}" y="{by + 28}" width="{bw - 36}" height="{bh - 85}" '
                f'fill="#bbdefb" fill-opacity="0.35" stroke="#1976d2" stroke-width="1"/>'
            )
            lines.append(
                f'<text x="{bx + bw / 2}" y="{by + bh / 2 - 10}" font-size="13" font-weight="bold" '
                f'text-anchor="middle" fill="#0d47a1">2.8" ILI9341 TFT EKRAN MODÜLÜ (50x86 mm)</text>'
            )
            lines.append(
                f'<text x="{bx + bw / 2}" y="{by + bh / 2 + 10}" font-size="10" '
                f'text-anchor="middle" fill="#0d47a1">Alt 1x14 Dişi Soket: Satır 34, Sütun 5..18</text>'
            )
            sd_x = bx + bw * 0.52
            sd_y = by + 4
            lines.append(
                f'<rect x="{sd_x}" y="{sd_y}" width="110" height="16" fill="#fff9c4" stroke="#f57f17" stroke-width="1.2"/>'
            )
            lines.append(
                f'<text x="{sd_x + 55}" y="{sd_y + 11}" font-size="8.5" text-anchor="middle" fill="#e65100">'
                f'Üst 1x4 SD (4 Uçan Tel)</text>'
            )
            sx1, sy1 = hole_xy(5, 34)
            sx2, _ = hole_xy(18, 34)
            lines.append(
                f'<rect x="{sx1 - 8}" y="{sy1 - 8}" width="{(sx2 - sx1) + 16}" height="16" '
                f'fill="#ffffff" fill-opacity="0.7" stroke="#0d47a1" stroke-width="1.4"/>'
            )
            lines.append(
                f'<text x="{(sx1 + sx2) / 2}" y="{sy1 - 11}" font-size="9.5" font-weight="bold" '
                f'text-anchor="middle" fill="#0d47a1">J_LCD (1x14 Dişi Header)</text>'
            )
        else:
            lines.append(
                f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="3" ry="3" '
                f'fill="#ffffff" fill-opacity="0.72" stroke="#37474f" stroke-width="1.5"/>'
            )
            label_x = bx + bw / 2
            label_y = by + bh / 2 + 3
            lines.append(
                f'<text x="{label_x}" y="{label_y}" font-size="8.5" font-weight="bold" '
                f'text-anchor="middle" fill="#263238">{html.escape(comp.ref)}</text>'
            )

    # Mark display mounting holes on FRONT board
    if board_name == "FRONT":
        for (mh_col, mh_row), (mm_x, mm_y) in zip(LCD_MOUNTING_HOLES_GRID, LCD_MOUNTING_HOLES_MM):
            mx, my = hole_xy(mh_col, mh_row)
            lines.append(
                f'<circle cx="{mx}" cy="{my}" r="7.5" fill="none" stroke="#c62828" stroke-width="2" stroke-dasharray="3,2"/>'
            )
            lines.append(
                f'<line x1="{mx - 8}" y1="{my}" x2="{mx + 8}" y2="{my}" stroke="#c62828" stroke-width="1.2"/>'
            )
            lines.append(
                f'<line x1="{mx}" y1="{my - 8}" x2="{mx}" y2="{my + 8}" stroke="#c62828" stroke-width="1.2"/>'
            )
            lines.append(
                f'<text x="{mx}" y="{my - 10}" font-size="8" font-weight="bold" text-anchor="middle" fill="#b71c1c">'
                f'MONTAJ ({mm_x:.0f},{mm_y:.1f}mm)</text>'
            )

    # Draw component pins colored by net class
    for comp in board_comps:
        for p in comp.pins:
            px, py = hole_xy(p.col, p.row)
            net = pin_to_net.get((comp.ref, p.name))
            nclass = "NC" if p.nc or net is None else net.net_class
            color = NET_CLASS_COLORS[nclass]
            lines.append(
                f'<circle cx="{px}" cy="{py}" r="5.0" fill="{color}" stroke="#ffffff" stroke-width="1.0"/>'
            )
            short_pin = p.name.split("_")[-1] if len(p.name) > 5 else p.name
            lines.append(
                f'<text x="{px}" y="{py + 2.2}" font-size="5.5" text-anchor="middle" fill="#ffffff">'
                f'{html.escape(short_pin[:4])}</text>'
            )

    # Draw Legend on right side
    leg_x = pad_left + board_w_px + 30
    leg_y = pad_top + 10
    lines.append(
        f'<rect x="{leg_x}" y="{leg_y}" width="195" height="230" rx="5" ry="5" '
        f'fill="#ffffff" stroke="#b0bec5" stroke-width="1.2"/>'
    )
    lines.append(
        f'<text x="{leg_x + 12}" y="{leg_y + 22}" font-size="11" font-weight="bold" fill="#263238">'
        f'RENK LEJANDI (HAT SINIFI)</text>'
    )
    legend_items = [
        ("POWER", "Güç (5V, 3V3, BAT+, VSYS)"),
        ("GND", "Şase (GND, BAT-)"),
        ("DISPLAY", "Ekran & SPI Sinyalleri"),
        ("CONTROL", "Butonlar & Joystick"),
        ("AUDIO", "Ses & RC Filtre Zinciri"),
        ("SENSE", "Pil Ölçümü (BAT_ADC)"),
        ("NC", "Bağlı Değil (NC)"),
    ]
    for idx, (cls_key, label_tr) in enumerate(legend_items):
        iy = leg_y + 44 + idx * 24
        c_hex = NET_CLASS_COLORS[cls_key]
        lines.append(f'<circle cx="{leg_x + 20}" cy="{iy}" r="6" fill="{c_hex}"/>')
        lines.append(
            f'<text x="{leg_x + 34}" y="{iy + 4}" font-size="9.5" fill="#333333">'
            f'{html.escape(label_tr)}</text>'
        )

    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Generate Turkish wiring.md
# ---------------------------------------------------------------------------
def generate_wiring_md(
    components: Dict[str, Component],
    nets: List[Net],
    out_path: Path,
) -> None:
    lines: List[str] = []
    lines.append("# Delikli Pertinaks Noktadan Noktaya Kablolama ve Lehimleme Rehberi")
    lines.append("")
    lines.append(
        "Bu belge `layout.py` tarafından otomatik üretilmiştir. Bakır yol çizimi yerine "
        "tüm bağlantılar noktadan noktaya (point-to-point) izole tellerle yapılır."
    )
    lines.append("")
    lines.append("## 1. Önemli Güvenlik ve Lehimleme Sırası (Önce Güç Zinciri!)")
    lines.append("")
    lines.append(
        "> **KRİTİK UYARI:** `ESP32-S3` geliştirme kartını dişi header yuvalarına **kesinlikle takmayın!** "
        "`MT3608` yükseltici modül fabrikadan 12 V – 28 V aralığında ayarlı gelebilir; ayarlanmadan "
        "`ESP32-S3` veya `PAM8403` bağlanırsa kartlar anında yanar."
    )
    lines.append("")
    lines.append("1. **Güç Zincirini Lehimleyin (`ARKA` Kart):**")
    lines.append(
        "   - `FUSE1` (5x20 mm sigorta yuvası), `PAD_BAT` (18650 pil yuvası uçları), `PAD_THERM` "
        "(pile bantlanan 50 °C KSD301 termostat uçları), `TP4056` şarj modülü, `SW_PWR` açma/kapama "
        "anahtarı ve `MT3608` yükseltici modülü lehimleyin."
    )
    lines.append(
        "   - **Dikkat:** `TP4056` üzerindeki `B-` (`B_M`) pini **yalnızca** pil yuvasının eksi "
        "(`PAD_BAT.BAT_M`) ucuna gider; sistem şasesi (`GND`) ise `TP4056.OUT_M` pininden alınır "
        "(DW01 aşırı deşarj ve kısa devre korumasının çalışması için şarttır)."
    )
    lines.append("2. **Zorunlu Test Adımı — `MT3608 5.0 V` Ayarı (`ESP32` Takılı Değilken):**")
    lines.append(
        "   - `ESP32-S3` dişi soketine henüz takılı değilken (ve `MT3608.VOUT_P` telini `ESP32` / `PAM8403`'e "
        "lehimlemeden önce veya soket boşken) 2 A sigortayı ve 18650 pili kutuplarına dikkat ederek takın."
    )
    lines.append(
        "   - `SW_PWR` anahtarını açın. Multimetreyi DC voltaj kademesine alıp `MT3608.VOUT_P` `(ARKA 12,27)` "
        "ile `MT3608.VOUT_M` `(ARKA 18,27)` arasını ölçün."
    )
    lines.append(
        "   - Multimetrede tam **`5.0 V`** (`4.95 V – 5.05 V`) okuyana kadar `MT3608` üzerindeki trimpotu "
        "küçük düz tornavidayla (genellikle saat yönünün tersine birçok tur) çevirin."
    )
    lines.append("   - Anahtarı kapatıp pili çıkarın.")
    lines.append("3. **Pasif Elemanlar ve Ses Amfisini Lehimleyin (`ARKA` Kart):**")
    lines.append(
        "   - Pil bölücü (`R_BAT1` 10k, `R_BAT2` 10k, `C_BAT` 1 µF), ses 2 kademeli RC filtresi ve bölücüsü "
        "(`R_AUD1` 1k, `C_AUD1` 10 nF, `R_AUD2` 1k, `C_AUD2` 10 nF, `R_AUD3` 10k, `R_AUD4` 1k, `C_AUD3` 1 µF), "
        "`R_SD` (10k pull-up), `R_BL` (10k pull-down) ve `PAM8403` modülünü lehimleyin."
    )
    lines.append(
        "   - Hoparlör kablolarını `PAD_SPK` (`SPK_P` ve `SPK_M`) padlerine bağlayın (`PAM8403` `L+` ve `L-` "
        "çıkışları **asla** `GND`'ye bağlanmaz)."
    )
    lines.append("4. **Dişi Header ve Konnektörleri Lehimleyin (`ARKA` ve `ÖN` Kart):**")
    lines.append(
        "   - `ARKA` kartta `ESP32` için iki adet `1x22` dişi header (`J1` sütun 1, `J3` sütun 10), "
        "`J_LINK_R` (`2x9` header) ve isteğe bağlı `J_JOY` (`1x5` header) lehimleyin."
    )
    lines.append(
        "   - `ÖN` kartta `J_LCD` (`1x14` dişi header, satır 34, sütun 5..18), sekiz adet `6x6 mm` tact switch "
        "(`SW_UP`, `SW_DOWN`, `SW_LEFT`, `SW_RIGHT`, `SW_A`, `SW_B`, `SW_START`, `SW_SELECT`) ve `J_LINK_F` "
        "(`2x9` header, satır 48..49, sütun 7..15) lehimleyin."
    )
    lines.append("5. **Son Kontroller ve Modüllerin Takılması:**")
    lines.append(
        "   - Multimetrenin kısa devre (buzzer) kademesiyle `5V` – `GND`, `3V3` – `GND` ve `BAT+` – `BAT-` "
        "arasında kısa devre olmadığını doğrulayın."
    )
    lines.append("   - `ESP32-S3` kartını ve `2.8\" ILI9341` ekran modülünü dişi soketlerine yerleştirin.")
    lines.append("")

    # Section 2: Point-to-point wiring table for every net
    lines.append("## 2. Noktadan Noktaya Kablolama Tablosu (Tüm Hatlar)")
    lines.append("")
    lines.append("| Hat Adı (Net) | Nereden (`Bileşen.Pin @ KART Sütun,Satır`) | Nereye (`Bileşen.Pin @ KART Sütun,Satır`) | Önerilen Tel Rengi | Açıklama |")
    lines.append("|---|---|---|---|---|")

    def format_node(ref: str, pin_name: str) -> str:
        comp = components[ref]
        p = comp.pin_map()[pin_name]
        b_tr = "ÖN" if comp.board == "FRONT" else "ARKA"
        return f"`{ref}.{pin_name}` @ {b_tr} ({p.col},{p.row})"

    for net in nets:
        for i in range(len(net.nodes) - 1):
            ref_a, pin_a = net.nodes[i]
            ref_b, pin_b = net.nodes[i + 1]
            note = net.description_tr
            if {ref_a, ref_b} == {"J_LINK_F", "J_LINK_R"}:
                note = f"{net.description_tr} (Kartlar arası 2x9 şerit kablo)"
            lines.append(
                f"| `{net.name}` | {format_node(ref_a, pin_a)} | {format_node(ref_b, pin_b)} | "
                f"{net.wire_color_tr} | {note} |"
            )

    lines.append("")

    # Section 3: Inter-board header pin-by-pin table
    lines.append("## 3. Kartlar Arası Bağlantı Header Pin Tablosu (`J_LINK_F` ↔ `J_LINK_R`, 2x9 = 18 Pin)")
    lines.append("")
    lines.append(
        "`ÖN` kartın alt kenarındaki `J_LINK_F` (`sütun 7..15, satır 48..49`) ile `ARKA` kartın alt "
        "kenarındaki `J_LINK_R` (`sütun 1..9, satır 36..37`) birebir aynı pin sırasıyla bağlanır:"
    )
    lines.append("")
    lines.append("| Pin No | Hat Adı (Net) | `J_LINK_F` (`ÖN` Kart Sütun,Satır) | `J_LINK_R` (`ARKA` Kart Sütun,Satır) | ESP32 Karşılığı | Önerilen Tel Rengi |")
    lines.append("|---|---|---|---|---|---|")

    j_link_f = components["J_LINK_F"]
    j_link_r = components["J_LINK_R"]
    pin_to_net: Dict[Tuple[str, str], Net] = {}
    for net in nets:
        for ref, pin_name in net.nodes:
            pin_to_net[(ref, pin_name)] = net

    for idx, (pf, pr) in enumerate(zip(j_link_f.pins, j_link_r.pins), start=1):
        net = pin_to_net[("J_LINK_F", pf.name)]
        esp_targets = [
            f"`{pin_name}`" for ref, pin_name in net.nodes if ref == "ESP32"
        ]
        esp_str = ", ".join(esp_targets) if esp_targets else "-"
        lines.append(
            f"| {idx} | `{net.name}` | `({pf.col},{pf.row})` | `({pr.col},{pr.row})` | {esp_str} | {net.wire_color_tr} |"
        )

    lines.append("")

    # Section 4: Display top 1x4 SD header flying wires
    lines.append("## 4. Ekran Modülü Üst `1x4` microSD Başlığı Uçan Kabloları (`PAD_SD`)")
    lines.append("")
    lines.append(
        "Ekran modülünün üst kenarındaki `1x4` SD erkek pin başlığı için delikli kartta soket kullanılmaz; "
        "4 adet esnek kablo doğrudan ekranın üst kenarından arkadaki `ARKA` kart üzerindeki `PAD_SD` lehim "
        "padlerine (`sütun 9..10, satır 26..27`) bağlanır:"
    )
    lines.append("")
    lines.append("| Ekran Üst SD Pini | Hat Adı (Net) | `ARKA` Kart Lehim Padi (`PAD_SD`) | ESP32 Pini | Ek Eleman / Not |")
    lines.append("|---|---|---|---|---|")
    lines.append("| `SD_CS` | `SD_CS` | `PAD_SD.SD_CS` @ ARKA (9,26) | `GPIO21` (`J3_18_21` @ 10,19) | `R_SD` (10k pull-up -> `3V3`) |")
    lines.append("| `SD_MOSI` | `SPI_MOSI` | `PAD_SD.SD_MOSI` @ ARKA (10,26) | `GPIO11` (`J1_17_11` @ 1,18) | `LCD_MOSI` ile ortak SPI hattı |")
    lines.append("| `SD_MISO` | `SPI_MISO` | `PAD_SD.SD_MISO` @ ARKA (9,27) | `GPIO13` (`J1_19_13` @ 1,20) | `LCD_MISO` ile ortak SPI hattı |")
    lines.append("| `SD_SCK` | `SPI_SCK` | `PAD_SD.SD_SCK` @ ARKA (10,27) | `GPIO12` (`J1_18_12` @ 1,19) | `LCD_SCK` ile ortak SPI hattı |")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------
def main() -> int:
    out_dir = Path(__file__).resolve().parent
    components = build_components()
    nets = build_nets()

    ok, passed, errors = run_self_checks(components, nets)
    for msg in passed:
        print(f"[PASS] {msg}")
    if not ok:
        for err in errors:
            print(f"[FAIL] {err}", file=sys.stderr)
        return 1

    front_svg = out_dir / "front.svg"
    rear_svg = out_dir / "rear.svg"
    wiring_md = out_dir / "wiring.md"

    render_board_svg(
        board_name="FRONT",
        title_tr="ÖN KART (FRONT) - 60 x 130 mm (22 x 49 Delik, Üstten Bileşen Görünümü)",
        subtitle_tr="2.8\" ILI9341 TFT Soketi (J_LCD), 8x Tact Switch (D-Pad, A/B, Start/Select) ve 2x9 Kartlar Arası Header",
        width_mm=FRONT_WIDTH_MM,
        height_mm=FRONT_HEIGHT_MM,
        cols=FRONT_COLS,
        rows=FRONT_ROWS,
        components=components,
        nets=nets,
        out_path=front_svg,
    )
    render_board_svg(
        board_name="REAR",
        title_tr="ARKA KART (REAR) - 50 x 100 mm (18 x 37 Delik, Bileşen Yüzünden Görünüm)",
        subtitle_tr=f"ESP32-S3 (Aralık={ESP32_ROW_SPACING} delik), TP4056, SW_PWR, MT3608, Sigorta, PAM8403, RC Filtre, Pil Bölücü",
        width_mm=REAR_WIDTH_MM,
        height_mm=REAR_HEIGHT_MM,
        cols=REAR_COLS,
        rows=REAR_ROWS,
        components=components,
        nets=nets,
        out_path=rear_svg,
    )
    generate_wiring_md(components, nets, wiring_md)

    print(f"[OK] Generated {front_svg.name}, {rear_svg.name}, and {wiring_md.name} successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
