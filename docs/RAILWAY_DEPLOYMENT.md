# Railway 배포 가이드

이 가이드는 Meeting Room Reservation Bot을 Railway에 배포하는 방법을 설명합니다.

## 📋 사전 준비사항

1. **Railway 계정** - [railway.app](https://railway.app)에서 가입
2. **Slack App** - Slack App이 생성되어 있어야 함 ([SLACK_SETUP.md](SLACK_SETUP.md) 참조)
3. **Git Repository** - 코드가 GitHub에 푸시되어 있어야 함

---

## 🚀 Railway 배포 단계

### 1단계: Railway 프로젝트 생성

1. [Railway Dashboard](https://railway.app/dashboard)에 접속
2. **"New Project"** 클릭
3. **"Deploy from GitHub repo"** 선택
4. 저장소에서 `sidekick` 선택
5. 프로젝트 이름 설정 (예: `meetingroom-bot`)

### 2단계: 환경 변수 설정

Railway Dashboard에서 **Variables** 탭으로 이동하여 다음 환경 변수를 추가:

#### 필수 환경 변수

```bash
# Slack Bot Token (Slack App 설정에서 복사)
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token

# Slack Signing Secret (Slack App 설정에서 복사)
SLACK_SIGNING_SECRET=your-actual-signing-secret

# 데이터베이스 경로
DATABASE_PATH=/app/data/meetingroom.db
```

#### Slack 토큰 찾는 방법

**SLACK_BOT_TOKEN**:
1. [Slack API](https://api.slack.com/apps) 접속
2. 해당 App 선택
3. **OAuth & Permissions** > **Bot User OAuth Token** 복사

**SLACK_SIGNING_SECRET**:
1. 동일한 App에서
2. **Basic Information** > **App Credentials** > **Signing Secret** 복사

### 3단계: Railway에서 앱 URL 확인

1. Railway가 자동으로 배포를 시작합니다
2. 배포 완료 후 **Settings** 탭에서 **Public URL** 생성
   - "Generate Domain" 클릭
   - 예시: `https://meetingroom-bot-production.up.railway.app`
3. 이 URL을 복사해둡니다 (다음 단계에서 사용)

---

## 🔧 Slack App 설정 변경

Railway 배포 후에는 **Socket Mode → HTTP Mode**로 변경해야 합니다.

### 1. Socket Mode 비활성화

1. [Slack API](https://api.slack.com/apps) 접속
2. 해당 App 선택
3. **Socket Mode** 메뉴로 이동
4. **Enable Socket Mode** 토글을 **OFF**로 변경

### 2. Event Subscriptions 설정

1. **Event Subscriptions** 메뉴로 이동
2. **Enable Events** 토글을 **ON**으로 변경
3. **Request URL** 입력:
   ```
   https://your-railway-app.up.railway.app/slack/events
   ```
   - `your-railway-app.up.railway.app`를 실제 Railway URL로 변경
   - Railway가 자동으로 URL 검증 (✅ Verified 표시되어야 함)

4. **Subscribe to bot events** 섹션에서 다음 이벤트 추가:
   - `app_mention` - 봇이 멘션될 때
   - `message.channels` - 채널 메시지
   - `message.im` - DM 메시지
   - `app_home_opened` - App Home 열릴 때

5. **Save Changes** 클릭

### 3. Slash Commands 설정 (선택사항)

Slash command를 사용하려면:

1. **Slash Commands** 메뉴로 이동
2. **Create New Command** 클릭
3. 설정:
   - **Command**: `/meetingroom`
   - **Request URL**: `https://your-railway-app.up.railway.app/slack/commands`
   - **Short Description**: 회의실 예약 관리
4. **Save** 클릭

### 4. Reinstall App

설정 변경 후 앱을 재설치해야 합니다:

1. **Install App** 메뉴로 이동
2. **Reinstall to Workspace** 클릭
3. 권한 승인

---

## ✅ 배포 확인

### 1. Health Check 확인

브라우저에서 다음 URL 접속:
```
https://your-railway-app.up.railway.app/health
```

정상적으로 응답이 오면 성공:
```json
{
  "status": "ok",
  "service": "meetingroom-bot",
  "database": "/app/data/meetingroom.db"
}
```

### 2. Slack에서 테스트

Slack 워크스페이스에서 봇을 테스트:

```
@봇이름 오후 4시~6시 Delhi 예약
```

예약이 정상적으로 처리되면 배포 완료! 🎉

---

## 📊 로그 확인

Railway에서 로그를 실시간으로 확인할 수 있습니다:

1. Railway Dashboard에서 프로젝트 선택
2. **Deployments** 탭 클릭
3. 최신 배포 선택
4. 로그 확인

**정상 로그 예시**:
```
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:8080
📦 Using SQLite database: /app/data/meetingroom.db
🌐 Starting API server on port 8080...
🤖 Starting Slack bot...
INFO:     Application startup complete.
```

---

## 🐛 트러블슈팅

### 1. "url_verification failed" 오류

**원인**: Slack이 Request URL을 검증할 수 없음

**해결**:
- Railway 배포가 완료되었는지 확인
- Health check URL이 정상 응답하는지 확인
- `/slack/events` 엔드포인트가 정상 작동하는지 로그 확인

### 2. 봇이 응답하지 않음

**원인**: 환경 변수 미설정 또는 Event Subscriptions 미설정

**해결**:
1. Railway Variables에서 `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` 확인
2. Slack App의 Event Subscriptions에서 이벤트가 추가되었는지 확인
3. Railway 로그에서 에러 메시지 확인

### 3. 데이터베이스 초기화 실패

**원인**: `/app/data` 디렉토리가 없음

**해결**:
Railway에서 자동으로 디렉토리를 생성하도록 코드 수정 (이미 적용됨)

---

## 🔄 업데이트 배포

코드를 수정한 후:

1. GitHub에 push:
   ```bash
   git add .
   git commit -m "Update bot features"
   git push
   ```

2. Railway가 자동으로 재배포 시작
3. Deployments 탭에서 진행 상황 확인

---

## 💰 비용

Railway는 다음과 같은 무료 플랜을 제공합니다:
- **$5 무료 크레딧** (매월)
- **500시간 실행 시간**

소규모 봇의 경우 무료 플랜으로 충분합니다.

---

## 📚 참고 자료

- [Railway 공식 문서](https://docs.railway.app/)
- [Slack Bolt 공식 문서](https://slack.dev/bolt-python/)
- [Slack API 문서](https://api.slack.com/)

---

**작성일**: 2025-12-05
**업데이트**: HTTP Mode 배포 방식으로 전환
