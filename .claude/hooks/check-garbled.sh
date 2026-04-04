#!/bin/bash
# PostToolUse Hook：编辑后自动检查乱码

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

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# 只检查文本文件
case "$FILE_PATH" in
  *.py|*.md|*.json|*.yaml|*.yml|*.txt|*.cfg|*.ini|*.toml|*.sh|*.html|*.css|*.js)
    ;;
  *)
    exit 0
    ;;
esac

if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

GARBLED=$(grep -n '�' "$FILE_PATH" 2>/dev/null)

if [ -n "$GARBLED" ]; then
  echo "WARNING: 发现乱码 $FILE_PATH，请立即修复：" >&2
  echo "$GARBLED" >&2
  exit 0
fi

exit 0
