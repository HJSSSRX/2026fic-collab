# 🔗 协作部署指令 — 手机取证角色

**立即执行以下步骤，部署 Git 协作同步。不要提问，按顺序做。**

## 步骤1：克隆协作仓库

```powershell
cd "F:\电子取证\FIC2026-线上赛"
git clone https://github.com/HJSSSRX/2026fic-collab.git case
```

如果 `case` 目录已存在，先删除或重命名：
```powershell
Rename-Item "F:\电子取证\FIC2026-线上赛\case" "F:\电子取证\FIC2026-线上赛\case_old" -ErrorAction SilentlyContinue
git clone https://github.com/HJSSSRX/2026fic-collab.git case
```

## 步骤2：配置 Git 身份

```powershell
cd "F:\电子取证\FIC2026-线上赛\case"
git config user.name "mobile_analyst"
git config user.email "mobile@2026fic.local"
```

## 步骤3：验证目录结构

确认以下结构存在：
```
F:\电子取证\FIC2026-线上赛\
├── case/                       ← Git 仓库（刚克隆的）
│   ├── shared/
│   │   ├── findings.yaml
│   │   ├── progress.yaml
│   │   ├── answers.yaml
│   │   ├── questions.yaml
│   │   └── timeline.yaml
│   └── role_prompt_mobile.md   ← 你的任务说明
└── 检材2-手机.tar              ← 证据文件（不进 Git）
```

## 步骤4：开始工作后的协作流程

### 拉取最新（每次开始工作前）
```powershell
cd "F:\电子取证\FIC2026-线上赛\case"
git pull --rebase
```

### 提交发现（解出题目后）
编辑 `shared/findings.yaml`，追加：
```yaml
- id: F-M001
  time: "当前时间"
  from: mobile_analyst
  type: evidence
  summary: "手机取证-1: 手机型号=xxx"
  detail: "来源: build.prop ro.product.model"
  related_to: []
```

然后推送：
```powershell
cd "F:\电子取证\FIC2026-线上赛\case"
git add shared/
git commit -m "mobile: 手机取证-1 已解出"
git push
```

### 查看其他角色进展
```powershell
git pull --rebase
cat shared/findings.yaml
cat shared/answers.yaml
```

### 遇到冲突时
```powershell
git pull --rebase
# 编辑冲突文件后：
git add shared/
git rebase --continue
git push
```

## 步骤5：确认部署完成

```powershell
cd "F:\电子取证\FIC2026-线上赛\case"
git log --oneline -1
cat shared/progress.yaml | Select-String "mobile"
```

**部署完成后，回到 `role_prompt_mobile.md` 中的任务，开始解题。**
