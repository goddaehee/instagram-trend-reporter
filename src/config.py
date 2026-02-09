"""설정 관리 모듈"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# 기본 계정 목록 (Streamlit Cloud용)
DEFAULT_ACCOUNTS = [
    {"username": "dip_magazine", "category": "Fashion"},
    {"username": "the_edit.co.kr", "category": "Fashion"},
    {"username": "on_fleekkk", "category": "Fashion"},
    {"username": "fashionandstyle.official", "category": "Fashion"},
    {"username": "luxmag.kr", "category": "Fashion"},
    {"username": "histofit", "category": "Fashion"},
]

DEFAULT_EMAIL_RECIPIENTS = [
    "dedurox@gmail.com",
    "kimdh@lfcorp.com",
]


@dataclass
class Account:
    username: str
    category: str = "general"


@dataclass
class ScraperConfig:
    """스크래퍼 방어 설정"""
    max_request_retries: int = 3        # 요청당 재시도 (Apify 기본값 30 → 3으로 제한)
    max_concurrency: int = 5            # 동시 요청 수 (rate limiting 방지)
    timeout_secs: int = 300             # 액터 실행 타임아웃 (5분)
    timeout_per_account_secs: int = 60  # 계정당 추가 타임아웃
    max_cost_usd: float = 2.0           # 실행당 비용 상한선 ($)
    min_results_threshold: int = 3      # 최소 결과 수 (이하면 경고)


@dataclass
class AnalysisConfig:
    days: int = 7
    content_type: str = "reels"
    limit_per_account: int = 50
    outlier_threshold: float = 2.0
    top_hashtags: int = 50
    top_viral: int = 7
    start_date: Optional[str] = None  # "YYYY-MM-DD" 형식, 직접 기간 지정 시
    end_date: Optional[str] = None    # "YYYY-MM-DD" 형식, 직접 기간 지정 시
    exclude_hashtags: List[str] = field(default_factory=list)


@dataclass
class Config:
    apify_token: str
    accounts: List[Account]
    analysis: AnalysisConfig
    scraper: ScraperConfig
    email_recipients: List[str]
    google_config_path: str
    gmail_token_key: str
    sheets_token_key: str
    
    @classmethod
    def load_from_secrets(cls) -> "Config":
        """Streamlit secrets에서 설정 로드 (클라우드 환경용)"""
        try:
            import streamlit as st
            apify_token = st.secrets.get("APIFY_TOKEN", os.environ.get("APIFY_TOKEN", ""))
        except Exception:
            apify_token = os.environ.get("APIFY_TOKEN", "")
        
        accounts = [
            Account(username=a["username"], category=a.get("category", "general"))
            for a in DEFAULT_ACCOUNTS
        ]
        
        return cls(
            apify_token=apify_token,
            accounts=accounts,
            analysis=AnalysisConfig(),
            scraper=ScraperConfig(),
            email_recipients=DEFAULT_EMAIL_RECIPIENTS,
            google_config_path="",
            gmail_token_key="gmail-token-json",
            sheets_token_key="google-sheets-token-json",
        )
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """설정 파일 로드 (파일 없으면 secrets에서 로드)"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        # 파일이 없으면 Streamlit secrets에서 로드
        if not Path(config_path).exists():
            return cls.load_from_secrets()
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        accounts = [
            Account(username=a["username"], category=a.get("category", "general"))
            for a in data.get("accounts", [])
        ]
        
        analysis_data = data.get("analysis", {})
        analysis = AnalysisConfig(
            days=analysis_data.get("days", 7),
            content_type=analysis_data.get("content_type", "reels"),
            limit_per_account=analysis_data.get("limit_per_account", 50),
            outlier_threshold=analysis_data.get("outlier_threshold", 2.0),
            top_hashtags=analysis_data.get("top_hashtags", 50),
            top_viral=analysis_data.get("top_viral", 7),
            start_date=analysis_data.get("start_date"),
            end_date=analysis_data.get("end_date"),
            exclude_hashtags=analysis_data.get("exclude_hashtags", []),
        )
        
        google = data.get("google", {})
        
        scraper_data = data.get("scraper", {})
        scraper = ScraperConfig(
            max_request_retries=scraper_data.get("max_request_retries", 3),
            max_concurrency=scraper_data.get("max_concurrency", 5),
            timeout_secs=scraper_data.get("timeout_secs", 300),
            timeout_per_account_secs=scraper_data.get("timeout_per_account_secs", 60),
            max_cost_usd=scraper_data.get("max_cost_usd", 2.0),
            min_results_threshold=scraper_data.get("min_results_threshold", 3),
        )

        return cls(
            apify_token=data.get("apify", {}).get("token", os.environ.get("APIFY_TOKEN", "")),
            accounts=accounts,
            analysis=analysis,
            scraper=scraper,
            email_recipients=data.get("email", {}).get("recipients", []),
            google_config_path=os.path.expanduser(google.get("config_path", "~/.config/agent-skills/google.yaml")),
            gmail_token_key=google.get("gmail_token_key", "gmail-token-json"),
            sheets_token_key=google.get("sheets_token_key", "google-sheets-token-json"),
        )


# 싱글톤 인스턴스
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """설정 가져오기 (싱글톤)"""
    global _config
    if _config is None:
        _config = Config.load(config_path)
    return _config
