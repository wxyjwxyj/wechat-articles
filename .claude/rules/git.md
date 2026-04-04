# Git 提交规范

```
<type>: <subject>

<body>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Type**: `feat` | `fix` | `refactor` | `test` | `docs`

## 分支约定
- `main`：GitHub Pages 展示页面，推 GitHub
- `dev`：所有代码改动，只本地保存

## ⚠️ 推送 GitHub Pages 注意
- **index.html 是手写门户页，不能用脚本覆盖！**
- 推送流程：dev 生成子页面 → 切 main → checkout 文件 → push → 切回 dev
- `daily_run.sh` 步骤 13 已自动处理
