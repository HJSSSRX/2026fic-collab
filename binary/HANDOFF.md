# 二进制取证交接文档 (2026-05-07 14:20)

## 总进度: 2/5 已解出

| 题号 | 状态 | 答案 |
|------|------|------|
| Q1 MD5 | ✅ | `764789dd9c095d74b6b258cf0f7568b2` |
| Q2 编译日期 | ✅ | `2026-04-17` |
| Q3 密码 | 🔄 80%完成 | 16字符，待破解MD5 |
| Q4 解密后缀 | ❌ | 依赖Q3 |
| Q5 收款金额 | ❌ | 依赖Q4 |

---

## Q1 — SampleVC.exe MD5 ✅

**答案**: `764789dd9c095d74b6b258cf0f7568b2`

**方法**: 从E01镜像用icat提取 → Python hashlib.md5 计算

**注意**: E01是原始NTFS卷（无分区表），mmls会失败，直接用 `fls -r` 和 `icat` 即可（offset=0）。

---

## Q2 — 编译日期 ✅

**答案**: `2026-04-17`

**方法**: Python解析PE头 IMAGE_FILE_HEADER.TimeDateStamp
```python
import struct, datetime
data = open('SampleVC.exe','rb').read()
pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
timestamp = struct.unpack_from('<I', data, pe_offset+8)[0]
dt = datetime.datetime.utcfromtimestamp(timestamp)
# → 2026-04-17 05:53:20 UTC
```

**编译环境**: MSVC 14.42 (VS2022), PE32+ x64, 无壳

---

## Q3 — 密码逆向分析 🔄 关键发现

### 已确定的程序逻辑

1. **密码长度必须恰好 16 字符**
   - 位置: VA 0x1400022C0 — `cmp rcx, 0x10; je continue`
   - 字符范围: 可打印ASCII 0x20-0x7E

2. **加密算法: AES-128**
   - AES S-box 在 file offset 0x4130
   - 加密后产出 VHD 文件（导入 VirtDisk.dll: OpenVirtualDisk, AttachVirtualDisk）

3. **密码验证流程**:
   - 输入密码 (16 wchar from EDIT control)
   - 初始化 MD5 状态: `0x67452301, 0xEFCDAB89` (VA 0x140002354)
   - 计算 MD5(password) → 16 bytes
   - 与硬编码期望值比较 (strncmp)
   - 若匹配，用 MD5 作 AES-128 key 解密 `vc` → VHD

4. **硬编码期望 MD5 哈希** (VA 0x1400023C0):
   ```
   mov dword [rsp+0x58], 0xAC77B9AF  → bytes: AF B9 77 AC
   mov dword [rsp+0x5C], 0x0CD62A24  → bytes: 24 2A D6 0C
   mov dword [rsp+0x60], 0xAD6124F4  → bytes: F4 24 61 AD
   mov dword [rsp+0x64], 0x4951CA72  → bytes: 72 CA 51 49
   mov byte  [rsp+0x68], 0x00        → null terminator
   ```
   **MD5 hex**: `afb977ac242ad60cf46124ad72ca5149`

5. **另一种可能: hex string "6595b64144ccf1df"**
   - 在 .rsrc section (file offset 0x1DE6B) 找到
   - 意义待确认

### 下一步建议 (Q3)

**方案A — 直接用期望MD5作AES key解密vc** (最可能成功)
```python
from Crypto.Cipher import AES
key = bytes.fromhex('afb977ac242ad60cf46124ad72ca5149')
vc = open('vc', 'rb').read()
# 尝试 ECB/CBC 模式
cipher = AES.new(key, AES.MODE_ECB)
dec = cipher.decrypt(vc[:16])
# 如果前8字节 == b'conectix' → VHD magic → 解密成功
```

**方案B — 破解MD5哈希找原始密码**
```powershell
# hashcat -m 0 -a 3 afb977ac242ad60cf46124ad72ca5149 ?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a?a
# 16字符可打印ASCII → 95^16 keyspace，纯暴力不可行
# 试字典: rockyou + 规则
hashcat -m 0 afb977ac242ad60cf46124ad72ca5149 rockyou.txt -r best64.rule
```

**方案C — Ghidra反编译确认逻辑**
```powershell
# Ghidra headless 反编译核心函数
analyzeHeadless . project_temp -import SampleVC.exe -postScript ExportDecompilation.java
```

**⚠️ 重要: 方案A应该最先尝试**，因为即使不知道原始密码，拿期望的MD5哈希直接作AES key就能解密文件。找到原始密码只是为了回答Q3。

---

## 文件布局

### 提取的证据
- `binary/SampleVC.exe` — 目标程序 (123392 bytes, PE32+ x64)
- `binary/vc` — 加密文件 (10,486,272 bytes = 10MB VHD)

### 分析脚本
- `binary/analyze_pe.py` — PE结构/AES S-box/MD5常量发现
- `binary/find_strings.py` — 字符串搜索/加密算法识别
- `binary/find_password.py` — 密码验证逻辑定位

### r2 输出 (部分受ANSI污染)
- `binary/r2_afl.txt` — 函数列表 (干净)
- `binary/r2_main.txt` — fcn.1400027b0 反汇编 (有ANSI码)
- `binary/r2_func1230.txt` — 失败/空
- `binary/r2_func1cf0.txt` — 失败/空

---

## 核心函数地图

| VA | Blocks | Size | 推测用途 |
|----|--------|------|----------|
| fcn.140001230 | 28 | 1307 | AES加解密 (大量byte XOR) |
| fcn.140001760 | 17 | 431 | 对话框/菜单过程 |
| fcn.140001cf0 | 47 | 1288 | WinMain / 消息循环 |
| fcn.140002200 | 20 | 670 | **密码验证+解密触发** (含MD5+strncmp) |
| fcn.1400027b0 | 43 | 1245 | VHD文件操作 (错误消息引用) |
| fcn.140002d00 | 18 | 274 | 文件I/O辅助 |
| fcn.140003000 | 34 | 455 | 对话框初始化 |

---

## 关键导入

- `strncmp` — 密码MD5比对
- `OpenVirtualDisk` / `AttachVirtualDisk` — 挂载解密后的VHD
- `CreateFileW` / `CreateFileA` — 文件操作
- `_wfopen_s` / `fwrite` — 写解密输出
- `DialogBoxParamW` / `SendMessageW` — GUI对话框

---

## 环境备注

- r2 在 PowerShell 中输出 ANSI 转义码，即使 `scr.color=0`
- 解决方案: 用 `cmd /c` 包装或直接写 Python 脚本分析二进制
- Sleuth Kit 路径: 需手动加 PATH 或用 `C:\Users\44116\scoop\shims\`
- E01 挂载密码: `FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}` (实际提取不需要)
