#!/bin/bash
# 通过 CDP 快速查询 Xiaomi MiMo Token Plan 套餐余额和使用量
# 依赖：Chrome 已开启 remote debugging，CDP Proxy 运行在 localhost:3456

PROXY="http://localhost:3456"

check_deps() {
    if ! curl -s "$PROXY" > /dev/null 2>&1; then
        echo "CDP Proxy 未运行，尝试启动..."
        bash ~/.claude/skills/web-access/scripts/check-deps.sh > /dev/null 2>&1
        if ! curl -s "$PROXY" > /dev/null 2>&1; then
            echo "启动失败，请确认 Chrome 已开启 remote debugging"
            exit 1
        fi
    fi
}

main() {
    check_deps
    echo "⏳ 正在查询 MiMo 套餐用量..."

    # 打开页面
    local RESP
    RESP=$(curl -s "$PROXY/new?url=https://platform.xiaomimimo.com/console/plan-manage")
    local TARGET
    TARGET=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('targetId',''))" 2>/dev/null)

    if [ -z "$TARGET" ]; then
        echo "无法创建 CDP tab"
        exit 1
    fi

    # 等待页面加载
    sleep 5

    # 提取数据（CDP eval 返回 {"value":"<json string>"}）
    local RAW
    RAW=$(curl -s -X POST "$PROXY/eval?target=$TARGET" \
        -d '(()=>{
            const text = document.querySelector("#root")?.innerText || "";
            const planMatch = text.match(/订阅套餐[\s\S]*?\n\s*(\S[^\n]+)/);
            const billingMatch = text.match(/(连续包月|按月订阅)/);
            const validMatch = text.match(/有效期至\s*([^\n]+)/);
            const renewalMatch = text.match(/(自动续费|不续费)/);
            const usageMatch = text.match(/([\d,]+)\s*\/\s*([\d,]+)/);
            const pctMatch = text.match(/已使用\s*([\d.]+%)/);
            return JSON.stringify({
                plan: planMatch ? planMatch[1].trim() : null,
                billing: billingMatch ? billingMatch[1] : null,
                validUntil: validMatch ? validMatch[1].trim() : null,
                autoRenewal: renewalMatch ? renewalMatch[1] : null,
                used: usageMatch ? usageMatch[1] : null,
                total: usageMatch ? usageMatch[2] : null,
                percentage: pctMatch ? pctMatch[1] : null,
            });
        })()')

    # 关闭 tab
    curl -s "$PROXY/close?target=$TARGET" > /dev/null 2>&1

    # 先提取 CDP eval 的 value（外层 JSON），再解析内层数据 JSON
    local JSON
    JSON=$(echo "$RAW" | python3 -c "import sys,json;print(json.load(sys.stdin).get('value','{}'))" 2>/dev/null)
    local PLAN USED TOTAL PCT VALID BILLING RENEWAL
    PLAN=$(echo "$JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('plan','--'))" 2>/dev/null)
    USED=$(echo "$JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('used','--'))" 2>/dev/null)
    TOTAL=$(echo "$JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('total','--'))" 2>/dev/null)
    PCT=$(echo "$JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('percentage','--'))" 2>/dev/null)
    VALID=$(echo "$JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('validUntil','--'))" 2>/dev/null)
    BILLING=$(echo "$JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('billing','--'))" 2>/dev/null)
    RENEWAL=$(echo "$JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('autoRenewal','--'))" 2>/dev/null)

    if [ "$PLAN" = "--" ] || [ "$PLAN" = "null" ] || [ -z "$PLAN" ]; then
        echo "获取失败。可能未登录，请在 Chrome 中登录 https://platform.xiaomimimo.com 后重试。"
        exit 1
    fi

    # 格式化数字
    local USED_FMT TOTAL_FMT
    USED_FMT=$(echo "$USED" | sed 's/,//g' | python3 -c "print(f'{int(input()):,}')" 2>/dev/null || echo "$USED")
    TOTAL_FMT=$(echo "$TOTAL" | sed 's/,//g' | python3 -c "print(f'{int(input()):,}')" 2>/dev/null || echo "$TOTAL")

    # 进度条
    local PCT_NUM BAR
    PCT_NUM=$(echo "$PCT" | sed 's/%//')
    local WIDTH=30
    local FILLED
    FILLED=$(python3 -c "print(int($PCT_NUM * $WIDTH / 100))" 2>/dev/null || echo "0")
    BAR=""
    for ((i=0; i<WIDTH; i++)); do
        if [ "$i" -lt "$FILLED" ]; then
            BAR="${BAR}█"
        else
            BAR="${BAR}░"
        fi
    done

    echo ""
    echo "  Xiaomi MiMo Token Plan"
    echo "  ─────────────────────────────────────"
    echo "  套餐：   $PLAN ($BILLING)"
    echo "  有效期： $VALID"
    echo "  续费：   $RENEWAL"
    echo "  ─────────────────────────────────────"
    echo "  用量：   $USED_FMT / $TOTAL_FMT Credits"
    printf "  进度：   %s %s\n" "$BAR" "$PCT"
    echo ""
    echo "  详情： https://platform.xiaomimimo.com/console/plan-manage"
    echo ""
}

main
