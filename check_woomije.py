import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


TARGET_YEAR = 2026
TARGET_MONTH = 8
TARGET_DAY = 1
RESERVATION_TYPE = "party"
TIMEZONE = "Asia/Seoul"

RESERVATION_URL = (
    "https://thewoomije.co.kr/reservation-step1.php"
    f"?year={TARGET_YEAR}&month={TARGET_MONTH}&type={RESERVATION_TYPE}"
)

AVAILABLE_WORDS = ("예약가능", "잔여")
UNAVAILABLE_WORDS = ("마감", "불가능", "예약불가", "불가")


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


def extract_target_status(html: str, day: int) -> str:
    soup = BeautifulSoup(html, "html.parser")
    lines = normalize_lines(soup)
    day_pattern = re.compile(rf"^{day}\s*일$")

    for index, line in enumerate(lines):
        if not day_pattern.match(line):
            continue

        for next_line in lines[index + 1 :]:
            if re.match(r"^\d+\s*일$", next_line):
                break
            return next_line

    # Fallback for compact markup such as "1일 마감" in one text node.
    compact_text = " ".join(lines)
    match = re.search(
        rf"{day}\s*일\s*(마감|잔여\s*\d*|예약가능|가능|불가능|예약불가|불가)",
        compact_text,
    )
    if match:
        return match.group(1).strip()

    raise ValueError(f"{TARGET_MONTH}월 {day}일 상태를 페이지에서 찾지 못했습니다.")


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


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError(
            "예약 가능 상태지만 TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 없습니다."
        )

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        api_url,
        data={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": "true",
        },
        timeout=20,
    )
    response.raise_for_status()


def main() -> int:
    checked_at = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{checked_at}] 더우미제 예약 상태 확인 시작")
    print(f"대상 URL: {RESERVATION_URL}")

    html = fetch_page(RESERVATION_URL)
    status = extract_target_status(html, TARGET_DAY)
    available = is_available(status)

    print(f"{TARGET_YEAR}년 {TARGET_MONTH}월 {TARGET_DAY}일 상태: {status}")
    print(f"예약 가능 판단: {'가능' if available else '불가'}")

    if available:
        message_title = "더우미제 돌잔치 예약 가능 알림"
        message_tail = "자동 예약은 하지 않았습니다. 직접 사이트에서 확인해 주세요."
    else:
        message_title = "더우미제 예약 확인 완료"
        message_tail = "아직 예약 가능 상태가 아닙니다. 계속 10분마다 확인합니다."

    message = (
        f"{message_title}\n"
        f"- 날짜: {TARGET_YEAR}년 {TARGET_MONTH}월 {TARGET_DAY}일\n"
        f"- 현재 상태: {status}\n"
        f"- 예약 가능 판단: {'가능' if available else '불가'}\n"
        f"- 확인 시간: {checked_at}\n"
        f"- 링크: {RESERVATION_URL}\n\n"
        f"{message_tail}"
    )
    send_telegram(message)
    print("텔레그램 알림을 발송했습니다.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        raise
