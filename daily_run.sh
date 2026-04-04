#!/usr/bin/env bash
# 每日自动采集 + 生成 HTML + 推送 GitHub
# 无交互，适合 launchd 定时调用

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$PROJECT_DIR/.claude/daily_run.log"
CDP_PROXY="http://localhost:3456"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

cd "$PROJECT_DIR" || exit 1
log "========== 开始每日采集 =========="

# 1. 检查 CDP Proxy
if ! curl -s "$CDP_PROXY/health" > /dev/null 2>&1; then
    log "❌ CDP Proxy 未运行，跳过今日采集"
    exit 0
fi

# 2. 检查微信公众平台标签页
if ! curl -s "$CDP_PROXY/targets" | grep -q "mp.weixin.qq.com"; then
    log "❌ 未找到微信公众平台标签页，跳过今日采集"
    exit 0
fi

log "✓ CDP Proxy 正常，微信标签页已打开"

# 3. 确保在 dev 分支（代码在这里）
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "dev" ]; then
    git checkout dev >> "$LOG_FILE" 2>&1
fi

# 4. 初始化 sources
log "初始化 sources..."
python scripts/seed_sources.py >> "$LOG_FILE" 2>&1

# 5. 采集今日文章
log "采集今日文章..."
python fetch_wechat_today.py >> "$LOG_FILE" 2>&1

# 6. 生成 bundle
log "生成 bundle..."
python scripts/build_bundle.py >> "$LOG_FILE" 2>&1

# 7. 检查是否有内容
if [ ! -f "bundle_today.json" ]; then
    log "⚠ 今日无内容，跳过 HTML 生成"
    exit 0
fi

# 8. 在 dev 分支生成 HTML
log "生成 HTML..."
python generate_html.py bundle_today.json >> "$LOG_FILE" 2>&1

# 9. 生成公众号发布稿
log "生成公众号发布稿..."
python scripts/generate_mp_article.py bundle_today.json >> "$LOG_FILE" 2>&1

# 11. 切换到 main，把 index.html 带过去，推送
log "推送 index.html 到 GitHub..."
git checkout main >> "$LOG_FILE" 2>&1
git checkout dev -- index.html >> "$LOG_FILE" 2>&1
git add index.html
git commit -m "Update: $(date +%Y-%m-%d) articles" >> "$LOG_FILE" 2>&1
git push origin main >> "$LOG_FILE" 2>&1

# 12. 切回 dev
git checkout dev >> "$LOG_FILE" 2>&1

log "✅ 完成！"
