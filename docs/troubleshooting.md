# Instagram Trend Reporter - 문제 해결 가이드

실제 버그 리포트와 운영 이슈를 바탕으로 공통적인 문제, 근본 원인, 해결 방법을 정리한 문서입니다.

---

## 목차

- [인증 관련 문제](#인증-관련-문제)
- [스크래핑 관련 문제](#스크래핑-관련-문제)
- [카테고리 분류 문제](#카테고리-분류-문제)
- [v2.0 릴리즈 개선사항](#v20-릴리즈-개선사항)

---

## 인증 관련 문제

### Google OAuth 설정 누락

**이슈 참조:** #2591

#### 문제
인스타그램 스크래핑은 성공했으나, Google Sheets 리포트 생성에서 다음 오류가 발생:

```
ValueError: Google OAuth 설정을 찾을 수 없습니다.
```

#### 근본 원인
`src/sheets.py:_get_credentials()`에서 환경에서 Google OAuth 자격 증명을 찾을 수 없습니다.

#### 해결 방법

**로컬 환경:**
```yaml
# config/settings.yaml
google:
  client_id: "your-client-id.apps.googleusercontent.com"
  client_secret: "your-client-secret"
```

또는 환경변수 설정:
```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

**Streamlit Cloud:**
`.streamlit/secrets.toml`에 추가:
```toml
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"
SHEETS_TOKEN = '{"token":"...","refresh_token":"..."}'
GMAIL_TOKEN = '{"token":"...","refresh_token":"..."}'
```

---

### 필수 Python 패키지 누락

**이슈 참조:** #2590

#### 문제
```
ModuleNotFoundError: No module named 'apify_client'
ModuleNotFoundError: No module named 'google_auth_oauthlib'
```

#### 근본 원인
필수 Python 패키지가 설치되지 않았습니다.

#### 해결 방법
모든 의존성 설치:
```bash
pip install -r requirements.txt
```

**필수 패키지:**
| 패키지 | 버전 | 용도 |
|---------|---------|---------|
| `apify-client` | 1.12.2 | Instagram 데이터 스크래핑 |
| `google-auth-oauthlib` | 1.2.4 | Google OAuth 인증 |
| `matplotlib` | 최신 | 차트 생성 (워드클라우드) |
| `wordcloud` | 최신 | 해시태그 워드클라우드 |
| `plotly` | 최신 | 인터랙티브 차트 |
| `kaleido` | 최신 | 정적 차트 내보내기 |
| `keyring` | 25.7.0 | 자격 증명 저장 (로컬) |

---

### OAuth 토큰 만료

#### 문제
```
Error: Token has been expired or revoked.
```

#### 해결 방법

**로컬 (keyring):**
```bash
# 저장된 토큰 삭제
python -c "import keyring; keyring.delete_password('instagram-trend-reporter', 'sheets')"

# OAuth 흐름 다시 실행
python main.py test
```

**Streamlit Cloud:**
새 OAuth 토큰을 생성하여 Secrets 업데이트:
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. OAuth 2.0 자격 증명 생성
3. 로컬에서 인증 흐름 실행하여 refresh 토큰 획득
4. 토큰 JSON을 Secrets에 복사

---

## 스크래핑 관련 문제

### Instagram GraphQL 파싱 오류

**이슈 참조:** #2598

#### 문제
```
Parse Error: Expected HTTP/, RTSP/ or ICE/
Error: malformed HTTP response
```

- 약 50% 실패율
- Instagram API에서 malformed 응답 반환

#### 근본 원인
- Instagram 봇 탐지 메커니즘
- Instagram GraphQL API의 Rate limiting
- Proxy IP 차단

#### 완화 전략

| 전략 | 구현 |
|----------|----------------|
| **재시도 로직** | Apify CheerioCrawler 세션 로테이션 |
| **타임아웃 연장** | `timeout_secs: 300` (5분) + 계정당 버퍼 |
| **청크 분할** | 30일 초과 기간을 자동 분할 |
| **비용 상한선** | 실행당 `max_cost_usd: 2.0` |

#### 설정 권장사항
```yaml
scraper:
  max_request_retries: 3
  max_concurrency: 5
  timeout_secs: 300
  timeout_per_account_secs: 30
  max_cost_usd: 2.0
```

---

### 높은 재시도율 / 프록시 오류

**이슈 참조:** #2703

#### 증상
```
proxy 590 UPSTREAM503
request blocked
session errors
```

#### 설명
이들은 Apify의 CheerioCrawler의 **정상 재시도 동작**입니다:
- 감지된 차단 시 세션 로테이션 트리거
- 프록시 풀 로테이션이 설계대로 작동
- 재시도는 스크래퍼에 내장되어 있습니다.

#### 우려 기준

| 지표 | 임계값 | 조치 |
|--------|-----------|--------|
| 실패율 | >80% | Apify 대시보드 확인 |
| 결과 0개 | 0개 포스트 | 계정명 확인 |
| 지속적인 타임아웃 | 매 실행 | `timeout_secs` 증가 |

---

### 데이터 품질 검증 실패

#### 문제
```
데이터 품질이 너무 낮아 분석을 진행할 수 없습니다.
```

#### 근본 원인
다음 이유로 수집된 데이터가 부족:
- 비공개/비활성 계정
- Instagram rate limits
- 너무 짧은 분석 기간

#### 해결 방법
`src/fetcher.py:validate_fetch_quality()`의 품질 지표 확인:

| 지표 | 최소값 | 경고 메시지 |
|--------|----------|----------------|
| 계정당 포스트 | 2개 | `포스트 부족` |
| 캡션 비율 | 30% | `캡션 비율 낮음` |
| 인게이지먼트 비율 | 50% | `인게이지먼트 데이터 부족` |

**해결책:**
1. 대상 계정이 공개 계정인지 확인
2. `days` 파라미터 증가 (기본값: 7)
3. 대상 계정 수 감소
4. Apify 할당량 소진 여부 확인

---

## 카테고리 분류 문제

### 셀럽/브랜드 매핑 누락

**이슈 참조:** #2829

#### 문제
10개 셀럽 태그와 4개 브랜드 태그가 "general"로 잘못 분류.

#### 누락 태그 (수정됨)
| 타입 | 누락 태그 |
|------|--------------|
| **셀럽** | 저스틴비버 (Justin Bieber), 랄리사 (Lalisa), bts완전체, 몽클레르 |
| **브랜드** | Moncler (몽클레르로 오타) |

#### 해결 방법
`src/categories.py`에 키워드 추가:
```python
_CLEB_SUBSTRING = frozenset({
    ...
    "저스틴비버", "justinbieber", "비버부부",
    "bts완전체",
    ...
})

_BRAND_SUBSTRING = frozenset({
    ...
    "몽클레르", "몽클레어", "moncler",  # 두 맞춤법 모두 추가
    ...
})
```

---

### 카테고리 분류 정확도 개선

**이슈 참조:** #2774

#### 개선 전/후
| 지표 | 개선 전 | 개선 후 | 향상도 |
|--------|---------|---------|---------|
| 셀럽 정확도 | 13 | 20 | +54% |
| 아이템 정확도 | 8 | 10 | +25% |
| General (노이즈) | 40% | 22% | -45% |

#### 변경 사항
1. **한국어 철자 변형** 추가: 일반적인 패션 용어
   - `김제니` → `제니`, `jennie`, `jenniekim`, `kimjennie`
   - `재킷` → `자켓`, `jacket`
   - `드레스` → `원피스`, `dress`

2. **2단계 매칭** 구현:
   ```python
   # 1단계: 모호한 짧은 단어 exact match
   if tag_clean in exact_set:
       return cat

   # 2단계: 고유 키워드 substring match
   for kw in substring_set:
       if kw in tag_clean:
           return cat
   ```

---

### 트렌드 분석의 셀럽 이름 노이즈

**이슈 참조:** #2705, #2767

#### 문제
팬 콘텐츠가 트렌드 분석에서 노이즈 생성 - 셀럽 해시태그가 패션 관련성이 없어도 트렌드를 지배.

#### 해결 방법
`app.py`의 셀럽 제외 필터:

**100개 이상 한국 셀럽**을 카테고리별로 기본 제외:
- **걸그룹/여성 아이돌**: IVE, BLACKPINK, NewJeans, aespa, LE SSERAFIM 등
- **남성 아이돌**: BTS, EXO, NCT, Stray Kids, SEVENTEEN 등
- **여배우**: 손연진, 김태리, 한소희 등
- **남배우**: 유재석, 강호동, 신동엽 등
- **힙합/R&B**: 지코, 크러쉬 등
- **예능/MC**: 유재석, 박명수 등

**UI 사용법:**
```python
use_celeb_filter = st.checkbox(
    f"셀럽/인물 이름 자동 제외 ({len(_DEFAULT_EXCLUDE_CELEB)}개)",
    value=False,
    help="활성화하면 아이돌, 배우 등 인물 이름 해시태그를 자동 제외합니다. "
         "패션 매거진처럼 셀럽 태그가 트렌드 신호인 경우 OFF 권장.",
)
```

**참고:** 패션 매거진은 셀럽 태그가 트렌드 신호인 경우 이 필터를 **OFF**로 유지.

---

## v2.0 릴리즈 개선사항

**이슈 참조:** #2720

### 추가된 기능

| 기능 | 설명 |
|---------|-------------|
| **시각화 대시보드** | 인터랙티브 차트가 포함된 Streamlit UI |
| **향상된 방어 로직** | 데이터 품질 검증, 청크 분할, 비용 상한선 |
| **확장된 셀럽 필터** | 100개 이상 한국 셀럽 제외 목록 |
| **한국어 워드클라우드** | 시각화를 위한 한국어 폰트 지원 |

### 품질 개선사항

#### v2.0 이전
- 기본 오류 처리
- 데이터 검증 없음
- 수동 설정만 가능

#### v2.0 이후
- 포괄적인 품질 검증
- 자동 30일 청크 분할
- 비개발자용 웹 UI
- 실시간 진행률 피드백

---

## 빠른 참조

### 공통 오류 메시지

| 오류 | 원인 | 빠른 해결 |
|-------|--------|-----------|
| `APIFY_TOKEN이 설정되지 않았습니다` | Apify 토큰 누락 | `APIFY_TOKEN` 환경변수 설정 |
| `Google OAuth 설정을 찾을 수 없습니다` | Google 자격 증명 누락 | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` 설정 |
| `수집 완전 실패` | 데이터 0개 수집 | 계정명 확인, 공개 계정인지 확인 |
| `SHEETS_TOKEN이 설정되지 않았습니다` | 클라우드 토큰 누락 | Streamlit Secrets에 OAuth 토큰 추가 |
| `Maximum total charge exceeded` | 비용 상한 도달 | `max_cost_usd` 증가 또는 계정 수 감소 |
| `ModuleNotFoundError` | 의존성 누락 | `pip install -r requirements.txt` 실행 |

### 환경변수 참조

| 변수 | 용도 | 필수 여부 |
|----------|---------|----------|
| `APIFY_TOKEN` | Apify API 인증 | 필수 |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | 로컬 전용 |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 시크릿 | 로컬 전용 |
| `SHEETS_TOKEN` | Sheets OAuth 토큰 (JSON) | 클라우드 전용 |
| `GMAIL_TOKEN` | Gmail OAuth 토큰 (JSON) | 클라우드 전용 |

### 설정 모범 사례

```yaml
# config/settings.yaml
scraper:
  max_request_retries: 3      # 실패 요청 재시도
  max_concurrency: 5          # 병렬 요청 수
  timeout_secs: 300           # 5분 기본 타임아웃
  timeout_per_account_secs: 30  # 계정당 추가 시간
  max_cost_usd: 2.0          # 비용 안전 상한선
  min_results_threshold: 3     # 계속할 최소 포스트 수

analysis:
  days: 7                     # 분석 기간 (일)
  content_type: reels          # posts, reels, 또는 stories
  limit_per_account: 50        # 계정당 최대 포스트 수
```

---

## 여전히 문제가 있나요?

1. 전체 설정 안내는 [README.md](../README.md) 참조
2. 사용법 상세는 [USER_GUIDE.md](USER_GUIDE.md) 참조
3. GitHub 이슈로 다음 정보 포함하여 제보:
   - 오류 메시지
   - 사용된 설정
   - 환경 (로컬 / Streamlit Cloud)
   - 재현 단계
