# Meeting Room Reservation Slack Bot - TODO

## 프로젝트 개요
회사 슬랙에서 자연어로 회의실을 예약하고 관리하는 슬랙봇 개발

**회의실 목록**: Delhi, Mumbai, Chennai

**핵심 기능**:
1. 자연어로 회의실 예약 (예: "오후 4:00~6:00 Delhi 예약해줘")
2. 중복 예약 방지 및 알림
3. 일주일치 전체 예약 현황 조회

---

## Phase 1: 기본 설계 및 아키텍처 정의

### 1.1 프로젝트 구조 설계
- [ ] 프로젝트 디렉토리 구조 정의
- [ ] 기술 스택 선택 (Python/Node.js, DB 등)
- [ ] 데이터 모델 설계
  - [ ] 회의실 정보 (id, name, location 등)
  - [ ] 예약 정보 (room_id, user_id, start_time, end_time, created_at 등)
  - [ ] 사용자 정보 (slack_user_id, slack_username 등)

### 1.2 Slack App 설정
- [ ] Slack App 생성 (workspace에 등록)
- [ ] Bot Token Permissions 설정
  - [ ] `channels:read` - 채널 정보 읽기
  - [ ] `chat:write` - 메시지 작성
  - [ ] `commands` - Slash commands 사용
  - [ ] `app_mentions:read` - 멘션 감지
- [ ] Event Subscriptions 설정
  - [ ] `app_mention` - 봇 멘션 이벤트
  - [ ] `message.channels` - 채널 메시지 이벤트
- [ ] Slash Commands 설정 (선택적)
  - [ ] `/reserve` - 예약 명령
  - [ ] `/reservations` - 예약 현황 조회

### 1.3 개발 환경 설정
- [ ] Git 저장소 초기화
- [ ] `.gitignore` 생성 (환경변수, DB 파일 등 제외)
- [ ] 의존성 관리 파일 생성 (`requirements.txt` 또는 `package.json`)
- [ ] 환경변수 설정 파일 템플릿 생성 (`.env.example`)
  - [ ] `SLACK_BOT_TOKEN`
  - [ ] `SLACK_SIGNING_SECRET`
  - [ ] `DATABASE_URL` (또는 로컬 SQLite 경로)

---

## Phase 2: 자연어 처리 (NLP) 모듈 개발

### 2.1 자연어 파싱 로직
- [ ] 날짜/시간 추출 함수 구현
  - [ ] "오후 4:00~6:00" → `14:00-16:00` 변환
  - [ ] "내일 오전 10시" → 날짜+시간 계산
  - [ ] "12월 5일 오후 2시~4시" → 날짜+시간 파싱
- [ ] 회의실 이름 추출 함수 구현
  - [ ] "Delhi", "Mumbai", "Chennai" 인식
  - [ ] 대소문자 무시, 오타 보정 (선택적)
- [ ] 예약 의도 분류
  - [ ] 예약 요청 vs 조회 요청 구분
  - [ ] "예약", "reserve", "book" 등의 키워드 인식

### 2.2 LLM 통합 (선택적 - 더 정확한 자연어 이해)
- [ ] OpenAI API 또는 Claude API 연동 고려
- [ ] Prompt 설계 (예약 정보 추출용)
- [ ] Fallback 로직 (API 실패 시 정규식 기반 파싱으로 전환)

---

## Phase 3: 예약 관리 시스템 개발

### 3.1 데이터베이스 구축
- [ ] SQLite (로컬 개발) 또는 PostgreSQL (프로덕션) 선택
- [ ] 테이블 스키마 생성
  ```sql
  CREATE TABLE rooms (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
  );

  CREATE TABLE reservations (
    id INTEGER PRIMARY KEY,
    room_id INTEGER NOT NULL,
    slack_user_id TEXT NOT NULL,
    slack_username TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id)
  );
  ```
- [ ] 초기 회의실 데이터 삽입 (Delhi, Mumbai, Chennai)

### 3.2 예약 비즈니스 로직
- [ ] 예약 생성 함수
  - [ ] 입력 검증 (시작 시간 < 종료 시간, 과거 날짜 방지 등)
  - [ ] 중복 예약 체크 로직
    ```python
    # 기존 예약과 시간이 겹치는지 확인
    # (new_start < existing_end) AND (new_end > existing_start)
    ```
  - [ ] 예약 저장
- [ ] 예약 조회 함수
  - [ ] 특정 회의실의 특정 날짜 예약 조회
  - [ ] 전체 회의실 일주일치 예약 조회
- [ ] 예약 취소 함수 (선택적)
  - [ ] 본인 예약만 취소 가능하도록 권한 체크

### 3.3 중복 예약 방지
- [ ] 트랜잭션 처리 (동시 예약 요청 대응)
- [ ] Lock 메커니즘 고려 (DB row locking)
- [ ] 충돌 시 사용자에게 명확한 에러 메시지 반환

---

## Phase 4: Slack Bot 통합

### 4.1 Slack 이벤트 핸들러
- [ ] 봇 멘션 이벤트 핸들러 구현
  - [ ] 메시지 수신 → NLP 파싱 → 예약 처리
- [ ] 채널 메시지 필터링
  - [ ] 특정 채널에서만 동작하도록 제한 (환경변수로 채널 ID 관리)
