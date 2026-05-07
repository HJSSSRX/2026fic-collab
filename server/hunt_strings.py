"""Targeted string hunt: ngrok config, Telegram group, ext4 superblocks, web markers."""
import struct
import re
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
S = 512
CHUNK = 4 * 1024 * 1024  # 4MB

fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()
size1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).size
size2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).size

print(f"disk1 size: {size1/(1024**3):.2f}GB")
print(f"disk2 size: {size2/(1024**3):.2f}GB")

# Patterns to hunt (with context type)
PATTERNS = [
    # ngrok config
    (b'tunnels:', "ngrok-yaml"),
    (b'authtoken', "ngrok-yaml"),
    (b'.ngrok.io', "ngrok-domain"),
    (b'.ngrok-free.', "ngrok-domain"),
    (b'.ngrok.app', "ngrok-domain"),
    # Telegram
    (b't.me/', "telegram-link"),
    (b'telegram', "telegram-ref"),
    (b'@joinchat', "telegram-invite"),
    (b'TG-', "telegram-ref"),
    (b'telegram-bot', "telegram-bot"),
    # Telegram group/channel ID format @xxx
    (b'@bot', "telegram-bot"),
    # Web/admin
    (b'admin.php', "admin-entry"),
    (b'manage.php', "admin-entry"),
    (b'login.php', "admin-entry"),
    # icp
    (b'\xe5\xa4\x87\xe6\xa1\x88', "icp-备案"),  # 备案
    (b'beian', "icp-beian"),
    (b'icp.miit.gov.cn', "icp-link"),
    # nginx/apache config
    (b'server_name', "nginx-config"),
    (b'rewrite ', "nginx-rewrite"),
    # docker
    (b'docker-compose', "docker-compose"),
    (b'image:', "docker-image"),
    (b'mariadb', "db-mariadb"),
    (b'tidb', "db-tidb"),
    (b'guessdb', "db-guess"),
    (b'GuessDB', "db-guess"),
    # 4000 port (备份数据库)
    (b'4000', "port-4000"),
    # USDT
    (b'USDT', "crypto-usdt"),
    (b'TRC20', "crypto-trc"),
    # ICP icp123 typical format ICP备123456号
    (b'\xe5\xa4\x87', "ICP-prefix"),
]

# Output: for each pattern, find first 5 occurrences with context
results = {}
for pattern, _ in PATTERNS:
    results[pattern] = []

def scan(stream, disk_name, total_size, max_per_pattern=5):
    print(f"\n{'#'*60}\n# Scanning {disk_name} ({total_size/(1024**3):.1f}GB)\n{'#'*60}")
    
    # Track which patterns we still need to find on this disk
    needed = {p: True for p, _ in PATTERNS}
    
    progress_step = total_size // 20
    next_progress = progress_step
    
    for offset in range(0, total_size, CHUNK):
        if not any(needed.values()):
            print(f"  All patterns hit max on {disk_name}, stopping at {offset/(1024**3):.1f}GB")
            break
        
        if offset >= next_progress:
            print(f"  ... {offset/(1024**3):.1f}GB scanned")
            next_progress += progress_step
        
        stream.seek(offset)
        data = stream.read(CHUNK)
        if not data:
            break
        
        for pattern, ptype in PATTERNS:
            if not needed[pattern]:
                continue
            start = 0
            while True:
                idx = data.find(pattern, start)
                if idx < 0:
                    break
                abs_off = offset + idx
                ctx_start = max(0, idx - 100)
                ctx_end = min(len(data), idx + 400)
                ctx = data[ctx_start:ctx_end]
                results[pattern].append((abs_off, disk_name, ctx))
                start = idx + len(pattern)
                if len(results[pattern]) >= max_per_pattern * 2:
                    needed[pattern] = False
                    break

scan(disk1, "检材3-1", size1)
scan(disk2, "检材3-2", size2)

# Print results by category
print("\n\n" + "="*70)
print("RESULTS BY PATTERN")
print("="*70)

for pattern, ptype in PATTERNS:
    hits = results[pattern]
    if not hits:
        continue
    print(f"\n--- '{pattern!r}' [{ptype}] ({len(hits)} hits) ---")
    for abs_off, disk_name, ctx in hits[:5]:
        text = ctx.decode('utf-8', errors='replace')
        # Filter out non-printable garbage; keep only reasonable lines
        clean_lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            if 3 < len(stripped) < 200 and sum(1 for c in stripped if c.isprintable()) / len(stripped) > 0.7:
                clean_lines.append(stripped)
        print(f"  [{disk_name}] @ 0x{abs_off:X} ({abs_off/(1024**2):.1f}MB):")
        for l in clean_lines[:6]:
            print(f"    | {l[:180]}")

# Save raw results to file for later analysis
import json
out = {}
for pattern, ptype in PATTERNS:
    pkey = pattern.decode('utf-8', errors='replace')
    out[pkey] = {
        "type": ptype,
        "hits": [{"offset": f"0x{o:X}", "disk": d, "context_hex": c[:200].hex()} for o,d,c in results[pattern][:10]]
    }

out_path = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\hunt_results.json")
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nSaved to: {out_path}")
