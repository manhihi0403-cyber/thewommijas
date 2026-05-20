import argparse
import calendar
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


DEFAULT_CONFIG = {
    "year": 2026,
    "month": 8,
    "reservation_type": "party",
    "watch_days": [],
    "check_interval_seconds": 60,
    "checks_per_run": 5,
    "notify_when_available": True,
    "notify_when_no_available": True,
    "include_status_list": True,
    "timezone": "Asia/Seoul",
}

AVAILABLE_WORDS = ("예약가능", "잔여")
UNAVAILABLE_WORDS = ("마감", "불가능", "예약불가", "불가")


def load_config(path: str) -> dict:
    config_path = Path(path)
    config = DEFAULT_CONFIG.copy()
    user_config = {}

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as config_file:
            user_config = json.load(config_file)
        config.update(user_config)

    if "type" in user_config and "reservation_type" not in user_config:
        config["reservation_type"] = user_config["type"]

    config["year"] = int(config["year"])
    config["month"] = int(config["month"])
    config["reservation_type"] = str(config["reservation_type"])
    config["check_interval_seconds"] = max(10, int(config["check_interval_seconds"]))
    config["checks_per_run"] = max(1, int(config["checks_per_run"]))
    config["watch_days"] = normalize_watch_days(config)
    return config


def normalize_watch_days(config: dict) -> list[int]:
    _, last_day = calendar.monthrange(int(config["year"]), int(config["month"]))
    watch_days = config.get("watch_days") or []

    if not watch_days:
        return list(range(1, last_day + 1))

    normalized_days = sorted({int(day) for day in watch_days})
    invalid_days = [day for day in normalized_days if day < 1 or day > last_day]
    if invalid_days:
        raise ValueError(
            f"{config['year']}년 {config['month']}월에 없는 날짜입니다: {invalid_days}"
        )
    return normalized_days


def build_reservation_url(config: dict) -> str:
    return (
        "https://thewoomije.co.kr/reservation-step1.php"
        f"?year={config['year']}&month={config['month']}&type={config['reservation_type']}"
    )


def fetch_page(url: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; WoomijeReservationChecker/1.0; "
                "+https://github.com/actions)"
            )
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def normalize_lines(soup: BeautifulSoup) -> list[str]:
    text = soup.get_text("\n")
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_month_statuses(html: str) -> dict[int, str]:
    soup = BeautifulSoup(html, "html.parser")
    lines = normalize_lines(soup)
    statuses: dict[int, str] = {}
    day_pattern = re.compile(r"^(\d{1,2})\s*일$")

    for index, line in enumerate(lines):
        day_match = day_pattern.match(line)
        if not day_match:
            continue

        day = int(day_match.group(1))
        for next_line in lines[index + 1 :]:
            if day_pattern.match(next_line):
                break
            statuses[day] = next_line
            break

    if statuses:
        return statuses

    compact_text = " ".join(lines)
    compact_pattern = re.compile(
        r"(\d{1,2})\s*일\s*(마감|잔여\s*\d*|예약가능|가능|불가능|예약불가|불가)"
    )
    return {
        int(match.group(1)): match.group(2).strip()
        for match in compact_pattern.finditer(compact_text)
    }


def is_available(status: str) -> bool:
    normalized = re.sub(r"\s+", "", status)

    if any(word in normalized for word in UNAVAILABLE_WORDS):
        return False

    remain_match = re.search(r"잔여\s*(\d+)", status)
    if remain_match:
        return int(remain_match.group(1)) > 0

    if any(word in normalized for word in AVAILABLE_WORDS):
        return True

    return "가능" in normalized


def normalize_bot_token(value: str) -> str:
    token = value.strip()
    url_match = re.search(r"api\.telegram\.org/bot([^/\s]+)/?", token)
    if url_match:
        return url_match.group(1)
    if token.lower().startswith("bot") and ":" in token:
        return token[3:].strip()
    return token


def normalize_chat_id(value: str) -> str:
    chat_id = value.strip()
    chat_match = re.search(r'"chat"\s*:\s*\{[^{}]*"id"\s*:\s*(-?\d+)', chat_id)
    if chat_match:
        return chat_match.group(1)
    if re.fullmatch(r"-?\d+", chat_id):
        return chat_id
    id_match = re.search(r'"id"\s*:\s*(-?\d+)', chat_id)
    if id_match:
        return id_match.group(1)
    return chat_id


