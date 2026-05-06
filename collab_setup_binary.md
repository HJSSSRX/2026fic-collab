# 🔗 协作部署指令 — 二进制/U盘取证角色（本机）

**立即执行以下步骤，部署 Git 协作同步。不要提问，按顺序做。**

本机 case 目录就是 Git 仓库本身，无需克隆，只需配置。

## 步骤1：配置 Git 身份

```powershell
cd "E:\ffffff-JIANCAI\2026FIC团体赛\case"
git config user.name "binary_analyst"
git config user.email "binary@2026fic.local"
```

**注意**：本机服务器角色也在同一仓库，你们共享同一个 .git。推送前务必先 `git pull --rebase`。

## 步骤2：协作流程

### 拉取最新
```powershell
cd "E:\ffffff-JIANCAI\2026FIC团体赛\case"
git pull --rebase
```

### 提交发现
编辑 `shared/findings.yaml`，追加：
```yaml
- id: F-B001
  time: "当前时间"
  from: binary_analyst
  type: evidence
  summary: "二进制-1: SampleVC.exe MD5=xxx"
  detail: "来源: 检材4-U盘.E01 提取"
  related_to: []
```

推送：
```powershell
cd "E:\ffffff-JIANCAI\2026FIC团体赛\case"
git add shared/
git commit -m "binary: 二进制-1 已解出"
git push
```

### 冲突处理（本机两个角色同时改 shared/ 时容易冲突）
```powershell
git pull --rebase
# 编辑冲突后：
git add shared/
git rebase --continue
git push
```

## 步骤3：确认后开始工作

```powershell
git status
```

**部署完成后，继续 `role_prompt_binary.md` 中的任务解题。**

**证据文件位置**：`E:\ffffff-JIANCAI\2026FIC团体赛\检材4-U盘.E01`
