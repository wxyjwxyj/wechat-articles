#!/bin/bash
# PreToolUse Hook：阻止编辑受保护的文件

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    ti = data.get('tool_input', {})
    print(ti.get('file_path', '') or ti.get('filename', ''))
except:
    print('')
" 2>/dev/null)

# 没有文件路径的操作直接放行
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

PROTECTED_PATTERNS=(
  ".env"
  "config.json"
  "content.db"
  ".pem"
  ".key"
  ".claude/hooks/"
)

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "已阻止：$FILE_PATH 匹配受保护模式 '$pattern'，如需修改请手动操作" >&2
    exit 2
  fi
done

exit 0
