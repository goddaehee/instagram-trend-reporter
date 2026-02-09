"""인스타그램 데이터 분석 모듈"""
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import statistics

from .config import get_config, Config


@dataclass
class HashtagStats:
    """해시태그 통계"""
    tag: str
    count: int
    total_engagement: float
    avg_engagement: float
    hot_score: float
    category: str
    grade: str
    grade_reason: str


@dataclass
class ViralContent:
    """바이럴 콘텐츠"""
    rank: int
    username: str
    topic: str
    likes: int
    comments: int
    views: int
    engagement: float
    url: str


@dataclass
class Insight:
    """인사이트"""
    number: int
    title: str
    description: str
    keywords: str


@dataclass
class AnalysisResult:
    """분석 결과"""
    total_posts: int
    analysis_period: str
    accounts: List[str]
    top_hashtags: List[HashtagStats]
    top_viral: List[ViralContent]
    insights: List[Insight]
    generated_at: str


class InstagramAnalyzer:
    """인스타그램 데이터 분석기"""
    
    # 카테고리 분류용 키워드
    CELEB_KEYWORDS = [
        "jennie", "jisoo", "rose", "lisa", "karina", "winter", "ningning", "giselle",
        "bts", "뷔", "지민", "태용", "nct", "stray", "아이브", "에스파", "블랙핑크",
        "제니", "지수", "로제", "닝닝", "카리나", "윈터", "라이즈", "원빈", "레이",
        "아이유", "뉴진스", "르세라핌", "세븐틴", "투바투"
    ]
    BRAND_KEYWORDS = [
        "샤넬", "디올", "구찌", "프라다", "루이비통", "마뗑킴", "디에디트", "올리브",
        "휠라", "나이키", "아디다스", "자라", "유니클로", "무신사"
    ]
    TREND_KEYWORDS = [
        "테크", "아이폰", "갤럭시", "iOS", "꿀팁", "업데이트", "AI", "폰", "앱",
        "틱톡", "숏폼", "릴스", "트렌드"
    ]
    ITEM_KEYWORDS = [
        "코트", "재킷", "아우터", "스카프", "링", "가방", "슈즈", "부츠", "원피스",
        "청바지", "니트", "후드", "맨투맨"
    ]
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
    
    @staticmethod
    def calc_engagement(post: Dict[str, Any]) -> float:
        """인게이지먼트 계산: 좋아요 + (댓글 × 3) + (조회수 × 0.1)"""
        likes = post.get("likesCount", 0) or 0
        comments = post.get("commentsCount", 0) or 0
        views = post.get("videoPlayCount", 0) or 0
        return likes + (comments * 3) + (views * 0.1)
    
    def categorize_hashtag(self, tag: str) -> str:
        """해시태그 카테고리 분류"""
        tag_lower = tag.lower()
        
        if any(kw in tag_lower or kw in tag for kw in self.CELEB_KEYWORDS):
            return "celeb"
        elif any(kw in tag for kw in self.BRAND_KEYWORDS):
            return "brand"
        elif any(kw in tag for kw in self.TREND_KEYWORDS):
            return "trend"
        elif any(kw in tag for kw in self.ITEM_KEYWORDS):
            return "item"
        return "general"
    
    def calc_grade(self, hot_score: float, count: int, avg_engagement: float) -> Tuple[str, str]:
        """등급 계산"""
        if hot_score >= 50:
            grade = "🔥 Hot"
            if count >= 3 and avg_engagement >= 100000:
                reason = "고빈도+고인게이지"
            elif avg_engagement >= 300000:
                reason = "초고인게이지 단발"
            elif count >= 5:
                reason = "고빈도"
            else:
                reason = "높은 핫스코어"
        elif hot_score >= 25:
            grade = "📈 Rising"
            reason = "상승세"
        else:
            grade = "⚪ Stable"
            reason = "안정적"
        return grade, reason
    
    def analyze_hashtags(self, posts: List[Dict[str, Any]]) -> List[HashtagStats]:
        """해시태그 분석 - Top N개 반환"""
        hashtag_data = defaultdict(lambda: {"count": 0, "total_engagement": 0})
        exclude_set = {t.lower() for t in self.config.analysis.exclude_hashtags}

        posts_with_caption = 0
        posts_with_hashtags = 0
        total_hashtags_found = 0
        excluded_count = 0
        excluded_tags_detail = defaultdict(int)

        for post in posts:
            caption = post.get("caption", "") or ""
            if caption.strip():
                posts_with_caption += 1
            engagement = self.calc_engagement(post)

            # 해시태그 추출 (대소문자 통합)
            hashtags = re.findall(r'#(\w+)', caption)
            if hashtags:
                posts_with_hashtags += 1
            total_hashtags_found += len(hashtags)
            for tag in hashtags:
                tag_lower = tag.lower()
                if tag_lower in exclude_set:
                    excluded_count += 1
                    excluded_tags_detail[tag_lower] += 1
                    continue
                hashtag_data[tag_lower]["count"] += 1
                hashtag_data[tag_lower]["total_engagement"] += engagement

        print(f"  📊 해시태그 진단: 전체 {len(posts)}개 포스트")
        print(f"     캡션 있음: {posts_with_caption}개 ({posts_with_caption*100//max(len(posts),1)}%)")
        print(f"     해시태그 포함: {posts_with_hashtags}개 ({posts_with_hashtags*100//max(len(posts),1)}%)")
        print(f"     해시태그 총 발견: {total_hashtags_found}개 → 제외 필터: {excluded_count}개 → 고유 태그: {len(hashtag_data)}개")
        if excluded_tags_detail:
            excluded_list = ", ".join(f"#{k}({v})" for k, v in sorted(excluded_tags_detail.items(), key=lambda x: x[1], reverse=True))
            print(f"     🚫 제외된 태그: {excluded_list}")
        
        # 핫스코어 계산 및 정렬
        result = []
        for tag, data in hashtag_data.items():
            avg_eng = data["total_engagement"] / data["count"] if data["count"] > 0 else 0
            hot_score = data["count"] * (avg_eng ** 0.3) if avg_eng > 0 else 0
            category = self.categorize_hashtag(tag)
            grade, reason = self.calc_grade(hot_score, data["count"], avg_eng)
            
            result.append(HashtagStats(
                tag=f"#{tag}",
                count=data["count"],
                total_engagement=data["total_engagement"],
                avg_engagement=int(avg_eng),
                hot_score=round(hot_score, 1),
                category=category,
                grade=grade,
                grade_reason=reason,
            ))
        
        # 핫스코어 기준 정렬
        result.sort(key=lambda x: x.hot_score, reverse=True)
        return result[:self.config.analysis.top_hashtags]
    
    def find_viral_content(self, posts: List[Dict[str, Any]]) -> List[ViralContent]:
        """바이럴 콘텐츠 찾기 - Top N개 반환"""
        posts_with_engagement = [
            (post, self.calc_engagement(post)) for post in posts
        ]
        posts_with_engagement.sort(key=lambda x: x[1], reverse=True)
        
        result = []
        for rank, (post, engagement) in enumerate(posts_with_engagement[:self.config.analysis.top_viral], 1):
            caption = (post.get("caption") or "")[:50]
            # 이모지 + 요약 주제 생성
            topic = self._generate_topic(caption, post)
            
            result.append(ViralContent(
                rank=rank,
                username=f"@{post.get('ownerUsername', 'N/A')}",
                topic=topic,
                likes=post.get("likesCount", 0) or 0,
                comments=post.get("commentsCount", 0) or 0,
                views=post.get("videoPlayCount", 0) or 0,
                engagement=int(engagement),
                url=post.get("url", ""),
            ))
        
        return result
    
    def _generate_topic(self, caption: str, post: Dict[str, Any]) -> str:
        """캡션에서 주제 추출"""
        # 간단한 키워드 기반 주제 생성
        caption_lower = caption.lower()
        
        if "아이폰" in caption or "iphone" in caption_lower or "ios" in caption_lower:
            return "📱 " + caption[:30]
        elif "패션" in caption or "코디" in caption or "옷" in caption:
            return "👗 " + caption[:30]
        elif any(kw in caption for kw in ["bts", "방탄", "블랙핑크", "에스파"]):
            return "🎵 " + caption[:30]
        elif "뷰티" in caption or "메이크업" in caption:
            return "💄 " + caption[:30]
        else:
            return "✨ " + caption[:30] if caption else "✨ 콘텐츠"
    
    def generate_insights(self, hashtags: List[HashtagStats], viral: List[ViralContent]) -> List[Insight]:
        """인사이트 자동 생성"""
        insights = []

        if not hashtags and not viral:
            insights.append(Insight(
                number=1,
                title="데이터 부족",
                description="수집된 데이터가 충분하지 않아 인사이트를 생성할 수 없습니다. 수집 기간이나 계정 수를 늘려보세요.",
                keywords="데이터 부족",
            ))
            return insights

        # 인사이트 1: Top 해시태그 분석
        category_names = {
            "celeb": "셀럽/아이돌",
            "brand": "브랜드",
            "trend": "테크/트렌드",
            "item": "패션 아이템",
            "general": "일반"
        }

        if hashtags:
            top_tags = [h.tag for h in hashtags[:5]]
            top_categories = [h.category for h in hashtags[:10]]
            dominant_category = max(set(top_categories), key=top_categories.count)

            insights.append(Insight(
                number=1,
                title=f"{category_names.get(dominant_category, '일반')} 콘텐츠 강세",
                description=f"상위 10개 해시태그 중 {category_names.get(dominant_category)} 관련이 다수. Top 해시태그: {', '.join(top_tags[:3])}",
                keywords=", ".join(top_tags[:4]),
            ))
        
        # 인사이트 1-b: 해시태그 없을 때 대체 인사이트
        if not hashtags:
            insights.append(Insight(
                number=1,
                title="해시태그 미사용 콘텐츠",
                description="수집된 콘텐츠에 해시태그가 포함되지 않았습니다. 해시태그 없는 릴스/포스트 위주로 수집된 것으로 보입니다.",
                keywords="해시태그 없음",
            ))

        # 인사이트 2: 바이럴 콘텐츠 분석
        if viral:
            top_viral = viral[0]
            insights.append(Insight(
                number=2,
                title=f"Top 바이럴: {top_viral.username}",
                description=f"조회수 {top_viral.views:,}회 달성. {top_viral.topic}",
                keywords=f"{top_viral.username}, 조회수 {top_viral.views:,}",
            ))
        
        # 인사이트 3: 계정별 성과
        account_counts = defaultdict(int)
        for v in viral:
            account_counts[v.username] += 1
        if account_counts:
            top_account = max(account_counts.items(), key=lambda x: x[1])
            insights.append(Insight(
                number=3,
                title=f"{top_account[0]} 독주",
                description=f"Top 7 바이럴 중 {top_account[1]}개가 {top_account[0]} 콘텐츠",
                keywords=top_account[0],
            ))
        
        # 인사이트 4: 셀럽 콘텐츠
        celeb_tags = [h for h in hashtags if h.category == "celeb"][:3]
        if celeb_tags:
            insights.append(Insight(
                number=4,
                title="K-pop 셀럽 = 트래픽 보증수표",
                description=f"셀럽 관련 해시태그가 높은 인게이지먼트 기록: {', '.join(t.tag for t in celeb_tags)}",
                keywords=", ".join(t.tag for t in celeb_tags),
            ))
        
        # 인사이트 5: 브랜드/광고
        brand_tags = [h for h in hashtags if h.category == "brand" or "광고" in h.tag or "제작지원" in h.tag][:3]
        if brand_tags:
            insights.append(Insight(
                number=5,
                title="브랜드 콜라보 활발",
                description=f"광고/협찬 콘텐츠가 상위권: {', '.join(t.tag for t in brand_tags)}",
                keywords=", ".join(t.tag for t in brand_tags),
            ))
        
        return insights[:5]  # 최대 5개
    
    def analyze(self, data: Dict[str, Any]) -> AnalysisResult:
        """전체 분석 실행"""
        posts = data.get("posts", [])
        metadata = data.get("metadata", {})

        print(f"분석 시작: {len(posts)}개 포스트")

        if not posts:
            print("  ⚠️ 수집된 포스트가 없습니다. 빈 결과를 반환합니다.")
            if self.config.analysis.start_date and self.config.analysis.end_date:
                period = f"{self.config.analysis.start_date} ~ {self.config.analysis.end_date}"
            else:
                from datetime import timedelta
                days = metadata.get("days", self.config.analysis.days)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                period = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
            return AnalysisResult(
                total_posts=0,
                analysis_period=period,
                accounts=metadata.get("accounts", []),
                top_hashtags=[],
                top_viral=[],
                insights=[Insight(
                    number=1,
                    title="데이터 수집 실패",
                    description="인스타그램에서 데이터를 수집하지 못했습니다. 네트워크 상태나 API 토큰을 확인해주세요.",
                    keywords="수집 실패",
                )],
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )

        # 해시태그 분석
        hashtags = self.analyze_hashtags(posts)
        print(f"  → Top {len(hashtags)} 해시태그 추출")

        # 바이럴 콘텐츠
        viral = self.find_viral_content(posts)
        print(f"  → Top {len(viral)} 바이럴 콘텐츠 추출")

        # 인사이트 생성
        insights = self.generate_insights(hashtags, viral)
        print(f"  → {len(insights)}개 인사이트 생성")

        # 분석 기간 문자열
        if self.config.analysis.start_date and self.config.analysis.end_date:
            period = f"{self.config.analysis.start_date} ~ {self.config.analysis.end_date}"
        else:
            from datetime import timedelta
            days = metadata.get("days", self.config.analysis.days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            period = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
        
        return AnalysisResult(
            total_posts=len(posts),
            analysis_period=period,
            accounts=metadata.get("accounts", []),
            top_hashtags=hashtags,
            top_viral=viral,
            insights=insights,
            generated_at=datetime.now().isoformat(),
        )


def analyze_instagram_data(data: Dict[str, Any], config: Optional[Config] = None) -> AnalysisResult:
    """인스타그램 데이터 분석 (편의 함수)"""
    analyzer = InstagramAnalyzer(config)
    return analyzer.analyze(data)
