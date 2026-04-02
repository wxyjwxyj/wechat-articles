#!/bin/bash
# 一键获取微信公众号文章并生成 HTML

set -e  # 遇到错误立即退出

echo "========================================="
echo "  微信公众号文章自动获取与发布"
echo "========================================="
echo ""

# 0. 检查配置文件
echo "📋 检查配置文件..."
if [ ! -f "config.json" ]; then
    echo "✗ 找不到 config.json"
    echo "  请复制 config.example.json 为 config.json 并填写配置"
    exit 1
fi
echo "✓ 配置文件存在"
echo ""

# 读取 CDP Proxy 地址
CDP_PROXY=$(python3 -c "import json; print(json.load(open('config.json'))['cdp_proxy'])")

# 1. 检查 CDP Proxy
echo "📡 检查 CDP Proxy..."
if ! curl -s ${CDP_PROXY}/health > /dev/null 2>&1; then
    echo "✗ CDP Proxy 未运行！"
    echo "  请先启动 CDP Proxy"
    exit 1
fi
echo "✓ CDP Proxy 正常运行"
echo ""

# 2. 检查浏览器登录状态
echo "🌐 检查浏览器状态..."
if ! curl -s ${CDP_PROXY}/targets | grep -q "mp.weixin.qq.com"; then
    echo "⚠️  未检测到微信公众平台标签页"
    echo "  正在打开..."
    curl -s "${CDP_PROXY}/new?url=https://mp.weixin.qq.com/" > /dev/null
    sleep 2
    echo "✓ 已打开微信公众平台，请确保已登录"
    echo ""
    read -p "按回车键继续..."
else
    echo "✓ 微信公众平台已打开"
fi
echo ""

# 3. 获取今日文章
echo "📥 获取今日文章..."
python fetch_wechat_today.py
if [ $? -ne 0 ]; then
    echo "✗ 获取文章失败！"
    exit 1
fi
echo ""

# 4. 生成 HTML
echo "🎨 生成 HTML 页面..."
TODAY=$(date +%Y%m%d)
JSON_FILE="wechat_today_${TODAY}.json"

if [ ! -f "$JSON_FILE" ]; then
    echo "✗ 找不到文件: $JSON_FILE"
    exit 1
fi

python generate_html.py "$JSON_FILE"
if [ $? -ne 0 ]; then
    echo "✗ 生成 HTML 失败！"
    exit 1
fi
echo ""

# 5. 询问是否提交到 Git
echo "========================================="
echo "✓ 完成！"
echo ""
echo "生成的文件："
echo "  - index.html"
echo "  - $JSON_FILE"
echo ""

if git rev-parse --git-dir > /dev/null 2>&1; then
    read -p "是否提交到 Git? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "📝 提交到 Git..."
        git add index.html "$JSON_FILE"
        git commit -m "Update: $(date +%Y-%m-%d) articles"
        echo ""
        read -p "是否推送到远程仓库? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push
            echo "✓ 已推送到远程仓库"
        fi
    fi
fi

echo ""
echo "========================================="
echo "🎉 全部完成！"
echo "========================================="
