"""Find password comparison logic and try to decrypt vc file"""
import struct, re, hashlib

data = open(r'E:\ffffff-JIANCAI\2026FIC团体赛\case\binary\SampleVC.exe','rb').read()
pe = struct.unpack_from('<I', data, 0x3C)[0]
image_base = struct.unpack_from('<Q', data, pe+24+24)[0]

# Find IAT entry for strncmp
# The import is from api-ms-win-crt-string-l1-1-0.dll
# IAT entries are in .rdata section
# Let's find all CALL instructions that reference strncmp

# First find "strncmp" string in import table
strncmp_idx = data.find(b'strncmp\x00')
print(f'strncmp string at file offset 0x{strncmp_idx:X}')

# Search .text section for CALL [rip+disp] patterns (FF 15 xx xx xx xx)
text_off = 0x400
text_size = 0x3800
text_va = 0x1000
text_bytes = data[text_off:text_off+text_size]

# Also search for all function call references
print('\n=== Looking for strncmp call sites ===')
# Find all FF 15 (call [rip+disp]) in .text
for i in range(len(text_bytes) - 6):
    if text_bytes[i] == 0xFF and text_bytes[i+1] == 0x15:
        disp = struct.unpack_from('<i', text_bytes, i+2)[0]
        target_rva = text_va + i + 6 + disp
        # The IAT should point to the function
        target_foff = 0x3C00 + (target_rva - 0x5000) if 0x5000 <= target_rva < 0x7832 else None
        if target_foff and 0 <= target_foff < len(data):
            # Check if this IAT entry name hints at strncmp
            # IAT entries contain addresses, but we can check the import lookup table
            pass

# Alternative: look for direct references to strncmp
# Let's search for the pattern that would reference strncmp IAT
# Instead, let me just disassemble around the MD5 init to find the password check

# The MD5 init constants are at file offset 0x1754-0x177C
# This is in function fcn.140001760 (dialog proc?)
# VA = 0x1000 + (0x1754 - 0x400) = 0x1000 + 0x1354 = 0x2354
# Wait, that's wrong. Let me recalculate.
# File offset 0x1754, .text starts at file offset 0x400 with VA 0x1000
# VA = 0x1000 + (0x1754 - 0x400) = 0x1000 + 0x1354 = 0x2354
md5_init_va = 0x1000 + (0x1754 - 0x400)
print(f'MD5 init constants at VA 0x{image_base + md5_init_va:X}')

# Dump the context around MD5 init more broadly
print('\n=== Code context around MD5 init (file offset 0x1730-0x17F0) ===')
for i in range(0x1730, 0x17F0, 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32<=b<127 else '.' for b in chunk)
    va = 0x1000 + (i - 0x400) + image_base
    print(f'  {va:016X}: {hex_str}  {ascii_str}')

# Now let's look at what's BEFORE the MD5 init - the password reading/checking
print('\n=== Code before MD5 init (file offset 0x16C0-0x1760) ===')
for i in range(0x16C0, 0x1760, 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32<=b<127 else '.' for b in chunk)
    va = 0x1000 + (i - 0x400) + image_base
    print(f'  {va:016X}: {hex_str}  {ascii_str}')

# Look for immediate string loads before MD5 init - these could be the password
# Search for LEA instructions that load .rdata addresses in this area
print('\n=== LEA to .rdata in range 0x1600-0x1800 ===')
for i in range(0x1600-0x400, 0x1800-0x400):
    if i+7 > len(text_bytes):
        break
    b0, b1, b2 = text_bytes[i], text_bytes[i+1], text_bytes[i+2]
    if b0 in (0x48, 0x4C) and b1 == 0x8D:
        mod = (b2 >> 6) & 3
        rm = b2 & 7
        if mod == 0 and rm == 5:  # RIP-relative
            disp = struct.unpack_from('<i', text_bytes, i+3)[0]
            target_rva = text_va + i + 7 + disp
            if 0x5000 <= target_rva < 0x7832:
                target_foff = 0x3C00 + (target_rva - 0x5000)
                s = data[target_foff:target_foff+80]
                ascii_str = ''
                for c in s:
                    if 32 <= c < 127:
                        ascii_str += chr(c)
                    else:
                        break
                va = text_va + i + image_base
                print(f'  0x{va:X}: lea -> RVA 0x{target_rva:X}: "{ascii_str[:60]}"')

# The password check might use strncmp with a hardcoded string
# Let me look for all string references in .rdata that are short (8-32 chars)
# and don't look like error messages
print('\n=== Short non-error strings in .rdata ===')
rdata = data[0x3C00:0x3C00+0x2A00]
for m in re.finditer(rb'[\x20-\x7e]{4,40}', rdata):
    s = m.group().decode('ascii')
    if any(k in s.lower() for k in ['fail','error','bad ','string ','unknown','.text','.rdata','.data','.crt','.rtc','.xdata','.idata','.pdata','.rsrc','.bss','.00cfg','_std_','_cxx','alloc','exception','noreturn','@std','char_traits','ostream','streambuf','basic_','ios_base','widen','setstate','flush','sput','length','terminate','msvcp','vcrun','kernel','user32','comctl','virtdisk','openvi','attachvi','detachvi','getvi','init','memo','wide','create','getlast','close','getfile','end','begin','update','dialog','system','post','load','translate','dispatch','show','register','send','message','destroy','defwindow','getmessage','seh_','set_','__p_','_c_exit','_cexit','_init','_register','_config','_get_wide','?_X','?uncaught','?wcout','?cerr','?_Osfx','?good','remove','fclose','fwrite','fread','_wfopen','wcscpy','wcscat','strncmp','callnew','malloc','free']):
        continue
    off = 0x5000 + m.start()
    print(f'  RVA 0x{off:04X} ({len(s)} chars): "{s}"')

# Look for wide string constants that could be passwords
print('\n=== Wide strings in .rdata (potential passwords) ===')
for m in re.finditer(rb'(?:[\x21-\x7e]\x00){4,32}\x00\x00', rdata):
    chars = m.group()[:-2:2]
    try:
        s = chars.decode('ascii')
    except:
        continue
    if any(k in s.lower() for k in ['fail','error','vhd','edit','button','path']):
        continue
    off = 0x5000 + m.start()
    print(f'  RVA 0x{off:04X}: L"{s}"')

# Finally, let's try the mount password as AES key
print('\n=== Trying mount password as decryption key ===')
mount_pw = b'FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}'
md5_key = hashlib.md5(mount_pw).digest()
print(f'MD5("{mount_pw.decode()}") = {md5_key.hex()}')

# Try AES-128-ECB decryption of first 16 bytes of vc
try:
    from Crypto.Cipher import AES
    vc = open(r'E:\ffffff-JIANCAI\2026FIC团体赛\case\binary\vc', 'rb').read()
    cipher = AES.new(md5_key, AES.MODE_ECB)
    dec = cipher.decrypt(vc[:16])
    print(f'AES-ECB decrypt first block: {dec.hex()} = {dec[:8]}')
    if dec[:8] == b'conectix':
        print('*** VHD MAGIC MATCH! Password is the mount password! ***')
    
    # Also try AES-CBC with IV=0
    cipher2 = AES.new(md5_key, AES.MODE_CBC, iv=b'\x00'*16)
    dec2 = cipher2.decrypt(vc[:16])
    print(f'AES-CBC(iv=0) decrypt: {dec2.hex()} = {dec2[:8]}')
    if dec2[:8] == b'conectix':
        print('*** VHD MAGIC MATCH with CBC! ***')
except Exception as e:
    print(f'Crypto error: {e}')
