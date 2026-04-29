# 数据采集 & 管道 & 公众号发布 — 经验教训

---

## 一、数据采集

### ❌ 搜狗微信搜索方案（已废弃）
- **问题**：反爬严重，频繁返回空结果或验证码，数据时效性差
- **教训**：第三方搜索引擎做微信采集不可靠，不要在这个方向上花时间

### ❌ Playwright 方案（已废弃）
- **问题**：不稳定，难以处理微信公众平台的登录态
- **教训**：自动化浏览器方案看似万能，但对登录态管理复杂的站点反而不如更轻量的方案

### ❌ async/await + CDP（已废弃）
- **问题**：CDP Proxy 的 `/eval` 端点对 Promise 返回值处理有 bug，异步代码返回空对象 `{}`
- **教训**：遇到中间层代理时，不要假设所有 JS 特性都能正常工作，先用最简单的方式验证

### ✅ 最终方案：同步 XMLHttpRequest + CDP Proxy
- 利用用户已登录的 Chrome 浏览器的 session
- 通过 CDP Proxy 注入同步 XMLHttpRequest 调用微信公众平台 API
- 复用已打开的标签页而非创建新标签页（更高效、更稳定）
- **关键**：同步 XHR 虽然"落后"，但在 CDP 场景下是最可靠的

### ✅ 微信登录过期自动重试（v19）
- exit=11 时：发通知 → `open -a "Google Chrome" "https://mp.weixin.qq.com"` → sleep 60 → 重试
- 仍失败才记录错误继续，不阻断其他采集源

### 微信公众号采集方案调研（2026-04）

**结论：CDP + 公众平台内部 API 是 2026 年最优的免费自建方案，不需要换。**

已调研并排除的方案：

| 方案 | 状态 | 原因 |
|------|------|------|
| 搜狗微信搜索 | ❌ 已死 | 2023年关闭 |
| RSSHub 微信路由 | ❌ 已死 | 依赖搜狗 |
| Playwright 模拟登录 | ❌ 已废弃 | 微信网页版对大量账号已关闭 |
| WeWeRSS（微信读书接口） | ⚠️ 可用但不稳定 | 账号 12-24h 失效需扫码，项目维护停滞 |
| WeChat-Article-Harvester | ⚠️ 参考价值有限 | Star=1，交互式 CLI，凭证 2h 过期 |
| 新榜/清博付费 API | 💰 企业级 | 成本高，面向媒体机构 |
| JustOneAPI | 💰 待评估 | 价格未知，需注册后查看 |

**待尝试的技术点（从 WeChat-Article-Harvester 发现）**：
- [x] **m2w 工具**（`wechatmp2markdown`）：无需 Cookie 渲染微信文章正文，M 系列 Mac 通过 Rosetta 可用
  - 下载：`https://github.com/fengxxc/wechatmp2markdown/releases/download/v1.1.11/wechatmp2markdown-v1.1.11_osx_amd64`
  - 用法：`./m2w <url> <output_dir> --image url`，输出 Markdown，按文章标题建子目录
  - 验证：2026-04-12 测试通过，无需登录态，正文完整
  - 当前用途：暂不集成（日报只用摘要不用正文），**将来如需正文内容供 Claude 分析时启用**
- [x] **appmsg_token / 阅读量调研**（2026-04-12）：
  - `getappmsgext` 不返回阅读量，只返回广告/相关视频等
  - 文章页面阅读量只在微信客户端内显示，网页端 `read_num` 为空
  - **他人文章阅读量无法通过任何公开接口获取**
  - **自己日报的阅读量** ✅ 可获取：`appmsgpublish?sub=list` 接口返回 `appmsg_info[].read_num/like_num/comment_num/share_num`
  - CDP eval 接口正确用法：`POST /eval?target=<targetId>`，body 是纯 JS 表达式字符串（非 JSON），返回 `{"value": ...}`
- [ ] **文章删除检测**：检测 ghost/dead/内容违规关键词判断文章是否失效

### wechat-download-api 源码调研（2026-04-12）

项目地址：https://github.com/tmwgsicp/wechat-download-api

**核心原理**：扫码登录微信公众号后台 → 拿 token+cookie → 调后台管理 API 拉文章列表（不爬文章页面）。

**值得借鉴的技术点**：

