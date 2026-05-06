# 🔗 协作部署指令 — 计算机取证角色

**立即执行以下步骤，部署 Git 协作同步。不要提问，按顺序做。**

## 步骤1：克隆协作仓库

```powershell
cd D:\2026FIC
git clone https://github.com/HJSSSRX/2026fic-collab.git case
```

如果 `case` 目录已存在，先删除或重命名：
```powershell
Rename-Item D:\2026FIC\case D:\2026FIC\case_old -ErrorAction SilentlyContinue
git clone https://github.com/HJSSSRX/2026fic-collab.git case
```

## 步骤2：配置 Git 身份

```powershell
cd D:\2026FIC\case
git config user.name "computer_analyst"
git config user.email "computer@2026fic.local"
```

## 步骤3：复制协作工具（可选）

如果需要用 `collab_sync.py` 的快捷命令，从仓库或主机获取：
```powershell
# 仓库中已有的话直接用，没有就手动编辑 YAML
```

## 步骤4：验证目录结构

确认以下结构存在：
```
D:\2026FIC\
├── case/                          ← Git 仓库（刚克隆的）
│   ├── shared/
│   │   ├── findings.yaml
│   │   ├── progress.yaml
│   │   ├── answers.yaml
│   │   ├── questions.yaml
│   │   └── timeline.yaml
│   └── role_prompt_computer.md    ← 你的任务说明
└── 检材1-计算机.E01               ← 证据文件（不进 Git）
```

## 步骤5：开始工作后的协作流程

### 拉取最新（每次开始工作前）
```powershell
cd D:\2026FIC\case
git pull --rebase
```

### 提交发现（解出题目后）
编辑 `shared/findings.yaml`，追加：
```yaml
- id: F-C001
  time: "当前时间"
  from: computer_analyst
  type: evidence
  summary: "计算机取证-1: OS版本=xxx"
  detail: "来源: SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion"
  related_to: []
```

然后推送：
```powershell
cd D:\2026FIC\case
git add shared/
git commit -m "computer: 计算机取证-1 已解出"
git push
```

### 查看其他角色进展
```powershell
cd D:\2026FIC\case
git pull --rebase
cat shared/findings.yaml
cat shared/answers.yaml
```

### 遇到冲突时
```powershell
git pull --rebase
# 如果有冲突，编辑冲突文件后：
git add shared/
git rebase --continue
git push
```

## 步骤6：确认部署完成

执行以下命令验证一切正常：
```powershell
cd D:\2026FIC\case
git log --oneline -1
cat shared/progress.yaml | Select-String "computer"
```

**部署完成后，回到 `role_prompt_computer.md` 中的任务，开始解题。**