- [ ] Slash Command 핸들러 (선택적)

### 4.2 응답 메시지 포맷
- [ ] 예약 성공 메시지
  ```
  ✅ 예약 완료!
  📍 회의실: Delhi
  🕐 시간: 2025-12-05 16:00 ~ 18:00
  👤 예약자: @mike.kwon
  ```
- [ ] 예약 실패 메시지 (중복 예약)
  ```
  ❌ 예약 불가
  📍 회의실: Delhi
  🕐 요청 시간: 2025-12-05 16:00 ~ 18:00
  ⚠️ 이유: 해당 시간에 이미 예약이 있습니다.

  기존 예약 정보:
  👤 예약자: @jack.yoon
  🕐 시간: 2025-12-05 15:00 ~ 17:00
  ```
- [ ] 전체 예약 현황 메시지
  ```
  📅 이번 주 회의실 예약 현황 (2025-12-05 ~ 2025-12-11)

  🏢 Delhi
  - 12/05 (목) 16:00-18:00 | @mike.kwon
  - 12/06 (금) 10:00-12:00 | @jack.yoon

  🏢 Mumbai
  - 12/05 (목) 14:00-16:00 | @dennis.choi

  🏢 Chennai
  - (예약 없음)
  ```

### 4.3 인터랙티브 요소 (선택적)
- [ ] Slack Block Kit 사용하여 버튼 추가
  - [ ] "예약 확인" / "취소" 버튼
- [ ] Modal 사용하여 예약 폼 제공

---

## Phase 5: 배포 및 운영

### 5.1 로컬 테스트
- [ ] Ngrok 등을 사용하여 로컬 서버 외부 노출
- [ ] Slack Event Subscriptions URL 설정
- [ ] 테스트 케이스 작성 및 실행
  - [ ] 정상 예약 시나리오
  - [ ] 중복 예약 시나리오
  - [ ] 자연어 파싱 정확도 테스트

### 5.2 프로덕션 배포
- [ ] 배포 환경 선택 (AWS Lambda, Heroku, Railway, GCP Cloud Run 등)
- [ ] 환경변수 설정 (Slack Token, DB URL 등)
- [ ] HTTPS 엔드포인트 설정
- [ ] Slack App Event URL 업데이트

### 5.3 모니터링 및 로깅
- [ ] 로그 시스템 구축 (예약 로그, 에러 로그)
- [ ] 알림 설정 (봇 다운 시 알림 등)
- [ ] 사용 통계 수집 (선택적)

---

## Phase 6: 고도화 (선택적)

### 6.1 추가 기능
- [ ] 반복 예약 (매주 월요일 10시 등)
- [ ] 예약 알림 (예약 시작 10분 전 리마인더)
- [ ] 회의실 사용 현황 분석 대시보드
- [ ] 예약 승인 시스템 (관리자 승인 필요)

### 6.2 AI 기능 강화
- [ ] 회의 목적 자동 분류 (팀 미팅, 1:1, 전체 회의 등)
- [ ] 최적 회의실 추천 (인원 수, 장비 필요 여부 등)
- [ ] 예약 패턴 분석 및 제안

### 6.3 UX 개선
- [ ] 다국어 지원 (한국어/영어)
- [ ] 타임존 처리 (글로벌 팀 대응)
- [ ] 캘린더 통합 (Google Calendar, Outlook 등)

---

## 추천 Sidekick

이 프로젝트에 가장 적합한 Sidekick은 **@slack-bot-config-master**입니다.

**선택 이유**:
- Slack Bot Configuration, GitHub Actions, Deployment 전문가
- 각 Sidekick을 독립적인 Slack Bot으로 운영하는 경험 보유
- Slack App 설정, 이벤트 핸들링, 배포 자동화에 특화

**호출 방법**:
```
@slack-bot-config-master 미팅룸 예약 봇 개발 도와줘
```

**대안 Sidekick**:
- `@developer` (dylan.min) - Agile 개발 전문가, 태스크 분해 및 검증 특화
- `@alchemist` (neal.lee) - 인프라-애플리케이션 변환 전문가, 인프라 자동화 지원

---

## 참고 사항

### 기술 스택 추천
- **Backend**: Python (Flask/FastAPI) 또는 Node.js (Express)
- **Database**: SQLite (개발), PostgreSQL (프로덕션)
- **Slack SDK**:
  - Python: `slack-bolt`
  - Node.js: `@slack/bolt`
- **NLP**: 정규식 + (선택적) OpenAI/Claude API
- **배포**: AWS Lambda + API Gateway 또는 Railway

### 보안 고려사항
- [ ] Slack Signing Secret 검증 (요청 위변조 방지)
- [ ] 환경변수 암호화 (프로덕션)
- [ ] 데이터베이스 접근 권한 제한
- [ ] 사용자 인증 (Slack User ID 기반)

### 성능 고려사항
- [ ] DB 인덱스 설정 (room_id, start_time, end_time)
- [ ] 캐싱 전략 (자주 조회되는 예약 현황)
- [ ] 비동기 처리 (Slack 응답 3초 제한 대응)

---

**작성일**: 2025-12-05
**작성자**: Genesis (via Claude Code)
