# 前端 & 分支 & 自动化脚本 — 经验教训

---

## 一、前端页面

### 教训：单页面 index.html 会越来越臃肿
- 最初所有内容都往 index.html 塞，功能多了之后维护困难，每次生成都覆盖整个文件

### ✅ 最终方案：拆分为门户 + 内容页
- `index.html` — 静态导航门户（手工维护，**绝对不能被脚本覆盖！**）
- `today.html` — 每日完整文章列表（脚本自动生成）
- `archive/digest_YYYY-MM-DD.html` — 每日导读存档
- `mp_article_preview.html` — 导读风精选页

### 教训：手机端适配不能忽视
- 表格布局在手机上溢出严重 → 改为卡片式布局
- 标签栏过长 → 加折叠按钮
- **方案**：CSS media query 在窄屏时切换布局，而非 JS 动态判断

---

## 二、分支管理

### ✅ 双分支策略
- `main` — 只放 GitHub Pages 的前端文件，推远端
- `dev` — 所有开发改动，只在本地
- 合并方式：`git checkout dev -- <文件>` 精准拉取，不要 `git merge dev`

### ⚠️ 关键教训：推 GitHub Pages 的正确流程

**错误流程（之前）**：
```
生成 HTML → 切 main → git checkout dev -- today.html → 推送
```
`git checkout dev -- today.html` 拉的是 dev **已提交**的版本，不是刚生成的文件！

**正确流程（现在）**：
```
生成 HTML → 在 dev 先提交 HTML → 切 main → git checkout dev -- today.html → 推送
```
步骤12.5：`git add today.html mp_article_preview.html archive/ && git commit` 必须在切换分支前执行。

- commit: `95e688f`

---

## 三、自动化脚本

### ✅ daily_run.sh 完整流程（16步）

```
1.  检查 CDP Proxy（http://localhost:3456/health）
2.  检查微信标签页（/targets 是否含 mp.weixin.qq.com）
3.  确保在 dev 分支
4.  初始化 sources（seed_sources.py）
5.  采集微信文章（exit=11 时自动打开 Chrome 等60s重试）
5.5 采集 HN
5.6 采集 ArXiv
5.7 采集 GitHub Trending
5.8 采集 RSS
6.  生成 bundle（build_bundle.py）
7.  检查 bundle_today.json 是否存在
8.  生成 today.html
9.  生成公众号发布稿（generate_mp_article.py）
10. 生成导读风 HTML（generate_mp_html.py）
11. 提交草稿箱（publish_to_mp.py）
12. 归档（archive/YYYY-MM-DD.html + generate_archive_index.py）
12.5 在 dev 提交今日 HTML（必须先提交！）
13. 推送 GitHub Pages（切 main → checkout 文件 → push → 切回 dev）
15. 统计结果 + macOS 通知
16. 清理30天前的旧日志
```

日志路径：`.claude/logs/YYYY-MM-DD.log`

### ✅ launchd 配置
- plist：`~/Library/LaunchAgents/com.news1.daily.plist`
- 执行时间：每天 **11:30**
- PATH 包含 miniconda3
- 前提：电脑开机 + Chrome 已打开微信公众平台标签页 + CDP Proxy 运行中
- exit code 78 = 脚本未运行（非业务错误，检查 launchd 配置）
- **不补跑**：机器睡眠期间错过的任务直接跳过

### 教训：脚本要幂等
- 同一天多次运行不应产生重复数据
- 采集脚本用日期过滤 + 数据库去重保证幂等性
