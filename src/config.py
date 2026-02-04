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
class AnalysisConfig:
    days: int = 7
    content_type: str = "reels"
    limit_per_account: int = 50
    outlier_threshold: float = 2.0
    top_hashtags: int = 50
    top_viral: int = 7


@dataclass
class Config:
    apify_token: str
    accounts: List[Account]
    analysis: AnalysisConfig
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
        except:
            apify_token = os.environ.get("APIFY_TOKEN", "")
        
        accounts = [
            Account(username=a["username"], category=a.get("category", "general"))
            for a in DEFAULT_ACCOUNTS
        ]
        
        return cls(
            apify_token=apify_token,
            accounts=accounts,
            analysis=AnalysisConfig(),
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
        )
        
        google = data.get("google", {})
        
        return cls(
            apify_token=data.get("apify", {}).get("token", os.environ.get("APIFY_TOKEN", "")),
            accounts=accounts,
            analysis=analysis,
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
