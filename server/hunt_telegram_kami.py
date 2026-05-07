"""Hunt for actual Telegram group / kami site refs in TiKV data region."""
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

# Output
OUT = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\telegram_kami_hits.txt")
out = open(OUT, 'w', encoding='utf-8')

CHUNK = 16 * 1024 * 1024  # 16MB chunks for speed

# Search for: 
# - https://t.me/SOMETHING (capture username)
# - tg://resolve?domain=NAME
# - sp-live88 related
# - actual website domain configs
# - mac_config table entries

patterns_re = [
    (re.compile(rb'https://t\.me/([a-zA-Z][a-zA-Z0-9_]{4,32})'), "telegram-link"),
    (re.compile(rb'tg://resolve\?domain=([a-zA-Z][a-zA-Z0-9_]{4,32})'), "telegram-deeplink"),
    (re.compile(rb'@([a-zA-Z][a-zA-Z0-9_]{4,32})\b'), "telegram-mention-maybe"),
    (re.compile(rb'sp[-_]?live88[a-z0-9.-]*'), "sp-live88-domain"),
    (re.compile(rb'site_url[^a-zA-Z0-9]+([a-zA-Z][-a-zA-Z0-9.]+\.[a-z]{2,4})'), "site_url-value"),
    (re.compile(rb'site_name[^a-zA-Z0-9]+([\x20-\x7E\xA0-\xFF\xE0-\xFF]{2,40})'), "site_name-value"),
    (re.compile(rb'(?:ICP|icp)[\s\xc2-\xff]*[\xe5\xa4\x87][\s]*\d{6,8}'), "icp-mainland"),
    (re.compile(rb'card_url[^a-zA-Z0-9]+([a-zA-Z][-a-zA-Z0-9./:?=]+)'), "kami-url"),
    (re.compile(rb'main_domain[^a-zA-Z0-9]+([a-zA-Z][-a-zA-Z0-9.]+\.[a-z]{2,4})'), "main_domain"),
]

# Search areas (in this order):
# 1. 检材3-1 30GB-50GB (likely TiKV / website data)
# 2. 检材3-1 28-30GB (already partially scanned)
# 3. 检材3-2 LVM region
SEARCH_AREAS = [
    (disk1, "检材3-1", 0x6FC000000, 0xC50000000, "检材3-1 LVM"),  # 27GB to 50GB
    (disk2, "检材3-2", 0x100000000, 0xF80000000, "检材3-2 LVM"),  # 4GB to 60GB
]

found = {}

for stream, label, start, end, desc in SEARCH_AREAS:
    print(f"\n=== Scanning {desc} ({(end-start)/(1024**3):.1f}GB) ===")
    out.write(f"\n=== {desc} ({(end-start)/(1024**3):.1f}GB) ===\n")
    
    last_log_g = start / (1024**3)
    for offset in range(start, end, CHUNK):
        if offset / (1024**3) - last_log_g >= 4:
            print(f"  {label}: {offset/(1024**3):.1f}GB")
            last_log_g = offset / (1024**3)
        
        stream.seek(offset)
        data = stream.read(CHUNK + 4096)
        if not data:
            break
        
        for pat, ptype in patterns_re:
            for m in pat.finditer(data):
                grp = m.group(1) if m.lastindex else m.group(0)
                if isinstance(grp, bytes):
                    grp = grp.decode('utf-8', errors='replace')[:80]
                else:
                    grp = grp.decode('utf-8', errors='replace')[:80] if isinstance(grp, bytes) else str(grp)[:80]
                key = f"{ptype}::{grp}"
                if key not in found:
                    found[key] = (offset + m.start(), label)
                    # Capture context
                    s, e = max(0, m.start()-100), min(len(data), m.end()+200)
                    ctx = data[s:e].decode('utf-8', errors='replace')
                    line = f"  [{ptype}] {grp!r} @ 0x{offset+m.start():X} ({label})"
                    print(line)
                    out.write(line + "\n")
                    out.write(f"    ctx: {ctx[:300]!r}\n")
                    out.flush()
                
                if len(found) > 500:
                    break

print(f"\n\nTotal unique findings: {len(found)}")
out.write(f"\n\nTotal: {len(found)}\n")
out.close()
print(f"Saved to: {OUT}")
