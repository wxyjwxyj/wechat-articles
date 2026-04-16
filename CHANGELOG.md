# CHANGELOG

## 2026-04-15

- fix: notify() 改用 terminal-notifier，修复 launchd 环境下通知失效
- feat: 深度研究页加「复制提示词」按钮，提示词统一改为中文

## 2026-04-14

- feat: Research Hub 新增深度研究功能 + 全面修复渲染层 XSS

## 2026-04-13

- feat: Research Hub 集成横纵分析法深度研究（SSE 流式输出）
- feat: publish_to_mp 新增 --force 参数跳过已有草稿检查
- fix: 量子位/机器之心/新智元 改回 CDP 采集
- fix: 去掉 You are 角色扮演句式，修复点评生成失败
- fix: 取最后一个 JSON 对象，处理 Claude 自我纠正场景
- fix: 加强去重 prompt 精度，新增误合并防护测试
- fix: 所有 prompt 改为英文，避免代理拦截（去重/翻译/tagging/mp_article）
- feat: 新增评分缓存，避免重复调用 Claude

## 2026-04-12

- feat: 微信公众号采集 CDP→RSS 迁移
- feat: 微信公众号严格按发布日期过滤（当天对当天）
- feat: Research Hub 主题搜索加入 Exa + Claude query 扩展
- feat: Research Hub 搜索历史持久化
- feat: 日志持久化到文件（按天滚动）
- feat: 所有搜索源均使用 Claude query 扩展提升召回率
- feat: 新增采集端初筛，减少 Claude 评分 token 消耗
- feat: build_bundle 支持 --date 参数指定日期
- fix: query 扩展改对话式 prompt，避免代理误判拦截
- fix: GitHub 初筛加 star < 50 硬过滤
- fix: list_items_by_date 兼容带时区后缀的 ISO 时间戳
- fix: 日志中文括号导致变量乱码

## 2026-04-11

- feat: 翻译结果持久化到数据库（重跑秒级完成）
- feat: daily_run 启动时探测 Claude API 可用性
- feat: 加入 code review 体系（agents + finish skill）
- perf: 翻译改为 5 并发，速度提升约 8x
- refactor: items 表冲突键从 url 改为 content_hash
- fix: HN 条目链接改为 HN 讨论页
- fix: 来源分类修复 + 海外源中文翻译 + XSS 防护
- fix: 系统安全与可靠性加固（P0-P2 共 9 项修复）

## 2026-04-10

- fix: bundle_items 插入时保序去重，防止 UNIQUE 约束失败

## 2026-04-09

- feat: 微信标签页未打开时自动创建，而非直接退出

## 2026-04-07

- feat: 接入小红书数据源（Research Hub 第 7 个数据源）

## 2026-04-06

- feat: 完成 Topic Research Hub 全链路（HN Search / GitHub Search / ArXiv / Web Search / 文档库 / 公众号本地搜索 / 小红书）
- feat: Claude 评分器 + 主题相关性约束
- feat: Web Search 新增 DuckDuckGo 零配置兜底
- feat: 微信登录态过期时自动打开登录页并重试

## 2026-04-05

- feat: 接入 RSS 数据源（TechCrunch / MIT / The Verge）
- feat: 接入 ArXiv AI 论文数据源
- feat: 接入 GitHub Trending AI/ML 仓库数据源
- feat: 接入 Hacker News 海外 AI 数据源
- feat: 公众号一键发布（封面图生成+上传+草稿箱自动提交）
- feat: 公众号排版升级（科技杂志风格）
- feat: 增强 LLM 编辑点评（更有态度的 prompt）
- feat: 添加 AI 内容标注合规 + 定时任务改为 11:30
- feat: 导读精选多样性保底
- feat: daily_run.sh 添加 macOS 通知提醒
- feat: 统一错误处理体系 + 增强失败通知
- refactor: 统一 logging 替代全项目 print()
- fix: 打标签分批处理，避免大批量 JSON 解析失败
- fix: RSS 时区差导致 build_bundle 日期过滤漏掉

## 2026-04-04

- feat: 每日自动采集脚本（daily_run.sh）+ 免确认权限配置
- feat: Claude 去重 + 导读风公众号稿 + 重要性打分
- feat: 新增导读风 HTML 生成脚本，推 GitHub Pages
- feat: 历史归档
- feat: 话题+来源双维度筛选
- feat: Bundle API / HTML 预览 / 公众号稿件生成
- feat: 内容去重逻辑 + Item Repository
- feat: 打标签 + 每日 Bundle 构建
- refactor: index.html 改为导航门户，完整版移至 today.html
- fix: 手机端适配（表格→卡片布局）

## 2026-04-03

- feat: 提取微信 collector + normalizer
- feat: SQLite schema（content hub）

## 2026-04-01 ~ 04-02

- 项目初始化，微信公众号文章监控系统原型
