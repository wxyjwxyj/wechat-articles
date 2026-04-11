# 项目状态快照

> 每次 session 结束后更新。详细踩坑记录见 `project_wechat_lessons.md`。

---

## 当前版本：v22

```
v20: Topic Research Hub 第6数据源（本地公众号搜索）
     + doc_library 扩充 Agent 框架（1→10条）
     + Claude 评分器加主题相关性约束
v21: daily_run.sh 健壮性改进（stash 保护 + bundle 失败跳过 + 日期校验）
     + wrapper exit code 修复
     + haiku 模型名修正
     + 3 个测试修复
v22: 系统安全与可靠性加固（P0-P2 共 9 项修复）
     + 密钥迁移到环境变量（.env）
     + SQLite WAL + busy_timeout 解决并发竞态
     + 全部采集脚本加 retry session（指数退避）
     + Claude API 429 重试
     + DB 索引（published_at / source_id）
     + 异常捕获细化 + 配置校验 + 封面图兜底 + bundle 失败清理
```

---

## 系统状态

| 组件 | 状态 | 备注 |
|------|------|------|
| 日报采集 | ✅ 运行中 | launchd 每天 **11:30** 自动执行 |
| 微信采集 | ✅ 正常 | 登录态过期时自动打开 Chrome 重试 |
| HN / ArXiv / GitHub Trending / RSS | ✅ 正常 | 无需 CDP |
| GitHub Pages | ✅ 已推送 | https://wxyjwxyj.github.io/wechat-articles/ |
| 公众号草稿箱 | ✅ 自动提交 | 含封面图，人工审核后发布 |
| Research Hub | ✅ 可用 | `python -m flask --app api.app run` → http://localhost:5000/research |

---

## 数据源

| 源 | 脚本 | 依赖 |
|----|------|------|
| 微信公众号（9个） | `fetch_wechat_today.py` | CDP Proxy + Chrome 登录 |
| Hacker News | `fetch_hackernews_today.py` | 无 |
| ArXiv | `fetch_arxiv_today.py` | 无 |
| GitHub Trending | `fetch_github_trending_today.py` | 无 |
| RSS（TechCrunch/MIT/The Verge）| `fetch_rss_today.py` | 无 |

---

## Research Hub 数据源（6个并行）

| 源 | 模块 | 备注 |
|----|------|------|
| ArXiv 论文 | `research/arxiv_search.py` | |
| GitHub 仓库 | `research/github_search.py` | |
| HN 讨论 | `research/hn_search.py` | |
| 官方文档库 | `research/doc_library.py` | 30+ 框架，本地匹配 |
| Web 搜索 | `research/web_search.py` | Google→Bing→DuckDuckGo 三级降级 |
| 本地公众号 | `research/wechat_search.py` | 查 content.db |

---

## 近期改动（按时间倒序）

| 日期 | 改动 | commit |
|------|------|--------|
| 2026-04-11 | 系统安全与可靠性加固 v22（9项修复） | 待提交 |
| 2026-04-11 | daily_run.sh 健壮性改进（5项） | 待提交 |
| 2026-04-06 | Research Hub 第6源（公众号本地搜索） | `3fe2dc5` |
| 2026-04-06 | doc_library 扩充 Agent 框架 1→10条 | `9319534` |
| 2026-04-06 | Claude 评分器加主题相关性约束 | `9319534` |
| 2026-04-06 | Web Search 升级三级降级（加 DuckDuckGo）| `1cc4bad` |
| 2026-04-06 | daily_run.sh 微信登录过期自动重试 | `313b3cd` |
| 2026-04-05 | RSS 接入（TechCrunch/MIT/The Verge）| `b6a8f50` |
| 2026-04-05 | Topic Research Hub 实现（Task 1-10）| 多个 commit |
| 2026-04-05 | ArXiv + GitHub Trending 数据源 | `cb37a64` |

---

## 待观察 / 下一步

- [ ] 跑几天看微信自动重试是否稳定
- [ ] 跑几天验证 daily_run.sh 健壮性改进效果（stash/bundle跳过/日期校验）
- [ ] Research Hub 搜索质量评估（ArXiv 有时 429 限流）
- [ ] 轮换 Claude API Key（旧 key 曾明文存在 config.json）
- [ ] 类型提示完善（mypy）- P1 待做
- [ ] 测试覆盖提升 - P1 待做

---

## 关键路径

```bash
# 手动跑日报
./daily_run.sh

# 只跑采集
python fetch_wechat_today.py
python fetch_hackernews_today.py

# 重建 bundle + HTML
python scripts/build_bundle.py
python generate_html.py bundle_today.json

# 启动 Research Hub
python -m flask --app api.app run

# 推 GitHub Pages（手动）
git checkout main
git checkout dev -- today.html archive/ mp_article_preview.html
git add today.html archive/ mp_article_preview.html
git commit -m "Update: $(date +%Y-%m-%d)"
git push origin main
git checkout dev
```

---

## 注意事项

- `index.html` 是手写门户页，**绝对不能被脚本覆盖**
- CDP Proxy 需要提前启动：`http://localhost:3456`
- launchd 时间是 **11:30**（不是 9:57）
- dev 分支放代码，main 分支只放前端产物
