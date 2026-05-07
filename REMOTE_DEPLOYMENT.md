# 远程机加入协作 — v3 部署指南

> 适用：4 角色协作模式（本机 server/binary + 远程机 computer/mobile）
> Hub 版本: v3 HTTP（已废弃 GitHub 方案）

---

## 第一部分：主机用户操作（你来做）

### Step 1 启动 Hub

在 PowerShell 里执行：

```powershell
python "E:\项目\自动化取证\tools\collab_hub.py" serve "E:\ffffff-JIANCAI\2026FIC团体赛\case" --port 8765 --bind 0.0.0.0
```

启动成功的标志：

```
============================================================
  Collaboration Hub v3  -  port 8765
============================================================
  Case dir:  E:\ffffff-JIANCAI\2026FIC团体赛\case
  Bind:      0.0.0.0:8765

  Remote machines connect via:
    curl http://172.21.161.2:8765/ping
    curl http://172.27.16.1:8765/ping
    ...
```

### Step 2 找出"对的那个 IP"

启动 Hub 后会列出 4 个 IP（本机所有网卡）：

| IP 段 | 含义 | 远程机能不能连 |
|---|---|---|
| `172.21.x.x` | 物理网卡（校园/办公室网络） | ✅ 大概率能 |
| `192.168.74.x` | VMware VMnet1（虚拟网卡） | ❌ 仅本机虚拟机 |
| `192.168.223.x` | VMware VMnet8（虚拟网卡） | ❌ 仅本机虚拟机 |
| `172.27.x.x` | WSL 网卡 | ❌ 仅 WSL |

**判断方法**：让远程机 `ping <IP>`，能 ping 通的就是对的。

通常是 `172.21.x.x` 或 `192.168.x.x`（家用路由器场景）。

### Step 3 配置 Windows 防火墙（关键）

如果远程机 ping 通但 `curl http://<IP>:8765/ping` 不通，是防火墙拦了。**用管理员 PowerShell** 执行：

```powershell
New-NetFirewallRule -DisplayName "AutoForensicAI Hub 8765" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow
```

执行后从远程机重试 curl 即可。

> 如果不想动防火墙，临时方案是**关闭专用网络的 Windows Defender 防火墙**（仅限可信局域网）。

### Step 4 把 IP 告诉远程机用户

发给远程机用户：
```
Hub 地址: http://172.21.161.2:8765
（先用 ping 测试能否连通，然后用 curl http://172.21.161.2:8765/ping 确认 Hub 可达）
```

---

## 第二部分：远程机用户操作

### Step 1 验证 Hub 可达

在远程机的 PowerShell 里执行：

```powershell
$Hub = "http://172.21.161.2:8765"   # 替换为主机用户告诉你的 IP
Invoke-RestMethod "$Hub/ping"
```

期望输出：
```
status  version time
------  ------- ----
ok      v3      2026-05-07 15:30:00
```

如果失败，参见末尾「故障排查」。

### Step 2 获取你的 role_prompt

主机的 Hub 已经把 prompt 暴露成 HTTP 文件下载，远程机直接 GET：

#### 计算机取证角色（远程机1）
```powershell
Invoke-RestMethod "$Hub/files/role_prompt_computer.md" | Out-File -Encoding utf8 "D:\2026FIC\role_prompt_computer.md"
```

#### 手机取证角色（远程机2）
```powershell
Invoke-RestMethod "$Hub/files/role_prompt_mobile.md" | Out-File -Encoding utf8 "F:\电子取证\FIC2026-线上赛\role_prompt_mobile.md"
```

### Step 3 把 prompt 完整内容粘贴给 IDE AI

打开你的 IDE（Windsurf/Cursor/Claude Desktop），新建会话，把上一步下载的 `role_prompt_*.md` **整个文件内容**粘贴到对话框，然后发送。

AI 看到 prompt 后会：
1. 自动 ping 你给定的 Hub
2. 拉取当前态势（其他角色的发现、主设计师策略）
3. 开始执行第一步分析任务

> **重要**：Hub IP 在 prompt 里写的是 `<主机IP>` 占位符，你需要在粘贴时把它替换为真实 IP，或者**告诉 AI**："Hub 地址是 http://172.21.161.2:8765"。

### Step 4 实时监控（可选）

远程机用户可以在另一个 PowerShell 窗口跑：

