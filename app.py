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

# 셀럽/인물 기본 제외 목록 (해시태그 분석 노이즈 제거)
_DEFAULT_EXCLUDE_CELEB = [
    # 걸그룹 / 여성 아이돌
    "아이브", "로제", "장원영", "안유진", "제니", "리사", "지수", "카리나", "윈터", "닝닝",
    "유나", "류진", "예지", "채령", "설현", "전소미",
    "나연", "정연", "모모", "사나", "지효", "미나", "다현", "채영", "쯔위",
    "슬기", "아이린", "웬디", "조이", "예리",
    "지젤", "미연", "우기", "민니", "소연", "슈화",
    "김채원", "사쿠라", "허윤진", "카즈하", "홍은채",
    "김민주", "권은비", "최예나", "조유리", "이채연", "강혜원",
    "하니", "혜리", "유라", "민아", "나라", "설인아",
    # 남성 아이돌 / BTS / EXO / NCT 등
    "진", "슈가", "제이홉", "RM", "지민", "뷔", "정국",
    "백현", "카이", "세훈", "찬열", "디오", "첸", "수호", "시우민", "도경수",
    "태민", "온유", "키", "민호", "종현",
    "태용", "재현", "도영", "마크", "해찬", "텐", "루카스", "윈윈",
    "샤오쥔", "헨드리", "양양", "성찬", "쇼타로",
    "지드래곤", "태양", "대성", "탑",
    "송민호", "이승훈", "강승윤", "김진우",
    "강다니엘", "박지훈", "옹성우", "황민현", "배진영", "김재환", "하성운", "라이관린",
    "이대휘", "박우진",
    "로운", "차은우", "문빈", "산하", "진영",
    "김민규", "김요한", "김도훈", "김강훈", "윤찬영",
    "황인엽", "배현성",
    # 여배우
    "수지", "아이유", "김태리", "전지현", "한지민", "한효주", "한소희",
    "고아성", "고윤정", "노윤서", "이주명", "이성경", "이다희", "이솜", "이엘",
    "이청아", "이유비", "이연희", "임윤아", "임수정", "임지연",
    "전여빈", "전도연", "정유미", "정은채", "정려원", "정호연",
    "천우희", "최수영", "최지우", "최강희", "최희서", "최성은", "최예빈",
    "채수빈", "채정안", "한예리", "한예슬", "홍수주", "홍수현",
    "김향기", "김새론", "김환희", "김혜수", "김하늘", "김희선",
    "김고은", "송혜교", "박보영", "박신혜", "박민영", "박규영", "박지후",
    "배수지", "배두나", "손예진", "손나은", "손담비",
    "신세경", "신민아", "신혜선", "서예지", "서현진", "서지혜", "서현", "서신애",
    "김세정", "김소현", "김유정", "김혜윤", "노정의", "김다미", "전종서",
    "박은빈", "조이현", "박지후",
    "태연", "윤아", "티파니", "써니", "효연", "보아", "선미", "현아", "청하",
    "화사", "휘인", "솔라", "문별",
    # 남배우
    "정해인", "남주혁", "박서준", "박형식", "박보검",
    "이종석", "이민호", "김수현", "김우빈", "유아인", "변요한", "류준열",
    "조정석", "강하늘", "임시완", "박정민", "이제훈", "이동욱",
    "공유", "현빈", "정우성", "이정재", "황정민", "하정우", "마동석",
    "유연석", "김남길", "김재욱", "이준기", "지창욱", "김선호", "안효섭",
    "송강", "송중기", "송지효",
    "이재욱", "안보현", "이진욱", "엄기준", "주지훈", "윤계상", "이준혁",
    "김영대", "배인혁", "로몬", "나인우", "곽동연", "유승호", "여진구",
    "조승우", "조인성", "차태현", "장기용", "장동윤", "장동건",
    "정경호", "정일우", "정용화", "차승원", "차인표", "최민식",
    "설경구", "안성기", "이병헌", "고수", "권상우", "소지섭", "원빈",
    "류승룡", "유해진", "이성민", "조진웅",
    "김성철", "김동욱", "김강우", "김래원", "김상경", "김윤석",
    "박성웅", "박해수", "배성우", "진선규",
    # 힙합 / R&B
    "지코", "크러쉬", "딘", "헤이즈", "로꼬", "그레이", "사이먼도미닉",
    "박재범", "우원재", "비아이", "바비",
    # 예능 / MC
    "유재석", "강호동", "신동엽", "김구라", "박명수", "하하",
    "조세호", "양세형", "양세찬", "이수근", "김종민", "김종국",
    "지석진", "전소민", "장성규", "전현무", "박진영",
]

