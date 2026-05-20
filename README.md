# 더우미제 예약 감시 봇

더우미제 돌잔치 예약 페이지에서 `2026년 8월 1일 party` 예약 상태를 확인하고, 자리가 났을 때만 텔레그램 알림을 보내는 봇입니다.

- 확인 주소: <https://thewoomije.co.kr/reservation-step1.php?year=2026&month=8&type=party>
- `마감`이면 예약 불가로 판단합니다.
- `잔여`, `예약가능`, `가능` 같은 표현이 있으면 예약 가능으로 판단합니다.
- 자동 예약은 하지 않습니다. 텔레그램 알림만 보냅니다.

## 파일 구성

- `check_woomije.py`: 예약 페이지를 확인하고 텔레그램 알림을 보내는 Python 코드
- `requirements.txt`: 실행에 필요한 Python 패키지 목록
- `.github/workflows/check-woomije.yml`: GitHub Actions 자동 실행 설정

## GitHub Secrets 설정

GitHub 저장소에서 아래 두 값을 Secrets로 등록해야 합니다.

1. GitHub 저장소 페이지로 이동합니다.
2. `Settings`를 누릅니다.
3. 왼쪽 메뉴에서 `Secrets and variables` → `Actions`를 누릅니다.
4. `New repository secret`을 눌러 아래 값을 각각 추가합니다.

| Secret 이름 | 설명 |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 알림을 받을 텔레그램 chat_id |

## 실행 방법 1: GitHub Actions에서 실행하기

이 방법이 실제 감시 봇 운영용입니다. 내 컴퓨터를 켜두지 않아도 GitHub가 10분마다 실행합니다.

### 1. GitHub 저장소에 파일 올리기

현재 폴더의 파일들을 GitHub 저장소에 올립니다.

반드시 아래 파일들이 저장소에 있어야 합니다.

```text
check_woomije.py
requirements.txt
README.md
.github/workflows/check-woomije.yml
```

### 2. Secrets 등록하기

GitHub 저장소에서 아래로 이동합니다.

```text
Settings → Secrets and variables → Actions → New repository secret
```

아래 두 개를 각각 추가합니다.

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

### 3. 수동으로 한 번 실행해보기

1. GitHub 저장소의 `Actions` 탭을 누릅니다.
2. 왼쪽에서 `Check Woomije Reservation`을 누릅니다.
3. 오른쪽의 `Run workflow` 버튼을 누릅니다.
4. 초록색 실행 항목이 생기면 그 항목을 클릭합니다.
5. `check` → `Check reservation status`를 눌러 로그를 확인합니다.

정상 실행되면 로그에 이런 내용이 보입니다.

```text
2026년 8월 1일 상태: 마감
예약 가능 판단: 불가
마감 또는 예약 불가 상태입니다. 텔레그램 알림은 보내지 않습니다.
```

자리가 난 경우에는 이런 식으로 보입니다.

```text
2026년 8월 1일 상태: 잔여 1
예약 가능 판단: 가능
예약 가능 상태입니다. 텔레그램 알림을 발송했습니다.
```

### 4. 자동 실행 확인하기

설정된 workflow는 10분마다 자동 실행됩니다.

```yaml
schedule:
  - cron: "*/10 * * * *"
```

확인은 GitHub 저장소의 `Actions` 탭에서 할 수 있습니다. 새 실행 기록이 10분 간격으로 쌓이면 정상입니다.

GitHub Actions 예약 실행은 정확히 초 단위로 실행되지 않을 수 있고, GitHub 상황에 따라 몇 분 늦게 시작될 수 있습니다.

## 텔레그램 봇 토큰 만들기

1. 텔레그램에서 `@BotFather`를 검색합니다.
2. `/newbot` 명령으로 새 봇을 만듭니다.
3. BotFather가 알려주는 토큰을 `TELEGRAM_BOT_TOKEN` Secret에 넣습니다.
4. 만든 봇에게 먼저 아무 메시지나 한 번 보냅니다.

