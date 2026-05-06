"""Verify LV offsets by directly reading from disks."""
import struct
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
SECTOR = 512

# Open both disks
fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()  # sdb
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()  # sda


def check_at(stream, abs_offset, label):
    """Check filesystem signature at given absolute byte offset."""
    stream.seek(abs_offset)
    data = stream.read(0x11000)
    
    fs = "unknown"
    if data[0x10040:0x10048] == b'_BHRfS_M':
        fs = "btrfs"
    elif data[:4] == b'XFSB':
        fs = "xfs"
    elif len(data) > 0x43A and struct.unpack_from('<H', data, 0x438)[0] == 0xEF53:
        fs = "ext4"
    
    is_zero = all(b == 0 for b in data[:512])
    print(f"  {label}: offset=0x{abs_offset:X}, fs={fs}, first512_zero={is_zero}")
    if not is_zero:
        print(f"    First 32 bytes: {data[:32].hex()}")
    return fs


print("=== Checking raw offsets on disk2 (sda = 检材3-2) ===")
# Part009 (sda2): sector 8204288
part_start = 8204288 * SECTOR
print(f"\nPartition sda2 start: sector 8204288, byte 0x{part_start:X}")
check_at(disk2, part_start, "sda2 start (LABELONE expected)")
check_at(disk2, part_start + 2048 * SECTOR, "sda2 + pe_start=2048 sectors")
check_at(disk2, part_start + 4096 * SECTOR, "sda2 + 4096 sectors")

# Part010 (sda3): sector 66797568
part_start2 = 66797568 * SECTOR
print(f"\nPartition sda3 start: sector 66797568, byte 0x{part_start2:X}")
check_at(disk2, part_start2, "sda3 start (LABELONE expected)")
check_at(disk2, part_start2 + 2048 * SECTOR, "sda3 + pe_start=2048 sectors")

print("\n=== Checking raw offsets on disk1 (sdb = 检材3-1) ===")
# Part002 (sdb1): sector 2048
part_start3 = 2048 * SECTOR
print(f"\nPartition sdb1 start: sector 2048, byte 0x{part_start3:X}")
check_at(disk1, part_start3, "sdb1 start (LABELONE expected)")
check_at(disk1, part_start3 + 2048 * SECTOR, "sdb1 + pe_start=2048 sectors")

# Part003 (sdb2): sector 58593280
part_start4 = 58593280 * SECTOR
print(f"\nPartition sdb2 start: sector 58593280, byte 0x{part_start4:X}")
check_at(disk1, part_start4, "sdb2 start (LABELONE expected)")
check_at(disk1, part_start4 + 2048 * SECTOR, "sdb2 + pe_start=2048 sectors")

# Now let's scan for filesystem signatures in first 50MB of each PV data area
print("\n=== Scanning for filesystem signatures ===")
import uuid

scan_targets = [
    (disk2, 8204288 * SECTOR + 2048 * SECTOR, "VG=volum PV=sda2"),
    (disk1, 2048 * SECTOR + 2048 * SECTOR, "VG=volum PV=sdb1"),
    (disk1, 58593280 * SECTOR + 2048 * SECTOR, "VG=root PV=sdb2"),
    (disk2, 66797568 * SECTOR + 2048 * SECTOR, "VG=root PV=sda3"),
]

for stream, base, label in scan_targets:
    print(f"\n  Scanning {label} (base=0x{base:X})...")
    found_any = False
    for off in range(0, 50 * 1024 * 1024, 65536):
        stream.seek(base + off)
        chunk = stream.read(0x11000)
        if chunk[0x10040:0x10048] == b'_BHRfS_M':
            print(f"    BTRFS at offset +0x{off:X}")
            sb = chunk[0x10000:0x11000]
            fs_uuid = uuid.UUID(bytes_le=sb[0x20:0x30])
            label_bytes = sb[0x12B:0x22B].split(b'\x00')[0]
            print(f"    UUID: {fs_uuid}, Label: '{label_bytes.decode()}'")
            found_any = True
            break
        if chunk[:4] == b'XFSB':
            print(f"    XFS at offset +0x{off:X}")
            fs_uuid = uuid.UUID(bytes=chunk[0x20:0x30])
            print(f"    UUID: {fs_uuid}")
            found_any = True
            break
        if len(chunk) > 0x43A and struct.unpack_from('<H', chunk, 0x438)[0] == 0xEF53:
            print(f"    EXT4 at offset +0x{off:X}")
            fs_uuid = uuid.UUID(bytes_le=chunk[0x468:0x478])
            print(f"    UUID: {fs_uuid}")
            found_any = True
            break
    if not found_any:
        print(f"    No FS signature in first 50MB")

print("\nDone.")
