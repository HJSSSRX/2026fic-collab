"""Extract full content around ngrok config locations."""
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()

# Locations of interest
LOCATIONS = [
    (0x709A9EE68, "ngrok agent yml #1"),
    (0x709C6A61E, "ngrok agent yml #2"),
    (0x7BE569A49, "ngrok server config (port 3000)"),
    (0x78F008EA4, ".ngrok.io reference #1"),
    (0x7973053A8, ".ngrok.io ref #2"),
    (0x7779110DB, ".ngrok-free reference"),
    (0x719ACE441, "t.me/maccms_channel"),
]

for off, label in LOCATIONS:
    # Read ±2KB around the position
    start = max(0, off - 1024)
    disk1.seek(start)
    data = disk1.read(4096)
    print(f"\n{'='*70}")
    print(f"# {label} @ 0x{off:X} ({off/(1024**2):.1f}MB)")
    print(f"# Reading 0x{start:X} - 0x{start+4096:X}")
    print(f"{'='*70}")
    
    # Output as text, ASCII chars only
    out_lines = []
    current = []
    for byte in data:
        if 32 <= byte < 127 or byte in (9, 10, 13):
            current.append(chr(byte))
        else:
            if current:
                line = ''.join(current)
                # Split by newlines
                for sub in line.split('\n'):
                    sub = sub.rstrip('\r').strip()
                    if 5 < len(sub) < 300:
                        out_lines.append(sub)
                current = []
    if current:
        line = ''.join(current)
        for sub in line.split('\n'):
            sub = sub.rstrip('\r').strip()
            if 5 < len(sub) < 300:
                out_lines.append(sub)
    
    for l in out_lines[:60]:
        # Safe printing
        try:
            print(f"  {l}")
        except:
            print(f"  {l.encode('ascii', errors='replace').decode('ascii')}")

print("\n\nDone.")
