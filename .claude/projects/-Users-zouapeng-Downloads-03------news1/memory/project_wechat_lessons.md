# 微信公众号文章监控项目 — 经验与教训（索引）

> 已拆分为专题文件，按需查阅。项目当前状态见 `MEMORY.md`。

---

## 文件导航

| 文件 | 内容 |
|------|------|
| `MEMORY.md` | 项目状态快照、当前版本、待做事项 |
| `lessons_data.md` | 数据采集、管道架构、公众号发布、多数据源接入 |
| `lessons_frontend.md` | 前端页面、分支管理、daily_run.sh 自动化 |
| `lessons_engineering.md` | Claude Code 工程化、代码质量、exit code |
| `lessons_research_hub.md` | Topic Research Hub 规划、实现、Web 搜索、教训 |

---

## 项目演进总线

```
v0:  搜狗搜索 → 失败
v1:  Playwright → 不稳定
v2:  CDP async → 返回空对象
v3:  CDP 同步 XHR → ✅ 稳定
v4:  SQLite + pipeline 架构
v5:  Claude 去重/打分/点评
v6:  前端拆分（门户+内容页+导读页）
v7:  手机端适配
v8:  公众号草稿箱自动提交
v9:  封面图自动生成+上传
v10: Claude Code 工程化
v11: 统一 logging
v12: 统一错误处理体系
v13: pyproject.toml 依赖管理
v14: ArXiv + GitHub Trending 数据源
v15: 导读精选多样性保底 + 打标签分批
v16: 修复 GitHub Pages 拉旧 HTML 的 bug
v17: RSS 接入（TechCrunch/MIT/The Verge）
v18: 精选 8条→6条
v19: 微信登录过期自动重试
v20: Research Hub 第6源（本地公众号）+ doc_library 扩充 + 评分器主题约束
```

每一步失败都直接指向了更好的方案。不要怕推翻重来，但要记录为什么失败。
