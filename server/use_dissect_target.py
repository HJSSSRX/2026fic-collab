"""Use dissect.target to parse E01 images with LVM support."""
import sys
from pathlib import Path

try:
    from dissect.target import Target
    print("dissect.target imported OK")
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

E01_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器")

# Try loading both E01 as a single target (two disks of same server)
e01_1 = str(E01_DIR / "检材3-1.E01")
e01_2 = str(E01_DIR / "检材3-2.E01")

print(f"\nAttempting to load: {e01_2}")
try:
    t = Target()
    t.disks.add(t._os_plugin._create_disk(open(e01_2, "rb")))
except Exception as ex:
    print(f"Method 1 failed: {ex}")

# Try official way
print("\nTrying Target.open()...")
try:
    t = Target.open(e01_2)
    print(f"  Target opened: {t}")
    print(f"  OS: {t.os}")
    print(f"  Hostname: {t.hostname}")
    print(f"  Volumes: {list(t.volumes)}")
    print(f"  Filesystems: {list(t.filesystems)}")
except Exception as ex:
    print(f"  Failed: {type(ex).__name__}: {ex}")

# Try with both disks
print("\nTrying with both E01s...")
try:
    t = Target.open(e01_1)
    print(f"  Target from E01-1: {t}")
    print(f"  Disks: {list(t.disks)}")
    print(f"  Volumes: {list(t.volumes)}")
    print(f"  Filesystems: {list(t.filesystems)}")
except Exception as ex:
    print(f"  Failed: {type(ex).__name__}: {ex}")

print("\nDone.")
