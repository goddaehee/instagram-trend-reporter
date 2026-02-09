"""Plotly/Matplotlib 차트 생성 모듈 - Streamlit 대시보드용"""

from typing import List
from collections import Counter

import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm

from ..analyzer import HashtagStats, ViralContent

# 한글 폰트 설정
def _find_kr_font():
    """한글 폰트 이름과 파일 경로를 찾아 반환"""
    candidates = ['Apple SD Gothic Neo', 'NanumGothic', 'Malgun Gothic', 'Noto Sans CJK KR']
    for name in candidates:
        for f in fm.fontManager.ttflist:
            if name.lower() in f.name.lower():
                return name, f.fname

    # Streamlit Cloud 등 Linux에서 apt 설치 후 캐시 미갱신 대비
    fm._load_fontmanager(try_read_cache=False)
    for name in candidates:
        for f in fm.fontManager.ttflist:
            if name.lower() in f.name.lower():
                return name, f.fname

    return None, None

_KR_FONT, _KR_FONT_PATH = _find_kr_font()
if _KR_FONT:
    matplotlib.rcParams['font.family'] = _KR_FONT
    matplotlib.rcParams['axes.unicode_minus'] = False
from .colors import (
    INSTAGRAM_COLORS,
    GRADE_COLORS,
    CATEGORY_COLORS,
    PLOTLY_GRADE_COLORS,
    PLOTLY_CATEGORY_SEQUENCE,
)

# 공통 레이아웃 설정
_COMMON_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Pretendard, -apple-system, sans-serif", size=12),
    margin=dict(l=20, r=20, t=50, b=20),
)


