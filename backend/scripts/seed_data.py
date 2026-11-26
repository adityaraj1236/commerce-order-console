"""Synthetic product catalogue for local development and demos.

Each row is (sku, name, description, price, stock_quantity). Stock levels are mixed on
purpose so every UI state appears: out of stock (0), low stock (1-5) and in stock.
SKUs must be unique; scripts/seed.py checks this before inserting.
"""

from decimal import Decimal

SeedRow = tuple[str, str, str, str, int]

# One product per line reads like a table, so the formatter leaves this list alone.
# fmt: off
SEED_ROWS: list[SeedRow] = [
    # ---- Original catalogue ----
    ("KB-MECH-001", "Mechanical Keyboard (TKL)", "Tenkeyless mechanical keyboard with hot-swappable brown switches.", "4499.00", 25),
    ("MS-WL-002", "Wireless Ergonomic Mouse", "Vertical ergonomic mouse with silent clicks and USB-C charging.", "1899.00", 40),
    ("MN-27Q-003", '27" QHD Monitor', "27-inch 2560x1440 IPS monitor with height-adjustable stand.", "18999.00", 8),
    ("HUB-USBC-004", "USB-C 7-in-1 Hub", "HDMI 4K, 3x USB-A, SD/microSD readers and 100W pass-through charging.", "2299.00", 3),
    ("HS-NC-005", "Noise-Cancelling Headset", "Over-ear Bluetooth headset with active noise cancellation and boom mic.", "7999.00", 0),
    ("CAM-1080-006", "1080p Webcam", "Full HD webcam with dual microphones and privacy shutter.", "2799.00", 15),
    ("STD-LAP-007", "Aluminium Laptop Stand", "Adjustable aluminium stand for 11-17 inch laptops.", "1499.00", 2),
    ("CBL-HDMI-008", "HDMI 2.1 Cable (2 m)", "Braided 8K/60Hz, 4K/120Hz certified high-speed HDMI cable.", "649.00", 120),
    # ---- Keyboards and mice ----
    ("KB-WL-009", "Wireless Slim Keyboard", "Low-profile Bluetooth keyboard that pairs with three devices.", "2499.00", 32),
    ("KB-FULL-010", "Full-Size Mechanical Keyboard", "104-key mechanical keyboard with red linear switches and RGB.", "5999.00", 14),
    ("KB-NUM-011", "Wireless Numeric Keypad", "Compact 2.4 GHz numeric keypad for spreadsheets and billing.", "899.00", 4),
    ("MS-GAM-012", "Gaming Mouse 16K DPI", "Lightweight wired mouse with a 16,000 DPI optical sensor.", "2199.00", 27),
    ("MS-TRV-013", "Travel Mouse", "Compact Bluetooth mouse with a rechargeable battery.", "999.00", 0),
    ("PAD-XL-014", "Extended Desk Mat (XL)", "900 x 400 mm stitched-edge desk mat with a non-slip base.", "799.00", 65),
    ("WR-KB-015", "Keyboard Wrist Rest", "Memory-foam wrist rest for full-size keyboards.", "599.00", 38),
    # ---- Monitors and displays ----
    ("MN-24F-016", '24" Full HD Monitor', "24-inch 1920x1080 IPS monitor with thin bezels.", "9499.00", 21),
    ("MN-32U-017", '32" 4K UHD Monitor', "32-inch 3840x2160 monitor with HDR10 and USB-C 65W.", "32999.00", 5),
    ("MN-34W-018", '34" Ultrawide Monitor', "34-inch 3440x1440 curved ultrawide for multitasking.", "38999.00", 0),
    ("MN-PRT-019", '15.6" Portable Monitor', "USB-C powered portable display with a folding cover.", "11999.00", 9),
    ("ARM-DUAL-020", "Dual Monitor Arm", "Gas-spring arm for two 17-32 inch monitors, VESA 75/100.", "4299.00", 12),
    # ---- Audio ----
    ("HS-WRD-021", "Wired Office Headset", "USB headset with an in-line mute control for calls.", "1299.00", 44),
    ("EB-TWS-022", "True Wireless Earbuds", "Bluetooth 5.3 earbuds with a charging case and 28-hour battery.", "3499.00", 19),
    ("SPK-BT-023", "Portable Bluetooth Speaker", "Water-resistant speaker with 12 hours of playback.", "2999.00", 3),
    ("MIC-USB-024", "USB Condenser Microphone", "Cardioid USB microphone with a desk stand for meetings.", "4499.00", 11),
    ("SPK-DSK-025", "Desktop Speakers (2.0)", "Compact stereo speakers with a 3.5 mm and USB input.", "1799.00", 23),
    # ---- Storage ----
    ("SSD-EXT-026", "Portable SSD 1 TB", "USB-C external SSD with 1,050 MB/s read speeds.", "7499.00", 17),
    ("SSD-NVM-027", "NVMe SSD 512 GB", "M.2 2280 PCIe 4.0 internal SSD.", "3999.00", 29),
    ("HDD-EXT-028", "External Hard Drive 2 TB", "USB 3.0 portable hard drive for backups.", "5799.00", 2),
    ("USB-PEN-029", "USB 3.2 Flash Drive 128 GB", "Metal-body flash drive with a key-ring loop.", "899.00", 150),
    ("SD-CARD-030", "microSD Card 256 GB", "A2 U3 microSD card with an SD adapter.", "1599.00", 0),
    # ---- Networking ----
    ("NET-RTR-031", "Wi-Fi 6 Router", "Dual-band AX3000 router with four gigabit LAN ports.", "6499.00", 13),
    ("NET-MSH-032", "Mesh Wi-Fi System (2-pack)", "Whole-home mesh Wi-Fi covering up to 4,000 sq ft.", "12999.00", 4),
    ("NET-SW8-033", "8-Port Gigabit Switch", "Unmanaged desktop switch with a metal casing.", "1899.00", 26),
    ("NET-ADP-034", "USB Wi-Fi Adapter", "AC1300 dual-band USB adapter for desktops.", "1199.00", 35),
    ("CBL-ETH-035", "Cat6 Ethernet Cable (5 m)", "Snagless Cat6 patch cable for gigabit networks.", "349.00", 210),
    # ---- Cables and charging ----
    ("CBL-USBC-036", "USB-C to USB-C Cable (1 m)", "100W braided charging and data cable.", "499.00", 180),
    ("CHG-65W-037", "65W GaN USB-C Charger", "Compact two-port charger for laptops and phones.", "2499.00", 22),
    ("CHG-WL-038", "Wireless Charging Pad", "15W Qi wireless charger with a non-slip surface.", "1299.00", 1),
    ("PWR-BNK-039", "Power Bank 20,000 mAh", "Dual USB-C power bank with 22.5W fast charging.", "2199.00", 31),
    ("CBL-DP-040", "DisplayPort 1.4 Cable (2 m)", "8K/60Hz DisplayPort cable with latching connectors.", "799.00", 60),
    # ---- Office and furniture ----
    ("CHR-ERG-041", "Ergonomic Office Chair", "Mesh-back chair with adjustable lumbar support and armrests.", "14999.00", 6),
    ("DSK-STD-042", "Electric Standing Desk", "Dual-motor sit-stand desk with four height presets.", "27999.00", 0),
    ("LMP-LED-043", "LED Desk Lamp", "Dimmable lamp with colour-temperature control and USB port.", "1999.00", 24),
    ("FT-REST-044", "Adjustable Footrest", "Tilting footrest with a textured massage surface.", "1499.00", 5),
    ("ORG-CBL-045", "Cable Management Tray", "Under-desk steel tray that keeps cables off the floor.", "999.00", 42),
    # ---- Printing and scanning ----
    ("PRN-LSR-046", "Mono Laser Printer", "Wireless laser printer with automatic duplex printing.", "12499.00", 7),
    ("PRN-INK-047", "Ink Tank Printer", "All-in-one ink tank printer with low cost per page.", "13999.00", 3),
    ("SCN-DOC-048", "Document Scanner", "Duplex sheet-fed scanner, 30 pages per minute.", "18499.00", 0),
    ("PPR-A4-049", "A4 Copier Paper (500 sheets)", "75 GSM bright-white paper for laser and inkjet printers.", "349.00", 300),
    ("LBL-THR-050", "Thermal Label Printer", "4x6 inch shipping label printer for dispatch desks.", "7999.00", 10),
    # ---- Laptop accessories ----
    ("BAG-LAP-051", "Laptop Backpack 15.6\"", "Water-resistant backpack with a padded laptop sleeve.", "2299.00", 28),
    ("SLV-LAP-052", "Laptop Sleeve 14\"", "Neoprene sleeve with an accessory pocket.", "899.00", 47),
    ("CLR-PAD-053", "Laptop Cooling Pad", "Cooling pad with five quiet fans and adjustable height.", "1599.00", 16),
    ("DOCK-TB4-054", "Thunderbolt 4 Dock", "Dock with dual 4K display support and 96W charging.", "24999.00", 2),
    ("LCK-KEN-055", "Laptop Security Lock", "Keyed cable lock for laptops with a lock slot.", "1199.00", 33),
    # ---- Smart office ----
    ("PLG-SMT-056", "Smart Wi-Fi Plug", "App and voice controlled plug with energy monitoring.", "999.00", 54),
    ("UPS-600-057", "UPS 600VA", "Line-interactive UPS with battery backup for one PC.", "3299.00", 9),
    ("SRG-PRT-058", "Surge Protector (6 sockets)", "Six-socket surge protector with two USB ports.", "1299.00", 37),
]
# fmt: on


def build_seed_products() -> list[dict[str, object]]:
    """Rows as dictionaries ready for INSERT, with money as Decimal (never float)."""
    return [
        {
            "sku": sku,
            "name": name,
            "description": description,
            "price": Decimal(price),
            "stock_quantity": stock_quantity,
        }
        for sku, name, description, price, stock_quantity in SEED_ROWS
    ]
