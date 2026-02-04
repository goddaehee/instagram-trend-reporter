"""Google Sheets 리포트 생성 모듈"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import yaml
import keyring
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import get_config, Config
from .analyzer import AnalysisResult


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsReporter:
    """Google Sheets 리포트 생성기"""
    
    # 부록: 용어설명 (고정)
    GLOSSARY = [
        ["용어", "영문", "설명", "예시"],
        ["인게이지먼트", "Engagement", "사용자가 콘텐츠와 상호작용한 총량. 좋아요, 댓글, 저장, 공유 등을 포함", "좋아요 1000 + 댓글 50 = 높은 인게이지먼트"],
        ["인게이지먼트율", "Engagement Rate", "팔로워 수 대비 인게이지먼트 비율. (인게이지먼트 ÷ 팔로워) × 100", "팔로워 10만, 좋아요 1만이면 10%"],
        ["조회수", "Views / Plays", "릴스/동영상이 재생된 횟수. 3초 이상 시청 시 1회로 카운트", "조회수 100만 = 100만 번 재생"],
        ["좋아요", "Likes", "사용자가 콘텐츠에 좋아요를 누른 횟수", "❤️ 버튼 클릭 횟수"],
        ["댓글", "Comments", "사용자가 남긴 댓글 수", "콘텐츠 하단 댓글 개수"],
        ["핫스코어", "Hot Score", "빈도 × (평균인게이지먼트^0.3). 높을수록 현재 트렌드에서 핫함", "빈도 3, 평균인게이지 10만 → 핫스코어 약 143"],
        ["빈도", "Frequency", "특정 해시태그가 분석 기간 내 포스트에 등장한 횟수", "7일간 #아이폰이 4개 포스트에 등장 → 빈도 4"],
        ["평균인게이지먼트", "Avg Engagement", "해당 해시태그가 포함된 포스트들의 평균 인게이지먼트", "4개 포스트의 인게이지먼트 합계 ÷ 4"],
        ["해시태그", "Hashtag", "#으로 시작하는 키워드. 콘텐츠 검색/분류에 사용", "#패션, #OOTD, #일상"],
        ["릴스", "Reels", "인스타그램의 짧은 동영상 콘텐츠 (최대 90초)", "15~60초 세로 동영상"],
        ["아웃라이어", "Outlier", "평균보다 훨씬 높은 성과를 낸 콘텐츠", "평균 조회수 1만인데 100만 달성"],
        ["바이럴", "Viral", "콘텐츠가 빠르게 확산되는 현상", "단기간 조회수 급상승"],
        ["등급", "Grade", "핫스코어 기준 분류: Hot(50+) / Rising(25~50) / Stable(25미만)", "🔥 Hot = 현재 가장 핫한 키워드"],
    ]
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.service = None
    
    def _get_credentials(self) -> Credentials:
        """Google 인증 정보 획득"""
        # 저장된 토큰 확인
        token_json = keyring.get_password("agent-skills", self.config.sheets_token_key)
        
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
                # OAuth 설정 로드
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
            
            # 토큰 저장
            keyring.set_password("agent-skills", self.config.sheets_token_key, creds.to_json())
        
        return creds
    
    def _get_service(self):
        """Sheets API 서비스 객체"""
        if self.service is None:
            creds = self._get_credentials()
            self.service = build("sheets", "v4", credentials=creds)
        return self.service
    
    def create_spreadsheet(self, title: str) -> str:
        """새 스프레드시트 생성"""
        service = self._get_service()
        
        spreadsheet = {
            "properties": {"title": title},
            "sheets": [
                {"properties": {"title": "Top50_해시태그"}},
                {"properties": {"title": "Top7_바이럴콘텐츠"}},
                {"properties": {"title": "인사이트"}},
                {"properties": {"title": "부록_용어설명"}},
                {"properties": {"title": "리포트정보"}},
            ]
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result["spreadsheetId"]
        print(f"스프레드시트 생성: {spreadsheet_id}")
        return spreadsheet_id
    
    def write_values(self, spreadsheet_id: str, range_name: str, values: list):
        """값 쓰기"""
        service = self._get_service()
        body = {"values": values}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()
    
    def generate_report(self, result: AnalysisResult) -> Dict[str, str]:
        """리포트 생성 및 반환"""
        # 스프레드시트 생성
        date_str = datetime.now().strftime("%Y-%m-%d")
        title = f"인스타그램_트렌드_리포트_{date_str}"
        spreadsheet_id = self.create_spreadsheet(title)
        
        # 1. Top50_해시태그
        hashtag_data = [["순위", "키워드", "카테고리", "빈도", "평균인게이지먼트", "핫스코어", "등급", "등급근거"]]
        for i, h in enumerate(result.top_hashtags, 1):
            hashtag_data.append([
                i, h.tag, h.category, h.count, h.avg_engagement, h.hot_score, h.grade, h.grade_reason
            ])
        self.write_values(spreadsheet_id, "Top50_해시태그!A1", hashtag_data)
        print(f"  → Top50_해시태그 시트 작성 완료 ({len(result.top_hashtags)}개)")
        
        # 2. Top7_바이럴콘텐츠
        viral_data = [["순위", "계정", "주제", "좋아요", "댓글", "조회수", "인게이지먼트", "URL"]]
        for v in result.top_viral:
            viral_data.append([
                v.rank, v.username, v.topic, v.likes, v.comments, v.views, v.engagement, v.url
            ])
        self.write_values(spreadsheet_id, "Top7_바이럴콘텐츠!A1", viral_data)
        print(f"  → Top7_바이럴콘텐츠 시트 작성 완료 ({len(result.top_viral)}개)")
        
        # 3. 인사이트
        insight_data = [["번호", "인사이트 제목", "상세 설명", "관련 키워드"]]
        for ins in result.insights:
            insight_data.append([ins.number, ins.title, ins.description, ins.keywords])
        self.write_values(spreadsheet_id, "인사이트!A1", insight_data)
        print(f"  → 인사이트 시트 작성 완료 ({len(result.insights)}개)")
        
        # 4. 부록_용어설명
        self.write_values(spreadsheet_id, "부록_용어설명!A1", self.GLOSSARY)
        print(f"  → 부록_용어설명 시트 작성 완료 ({len(self.GLOSSARY)-1}개 용어)")
        
        # 5. 리포트정보
        report_info = [
            ["항목", "내용"],
            ["리포트 제목", "인스타그램 트렌드 키워드 리포트"],
            ["수집일", date_str],
            ["분석 기간", result.analysis_period],
            ["분석 계정 수", f"{len(result.accounts)}개"],
            ["분석 계정", ", ".join([f"@{a}" for a in result.accounts])],
            ["총 분석 포스트", f"{result.total_posts}개"],
            ["추출 해시태그 수", f"{len(result.top_hashtags)}개"],
            ["", ""],
            ["핫스코어 공식", "빈도 × (평균인게이지먼트 ^ 0.3)"],
            ["인게이지먼트 공식", "좋아요 + (댓글 × 3) + (조회수 × 0.1)"],
        ]
        self.write_values(spreadsheet_id, "리포트정보!A1", report_info)
        print(f"  → 리포트정보 시트 작성 완료")
        
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        
        return {
            "spreadsheet_id": spreadsheet_id,
            "url": url,
            "title": title,
        }


def create_sheets_report(result: AnalysisResult, config: Optional[Config] = None) -> Dict[str, str]:
    """Google Sheets 리포트 생성 (편의 함수)"""
    reporter = SheetsReporter(config)
    return reporter.generate_report(result)
