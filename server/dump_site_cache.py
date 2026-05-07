"""Dump full MacCMS site cache PHP config from disk."""
from pathlib import Path
from dissect.evidence.ewf import EWF

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")
fhs2 = [open(f, "rb") for f in sorted(E01_DIR.glob("检材3-2.E0?"))]
disk2 = (EWF(*fhs2) if len(fhs2) > 1 else EWF(fhs2[0])).open()

# offset 0x267D701CE on 检材3-2
START = 0x267D70000  # back up some
SIZE = 0x10000  # 64KB

disk2.seek(START)
data = disk2.read(SIZE)
text = data.decode('utf-8', errors='replace')

print(f"=== Reading 检材3-2 0x{START:X} - 0x{START+SIZE:X} ===\n")

# Find PHP array start
idx = text.find('return array')
if idx < 0:
    idx = text.find("'site'")
    if idx > 100:
        # back up to find array start
        scan_from = idx
        for i in range(scan_from, max(0, scan_from-2000), -1):
            if text[i:i+5] == 'array' or text[i:i+13] == 'return array':
                idx = i
                break

# Print context around config
if idx >= 0:
    end = idx + 8000
    if end > len(text):
        end = len(text)
    section = text[max(0, idx-200):end]
    # Find a sensible end (PHP closing)
    end_marker = section.find("\x00\x00\x00\x00")
    if end_marker > 0:
        section = section[:end_marker]
    print(section)
else:
    print("'site' not found, dumping raw text:")
    print(text[:5000])

# Save for grep
out = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\server\site_cache_dump.txt")
out.write_text(text, encoding='utf-8')
print(f"\n\n[Saved {len(text)} bytes to {out}]")
