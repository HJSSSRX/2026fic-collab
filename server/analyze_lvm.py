"""Analyze LVM structures in both E01 images and find root filesystem."""
import struct
import sys
from pathlib import Path

from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")

def read_at(ewf_obj, offset, size):
    ewf_obj.seek(offset)
    return ewf_obj.read(size)

def check_fs_signature(data):
    """Check filesystem signature from first bytes of a partition."""
    sigs = []
    # btrfs: "_BHRfS_M" at offset 0x10040
    if len(data) > 0x10048:
        if data[0x10040:0x10048] == b'_BHRfS_M':
            sigs.append('btrfs')
    # xfs: "XFSB" at offset 0
    if data[:4] == b'XFSB':
        sigs.append('xfs')
    # ext4: magic 0xEF53 at offset 0x438
    if len(data) > 0x43A:
        if struct.unpack_from('<H', data, 0x438)[0] == 0xEF53:
            sigs.append('ext4')
    # LVM PV header: "LABELONE" at offset 0x200
    if len(data) > 0x208:
        if data[0x200:0x208] == b'LABELONE':
            sigs.append('lvm_pv')
    # Also check offset 0 for LABELONE
    if data[:8] == b'LABELONE':
        sigs.append('lvm_pv_0')
    # LUKS
    if data[:6] == b'LUKS\xba\xbe':
        sigs.append('luks')
    return sigs if sigs else ['unknown']

def analyze_lvm_pv(ewf_obj, part_offset, label):
    """Read LVM PV header and metadata."""
    # LVM PV label is at sector 1 (offset 512)
    data = read_at(ewf_obj, part_offset, 0x11000)
    
    sigs = check_fs_signature(data)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Offset: {part_offset} (0x{part_offset:X})")
    print(f"  Signatures: {sigs}")
    print(f"{'='*60}")
    
    if 'lvm_pv' in sigs or 'lvm_pv_0' in sigs:
        # Parse LABELONE
        label_offset = 0x200 if 'lvm_pv' in sigs else 0
        sector = data[label_offset:label_offset+512]
        print(f"  Label header: {sector[:32].hex()}")
        # offset to PV header from label
        pv_hdr_offset = struct.unpack_from('<I', sector, 20)[0]
        print(f"  PV header offset from label: {pv_hdr_offset}")
        
        # Read PV UUID (32 bytes after PV header)
        pv_offset_abs = label_offset + pv_hdr_offset
        if pv_offset_abs + 64 < len(data):
            pv_uuid = data[pv_offset_abs:pv_offset_abs+32]
            print(f"  PV UUID raw: {pv_uuid}")
        
        # Try to find metadata area - search for VG metadata text
        meta_search = read_at(ewf_obj, part_offset, 0x200000)  # Read 2MB
        # Look for typical VG metadata markers
        for marker in [b'id = "', b'physical_volumes', b'logical_volumes', b'segment']:
            idx = meta_search.find(marker)
            if idx >= 0:
                # Found metadata text area
                # Find start of metadata (back up to find '{')
                start = max(0, idx - 2000)
                end = min(len(meta_search), idx + 20000)
                text = meta_search[start:end]
                try:
                    decoded = text.decode('utf-8', errors='replace')
                    # Find the VG name (first line usually)
                    lines = decoded.split('\n')
                    print(f"\n  LVM Metadata (from offset 0x{start:X}):")
                    printed = 0
                    for line in lines:
                        line_s = line.strip()
                        if line_s and printed < 100:
                            print(f"    {line_s}")
                            printed += 1
                except:
                    pass
                break
    
    return sigs

def main():
    # Analyze 检材3-1
    print("\n" + "#"*70)
    print("# 检材3-1.E01")
    print("#"*70)
    
    ewf1_files = sorted(E01_DIR.glob("检材3-1.E0?"))
    print(f"Files: {[f.name for f in ewf1_files]}")
    fhs1 = [open(f, "rb") for f in ewf1_files]
    ewf1_raw = EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])
    ewf1 = ewf1_raw.open()
    print(f"Size: {ewf1_raw.size} bytes ({ewf1_raw.size/(1024**3):.2f} GB)")
    
    analyze_lvm_pv(ewf1, 2048 * 512, "检材3-1 Part002 (LVM @ s2048)")
    analyze_lvm_pv(ewf1, 58593280 * 512, "检材3-1 Part003 (LVM @ s58593280)")
    
    # Analyze 检材3-2
    print("\n" + "#"*70)
    print("# 检材3-2.E01")
    print("#"*70)
    
    ewf2_files = sorted(E01_DIR.glob("检材3-2.E0?"))
    print(f"Files: {[f.name for f in ewf2_files]}")
    fhs2 = [open(f, "rb") for f in ewf2_files]
    ewf2_raw = EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])
    ewf2 = ewf2_raw.open()
    print(f"Size: {ewf2_raw.size} bytes ({ewf2_raw.size/(1024**3):.2f} GB)")
    
    analyze_lvm_pv(ewf2, 8204288 * 512, "检材3-2 Part009 (LVM @ s8204288)")
    analyze_lvm_pv(ewf2, 66797568 * 512, "检材3-2 Part010 (LVM @ s66797568)")
    
    # Also check EFI partition
    print(f"\n{'='*60}")
    print(f"  检材3-2 EFI Partition (s2048)")
    efi_data = read_at(ewf2, 2048 * 512, 4096)
    print(f"  First 16 bytes: {efi_data[:16].hex()}")
    if efi_data[0x36:0x3B] == b'FAT16' or efi_data[0x52:0x57] == b'FAT32':
        print("  FAT filesystem detected")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
