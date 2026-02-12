# Instagram Trend Reporter

인스타그램 릴스/포스트 트렌드를 자동 분석하여 Google Sheets 리포트를 생성하고, 이메일로 발송하는 자동화 도구입니다. 패션 관련 인스타그램 계정의 해시태그 트렌드와 바이럴 콘텐츠를 분석하여 주간 리포트를 생성합니다.

## Tech Stack

| 분야 | 기술 |
|------|------|
| **언어** | Python 3.10+ |
| **CLI** | argparse |
| **웹 UI** | Streamlit |
| **데이터 수집** | Apify Client (Instagram Scraper) |
| **데이터 분석** | pandas, statistics |
| **리포트 생성** | Google Sheets API v4 |
| **이메일 발송** | Gmail API |
| **시각화** | Matplotlib, Plotly, Google Charts |
| **인증** | Google OAuth 2.0, keyring |
| **배포** | Streamlit Cloud, GitHub Actions |

### Tech Stack 상세 설명

| 기술 | 설명 |
|------|------|
| **Python 3.10+** | 프로젝트 기반 언어 |
| **argparse** | CLI 옵션 파싱 (`--days`, `--no-email` 등) |
| **Streamlit** | 비개발자용 웹 UI 프레임워크, 사이드바 설정/실시간 피드백 |
| **Apify Client** | Instagram 데이터 스크래핑을 위한 서드파티 API (Instagram Scraper Actor 사용) |
| **pandas** | 데이터 분석 및 통계 처리 |
| **statistics** | 통계 함수 (평균, 표준편차 등) |
| **Google Sheets API v4** | 스프레드시트 생성/포맷팅/차트 삽입 |
| **Gmail API** | HTML 이메일 발송 (MIME multipart, 첨부 이미지) |
| **Matplotlib** | 정적 차트 생성 (워드클라우드, 이메일용 바/파이 차트) |
| **Plotly** | Streamlit 대시보드용 인터랙티브 차트 (버블, 트리맵) |
| **Google Charts** | Sheets 내장 차트 (바, 컬럼, 도넛) |
| **Google OAuth 2.0** | 구글 API 인증 (keyring 로컬 저장 / Secrets 클라우드) |
| **keyring** | 로컬 환경에서 OAuth 토큰 안전 저장 |
| **Streamlit Cloud** | 1-Click 클라우드 배포, Secrets 관리 |
| **GitHub Actions** | 주간 리포트 자동화 CI/CD |

## Overview

### 핵심 기능

| 기능 | 설명 |
|------|------|
| **자동 데이터 수집** | Apify API로 인스타그램 릴스/포스트 수집 |
| **핫스코어 분석** | 빈도와 인게이지먼트를 결합한 트렌드 점수화 |
| **카테고리 분류** | 8개 카테고리, 908개 키워드 자동 분류 |
| **등급 부여** | Hot / Rising / Stable 3단계 등급 시스템 |
| **인사이트 생성** | 데이터 기반 자동 인사이트 5개 추출 |
| **Google Sheets 리포트** | 5개 시트로 구성된 시각화 리포트 |
| **이메일 발송** | HTML 차트 포함 이메일 자동 전송 |
| **Streamlit UI** | 비개발자용 웹 인터페이스 |

### 대상 사용자

- **개발자**: CLI로 자동화 파이프라인 구축
- **비개발자**: Streamlit 웹 UI로 클릭만으로 리포트 생성
- **데이터 분석가**: Google Sheets에서 추가 분석 수행

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           ENTRY POINTS                                  │
│  ┌────────────────────┐         ┌──────────────────────┐              │
│  │  main.py (CLI)  │         │ app.py (Streamlit) │              │
│  └────────┬───────────┘         └──────────┬───────────┘              │
└───────────┼──────────────────────────────┼───────────────────────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      CORE ORCHESTRATOR (reporter.py)                         │
│   fetcher → analyzer → sheets → mailer                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 모듈 구조

