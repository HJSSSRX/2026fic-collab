"""Read more of the nginx access logs to find Telegram referers and main domain."""
from pathlib import Path
from dissect.evidence.ewf import EWF
import re

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
fhs1 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-1.E0?"))]
disk1 = (EWF(*fhs1) if len(fhs1) > 1 else EWF(fhs1[0])).open()

# Read 50MB around the nginx access log area
START = 0x777000000
SIZE = 0x4000000  # 64MB

print(f"Reading 检材3-1 from 0x{START:X} to 0x{START+SIZE:X}")
disk1.seek(START)
data = disk1.read(SIZE)
print(f"Read {len(data)/(1024**2):.1f}MB")

# Extract all access log lines
text = data.decode('utf-8', errors='replace')

# Match access log pattern: IP - - [date] "METHOD URL HTTP/x" status size "referer" "ua"
log_pattern = re.compile(
    r'((?:\d+\.\d+\.\d+\.\d+|::1|[0-9a-f:]+)) - .* \[([^\]]+)\] "(\w+) ([^"]+) HTTP/[\d.]+" (\d+) (\d+) "([^"]*)" "([^"]*)"',
    re.MULTILINE
)

matches = log_pattern.findall(text)
print(f"\nFound {len(matches)} access log entries")

# Stats
domains = set()
referers = set()
status_codes = {}
methods = {}
paths = []

for ip, date, method, url, status, size, ref, ua in matches:
    methods[method] = methods.get(method, 0) + 1
    status_codes[status] = status_codes.get(status, 0) + 1
    paths.append(url)
    if ref and ref != '-':
        referers.add(ref)
        # Extract domain
        m = re.match(r'https?://([^/]+)', ref)
        if m:
            domains.add(m.group(1))

print(f"\n--- Methods ---")
for m, c in sorted(methods.items(), key=lambda x: -x[1]):
    print(f"  {m}: {c}")

print(f"\n--- Status Codes ---")
for sc, c in sorted(status_codes.items(), key=lambda x: -x[1]):
    print(f"  {sc}: {c}")

print(f"\n--- All Referer Domains ({len(domains)}) ---")
for d in sorted(domains):
    print(f"  {d}")

print(f"\n--- All unique Referers ({len(referers)}) ---")
for r in sorted(referers)[:30]:
    print(f"  {r}")

# Find paths with admin/manage/login
admin_paths = set()
for p in paths:
    if any(k in p.lower() for k in ['admin', 'manage', 'login', 'dashboard']):
        admin_paths.add(p[:200])
print(f"\n--- Admin-related paths ({len(admin_paths)}) ---")
for p in sorted(admin_paths)[:20]:
    print(f"  {p}")

# Find paths with telegram/tg/kami
suspect_paths = set()
for p in paths:
    if any(k in p.lower() for k in ['telegram', 'kami', '卡密', 'tg', 'pay', 'order']):
        suspect_paths.add(p[:200])
print(f"\n--- Suspect paths (telegram/kami/pay) ---")
for p in sorted(suspect_paths)[:30]:
    print(f"  {p}")

# Sample of all unique paths
unique_paths = sorted(set(p[:150] for p in paths))
print(f"\n--- Sample 30 unique paths (out of {len(unique_paths)}) ---")
for p in unique_paths[:30]:
    print(f"  {p}")

# Also save full text for grep
out = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\nginx_logs_dump.txt")
# Filter: keep only ASCII printable lines
clean = []
for line in text.split('\n'):
    s = line.strip()
    if 5 < len(s) < 1000 and sum(1 for c in s if c.isprintable() and ord(c) < 128) > len(s) * 0.85:
        clean.append(s)
out.write_text('\n'.join(clean), encoding='utf-8')
print(f"\nSaved {len(clean)} lines to: {out}")
