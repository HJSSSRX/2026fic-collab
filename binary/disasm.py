"""Disassemble key functions of SampleVC.exe with capstone."""
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

data = open(r"E:\ffffff-JIANCAI\2026FIC团体赛\case\binary\SampleVC.exe", "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
image_base = struct.unpack_from("<Q", data, pe + 24 + 24)[0]

# .text section: file offset 0x400, VA 0x1000, size 0x3800
TEXT_OFF = 0x400
TEXT_VA = 0x1000

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
md.skipdata = True

def disasm_func(name, va, size):
    print(f"\n{'=' * 70}")
    print(f"=== {name} @ VA 0x{image_base + va:X} (size={size}) ===")
    print("=" * 70)
    foff = TEXT_OFF + (va - TEXT_VA)
    code = data[foff : foff + size]
    cur_addr = image_base + va
    for ins in md.disasm(code, cur_addr):
        ops = ins.op_str
        # Add string preview for RIP-relative LEAs
        if ins.mnemonic == "lea" and "rip" in ops.lower():
            try:
                target = ins.address + ins.size + struct.unpack(
                    "<i", ins.bytes[-4:]
                )[0]
                rva = target - image_base
                if 0x5000 <= rva < 0x7832:  # in .rdata
                    str_off = 0x3C00 + (rva - 0x5000)
                    s = data[str_off : str_off + 80]
                    txt = ""
                    for c in s:
                        if 32 <= c < 127:
                            txt += chr(c)
                        elif c == 0:
                            break
                        else:
                            txt += "."
                    if txt:
                        ops += f"  ; \"{txt[:50]}\""
            except Exception:
                pass
        # Add IAT name for CALL [rip+disp]
        if ins.mnemonic == "call" and "rip" in ops.lower():
            try:
                target = ins.address + ins.size + struct.unpack(
                    "<i", ins.bytes[-4:]
                )[0]
                rva = target - image_base
                if 0x5000 <= rva < 0x7832:
                    str_off = 0x3C00 + (rva - 0x5000)
                    iat_target = struct.unpack_from("<Q", data, str_off)[0]
                    # Print just IAT addr
                    ops += f"  ; IAT->0x{iat_target:X}"
            except Exception:
                pass
        print(f"  0x{ins.address:X}: {ins.mnemonic:8} {ops}")


# fcn.140002200 - password validation function
disasm_func("fcn.140002200 (password validation)", 0x2200, 670)

# fcn.140001230 - the cipher function
disasm_func("fcn.140001230 (cipher)", 0x1230, 1307)

# fcn.140003654 - small helper called twice
disasm_func("fcn.140003654 (helper, called twice)", 0x3654, 16)

# fcn.140001010 - AES rounds
disasm_func("fcn.140001010 (AES rounds)", 0x1010, 208)

# fcn.1400010e0 - has XOR 0x1B, MixColumns?
disasm_func("fcn.1400010e0 (MixColumns?)", 0x10E0, 325)

# fcn.140003610 - tail-called by 0x140003654
disasm_func("fcn.140003610 (helper)", 0x3610, 60)
