#!/usr/bin/env python3

import argparse
import csv
import datetime as dt
import pathlib
import re
import subprocess
import sys
import urllib.parse


MAX_RECIPIENTS = 20
DEFAULT_COMPOSE_DELAY = 2.0
DEFAULT_POST_SEND_DELAY = 1.5
SCRIPT_PATH = pathlib.Path(__file__).parent / "scripts" / "send_message.applescript"
DEFAULT_LOG_PATH = pathlib.Path(__file__).parent / "sms_send.log"


def normalize_phone_number(value: str) -> str:
    trimmed = value.strip()
    has_plus = trimmed.startswith("+")
    digits = re.sub(r"\D", "", trimmed)

    if not digits:
        return ""

    normalized = f"+{digits}" if has_plus else digits
    if len(digits) < 8:
        raise ValueError(f"전화번호 형식이 너무 짧습니다: {value}")

    return normalized


def parse_recipients(raw_values: list[str]) -> list[str]:
    recipients: list[str] = []
    seen: set[str] = set()

    for raw in raw_values:
        for token in re.split(r"[\n,]", raw):
            normalized = normalize_phone_number(token)
            if normalized and normalized not in seen:
                seen.add(normalized)
                recipients.append(normalized)

    if not recipients:
        raise ValueError("수신자를 한 명 이상 입력하세요.")

    if len(recipients) > MAX_RECIPIENTS:
        raise ValueError(f"수신자는 최대 {MAX_RECIPIENTS}명까지 허용됩니다.")

    return recipients


def read_recipients_file(file_path: pathlib.Path) -> list[str]:
    if not file_path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {file_path}")

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []

    if file_path.suffix.lower() == ".csv":
        values: list[str] = []
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.reader(handle):
                values.extend(row)
        return values

    return [content]


def build_sms_url(phone_number: str, message: str) -> str:
    encoded_message = urllib.parse.quote(message, safe="")
    return f"sms:{phone_number}&body={encoded_message}"


def send_message(sms_url: str, compose_delay: float, post_send_delay: float) -> str:
    completed = subprocess.run(
        [
            "osascript",
            str(SCRIPT_PATH),
            sms_url,
            str(compose_delay),
            str(post_send_delay),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip() or "no-output"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Messages 앱을 순차 조작해 동일한 문구를 여러 수신자에게 보냅니다."
    )
    parser.add_argument(
        "--to",
        action="append",
        default=[],
        help="쉼표 또는 줄바꿈으로 구분된 전화번호 목록",
    )
    parser.add_argument(
        "--recipients-file",
        type=pathlib.Path,
        help="전화번호 목록 파일(.txt 또는 .csv)",
    )
    parser.add_argument("--message", required=True, help="보낼 문자 내용")
    parser.add_argument(
        "--compose-delay",
        type=float,
        default=DEFAULT_COMPOSE_DELAY,
        help="작성창이 뜨길 기다리는 초 단위 지연",
    )
    parser.add_argument(
        "--post-send-delay",
        type=float,
        default=DEFAULT_POST_SEND_DELAY,
        help="각 메시지 전송 후 다음 전송 전까지의 지연",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 발송 없이 정규화된 수신자와 링크만 출력",
    )
    parser.add_argument(
        "--log-file",
        type=pathlib.Path,
        default=DEFAULT_LOG_PATH,
        help="발송 로그를 남길 파일 경로",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    raw_values = list(args.to)
    if args.recipients_file:
        raw_values.extend(read_recipients_file(args.recipients_file))

    try:
        recipients = parse_recipients(raw_values)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))

    message = args.message.strip()
    if not message:
        parser.error("문자 내용은 비어 있을 수 없습니다.")

    urls = [build_sms_url(phone, message) for phone in recipients]

    if args.dry_run:
        for index, sms_url in enumerate(urls, start=1):
            print(f"{index:02d}. {sms_url}")
        return 0

    log_path = args.log_file
    print(f"{len(recipients)}명에게 순차 발송을 시작합니다.")
    print("Messages, Terminal, Python에 대한 접근성/자동화 권한이 필요할 수 있습니다.")
    print(f"로그 파일: {log_path}")

    with log_path.open("a", encoding="utf-8") as log_handle:
        log_handle.write(
            f"\n=== {dt.datetime.now().isoformat(timespec='seconds')} start recipients={len(recipients)} ===\n"
        )

        try:
            for index, sms_url in enumerate(urls, start=1):
                recipient = recipients[index - 1]
                print(f"[{index}/{len(urls)}] 발송 중: {recipient}")
                result = send_message(sms_url, args.compose_delay, args.post_send_delay)
                log_handle.write(f"{index:02d}\tOK\t{recipient}\t{result}\n")
                log_handle.flush()
                print(f"  -> {result}")
        except subprocess.CalledProcessError as error:
            recipient = recipients[index - 1]
            log_handle.write(f"{index:02d}\tERROR\t{recipient}\treturncode={error.returncode}\n")
            log_handle.flush()
            print("메시지 자동화 실행 중 오류가 발생했습니다.", file=sys.stderr)
            print(str(error), file=sys.stderr)
            return error.returncode or 1
        except KeyboardInterrupt:
            log_handle.write("INTERRUPTED\t사용자 중단\n")
            log_handle.flush()
            print("\n사용자 중단으로 발송을 멈췄습니다.", file=sys.stderr)
            return 130

    print("발송 작업을 마쳤습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
