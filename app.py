"""
📊 Instagram Trend Reporter - Streamlit Web App
비개발자도 쉽게 사용할 수 있는 인스타그램 트렌드 분석 도구
"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import sys

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config, get_config
from src.fetcher import InstagramFetcher
from src.analyzer import InstagramAnalyzer
from src.sheets import SheetsReporter
from src.mailer import GmailSender

# 페이지 설정
st.set_page_config(
    page_title="인스타그램 트렌드 리포터",
    page_icon="📊",
    layout="wide",
)

# 통일된 스타일 시스템
st.markdown("""
<style>
    /* 전체 폰트 기본 설정 */
    .stApp {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 메인 헤더 */
    .main-header {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #E1306C, #F77737);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 1rem 0 0.5rem 0;
        padding: 0;
    }
    
    .sub-header {
        font-size: 0.9rem;
        color: #888;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* 섹션 헤더 통일 */
    .section-header {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #E0E0E0 !important;
        margin-bottom: 0.8rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #333;
    }
    
    /* Streamlit 기본 헤더 오버라이드 */
    .stApp h1 {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    
    .stApp h2 {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    .stApp h3 {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    
    /* 메트릭 카드 크기 조정 */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #888 !important;
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #1a1a1a;
    }
    
    [data-testid="stSidebar"] .stMarkdown h2 {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #E0E0E0 !important;
        margin-top: 1rem;
    }
    
    /* 슬라이더 라벨 */
    .stSlider label {
        font-size: 0.85rem !important;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        border-radius: 8px !important;
    }
    
    /* 성공/정보 박스 */
    .stAlert {
        font-size: 0.85rem !important;
    }
    
    /* 텍스트 영역 */
    .stTextArea textarea {
        font-size: 0.85rem !important;
    }
    
    /* 데이터프레임 */
    .stDataFrame {
        font-size: 0.85rem !important;
    }
    
    /* 카드 스타일 */
    .metric-card {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    
    .metric-card .value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #E1306C;
    }
    
    .metric-card .label {
        font-size: 0.8rem;
        color: #888;
        margin-top: 0.3rem;
    }
    
    /* 구분선 */
    hr {
        margin: 1.5rem 0 !important;
        border-color: #333 !important;
    }
    
    /* 푸터 */
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.75rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown('<h1 class="main-header">📊 인스타그램 트렌드 리포터</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">인스타그램 릴스 트렌드 분석 → Google Sheets 리포트 → 이메일 전송</p>', unsafe_allow_html=True)

# 사이드바 - 설정
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")
    
    # 분석 기간
    days = st.slider("분석 기간 (일)", 1, 30, 7)
    
    # 콘텐츠 유형
    content_type = st.selectbox(
        "콘텐츠 유형",
        ["reels", "posts"],
        index=0,
        help="릴스: 짧은 동영상 (바이럴 분석에 추천) | 포스트: 이미지/캐러셀",
    )
    
    # Top N 설정
    top_hashtags = st.slider("Top 해시태그 개수", 10, 100, 50)
    top_viral = st.slider("Top 바이럴 개수", 3, 20, 7)
    
    st.markdown("---")
    
    # 이메일 설정
    st.markdown("## 📧 이메일 전송")
    send_email = st.checkbox("이메일로 리포트 전송", value=True)
    
    if send_email:
        email_input = st.text_area(
            "수신자 이메일 (줄바꿈으로 구분)",
            "dedurox@gmail.com\nkimdh@lfcorp.com",
            height=80,
        )
        recipients = [e.strip() for e in email_input.split("\n") if e.strip()]

# 메인 영역
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown('<p class="section-header">📋 분석 대상 계정</p>', unsafe_allow_html=True)
    
    # 기본 계정 목록
    default_accounts = [
        "dip_magazine",
        "the_edit.co.kr", 
        "on_fleekkk",
        "fashionandstyle.official",
        "luxmag.kr",
        "histofit",
    ]
    
    accounts_input = st.text_area(
        "계정 목록 (줄바꿈으로 구분, @ 없이)",
        "\n".join(default_accounts),
        height=180,
        label_visibility="collapsed",
    )
    accounts = [a.strip().replace("@", "") for a in accounts_input.split("\n") if a.strip()]

with col2:
    st.markdown('<p class="section-header">📊 현재 설정 요약</p>', unsafe_allow_html=True)
    
    # 2x2 그리드로 메트릭 표시
    m1, m2 = st.columns(2)
    with m1:
        st.metric("분석 기간", f"{days}일")
        st.metric("Top 해시태그", f"{top_hashtags}개")
    with m2:
        st.metric("콘텐츠", content_type)
        st.metric("Top 바이럴", f"{top_viral}개")

st.markdown("---")

# 실행 버튼
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    run_button = st.button(
        "🚀 리포트 생성 시작",
        type="primary",
        use_container_width=True,
    )

# 실행 로직
if run_button:
    # 진행 상황 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 설정 로드 및 오버라이드
        config = get_config()
        config.analysis.days = days
        config.analysis.content_type = content_type
        config.analysis.top_hashtags = top_hashtags
        config.analysis.top_viral = top_viral
        
        # 계정 업데이트
        from src.config import Account
        config.accounts = [Account(username=a, category="Fashion") for a in accounts]
        
        # 1. 데이터 수집
        status_text.text("📥 인스타그램 데이터 수집 중...")
        progress_bar.progress(10)
        
        fetcher = InstagramFetcher(config)
        data = fetcher.fetch_all()
        
        progress_bar.progress(40)
        status_text.text(f"✅ {len(data['posts'])}개 콘텐츠 수집 완료")
        
        # 2. 분석
        status_text.text("🔍 데이터 분석 중...")
        progress_bar.progress(50)
        
        analyzer = InstagramAnalyzer(config)
        result = analyzer.analyze(data)
        
        progress_bar.progress(60)
        
        # 3. Google Sheets 생성
        status_text.text("📊 Google Sheets 리포트 생성 중...")
        progress_bar.progress(70)
        
        sheets_reporter = SheetsReporter(config)
        sheets_info = sheets_reporter.generate_report(result)
        
        progress_bar.progress(85)
        
        # 4. 이메일 전송
        email_results = []
        if send_email and recipients:
            status_text.text("📧 이메일 전송 중...")
            gmail_sender = GmailSender(config)
            email_results = gmail_sender.send_report(result, sheets_info, recipients)
        
        progress_bar.progress(100)
        status_text.text("✅ 완료!")
        
        # 결과 표시
        st.success("🎉 리포트 생성 완료!")
        
        # 결과 메트릭
        st.markdown('<p class="section-header">📈 분석 결과</p>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("분석 포스트", f"{result.total_posts}개")
        with col2:
            st.metric("Top 해시태그", f"{len(result.top_hashtags)}개")
        with col3:
            st.metric("Top 바이럴", f"{len(result.top_viral)}개")
        with col4:
            st.metric("인사이트", f"{len(result.insights)}개")
        
        # 리포트 링크
        st.markdown("---")
        st.markdown(f"### 📎 리포트 링크")
        st.link_button("Google Sheets에서 보기 →", sheets_info['url'])
        
        # Top 해시태그 미리보기
        st.markdown('<p class="section-header">🏷️ Top 10 해시태그</p>', unsafe_allow_html=True)
        hashtag_data = [
            {
                "순위": i+1,
                "해시태그": h.tag,
                "핫스코어": h.hot_score,
                "등급": h.grade,
            }
            for i, h in enumerate(result.top_hashtags[:10])
        ]
        st.dataframe(hashtag_data, use_container_width=True, hide_index=True)
        
        # Top 바이럴 미리보기
        st.markdown('<p class="section-header">🔥 Top 바이럴 콘텐츠</p>', unsafe_allow_html=True)
        viral_data = [
            {
                "순위": v.rank,
                "계정": v.username,
                "주제": v.topic[:30],
                "조회수": f"{v.views:,}",
                "좋아요": f"{v.likes:,}",
            }
            for v in result.top_viral
        ]
        st.dataframe(viral_data, use_container_width=True, hide_index=True)
        
        # 이메일 결과
        if email_results:
            st.markdown('<p class="section-header">📧 이메일 전송 결과</p>', unsafe_allow_html=True)
            for r in email_results:
                if r["success"]:
                    st.success(f"✅ {r['to']}")
                else:
                    st.error(f"❌ {r['to']}: {r.get('error', 'Unknown error')}")
        
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.exception(e)

# 푸터
st.markdown(
    '<p class="footer">Made with ❤️ by 갓댐봇 🐻 | <a href="https://github.com/your-repo">GitHub</a></p>',
    unsafe_allow_html=True,
)
