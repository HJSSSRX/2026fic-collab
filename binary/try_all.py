"""Try all algorithm combinations to recover the password."""
from Crypto.Cipher import AES

KEY = bytes.fromhex("0123456789ABCDEF" * 2)
EXPECTED = bytes.fromhex("afb977ac242ad60cf46124ad72ca5149")
xor_pat = bytes((3 * i + 0x7F) & 0xFF for i in range(16))

cipher = AES.new(KEY, AES.MODE_ECB)

def show(name, data):
    ascii_ok = all(0x20 <= b <= 0x7E for b in data)
    marker = "  *** PRINTABLE ASCII ***" if ascii_ok else ""
    print(f"  {name}: {data.hex()}  {data!r}{marker}")
    return ascii_ok

print("Attempting recoveries:")

# Standard: pwd -> XOR -> AES_enc = expected
# Recover: pwd = (AES_dec(expected)) XOR pat
r1 = bytes(b ^ x for b, x in zip(cipher.decrypt(EXPECTED), xor_pat))
show("AES_dec ^ XOR_pat (forward)", r1)

# Reverse direction: pwd -> AES_dec -> XOR = expected
# Recover: pwd = AES_enc(expected XOR pat)
r2 = cipher.encrypt(bytes(b ^ x for b, x in zip(EXPECTED, xor_pat)))
show("AES_enc(expected ^ pat)", r2)

# pwd -> XOR -> AES_dec = expected  =>  pwd = AES_enc(expected) ^ pat
r3 = bytes(b ^ x for b, x in zip(cipher.encrypt(EXPECTED), xor_pat))
show("AES_enc ^ pat", r3)

# pwd -> AES_enc -> XOR = expected  =>  pwd = AES_dec(expected ^ pat)
r4 = cipher.decrypt(bytes(b ^ x for b, x in zip(EXPECTED, xor_pat)))
show("AES_dec(expected ^ pat)", r4)

# Just AES (no XOR)
show("AES_dec only", cipher.decrypt(EXPECTED))
show("AES_enc only", cipher.encrypt(EXPECTED))

# Just XOR (no AES)
show("expected ^ pat", bytes(b ^ x for b, x in zip(EXPECTED, xor_pat)))

# Maybe the key bytes are reversed or different ordering
KEY_REV = KEY[::-1]
cipher_rev = AES.new(KEY_REV, AES.MODE_ECB)
show("rev key, AES_dec ^ pat", bytes(b ^ x for b, x in zip(cipher_rev.decrypt(EXPECTED), xor_pat)))
show("rev key, AES_dec only", cipher_rev.decrypt(EXPECTED))

# What if expected bytes are in a different order? Try reversed
EXPECTED_REV = EXPECTED[::-1]
show("AES_dec(expected_reversed) ^ pat", bytes(b ^ x for b, x in zip(cipher.decrypt(EXPECTED_REV), xor_pat)))

# What if the XOR pattern is different? E.g., 3i + 0xAC (running BACKWARD from end)
xor_pat2 = bytes((3 * (15 - i) + 0x7F) & 0xFF for i in range(16))
print(f"\nAlternate XOR pattern (reversed): {xor_pat2.hex()}")
show("AES_dec ^ pat2", bytes(b ^ x for b, x in zip(cipher.decrypt(EXPECTED), xor_pat2)))

# Maybe the SIMD path uses a different formula
# Loop processed 4-byte groups: maybe (4*i + 0x7F) or (i*0x10 + 0x7F) etc.
for mult, add in [(1, 0x7F), (2, 0x7F), (4, 0x7F), (3, 0xAC), (3, 0x80), (3, 0x70)]:
    p = bytes((mult * i + add) & 0xFF for i in range(16))
    r = bytes(b ^ x for b, x in zip(cipher.decrypt(EXPECTED), p))
    if all(0x20 <= b <= 0x7E for b in r):
        print(f"  *** mult={mult} add={hex(add)}: {r!r} ***")
