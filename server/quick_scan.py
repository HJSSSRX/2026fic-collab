"""Fast targeted scan: ext4 magic + Telegram (excluding maccms) + 卡密 + admin entry."""
import struct
import json
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
S = 512
CHUNK = 8 * 1024 * 1024  # 8MB - faster

fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()
size1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).size
size2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).size

# Output file - written incrementally
OUT = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\quick_scan_results.txt")

# Patterns
patterns = [
    # ext4 - look for typical kernel string and config evidence
    (b'EXT4-fs (', "ext4-kernel-msg"),
    (b'ext4 filesystem', "ext4-doc"),
    (b'TYPE="ext4"', "blkid-ext4"),
    (b'/etc/fstab', "fstab-ref"),
    # Telegram - exclude maccms_channel
    (b'https://t.me/', "telegram-link"),
    (b'tg://resolve?domain=', "telegram-domain"),
    (b'telegram_bot_token', "telegram-bot-cfg"),
    # 卡密
    (b'\xe5\x8d\xa1\xe5\xaf\x86', "kami-utf8"),
    # admin entry  
    (b'/admin.php', "admin-php"),
    (b'/manage.php', "manage-php"),
    (b'/login.php', "login-php"),
    # Site config
    (b'mac_site_url', "maccms-url"),
    (b'site_url', "site-url"),
    (b'app_url', "app-url"),
    # ICP
    (b'icp.miit.gov.cn', "icp-link"),
    (b'\xe6\xb2\xaa\xe5\x86\x96', "icp-沪icp-shanghai"),  # 沪ICP
    (b'\xe4\xba\xacICP', "icp-京ICP"),  # 京ICP
    (b'\xe7\xb2\xa4ICP', "icp-粤ICP"),  # 粤ICP
    # database services 
    (b'tidb-server', "db-tidb"),
    (b'mariadbd', "db-mariadb"),
    (b'GuessDB', "db-guess"),
    # Domain config
    (b'server_name ', "nginx-vhost"),
    (b'$_SERVER[\'HTTP_HOST\']', "php-host"),
]

total_size_g = (size1 + size2) / (1024**3)
print(f"Total: {total_size_g:.1f}GB to scan")

results = {p[0]: [] for p in patterns}

def write_results():
    """Incremental write."""
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(f"# Quick scan results (live updating)\n\n")
        for pat, ptype in patterns:
            hits = results[pat]
            if not hits:
                continue
            f.write(f"\n## {pat!r} [{ptype}] ({len(hits)} hits)\n")
            for off, disk_name, ctx in hits[:8]:
                f.write(f"\n### @ 0x{off:X} ({off/(1024**2):.1f}MB) on {disk_name}\n```\n")
                # Extract printable strings
                text = ctx.decode('utf-8', errors='replace')
                for line in text.split('\n')[:8]:
                    line = line.strip()
                    if 4 < len(line) < 200:
                        f.write(f"{line}\n")
                f.write("```\n")

def scan(stream, total, label):
    print(f"\n--- Scanning {label} ({total/(1024**3):.1f}GB) ---")
    last_log = 0
    for offset in range(0, total, CHUNK):
        # Progress every 5GB
        if offset - last_log >= 5*(1024**3):
            print(f"  {label}: {offset/(1024**3):.1f}GB")
            last_log = offset
            write_results()  # incremental dump
        
        stream.seek(offset)
        data = stream.read(CHUNK + 1024)  # overlap
        if not data:
            break
        
        for pat, _ in patterns:
            if len(results[pat]) >= 50:
                continue
            idx = 0
            while idx < len(data) and len(results[pat]) < 50:
                idx = data.find(pat, idx)
                if idx < 0:
                    break
                abs_off = offset + idx
                ctx = data[max(0, idx-150):min(len(data), idx+400)]
                results[pat].append((abs_off, label, ctx))
                idx += len(pat)

scan(disk1, size1, "检材3-1")
scan(disk2, size2, "检材3-2")
write_results()
print(f"\nDone. Results: {OUT}")
