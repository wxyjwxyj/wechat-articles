---
paths:
  - "collectors/**/*.py"
  - "pipeline/**/*.py"
  - "publishers/**/*.py"
  - "api/**/*.py"
  - "storage/**/*.py"
  - "scripts/**/*.py"
---

# 代码风格

- 遵循 PEP 8，注释使用中文
- import 顺序：标准库 → 第三方库 → 项目内部，各组间空一行
- 大文件（>200行）分段读取，先看结构再看细节

# 模块职责边界

| 模块 | 职责 | 边界 |
|------|------|------|
| `collectors/` | 从外部拿数据，写入 items 表 | 不写 bundle |
| `pipeline/` | 标准化、去重、打标签、bundle 生成 | 不负责 API 或页面 |
| `publishers/` | 消费 bundle 数据，生成 HTML / 公众号稿 | 不直接读原始抓取结果 |
| `api/` | 只读接口，供小程序或调试使用 | 不承担采集或生成逻辑 |
| `storage/` | SQLite 数据库访问层 | 统一的数据访问入口 |
| `scripts/` | 独立执行脚本 | 编排各模块 |

# 技术要点

- CDP Proxy 用**同步 XMLHttpRequest**，不用 async fetch
- 微信公众号 HTML 只能用**内联 style**，不支持 class/flex/grid/animation
- 主数据源是 `content.db`（SQLite），不是 JSON 文件
