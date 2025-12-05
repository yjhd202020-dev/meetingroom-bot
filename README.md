# Meeting Room Reservation Slack Bot

Slack에서 자연어로 회의실을 예약하고 관리하는 봇입니다.

## 🏢 회의실 목록
- **Delhi** (델리)
- **Mumbai** (뭄바이)
- **Chennai** (첸나이)

## ✨ 주요 기능
1. 자연어로 회의실 예약 (예: "오후 4:00~6:00 Delhi 예약해줘")
2. 중복 예약 방지 및 알림
3. 일주일치 전체 예약 현황 조회

## 🚀 로컬 개발 시작하기

### 1. 환경 설정
```bash
# 프로젝트 디렉토리로 이동
cd mike.kwon/meetingroom

# 의존성 설치
uv sync

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어서 Slack 토큰 값 입력
```

### 2. Slack App 설정
자세한 가이드는 `docs/SLACK_SETUP.md` 참조

### 3. 데이터베이스 초기화
```bash
uv run python scripts/init_db.py
```

### 4. 봇 실행 (Socket Mode)
```bash
uv run python src/app.py
```

## 📋 사용 예시

### 예약하기
```
오후 4:00~6:00 Delhi 예약해줘
내일 오전 10시부터 12시까지 Mumbai 예약
12월 10일 오후 2시~4시 Chennai
```

### 예약 현황 보기
```
전체 예약 현황
이번주 예약
```

## 🏗️ 프로젝트 구조
```
meetingroom/
├── src/
│   ├── app.py              # 메인 봇 애플리케이션
│   ├── handlers/           # Slack 이벤트 핸들러
│   ├── services/           # 비즈니스 로직
│   ├── models/             # 데이터 모델
│   └── utils/              # 유틸리티 함수
├── scripts/                # 초기화 스크립트
├── config/                 # 설정 파일
├── data/                   # SQLite DB 저장 위치
└── docs/                   # 문서
```

## 🔒 보안
- `.env` 파일은 절대 커밋하지 마세요
- Slack 토큰은 안전하게 보관하세요
- 프로덕션 배포 시 GitHub Secrets 사용

## 📚 기술 스택
- **언어**: Python 3.10+
- **프레임워크**: slack-bolt (Socket Mode)
- **데이터베이스**: SQLite
- **배포**: (향후 추가)
# Trigger redeploy
