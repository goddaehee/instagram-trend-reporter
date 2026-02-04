"""Gmail 이메일 전송 모듈"""
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
import yaml
import keyring
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import get_config, Config
from .analyzer import AnalysisResult


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailSender:
    """Gmail 이메일 전송기"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.service = None
    
    def _get_credentials(self) -> Credentials:
        """Gmail 인증 정보 획득"""
        token_json = keyring.get_password("agent-skills", self.config.gmail_token_key)
        
        creds = None
        if token_json:
            try:
                creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
            except Exception:
                pass
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                with open(self.config.google_config_path) as f:
                    google_config = yaml.safe_load(f)
                
                client_config = {
                    "installed": {
                        "client_id": google_config["oauth_client"]["client_id"],
                        "client_secret": google_config["oauth_client"]["client_secret"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                creds = flow.run_local_server(port=0)
            
            keyring.set_password("agent-skills", self.config.gmail_token_key, creds.to_json())
        
        return creds
    
    def _get_service(self):
        """Gmail API 서비스 객체"""
        if self.service is None:
            creds = self._get_credentials()
            self.service = build("gmail", "v1", credentials=creds)
        return self.service
    
    def create_report_email(
        self,
        result: AnalysisResult,
        sheets_info: Dict[str, str],
    ) -> str:
        """리포트 이메일 본문 생성"""
        # Top 3 해시태그
        top_tags = ", ".join([h.tag for h in result.top_hashtags[:3]])
        
        # Top 바이럴
        top_viral_text = ""
        if result.top_viral:
            v = result.top_viral[0]
            top_viral_text = f"{v.username} - {v.topic} (조회수 {v.views:,})"
        
        # 인사이트 요약
        insights_text = ""
        for ins in result.insights[:3]:
            insights_text += f"  • {ins.title}\n"
        
        body = f"""안녕하세요!

📊 인스타그램 주간 트렌드 리포트가 생성되었습니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 분석 기간: {result.analysis_period}
📝 분석 콘텐츠: {result.total_posts}개

🔥 이번 주 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▸ Top 해시태그: {top_tags}
▸ Top 바이럴: {top_viral_text}

💡 주요 인사이트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{insights_text}
📎 리포트 링크
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{sheets_info['url']}

(시트 구성: Top50_해시태그 / Top7_바이럴콘텐츠 / 인사이트 / 부록_용어설명 / 리포트정보)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
갓댐봇 🐻
"""
        return body
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """이메일 전송"""
        service = self._get_service()
        
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        result = service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()
        
        return result
    
    def send_report(
        self,
        result: AnalysisResult,
        sheets_info: Dict[str, str],
        recipients: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """리포트 이메일 전송"""
        if recipients is None:
            recipients = self.config.email_recipients
        
        subject = f"📊 인스타그램 주간 트렌드 리포트 ({result.analysis_period.split('~')[1].strip()})"
        body = self.create_report_email(result, sheets_info)
        
        results = []
        for recipient in recipients:
            try:
                send_result = self.send_email(recipient, subject, body)
                print(f"  ✅ 이메일 전송 완료: {recipient}")
                results.append({"to": recipient, "success": True, "message_id": send_result.get("id")})
            except Exception as e:
                print(f"  ❌ 이메일 전송 실패: {recipient} - {e}")
                results.append({"to": recipient, "success": False, "error": str(e)})
        
        return results


def send_report_email(
    result: AnalysisResult,
    sheets_info: Dict[str, str],
    recipients: Optional[List[str]] = None,
    config: Optional[Config] = None,
) -> List[Dict[str, Any]]:
    """리포트 이메일 전송 (편의 함수)"""
    sender = GmailSender(config)
    return sender.send_report(result, sheets_info, recipients)
