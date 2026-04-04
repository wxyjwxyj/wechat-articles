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

DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \$HOME"
  "rm -rf /*"
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

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
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

exit 0
