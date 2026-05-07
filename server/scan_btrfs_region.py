"""Targeted scan of btrfs region on 检材3-1 (offset 28-60GB) for config files."""
import struct
import re
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
S = 512
CHUNK = 4 * 1024 * 1024

fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()
size1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).size

# btrfs starts ~0x6FE400000 (28644MB), partition end ~0xEAA000000 (60GB area)
START = 0x6FE000000  # 28608MB - just before btrfs
END = min(size1, 0xEAA000000)

# Patterns - more focused
PATTERNS = [
    # ngrok specific
    (b'ngrok-agent', "ngrok-bin"),
    (b'.ngrok.io', "ngrok-domain"),
    (b'.ngrok-free.', "ngrok-domain"),
    (b'.ngrok.app', "ngrok-domain"),
    (b'authtoken:', "ngrok-yaml"),
    (b'tunnels:', "ngrok-yaml"),
    (b'tcp_addr', "ngrok-config"),
    (b'http_addr', "ngrok-config"),
    # Telegram
    (b't.me/', "telegram-link"),
    (b'@joinchat', "telegram-invite"),
    (b'tg://', "telegram-deeplink"),
    (b'@bot', "telegram-bot-mention"),
    (b'telegram-cli', "telegram-cli"),
    (b'tdlib', "telegram-tdlib"),
    # database / docker
    (b'mariadb', "db"),
    (b'tidb', "db"),
    (b'GuessDB', "db"),
    (b'image:', "docker-yaml"),
    (b'compose.yaml', "docker"),
    (b'docker-compose', "docker"),
    # web
    (b'admin.php', "admin"),
    (b'manage.php', "admin"),
    (b'rewrite ^', "nginx-rewrite"),
    (b'icp.miit', "icp"),
    # filesystem detection (Q16)
    (b'EXT4-fs', "kernel-ext4"),
    (b'BTRFS', "kernel-btrfs"),
    (b'XFS', "kernel-xfs"),
    (b'NTFS', "kernel-ntfs"),
]

results = {p[0]: [] for p in PATTERNS}
PROGRESS = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\scan_progress.txt")

print(f"Scanning 检材3-1 from 0x{START:X} to 0x{END:X} ({(END-START)/(1024**3):.1f}GB)")
PROGRESS.write_text(f"Started: {START:X} to {END:X}\n", encoding="utf-8")

step = (END - START) // 50
next_p = START + step

for offset in range(START, END, CHUNK):
    if offset >= next_p:
        msg = f"  {offset/(1024**3):.1f}GB / {END/(1024**3):.1f}GB"
        print(msg)
        with open(PROGRESS, 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
        next_p += step
    
    disk1.seek(offset)
    data = disk1.read(CHUNK)
    if not data:
        break
    
    for pattern, ptype in PATTERNS:
        if len(results[pattern]) >= 10:
            continue
        idx = 0
        while True:
            idx = data.find(pattern, idx)
            if idx < 0:
                break
            abs_off = offset + idx
            ctx = data[max(0, idx-150):min(len(data), idx+400)]
            results[pattern].append((abs_off, ctx))
            idx += len(pattern)
            if len(results[pattern]) >= 10:
                break

# Output
import json
print("\n" + "="*70)
print("RESULTS")
print("="*70)

for pattern, ptype in PATTERNS:
    hits = results[pattern]
    if not hits:
        continue
    print(f"\n--- {pattern!r} [{ptype}] ({len(hits)}) ---")
    for abs_off, ctx in hits[:5]:
        text = ctx.decode('utf-8', errors='replace')
        lines = [l.strip() for l in text.split('\n') 
                 if 3 < len(l.strip()) < 200 
                 and sum(1 for c in l.strip() if c.isprintable()) > len(l.strip()) * 0.7]
        print(f"  @ 0x{abs_off:X} ({abs_off/(1024**2):.1f}MB):")
        for l in lines[:5]:
            print(f"    | {l[:180]}")

# Save full
out = {}
for pattern, ptype in PATTERNS:
    pkey = pattern.decode('utf-8', errors='replace')
    out[pkey] = {
        "type": ptype,
        "count": len(results[pattern]),
        "hits": [{"offset": f"0x{o:X}", "context_hex": c[:300].hex()} for o, c in results[pattern]]
    }

Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\scan_btrfs_results.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

print("\nDone.")
PROGRESS.write_text("DONE\n", encoding="utf-8")