| 모듈 | 역할 |
|------|------|
| `src/fetcher.py` | Apify API로 인스타그램 데이터 수집 |
| `src/analyzer.py` | 핫스코어 계산, 등급 분류, 인사이트 생성 |
| `src/sheets.py` | Google Sheets 리포트 생성 및 포맷팅 |
| `src/mailer.py` | Gmail로 HTML 이메일 전송 |
| `src/credentials.py` | 로컬/클라우드 환경 인증 관리 |
| `src/categories.py` | 908개 키워드 카테고리 분류 |
| `src/visualization/` | 차트 생성, 이메일 템플릿 |

---

## Data Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FETCHER   │ →  │  ANALYZER   │ →  │   SHEETS    │ →  │   MAILER    │
│  Apify API  │    │   Hot Score │    │  Report Gen │    │   Gmail     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

| 단계 | 모듈 | 입력 | 출력 | 핵심 작업 |
|------|------|------|------|----------|
| 1 | fetcher | config (계정, 기간) | raw 데이터 | Apify API로 Instagram 수집 |
| 2 | analyzer | raw 데이터 | AnalysisResult | 핫스코어, 등급, 인사이트 생성 |
| 3 | sheets | AnalysisResult | spreadsheet_id | Google Sheets 리포트 생성 |
| 4 | mailer | 결과 + URL | 전송 결과 | 이메일 발송 |

---

## Hot Score Formula

### 인게이지먼트 계산

```
인게이지먼트 = 좋아요 + (댓글 × 3) + (조회수 × 0.1)
```

- **댓글 × 3**: 댓글은 좋아요보다 참여도가 높은 신호로 가중치 부여
- **조회수 × 0.1**: 영상 조회는 상대적으로 쉬운 행위이므로 낮은 가중치

### 핫스코어 계산

```
핫스코어 = 빈도 × (평균인게이지먼트 ^ 0.3)
```

- **지수 0.3**: 인게이지먼트가 핫스코어에 과도한 영향을 미치지 않도록 완화
  - 0.3 미만: 빈도가 너무 중시됨
  - 0.5 초과: 인게이지먼트가 지나치게 반영됨
  - **0.3**: 빈도와 인게이지먼트의 균형 있는 조합

### 예시 계산

| 해시태그 | 빈도 | 평균 인게이지먼트 | 핫스코어 |
|----------|-------|-------------------|----------|
| #패션 | 8 | 50,000 | 8 × (50000^0.3) ≈ **136** |
| #룩북 | 5 | 80,000 | 5 × (80000^0.3) ≈ **103** |
| #데일리룩 | 12 | 10,000 | 12 × (10000^0.3) ≈ **96** |

---

## Grade Classification

| 등급 | 핫스코어 | 색상 | 의미 |
|------|-----------|------|------|
| 🔥 Hot | 50+ | 핑크 #E1306C | 현재 가장 핫한 키워드 |
| 📈 Rising | 25~50 | 오렌지 #F77737 | 상승 중인 키워드 |
| ⚪ Stable | <25 | 회색 #9E9E9E | 안정적인 키워드 |

### 등급 결정 로직

```
if hot_score >= 50:
    if count >= 3 and avg_engagement >= 100,000:
        reason = "고빈도+고인게이지"
    elif avg_engagement >= 300,000:
        reason = "초고인게이지 단발"
    elif count >= 5:
        reason = "고빈도"
    else:
        reason = "높은 핫스코어"
elif hot_score >= 25:
    reason = "상승세"
else:
    reason = "안정적"
```

---

## Category System

### 8개 카테고리

