"""Recover password by AES-decrypting the expected value.

Hypothesis:
- [rsp+0x40] init bytes (16 bytes) = 01 23 45 67 89 AB CD EF 01 23 45 67 89 AB CD EF
  These are the constants 0x67452301, 0xEFCDAB89 stored as little-endian dwords.
- The cipher function (fcn.140001230) does AES_encrypt(password, [rsp+0x40] as key)
- Expected output [rsp+0x58] = AF B9 77 AC 24 2A D6 0C F4 24 61 AD 72 CA 51 49

So password = AES_decrypt(expected, key=01234567...)
"""
from Crypto.Cipher import AES

# Method 1: AES key = init buffer; expected = ciphertext; password = plaintext
init_buf = bytes.fromhex("0123456789ABCDEF" * 2)  # 16 bytes
expected = bytes.fromhex("afb977ac242ad60cf46124ad72ca5149")

print(f"init_buf (potential key): {init_buf.hex()}")
print(f"expected (potential ciphertext): {expected.hex()}")

# Try ECB decrypt
print("\n=== AES-128-ECB decrypt(expected, key=init) ===")
c = AES.new(init_buf, AES.MODE_ECB)
pt = c.decrypt(expected)
print(f"plaintext: {pt.hex()}")
print(f"as ASCII: {pt!r}")
if all(0x20 <= b <= 0x7E for b in pt):
    print("*** ALL PRINTABLE ASCII - LIKELY THE PASSWORD! ***")

# Try ECB encrypt (other direction)
print("\n=== AES-128-ECB encrypt(expected, key=init) ===")
pt2 = c.encrypt(expected)
print(f"result: {pt2.hex()}")
print(f"as ASCII: {pt2!r}")
if all(0x20 <= b <= 0x7E for b in pt2):
    print("*** ALL PRINTABLE ASCII ***")

# Try swapped: maybe init is the ciphertext and expected is the key
print("\n=== AES-128-ECB decrypt(init, key=expected) ===")
c3 = AES.new(expected, AES.MODE_ECB)
pt3 = c3.decrypt(init_buf)
print(f"plaintext: {pt3.hex()}")
print(f"as ASCII: {pt3!r}")
if all(0x20 <= b <= 0x7E for b in pt3):
    print("*** ALL PRINTABLE ASCII ***")

# Try with reverse byte order (big-endian dwords)
init_be = bytes.fromhex("67452301EFCDAB89" * 2)
print(f"\n=== Try with big-endian dword key: {init_be.hex()} ===")
c4 = AES.new(init_be, AES.MODE_ECB)
pt4 = c4.decrypt(expected)
print(f"decrypt: {pt4.hex()}")
print(f"as ASCII: {pt4!r}")
if all(0x20 <= b <= 0x7E for b in pt4):
    print("*** ALL PRINTABLE ASCII ***")

pt5 = c4.encrypt(expected)
print(f"encrypt: {pt5.hex()}")
print(f"as ASCII: {pt5!r}")
if all(0x20 <= b <= 0x7E for b in pt5):
    print("*** ALL PRINTABLE ASCII ***")

# Maybe the password is encrypted, expected is plaintext?
# i.e., expected = AES_decrypt(password, key=init)
# Then password = AES_encrypt(expected, key=init)
print("\n=== Maybe 'expected' is plaintext, password is ciphertext ===")
c6 = AES.new(init_buf, AES.MODE_ECB)
pt6 = c6.encrypt(expected)
print(f"encrypted expected w/ init key: {pt6.hex()}")
print(f"as ASCII: {pt6!r}")

# Just to be thorough: maybe both buffers are stored with a different order
# Since strncmp compares byte-by-byte, the values in memory should match exactly.
# But the immediate values in the mov instructions could be displayed in either order.
# Let me list ALL possible byte orderings of the expected hash.

print("\n=== Different interpretations of expected hash ===")
# Original little-endian dword storage:
print(f"LE dwords (current): {expected.hex()}")
# Big-endian dword storage:
import struct
dwords = struct.unpack("<IIII", expected)
expected_be = b"".join(struct.pack(">I", d) for d in dwords)
print(f"BE dwords: {expected_be.hex()}")

c7 = AES.new(init_buf, AES.MODE_ECB)
for name, e in [("LE", expected), ("BE", expected_be)]:
    for op in ("decrypt", "encrypt"):
        result = getattr(c7, op)(e)
        ascii_check = all(0x20 <= b <= 0x7E for b in result)
        marker = "  *** PRINTABLE ASCII ***" if ascii_check else ""
        print(f"  {op}({name}): {result.hex()} = {result!r}{marker}")