```powershell
$Hub = "http://172.21.161.2:8765"
while ($true) {
    Clear-Host
    Write-Host "=== Progress ===" -ForegroundColor Yellow
    Invoke-RestMethod "$Hub/progress" | ConvertTo-Json -Depth 3
    Write-Host "`n=== Latest Findings ===" -ForegroundColor Yellow
    Invoke-RestMethod "$Hub/findings" | Select-Object -Last 5 | ConvertTo-Json -Depth 3
    Start-Sleep -Seconds 30
}
```

每 30 秒刷新一次，看你的 AI 和其他角色的进展。

---

## 第三部分：常见问题与故障排查

### 问题 1：远程机 ping 不通主机 IP

**原因**：不在同一局域网。
**解决**：
- 让两台机器连同一个 Wi-Fi / 路由器
- 或主机开手机热点，两台都连
- 或两台用网线直连（需配同网段静态 IP）

### 问题 2：ping 通但 curl 不通

**原因**：防火墙拦截 8765 端口。
**解决**：执行第一部分 Step 3 的防火墙规则。

### 问题 3：`Invoke-RestMethod` 报错 "无法连接到远程服务器"

**原因**：
- Hub 没启动 → 主机用户检查 Hub 进程是否还在跑
- IP 写错了 → 重新确认 Hub 启动时输出的 IP 列表

### 问题 4：POST 请求返回 400 "Invalid JSON body"

**原因**：JSON 格式有问题（PowerShell 引号转义错了）。
**解决**：用 `@{}` hashtable + `ConvertTo-Json` 而不是手写 JSON 字符串：

```powershell
# ❌ 错误：手写 JSON 容易出引号错
Invoke-RestMethod "$Hub/findings" -Method POST -Body '{"from":"computer_analyst",...}'

# ✅ 正确：用 hashtable
$body = @{ from = "computer_analyst"; summary = "..." } | ConvertTo-Json
Invoke-RestMethod "$Hub/findings" -Method POST -Body $body -ContentType "application/json"
```

### 问题 5：finding 提交了但其他角色看不到

**原因**：ID 重复或角色名拼错。
**解决**：
- 检查 `from` 字段必须是 `computer_analyst` / `mobile_analyst` / `server_analyst` / `binary_analyst` 之一
- ID 由 Hub 自动分配，不要自己写

### 问题 6：远程机 IDE AI 不会调用 Hub

**原因**：AI 看了 prompt 但没执行协作部分。
**解决**：手动告诉 AI："请先执行 prompt 里『启动时必做』的 PowerShell 命令"。

---

## 附录：完整 API 速查

```powershell
$Hub = "http://172.21.161.2:8765"   # 替换为你的 Hub IP

# 健康检查
Invoke-RestMethod "$Hub/ping"

# 拉发现 / 进度 / 答案 / 问题 / 一站式快照
Invoke-RestMethod "$Hub/findings"
Invoke-RestMethod "$Hub/findings?from=computer_analyst"
Invoke-RestMethod "$Hub/progress"
Invoke-RestMethod "$Hub/answers"
Invoke-RestMethod "$Hub/questions?to=mobile_analyst"
Invoke-RestMethod "$Hub/session"

# 提交发现
$body = @{ from="computer_analyst"; type="evidence"; summary="..."; detail="..."; related_to=@() } | ConvertTo-Json
Invoke-RestMethod "$Hub/findings" -Method POST -Body $body -ContentType "application/json"

# 更新进度
$body = @{ status="in_progress"; current_task="..."; completed=@(); pending=@() } | ConvertTo-Json
Invoke-RestMethod "$Hub/progress/computer_analyst" -Method POST -Body $body -ContentType "application/json"

# 报告卡点
$body = @{ from="computer_analyst"; blocker="..."; needs="..."; status="open" } | ConvertTo-Json
Invoke-RestMethod "$Hub/session/blocker" -Method POST -Body $body -ContentType "application/json"

# 提问/回答
$body = @{ from="computer_analyst"; to="server_analyst"; question="..." } | ConvertTo-Json
Invoke-RestMethod "$Hub/questions" -Method POST -Body $body -ContentType "application/json"

$body = @{ answer="..." } | ConvertTo-Json
Invoke-RestMethod "$Hub/questions/Q001/reply" -Method POST -Body $body -ContentType "application/json"

# 下载文件（白名单：role_prompt_*.md, shared/*.yaml）
Invoke-RestMethod "$Hub/files/role_prompt_computer.md"
Invoke-RestMethod "$Hub/files/shared/findings.yaml"
```

---

## 一句话总结

> **主机**：启动 Hub → 开防火墙 → 把 IP 告诉远程
> **远程**：ping 测试 → curl /ping → 下载 prompt → 粘给 IDE AI