| 카테고리 | 색상 | 샘플 키워드 수 | 우선순위 |
|----------|------|----------------|----------|
| 셀럽/인플루언서 | 보라 #833AB4 | 150개 | 1위 |
| 브랜드 | 파랑 #405DE6 | 180개 | 2위 |
| 패션 아이템 | 초록 #2ECC71 | 200개 | 3위 |
| 스타일/무드 | 핑크 #E1306C | 150개 | 4위 |
| 뷰티 | 분홍 #FF6B9D | 100개 | 5위 |
| 라이프스타일 | 노랑 #F39C12 | 80개 | 6위 |
| 이벤트/시즌 | 청록 #1ABC9C | 30개 | 7위 |
| 일반 | 회색 #9E9E9E | 기타 | 8위 |

### 2단계 매칭

1. **Exact Match**: 태그 전체가 키워드와 일치 (짧은/모호한 키워드용)
   - 예: `#v`, `#cos`, `#gap`, `#bts` → 정확히 일치할 때만

2. **Substring Match**: 태그 내 키워드 포함 (고유 키워드용)
   - 예: `#blackpink` → `블랙핑크` 포함 확인

### 우선순위

```
celeb > brand > item > style > beauty > lifestyle > event > general
```

동일 해시태그가 여러 카테고리에 매칭될 경우, 높은 우선순위 카테고리가 선택됩니다.

---

## Report Structure

### Google Sheets 5개 시트

| 시트 | 컬럼 | 설명 |
|------|-------|------|
| **Top50_해시태그** | 순위, 키워드, 카테고리, 빈도, 평균인게이지먼트, 핫스코어, 등급, 등급근거 | 트렌드 해시태그 랭킹 |
| **Top7_바이럴콘텐츠** | 순위, 계정, 주제, 좋아요, 댓글, 조회수, 인게이지먼트, URL | 바이럴 콘텐츠 상세 |
| **인사이트** | 번호, 인사이트 제목, 상세 설명, 관련 키워드 | 자동 생성된 인사이트 5개 |
| **부록_용어설명** | 용어, 영문, 설명, 예시 | 14개 용어 정리 |
| **리포트정보** | 항목, 내용 | 메타데이터 및 공식 |

### 시각화 요소

- **핫스코어 바 차트**: Top 10 해시태그
- **카테고리 도넛 차트**: 카테고리별 분포
- **바이럴 비교 차트**: 좋아요/댓글/조회수 그룹 바

---

## Email Structure

### 이메일 구성

```
┌─────────────────────────────────────────┐
│  Header (Instagram Gradient)        │
│  - 제목: 인스타그램 주간 트렌드 리포트  │
│  - 분석 기간                        │
├─────────────────────────────────────────┤
│  Metric Cards (3개)                │
│  - 분석 포스트 수                    │
│  - Top 해시태그 수                  │
│  - 바이럴 콘텐츠 수                │
├─────────────────────────────────────────┤
│  Charts                           │
│  - 핫스코어 바 차트                 │
│  - 카테고리 파이 차트                │
├─────────────────────────────────────────┤
│  Top Hashtags Tag Cloud            │
│  - 등급별 색상 태그 (핑크/오렌지/회색) │
├─────────────────────────────────────────┤
│  Viral Content Table               │
│  - 순위, 계정, 주제, 조회수, 좋아요, 링크 │
├─────────────────────────────────────────┤
│  Insights Cards                   │
│  - 인사이트 제목 + 설명              │
├─────────────────────────────────────────┤
│  CTA Button                      │
│  - Google Sheets 링크               │
└─────────────────────────────────────────┘
```

---

## Installation

### 사전 요구사항

- Python 3.10+
- Apify 계정 및 API 토큰
- Google Cloud Project (Gmail/Sheets API 활성화)

### 로컬 설치

```bash
# 리포지토리 클론
git clone https://github.com/your-repo/instagram-trend-reporter.git
cd instagram-trend-reporter

# 의존성 설치
pip install -r requirements.txt

# 설정 파일 복사
cp config/settings.example.yaml config/settings.yaml
```

### Streamlit Cloud 배포

