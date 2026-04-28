#!/bin/bash
# 阻止 merge dev → main，只允许 checkout dev -- <files> 方式更新 main
# 安装: ln -s ../../.claude/hooks/prevent-main-merge.sh .git/hooks/prepare-commit-msg

BRANCH=$(git rev-parse --abbrev-ref HEAD)
MSG_FILE="$1"
MSG_SOURCE="$2"

# 只拦截 main 分支上的 merge
if [ "$BRANCH" = "main" ] && [ "$MSG_SOURCE" = "merge" ]; then
    echo "============================================" >&2
    echo "  BLOCKED: 不允许 git merge dev → main" >&2
    echo "  正确做法: git checkout dev -- <html文件>" >&2
    echo "  详见 CLAUDE.md 分支约定" >&2
    echo "============================================" >&2
    exit 1
fi

exit 0
