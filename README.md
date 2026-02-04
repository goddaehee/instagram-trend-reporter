# 📊 Instagram Trend Reporter

인스타그램 트렌드 분석 → Google Sheets 리포트 → 이메일 전송 자동화 도구

## 🚀 기능

- **Apify**로 인스타그램 릴스/포스트 수집
- **핫스코어 분석**으로 트렌드 해시태그 Top 50 추출
- **바이럴 콘텐츠** Top 7 식별
- **인사이트** 자동 생성
- **Google Sheets** 리포트 생성 (5개 시트)
- **Gmail**로 리포트 자동 전송

## 📁 프로젝트 구조

```
instagram-trend-reporter/
├── src/
│   ├── config.py      # 설정 관리
│   ├── fetcher.py     # Apify 데이터 수집
│   ├── analyzer.py    # 분석 (핫스코어, 아웃라이어)
│   ├── sheets.py      # Google Sheets 리포트
│   ├── mailer.py      # Gmail 전송
│   └── reporter.py    # 전체 파이프라인
├── config/
│   └── settings.yaml  # 설정 파일
├── main.py            # CLI 엔트리포인트
├── requirements.txt
└── README.md
```

## ⚙️ 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 설정 파일 수정
vi config/settings.yaml
```

## 🔧 설정

`config/settings.yaml`:

```yaml
apify:
  token: "your_apify_token"

accounts:
  - username: account1
    category: Fashion

analysis:
  days: 7
  top_hashtags: 50
  top_viral: 7

email:
  recipients:
    - you@example.com
```

## 🎯 사용법

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

## 📊 리포트 시트 구성

| 시트 | 내용 |
|------|------|
| Top50_해시태그 | 순위/키워드/카테고리/빈도/핫스코어/등급 |
| Top7_바이럴콘텐츠 | 순위/계정/주제/좋아요/댓글/조회수/URL |
| 인사이트 | 핵심 트렌드 분석 5가지 |
| 부록_용어설명 | 14개 용어 정리 |
| 리포트정보 | 메타데이터 및 공식 |

## 📈 핫스코어 공식

```
핫스코어 = 빈도 × (평균인게이지먼트 ^ 0.3)
인게이지먼트 = 좋아요 + (댓글 × 3) + (조회수 × 0.1)
```

## ⏰ 크론 설정 (선택)

```bash
# 매주 월요일 오전 9시 실행
0 9 * * 1 cd /path/to/instagram-trend-reporter && python main.py run
```

## 📝 라이선스

MIT License
