# Slack App 설정 가이드

Meeting Room Bot을 위한 Slack App을 생성하고 설정하는 단계별 가이드입니다.

## 📋 1단계: Slack App 생성

1. **Slack API 페이지 접속**
   - https://api.slack.com/apps 이동
   - "Create New App" 클릭

2. **앱 생성 방법 선택**
   - "From scratch" 선택
   - App Name: `Meeting Room Bot` (원하는 이름)
   - Workspace: 설치할 워크스페이스 선택
   - "Create App" 클릭

## 🔑 2단계: Socket Mode 활성화

Socket Mode를 사용하면 외부 URL 없이 로컬에서 봇을 실행할 수 있습니다.

1. **좌측 메뉴에서 "Socket Mode" 클릭**
2. **"Enable Socket Mode" 토글 ON**
3. **App-Level Token 생성**
   - Token Name: `socket-token` (원하는 이름)
   - Scope: `connections:write` 자동 선택됨
   - "Generate" 클릭
   - 🔒 **중요**: 생성된 토큰(`xapp-...`) 복사해서 안전하게 보관
   - 이 토큰은 `.env` 파일의 `SLACK_APP_TOKEN`에 사용됩니다

## ⚙️ 3단계: OAuth & Permissions 설정

1. **좌측 메뉴에서 "OAuth & Permissions" 클릭**

2. **Bot Token Scopes 추가** (아래로 스크롤)

   다음 스코프들을 추가하세요:
   ```
   app_mentions:read      # 봇 멘션 감지
   channels:history       # 채널 메시지 읽기
   channels:read          # 채널 정보 읽기
   chat:write             # 메시지 전송
   groups:history         # 비공개 채널 메시지 읽기 (선택)
   im:history             # DM 메시지 읽기 (선택)
   ```

3. **Install to Workspace**
   - 페이지 상단의 "Install to Workspace" 버튼 클릭
   - 권한 확인 후 "Allow" 클릭

4. **Bot User OAuth Token 복사**
   - 🔒 **중요**: 생성된 토큰(`xoxb-...`) 복사
   - 이 토큰은 `.env` 파일의 `SLACK_BOT_TOKEN`에 사용됩니다

## 📡 4단계: Event Subscriptions 설정

1. **좌측 메뉴에서 "Event Subscriptions" 클릭**
2. **"Enable Events" 토글 ON**

3. **Subscribe to bot events** (아래로 스크롤)

   다음 이벤트들을 추가하세요:
   ```
   app_mention           # @봇 멘션 이벤트
   message.channels      # 채널 메시지 이벤트
   message.groups        # 비공개 채널 (선택)
   message.im            # DM 메시지 (선택)
   ```

4. **"Save Changes" 클릭**

## 🏠 5단계: App Home 설정 (선택)

1. **좌측 메뉴에서 "App Home" 클릭**
2. **"Home Tab" 섹션**
   - "Home Tab" 토글 ON
   - 사용자가 봇을 클릭하면 사용 방법을 볼 수 있습니다

## 🔐 6단계: Signing Secret 확인

1. **좌측 메뉴에서 "Basic Information" 클릭**
2. **"App Credentials" 섹션 찾기**
3. **Signing Secret 확인**
   - "Show" 버튼 클릭하여 시크릿 확인
   - 🔒 **중요**: 이 값을 `.env` 파일의 `SLACK_SIGNING_SECRET`에 사용

## 📝 7단계: 환경변수 설정

프로젝트 루트의 `.env` 파일을 생성하고 다음 내용을 입력하세요:

```bash
# Slack Bot Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here           # OAuth & Permissions에서 복사
SLACK_APP_TOKEN=xapp-your-app-token-here           # Socket Mode에서 복사
SLACK_SIGNING_SECRET=your-signing-secret-here      # Basic Information에서 복사

# Optional: Restrict to specific channel
# SLACK_CHANNEL_ID=C1234567890

# Database
DATABASE_PATH=./data/meetingroom.db

# Bot Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## ✅ 8단계: 봇을 채널에 초대

1. **Slack 워크스페이스에서 봇을 사용할 채널로 이동**
2. **채널에 봇 초대**
   - `/invite @Meeting Room Bot` 입력
   - 또는 채널 설정 → Integrations → Add apps 에서 봇 추가

## 🧪 9단계: 로컬 테스트

이제 모든 설정이 완료되었습니다! 봇을 실행해보세요:

```bash
# 프로젝트 디렉토리에서
cd mike.kwon/meetingroom

# 의존성 설치 (첫 실행 시)
uv sync

# 데이터베이스 초기화 (첫 실행 시)
uv run python scripts/init_db.py

# 봇 실행
uv run python src/app.py
```

출력에서 다음과 같은 메시지가 나타나야 합니다:
```
🤖 Starting Meeting Room Reservation Bot...
📍 Database: ./data/meetingroom.db
🔌 Socket Mode: Enabled
✅ Bot is running! Press Ctrl+C to stop.
```

## 🎯 테스트하기

Slack 채널에서 봇을 테스트해보세요:

1. **봇 멘션으로 예약**
   ```
   @Meeting Room Bot 오후 4:00~6:00 Delhi 예약해줘
   ```

2. **예약 현황 확인**
   ```
   @Meeting Room Bot 전체 예약 현황
   ```

## 🔒 보안 주의사항

⚠️ **절대로 다음 정보를 공개하거나 Git에 커밋하지 마세요:**
- Bot Token (`xoxb-...`)
- App Token (`xapp-...`)
- Signing Secret

`.gitignore`에 `.env` 파일이 포함되어 있는지 확인하세요!

## 🚨 문제 해결

### 봇이 응답하지 않을 때
1. `.env` 파일의 토큰 값이 올바른지 확인
2. 봇이 채널에 초대되어 있는지 확인
3. Socket Mode가 활성화되어 있는지 확인
4. Event Subscriptions가 올바르게 설정되어 있는지 확인

### "missing_scope" 에러
- OAuth & Permissions에서 필요한 스코프가 모두 추가되었는지 확인
- 스코프 추가 후 "Reinstall to Workspace" 필요

### Database 에러
```bash
# 데이터베이스 초기화
uv run python scripts/init_db.py
```

## 📚 추가 리소스

- [Slack Bolt Python 문서](https://slack.dev/bolt-python/)
- [Socket Mode 가이드](https://api.slack.com/apis/connections/socket)
- [Slack API 문서](https://api.slack.com/)
