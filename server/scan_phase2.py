"""Phase 2 scan: ICP, DB config, suspect Telegram (not maccms), ext4 magic."""
import struct
import re
import json
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
S = 512
CHUNK = 4 * 1024 * 1024
fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()
size1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).size
size2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).size

# Patterns
PATTERNS = [
    # ICP - icp.miit.gov.cn or "ICP" in text + number patterns
    (b'icp.miit', "icp"),
    (b'\xe5\xa4\x87\xe6\xa1\x88\xe5\x8f\xb7', "icp-备案号"),  # 备案号
    (b'ICP\xe5\xa4\x87', "icp-ICP备"),
    # Database config
    (b'DB_HOST', "db-config"),
    (b'db_host', "db-config"),
    (b'database:', "db-config"),
    (b'DATABASE_URL', "db-url"),
    (b'mysql://', "db-mysql-url"),
    (b'mysqli_connect', "db-mysql-php"),
    (b'\'host\' =>', "db-php-config"),
    (b'"host" =>', "db-php-config"),
    (b'app/config/database', "db-config-file"),
    # Domain (look for primary domains used by the site)
    (b'server_name ', "nginx-server-name"),
    (b'<title>', "html-title"),
    # Telegram - look for things OTHER than maccms_channel
    (b'@JoinChatBot', "telegram-bot"),
    (b'tg://', "telegram-deeplink"),
    (b'@joinchat/', "telegram-invite"),
    (b'telegram', "telegram-generic"),
    (b'\xe5\x8d\xa1\xe5\xaf\x86', "kami-cn"),  # 卡密 UTF-8
    (b'kami', "kami-en"),
    # ext4
    (b'EXT4-fs', "kernel-ext4"),
    (b'ext4_', "ext4-internal"),
    # Admin entry
    (b'/admin.php', "admin-php"),
    (b'/manage.php', "admin-manage"),
    (b'/login.php', "admin-login"),
    (b'/admin/', "admin-path"),
    (b'$ADMIN_PATH', "admin-path-var"),
    (b'$admin_path', "admin-path-var"),
    (b"'admin_path'", "admin-path-key"),
    # site_name / site_setting
    (b'mac_site', "maccms-site"),
    (b'site_name', "site-name"),
    # Database services
    (b'mariadb', "db-mariadb"),
    (b'tidb', "db-tidb"),
    (b'GuessDB', "db-guess"),
    (b'TiDB', "db-tidb"),
    # backup db on port 4000
    (b':4000', "port-4000"),
    (b'backup', "backup-ref"),
    # rewrite rule
    (b'rewrite ^', "nginx-rewrite"),
    (b'.htaccess', "htaccess"),
]

# Filter for less common matches
results = {p[0]: [] for p in PATTERNS}
MAX_HITS = 20

def scan(stream, total_size, label):
    print(f"\n# Scanning {label} ({total_size/(1024**3):.1f}GB)")
    
    next_p = total_size // 30
    step = next_p
    
    for offset in range(0, total_size, CHUNK):
        if offset >= next_p:
            print(f"  {label}: {offset/(1024**3):.1f}GB / {total_size/(1024**3):.1f}GB")
            next_p += step
        
        stream.seek(offset)
        data = stream.read(CHUNK)
        if not data:
            break
        
        for pattern, _ in PATTERNS:
            if len(results[pattern]) >= MAX_HITS:
                continue
            idx = 0
            while idx < len(data) and len(results[pattern]) < MAX_HITS:
                idx = data.find(pattern, idx)
                if idx < 0:
                    break
                abs_off = offset + idx
                ctx = data[max(0, idx-200):min(len(data), idx+400)]
                results[pattern].append((abs_off, label, ctx))
                idx += len(pattern)

scan(disk1, size1, "检材3-1")
scan(disk2, size2, "检材3-2")

# Save to JSON
out = {}
for pattern, ptype in PATTERNS:
    pkey = pattern.decode('utf-8', errors='replace')
    out[pkey] = {
        "type": ptype,
        "count": len(results[pattern]),
        "hits": []
    }
    for abs_off, disk_name, ctx in results[pattern][:MAX_HITS]:
        # Save text + hex context
        text_lines = []
        try:
            text = ctx.decode('utf-8', errors='replace')
            for line in text.split('\n'):
                line = line.strip()
                if 3 < len(line) < 250:
                    text_lines.append(line)
        except:
            pass
        out[pkey]["hits"].append({
            "offset_hex": f"0x{abs_off:X}",
            "offset_mb": f"{abs_off/(1024*1024):.1f}",
            "disk": disk_name,
            "lines": text_lines[:10]
        })

out_file = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\phase2_results.json")
out_file.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nSaved: {out_file}")
print("Done.")
