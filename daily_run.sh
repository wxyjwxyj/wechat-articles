#!/usr/bin/env bash
# 每日自动采集 + 生成 HTML + 推送 GitHub
# 无交互，适合 launchd 定时调用

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/.claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"
CDP_PROXY="http://localhost:3456"
ERRORS=""

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
notify() {
    # macOS 通知：$1=标题 $2=内容
    osascript -e "display notification \"$2\" with title \"$1\"" 2>/dev/null
}

cd "$PROJECT_DIR" || exit 1
log "========== 开始每日采集 =========="

# 1. 检查 CDP Proxy
if ! curl -s "$CDP_PROXY/health" > /dev/null 2>&1; then
    log "❌ CDP Proxy 未运行，跳过今日采集"
    notify "AI日报 ❌" "CDP Proxy 未运行，今日采集跳过"
    exit 0
fi

# 2. 检查微信公众平台标签页
if ! curl -s "$CDP_PROXY/targets" | grep -q "mp.weixin.qq.com"; then
    log "❌ 未找到微信公众平台标签页，跳过今日采集"
    notify "AI日报 ❌" "未找到微信公众平台标签页，请检查浏览器"
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
    notify "AI日报 ⚠" "今日无内容，跳过生成"
    exit 0
fi

# 8. 在 dev 分支生成 HTML
log "生成 HTML..."
python generate_html.py bundle_today.json >> "$LOG_FILE" 2>&1

# 9. 生成公众号发布稿
log "生成公众号发布稿..."
python scripts/generate_mp_article.py bundle_today.json >> "$LOG_FILE" 2>&1

# 10. 生成导读风 HTML（mp_article_preview.html + archive/digest_YYYY-MM-DD.html）
log "生成导读风 HTML..."
python scripts/generate_mp_html.py >> "$LOG_FILE" 2>&1

# 11. 提交到公众号草稿箱
log "提交到公众号草稿箱..."
python scripts/publish_to_mp.py >> "$LOG_FILE" 2>&1 || { log "⚠ 草稿提交失败，继续"; ERRORS="${ERRORS}草稿提交失败 "; }

# 12. 归档当日 HTML
TODAY_DATE=$(date +%Y-%m-%d)
log "归档当日 HTML → archive/${TODAY_DATE}.html"
mkdir -p archive
cp today.html "archive/${TODAY_DATE}.html"
python scripts/generate_archive_index.py >> "$LOG_FILE" 2>&1

# 13. 切换到 main，把 index.html / today.html / archive/ 带过去，推送
log "推送到 GitHub..."
git checkout main >> "$LOG_FILE" 2>&1
git checkout dev -- index.html >> "$LOG_FILE" 2>&1
git checkout dev -- today.html >> "$LOG_FILE" 2>&1
git checkout dev -- archive/ >> "$LOG_FILE" 2>&1
git checkout dev -- mp_article_preview.html >> "$LOG_FILE" 2>&1
git add index.html today.html archive/ mp_article_preview.html
git commit -m "Update: $(date +%Y-%m-%d) articles" >> "$LOG_FILE" 2>&1
git push origin main >> "$LOG_FILE" 2>&1 || ERRORS="${ERRORS}GitHub推送失败 "

# 14. 切回 dev
git checkout dev >> "$LOG_FILE" 2>&1

# 15. 统计结果并通知
ARTICLE_COUNT=$(python -c "import json; d=json.load(open('bundle_today.json')); print(len(d.get('items_flat', d.get('items', []))))" 2>/dev/null || echo "?")
if [ -z "$ERRORS" ]; then
    log "✅ 完成！共 ${ARTICLE_COUNT} 条"
    notify "AI日报 ✅" "采集完成：${ARTICLE_COUNT} 条，草稿已提交，GitHub 已推送"
else
    log "⚠ 完成，但有问题：${ERRORS}"
    notify "AI日报 ⚠" "采集 ${ARTICLE_COUNT} 条，但：${ERRORS}"
fi

# 16. 清理 30 天前的旧日志
find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null
