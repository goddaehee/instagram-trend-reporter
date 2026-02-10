<!-- Generated: 2026-02-05 | Updated: 2026-02-05 -->

# Instagram Trend Reporter

## Purpose

Instagram Trend Reporter는 인스타그램 릴스/포스트 트렌드를 분석하여 Google Sheets 리포트를 생성하고 이메일로 전송하는 자동화 도구입니다. 패션 관련 인스타그램 계정의 해시태그 트렌드와 바이럴 콘텐츠를 분석합니다.

## Key Files

| File | Description |
|------|-------------|
| `app.py` | Streamlit 웹 앱 진입점 - 비개발자용 GUI 인터페이스 |
| `main.py` | CLI 진입점 - 커맨드라인 실행 및 자동화용 |
| `requirements.txt` | Python 의존성 패키지 목록 |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `src/` | 핵심 비즈니스 로직 모듈 (see `src/AGENTS.md`) |
| `config/` | 설정 파일 (settings.example.yaml) |
| `docs/` | 사용자 문서 |
| `.github/workflows/` | GitHub Actions CI/CD (weekly-report.yml) |
| `.streamlit/` | Streamlit 설정 |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Entry Points                              │
│  app.py (Streamlit GUI)  │  main.py (CLI)                   │
└────────────────┬─────────────────┬──────────────────────────┘
                 │                 │
                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                 src/reporter.py                              │
│              Pipeline Orchestrator                           │
└────────────────┬─────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬────────────┬────────────┐
    ▼            ▼            ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────────┐
│fetcher │→ │analyzer│→ │ sheets │→ │ mailer │  │credentials │
│ (Apify)│  │(분석)  │  │(Sheets)│  │(Gmail) │  │  (인증)    │
└────────┘  └────────┘  └────────┘  └────────┘  └────────────┘
```

## Data Flow

1. **Fetch**: Apify API로 Instagram 데이터 수집
2. **Analyze**: 해시태그 통계, 바이럴 콘텐츠, 인사이트 생성
3. **Report**: Google Sheets에 리포트 생성
4. **Notify**: Gmail로 리포트 링크 전송

## For AI Agents

### Working In This Directory

- 두 진입점(`app.py`, `main.py`)은 동일한 `src/` 모듈을 사용
- 설정은 `config/settings.yaml` 또는 환경변수/Streamlit Secrets로 관리
- 인증 토큰은 로컬에서는 keyring, 클라우드에서는 환경변수 사용

### Testing Requirements

```bash
# CLI 테스트
python main.py test              # 설정 확인
python main.py run --no-email    # 이메일 제외 실행

# Streamlit 테스트
streamlit run app.py
```

### Common Patterns

- 모든 모듈은 `Config` 객체를 통해 설정 접근
- `get_config()` 함수로 기본 설정 로드
- 환경에 따른 인증 분기 (`credentials.py`)

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `APIFY_TOKEN` | Apify API 토큰 |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 시크릿 |
| `SHEETS_TOKEN` | Google Sheets OAuth 토큰 (JSON) |
| `GMAIL_TOKEN` | Gmail OAuth 토큰 (JSON) |

## Dependencies

### External

| Package | Purpose |
|---------|---------|
| `apify-client` | Instagram 데이터 스크래핑 |
| `google-api-python-client` | Google Sheets/Gmail API |
| `google-auth-oauthlib` | Google OAuth 인증 |
| `keyring` | 로컬 크레덴셜 저장 |
| `streamlit` | 웹 GUI 프레임워크 |
| `pyyaml` | YAML 설정 파싱 |

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
