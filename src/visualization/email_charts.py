"""이메일용 차트 이미지 생성 모듈"""
import io
from typing import List

import matplotlib
matplotlib.use('Agg')  # Headless rendering
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from ..analyzer import HashtagStats

# 한글 폰트 설정
_KR_FONT = None
for _name in ['Apple SD Gothic Neo', 'NanumGothic', 'Malgun Gothic', 'Noto Sans CJK KR']:
    if any(_name.lower() in f.name.lower() for f in fm.fontManager.ttflist):
        _KR_FONT = _name
        break
if _KR_FONT:
    matplotlib.rcParams['font.family'] = _KR_FONT
    matplotlib.rcParams['axes.unicode_minus'] = False
from .colors import GRADE_COLORS, CATEGORY_COLORS


def _create_empty_png() -> bytes:
    """빈 1x1 흰색 PNG 생성"""
    fig, ax = plt.subplots(figsize=(1, 1))
    ax.set_facecolor('white')
    ax.axis('off')
    fig.patch.set_facecolor('white')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=72, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def create_email_hashtag_chart(hashtags: List[HashtagStats], top_n: int = 10) -> bytes:
    """
    해시태그 핫스코어 수평 막대 차트 생성

    Args:
        hashtags: 해시태그 통계 리스트
        top_n: 상위 N개 표시

    Returns:
        PNG 이미지 바이트
    """
    if not hashtags:
        return _create_empty_png()

    # 상위 N개 선택 (역순으로 표시하여 가장 높은 것이 위에)
    display_hashtags = hashtags[:top_n][::-1]

    tags = [h.tag for h in display_hashtags]
    scores = [h.hot_score for h in display_hashtags]

    # 등급별 색상 매핑
    def get_grade_color(grade: str) -> str:
        if "Hot" in grade:
            return GRADE_COLORS["hot"]["hex"]
        elif "Rising" in grade:
            return GRADE_COLORS["rising"]["hex"]
        return GRADE_COLORS["stable"]["hex"]

    colors = [get_grade_color(h.grade) for h in display_hashtags]

    # 차트 생성
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    bars = ax.barh(tags, scores, color=colors, height=0.6)

    # 스타일링
    ax.set_xlabel('Hot Score', fontsize=11, fontweight='bold', color='#333333')
    ax.set_title('Top 해시태그 by Hot Score', fontsize=14, fontweight='bold',
                 color='#333333', pad=15)

    # 값 레이블 추가
    for bar, score in zip(bars, scores):
        width = bar.get_width()
        ax.text(width + max(scores) * 0.02, bar.get_y() + bar.get_height()/2,
                f'{score:.1f}', va='center', ha='left', fontsize=9, color='#666666')

    # 그리드 최소화
    ax.xaxis.grid(True, linestyle='--', alpha=0.3, color='#cccccc')
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)

    # 테두리 제거
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')

    # tick 색상
    ax.tick_params(axis='both', colors='#333333')

    plt.tight_layout()

    # PNG로 저장
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def create_email_category_pie(hashtags: List[HashtagStats]) -> bytes:
    """
    카테고리 분포 도넛 파이 차트 생성

    Args:
        hashtags: 해시태그 통계 리스트

    Returns:
        PNG 이미지 바이트
    """
    if not hashtags:
        return _create_empty_png()

    # 카테고리별 집계
    category_counts = {}
    for h in hashtags:
        cat = h.category
        category_counts[cat] = category_counts.get(cat, 0) + 1

    if not category_counts:
        return _create_empty_png()

    # 카테고리 이름 매핑
    category_names = {
        "celeb": "셀럽/아이돌",
        "brand": "브랜드",
        "trend": "테크/트렌드",
        "item": "패션 아이템",
        "general": "일반"
    }

    labels = [category_names.get(cat, cat) for cat in category_counts.keys()]
    sizes = list(category_counts.values())
    colors = [CATEGORY_COLORS.get(cat, {"hex": "#9E9E9E"})["hex"]
              for cat in category_counts.keys()]

    # 차트 생성
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # 도넛 차트 (wedgeprops로 가운데 구멍)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops=dict(width=0.6, edgecolor='white', linewidth=2),
        textprops={'fontsize': 10, 'color': '#333333'},
        pctdistance=0.75
    )

    # 퍼센트 텍스트 스타일
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    ax.set_title('카테고리 분포', fontsize=14, fontweight='bold',
                 color='#333333', pad=15)

    # 동그라미 유지
    ax.axis('equal')

    plt.tight_layout()

    # PNG로 저장
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf.read()
