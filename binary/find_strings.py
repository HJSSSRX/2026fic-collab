"""Search for password/key strings in SampleVC.exe"""
import struct, re

data = open(r'E:\ffffff-JIANCAI\2026FIC团体赛\case\binary\SampleVC.exe','rb').read()

# .rdata: FileOff=0x3C00 Size=0x2A00
rdata = data[0x3C00:0x3C00+0x2A00]
skip_kw = ['std@@','dll','basic_','VCRUNTIME','MSVCP','KERNEL','USER32','api-ms',
           'COMCTL','VirtDisk','assembly','Microsoft','requestedE','security',
           'trustInfo','urn:schema','dependency','publicKeyToken','language',
           'processorArch','assemblyIdentity','dependentAssembly','win32',
           'Common-Controls','manifestVersion','standalone','encoding',
           'xml version', 'uiAccess']

print('=== ASCII strings 6+ chars in .rdata ===')
for m in re.finditer(rb'[\x20-\x7e]{6,}', rdata):
    s = m.group().decode('ascii')
    if any(skip in s for skip in skip_kw):
        continue
    off = 0x5000 + m.start()
    print(f'  RVA 0x{off:04X}: "{s}"')

print('\n=== Wide (UTF-16) strings 4+ chars in .rdata ===')
for m in re.finditer(rb'(?:[\x20-\x7e]\x00){4,}', rdata):
    chars = m.group()[::2]
    s = chars.decode('ascii')
    if any(skip in s for skip in skip_kw):
        continue
    off = 0x5000 + m.start()
    print(f'  RVA 0x{off:04X}: L"{s}"')

# Also look in .rsrc section for dialog strings
rsrc = data[0x6C00:0x6C00+0x17400]
print('\n=== Wide strings in .rsrc (dialog labels) ===')
for m in re.finditer(rb'(?:[\x20-\x7e]\x00){4,}', rsrc):
    chars = m.group()[::2]
    s = chars.decode('ascii')
    if any(skip in s for skip in skip_kw):
        continue
    off = 0xA000 + m.start()
    print(f'  RVA 0x{off:04X}: L"{s}"')

# Search for hex strings 16+ chars
print('\n=== Hex-like strings (potential passwords) ===')
for m in re.finditer(rb'[0-9a-fA-F]{16,}', data):
    s = m.group().decode('ascii')
    off = m.start()
    print(f'  FileOff 0x{off:04X}: "{s}"')

# Look for the #Eg3 string context
print('\n=== Context around "#Eg3" ===')
idx = data.find(b'#Eg3')
if idx >= 0:
    ctx = data[idx-16:idx+48]
    for i in range(0, len(ctx), 16):
        hex_str = ' '.join(f'{b:02x}' for b in ctx[i:i+16])
        ascii_str = ''.join(chr(b) if 32<=b<127 else '.' for b in ctx[i:i+16])
        print(f'  {idx-16+i:06x}: {hex_str}  {ascii_str}')

# Check for Blowfish/TEA/XTEA signatures
# Blowfish has magic Pi hex digits: 243F6A88 885A308D 313198A2 E0370734
print('\n=== Checking for known cipher constants ===')
bf_pi = bytes.fromhex('886a3f24')  # 243F6A88 in little-endian
if bf_pi in data:
    idx = data.find(bf_pi)
    print(f'  Blowfish Pi constant found at offset 0x{idx:X}!')
else:
    print('  No Blowfish Pi constant found')

# Check for AES S-box (first few bytes: 63 7c 77 7b f2 6b 6f c5)
aes_sbox = bytes([0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5])
if aes_sbox in data:
    idx = data.find(aes_sbox)
    print(f'  AES S-box found at offset 0x{idx:X}!')
else:
    print('  No AES S-box found')

# Check for DES S-box (starts with 0xe, 0x0, 0x4, 0xf, 0xd, 0x7...)
# DES initial permutation table
des_ip = bytes([58, 50, 42, 34, 26, 18, 10, 2])
if des_ip in data:
    idx = data.find(des_ip)
    print(f'  DES IP table found at offset 0x{idx:X}!')
else:
    print('  No DES IP table found')
