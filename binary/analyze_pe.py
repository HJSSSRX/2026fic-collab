"""Analyze SampleVC.exe - find password/encryption logic"""
import struct, re, sys

def read_pe(path):
    with open(path, 'rb') as f:
        return f.read()

def get_sections(data):
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    num_sec = struct.unpack_from('<H', data, pe+6)[0]
    opt_size = struct.unpack_from('<H', data, pe+20)[0]
    sec_start = pe + 24 + opt_size
    sections = {}
    for i in range(num_sec):
        off = sec_start + i*40
        name = data[off:off+8].rstrip(b'\x00').decode('ascii','replace')
        vsize, vaddr, rsize, roff = struct.unpack_from('<IIII', data, off+8)
        sections[name] = {'va': vaddr, 'vsize': vsize, 'roff': roff, 'rsize': rsize}
    return sections

def va_to_file(sections, va):
    """Convert RVA to file offset"""
    for name, s in sections.items():
        if s['va'] <= va < s['va'] + s['vsize']:
            return s['roff'] + (va - s['va'])
    return None

data = read_pe(r'E:\ffffff-JIANCAI\2026FIC团体赛\case\binary\SampleVC.exe')
sections = get_sections(data)
pe_off = struct.unpack_from('<I', data, 0x3C)[0]
image_base = struct.unpack_from('<Q', data, pe_off+24+24)[0]  # PE32+ ImageBase

print(f"ImageBase: 0x{image_base:X}")
for name, s in sections.items():
    print(f"  {name}: VA=0x{s['va']:X} Size=0x{s['vsize']:X} FileOff=0x{s['roff']:X}")

# Extract .text section raw bytes
text = sections['.text']
text_bytes = data[text['roff']:text['roff']+text['rsize']]

# Look for all XOR instructions with immediate values in .text
# XOR r/m8, imm8: REX? 80 modrm(reg=6) imm8
# XOR r/m32, imm32: REX? 81 modrm(reg=6) imm32
# XOR r/m32, imm8: REX? 83 modrm(reg=6) imm8
# XOR r8, r/m8: REX? 32 modrm
# XOR r32, r/m32: REX? 33 modrm
print("\n=== XOR with immediate values ===")
for i in range(len(text_bytes)-3):
    b = text_bytes[i]
    # Check for REX prefix (0x40-0x4F)
    has_rex = 0x40 <= b <= 0x4F
    opcode_idx = i+1 if has_rex else i
    if opcode_idx >= len(text_bytes)-2:
        continue
    opcode = text_bytes[opcode_idx]
    modrm = text_bytes[opcode_idx+1]
    reg_field = (modrm >> 3) & 7
    
    if opcode == 0x80 and reg_field == 6:
        imm = text_bytes[opcode_idx+2]
        va = text['va'] + i
        print(f"  0x{image_base+va:X}: xor byte ptr [...], 0x{imm:02X}")
    elif opcode == 0x83 and reg_field == 6:
        imm = text_bytes[opcode_idx+2]
        va = text['va'] + i
        if imm != 0:  # skip xor x, 0
            print(f"  0x{image_base+va:X}: xor dword ptr [...], 0x{imm:02X}")

# Look for string references - scan for LEA instructions loading .rdata addresses
# In x64, LEA uses RIP-relative: 48 8D 0D/15/05/35/3D xx xx xx xx
print("\n=== String references (LEA rip+disp to .rdata) ===")
rdata = sections['.rdata']
for i in range(len(text_bytes)-7):
    # Check for LEA with RIP-relative addressing
    b0 = text_bytes[i]
    b1 = text_bytes[i+1]
    b2 = text_bytes[i+2]
    
    if b0 in (0x48, 0x4C) and b1 == 0x8D:
        mod = (b2 >> 6) & 3
        rm = b2 & 7
        if mod == 0 and rm == 5:  # RIP-relative
            disp = struct.unpack_from('<i', text_bytes, i+3)[0]
            target_rva = text['va'] + i + 7 + disp
            if rdata['va'] <= target_rva < rdata['va'] + rdata['vsize']:
                target_foff = va_to_file(sections, target_rva)
                if target_foff:
                    s = data[target_foff:target_foff+80]
                    # Try as ASCII
                    ascii_str = ''
                    for c in s:
                        if 32 <= c < 127:
                            ascii_str += chr(c)
                        else:
                            break
                    if len(ascii_str) >= 3:
                        va = text['va'] + i
                        print(f"  0x{image_base+va:X}: lea -> 0x{target_rva:X} \"{ascii_str[:60]}\"")

# Look for interesting constants that could be crypto keys
print("\n=== Interesting constants in .data ===")
ddata = data[sections['.data']['roff']:sections['.data']['roff']+sections['.data']['rsize']]
# Look for non-zero runs
for i in range(0, len(ddata), 8):
    chunk = ddata[i:i+8]
    if any(b != 0 and b != 0xFF for b in chunk):
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32<=b<127 else '.' for b in chunk)
        va = sections['.data']['va'] + i
        print(f"  0x{va:X}: {hex_str}  {ascii_str}")

# Check the vc file header vs VHD magic "conectix"
print("\n=== VC file analysis ===")
vc = open(r'E:\ffffff-JIANCAI\2026FIC团体赛\case\binary\vc', 'rb').read()
print(f"Size: {len(vc)} bytes")
print(f"Header (32 bytes): {vc[:32].hex()}")
print(f"Footer (32 bytes): {vc[-32:].hex()}")

# VHD magic = "conectix" = 63 6f 6e 65 63 74 69 78
vhd_magic = b'conectix'
print(f"\nXOR vc[:8] with VHD magic 'conectix':")
xor_key = bytes(a^b for a,b in zip(vc[:8], vhd_magic))
print(f"  Key bytes: {xor_key.hex()} = {xor_key}")

# Also check if footer has VHD signature
print(f"\nXOR vc[-512:-504] with VHD magic:")
footer = vc[-512:]
xor_footer = bytes(a^b for a,b in zip(footer[:8], vhd_magic))
print(f"  Key bytes: {xor_footer.hex()} = {xor_footer}")

# Try repeating XOR with short keys
print(f"\nTrying single-byte XOR on vc:")
for key_byte in range(256):
    decrypted = bytes(b ^ key_byte for b in vc[:8])
    if decrypted == vhd_magic:
        print(f"  MATCH! Single byte key: 0x{key_byte:02X} = '{chr(key_byte) if 32<=key_byte<127 else '?'}'")
