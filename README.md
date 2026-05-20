# 더우미제 예약 감시 봇

더우미제 예약 페이지에서 원하는 날짜들의 예약 상태를 확인하고 텔레그램으로 알려주는 봇입니다.

- 자동 예약은 하지 않습니다.
- 기본값은 `2026년 8월 party` 전체 날짜 감시입니다.
- `잔여`, `예약가능`, `가능` 같은 표현이 있으면 예약 가능으로 판단합니다.
- `마감`, `예약불가`, `불가` 같은 표현이 있으면 예약 불가로 판단합니다.
- 감시 날짜, 알림 간격, 알림 방식은 `config.json`에서 직접 바꿀 수 있습니다.

## 파일 구성

- `check_woomije.py`: 예약 상태 확인 및 텔레그램 발송 코드
- `config.json`: 사용자가 직접 바꾸는 설정 파일
- `requirements.txt`: Python 패키지 목록
- `.github/workflows/check-woomije.yml`: GitHub Actions 자동 실행 설정

## 설정 바꾸기

`config.json`을 열어서 값을 바꾸면 됩니다.

```json
{
  "year": 2026,
  "month": 8,
  "reservation_type": "party",
  "watch_days": [],
  "check_interval_seconds": 60,
  "checks_per_run": 5,
  "notify_when_available": true,
  "notify_when_no_available": true,
  "include_status_list": true,
  "timezone": "Asia/Seoul"
}
```

각 항목 뜻은 아래와 같습니다.

| 항목 | 뜻 |
| --- | --- |
| `year` | 감시할 연도 |
| `month` | 감시할 월 |
| `reservation_type` | 예약 타입. 현재는 `party` |
| `watch_days` | 감시할 날짜 목록. 빈 배열 `[]`이면 해당 월 전체 |
| `check_interval_seconds` | 한 실행 안에서 몇 초 간격으로 다시 확인할지 |
| `checks_per_run` | 한 번 실행될 때 몇 번 확인할지 |
| `notify_when_available` | 가능한 날짜가 있을 때 알림 보낼지 |
| `notify_when_no_available` | 가능한 날짜가 없어도 확인 완료 알림 보낼지 |
| `include_status_list` | 알림에 감시 날짜 전체 상태를 같이 넣을지 |
| `timezone` | 확인 시간 표시 기준 |

## 날짜 설정 예시

8월 전체를 감시하려면:

```json
"watch_days": []
```

8월 1일만 감시하려면:

```json
"watch_days": [1]
```

8월 1일, 3일, 15일만 감시하려면:

```json
"watch_days": [1, 3, 15]
```

## 알림 간격 설정 예시

1분마다 확인하려면:

```json
"check_interval_seconds": 60,
"checks_per_run": 5
```

GitHub Actions는 예약 실행을 5분마다 시작하고, 봇은 그 안에서 1분 간격으로 5번 확인합니다.

5분마다 한 번만 확인하려면:

```json
"check_interval_seconds": 60,
"checks_per_run": 1
```

GitHub Actions 자체가 5분마다 시작하므로 한 번 실행될 때 1번만 확인하면 됩니다.

마감일 때 알림이 너무 많이 오면:

```json
"notify_when_no_available": false
```

이렇게 바꾸면 가능한 날짜가 있을 때만 텔레그램 알림을 보냅니다.

## 텔레그램 알림 예시

가능한 날짜가 있으면:

```text
더우미제 예약 가능 날짜 알림
- 대상: 2026년 8월 party
- 감시 날짜: 8월 전체
- 확인 시간: ...

가능한 날짜:
- 8월 3일: 잔여 1
- 8월 15일: 예약가능

감시 날짜 전체 상태:
- 8월 1일: 마감
- 8월 2일: 마감
- 8월 3일: 잔여 1

링크: https://thewoomije.co.kr/reservation-step1.php?year=2026&month=8&type=party

자동 예약은 하지 않았습니다.
```

가능한 날짜가 없고 `notify_when_no_available`이 `true`이면:

```text
더우미제 예약 확인 완료
- 대상: 2026년 8월 party
- 감시 날짜: 8월 전체
- 확인 시간: ...

가능한 날짜:
- 가능한 날짜 없음
```

## GitHub Secrets 설정

GitHub 저장소에서 아래 두 값을 Secrets로 등록해야 합니다.

| Secret 이름 | 설명 |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 BotFather가 준 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 알림을 받을 텔레그램 chat_id |

Secrets 설정 위치:

```text
Settings → Secrets and variables → Actions → New repository secret
```

## chat_id 확인하기

1. 텔레그램에서 만든 봇에게 먼저 아무 메시지나 보냅니다.
2. 브라우저에서 아래 주소를 엽니다.

```text
https://api.telegram.org/bot여기에_봇_토큰/getUpdates
```

3. 응답에서 아래 부분을 찾습니다.

```text
"chat":{"id":123456789
```

여기서 `123456789` 같은 숫자가 `TELEGRAM_CHAT_ID`입니다.

## GitHub Actions에서 실행하기

수동 실행:

1. GitHub 저장소의 `Actions` 탭을 엽니다.
2. `Check Woomije Reservation`을 누릅니다.
3. `Run workflow`를 누릅니다.

자동 실행:

```yaml
schedule:
  - cron: "*/5 * * * *"
```

GitHub Actions 제한 때문에 workflow는 5분마다 시작합니다. 실제 확인 간격과 반복 횟수는 `config.json`의 `check_interval_seconds`, `checks_per_run` 값으로 조절합니다.

## 로컬 테스트

PowerShell에서:

```powershell
cd "C:\Users\김경호\Documents\더우미제 예약 프로그램"
python -m pip install -r requirements.txt
python check_woomije.py
```

반복 실행까지 테스트하려면:

```powershell
python check_woomije.py --loop
```