def send_telegram(message: str) -> None:
    token = normalize_bot_token(os.environ.get("TELEGRAM_BOT_TOKEN") or "")
    chat_id = normalize_chat_id(os.environ.get("TELEGRAM_CHAT_ID") or "")

    if not token or not chat_id:
        raise RuntimeError(
            "텔레그램 알림 발송에 필요한 TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 없습니다."
        )

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": "true",
        },
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"텔레그램 알림 발송 실패: HTTP {response.status_code} {response.text}"
        )


def format_day_list(days: list[int], month: int) -> str:
    if not days:
        return "없음"
    return ", ".join(f"{month}월 {day}일" for day in days)


def build_message(
    config: dict,
    checked_at: str,
    url: str,
    watched_statuses: dict[int, str],
    available_days: list[int],
) -> str:
    year = config["year"]
    month = config["month"]
    reservation_type = config["reservation_type"]
    all_month_days = list(range(1, calendar.monthrange(year, month)[1] + 1))
    watch_label = (
        f"{month}월 전체"
        if config["watch_days"] == all_month_days
        else format_day_list(config["watch_days"], month)
    )

    if available_days:
        title = "더우미제 예약 가능 날짜 알림"
        available_lines = "\n".join(
            f"- {month}월 {day}일: {watched_statuses[day]}"
            for day in available_days
        )
    else:
        title = "더우미제 예약 확인 완료"
        available_lines = "- 가능한 날짜 없음"

    message_parts = [
        title,
        f"- 대상: {year}년 {month}월 {reservation_type}",
        f"- 감시 날짜: {watch_label}",
        f"- 확인 시간: {checked_at}",
        "",
        "가능한 날짜:",
        available_lines,
    ]

    if config.get("include_status_list", True):
        status_lines = "\n".join(
            f"- {month}월 {day}일: {watched_statuses[day]}"
            for day in config["watch_days"]
            if day in watched_statuses
        )
        message_parts.extend(["", "감시 날짜 전체 상태:", status_lines])

    message_parts.extend(["", f"링크: {url}", "", "자동 예약은 하지 않았습니다."])
    return "\n".join(part for part in message_parts if part is not None)


def run_once(config: dict) -> None:
    timezone = ZoneInfo(config["timezone"])
    checked_at = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S %Z")
    url = build_reservation_url(config)

    print(f"[{checked_at}] 더우미제 예약 상태 확인 시작")
    print(f"대상 URL: {url}")
    print(f"감시 날짜: {format_day_list(config['watch_days'], config['month'])}")

    html = fetch_page(url)
    month_statuses = extract_month_statuses(html)
    if not month_statuses:
        raise ValueError("예약 상태를 페이지에서 찾지 못했습니다.")

    watched_statuses: dict[int, str] = {}
    for day in config["watch_days"]:
        status = month_statuses.get(day)
        if status is None:
            print(f"{config['month']}월 {day}일 상태: 찾지 못함")
            continue
        watched_statuses[day] = status
        print(f"{config['month']}월 {day}일 상태: {status}")

    available_days = [
        day for day, status in watched_statuses.items() if is_available(status)
    ]
    print(f"예약 가능 날짜: {format_day_list(available_days, config['month'])}")

    should_notify = (
        bool(available_days) and config.get("notify_when_available", True)
    ) or (
        not available_days and config.get("notify_when_no_available", True)
    )
    if not should_notify:
        print("설정에 따라 텔레그램 알림은 보내지 않습니다.")
        return

    message = build_message(config, checked_at, url, watched_statuses, available_days)
    send_telegram(message)
    print("텔레그램 알림을 발송했습니다.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    checks_per_run = config["checks_per_run"] if args.loop else 1

    for check_index in range(1, checks_per_run + 1):
        if checks_per_run > 1:
            print(f"Check {check_index}/{checks_per_run}")
        run_once(config)

        if check_index < checks_per_run:
            time.sleep(config["check_interval_seconds"])

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        raise