## chat_id 확인하기

브라우저에서 아래 주소를 열어 `chat_id`를 확인합니다.

```text
https://api.telegram.org/bot여기에_봇_토큰/getUpdates
```

응답에서 `"chat":{"id":...}` 부분의 숫자를 찾아 `TELEGRAM_CHAT_ID` Secret에 넣으면 됩니다.

## 실행 방법 2: 내 컴퓨터에서 직접 실행하기

내 컴퓨터에서 한 번만 테스트할 때 쓰는 방법입니다.

### 1. Python 설치 확인

PowerShell을 열고 아래 명령을 실행합니다.

```powershell
python --version
```

버전이 나오면 Python이 설치된 것입니다.

```text
Python 3.12.0
```

`Python was not found` 같은 메시지가 나오면 Python이 설치되어 있지 않거나 PATH에 잡혀 있지 않은 상태입니다. 이 경우 <https://www.python.org/downloads/>에서 Python을 설치한 뒤 다시 PowerShell을 열어 확인합니다.

### 2. 현재 폴더로 이동

PowerShell에서 이 폴더로 이동합니다.

```powershell
cd "C:\Users\김경호\Documents\더우미제 예약 프로그램"
```

### 3. 패키지 설치

```powershell
python -m pip install -r requirements.txt
```

### 4. 실행

```powershell
python check_woomije.py
```

현재 상태가 `마감`이면 이런 식으로 로그만 나오고 텔레그램 알림은 보내지 않습니다.

```text
2026년 8월 1일 상태: 마감
예약 가능 판단: 불가
마감 또는 예약 불가 상태입니다. 텔레그램 알림은 보내지 않습니다.
```

## 텔레그램 알림 확인 방법

이 봇은 자리가 났을 때만 텔레그램을 보냅니다.

따라서 현재 상태가 `마감`이면 텔레그램 메시지가 오지 않는 것이 정상입니다.

자리가 나면 아래 같은 메시지가 옵니다.

```text
더우미제 돌잔치 예약 가능 알림
- 날짜: 2026년 8월 1일
- 현재 상태: 잔여 1
- 확인 시간: ...
- 링크: https://thewoomije.co.kr/reservation-step1.php?year=2026&month=8&type=party

자동 예약은 하지 않았습니다. 직접 사이트에서 확인해 주세요.
```

로컬에서 텔레그램 발송까지 테스트하려면 PowerShell에서 환경 변수를 먼저 설정합니다.

```powershell
$env:TELEGRAM_BOT_TOKEN="봇_토큰"
$env:TELEGRAM_CHAT_ID="chat_id"
python check_woomije.py
```

단, 실제 사이트 상태가 `마감`이면 이 경우에도 메시지는 오지 않습니다.

## 문제가 생겼을 때 확인할 것

### GitHub Actions에서 빨간색 실패가 뜨는 경우

실행 항목을 클릭한 뒤 `check` 단계의 로그를 봅니다.

- `TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 없습니다.`: GitHub Secrets 이름이 틀렸거나 등록되지 않았습니다.
- `HTTPError`: 더우미제 사이트 또는 텔레그램 API 응답에 문제가 있었을 수 있습니다.
- `상태를 페이지에서 찾지 못했습니다.`: 더우미제 페이지 구조가 바뀌었을 수 있습니다.

### 텔레그램이 오지 않는 경우

아래를 확인합니다.

1. 현재 상태가 `마감`이면 메시지가 오지 않는 것이 정상입니다.
2. 봇에게 먼저 아무 메시지나 보냈는지 확인합니다.
3. `TELEGRAM_CHAT_ID`가 정확한지 확인합니다.
4. GitHub Actions 로그에 `예약 가능 상태입니다. 텔레그램 알림을 발송했습니다.`가 찍혔는지 확인합니다.
