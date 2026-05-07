"""Search raw disk data for key system file content to locate root FS."""
import struct, uuid
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
S = 512

fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()

CHUNK = 4 * 1024 * 1024  # 4MB

targets = [
    (b'PRETTY_NAME', "os-release"),
    (b'VERSION_ID=', "os-release"),
    (b'/dev/volum/', "fstab/LVM ref"),
    (b'/dev/root/', "fstab/LVM ref"),
    (b'_BHRfS_M', "btrfs superblock"),
    (b'XFSB', "xfs superblock"),
    (b'docker', "docker reference"),
    (b'nginx', "nginx reference"),
    (b'ngrok', "ngrok reference"),
]

def scan_disk(stream, disk_name, max_gb=60):
    print(f"\n{'#'*60}")
    print(f"# Scanning {disk_name} (first {max_gb}GB)")
    print(f"{'#'*60}")
    
    found_items = {}
    max_bytes = max_gb * 1024 * 1024 * 1024
    
    for offset in range(0, max_bytes, CHUNK):
        stream.seek(offset)
        data = stream.read(CHUNK)
        if not data:
            break
        
        for pattern, desc in targets:
            key = f"{pattern.decode('utf-8', errors='replace')}@{desc}"
            if key in found_items:
                continue
            idx = data.find(pattern)
            if idx >= 0:
                abs_off = offset + idx
                found_items[key] = abs_off
                # Get context
                ctx_start = max(0, idx - 50)
                ctx_end = min(len(data), idx + 300)
                ctx = data[ctx_start:ctx_end]
                text = ctx.decode('utf-8', errors='replace')
                # Clean up
                lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) < 200]
                print(f"\n  [{desc}] Found at offset 0x{abs_off:X} ({abs_off/(1024*1024):.1f} MB):")
                for l in lines[:10]:
                    print(f"    {l}")
                
                # For btrfs, extract UUID
                if pattern == b'_BHRfS_M':
                    sb_start = idx - 0x40  # magic is at +0x40 in superblock
                    if sb_start >= 0:
                        sb = data[sb_start:sb_start+0x1000]
                        fs_uuid = uuid.UUID(bytes_le=sb[0x20:0x30])
                        print(f"    → UUID: {fs_uuid}")
    
    if not found_items:
        print("  Nothing found!")
    return found_items

scan_disk(disk1, "检材3-1 (sdb)")
scan_disk(disk2, "检材3-2 (sda)")

print("\n\nScan complete.")
