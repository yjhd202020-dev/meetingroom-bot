# Meeting Room Reservation Slack Bot

## 프로젝트 개요

Balance Hero 워크스페이스에서 사용하는 회의실 예약 Slack 봇입니다.

- **Slack App**: meetingroom wizard
- **배포 플랫폼**: Railway
- **상태**: ✅ 운영 중

---

## 🏢 회의실 목록
- Delhi (델리)
- Mumbai (뭄바이)
- Chennai (첸나이)

---

## 📂 프로젝트 구조

```
meetingroom-bot/
├── src/
│   ├── app.py                 # 메인 봇 애플리케이션
│   ├── handlers/
│   │   └── message_handler.py # Slack 이벤트 핸들러
│   ├── services/
│   │   └── reservation_service.py # 예약 비즈니스 로직
│   ├── models/
│   │   └── database.py        # SQLite 데이터베이스
│   └── utils/
│       └── nlp_parser.py      # 자연어 파싱
├── scripts/
│   └── init_db.py             # DB 초기화 스크립트
├── data/                      # SQLite DB 파일
├── docs/
│   └── SLACK_SETUP.md         # Slack App 설정 가이드
├── Procfile                   # Railway 실행 명령어
├── requirements.txt           # Python 의존성
├── runtime.txt                # Python 버전
├── pyproject.toml             # 프로젝트 설정
└── .env.example               # 환경변수 템플릿
```

---

## 🚀 Quick Commands

```bash
# 로컬 개발
cd meetingroom-bot
uv sync
cd src && uv run python app.py

# DB 초기화
uv run python scripts/init_db.py
```

---

## 🔧 환경변수

| 변수명 | 설명 |
|--------|------|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | App-Level Token (`xapp-...`) |
| `SLACK_SIGNING_SECRET` | Signing Secret |
| `DATABASE_PATH` | SQLite DB 경로 (default: `./data/meetingroom.db`) |

---

## 📦 배포 정보

| 항목 | 값 |
|------|-----|
| **플랫폼** | Railway |
| **GitHub** | https://github.com/yjhd202020-dev/meetingroom-bot |
| **Slack App** | meetingroom wizard |
| **App ID** | A09JQA6DBC1 |
| **워크스페이스** | Balance Hero |

---

## 📋 사용 예시

### 예약하기
```
@meetingroom wizard 오후 4:00~6:00 Delhi 예약해줘
@meetingroom wizard 내일 오전 10시~12시 Mumbai
```

### 예약 현황 보기
```
@meetingroom wizard 전체 예약 현황
@meetingroom wizard 이번주 예약
```

---

## 🔗 관련 문서
- [README.md](README.md) - 프로젝트 개요
- [TODO.md](TODO.md) - 개발 로드맵
- [docs/SLACK_SETUP.md](docs/SLACK_SETUP.md) - Slack App 설정 가이드

---

**배포일**: 2025-12-05
**개발자**: Mike Kwon
