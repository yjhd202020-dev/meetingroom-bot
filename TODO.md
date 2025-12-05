# Meeting Room Reservation Slack Bot - TODO

## 프로젝트 개요
회사 슬랙에서 자연어로 회의실을 예약하고 관리하는 슬랙봇

**회의실 목록**: Delhi, Mumbai, Chennai

**핵심 기능**:
1. 자연어로 회의실 예약 (예: "오후 4:00~6:00 Delhi 예약해줘")
2. 중복 예약 방지 및 알림
3. 일주일치 전체 예약 현황 조회

---

## ✅ 완료된 작업

### Phase 1: 기본 설계 및 아키텍처 정의
- [x] 프로젝트 디렉토리 구조 정의
- [x] 기술 스택 선택 (Python, SQLite, slack-bolt)
- [x] 데이터 모델 설계
  - [x] 회의실 정보 (id, name, description)
  - [x] 예약 정보 (room_id, user_id, start_time, end_time, created_at)

### Phase 2: Slack App 설정
- [x] Slack App 생성 (meetingroom wizard)
- [x] Bot Token Permissions 설정
- [x] Socket Mode 활성화
- [x] Event Subscriptions 설정 (app_mention)

### Phase 3: 개발 환경 설정
- [x] Git 저장소 초기화
- [x] `.gitignore` 생성
- [x] 의존성 관리 (pyproject.toml, requirements.txt)
- [x] 환경변수 설정 파일 템플릿 생성 (`.env.example`)

### Phase 4: 자연어 처리 모듈 개발
- [x] 날짜/시간 추출 함수 구현
- [x] 회의실 이름 추출 함수 구현
- [x] 예약 의도 분류 (예약 요청 vs 조회 요청)

### Phase 5: 예약 관리 시스템 개발
- [x] SQLite 데이터베이스 구축
- [x] 테이블 스키마 생성 (rooms, reservations)
- [x] 초기 회의실 데이터 삽입 (Delhi, Mumbai, Chennai)
- [x] 예약 생성 함수 (입력 검증, 중복 체크)
- [x] 예약 조회 함수 (주간 예약 현황)
- [x] 중복 예약 방지 로직

### Phase 6: Slack Bot 통합
- [x] 봇 멘션 이벤트 핸들러 구현
- [x] 예약 성공/실패 메시지 포맷
- [x] 전체 예약 현황 메시지 포맷

### Phase 7: 배포 및 운영
- [x] Railway 배포 완료
- [x] 환경변수 설정 (Railway Variables)
- [x] GitHub 저장소 연동

---

## 📋 향후 계획 (선택적)

### 추가 기능
- [ ] 예약 취소 기능
- [ ] 반복 예약 (매주 월요일 10시 등)
- [ ] 예약 알림 (예약 시작 10분 전 리마인더)
- [ ] Slash Commands 지원 (/reserve, /reservations)

### AI 기능 강화
- [ ] LLM 통합으로 더 정확한 자연어 이해
- [ ] 회의 목적 자동 분류
- [ ] 최적 회의실 추천

### UX 개선
- [ ] Slack Block Kit 버튼 추가
- [ ] Modal 예약 폼
- [ ] 다국어 지원 (한국어/영어)

### 인프라 개선
- [ ] PostgreSQL 마이그레이션 (프로덕션)
- [ ] 로그 시스템 구축
- [ ] 모니터링 및 알림 설정

---

## 📦 배포 정보

| 항목 | 값 |
|------|-----|
| **플랫폼** | Railway |
| **GitHub** | https://github.com/yjhd202020-dev/meetingroom-bot |
| **Slack App** | meetingroom wizard |
| **워크스페이스** | Balance Hero |
| **배포일** | 2025-12-05 |

---

**최종 업데이트**: 2025-12-05
**개발자**: Mike Kwon
