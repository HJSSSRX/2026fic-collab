# 🔗 协作部署指令 — 服务器取证角色（本机）

**立即执行以下步骤，部署 Git 协作同步。不要提问，按顺序做。**

本机 case 目录就是 Git 仓库本身，无需克隆，只需配置。

## 步骤1：配置 Git 身份

```powershell
cd "E:\ffffff-JIANCAI\2026FIC团体赛\case"
git config user.name "server_analyst"
git config user.email "server@2026fic.local"
```

## 步骤2：确认仓库状态

```powershell
cd "E:\ffffff-JIANCAI\2026FIC团体赛\case"
git remote -v
git log --oneline -1
```

应看到 `origin → https://github.com/HJSSSRX/2026fic-collab.git`

## 步骤3：协作流程

### 拉取最新（每次开始前）
```powershell
cd "E:\ffffff-JIANCAI\2026FIC团体赛\case"
git pull --rebase
```

### 提交发现
编辑 `shared/findings.yaml`，追加：
```yaml
- id: F-S001
  time: "当前时间"
  from: server_analyst
  type: evidence
  summary: "服务器取证-1: OS版本=xxx"
  detail: "来源: /etc/os-release"
  related_to: []
```

推送：
```powershell
cd "E:\ffffff-JIANCAI\2026FIC团体赛\case"
git add shared/
git commit -m "server: 服务器取证-1 已解出"
git push
```

### 冲突处理
```powershell
git pull --rebase
git add shared/
git rebase --continue
git push
```

## 步骤4：确认后开始工作

```powershell
git status
cat shared/progress.yaml | Select-String "server"
```

**部署完成后，继续 `role_prompt_server.md` 中的任务解题。**

**证据文件位置**：
- `E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器\检材3-1.E01`
- `E:\ffffff-JIANCAI\2026FIC团体赛\检材3-服务器\检材3-2.E01`
