# 微信公众号文章监控

自动获取指定微信公众号的最新文章，生成 HTML 汇总页面。

## 监控的公众号

- 量子位
- AI寒武纪
- 机器之心
- 数字生命卡兹克
- APPSO

## 快速开始

### 1. 配置

```bash
# 复制配置模板
cp config.example.json config.json

# 编辑配置文件，填写你的 token
# token 从微信公众平台 URL 中获取: https://mp.weixin.qq.com/...?token=YOUR_TOKEN
```

`config.json` 示例：
```json
{
  "accounts": {
    "量子位": "MzIzNjc1NzUzMw==",
    ...
  },
  "token": "YOUR_TOKEN_HERE",
  "target_id": "",  // 可选，留空自动查找
  "cdp_proxy": "http://localhost:3456"
}
```

### 2. 前置条件

1. 启动 CDP Proxy（端口 3456）
2. 在 Chrome 浏览器中登录微信公众平台 (mp.weixin.qq.com)

### 3. 一键执行

```bash
./run.sh
```

这会自动：
- ✅ 检查环境
- 📥 获取今日文章
- 🎨 生成 HTML 页面
- 📝 可选提交到 Git

## 手动执行

```bash
# 1. 获取今日文章
python fetch_wechat_today.py

# 2. 生成 HTML
python generate_html.py wechat_today_20260402.json

# 3. 查看结果
open index.html
```

## 输出示例

```
获取 量子位 今天的文章...
  找到 2 篇
    2026-04-02 09:30:05 - 封不住！Claude Code爆改Python版...
    2026-04-02 09:30:05 - 再融20亿！星海图把具身智能头部门槛...

✓ 结果已保存到: wechat_today_20260402.json
✓ HTML 已生成: index.html
```

## 技术方案

- **数据来源**：微信公众平台官方 API
- **认证方式**：CDP Proxy + 浏览器登录态
- **数据格式**：JSON → HTML

## 常见问题

**Q: 为什么不用搜狗微信搜索？**

A: 搜狗有反爬机制，数据不准确。我们使用官方 API，更稳定可靠。

**Q: 返回空数据怎么办？**

A: 检查：
1. CDP Proxy 是否运行
2. 浏览器是否登录微信公众平台
3. Token 是否过期（从浏览器 URL 中更新）

**Q: 如何添加新的公众号？**

A: 编辑 `fetch_wechat_today.py` 中的 `ACCOUNTS` 字典，添加公众号名称和 fakeid。

## 项目结构

```
.
├── run.sh                      # 一键执行脚本
├── fetch_wechat_today.py       # 获取今日文章
├── generate_html.py            # 生成 HTML
├── index.html                  # 输出的 HTML 页面
├── wechat_today_*.json         # 每日文章数据
├── CLAUDE.md                   # 详细文档
└── .claude/
    └── skills/
        └── wechat-news.md      # Claude Code skill
```

## License

MIT
