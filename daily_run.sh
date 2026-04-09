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

# exit code → 失败原因映射
describe_exit() {
    case "$1" in
        0)  echo "" ;;
        10) echo "CDP Proxy 未运行" ;;
        11) echo "微信登录态过期" ;;
        12) echo "采集超时/网络错误" ;;
        13) echo "AI API 调用失败" ;;
        14) echo "草稿提交失败" ;;
        15) echo "数据处理失败" ;;
        *)  echo "未知错误(code=$1)" ;;
    esac
}

cd "$PROJECT_DIR" || exit 1
log "========== 开始每日采集 =========="

# 1. 检查 CDP Proxy
if ! curl -s "$CDP_PROXY/health" > /dev/null 2>&1; then
    log "❌ CDP Proxy 未运行，跳过今日采集"
    notify "AI日报 ❌" "CDP Proxy 未运行，今日采集跳过"
    exit 10
fi

# 2. 检查微信公众平台标签页，没有则自动打开
if ! curl -s "$CDP_PROXY/targets" | grep -q "mp.weixin.qq.com"; then
    log "⚠ 未找到微信标签页，自动打开..."
    curl -s "$CDP_PROXY/new?url=https://mp.weixin.qq.com" > /dev/null 2>&1
    sleep 5
    # 再检查一次
    if ! curl -s "$CDP_PROXY/targets" | grep -q "mp.weixin.qq.com"; then
        log "❌ 微信标签页打开失败，跳过今日采集"
        notify "AI日报 ❌" "微信标签页打开失败，请检查 Chrome"
        exit 11
    fi
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

# 5. 采集今日微信文章
log "采集今日微信文章..."
python fetch_wechat_today.py >> "$LOG_FILE" 2>&1
WX_EXIT=$?
if [ $WX_EXIT -eq 11 ]; then
    # 登录态过期：自动打开微信公众平台，等待登录后重试
    log "⚠ 微信登录态过期，自动打开登录页面，60秒后重试..."
    notify "AI日报 ⚠️" "微信登录态过期，请扫码登录，60秒后自动重试"
    open -a "Google Chrome" "https://mp.weixin.qq.com"
    sleep 60
    log "重试采集微信文章..."
    python fetch_wechat_today.py >> "$LOG_FILE" 2>&1
    WX_EXIT=$?
fi
if [ $WX_EXIT -ne 0 ]; then
    WX_REASON=$(describe_exit $WX_EXIT)
    log "⚠ 微信采集失败: $WX_REASON (exit=$WX_EXIT)"
    ERRORS="${ERRORS}微信:${WX_REASON} "
    # CDP/登录问题不影响 HN 采集，但需要记录
fi

# 5.5 采集 Hacker News AI 文章（不依赖 CDP，独立运行）
log "采集 Hacker News AI 文章..."
python fetch_hackernews_today.py >> "$LOG_FILE" 2>&1
HN_EXIT=$?
if [ $HN_EXIT -ne 0 ]; then
    HN_REASON=$(describe_exit $HN_EXIT)
    log "⚠ HN 采集失败: $HN_REASON (exit=$HN_EXIT)"
    ERRORS="${ERRORS}HN:${HN_REASON} "
fi

# 5.6 采集 ArXiv AI 论文（不依赖 CDP，独立运行）
log "采集 ArXiv AI 论文..."
python fetch_arxiv_today.py >> "$LOG_FILE" 2>&1
ARXIV_EXIT=$?
if [ $ARXIV_EXIT -ne 0 ]; then
    ARXIV_REASON=$(describe_exit $ARXIV_EXIT)
    log "⚠ ArXiv 采集失败: $ARXIV_REASON (exit=$ARXIV_EXIT)"
    ERRORS="${ERRORS}ArXiv:${ARXIV_REASON} "
fi

# 5.7 采集 GitHub Trending AI 仓库（不依赖 CDP，独立运行）
log "采集 GitHub Trending AI 仓库..."
python fetch_github_trending_today.py >> "$LOG_FILE" 2>&1
GH_EXIT=$?
if [ $GH_EXIT -ne 0 ]; then
    GH_REASON=$(describe_exit $GH_EXIT)
    log "⚠ GitHub Trending 采集失败: $GH_REASON (exit=$GH_EXIT)"
    ERRORS="${ERRORS}GitHub:${GH_REASON} "
fi

# 5.8 采集 RSS 文章（不依赖 CDP，独立运行）
log "采集 RSS 文章..."
python fetch_rss_today.py >> "$LOG_FILE" 2>&1
RSS_EXIT=$?
if [ $RSS_EXIT -ne 0 ]; then
    RSS_REASON=$(describe_exit $RSS_EXIT)
    log "⚠ RSS 采集失败: $RSS_REASON (exit=$RSS_EXIT)"
    ERRORS="${ERRORS}RSS:${RSS_REASON} "
fi

# 6. 生成 bundle
log "生成 bundle..."
python scripts/build_bundle.py >> "$LOG_FILE" 2>&1
BUNDLE_EXIT=$?
if [ $BUNDLE_EXIT -ne 0 ]; then
    BUNDLE_REASON=$(describe_exit $BUNDLE_EXIT)
    log "⚠ bundle 生成失败: $BUNDLE_REASON (exit=$BUNDLE_EXIT)"
    ERRORS="${ERRORS}Bundle:${BUNDLE_REASON} "
fi

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
python scripts/publish_to_mp.py >> "$LOG_FILE" 2>&1
PUB_EXIT=$?
if [ $PUB_EXIT -ne 0 ]; then
    PUB_REASON=$(describe_exit $PUB_EXIT)
    log "⚠ 草稿提交失败: $PUB_REASON (exit=$PUB_EXIT)"
    ERRORS="${ERRORS}草稿:${PUB_REASON} "
fi

# 12. 归档当日 HTML
TODAY_DATE=$(date +%Y-%m-%d)
log "归档当日 HTML → archive/${TODAY_DATE}.html"
mkdir -p archive
cp today.html "archive/${TODAY_DATE}.html"
python scripts/generate_archive_index.py >> "$LOG_FILE" 2>&1

# 12.5 在 dev 提交今日 HTML（必须先提交，步骤13才能正确拉取）
git add today.html mp_article_preview.html archive/ >> "$LOG_FILE" 2>&1
git commit -m "content: ${TODAY_DATE} HTML" >> "$LOG_FILE" 2>&1

# 13. 切换到 main，把 today.html / archive/ / mp_article_preview.html 带过去，推送
log "推送到 GitHub..."
git checkout main >> "$LOG_FILE" 2>&1
git checkout dev -- today.html >> "$LOG_FILE" 2>&1
git checkout dev -- archive/ >> "$LOG_FILE" 2>&1
git checkout dev -- mp_article_preview.html >> "$LOG_FILE" 2>&1
git add today.html archive/ mp_article_preview.html
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
    notify "AI日报 ⚠" "采集 ${ARTICLE_COUNT} 条 | 问题：${ERRORS}"
fi

# 16. 清理 30 天前的旧日志
find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null
