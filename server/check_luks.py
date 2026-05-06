"""Check LUKS and verify LABELONE on PVs."""
import struct
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
S = 512

fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()

# Verify LABELONE at partition 009 start (sector 8204288)
off = 8204288 * S
disk2.seek(off)
data = disk2.read(4096)
print(f"disk2 @ sector 8204288 (0x{off:X}):")
# Find first non-zero
for i in range(len(data)):
    if data[i] != 0:
        print(f"  First non-zero at offset {i}: {data[i:i+32].hex()}")
        print(f"  As text: {data[i:i+32]}")
        break
else:
    print("  ALL ZERO in first 4KB!")

# Check pe_start area for LUKS
pe_off = (8204288 + 2048) * S
disk2.seek(pe_off)
pe_data = disk2.read(4096)
print(f"\ndisk2 @ pe_start (0x{pe_off:X}):")
for i in range(len(pe_data)):
    if pe_data[i] != 0:
        print(f"  First non-zero at offset {i}: {pe_data[i:i+32].hex()}")
        print(f"  LUKS magic check: {pe_data[:6] == bytes.fromhex('4c554b53babe')}")
        break
else:
    print("  ALL ZERO!")

# Scan entire disk2 for LUKS magic
print("\nScanning disk2 for LUKS magic (every 1MB, first 4GB)...")
for mb in range(0, 4096):
    disk2.seek(mb * 1024 * 1024)
    magic = disk2.read(6)
    if magic == bytes.fromhex("4c554b53babe"):
        print(f"  LUKS found at offset {mb}MB (0x{mb*1024*1024:X})")

# Also scan disk1
fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()

print("\nScanning disk1 for LUKS magic (every 1MB, first 4GB)...")
for mb in range(0, 4096):
    disk1.seek(mb * 1024 * 1024)
    magic = disk1.read(6)
    if magic == bytes.fromhex("4c554b53babe"):
        print(f"  LUKS found at offset {mb}MB (0x{mb*1024*1024:X})")

print("\nDone.")