| 技术点 | 实现方式 | 对我们的价值 |
|--------|---------|-------------|
| TLS 指纹伪装 | `curl_cffi` + `impersonate="chrome120"` | 无头 HTTP 采集时绕过微信 TLS 检测，比普通 requests 抗封 |
| 代理池 | 轮转 + 120s 冷却 + 直连兜底 | 参考 `utils/proxy_pool.py` 设计，给 RSS 采集加代理支持 |
| 凭证过期分级告警 | 每 6h 检查，提前 24h/6h 发 webhook | 我们目前等跑失败才知道过期，可加主动检测 |
| 区分验证页 vs 文章删除 | `has_article_content()` + `is_article_unavailable()` | 验证页（IP 风控）可重试，文章删除不重试，减少误判 |
| 微信后台 API 拉文章列表 | `GET /cgi-bin/appmsgpublish?sub=list&fakeid=xxx&token=xxx` | 返回结构化 JSON，风控风险极低，比 CDP 爬页面稳定 |

**关键接口**（他们用的，我们 CDP 方案也可以直接调）：
```
# 文章列表（结构化 JSON，无风控）
GET https://mp.weixin.qq.com/cgi-bin/appmsgpublish
    ?sub=list&fakeid=xxx&token=xxx&count=10&type=101_1&sub_action=list_ex

# 搜索公众号获取 fakeid
GET https://mp.weixin.qq.com/cgi-bin/searchbiz?query=xxx&token=xxx
```

**SaaS 版**：https://wechatrss.waytomaster.com（免费 2 个公众号，¥9.9/月 20 个）
- 已验证：RSS 接口可用，返回标准 RSS 2.0，可直接接入 `fetch_rss_today.py`
- 免费额度不够（我们需要 9 个公众号），暂不替换 CDP 方案

### Wechat2RSS 免费 RSS（ttttmr，2021年起运营，稳定）

我们 9 个公众号中有 3 个已收录，可直接用免费 RSS 替代 CDP 采集：

| 公众号 | RSS 地址 |
|--------|---------|
| 量子位 | https://wechat2rss.xlab.app/feed/7131b577c61365cb47e81000738c10d872685908.xml |
| 机器之心 | https://wechat2rss.xlab.app/feed/51e92aad2728acdd1fda7314be32b16639353001.xml |
| 新智元 | https://wechat2rss.xlab.app/feed/ede30346413ea70dbef5d485ea5cbb95cca446e7.xml |

其余 6 个（AI寒武纪、数字生命卡兹克、APPSO、36氪、虎嗅APP、硅星人Pro）未收录，继续走 CDP。

注意：同批次文章时间戳相同（如都是 09:05:00），排序时会并列，不影响日期过滤。

### launchd 注意事项
| 问题 | 说明 |
|------|------|
| exit code 78 | `EX_CONFIG`，脚本从未运行（非业务错误） |
| 不补跑 | `StartCalendarInterval` 错过的时间点直接跳过 |
| 当前时间 | **11:30**（plist 路径：`~/Library/LaunchAgents/com.news1.daily.plist`）|
| 日志 | `.claude/logs/YYYY-MM-DD.log` |

---

## 二、数据管道架构

### 教训：先定数据流再写代码
- 早期直接从采集脚本输出 JSON 文件，导致格式不统一、重复数据难处理
- **最终架构**：`采集 → SQLite(items表) → 标准化/去重/打标签 → bundle → 输出`
- SQLite 作为单一数据源（single source of truth）是正确决策

### 教训：去重需要多级策略
- 简单 URL 去重不够 — 同一篇文章可能有不同的短链
- 最终实现：URL 精确匹配 + 标题相似度 + Claude 智能去重（三级）

### 教训：bundle 是衔接采集和输出的关键抽象
- `bundle_today.json` 作为"每日快照"，解耦采集逻辑和输出逻辑
- HTML 生成和公众号稿件生成共用同一个 bundle 输入，保证一致性

### 打标签分批处理
- 文章超过 ~20 篇时，Claude 返回的 JSON 容易因长度超限而解析失败
- 改为每批 BATCH_SIZE=15 篇，单批失败降级为关键词匹配
- 分批时 id 用全局编号（`id_offset + i + 1`），解析时转换回批内下标

### Bug 修复记录
| bug | commit | 教训 |
|---|---|---|
| fetch_wechat_today 遍历所有 source（含非微信）| `f3e258b` | list_sources() 要加 type 过滤 |
| mp_article 模型名格式错误 | `d78018e` | 中转服务只识别 `claude-haiku-4-6` 格式 |
| 打标签44篇一次送 Claude → JSON 解析失败 | `8689c16` | BATCH_SIZE=15 |
| items_flat 缺 source_type 字段 | `647ef16` | build_bundle 输出要包含所有下游用到的字段 |

