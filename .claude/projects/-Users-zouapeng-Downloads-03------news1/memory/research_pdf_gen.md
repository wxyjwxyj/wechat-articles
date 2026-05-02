---
name: research-pdf-generation
description: 横纵分析报告 Markdown → PDF 生成流程
type: reference
---

**工具**：`~/.claude/skills/hv-analysis/scripts/md_to_pdf.py`
**Skill**：`hv-analysis`（触发词：横纵分析、研究一下 等）

**目录结构**：
- Markdown 源文件：`assets/research/markdown/`
- PDF 输出：`assets/research/pdf/`
- HTML 调试文件：`assets/research/html/`

**为什么之前找了很久**：这个脚本不在项目目录里，在用户级 skill 目录（`~/.claude/skills/hv-analysis/scripts/`），搜项目目录搜不到。

**使用方法**：
```bash
set -a && source .env && set +a && \
python ~/.claude/skills/hv-analysis/scripts/md_to_pdf.py \
  "assets/research/markdown/XXX.md" \
  "assets/research/pdf/XXX.pdf" \
  --title "XXX"
```

**注意事项**：
- 脚本只依赖系统安装的 Google Chrome，无需额外 Python 库
- HTML 调试文件固定生成在 PDF 同目录，需要手动移到 `assets/research/html/`
- 需要先 `source .env` 加载环境变量（虽然这个脚本不直接需要，但项目惯例）
