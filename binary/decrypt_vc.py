"""Decrypt vc file using the hardcoded MD5 hash as AES-128 key.

Hypothesis from binary analysis:
- Password is 16 chars
- MD5(password) is compared with hardcoded bytes at VA 0x1400023C0:
    AF B9 77 AC 24 2A D6 0C F4 24 61 AD 72 CA 51 49
- If match, the same MD5 is used as AES-128 key to decrypt vc -> VHD

If the assumption is correct, decrypting the first block should yield
"conectix" (VHD magic for cookie field at VHD footer offset 0).

VHD format note: A FIXED VHD has the 512-byte footer at the END, not the
start. So the first block of plaintext might NOT be "conectix" - we need
to check the LAST 512 bytes for VHD footer signature.
"""
from Crypto.Cipher import AES
from pathlib import Path
import hashlib

VC_PATH = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\binary\vc")
OUT_DIR = Path(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\binary")

# Hardcoded expected MD5 hash from binary VA 0x1400023C0
KEY = bytes.fromhex("afb977ac242ad60cf46124ad72ca5149")
print(f"AES key (16 bytes): {KEY.hex()}")

vc = VC_PATH.read_bytes()
print(f"vc size: {len(vc)} bytes (= {len(vc)//1024//1024} MB)")
print(f"vc[:32] cipher: {vc[:32].hex()}")
print(f"vc[-32:] cipher: {vc[-32:].hex()}")

# Try AES-128-ECB first
print("\n=== Try 1: AES-128-ECB ===")
cipher = AES.new(KEY, AES.MODE_ECB)
plain_ecb = cipher.decrypt(vc)
print(f"plain[:32]: {plain_ecb[:32].hex()}")
print(f"plain[:8] as ASCII: {plain_ecb[:8]}")
print(f"plain[-512:-504] as ASCII (VHD footer cookie): {plain_ecb[-512:-504]}")
print(f"plain[-32:] hex: {plain_ecb[-32:].hex()}")

if plain_ecb[:8] == b"conectix":
    print("\n*** ECB MATCH: Dynamic VHD header ***")
    out = OUT_DIR / "vc_decrypted.vhd"
    out.write_bytes(plain_ecb)
    print(f"Written: {out}")
elif plain_ecb[-512:-504] == b"conectix":
    print("\n*** ECB MATCH: Fixed VHD footer ***")
    out = OUT_DIR / "vc_decrypted.vhd"
    out.write_bytes(plain_ecb)
    print(f"Written: {out}")

# Try AES-128-CBC with IV=0
print("\n=== Try 2: AES-128-CBC IV=0 ===")
cipher2 = AES.new(KEY, AES.MODE_CBC, iv=b"\x00" * 16)
plain_cbc0 = cipher2.decrypt(vc)
print(f"plain[:8] as ASCII: {plain_cbc0[:8]}")
print(f"plain[-512:-504]: {plain_cbc0[-512:-504]}")

if plain_cbc0[:8] == b"conectix" or plain_cbc0[-512:-504] == b"conectix":
    print("\n*** CBC IV=0 MATCH ***")
    out = OUT_DIR / "vc_decrypted.vhd"
    out.write_bytes(plain_cbc0)
    print(f"Written: {out}")

# Try AES-128-CBC with IV = first 16 bytes of vc (some impls do this)
print("\n=== Try 3: AES-128-CBC IV=key ===")
cipher3 = AES.new(KEY, AES.MODE_CBC, iv=KEY)
plain_cbc_key = cipher3.decrypt(vc)
print(f"plain[:8]: {plain_cbc_key[:8]}")
print(f"plain[-512:-504]: {plain_cbc_key[-512:-504]}")

# Search any 8-byte aligned location for "conectix" in ECB result
print("\n=== Search 'conectix' in ECB plaintext ===")
idx = plain_ecb.find(b"conectix")
print(f"ECB: 'conectix' at offset {idx}")
idx = plain_cbc0.find(b"conectix")
print(f"CBC IV=0: 'conectix' at offset {idx}")

# Also check common file magic in ECB result
print("\n=== Common file magic in ECB plaintext head ===")
magics = {
    b"\x50\x4b\x03\x04": "ZIP/Office",
    b"\x52\x61\x72\x21": "RAR",
    b"\x37\x7a\xbc\xaf": "7z",
    b"\x4d\x5a": "PE/EXE",
    b"\x7f\x45\x4c\x46": "ELF",
    b"\x25\x50\x44\x46": "PDF",
    b"\xd0\xcf\x11\xe0": "MS Office (CFB)",
    b"\x89PNG": "PNG",
    b"\xff\xd8\xff": "JPEG",
    b"\x1f\x8b\x08": "gzip",
    b"\xfd\x37\x7a\x58": "xz",
    b"conectix": "VHD",
    b"vhdxfile": "VHDX",
    b"QFI\xfb": "qcow2",
}
for magic, name in magics.items():
    if plain_ecb.startswith(magic):
        print(f"  ECB head matches: {name}")
    if plain_cbc0.startswith(magic):
        print(f"  CBC IV=0 head matches: {name}")
