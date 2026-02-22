"""
통합 인증 관리 모듈
- 로컬: keyring 사용
- 클라우드 (Streamlit): st.secrets 또는 환경변수 사용
"""
import os
from typing import Optional, Tuple
import yaml

# Streamlit 환경 감지
try:
    import streamlit as st
    IS_STREAMLIT = hasattr(st, 'secrets')
except ImportError:
    IS_STREAMLIT = False

# keyring (로컬 환경)
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False


def is_cloud_environment() -> bool:
    """클라우드 환경인지 확인"""
    # Streamlit Cloud 환경 변수
    if os.environ.get("STREAMLIT_SHARING_MODE"):
        return True
    # 환경변수로 토큰이 설정된 경우
    if os.environ.get("SHEETS_TOKEN") or os.environ.get("GMAIL_TOKEN"):
        return True
    # Streamlit secrets가 있는 경우
    if IS_STREAMLIT:
        try:
            if st.secrets.get("SHEETS_TOKEN") or st.secrets.get("GMAIL_TOKEN"):
                return True
        except:
            pass
    return False


def get_google_oauth_config() -> Tuple[str, str]:
    """Google OAuth client_id, client_secret 가져오기"""
    # 1. 환경변수 확인
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    # 2. Streamlit secrets 확인
    if not client_id and IS_STREAMLIT:
        try:
            client_id = st.secrets.get("GOOGLE_CLIENT_ID")
            client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET")
        except:
            pass
    
    # 3. 로컬 설정 파일 확인
    if not client_id:
        config_path = os.path.expanduser("~/.config/agent-skills/google.yaml")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = yaml.safe_load(f)
                client_id = config.get("oauth_client", {}).get("client_id")
                client_secret = config.get("oauth_client", {}).get("client_secret")
    
    return client_id, client_secret


def get_token(service: str) -> Optional[str]:
    """
    토큰 가져오기
    service: 'sheets' 또는 'gmail'
    """
    token_key = f"{service.upper()}_TOKEN"
    keyring_key = f"google-{service}-token-json"
    
    # 1. 환경변수 확인
    token = os.environ.get(token_key)
    if token:
        return token
    
    # 2. Streamlit secrets 확인
    if IS_STREAMLIT:
        try:
            token = st.secrets.get(token_key)
            if token:
                return token
        except:
            pass
    
    # 3. keyring 확인 (로컬)
    if HAS_KEYRING:
        try:
            token = keyring.get_password("agent-skills", keyring_key)
            if token:
                return token
        except:
            pass
    
    return None


def save_token(service: str, token_json: str):
    """
    토큰 저장 (로컬 환경에서만)
    """
    keyring_key = f"google-{service}-token-json"
    
    if HAS_KEYRING and not is_cloud_environment():
        try:
            keyring.set_password("agent-skills", keyring_key, token_json)
        except Exception as e:
            print(f"Warning: Failed to save token to keyring: {e}")


def get_apify_token() -> Optional[str]:
    """Apify 토큰 가져오기"""
    # 1. 환경변수
    token = os.environ.get("APIFY_TOKEN")
    if token:
        return token
    
    # 2. Streamlit secrets
    if IS_STREAMLIT:
        try:
            token = st.secrets.get("APIFY_TOKEN")
            if token:
                return token
        except:
            pass
    
    return None
