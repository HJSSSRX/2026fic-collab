"""Recover the password by inverting the cipher.

Cipher (from disassembly of fcn.140001230 + sub-routines):
1. Read 16-char password as wide chars from EDIT control
2. WideCharToMultiByte CP_UTF8 -> 16 ASCII bytes (since chars are 0x20-0x7E)
3. Pre-XOR: pwd[i] ^= (3*i + 0x7F) & 0xFF
4. Standard AES-128-ECB encrypt with key = init_buffer
   - init_buffer: dwords 0x67452301, 0xEFCDAB89, 0x67452301, 0xEFCDAB89 (LE)
   - In memory: 01 23 45 67 89 AB CD EF 01 23 45 67 89 AB CD EF
5. Result compared (strncmp 16 bytes) with expected:
   - dwords 0xAC77B9AF, 0x0CD62A24, 0xAD6124F4, 0x4951CA72 (LE)
   - In memory: AF B9 77 AC 24 2A D6 0C F4 24 61 AD 72 CA 51 49

To recover password:
1. AES-128-ECB decrypt(expected, key=init_buffer)
2. result[i] ^= (3*i + 0x7F) & 0xFF
"""
from Crypto.Cipher import AES

KEY = bytes.fromhex("0123456789ABCDEF" * 2)
EXPECTED = bytes.fromhex("afb977ac242ad60cf46124ad72ca5149")

print(f"AES key:  {KEY.hex()}")
print(f"Expected: {EXPECTED.hex()}")

# Step 1: AES-128-ECB decrypt
cipher = AES.new(KEY, AES.MODE_ECB)
xored_pwd = cipher.decrypt(EXPECTED)
print(f"\nStep 1 (AES decrypt): {xored_pwd.hex()}")

# Step 2: Inverse XOR
xor_pattern = bytes((3 * i + 0x7F) & 0xFF for i in range(16))
print(f"XOR pattern: {xor_pattern.hex()}")

password = bytes(b ^ x for b, x in zip(xored_pwd, xor_pattern))
print(f"\nStep 2 (XOR): {password.hex()}")
print(f"As ASCII:     {password!r}")

# Check if all printable ASCII
all_printable = all(0x20 <= b <= 0x7E for b in password)
print(f"All printable ASCII: {all_printable}")
if all_printable:
    print(f"\n*** PASSWORD: {password.decode('ascii')} ***")

# Verify by re-encrypting
xored_check = bytes(b ^ x for b, x in zip(password, xor_pattern))
result = cipher.encrypt(xored_check)
print(f"\nVerify: re-encrypt = {result.hex()}")
print(f"Match expected: {result == EXPECTED}")