1. GitHub에 리포지토리 푸시
2. Streamlit Cloud에 연결
3. Secrets에 다음 항목 추가:
   ```
   APIFY_TOKEN=your_token
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   SHEETS_TOKEN={"token":"...","refresh_token":"..."}
   GMAIL_TOKEN={"token":"...","refresh_token":"..."}
   ```

---

## Configuration

### YAML 설정 (config/settings.yaml)

```yaml
# Apify API 토큰
apify:
  token: "your_apify_token"

# 분석 대상 계정
accounts:
  - username: dip_magazine
    category: Fashion
  - username: the_edit.co.kr
    category: Fashion

# 분석 설정
analysis:
  days: 7                    # 분석 기간 (일)
  content_type: reels          # posts, reels, stories
  limit_per_account: 50        # 계정당 최대 수집 개수
  top_hashtags: 50           # Top 해시태그 개수
  top_viral: 7               # Top 바이럴 콘텐츠 개수
  exclude_hashtags:           # 제외할 해시태그
    - 제작지원
    - 광고
    - 행사초대

# 스크래퍼 안정성 설정
scraper:
  max_request_retries: 3       # 요청 재시도 횟수
  max_concurrency: 5           # 동시 요청 수
  timeout_secs: 300            # 타임아웃 (초)
  max_cost_usd: 2.0           # 비용 상한선 ($)
  min_results_threshold: 3     # 최소 결과 수

# 이메일 수신자
email:
  recipients:
    - you@example.com
```

### 환경변수

| 변수 | 설명 | 필수 여부 |
|------|------|----------|
| `APIFY_TOKEN` | Apify API 토큰 | 필수 |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | 로컬에서 필수 |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 시크릿 | 로컬에서 필수 |
| `SHEETS_TOKEN` | Google Sheets OAuth 토큰 (JSON) | Streamlit Cloud 필수 |
| `GMAIL_TOKEN` | Gmail OAuth 토큰 (JSON) | Streamlit Cloud 필수 |

### Keyring (로컬 전용)

로컬 환경에서는 OAuth 토큰을 keyring에 저장할 수 있습니다:

```bash
# 첫 실행 시 OAuth 흐름이 자동으로 시작됨
python main.py test
```

---

## Usage

### CLI 사용

```bash
# 전체 파이프라인 실행
python main.py run

# 이메일 전송 제외
python main.py run --no-email

# 분석 기간 변경 (14일)
python main.py run --days 14

# 수신자 지정
python main.py run --email a@b.com --email c@d.com

# 설정 테스트
python main.py test
```

### Streamlit UI 사용

```bash
# 로컬에서 실행
streamlit run app.py

# 브라우저에서 http://localhost:8501 접속
```

UI에서 다음을 설정할 수 있습니다:
- 분석 기간 (최근 N일 또는 기간 직접 지정)
- 콘텐츠 유형 (posts / reels)
- Top 해시태그/바이럴 개수
- 제외 해시태그
- 셀럽/인물 자동 제외 필터
- 수신자 이메일

### 크론 설정

```bash
# 매주 월요일 오전 9시 실행
0 9 * * 1 cd /path/to/instagram-trend-reporter && python main.py run

# 매월 1일, 15일 오전 10시 실행
0 10 1,15 * * cd /path/to/instagram-trend-reporter && python main.py run
```

---

## Defense Logic & Stability

### 30일 청크 분할

- **문제**: Instagram 스크래핑은 30일 이상 과거 데이터를 수집할 때 불안정
- **해결**: 자동으로 30일 단위로 분할하여 수집
  ```python
  # 60일 요청 → 2회 분할
  # 90일 요청 → 3회 분할
  ```

### 품질 검증

수집 완료 후 다음 항목 검증:

| 항목 | 기준 | 경고 |
|------|------|------|
| 포스트 수 | 계정당 최소 2개 | `포스트 부족` |
| 캡션 비율 | 30% 이상 | `캡션 비율 낮음` |
| 인게이지먼트 데이터 | 50% 이상 | `인게이지먼트 데이터 부족` |

