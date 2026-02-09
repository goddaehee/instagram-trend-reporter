"""Apify를 사용한 인스타그램 데이터 수집 모듈"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from apify_client import ApifyClient

from .config import get_config, Config
from .credentials import get_apify_token


class FetcherError(Exception):
    """스크래퍼 실행 중 복구 불가능한 오류"""
    pass


class InstagramFetcher:
    """인스타그램 데이터 수집기"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        # 환경변수/Secrets에서 토큰 우선 확인
        apify_token = get_apify_token() or self.config.apify_token
        if not apify_token:
            raise ValueError("APIFY_TOKEN이 설정되지 않았습니다.")
        self.client = ApifyClient(apify_token)
    
    def fetch_profiles(self, usernames: List[str]) -> Dict[str, Any]:
        """프로필 데이터 수집"""
        print(f"프로필 데이터 수집 중: {', '.join(usernames)}")

        scraper_cfg = self.config.scraper

        run_input = {
            "usernames": usernames,
        }

        try:
            run = self.client.actor("apify/instagram-profile-scraper").call(
                run_input=run_input,
                timeout_secs=scraper_cfg.timeout_secs,
                max_total_charge_usd=scraper_cfg.max_cost_usd,
            )
        except Exception as e:
            raise FetcherError(f"프로필 스크래퍼 실행 실패: {e}")
        
        profiles = {}
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            username = item.get("username", "").lower()
            profiles[username] = item
        
        print(f"  → {len(profiles)}개 프로필 수집 완료")
        return profiles
    
    # 30일 초과 기간은 자동 분할
    MAX_CHUNK_DAYS = 30

    def fetch_posts(
        self,
        usernames: List[str],
        days: int = 7,
        content_type: str = "reels",
        limit_per_account: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """포스트/릴스 데이터 수집

        start_date/end_date가 지정되면 해당 기간, 아니면 최근 days일 기준.
        30일 초과 기간은 자동으로 30일 단위로 분할 수집합니다.
        """
        if start_date and end_date:
            since_date = datetime.strptime(start_date, "%Y-%m-%d")
            until_date = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            since_date = datetime.now() - timedelta(days=days)
            until_date = datetime.now()

        total_days = (until_date - since_date).days

        # 30일 이하면 단일 실행
        if total_days <= self.MAX_CHUNK_DAYS:
            print(f"콘텐츠 수집 중: {content_type}, {total_days}일 ({since_date.strftime('%Y-%m-%d')} ~ {until_date.strftime('%Y-%m-%d')})")
            return self._fetch_posts_chunk(
                usernames, content_type, limit_per_account, since_date, until_date
            )

        # 30일 초과면 청크 분할
        chunks = []
        chunk_start = since_date
        while chunk_start < until_date:
            chunk_end = min(chunk_start + timedelta(days=self.MAX_CHUNK_DAYS), until_date)
            chunks.append((chunk_start, chunk_end))
            chunk_start = chunk_end + timedelta(seconds=1)

        print(f"콘텐츠 수집 중: {content_type}, {total_days}일 → {len(chunks)}회 분할 수집")

        all_posts = []
        failed_chunks = []
        for i, (c_start, c_end) in enumerate(chunks, 1):
            chunk_days = (c_end - c_start).days
            print(f"\n  📦 [{i}/{len(chunks)}] {c_start.strftime('%Y-%m-%d')} ~ {c_end.strftime('%Y-%m-%d')} ({chunk_days}일)")
            try:
                chunk_posts = self._fetch_posts_chunk(
                    usernames, content_type, limit_per_account, c_start, c_end
                )
                all_posts.extend(chunk_posts)
                print(f"  📦 [{i}/{len(chunks)}] 누적: {len(all_posts)}개")
            except FetcherError as e:
                failed_chunks.append((i, c_start, c_end, str(e)))
                print(f"  ⚠️ [{i}/{len(chunks)}] 청크 실패: {e}")

        if failed_chunks and not all_posts:
            raise FetcherError(
                f"모든 청크 수집 실패 ({len(failed_chunks)}/{len(chunks)}). "
                f"첫 오류: {failed_chunks[0][3]}"
            )
        if failed_chunks:
            print(f"\n  ⚠️ {len(failed_chunks)}/{len(chunks)} 청크 실패 (수집된 데이터로 계속 진행)")

        # 중복 제거 (URL 기준)
        seen_urls = set()
        unique_posts = []
        for post in all_posts:
            url = post.get("url", post.get("id", id(post)))
            if url not in seen_urls:
                seen_urls.add(url)
                unique_posts.append(post)

        if len(all_posts) != len(unique_posts):
            print(f"  → 중복 제거: {len(all_posts)}개 → {len(unique_posts)}개")

        print(f"\n✅ 전체 수집 완료: {len(unique_posts)}개 ({len(chunks)}회 분할)")
        return unique_posts

    def _fetch_posts_chunk(
        self,
        usernames: List[str],
        content_type: str,
        limit_per_account: int,
        since_date: datetime,
        until_date: datetime,
    ) -> List[Dict[str, Any]]:
        """단일 기간 포스트 수집 (내부 메서드)"""
        # 콘텐츠 타입에 따른 URL 생성
        direct_urls = []
        for username in usernames:
            if content_type == "reels":
                direct_urls.append(f"https://www.instagram.com/{username}/reels/")
            else:
                direct_urls.append(f"https://www.instagram.com/{username}/")

        scraper_cfg = self.config.scraper

        # 과거 기간 요청 시 limit 자동 증가
        # resultsLimit은 날짜 필터보다 먼저 적용되므로, 현재~since_date 사이
        # 포스트를 모두 포함할 만큼 충분히 높여야 함
        days_ago = (datetime.now() - since_date).days
        if days_ago > 14:
            adjusted_limit = max(limit_per_account, days_ago * 5)
            adjusted_limit = min(adjusted_limit, 500)  # 비용 상한
        else:
            adjusted_limit = limit_per_account

        run_input = {
            "directUrls": direct_urls,
            "resultsLimit": adjusted_limit,
            "resultsType": "posts" if content_type != "stories" else "stories",
            "searchType": "user",
            "onlyPostsNewerThan": since_date.strftime("%Y-%m-%d"),
            # NOTE: apify/instagram-scraper는 maxRequestRetries를 공식 input으로
            # 노출하지 않아 무시될 수 있음. 실질적 방어는 timeout_secs와 max_total_charge_usd.
            "maxRequestRetries": scraper_cfg.max_request_retries,
            "maxConcurrency": scraper_cfg.max_concurrency,
        }

        if adjusted_limit != limit_per_account:
            print(f"    ℹ️ 과거 기간({days_ago}일 전) → resultsLimit {limit_per_account} → {adjusted_limit} 자동 조정")

        # 동적 타임아웃: 기본 + 계정 수 비례
        timeout = scraper_cfg.timeout_secs + (len(usernames) * scraper_cfg.timeout_per_account_secs)
        timeout = min(timeout, 900)  # 최대 15분

        try:
            run = self.client.actor("apify/instagram-scraper").call(
                run_input=run_input,
                timeout_secs=timeout,
                max_total_charge_usd=scraper_cfg.max_cost_usd,
            )
        except Exception as e:
            raise FetcherError(f"Apify 스크래퍼 실행 실패: {e}")

        posts = []
        total_items = 0
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            total_items += 1
            # 날짜 필터링
            timestamp = item.get("timestamp")
            if timestamp:
                try:
                    post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    post_date_naive = post_date.replace(tzinfo=None)
                    if post_date_naive < since_date:
                        continue
                    if post_date_naive > until_date:
                        continue
                except (ValueError, TypeError):
                    pass

            posts.append(item)

        print(f"    → {len(posts)}개 콘텐츠 (전체 {total_items}개 중 기간 내 필터)")

        # Circuit Breaker: 수집 결과 검증
        min_threshold = self.config.scraper.min_results_threshold
        if total_items == 0:
            raise FetcherError(
                "수집 완전 실패: 스크래퍼에서 데이터를 가져오지 못했습니다. "
                "API 토큰 또는 계정명을 확인해주세요."
            )
        if total_items > 0 and len(posts) == 0:
            print("    ⚠️ 수집된 콘텐츠가 모두 지정 기간 밖입니다.")
        elif len(posts) < min_threshold:
            print(f"    ⚠️ 수집량이 최소 기준({min_threshold}개) 미만입니다 ({len(posts)}개).")

        return posts
    
    def fetch_all(self) -> Dict[str, Any]:
        """전체 데이터 수집 (프로필 + 포스트)"""
        usernames = [a.username for a in self.config.accounts]
        
        # 프로필 수집
        profiles = self.fetch_profiles(usernames)
        
        # 포스트 수집
        posts = self.fetch_posts(
            usernames=usernames,
            days=self.config.analysis.days,
            content_type=self.config.analysis.content_type,
            limit_per_account=self.config.analysis.limit_per_account,
            start_date=self.config.analysis.start_date,
            end_date=self.config.analysis.end_date,
        )
        
        return {
            "profiles": profiles,
            "posts": posts,
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "days": self.config.analysis.days,
                "content_type": self.config.analysis.content_type,
                "accounts": usernames,
                "total_posts": len(posts),
            }
        }


