# 服务器取证 — 交接文档 (2026-05-07 15:34)

## 角色身份
- **role**: server_analyst
- **Hub**: http://127.0.0.1:8765 (v3 HTTP Hub)
- **Git仓库**: https://github.com/HJSSSRX/2026fic-collab.git
- **case 目录**: `E:\ffffff-JIANCAI\2026FIC团体赛\case\`
- **工作目录**: `case\server\`
- **Git身份**: server_analyst <server@2026fic.local>

## 已完成进度 (3/20)

| 题号 | 答案 | 状态 |
|---|---|---|
| 服务器Q1 | OS版本 = **13.0** (Debian 13 trixie) | ✅ POST F-S002 |
| 服务器Q16 | 推测 **A. ntfs** 未被使用 | ⏳ 需 phase2 扫描确认无 ext4 |
| 互联网Q3 | ngrok域名 = **blemish-junior-unengaged.ngrok-free.dev** | ✅ POST F-S006 |

## 检材与LVM结构（已完整解析）

### 物理磁盘
| 磁盘 | E01 | 大小 | 内容 |
|---|---|---|---|
| **sda** | 检材3-2.E01 | 60GB | EFI(s2048) + Swap(s393216) + sda2/LVM(s8204288) + sda3/LVM(s66797568) |
| **sdb** | 检材3-1.E01 | 60GB | sdb1/LVM(s2048) + sdb2/LVM(s58593280) |

### LVM (跨双盘)
| VG | LV | PV0 | PV1 | 大小 |
|---|---|---|---|---|
| **volum** | root (系统盘) | sda2 (s8204288, pe_start=2048) | sdb1 (s2048, pe_start=2048) | 14304 ext = 56GB |
| **root** | data (数据盘) | sda3 (s66797568, pe_start=2048) | sdb2 (s58593280, pe_start=2048) | 15412 ext = 60GB |

- extent_size = 8192 sectors = 4MB
- 主机名: `mac` (Linux mac 6.12.38+deb13-amd64, Debian 13)
- 创建时间: 2026-04-11 09:54-09:59
- LVM2 v2.03.31

### LV "data" 段映射（btrfs文件系统）
```
segment1: PE 0-8206  → pv1 (sdb2, 检材3-1 part003)
segment2: PE 8207-15411 → pv0 (sda3, 检材3-2 part010)
```

### LV "root" 段映射（**前50MB全零，疑似加密**）
```
segment1: PE 0-7151    → pv0 (sda2, 检材3-2 part009)
segment2: PE 7152-14303 → pv1 (sdb1, 检材3-1 part002)
```

## 文件系统识别

| LV | 文件系统 | 状态 |
|---|---|---|
| LV root (VG volum) | **未知，PE区域全零** | ⛔ 阻塞中 |
| LV data (VG root) | **BTRFS** UUID=`2fe53132-155e-c444-b224-e29cb4201c0e` | ✅ 已确认 |
| 检材3-2 EFI | FAT32 | ✅ 已确认 |
| 检材3-1 内部 | XFS签名 (推测Docker overlay) at 0x744550D12 | ⏳ 待确认 |

## 阻塞点 B001（已上报Hub）

**问题**: VG "volum" / LV "root" 数据区前50MB全零，无 LUKS / btrfs / xfs / ext4 任何签名。

**需要**: WSL 环境用 ewfmount → kpartx → vgscan → cryptsetup open → mount

**密码**: `FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}`（已知）

```bash
# WSL 操作步骤
sudo apt install ewf-tools lvm2 kpartx
sudo ewfmount /mnt/e/ffffff-JIANCAI/2026FIC团体赛/检材3-服务器/检材3-1.E01 /mnt/ewf1
sudo ewfmount /mnt/e/ffffff-JIANCAI/2026FIC团体赛/检材3-服务器/检材3-2.E01 /mnt/ewf2
sudo kpartx -av /mnt/ewf1/ewf1
sudo kpartx -av /mnt/ewf2/ewf1
sudo vgscan && sudo vgchange -ay
# 如果 volum/root 直接挂载失败，尝试解密：
sudo cryptsetup open /dev/volum/root root_dec
# 用密码: FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}
sudo mount /dev/mapper/root_dec /mnt/root
sudo mount /dev/root/data /mnt/data
```

## 已发现的关键证据

### 1. 网站 = MacCMS v10 (PHP影视CMS)
- 来源: 检材3-1 0x719ACE441 提取 welcome.html
- 模板路径: `application/admin/view_new/`
- 后台路径变量: `${ADMIN_PATH}` (待确定具体值)
- 框架: layui + thinkphp
- GitHub: magicblack/maccms10
- ⚠️ **`t.me/maccms_channel` 是 MacCMS 官方频道，不是嫌疑人的群组（不要误答互联网Q1）**

### 2. ngrok 配置
- **agent authtoken**: `3CIUoZ26RGTLqfk7SS41Exw4bG0_5xHeahQZMhxn3J28BP8DV` (检材3-1 0x709A9EE68)
- **domain**: `blemish-junior-unengaged.ngrok-free.dev` (从 nginx access.log 0x7779110DB 提取)
- **server config**: `[server] http_addr=0.0.0.0, http_port=3000` (0x7BE569A49) — **自建 ngrok 服务器！**
- 推测嫌疑人架设了**自定义 ngrok 服务**，用于反向代理网站

### 3. 网络配置
- eth0: `1.1.1.1/24` 和 `2001:cafe:face::1/64` (0x7F1F5FCB3) — 测试地址
- WireGuard: `wg0 server, addresses: [10.10.10.20/24]` (0x7F3054C18)

### 4. 全盘字符串扫描发现（位置）
| 内容 | 检材3-1 偏移 | 说明 |
|---|---|---|
| btrfs superblock | 0x6FE410040 (28644MB) | LV data 主超级块 |
| os-release (Debian13) | 0x6FED41004 | 在btrfs内部 |
| docker | 0x6FF809353 | docker相关 |
| nginx | 0x6FF845D38 | nginx安装 |
| ngrok二进制 | 0x6FF8432C4 | /usr/local/bin/ngrok |
| ngrok agent yml | 0x709A9EE68, 0x709C6A61E, 0x709EA2E68 | 多个备份 |
| nginx access.log | 0x7779110DB (30585MB) | 含ngrok域名 |
| ngrok server cfg | 0x7BE569A49 (31717MB) | http_addr/port |
| MacCMS welcome.html | 0x719ACE441 (29082MB) | 后台模板 |
| netplan eth0 | 0x7F1F5FCB3 (32543MB) | 网络配置 |
| WireGuard wg0 | 0x7F3054C18 (32560MB) | VPN隧道 |
| XFS签名 | 0x744550D12 (29765MB) | 可能Docker overlay |
| HSTS hostname list | 0x6FF8437BF | mirror.nyist.edu.cn |

| 内容 | 检材3-2 偏移 | 说明 |
|---|---|---|
| os-release | 0xC25A000 (194MB) | swap分区中 |
| docker | 0xC04A027 (192MB) | swap中 |
| nginx路径 | 0x1B834AFE (440MB) | swap中 |
| ngrok apt源 | 0xFDCD200D (4061MB) | sda2 LVM区，apt源配置 |

## 待解题目（17题）

### 依赖 LVM 解密 (B001 解除后可做)
- **Q2**: 根分区UUID
- **Q3**: 最新docker镜像创建时间 (timestamp)
- **Q4**: 根分区快照路径 (btrfs subvolume)
- **Q5**: 网站后台管理入口文件名 (找 `${ADMIN_PATH}` 的实际值)
- **Q6**: 网站ICP备案号
- **Q7**: 网站主域名
- **Q8**: 分类3的视频拼音
- **Q9**: 站点设置页面前端模板源文件
- **Q10**: 伪静态规则配置文件 sm3 哈希
- **Q11**: 数据库IP地址
- **Q12**: 数据库容器技术 (docker?)
- **Q13**: 4000端口备份数据库版本号
- **Q14**: 新注册用户数量最多日期
- **Q15**: 马慧美最后登录IP
- **Q17**: 数据库服务列表 (多选: mysql/GuessDB/tidb/postgresql/mariadb)

### 不依赖 LVM (可继续)
- **Q16**: 未被使用的文件系统 → 推测 **A. ntfs**（待 phase2 确认无 ext4）
- **互联网Q1**: 售卖卡密的公开群组ID（@开头格式）
- **互联网Q2**: 备份数据库中视频图片的文件名

## 后台扫描进程（仍在运行）

```
PID 121032 (python3.13, 启动 15:28:21): scan_phase2.py 
  - 扫描 ICP/DB配置/Telegram/ext4/admin/数据库服务
  - 输出: case/server/phase2_results.json (尚未生成)
  - 日志: case/server/phase2_log.txt (Out-File 缓冲中)