def _empty_figure(message: str = "데이터가 없습니다") -> go.Figure:
    """빈 데이터용 플레이스홀더 Figure 생성"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="#9E9E9E"),
    )
    fig.update_layout(**_COMMON_LAYOUT, xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def create_hashtag_bar_chart(hashtags: List[HashtagStats], top_n: int = 15) -> go.Figure:
    """
    해시태그 핫스코어 수평 바 차트

    Args:
        hashtags: HashtagStats 리스트
        top_n: 상위 N개만 표시 (기본 15)

    Returns:
        Plotly Figure 객체
    """
    if not hashtags:
        return _empty_figure("해시태그 데이터가 없습니다")

    # 상위 N개, hot_score 기준 정렬 (이미 정렬되어 있지만 확실히)
    sorted_tags = sorted(hashtags, key=lambda x: x.hot_score, reverse=True)[:top_n]

    # 차트에서는 아래에서 위로 그려지므로 역순 정렬 (가장 높은 것이 맨 위)
    sorted_tags = sorted_tags[::-1]

    tags = [h.tag for h in sorted_tags]
    scores = [h.hot_score for h in sorted_tags]
    colors = [PLOTLY_GRADE_COLORS.get(h.grade, "#9E9E9E") for h in sorted_tags]

    fig = go.Figure(
        go.Bar(
            x=scores,
            y=tags,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{s:.1f}" for s in scores],
            textposition="inside",
            textfont=dict(color="white", size=11),
            hovertemplate="<b>%{y}</b><br>핫스코어: %{x:.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        **_COMMON_LAYOUT,
        title=dict(
            text="Top 해시태그 핫스코어 랭킹",
            font=dict(size=16, color=INSTAGRAM_COLORS["pink"]),
        ),
        xaxis=dict(
            title="핫스코어",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.3)",
            zeroline=False,
        ),
        yaxis=dict(title="", tickfont=dict(size=11)),
        height=max(400, len(sorted_tags) * 28),
    )

    return fig


def create_category_treemap(hashtags: List[HashtagStats]) -> go.Figure:
    """
    카테고리별 해시태그 분포 Treemap

    Args:
        hashtags: HashtagStats 리스트

    Returns:
        Plotly Figure 객체
    """
    if not hashtags:
        return _empty_figure("해시태그 데이터가 없습니다")

    # 카테고리별 카운트
    category_counts = Counter(h.category for h in hashtags)

    labels = []
    values = []
    colors = []
    parents = []

    for cat, count in category_counts.items():
        cat_info = CATEGORY_COLORS.get(cat, {"hex": "#9E9E9E", "name": cat})
        labels.append(f"{cat_info['name']}<br>({count}개)")
        values.append(count)
        colors.append(cat_info["hex"])
        parents.append("")

    fig = go.Figure(
        go.Treemap(
            labels=labels,
            values=values,
            parents=parents,
            marker=dict(colors=colors, line=dict(width=2, color="white")),
            textinfo="label",
            textfont=dict(size=14, color="white"),
            hovertemplate="<b>%{label}</b><br>해시태그 수: %{value}<extra></extra>",
        )
    )

    fig.update_layout(
        **_COMMON_LAYOUT,
        title=dict(
            text="카테고리별 해시태그 분포",
            font=dict(size=16, color=INSTAGRAM_COLORS["pink"]),
        ),
        height=400,
    )

    return fig


def create_hashtag_bubble(hashtags: List[HashtagStats]) -> go.Figure:
    """
    해시태그 빈도 vs 인게이지먼트 버블 차트

    Args:
        hashtags: HashtagStats 리스트

    Returns:
        Plotly Figure 객체
    """
    if not hashtags:
        return _empty_figure("해시태그 데이터가 없습니다")

    # 카테고리별로 그룹화
    category_groups = {}
    for h in hashtags:
        if h.category not in category_groups:
            category_groups[h.category] = []
        category_groups[h.category].append(h)

    fig = go.Figure()

    for category, items in category_groups.items():
        cat_info = CATEGORY_COLORS.get(category, {"hex": "#9E9E9E", "name": category})

        # 버블 크기 정규화 (hot_score 기준, 최소 10, 최대 60)
        max_score = max(h.hot_score for h in hashtags) if hashtags else 1
        sizes = [max(10, min(60, (h.hot_score / max_score) * 50 + 10)) for h in items]

        fig.add_trace(
            go.Scatter(
                x=[h.count for h in items],
                y=[h.avg_engagement for h in items],
                mode="markers",
                name=cat_info["name"],
                marker=dict(
                    size=sizes,
                    color=cat_info["hex"],
                    opacity=0.7,
                    line=dict(width=1, color="white"),
                ),
                text=[h.tag for h in items],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "빈도: %{x}회<br>"
                    "평균 인게이지먼트: %{y:,.0f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        **_COMMON_LAYOUT,
        title=dict(
            text="해시태그 빈도 vs 인게이지먼트",
            font=dict(size=16, color=INSTAGRAM_COLORS["pink"]),
        ),
        xaxis=dict(
            title="빈도 (등장 횟수)",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.3)",
            zeroline=False,
        ),
        yaxis=dict(
            title="평균 인게이지먼트",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.3)",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        height=500,
    )

    return fig


def create_viral_comparison(viral: List[ViralContent]) -> go.Figure:
    """
    바이럴 콘텐츠 성과 비교 그룹 바 차트

    Args:
        viral: ViralContent 리스트

    Returns:
        Plotly Figure 객체
    """
    if not viral:
        return _empty_figure("바이럴 콘텐츠 데이터가 없습니다")

    usernames = [f"#{v.rank} {v.username}" for v in viral]
    gradient = INSTAGRAM_COLORS["gradient"]

    fig = go.Figure()

    # 좋아요
    fig.add_trace(
        go.Bar(
            name="좋아요",
            x=usernames,
            y=[v.likes for v in viral],
            marker_color=gradient[0],
            hovertemplate="%{x}<br>좋아요: %{y:,}<extra></extra>",
        )
    )

    # 댓글
    fig.add_trace(
        go.Bar(
            name="댓글",
            x=usernames,
            y=[v.comments for v in viral],
            marker_color=gradient[1],
            hovertemplate="%{x}<br>댓글: %{y:,}<extra></extra>",
        )
    )

    # 조회수
    fig.add_trace(
        go.Bar(
            name="조회수",
            x=usernames,
            y=[v.views for v in viral],
            marker_color=gradient[2],
            hovertemplate="%{x}<br>조회수: %{y:,}<extra></extra>",
        )
    )

    fig.update_layout(
        **_COMMON_LAYOUT,
        title=dict(
            text="바이럴 콘텐츠 성과 비교",
            font=dict(size=16, color=INSTAGRAM_COLORS["pink"]),
        ),
        barmode="group",
        xaxis=dict(
            title="",
            tickangle=-45,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="수치",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.3)",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        height=450,
    )

    return fig


def create_hashtag_wordcloud(hashtags: List[HashtagStats]) -> matplotlib.figure.Figure:
    """
    해시태그 워드클라우드 (Matplotlib Figure)

    Args:
        hashtags: HashtagStats 리스트

    Returns:
        Matplotlib Figure 객체 (st.pyplot() 사용)
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    if not hashtags:
        ax.text(
            0.5,
            0.5,
            "해시태그 데이터가 없습니다",
            ha="center",
            va="center",
            fontsize=16,
            color="#9E9E9E",
        )
        ax.axis("off")
        fig.patch.set_alpha(0)
        return fig

    try:
        from wordcloud import WordCloud
    except ImportError:
        ax.text(
            0.5,
            0.5,
            "wordcloud 패키지가 필요합니다\npip install wordcloud",
            ha="center",
            va="center",
            fontsize=14,
            color="#9E9E9E",
        )
        ax.axis("off")
        fig.patch.set_alpha(0)
        return fig

    # hot_score 기준 가중치 딕셔너리
    word_weights = {h.tag.lstrip("#"): h.hot_score for h in hashtags}

    # Instagram 핑크 컬러맵 생성
    from matplotlib.colors import LinearSegmentedColormap

    pink_cmap = LinearSegmentedColormap.from_list(
        "instagram_pink",
        ["#FCE4EC", "#F48FB1", "#E1306C", "#AD1457"],
    )

    wc_kwargs = dict(
        width=1000,
        height=500,
        background_color=None,
        mode="RGBA",
        colormap=pink_cmap,
        prefer_horizontal=0.8,
        min_font_size=10,
        max_font_size=100,
    )
    if _KR_FONT_PATH:
        wc_kwargs["font_path"] = _KR_FONT_PATH

    wordcloud = WordCloud(**wc_kwargs).generate_from_frequencies(word_weights)

    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(
        "해시태그 워드클라우드",
        fontsize=14,
        color=INSTAGRAM_COLORS["pink"],
        pad=10,
    )

    fig.patch.set_alpha(0)
    plt.tight_layout()

    return fig
