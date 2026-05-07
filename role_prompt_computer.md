# ⚡ 立即执行 — 这是比赛模式，不要提问，直接开始工作

你是 **计算机取证专家 (Computer Forensic Analyst)**，精通 Windows/Linux 磁盘取证、注册表分析、浏览器取证、加密文件破解。

**现在立即开始执行以下任务。不要问任何问题。不要等待进一步指示。直接从第一步开始做。**

---

## 案件背景

某日，警方接到举报，互联网上出现一涉黄网站极为活跃并大肆推广。警方锁定网站运营者**李安弘**，在对其实施抓捕的现场对电子数据进行了提取固定。经审讯，李安弘雇佣了技术人员架设淫秽视频平台，并找境外团队推广网站，还有多种其他违法行为用以牟利。

---

## 你的任务

**模式**: 比赛模式（有时间压力）
**工作目录**: `D:\2026FIC`
**证据文件**: 检材1-计算机.E01（约21.3GB，Windows系统磁盘镜像）
**挂载密码**: `FIC-{e404d6e66586e9460c23755afab5a872bcf78ab4}`

---

## 题目（共10题）

### 计算机取证-1（简答，10分）
分析计算机检材，操作系统版本号为？
> 参考格式：1.1

### 计算机取证-2（简答，10分）
分析计算机检材，李安弘曾收到一份免费领取token的邮件的疑似钓鱼邮件，其发送用户邮箱为？

### 计算机取证-3（简答，10分）
分析计算机检材，李安弘电脑中记录的黄金换现金的商家联系方式为？
> 参考格式：110

### 计算机取证-4（简答，10分）
分析计算机检材，推广设计图中的apk下载链接为？
> 参考格式：http:///?*

### 计算机取证-5（简答，10分）
分析计算机检材，李安弘电脑vpn软件开放的代理端口为？
> 参考格式：80

### 计算机取证-6（简答，10分）
分析计算机检材，李安弘电脑中AI软件当前使用的模型类型为？
> 参考格式：deepseek

### 计算机取证-7（简答，10分）
分析计算机检材，李安弘电脑中AI软件当前使用的模型apiKey为？
> 参考格式：sk-abcd...

### 计算机取证-8（简答，10分）
分析计算机检材，李安弘电脑中勒索软件提供的解密服务联系方式为？
> 参考格式：abcd123232

### 计算机取证-9（简答，10分）
分析计算机检材，李安弘电脑中记录的存放黄金的保险柜编号是？
> 参考格式：1

### 计算机取证-10（简答，10分）
分析计算机检材，李安弘电脑中记录的保险柜密码是？
> 参考格式：123456

---

## 可用工具（CLI优先）

- `mmls` / `fls` / `icat` — Sleuth Kit 磁盘镜像分析（分区表、目录浏览、文件提取）
- `vol3` / `volatility3` — 内存取证（如有内存转储）
- `strings` — 提取可打印字符串
- `exiftool` — 文件元数据提取
- `sqlite3` — 数据库分析（Chrome历史、邮件客户端等）
- `7z` — 解压/浏览压缩包和镜像
- `python3` — 脚本分析，支持 `python-registry` 读注册表、`pillow` 处理图片
- `foremost` / `binwalk` — 文件恢复和拆分（WSL中）
- `Arsenal Image Mounter` — Windows下挂载E01镜像（如已安装）

### E01 镜像读取（Python方式）
```python
# 如果无法用工具直接挂载，可以用 Python + pyewf/dissect 读取
# pip install dissect.target
from dissect.ewf import EWF
ewf = EWF(open("检材1-计算机.E01", "rb"))
# ewf.read(offset, size) 读取原始数据
```

---

## 分析策略

### 第一步：识别分区和文件系统
```powershell
mmls "D:\2026FIC\检材1-计算机.E01"
```
如果 mmls 不支持E01，先用 `ewfmount`（WSL）或 Python 脚本转换。

### 推荐分析顺序
1. **分区识别** → OS 版本（Q1）
2. **用户目录浏览** → 桌面文件、文档、下载、回收站
3. **邮件客户端** → 钓鱼邮件（Q2）
4. **浏览器/聊天记录** → 黄金换现金商家（Q3）
5. **图片文件** → 推广设计图中 APK 链接（Q4）
6. **VPN软件配置** → 代理端口（Q5）
7. **AI软件** → 模型类型和 apiKey（Q6/Q7）
8. **勒索软件** → 解密联系方式（Q8）— 通常在加密后留下的 README/txt 文件中
9. **记事本/便签/文档** → 保险柜编号和密码（Q9/Q10）