def validate_fetch_quality(posts: List[Dict[str, Any]], num_accounts: int) -> Dict[str, Any]:
    """수집 데이터 품질 검증"""
    total = len(posts)
    if total == 0:
        return {"valid": False, "issues": ["수집된 포스트 없음"], "stats": {}}

    with_caption = sum(1 for p in posts if p.get("caption"))
    with_engagement = sum(1 for p in posts if p.get("likesCount") or p.get("videoPlayCount"))

    stats = {
        "total_posts": total,
        "caption_rate": with_caption / total,
        "engagement_rate": with_engagement / total,
    }

    issues = []
    if total < num_accounts * 2:
        issues.append(f"포스트 부족: {total}개 (계정당 최소 2개 = {num_accounts * 2}개 기대)")
    if stats["caption_rate"] < 0.3:
        issues.append(f"캡션 비율 낮음: {stats['caption_rate']:.0%} (해시태그 분석 제한적)")
    if stats["engagement_rate"] < 0.5:
        issues.append(f"인게이지먼트 데이터 부족: {stats['engagement_rate']:.0%} (랭킹 신뢰도 낮음)")

    if issues:
        for issue in issues:
            print(f"  ⚠️ 데이터 품질: {issue}")

    return {
        "valid": total >= num_accounts and not issues,
        "issues": issues,
        "stats": stats,
    }


def fetch_instagram_data(config: Optional[Config] = None) -> Dict[str, Any]:
    """인스타그램 데이터 수집 (편의 함수)"""
    fetcher = InstagramFetcher(config)
    return fetcher.fetch_all()