### 비용 상한선

```yaml
scraper:
  max_cost_usd: 2.0  # 실행당 최대 $2
```

초과 시 Apify가 자동으로 중단합니다.

---

## Visualization

### Instagram 브랜드 컬러

```python
INSTAGRAM_COLORS = {
    "pink": "#E1306C",     # Primary
    "orange": "#F77737",   # Secondary
    "yellow": "#FCAF45",   # Accent
    "purple": "#833AB4",   # Additional
    "blue": "#405DE6",     # Additional
}
```

### 차트 종류

| 차트 | 라이브러리 | 용도 |
|------|-----------|------|
| 핫스코어 바 차트 | Matplotlib (이메일), Google Charts (시트) | Top 10 해시태그 |
| 카테고리 파이 차트 | Matplotlib (이메일), Google Charts (시트) | 카테고리 분포 |
| 바이럴 비교 차트 | Google Charts (시트) | 좋아요/댓글/조회수 |
| 워드클라우드 | Matplotlib | 해시태그 빈도 시각화 |
| 버블 차트 | Plotly (Streamlit) | 핫스코어 vs 빈도 |
| 트리맵 | Plotly (Streamlit) | 카테고리 계층 구조 |

---

## Troubleshooting

### 인증 관련

#### Google OAuth 토큰 만료

```
Error: Token has been expired or revoked.
```

**해결**:
- 로컬: `keyring` 삭제 후 재인증
- Streamlit Cloud: Secrets에 새 토큰 발급

#### OAuth 흐름 실패

```
Error: Google OAuth 설정을 찾을 수 없습니다.
```

**해결**:
1. `~/.config/agent-skills/google.yaml` 확인
2. 또는 환경변수 `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` 설정

### Apify 관련

#### 스크래핑 실패

```
Error: 수집 완전 실패: 스크래퍼에서 데이터를 가져오지 못했습니다.
```

**해결**:
1. APIFY_TOKEN 유효성 확인
2. 계정명이 올바른지 확인
3. Instagram 로그인 요청 발생 시 Apify 대시보드에서 수동 처리

#### 비용 초과

```
Error: Apify 스크래퍼 실행 실패: Maximum total charge exceeded
```

**해결**:
- `scraper.max_cost_usd` 값 증가
- 또는 수집 계정 수 감소

### Google API 관련

#### Quota 초과

```
Error: Quota exceeded for sheets.googleapis.com
```

**해결**:
1. Google Cloud Console에서 Quota 증가 요청
2. 또는 일일 실행 횟수 감소

---

## Project Structure

```
instagram-trend-reporter/
├── app.py                    # Streamlit 웹 앱
├── main.py                   # CLI 엔트리포인트
├── requirements.txt           # Python 의존성
├── config/
│   ├── settings.yaml         # 설정 파일 (생성 필요)
│   └── settings.example.yaml # 설정 예제
├── src/
│   ├── config.py            # 설정 관리
│   ├── credentials.py       # 인증 관리
│   ├── fetcher.py          # Apify 데이터 수집
│   ├── analyzer.py         # 분석 (핫스코어, 등급)
│   ├── sheets.py          # Google Sheets 리포트
│   ├── mailer.py          # Gmail 전송
│   ├── reporter.py        # 전체 파이프라인
│   ├── categories.py       # 카테고리 분류 (908개 키워드)
│   └── visualization/
│       ├── colors.py        # 공통 컬러 팔레트
│       ├── email_charts.py # 이메일용 차트 생성
│       ├── email_template.py # HTML 이메일 템플릿
│       └── charts.py       # Streamlit용 차트
└── .github/
    └── workflows/
        └── weekly-report.yml # GitHub Actions 예제
```

---

## License

MIT License

---

## Contributing

버그 리포트나 기능 요청은 Issue로 남겨주세요.
