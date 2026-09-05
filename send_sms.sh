#!/bin/zsh

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo '사용법: ./send_sms.sh "01012345678,01098765432" "보낼 문구"' >&2
  echo '예시:   ./send_sms.sh "01012345678,01098765432" "안녕하세요. 테스트 문자입니다."' >&2
  exit 1
fi

extra_args=("${@:3}")

python3 "$(dirname "$0")/send_bulk_sms.py" \
  --to "$1" \
  --message "$2" \
  --compose-delay "${SMS_COMPOSE_DELAY:-2.0}" \
  --post-send-delay "${SMS_POST_SEND_DELAY:-1.5}" \
  "${extra_args[@]}"
