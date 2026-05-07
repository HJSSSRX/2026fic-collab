# 服务器取证进度 — 2026-05-07 14:18

## 当前状态: Phase 1 进行中（系统信息识别）

---

## 已确认的事实

### 磁盘映射
| 物理磁盘 | E01文件 | 分区表 |
|---|---|---|
| **sda** | 检材3-2.E01 (60GB) | EFI(s2048) + Swap(s393216) + sda2/LVM(s8204288) + sda3/LVM(s66797568) |
| **sdb** | 检材3-1.E01 (60GB) | sdb1/LVM(s2048) + sdb2/LVM(s58593280) |

### LVM 结构
| VG名称 | LV名称 | PV0 | PV1 | 大小 |
|---|---|---|---|---|
| **volum** | root | sda2 (检材3-2 s8204288, pe_start=2048, pe_count=7152) | sdb1 (检材3-1 s2048, pe_start=2048, pe_count=7152) | 14304 ext ≈ 56GB |
| **root** | data | sda3 (检材3-2 s66797568, pe_start=2048, pe_count=7205) | sdb2 (检材3-1 s58593280, pe_start=2048, pe_count=8207) | 15412 ext ≈ 60GB |

- **extent_size**: 8192 sectors = 4MB
- **LVM版本**: LVM2 2.03.31(2) (2025-02-27)
- **创建时间**: 2026-04-11 09:54-09:59
- **创建主机名**: `mac` (Linux mac 6.12.38+deb13-amd64, Debian 13)

### LV "root" (VG volum) 段映射
```
segment1: PE 0-7151 → pv0 (sda2, 检材3-2 part009)
segment2: PE 7152-14303 → pv1 (sdb1, 检材3-1 part002)
```

### LV "data" (VG root) 段映射
```
segment1: PE 0-8206 → pv1 (sdb2, 检材3-1 part003)
segment2: PE 8207-15411 → pv0 (sda3, 检材3-2 part010)
```

### 文件系统
- **VG volum / LV root**: PE数据区前50MB全零，**未找到任何FS签名**（无btrfs/xfs/ext4/LUKS）
- **VG root / LV data**: 在sdb2 PE区偏移 ~33MB 处发现 **BTRFS** (UUID: `2fe53132-155e-c444-b224-e29cb4201c0e`)
- 检材3-2 EFI分区: FAT16/FAT32

### 关键字符串扫描结果

#### 检材3-1 (sdb) 上的发现
| 内容 | 绝对偏移 | 所在分区 | 说明 |
|---|---|---|---|
| btrfs superblock | 0x6FE410040 (28644MB) | sdb2 (VG root) | UUID: 2fe53132-155e-c444-b224-e29cb4201c0e |
| os-release | 0x6FED41004 (28653MB) | sdb2 (VG root) | 在btrfs内 |
| docker | 0x6FF809353 (28664MB) | sdb2 (VG root) | Docker相关数据 |
| nginx | 0x6FF845D38 (28664MB) | sdb2 (VG root) | nginx安装 |
| ngrok | 0x6FF8432C4 (28664MB) | sdb2 (VG root) | ngrok二进制 |
| xfs superblock | 0x744550D12 (29765MB) | sdb2 (VG root) | 可能是Docker overlay中的XFS |

#### 检材3-2 (sda) 上的发现
| 内容 | 绝对偏移 | 所在分区 | 说明 |
|---|---|---|---|
| os-release | 0xC25A000 (194MB) | Swap分区 | **Debian GNU/Linux 13 (trixie)**, VERSION_ID="13" |
| docker | 0xC04A027 (192MB) | Swap分区 | 被换出的内存 |
| nginx | 0x1B834AFE (440MB) | Swap分区 | /var/lib/nginx 路径 |
| ngrok | 0xFDCD200D (4061MB) | sda2 (VG volum) | ngrok apt源配置 |

---

## 已解答的题目

### Q1: 操作系统版本
**答案: 13** (或 13.0)
- 来源: /etc/os-release 在swap中找到
- `PRETTY_NAME="Debian GNU/Linux 13 (trixie)"`, `VERSION_ID="13"`, `DEBIAN_VERSION_FULL=13.0`
- 参考格式 "0.9" 暗示小数 → 可能是 **13.0**

### Q16: 未被使用的文件系统
**推测答案: A (ntfs)**
- 已发现: btrfs (LV data), xfs (Docker overlay内), LVM
- swap 分区存在
- 无 NTFS 证据（纯 Linux 服务器）
- 但需要确认所有4个选项

---

## 未解决的关键问题

### 1. VG "volum" LV "root" 为何全零？
**可能原因**:
- dm-crypt plain 模式加密（无头部签名，需要密码解密）
- 挂载密码 `FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}` 可能用于此
- 需要通过 WSL 用 cryptsetup 或 losetup 尝试解密

### 2. btrfs在LV "data" 中的偏移不在PE 0
- btrfs FS 起始于 PE数据区偏移约33MB，不在 PE 0 边界
- 可能是 thin provisioning / 额外的metadata层
- 需要进一步验证偏移计算

### 3. 数据在swap中
- os-release 和 docker 引用在检材3-2的swap分区中找到
- 说明系统运行时这些数据被换出过
- swap中的数据可能包含更多线索

---

## 推荐下一步操作

### 优先级1: WSL挂载解密根文件系统
```bash
# 在WSL中:
# 1. 用ewfmount挂载E01
sudo apt install ewf-tools
sudo ewfmount /mnt/e/ffffff-JIANCAI/2026FIC团体赛/检材3-服务器/检材3-1.E01 /mnt/ewf1
sudo ewfmount /mnt/e/ffffff-JIANCAI/2026FIC团体赛/检材3-服务器/检材3-2.E01 /mnt/ewf2

# 2. 用kpartx创建LVM设备
sudo apt install lvm2 kpartx
sudo kpartx -av /mnt/ewf1/ewf1
sudo kpartx -av /mnt/ewf2/ewf1
sudo vgscan
sudo vgchange -ay

# 3. 如果LV root被加密
sudo cryptsetup open /dev/volum/root root_decrypted
# 密码: FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}

# 4. 挂载
sudo mount /dev/mapper/root_decrypted /mnt/root
# 或直接
sudo mount /dev/root/data /mnt/data
```

### 优先级2: 直接从btrfs提取文件
- 用Python读取btrfs内的文件（os-release, fstab, docker配置等）
- 需要计算正确的btrfs起始偏移

### 优先级3: 字符串暴力搜索
- 在整个磁盘上搜索更多关键字符串（fstab, docker-compose, nginx.conf等）

---

## 已创建的分析脚本
| 文件 | 用途 |
|---|---|
| `analyze_lvm.py` | 解析LVM PV/VG/LV元数据 |
| `read_lv.py` | 重组LV并检测文件系统类型 |
| `verify_offsets.py` | 验证PV偏移和扫描FS签名 |
| `check_luks.py` | 检查LUKS加密 |
| `find_root_fs.py` | 全盘字符串扫描关键文件内容 |
| `use_dissect_target.py` | 尝试用dissect.target加载（失败） |

---

## 技术环境
- Python: 3.13.13 (用 `python3` 命令)
- Python 3.8.6 (默认 `python`，不要用)
- dissect.evidence.ewf: ✓ (import路径: `from dissect.evidence.ewf import EWF`)
- dissect.target: 安装但无法直接加载E01
- sleuthkit (mmls/fls/icat): `C:\Users\44116\scoop\apps\sleuthkit\4.15.0\bin\`
- 挂载密码: `FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}`