---

## 三、AI 集成

### ✅ Claude 的合适用途
- **去重判断**：标题相似但不完全相同的文章，准确率很高
- **内容摘要/点评**：为每篇文章生成编辑点评，质量稳定
- **重要性打分**：基于标题和摘要给文章打分排序

### 教训：AI 调用要有成本意识
- 每次 build_bundle 都调用 Claude 做去重和打分，日均成本可控（20 条左右）
- 量级增大时需要考虑缓存或批量处理

---

## 四、公众号草稿箱自动提交

### ✅ 通过 CDP 调用公众号后台内部接口
- 接口：`POST /cgi-bin/operate_appmsg?t=ajax-response&sub=create&type=77`
- FormData：title0, content0, digest0, author0, count=1 等
- 不需要官方 API 认证，直接利用浏览器 session

### 教训：type=77 是草稿箱
- `type=10` 是旧版素材管理，`type=77` 对应 2021 年后的草稿箱+发布体系
- 创建返回 `appMsgId`，删除时用 `sub=del` + `AppMsgId`

### 安全策略
- **只提交到草稿箱，不自动发布**（发布需要人工确认）
- 提交前检查是否已有同日草稿（按标题日期判断），防止重复

### 相关文件
- `publishers/mp_publisher.py` — MpPublisher 类
- `scripts/publish_to_mp.py` — 命令行入口（支持 --dry-run）

---

## 五、封面图自动生成与上传

### ✅ 封面图生成（Pillow）
- 尺寸 900×383（微信公众号推荐比例 2.35:1）
- 深蓝渐变底色 + 红色装饰条 + 日期文字
- 文件：`publishers/cover_generator.py`，输出 `cover_today.png`

### ✅ 封面图上传流程
- 通过 CDP 调用 `filetransfer` 接口上传图片到公众号素材库
- 返回 `fileid`，作为 `create_draft` 的 `fileid` 参数
- 上传前需将图片转为 base64

### 教训：草稿创建带封面
- `create_draft` 的 FormData 中 `fileid0=<封面fileid>` 即可绑定封面
- 不设置 fileid 草稿也能创建，但公众号后台显示无封面

---

## 六、多数据源接入记录

### ArXiv
- commit: `cb37a64`，days_back=3（周末也能抓到周五论文）
- max_results=100 作为候选池，按关键词相关度打分取前10（30条候选池会漏高分论文）

#### ⚠️ ArXiv 429 限流问题（2026-04-29 修复）
- **现象**：早上 9:30 采集窗口频繁 429，下午/晚上窗口很少出问题
- **根因**：4 个采集进程并行启动，HN/ArXiv/GitHub/RSS 几乎同时请求，jitter=2-8s 不够错开
- **排查过程**：测了代理直连(11.2s) vs 走代理(0.9s)，代理反而更快；max_results 30/50/100 对响应时间无影响。**问题不在代理也不在 payload 大小，在于并行突发请求**
- **修复**：jitter 2-8s → 20-40s，让 ArXiv 请求自然错开到其他采集完成之后（实测 ArXiv 实际请求时 HN/GitHub/RSS 均已结束）
- **日志改进**：429 失败时记录 proxy 状态和总耗时，方便下次排查
- **教训**：并行采集的 jitter 要大于最长的快速采集（RSS ~2s），否则所有请求仍会重叠

### GitHub Trending
- commit: `9b204c6`，用标准库 HTMLParser 解析，无需 BeautifulSoup
- 未登录约返回 25 个仓库，今日 star 数用 regex 从 "343 stars today" 提取

### RSS（TechCrunch/MIT/The Verge）
- commit: `b6a8f50`，技术栈：feedparser，通用 RssCollector 类

#### ⚠️ RSS 教训1：分类专属 URL 不一定可靠
- The Verge AI 分类 feed 返回不规范 XML → 改用全站 RSS + 关键词过滤

#### ⚠️ RSS 教训2：时区差导致日期过滤漏掉
- RSS 文章存入 DB 的是美国时间，build_bundle 按北京时间过滤 → 0 条
- **正确做法**：`normalize_rss_item` 用 `datetime.now(timezone.utc)` 作为 `published_at`
- commit: `5d50f1f`

### 导读精选策略
- 精选 **6 条**（8→6，降低读者负担）
- 保底：HN + GitHub Trending 各1条（ArXiv 靠分数自然竞争）
- 所有候选统一按 score 降序，保底不强制排前面
