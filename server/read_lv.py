"""Reconstruct LVM logical volumes and read filesystem data."""
import struct
import sys
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
SECTOR = 512
EXTENT_SIZE = 8192 * SECTOR  # 4MB

# Open both E01s
ewf1_fhs = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
ewf2_fhs = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk1 = (EWF(*ewf1_fhs) if len(ewf1_fhs) > 1 else EWF(ewf1_fhs[0])).open()  # sdb
disk2 = (EWF(*ewf2_fhs) if len(ewf2_fhs) > 1 else EWF(ewf2_fhs[0])).open()  # sda


class LVReader:
    """Read from a reassembled LVM logical volume."""
    def __init__(self, segments):
        # segments: list of (disk_stream, pv_partition_sector_offset, pv_pe_start_sectors, extent_count)
        self.segments = []
        offset = 0
        for disk_stream, part_start_sect, pe_start_sect, ext_count in segments:
            pv_data_start = (part_start_sect + pe_start_sect) * SECTOR
            seg_size = ext_count * EXTENT_SIZE
            self.segments.append((offset, offset + seg_size, disk_stream, pv_data_start))
            offset += seg_size
        self.size = offset

    def read_at(self, offset, size):
        data = b''
        remaining = size
        pos = offset
        for seg_start, seg_end, stream, pv_data_start in self.segments:
            if pos >= seg_end or remaining <= 0:
                continue
            if pos < seg_start:
                continue
            seg_offset = pos - seg_start
            available = seg_end - pos
            to_read = min(remaining, available)
            stream.seek(pv_data_start + seg_offset)
            chunk = stream.read(to_read)
            data += chunk
            remaining -= len(chunk)
            pos += len(chunk)
        return data


# VG "volum" → LV "root": segment1=pv0(sda2)@7152ext, segment2=pv1(sdb1)@7152ext
lv_root = LVReader([
    (disk2, 8204288, 2048, 7152),   # pv0=sda2, 检材3-2 part009
    (disk1, 2048, 2048, 7152),      # pv1=sdb1, 检材3-1 part002
])

# VG "root" → LV "data": segment1=pv1(sdb2)@8207ext, segment2=pv0(sda3)@7205ext
lv_data = LVReader([
    (disk1, 58593280, 2048, 8207),  # pv1=sdb2, 检材3-1 part003
    (disk2, 66797568, 2048, 7205),  # pv0=sda3, 检材3-2 part010
])

def check_fs(lv, label):
    print(f"\n{'='*60}")
    print(f"  {label} (size: {lv.size/(1024**3):.2f} GB)")
    data = lv.read_at(0, 0x11000)
    
    # btrfs: "_BHRfS_M" at offset 0x10040
    if len(data) > 0x10048 and data[0x10040:0x10048] == b'_BHRfS_M':
        print("  Filesystem: BTRFS")
        # Read btrfs superblock at 0x10000
        sb = data[0x10000:0x10000+0x1000]
        # UUID at offset 0x20 (16 bytes)
        import uuid
        fs_uuid = uuid.UUID(bytes_le=sb[0x20:0x30])
        print(f"  UUID: {fs_uuid}")
        # label at offset 0x12B (256 bytes)
        fs_label = sb[0x12B:0x22B].split(b'\x00')[0].decode('utf-8', errors='replace')
        print(f"  Label: '{fs_label}'")
        return 'btrfs'
    
    # xfs: "XFSB" at offset 0
    if data[:4] == b'XFSB':
        print("  Filesystem: XFS")
        import uuid
        fs_uuid = uuid.UUID(bytes=data[0x20:0x30])
        print(f"  UUID: {fs_uuid}")
        return 'xfs'
    
    # ext4: magic 0xEF53 at offset 0x438
    if len(data) > 0x43A and struct.unpack_from('<H', data, 0x438)[0] == 0xEF53:
        print("  Filesystem: EXT4")
        import uuid
        fs_uuid = uuid.UUID(bytes_le=data[0x468:0x478])
        print(f"  UUID: {fs_uuid}")
        return 'ext4'
    
    print(f"  Unknown FS. First 64 bytes: {data[:64].hex()}")
    return 'unknown'

print("=" * 60)
print("  Checking filesystem types on LVs")
print("=" * 60)

fs_root = check_fs(lv_root, "VG=volum LV=root (system root)")
fs_data = check_fs(lv_data, "VG=root LV=data (data volume)")

# Now try to read key system files from the root LV
if fs_root == 'btrfs':
    print("\n\n" + "=" * 60)
    print("  BTRFS detected on root. Searching for key files...")
    print("  Scanning for /etc/os-release, /etc/fstab patterns...")
    print("=" * 60)
    
    # Search for os-release content in chunks
    # Btrfs default subvolume data starts after the superblock region
    # Let's search for common strings
    SEARCH_STRINGS = [
        b'PRETTY_NAME=',   # os-release
        b'ID=debian',      # os-release
        b'/dev/volum/',     # fstab
        b'UUID=',          # fstab
        b'btrfs subvol',   # fstab
        b'docker',         # various
    ]
    
    chunk_size = 4 * 1024 * 1024  # 4MB
    max_search = min(lv_root.size, 2 * 1024 * 1024 * 1024)  # Search first 2GB
    
    found = set()
    for offset in range(0, max_search, chunk_size):
        if len(found) >= len(SEARCH_STRINGS):
            break
        chunk = lv_root.read_at(offset, chunk_size)
        for s in SEARCH_STRINGS:
            if s in found:
                continue
            idx = chunk.find(s)
            if idx >= 0:
                found.add(s)
                context_start = max(0, idx - 200)
                context_end = min(len(chunk), idx + 500)
                context = chunk[context_start:context_end]
                try:
                    text = context.decode('utf-8', errors='replace')
                except:
                    text = repr(context)
                print(f"\n  Found '{s.decode()}' at offset 0x{offset + idx:X}:")
                # Print clean lines
                for line in text.split('\n'):
                    line = line.strip()
                    if line and len(line) < 200:
                        print(f"    {line}")

elif fs_root == 'xfs' or fs_root == 'ext4':
    print(f"\n  {fs_root.upper()} on root - will need to parse inode tree")
    # For ext4/xfs, try strings search as well
    print("  Scanning for key strings...")
    chunk_size = 4 * 1024 * 1024
    max_search = min(lv_root.size, 500 * 1024 * 1024)  # 500MB
    
    for offset in range(0, max_search, chunk_size):
        chunk = lv_root.read_at(offset, chunk_size)
        for pattern in [b'PRETTY_NAME=', b'ID=debian', b'/etc/fstab']:
            idx = chunk.find(pattern)
            if idx >= 0:
                ctx = chunk[max(0,idx-100):idx+300]
                print(f"\n  Found at 0x{offset+idx:X}: {ctx.decode('utf-8',errors='replace')[:300]}")

print("\n\nDone.")