PID 127600 (python3.13, 启动 15:19:21): hunt_strings.py 
  - 已 Tee-Object 完成但 Python 进程未退出
  - 内存占用 6.6GB，可安全 Stop-Process
```

**等待 phase2 结果**：完成后会生成 `case/server/phase2_results.json`，包含 `EXT4-fs/卡密/admin.php/数据库` 等关键搜索结果。

## 已上报到 Hub 的 findings

| ID | 类型 | 摘要 |
|---|---|---|
| F-S001 | evidence | 磁盘映射: sda=检材3-2, sdb=检材3-1, 两个VG跨双盘 |
| F-S002 | answer | Q1: OS = Debian 13 trixie (13.0) |
| F-S003 | evidence | LV data btrfs确认; LV root 加密未确认 |
| F-S004 | evidence | 服务器装了docker/nginx/ngrok/postgresql |
| F-S005 | blocker | 需WSL挂载LVM+解密 |
| F-S006 | answer | 互联网Q3: ngrok = blemish-junior-unengaged.ngrok-free.dev |
| F-S007 | evidence | 网站CMS = MacCMS v10 |

## 下一个 AI 接手指南

### 启动时必做（30秒）
```powershell
$Hub = "http://127.0.0.1:8765"
Invoke-RestMethod "$Hub/ping"
Invoke-RestMethod "$Hub/session"  | ConvertTo-Json -Depth 5
Invoke-RestMethod "$Hub/findings" | ConvertTo-Json -Depth 5
Invoke-RestMethod "$Hub/progress" | ConvertTo-Json -Depth 5
Invoke-RestMethod "$Hub/questions?to=server_analyst"
```

### 优先做的事
1. **检查 phase2_results.json 是否已生成** → 看是否有 ext4 / kami / admin.php 等关键命中
2. **POST findings**: 任何新答案都通过 `POST $Hub/findings`
3. **POST progress**: 阶段性更新 `POST $Hub/progress/server_analyst`
4. **检查B001状态**: 主设计师可能已用 WSL 协助解密
5. **不要误答**: `t.me/maccms_channel` 是 CMS 官方频道，不是 Q1 答案
6. **不要重做的题**: Q1, 互联网Q3 已答（见上表）

### 关键脚本（已写）
| 脚本 | 用途 |
|---|---|
| `analyze_lvm.py` | 解析LVM元数据 |
| `read_lv.py` | 重组LV |
| `verify_offsets.py` | 验证PV偏移 |
| `check_luks.py` | 检查LUKS |
| `find_root_fs.py` | 全盘字符串扫描 |
| `hunt_strings.py` | 多字符串搜索（崩溃于Unicode） |
| `scan_btrfs_region.py` | btrfs区域扫描（崩溃于Unicode） |
| `scan_phase2.py` | **运行中** ICP/DB/Telegram扫描 |
| `read_ngrok_config.py` | 读取ngrok配置具体内容 |

### 已知坑
- **PowerShell 与 Python 编码冲突**: GBK 默认 codec 无法编码 `\ufffd`。在 print 前 `$env:PYTHONIOENCODING="utf-8"` 或用 try/except。
- **EWF 接口**: `from dissect.evidence.ewf import EWF`（不是 `dissect.ewf`），用 `ewf.open()` 获取 stream。
- **dissect.target 无法直接加载E01**: 需要先 ewfmount。
- **LV 重组验证**: `read_lv.py` 中读 LV 0x10000 处仍返回零，说明 LV root 真的全零。

## 技术环境
- Python 3.13.13: 用 `python3` 命令（**不要用 `python`，那是 3.8.6**）
- sleuthkit: `C:\Users\44116\scoop\apps\sleuthkit\4.15.0\bin\`
- WSL Ubuntu: 用户 `hjsssr`，密码在 `E:\项目\psw` 第一行

## 协作上下文（来自Hub session）

主设计师当前 strategy.priorities：
1. binary_analyst: F-B003 已分析出可用期望MD5作AES key，但 progress 仍 paused，需推动
2. server_analyst: B001 等待主设计师本机用WSL协助解密
3. computer_analyst / mobile_analyst: 远程机尚未加入Hub
