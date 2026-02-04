"""Apify를 사용한 인스타그램 데이터 수집 모듈"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from apify_client import ApifyClient

from .config import get_config, Config
from .credentials import get_apify_token


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
        
        run_input = {
            "usernames": usernames,
        }
        
        run = self.client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
        
        profiles = {}
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            username = item.get("username", "").lower()
            profiles[username] = item
        
        print(f"  → {len(profiles)}개 프로필 수집 완료")
        return profiles
    
    def fetch_posts(
        self,
        usernames: List[str],
        days: int = 7,
        content_type: str = "reels",
        limit_per_account: int = 50,
    ) -> List[Dict[str, Any]]:
        """포스트/릴스 데이터 수집"""
        print(f"콘텐츠 수집 중: {content_type}, 최근 {days}일")
        print(f"  계정: {', '.join(usernames)}")
        
        since_date = datetime.now() - timedelta(days=days)
        
        # 콘텐츠 타입에 따른 URL 생성
        direct_urls = []
        for username in usernames:
            if content_type == "reels":
                direct_urls.append(f"https://www.instagram.com/{username}/reels/")
            else:
                direct_urls.append(f"https://www.instagram.com/{username}/")
        
        run_input = {
            "directUrls": direct_urls,
            "resultsLimit": limit_per_account,
            "resultsType": "posts" if content_type != "stories" else "stories",
            "searchType": "user",
        }
        
        run = self.client.actor("apify/instagram-scraper").call(run_input=run_input)
        
        posts = []
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            # 날짜 필터링
            timestamp = item.get("timestamp")
            if timestamp:
                try:
                    post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if post_date.replace(tzinfo=None) < since_date:
                        continue
                except (ValueError, TypeError):
                    pass
            
            posts.append(item)
        
        print(f"  → {len(posts)}개 콘텐츠 수집 완료")
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


def fetch_instagram_data(config: Optional[Config] = None) -> Dict[str, Any]:
    """인스타그램 데이터 수집 (편의 함수)"""
    fetcher = InstagramFetcher(config)
    return fetcher.fetch_all()
