# 微信公众号文章监控项目

## 项目概述

自动获取指定微信公众号的最新文章，生成 HTML 汇总页面。

## 监控的公众号

- 量子位 (MzIzNjc1NzUzMw==)
- AI寒武纪 (Mzg3MTkxMjYzOA==)
- 机器之心 (MzA3MzI4MjgzMw==)
- 数字生命卡兹克 (MzIyMzA5NjEyMA==)
- APPSO (MjM5MjAyNDUyMA==)

## 核心脚本说明

### ✅ 推荐使用

**`fetch_wechat_today.py`** - 获取今天的文章
- 使用 CDP Proxy + 同步 XMLHttpRequest
- 只返回今天发布的文章
- 复用已打开的浏览器标签页
- **最稳定可靠的方案**

### ⚠️ 已废弃

以下脚本**不要使用**：

- `fetch_all_wechat.py` - 使用搜狗微信搜索（反爬严重，数据不准）
- `fetch_wechat.py` - 早期测试脚本
- `fetch_wechat_articles.py` - 早期测试脚本
- `fetch_wechat_browser.py` - 使用搜狗搜索（已废弃）
- `wechat_playwright.py` - Playwright 方案（不稳定）
- `test_playwright.py` - 测试脚本
- `wechat_api.py` - 直接调用 API（缺少认证）
- `wechat_monitor.py` - 早期监控脚本

### 📝 参考

- `fetch_wechat_cdp.py` - CDP 方案的早期版本（async 有问题，已被 fetch_wechat_today.py 替代）

## 技术方案

### 为什么不用搜狗微信搜索？

❌ **搜狗微信搜索的问题：**
- 反爬机制严重
- 返回空结果或被拦截
- 数据不准确
- 需要处理验证码

### ✅ 正确方案：CDP Proxy + 微信公众平台 API

**原理：**
1. 启动 CDP Proxy 连接用户的 Chrome 浏览器
2. 在浏览器中打开微信公众平台 (mp.weixin.qq.com)
3. 利用浏览器的完整登录态执行 fetch 调用官方 API
4. 自动处理所有认证和 CSRF token

**关键技术细节：**
- 使用**同步 XMLHttpRequest** 而非 async fetch（CDP 的 /eval 端点对 Promise 处理有 bug）
- 复用已打开的标签页而非每次创建新标签页（提高效率和稳定性）

## 快速开始

### 一键执行（推荐）

```bash
./run.sh
```

这个脚本会自动：
1. 检查 CDP Proxy 状态
2. 检查浏览器登录状态
3. 获取今日文章
4. 生成 HTML 页面
5. 询问是否提交到 Git

### 手动执行

如果需要更细粒度的控制，可以手动执行各个步骤。

## 使用流程

### 前置条件

1. **启动 CDP Proxy**
   ```bash
   # 确保 CDP Proxy 在 localhost:3456 运行
   curl http://localhost:3456/health
   ```

2. **登录微信公众平台**
   - 在 Chrome 浏览器中打开 https://mp.weixin.qq.com/
   - 确保已登录

3. **获取 token**
   - 在微信公众平台任意页面的 URL 中找到 `token=xxxxx` 参数
   - 更新 `fetch_wechat_today.py` 中的 `TOKEN` 变量

### 执行步骤

**方式一：一键执行（推荐）**

```bash
./run.sh
```

**方式二：手动执行**

```bash
# 1. 获取今天的文章
python fetch_wechat_today.py

# 2. 生成 HTML 页面
python generate_html.py wechat_today_$(date +%Y%m%d).json

# 3. 提交到 Git（可选）
git add index.html wechat_today_*.json
git commit -m "Update: $(date +%Y-%m-%d) articles"
git push
```

## 项目文件说明

### 核心脚本

- `fetch_wechat_today.py` - 获取今日文章（主要脚本）
- `generate_html.py` - 生成 HTML 页面
- `run.sh` - 一键执行脚本

### 配置文件

- `CLAUDE.md` - 项目文档（本文件）
- `.claude/skills/wechat-news.md` - Claude Code skill 定义

### 输出文件

- `wechat_today_YYYYMMDD.json` - 每日文章数据
- `index.html` - 生成的 HTML 页面

### 废弃文件（不要使用）

- `fetch_all_wechat.py` - 使用搜狗搜索（已废弃）
- `fetch_wechat_cdp.py` - 早期 CDP 版本（已被 fetch_wechat_today.py 替代）
- 其他 `fetch_*.py` 和 `wechat_*.py` - 早期测试脚本

## 数据格式

### API 返回字段

```json
{
  "公众号名称": [
    {
      "title": "文章标题",
      "link": "https://mp.weixin.qq.com/s/xxxxx",
      "digest": "文章摘要",
      "time": "2026-04-02 09:30:05"
    }
  ]
}
```

### 注意事项

- **不包含**：阅读量、评论数（需要访问文章详情页才能获取）
- **时间戳**：`update_time` 字段是发布时间的 Unix 时间戳

## 常见问题

### Q: 为什么返回空数据？

A: 检查以下几点：
1. CDP Proxy 是否正常运行
2. 浏览器是否已登录微信公众平台
3. token 是否过期（从浏览器 URL 中重新获取）
4. 标签页 ID 是否正确（可以通过 `curl http://localhost:3456/targets` 查看）

### Q: 为什么不用 async/await？

A: CDP Proxy 的 `/eval` 端点对 Promise 返回值处理不完善，异步代码会返回空对象 `{}`。使用同步的 XMLHttpRequest 更可靠。

### Q: 如何添加新的公众号？

A: 
1. 在微信公众平台搜索公众号
2. 从 searchbiz API 响应中提取 fakeid
3. 添加到 `ACCOUNTS` 字典中

## 项目历史

详见 `.claude/projects/-Users-zouapeng-Downloads-03------news1/memory/project_wechat_lessons.md`

记录了所有踩过的坑和最终解决方案。