from src.config import Config, get_config
from src.fetcher import InstagramFetcher, validate_fetch_quality
from src.analyzer import InstagramAnalyzer
from src.sheets import SheetsReporter
from src.mailer import GmailSender
from src.visualization.charts import (
    create_hashtag_bar_chart,
    create_category_treemap,
    create_hashtag_bubble,
    create_viral_comparison,
    create_hashtag_wordcloud,
)

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
        margin-bottom: 0.8rem;
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
        margin: 1rem 0 !important;
        border-color: #333 !important;
    }
    
    /* 푸터 */
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.75rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #333;
    }

    /* info box 브랜드 컬러 */
    div[data-testid="stAlert"] {
        background-color: rgba(225, 48, 108, 0.08) !important;
        border-left-color: #E1306C !important;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown('<h1 class="main-header">📊 인스타그램 트렌드 리포터</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">인스타그램 릴스 트렌드 분석 → Google Sheets 리포트 → 이메일 전송</p>', unsafe_allow_html=True)

# 사이드바 - 설정
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")

    # 분석 기간 - 양자택일
    from datetime import date, timedelta
    period_mode = st.radio(
        "기간 설정 방식",
        ["최근 N일", "기간 직접 지정"],
        horizontal=True,
    )

    if period_mode == "최근 N일":
        days = st.slider("분석 기간 (일)", 1, 30, 7)
        start_date_val = None
        end_date_val = None
    else:
        date_cols = st.columns(2)
        with date_cols[0]:
            start_date_val = st.date_input(
                "시작일",
                value=date(2025, 12, 1),
                min_value=date(2024, 1, 1),
                max_value=date.today(),
            )
        with date_cols[1]:
            end_date_val = st.date_input(
                "종료일",
                value=date.today(),
                min_value=date(2024, 1, 1),
                max_value=date.today(),
            )
        # 기간 일수 계산 (limit 조정용)
        days = (end_date_val - start_date_val).days
        if days <= 0:
            st.error("종료일은 시작일보다 뒤여야 합니다.")
            st.stop()
        elif days > 30:
            st.info(f"📋 {days}일간 분석 → 계정당 수집량이 자동으로 늘어납니다.")

    # 콘텐츠 유형
    content_type = st.selectbox(
        "콘텐츠 유형",
        ["posts", "reels"],
        index=0,
        help="릴스: 짧은 동영상 (바이럴 분석에 추천) | 포스트: 이미지/캐러셀",
    )
    
    # Top N 설정
    top_hashtags = st.slider("Top 해시태그 개수", 10, 100, 50)
    top_viral = st.slider("Top 바이럴 개수", 3, 20, 7)

    # 제외 해시태그
    exclude_input = st.text_input(
        "제외 해시태그 (쉼표로 구분)",
        "제작지원, 광고, 행사초대",
        help="분석에서 제외할 해시태그. # 없이 쉼표로 구분",
    )
    _ui_exclude = [t.strip().lstrip("#") for t in exclude_input.split(",") if t.strip()]

    use_celeb_filter = st.checkbox(
        f"셀럽/인물 이름 자동 제외 ({len(_DEFAULT_EXCLUDE_CELEB)}개)",
        value=False,
        help="활성화하면 아이돌, 배우 등 인물 이름 해시태그를 자동 제외합니다. "
             "패션 매거진처럼 셀럽 태그가 트렌드 신호인 경우 OFF 권장.",
    )
    if use_celeb_filter:
        exclude_tags = list(set(_ui_exclude + _DEFAULT_EXCLUDE_CELEB))
    else:
        exclude_tags = _ui_exclude
    
    with st.expander("🔑 API 설정"):
        # 기존 토큰이 있으면 마스킹 표시
        _existing_token = ""
        try:
            _existing_token = st.secrets.get("APIFY_TOKEN", "") or ""
        except Exception:
            pass

        apify_token_input = st.text_input(
            "Apify API 토큰",
            value=_existing_token,
            type="password",
            help="Apify에서 발급받은 API 토큰. secrets.toml 또는 환경변수 대신 여기에 직접 입력할 수 있습니다.",
        )

    with st.expander("📧 이메일 설정"):
        send_email = st.checkbox("이메일로 리포트 전송", value=True)

        if send_email:
            email_input = st.text_area(
                "수신자 이메일 (줄바꿈으로 구분)",
                "dedurox@gmail.com\nkimdh@lfcorp.com",
                height=60,
            )
            recipients = [e.strip() for e in email_input.split("\n") if e.strip()]

# 메인 영역
col1, col2 = st.columns([3, 2], gap="medium")

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
        height=120,
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
run_button = st.button(
    "🚀 리포트 생성 시작",
    type="primary",
    use_container_width=True,
)

# 실행 로직
if run_button:
    try:
        # 설정 로드 및 오버라이드
        config = get_config()
        config.analysis.days = days
        config.analysis.content_type = content_type
        config.analysis.top_hashtags = top_hashtags
        config.analysis.top_viral = top_viral
        config.analysis.exclude_hashtags = exclude_tags

        # 기간 직접 지정 모드
        if start_date_val and end_date_val:
            config.analysis.start_date = start_date_val.strftime("%Y-%m-%d")
            config.analysis.end_date = end_date_val.strftime("%Y-%m-%d")
            # 긴 기간은 수집량 자동 증가
            if days > 14:
                config.analysis.limit_per_account = max(config.analysis.limit_per_account, min(days * 5, 500))
        else:
            config.analysis.start_date = None
            config.analysis.end_date = None

        # Apify 토큰 오버라이드 (UI 입력값 우선)
        if apify_token_input:
            config.apify_token = apify_token_input

        # 계정 업데이트
        from src.config import Account
        config.accounts = [Account(username=a, category="Fashion") for a in accounts]

        email_results = []

        with st.status("리포트 생성 중...", expanded=True) as status:
            # 1. 데이터 수집
            st.write("📥 인스타그램 데이터 수집 중...")
            fetcher = InstagramFetcher(config)
            data = fetcher.fetch_all()
            st.write(f"✅ {len(data['posts'])}개 콘텐츠 수집 완료")

            # 1-b. 데이터 품질 검증
            quality = validate_fetch_quality(data["posts"], len(accounts))
            if quality["issues"]:
                for issue in quality["issues"]:
                    st.write(f"⚠️ {issue}")
            if not quality["valid"]:
                status.update(label="데이터 품질 부족", state="error", expanded=True)
                st.error("데이터 품질이 너무 낮아 분석을 진행할 수 없습니다. 설정을 확인해주세요.")
                st.stop()

            # 2. 분석
            st.write("🔍 데이터 분석 중...")
            analyzer = InstagramAnalyzer(config)
            result = analyzer.analyze(data)
            st.write(f"✅ 해시태그 {len(result.top_hashtags)}개, 바이럴 {len(result.top_viral)}개 추출")

            # 3. Google Sheets 생성
            st.write("📊 Google Sheets 리포트 생성 중...")
            sheets_reporter = SheetsReporter(config)
            sheets_info = sheets_reporter.generate_report(result)
            st.write(f"✅ 스프레드시트 생성 완료")

            # 4. 이메일 전송
            if send_email and recipients:
                st.write(f"📧 이메일 전송 중... ({len(recipients)}명)")
                gmail_sender = GmailSender(config)
                email_results = gmail_sender.send_report(result, sheets_info, recipients)
                st.write(f"✅ 이메일 전송 완료")

            status.update(label="리포트 생성 완료!", state="complete", expanded=False)
        
        # 결과 표시
        st.success("🎉 리포트 생성 완료!")

        # 탭 기반 대시보드
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏷️ 해시태그 분석", "🔥 바이럴 콘텐츠", "💡 인사이트"])

        with tab1:
            # 메트릭 카드
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("분석 포스트", f"{result.total_posts}개")
            with col2:
                st.metric("Top 해시태그", f"{len(result.top_hashtags)}개")
            with col3:
                st.metric("Top 바이럴", f"{len(result.top_viral)}개")
            with col4:
                st.metric("인사이트", f"{len(result.insights)}개")

            st.markdown("---")

            # 워드클라우드
            if result.top_hashtags:
                st.markdown('<p class="section-header">☁️ 해시태그 워드클라우드</p>', unsafe_allow_html=True)
                wc_fig = create_hashtag_wordcloud(result.top_hashtags)
                if wc_fig:
                    st.pyplot(wc_fig)

            # 리포트 링크
            st.markdown("---")
            st.link_button("📎 Google Sheets에서 전체 리포트 보기 →", sheets_info['url'], use_container_width=True)

        with tab2:
            if result.top_hashtags:
                # 2컬럼: 바 차트 | 트리맵
                col1, col2 = st.columns(2)
                with col1:
                    bar_fig = create_hashtag_bar_chart(result.top_hashtags)
                    st.plotly_chart(bar_fig, use_container_width=True)
                with col2:
                    treemap_fig = create_category_treemap(result.top_hashtags)
                    st.plotly_chart(treemap_fig, use_container_width=True)

                # 버블 차트 (전체 폭)
                bubble_fig = create_hashtag_bubble(result.top_hashtags)
                st.plotly_chart(bubble_fig, use_container_width=True)

                # 데이터테이블 with progress column
                st.markdown('<p class="section-header">📋 전체 해시태그 데이터</p>', unsafe_allow_html=True)

                max_score = max(h.hot_score for h in result.top_hashtags) if result.top_hashtags else 1
                hashtag_df_data = [
                    {
                        "순위": i + 1,
                        "해시태그": h.tag,
                        "카테고리": h.category,
                        "빈도": h.count,
                        "평균인게이지": h.avg_engagement,
                        "핫스코어": h.hot_score,
                        "등급": h.grade,
                    }
                    for i, h in enumerate(result.top_hashtags)
                ]
                st.dataframe(
                    hashtag_df_data,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "핫스코어": st.column_config.ProgressColumn(
                            "핫스코어",
                            min_value=0,
                            max_value=max_score,
                            format="%.1f",
                        ),
                        "평균인게이지": st.column_config.NumberColumn(
                            "평균인게이지",
                            format="%d",
                        ),
                    },
                )
            else:
                st.info("해시태그 데이터가 없습니다.")

        with tab3:
            if result.top_viral:
                # 그룹드 바 차트
                viral_fig = create_viral_comparison(result.top_viral)
                st.plotly_chart(viral_fig, use_container_width=True)

                st.markdown("---")

                # 카드형 expander
                st.markdown('<p class="section-header">📱 콘텐츠 상세</p>', unsafe_allow_html=True)
                for v in result.top_viral:
                    with st.expander(f"#{v.rank} {v.username} - {v.topic[:40]}"):
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("좋아요", f"{v.likes:,}")
                        with m2:
                            st.metric("댓글", f"{v.comments:,}")
                        with m3:
                            st.metric("조회수", f"{v.views:,}")
                        with m4:
                            st.metric("인게이지먼트", f"{v.engagement:,.0f}")
                        if v.url:
                            st.link_button("인스타그램에서 보기 →", v.url)
            else:
                st.info("바이럴 콘텐츠 데이터가 없습니다.")

        with tab4:
            if result.insights:
                for ins in result.insights:
                    st.info(f"**{ins.number}. {ins.title}**\n\n{ins.description}\n\n🏷️ _{ins.keywords}_")
            else:
                st.info("인사이트가 없습니다.")

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
