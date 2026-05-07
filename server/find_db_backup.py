"""Find database backup SQL files (mac_vod table dumps)."""
from pathlib import Path
from dissect.evidence.ewf import EWF
import re

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()
size1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).size
size2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).size

OUT = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\db_backup_hits.txt")
out = open(OUT, 'w', encoding='utf-8')

CHUNK = 16 * 1024 * 1024  # 16MB

# MacCMS data backup format: 'data' field with SQL INSERT statements
# Mac CMS table backup PHP files might look like: $tableData = "...";
# OR actual .sql.gz/sql files
# Key markers for vod table data:
patterns_re = [
    (re.compile(rb'INSERT INTO `mac_vod`'), "sql-insert-mac_vod"),
    (re.compile(rb'CREATE TABLE `mac_vod`'), "sql-create-mac_vod"),
    (re.compile(rb"vod_pic[^\x20-\x7e]?[^a-zA-Z0-9]+(?:'|\")[a-zA-Z0-9./-]+\.(?:jpg|png|webp|gif)"), "vod_pic-value"),
    (re.compile(rb"backup/database/[\w.]+"), "backup-file-name"),
    (re.compile(rb"upload/vod/2026[\d]+-\d+/[a-f0-9]{32}\.jpg"), "vod-image-uri"),
    (re.compile(rb"`vod_name`[^,]*,[^,]*,"), "vod_record"),
    (re.compile(rb'\.sql\b'), "sql-file"),
    (re.compile(rb'mac_vod'), "mac_vod-mention"),
    (re.compile(rb'mac_user|mac_admin|mac_collect|mac_pay'), "mac-table-other"),
]

# Focus search on regions where we already saw maccms cache (around 0x267D70000 on 检材3-2)
SEARCH_AREAS = [
    (disk2, "检材3-2", 0x100000000, size2, "检材3-2 LVM"),
    (disk1, "检材3-1", 0x6FC000000, size1, "检材3-1 LVM"),
]

found = {}

for stream, label, start, end, desc in SEARCH_AREAS:
    print(f"\n=== Scanning {desc} 0x{start:X}-0x{end:X} ({(end-start)/(1024**3):.1f}GB) ===")
    out.write(f"\n=== {desc} ===\n")
    
    last_log_g = start / (1024**3)
    for offset in range(start, end, CHUNK):
        if offset / (1024**3) - last_log_g >= 5:
            print(f"  {label}: {offset/(1024**3):.1f}GB")
            last_log_g = offset / (1024**3)
        
        stream.seek(offset)
        data = stream.read(CHUNK + 4096)
        if not data:
            break
        
        for pat, ptype in patterns_re:
            for m in pat.finditer(data):
                grp = m.group(0)
                if isinstance(grp, bytes):
                    grp = grp.decode('utf-8', errors='replace')[:80]
                key = f"{ptype}::{grp}"
                if key not in found:
                    found[key] = (offset + m.start(), label)
                    s, e = max(0, m.start()-200), min(len(data), m.end()+400)
                    ctx = data[s:e].decode('utf-8', errors='replace')
                    line = f"  [{ptype}] {grp!r} @ 0x{offset+m.start():X} ({label})"
                    print(line)
                    out.write(line + "\n")
                    out.write(f"    ctx: {ctx[:600]!r}\n")
                    out.flush()
                
                if len(found) > 500:
                    break

print(f"\nTotal: {len(found)}")
out.write(f"\nTotal: {len(found)}\n")
out.close()
