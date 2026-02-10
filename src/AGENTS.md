<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-05 | Updated: 2026-02-05 -->

# src - Core Business Logic

## Purpose

Instagram Trend Reporter의 핵심 비즈니스 로직 모듈. 데이터 수집, 분석, 리포트 생성, 이메일 전송의 전체 파이프라인을 구성합니다.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 패키지 초기화, 버전 정보 (`__version__ = "1.0.0"`) |
| `config.py` | 설정 관리 - `Config`, `Account`, `AnalysisConfig` 데이터클래스 |
| `credentials.py` | 통합 인증 관리 - 로컬(keyring) / 클라우드(Streamlit Secrets) 분기 |
| `fetcher.py` | Instagram 데이터 수집 - Apify API 클라이언트 |
| `analyzer.py` | 데이터 분석 - 해시태그 통계, 바이럴 콘텐츠, 인사이트 생성 |
| `sheets.py` | Google Sheets 리포트 생성 - 스프레드시트 작성 |
| `mailer.py` | Gmail 이메일 전송 - HTML 이메일 발송 |
| `reporter.py` | 파이프라인 오케스트레이터 - 전체 흐름 조율 |

## Module Relationships

```
config.py ←──────────────────────────────────────────┐
    ↓                                                │
credentials.py ←─────────────────────────────────────┤
    ↓                                                │
fetcher.py ─→ analyzer.py ─→ sheets.py ─→ mailer.py │
    ↑              ↑             ↑           ↑      │
    └──────────────┴─────────────┴───────────┴──────┘
                         ↓
                   reporter.py (orchestrator)
```

## For AI Agents

### Working In This Directory

- 모든 모듈은 `Config` 객체를 인자로 받아 설정 접근
- `get_config()`: 설정 파일 또는 기본값으로 Config 생성
- 분석 결과는 `AnalysisResult` 데이터클래스로 표현

### Key Data Classes

**config.py:**
- `Account(username, category)` - 분석 대상 계정
- `AnalysisConfig(days, content_type, limit_per_account, ...)` - 분석 설정
- `Config(apify_token, accounts, analysis, ...)` - 전체 설정

**analyzer.py:**
- `HashtagStats(tag, count, hot_score, grade, ...)` - 해시태그 통계
- `ViralContent(rank, username, topic, views, likes, ...)` - 바이럴 콘텐츠
- `Insight(number, title, description, keywords)` - 분석 인사이트
- `AnalysisResult(total_posts, top_hashtags, top_viral, insights)` - 최종 결과

### Key Functions

**fetcher.py:**
- `InstagramFetcher.fetch_all()` → `Dict` (profiles, posts)
- `InstagramFetcher.fetch_posts()` → `List[Dict]`

**analyzer.py:**
- `InstagramAnalyzer.analyze(data)` → `AnalysisResult`

**sheets.py:**
- `SheetsReporter.generate_report(result)` → `Dict` (url, spreadsheet_id)

**mailer.py:**
- `GmailSender.send_report(result, sheets_info, recipients)` → `List[Dict]`

**reporter.py:**
- `InstagramTrendReporter.run()` → `Dict` (summary)

### Testing Requirements

각 모듈은 독립적으로 테스트 가능:

```python
# fetcher 테스트
from src.fetcher import InstagramFetcher
fetcher = InstagramFetcher(config)
data = fetcher.fetch_all()

# analyzer 테스트
from src.analyzer import InstagramAnalyzer
analyzer = InstagramAnalyzer(config)
result = analyzer.analyze(data)
```

### Common Patterns

1. **Dependency Injection**: 모든 클래스는 `Config` 객체를 생성자로 받음
2. **Optional Config**: `config: Optional[Config] = None` → `get_config()` 폴백
3. **환경 분기**: `is_cloud_environment()`로 로컬/클라우드 인증 분기
4. **데이터클래스**: 모든 데이터 구조는 `@dataclass`로 정의

### Hot Score Formula

해시태그 랭킹에 사용되는 핫스코어 계산:
```
hot_score = frequency × (avg_engagement ^ 0.3)
```

### Grade Classification

| Grade | Hot Score | Meaning |
|-------|-----------|---------|
| 🔥 Hot | 50+ | 현재 가장 핫한 키워드 |
| 📈 Rising | 25-50 | 상승 중인 키워드 |
| ⚖️ Stable | <25 | 안정적인 키워드 |

## Dependencies

### Internal

모든 모듈은 `config.py`와 `credentials.py`에 의존

### External

| Package | Used In | Purpose |
|---------|---------|---------|
| `apify_client` | fetcher.py | Instagram API 호출 |
| `google-api-python-client` | sheets.py, mailer.py | Google API |
| `google-auth-oauthlib` | sheets.py, mailer.py | OAuth 인증 |
| `keyring` | credentials.py | 로컬 크레덴셜 저장 |
| `pyyaml` | config.py | YAML 설정 파싱 |
| `statistics` | analyzer.py | 통계 계산 |

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
