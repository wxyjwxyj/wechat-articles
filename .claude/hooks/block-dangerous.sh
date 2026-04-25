#!/bin/bash
# PreToolUse Hook：阻止危险的 Bash 命令

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null)

if [ -z "$COMMAND" ]; then
  exit 0
fi

# 子串匹配模式（包含即拦截）
SUBSTRING_PATTERNS=(                                                                                                                  
  "rm -rf ~"
  "rm -rf \$HOME"                                                                                                                     
  "> /dev/sd"   
  "mkfs."                                                                                                                             
  "dd if="
  ":(){:|:&};:"                                                                                                                       
  "chmod -R 777 /"
  "git push --force origin main"
  "git push --force origin master"
  "git push -f origin main"
  "git push -f origin master"
  "git reset --hard origin"
  "git clean -fd"
  "DROP DATABASE"
  "DROP TABLE"
)

# 正则匹配模式（精确语义，避免误判正常路径）
REGEX_PATTERNS=(
  "rm -rf /[[:space:]]*$"
  "rm -rf /\*"
)

for pattern in "${SUBSTRING_PATTERNS[@]}"; do
  if [[ "$COMMAND" == *"$pattern"* ]]; then
    echo "BLOCKED: command matches dangerous pattern '$pattern'" >&2
    cat <<EOF                                                                                                                         
{
  "hookSpecificOutput": {                                                                                                             
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked dangerous command: $pattern"
  }
}
EOF
    exit 2
  fi
done

for pattern in "${REGEX_PATTERNS[@]}"; do
  if [[ "$COMMAND" =~ $pattern ]]; then
    echo "BLOCKED: command matches dangerous pattern '$pattern'" >&2
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked dangerous command: $pattern"
  }
}
EOF
    exit 2
  fi
done


exit 0