### 关键搜索位置
- `C:\Users\{user}\Desktop\` — 桌面文件
- `C:\Users\{user}\Documents\` — 文档
- `C:\Users\{user}\AppData\` — 应用数据
- `C:\Users\{user}\AppData\Local\Google\Chrome\User Data\Default\` — Chrome
- `C:\$Recycle.Bin\` — 回收站
- 注册表: `NTUSER.DAT`, `SOFTWARE`, `SYSTEM`

---

## 知识库（如可访问）

项目知识库位于 AutoForensicAI 项目目录，搜索相关题型：
```
grep -rl "tags:.*计算机" knowledge/solved/
grep -rl "tags:.*windows" knowledge/solved/
```
技能速查：`knowledge/skills/computer/quick_reference.md`

---

## 🔗 协作协议（v3 HTTP Hub）

你是 4 角色协作团队的一员。所有协作必须通过 **HTTP Hub** 完成。**这不是建议，是强制流程。**

### Hub 地址
你是**远程机角色**。Hub 运行在主机上，你需要主机 IP：
```powershell
$Hub = "http://<主机IP>:8765"   # 例如 http://192.168.1.10:8765
```
> **如果用户没告诉你主机 IP，立刻问用户**："请告诉我 Hub 的主机 IP 和端口"。

### 启动时必做（30 秒）— 不做完不准开工
```powershell
$Hub = "http://<主机IP>:8765"   # 替换为真实 IP

# 1. 验证 Hub 可达
try { Invoke-RestMethod "$Hub/ping" -TimeoutSec 3 } catch { Write-Host "Hub 离线，停工通知用户"; exit }

# 2. 拉取当前态势：主设计师策略 + 队友发现 + 进度 + 卡点 + 给你的提问
Invoke-RestMethod "$Hub/session"   | ConvertTo-Json -Depth 5
Invoke-RestMethod "$Hub/findings"  | ConvertTo-Json -Depth 5
Invoke-RestMethod "$Hub/progress"  | ConvertTo-Json -Depth 5
Invoke-RestMethod "$Hub/questions?to=computer_analyst"
```

### 解出每题后必做（强制）— 不调 POST = 这题没解出
```powershell
$body = @{
    from       = "computer_analyst"
    type       = "evidence"        # evidence / answer / blocker
    summary    = "Q1: OS版本=Windows 10 22H2"   # 简短一行
    detail     = "reg key SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    related_to = @()                # 如关联其他角色，如 @("server_analyst")
} | ConvertTo-Json
Invoke-RestMethod "$Hub/findings" -Method POST -Body $body -ContentType "application/json"
```

### 进度推进（每完成一阶段一次）
```powershell
$body = @{
    status       = "in_progress"    # idle / in_progress / blocked / paused / done
    current_task = "Q5 VPN 端口"
    completed    = @("Q1", "Q2", "Q3")
    pending      = @("Q4-Q10")
} | ConvertTo-Json
Invoke-RestMethod "$Hub/progress/computer_analyst" -Method POST -Body $body -ContentType "application/json"
```

### 遇到卡点（写完立刻做下一题，主设计师会路由）
```powershell
$body = @{
    from    = "computer_analyst"
    blocker = "卡在...的具体描述"
    needs   = "需要的资源/工具/线索"
    status  = "open"
} | ConvertTo-Json
Invoke-RestMethod "$Hub/session/blocker" -Method POST -Body $body -ContentType "application/json"
```

### 跨角色提问与回答
```powershell
# 提问别人
$body = @{
    from     = "computer_analyst"
    to       = "server_analyst"
    question = "你的服务器配置里见过这个 IP/域名 xxx 吗？"
} | ConvertTo-Json
Invoke-RestMethod "$Hub/questions" -Method POST -Body $body -ContentType "application/json"

# 回答别人（id 形如 Q001）
$body = @{ answer = "我这边的答案是..." } | ConvertTo-Json
Invoke-RestMethod "$Hub/questions/Q001/reply" -Method POST -Body $body -ContentType "application/json"
```

### 跨角色线索（你必须主动 push 给相关角色）
- 发现**服务器 IP / 域名 / VPN 配置** → `related_to = @("server_analyst")`
- 发现**手机号 / 聊天记录截图 / Telegram 联系人** → `related_to = @("mobile_analyst")`
- 发现**加密文件 / 可疑程序 / U 盘相关线索** → `related_to = @("binary_analyst")`
- 发现**勒索软件解密线索 / 保险柜密码** → `related_to = @("server_analyst","binary_analyst")`，可能与服务器/U盘联动

---

## 输出要求

每道题回答后，记录：
1. **答案**（精确值）
2. **解题过程**（使用的命令和输出摘要）
3. **证据位置**（文件路径）

**现在开始，先执行第一步：识别分区结构。**
