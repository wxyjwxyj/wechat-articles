#!/usr/bin/env bash
# 每日自动采集 + 生成 HTML + 推送 GitHub
# 无交互，适合 launchd 定时调用

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/.claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"
CDP_PROXY="http://localhost:3456"
ERRORS=""

# 从 .env 加载环境变量（ANTHROPIC_API_KEY 等）
[ -f "$PROJECT_DIR/.env" ] && set -a && source "$PROJECT_DIR/.env" && set +a

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
notify() {
    # macOS 通知：$1=标题 $2=内容
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"default\"" 2>/dev/null
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

# 解析 --steps 参数（逗号分隔，如 wechat,bundle,generate）
# 不传则默认全量执行所有步骤
STEPS_ARG=""
ALL_STEPS="wechat parallel_collect bundle generate archive self_improve push_github publish_mp"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --steps) STEPS_ARG="$2"; shift 2 ;;
        *) shift ;;
    esac
done
STEPS="${STEPS_ARG//,/ }"
[ -z "$STEPS" ] && STEPS="$ALL_STEPS"

# 判断某步骤是否应该执行
should_run() { echo " $STEPS " | grep -q " $1 "; }

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

# 4.5 检查 Claude API 可用性（走 claude_call 同一路径，不可用时提前通知）
CLAUDE_OK=$(python -c "
from utils.claude import claude_call
import sys
try:
    # 跟实际流水线走同一条代码路径，max_tokens=1 最小消耗
    claude_call('hi', max_tokens=1)
    print('ok')
except Exception as e:
    print(f'fail:{str(e)[:80]}')
" 2>>"$LOG_FILE")
if [ "$CLAUDE_OK" = "ok" ]; then
    log "✓ Claude API 可用"
else
    log "⚠ Claude API 不可用（$CLAUDE_OK），build_bundle 将降级为关键词方案"
    CLAUDE_MSG=$(echo "$CLAUDE_OK" | head -c 80 | tr '"' "'")
    notify "AI日报 ⚠️" "Claude API 不可用：$CLAUDE_MSG"
fi

# 5. 采集今日微信文章
if should_run wechat; then
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
fi  # wechat

# 5.5-5.8 并行采集（HN / ArXiv / GitHub / RSS 互相独立）
# HN 直连更稳定；ArXiv / GitHub / RSS 需要走代理（系统 DNS 依赖代理）
if should_run parallel_collect; then
DIRECT="env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY"
log "并行采集 HN / ArXiv / GitHub Trending / RSS..."
$DIRECT python fetch_hackernews_today.py >> "$LOG_FILE" 2>&1 &
PID_HN=$!
python fetch_arxiv_today.py >> "$LOG_FILE" 2>&1 &
PID_ARXIV=$!
python fetch_github_trending_today.py >> "$LOG_FILE" 2>&1 &
PID_GH=$!
python fetch_rss_today.py >> "$LOG_FILE" 2>&1 &
PID_RSS=$!

wait $PID_HN;    HN_EXIT=$?
wait $PID_ARXIV; ARXIV_EXIT=$?
wait $PID_GH;    GH_EXIT=$?
wait $PID_RSS;   RSS_EXIT=$?
log "并行采集完成 HN=$HN_EXIT ArXiv=$ARXIV_EXIT GH=$GH_EXIT RSS=$RSS_EXIT"

if [ $HN_EXIT -ne 0 ]; then
    log "⚠ HN 采集失败: $(describe_exit $HN_EXIT) (exit=$HN_EXIT)"
    ERRORS="${ERRORS}HN:$(describe_exit $HN_EXIT) "
fi
if [ $ARXIV_EXIT -ne 0 ]; then
    log "⚠ ArXiv 采集失败: $(describe_exit $ARXIV_EXIT) (exit=$ARXIV_EXIT)"
    ERRORS="${ERRORS}ArXiv:$(describe_exit $ARXIV_EXIT) "
fi
if [ $GH_EXIT -ne 0 ]; then
    log "⚠ GitHub Trending 采集失败: $(describe_exit $GH_EXIT) (exit=$GH_EXIT)"
    ERRORS="${ERRORS}GitHub:$(describe_exit $GH_EXIT) "
fi
if [ $RSS_EXIT -ne 0 ]; then
    log "⚠ RSS 采集失败: $(describe_exit $RSS_EXIT) (exit=$RSS_EXIT)"
    ERRORS="${ERRORS}RSS:$(describe_exit $RSS_EXIT) "
fi
fi  # parallel_collect

# 6. 生成 bundle
if should_run bundle; then
log "生成 bundle..."
python scripts/build_bundle.py >> "$LOG_FILE" 2>&1
BUNDLE_EXIT=$?
if [ $BUNDLE_EXIT -ne 0 ]; then
    BUNDLE_REASON=$(describe_exit $BUNDLE_EXIT)
    log "⚠ bundle 生成失败: $BUNDLE_REASON (exit=$BUNDLE_EXIT)"
    ERRORS="${ERRORS}Bundle:${BUNDLE_REASON} "
    log "⚠ 跳过 HTML/草稿生成（bundle 失败）"
    # 删除旧 bundle 防止后续步骤误用过期数据
    rm -f bundle_today.json
    SKIP_GENERATE=1
fi
fi  # bundle

# 7. 检查是否有内容 + 日期校验 + 条数异常检测
if [ ! -f "bundle_today.json" ]; then
    log "⚠ 今日无内容，跳过 HTML 生成"
    notify "AI日报 ⚠" "今日无内容，跳过生成"
    exit 0
fi

# 条数异常检测：少于 20 条发出警告（正常应有 40-80 条）
BUNDLE_COUNT=$(python -c "import json; d=json.load(open('bundle_today.json')); print(len(d.get('items_flat', d.get('items', []))))" 2>/dev/null || echo "0")
BUNDLE_COUNT=${BUNDLE_COUNT:-0}
if [ "$BUNDLE_COUNT" -lt 20 ]; then
    log "⚠ 今日内容偏少：${BUNDLE_COUNT} 条（正常应有 40+ 条），请检查采集是否正常"
    notify "AI日报 ⚠️" "内容偏少：${BUNDLE_COUNT} 条，请检查采集"
    ERRORS="${ERRORS}内容偏少(${BUNDLE_COUNT}条) "
fi
if [ -z "$SKIP_GENERATE" ]; then
    BUNDLE_DATE=$(python -c "import json; print(json.load(open('bundle_today.json')).get('bundle_date',''))" 2>/dev/null)
    TODAY_DATE=$(date +%Y-%m-%d)
    if [ "$BUNDLE_DATE" != "$TODAY_DATE" ]; then
        log "⚠ bundle 日期不匹配(bundle=$BUNDLE_DATE, today=$TODAY_DATE)，跳过生成"
        ERRORS="${ERRORS}Bundle:日期不匹配 "
        SKIP_GENERATE=1
    fi
fi

if [ -z "$SKIP_GENERATE" ]; then

if should_run generate; then
# 8. 在 dev 分支生成 HTML
log "生成 HTML..."
python scripts/generate_html.py bundle_today.json >> "$LOG_FILE" 2>&1

# 9. 生成公众号发布稿
log "生成公众号发布稿..."
python scripts/generate_mp_article.py bundle_today.json >> "$LOG_FILE" 2>&1

# 10. 生成导读风 HTML（mp_article_preview.html + archive/digest_YYYY-MM-DD.html）
log "生成导读风 HTML..."
python scripts/generate_mp_html.py >> "$LOG_FILE" 2>&1
fi  # generate


fi  # SKIP_GENERATE

if [ -z "$SKIP_GENERATE" ]; then

if should_run archive; then
# 12. 归档当日 HTML
TODAY_DATE=$(date +%Y-%m-%d)
log "归档当日 HTML → archive/${TODAY_DATE}.html"
mkdir -p archive
cp today.html "archive/${TODAY_DATE}.html"
python scripts/generate_archive_index.py >> "$LOG_FILE" 2>&1

# 12.3 自学习：分析今日新闻，自动优化配置
if should_run self_improve; then
log "自学习分析..."
python scripts/self_improve.py >> "$LOG_FILE" 2>&1 || log "⚠ 自学习失败（不影响主流程）"
fi  # self_improve

# 12.5 在 dev 提交今日 HTML（必须先提交，步骤13才能正确拉取）
git add today.html mp_article_preview.html archive/ >> "$LOG_FILE" 2>&1
git commit -m "content: ${TODAY_DATE} HTML" >> "$LOG_FILE" 2>&1
fi  # archive

fi  # SKIP_GENERATE (archive + commit)

# 13. stash 保护 → 切 main → 推送
if [ -z "$SKIP_GENERATE" ] && should_run push_github; then
log "推送到 GitHub..."
git stash --include-untracked >> "$LOG_FILE" 2>&1
STASHED=$?
git checkout main >> "$LOG_FILE" 2>&1
git checkout dev -- today.html >> "$LOG_FILE" 2>&1
git checkout dev -- archive/ >> "$LOG_FILE" 2>&1
git checkout dev -- mp_article_preview.html >> "$LOG_FILE" 2>&1
git add today.html archive/ mp_article_preview.html
git commit -m "Update: $(date +%Y-%m-%d) articles" >> "$LOG_FILE" 2>&1
git push origin main >> "$LOG_FILE" 2>&1 || ERRORS="${ERRORS}GitHub推送失败 "

# 14. 切回 dev + 恢复 stash
git checkout dev >> "$LOG_FILE" 2>&1
[ $STASHED -eq 0 ] && git stash pop >> "$LOG_FILE" 2>&1
fi  # push_github

# publish_mp：提交公众号草稿（原来由 publish.plist 单独触发）
if should_run publish_mp; then
    log "提交公众号草稿..."
    python scripts/publish_to_mp.py >> "$LOG_FILE" 2>&1
fi

# 15. 统计结果并通知
ARTICLE_COUNT=$(python -c "import json; d=json.load(open('bundle_today.json')); print(len(d.get('items_flat', d.get('items', []))))" 2>/dev/null || echo "0")
if [ -z "$ERRORS" ]; then
    log "✅ 完成！共 ${ARTICLE_COUNT} 条"
    notify "AI日报 ✅" "采集完成：${ARTICLE_COUNT} 条，GitHub 已推送"
else
    log "⚠ 完成，但有问题：${ERRORS}"
    notify "AI日报 ⚠" "采集 ${ARTICLE_COUNT} 条 | 问题：${ERRORS}"
fi

# 15.5 统计今日 Claude API token 消耗
python -c "
import re
total_in, total_out = 0, 0
with open('$LOG_FILE', encoding='utf-8', errors='replace') as f:
    for line in f:
        m = re.search(r'claude_call: .+? (\d+) in / (\d+) out', line)
        if m:
            total_in += int(m.group(1))
            total_out += int(m.group(2))
total = total_in + total_out
print(f'今日 token 消耗: {total_in:,} in + {total_out:,} out = {total:,} total')
" | tee -a "$LOG_FILE"

# 16. 记录可观测性指标到 metrics.csv
METRICS_FILE="$PROJECT_DIR/.claude/metrics.csv"
if [ ! -f "$METRICS_FILE" ]; then
    echo "date,time,total,wechat,hackernews,arxiv,github,rss,errors,status" > "$METRICS_FILE"
fi
export METRICS_DATE="$(date +%Y-%m-%d)"
export METRICS_TIME="$(date +%H:%M)"
export METRICS_TOTAL="${ARTICLE_COUNT:-0}"
export METRICS_ERRORS="${ERRORS:-}"
export METRICS_FILE="$METRICS_FILE"
python -c "
import sqlite3, csv, os
from datetime import timezone, timedelta

today = os.environ['METRICS_DATE']
now = os.environ['METRICS_TIME']
total = os.environ.get('METRICS_TOTAL', '0') or '0'
errors = os.environ.get('METRICS_ERRORS', '').strip() or 'none'
status = 'ok' if errors == 'none' else 'warn'
metrics_file = os.environ['METRICS_FILE']

conn = sqlite3.connect('content.db')
rows = conn.execute('''
    SELECT s.type, COUNT(i.id)
    FROM items i JOIN sources s ON i.source_id = s.id
    WHERE date(i.published_at, \"+8 hours\") = ? OR date(i.created_at) = ?
    GROUP BY s.type
''', (today, today)).fetchall()
conn.close()
src = dict(rows)

with open(metrics_file, 'a', newline='') as f:
    w = csv.writer(f)
    w.writerow([today, now, total,
        src.get('wechat',0), src.get('hackernews',0),
        src.get('arxiv',0), src.get('github_trending',0), src.get('rss',0),
        errors, status])
print('指标已记录')
" >> "$LOG_FILE" 2>&1

# 17. 清理 30 天前的旧日志
find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null
