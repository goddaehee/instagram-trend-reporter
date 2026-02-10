"""Google Sheets 리포트 생성 모듈"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import yaml
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import get_config, Config
from .analyzer import AnalysisResult
from .credentials import get_token, save_token, get_google_oauth_config, is_cloud_environment
from .visualization.colors import (
    SHEETS_HEADER_BG, SHEETS_HEADER_FG, SHEETS_BORDER_COLOR,
    SHEETS_GRADE_BG, SHEETS_GRADIENT, SHEETS_TAB_COLORS, CATEGORY_COLORS
)


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",  # 권한 설정용
]


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
        self._sheet_ids = {}
        self._hashtag_tab = "Top50_해시태그"  # Will be set dynamically in generate_report
        self._viral_tab = "Top7_바이럴콘텐츠"  # Will be set dynamically in generate_report
    
    def _get_credentials(self) -> Credentials:
        """Google 인증 정보 획득"""
        # 저장된 토큰 확인
        token_json = get_token("sheets")
        
        creds = None
        if token_json:
            try:
                creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
            except Exception:
                pass
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # 갱신된 토큰 저장
                save_token("sheets", creds.to_json())
            else:
                # 클라우드 환경에서는 토큰이 필수
                if is_cloud_environment():
                    raise ValueError("SHEETS_TOKEN이 설정되지 않았습니다. Streamlit Secrets에 토큰을 추가하세요.")
                
                # OAuth 설정 로드
                client_id, client_secret = get_google_oauth_config()
                if not client_id:
                    raise ValueError("Google OAuth 설정을 찾을 수 없습니다.")
                
                client_config = {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # 토큰 저장
                save_token("sheets", creds.to_json())
        
        return creds
    
    def _get_service(self):
        """Sheets API 서비스 객체"""
        if self.service is None:
            creds = self._get_credentials()
            self.service = build("sheets", "v4", credentials=creds)
        return self.service
    
    def _get_drive_service(self):
        """Drive API 서비스 객체 (권한 설정용)"""
        creds = self._get_credentials()
        return build("drive", "v3", credentials=creds)
    
    def set_public_permission(self, spreadsheet_id: str):
        """스프레드시트를 '링크가 있는 모든 사용자 > 뷰어'로 설정"""
        drive_service = self._get_drive_service()
        
        permission = {
            "type": "anyone",
            "role": "reader",
        }
        
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            fields="id",
        ).execute()
        
        print("  → 공개 권한 설정 완료 (링크가 있는 모든 사용자 > 뷰어)")
    
    def create_spreadsheet(self, title: str, hashtag_tab: Optional[str] = None, viral_tab: Optional[str] = None) -> str:
        """새 스프레드시트 생성"""
        service = self._get_service()

        # Use provided tab names or fall back to instance variables
        hashtag_tab_name = hashtag_tab or self._hashtag_tab
        viral_tab_name = viral_tab or self._viral_tab

        spreadsheet = {
            "properties": {"title": title},
            "sheets": [
                {"properties": {"title": hashtag_tab_name}},
                {"properties": {"title": viral_tab_name}},
                {"properties": {"title": "인사이트"}},
                {"properties": {"title": "부록_용어설명"}},
                {"properties": {"title": "리포트정보"}},
            ]
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result["spreadsheetId"]

        # Store sheet IDs for batchUpdate operations
        self._sheet_ids = {}
        for sheet in result.get("sheets", []):
            title = sheet["properties"]["title"]
            sheet_id = sheet["properties"]["sheetId"]
            self._sheet_ids[title] = sheet_id

        print(f"스프레드시트 생성: {spreadsheet_id}")
        return spreadsheet_id
    
    def write_values(self, spreadsheet_id: str, range_name: str, values: list):
        """값 쓰기"""
        service = self._get_service()
        body = {"values": values}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()

    def _build_formatting_requests(self, result: AnalysisResult) -> list:
        """Build batchUpdate requests for formatting, conditional formatting, and charts"""
        requests = []

        # Sheet name to tab color mapping
        tab_color_map = {
            self._hashtag_tab: SHEETS_TAB_COLORS["hashtag"],
            self._viral_tab: SHEETS_TAB_COLORS["viral"],
            "인사이트": SHEETS_TAB_COLORS["insight"],
            "부록_용어설명": SHEETS_TAB_COLORS["glossary"],
            "리포트정보": SHEETS_TAB_COLORS["info"],
        }

        # Data row counts for each sheet (including header)
        row_counts = {
            self._hashtag_tab: len(result.top_hashtags) + 1,
            self._viral_tab: len(result.top_viral) + 1,
            "인사이트": len(result.insights) + 1,
            "부록_용어설명": len(self.GLOSSARY),
            "리포트정보": 11,
        }

        # Column counts for each sheet
        col_counts = {
            self._hashtag_tab: 8,
            self._viral_tab: 8,
            "인사이트": 4,
            "부록_용어설명": 4,
            "리포트정보": 2,
        }

        for sheet_name, sheet_id in self._sheet_ids.items():
            # a) Tab colors
            if sheet_name in tab_color_map:
                requests.append({
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "tabColor": tab_color_map[sheet_name],
                        },
                        "fields": "tabColor",
                    }
                })

            # b) Frozen header rows
            requests.append({
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": 1},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            })

            # c) Header formatting (row 0)
            col_count = col_counts.get(sheet_name, 8)
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": col_count,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": SHEETS_HEADER_BG,
                            "textFormat": {
                                "foregroundColor": SHEETS_HEADER_FG,
                                "bold": True,
                            },
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }
            })

            # d) Borders on all data cells
            row_count = row_counts.get(sheet_name, 10)
            requests.append({
                "updateBorders": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": row_count,
                        "startColumnIndex": 0,
                        "endColumnIndex": col_count,
                    },
                    "top": {"style": "SOLID", "color": SHEETS_BORDER_COLOR},
                    "bottom": {"style": "SOLID", "color": SHEETS_BORDER_COLOR},
                    "left": {"style": "SOLID", "color": SHEETS_BORDER_COLOR},
                    "right": {"style": "SOLID", "color": SHEETS_BORDER_COLOR},
                    "innerHorizontal": {"style": "SOLID", "color": SHEETS_BORDER_COLOR},
                    "innerVertical": {"style": "SOLID", "color": SHEETS_BORDER_COLOR},
                }
            })

            # e) Auto-resize columns
            requests.append({
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": col_count,
                    }
                }
            })

        # f) Number formatting for large numbers
        hashtag_sheet_id = self._sheet_ids.get(self._hashtag_tab)
        viral_sheet_id = self._sheet_ids.get(self._viral_tab)

        if hashtag_sheet_id is not None:
            hashtag_row_count = len(result.top_hashtags) + 1
            # 평균인게이지먼트 (E, index 4) - comma format
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": hashtag_sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": hashtag_row_count,
                        "startColumnIndex": 4,
                        "endColumnIndex": 5,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            })
            # 핫스코어 (F, index 5) - one decimal
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": hashtag_sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": hashtag_row_count,
                        "startColumnIndex": 5,
                        "endColumnIndex": 6,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "NUMBER", "pattern": "#,##0.0"}
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            })

        if viral_sheet_id is not None:
            viral_row_count = len(result.top_viral) + 1
            # 좋아요(D,3), 댓글(E,4), 조회수(F,5), 인게이지먼트(G,6) - comma format
            for col_idx in [3, 4, 5, 6]:
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": viral_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": viral_row_count,
                            "startColumnIndex": col_idx,
                            "endColumnIndex": col_idx + 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat",
                    }
                })

        # g) Conditional formatting on hashtag sheet
        if hashtag_sheet_id is not None:
            hashtag_row_count = len(result.top_hashtags) + 1

            # Grade column (G, index 6) - Hot
            requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": hashtag_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": hashtag_row_count,
                            "startColumnIndex": 6,
                            "endColumnIndex": 7,
                        }],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_CONTAINS",
                                "values": [{"userEnteredValue": "Hot"}],
                            },
                            "format": {"backgroundColor": SHEETS_GRADE_BG["hot"]},
                        },
                    },
                    "index": 0,
                }
            })

            # Grade column (G, index 6) - Rising
            requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": hashtag_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": hashtag_row_count,
                            "startColumnIndex": 6,
                            "endColumnIndex": 7,
                        }],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_CONTAINS",
                                "values": [{"userEnteredValue": "Rising"}],
                            },
                            "format": {"backgroundColor": SHEETS_GRADE_BG["rising"]},
                        },
                    },
                    "index": 1,
                }
            })

            # Hot score column (F, index 5) - Gradient
            requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": hashtag_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": hashtag_row_count,
                            "startColumnIndex": 5,
                            "endColumnIndex": 6,
                        }],
                        "gradientRule": {
                            "minpoint": {
                                "color": SHEETS_GRADIENT["min"],
                                "type": "MIN",
                            },
                            "maxpoint": {
                                "color": SHEETS_GRADIENT["max"],
                                "type": "MAX",
                            },
                        },
                    },
                    "index": 2,
                }
            })

        # g) Charts
        # Bar chart for top 10 hashtags by hot_score on hashtag sheet
        if hashtag_sheet_id is not None:
            requests.append({
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "Top 10 핫스코어 해시태그",
                            "basicChart": {
                                "chartType": "BAR",
                                "legendPosition": "NO_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "핫스코어"},
                                    {"position": "LEFT_AXIS", "title": "해시태그"},
                                ],
                                "domains": [{
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": hashtag_sheet_id,
                                                "startRowIndex": 1,
                                                "endRowIndex": 11,
                                                "startColumnIndex": 1,
                                                "endColumnIndex": 2,
                                            }]
                                        }
                                    }
                                }],
                                "series": [{
                                    "series": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": hashtag_sheet_id,
                                                "startRowIndex": 1,
                                                "endRowIndex": 11,
                                                "startColumnIndex": 5,
                                                "endColumnIndex": 6,
                                            }]
                                        }
                                    },
                                    "color": SHEETS_HEADER_BG,
                                }],
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": hashtag_sheet_id,
                                    "rowIndex": 1,
                                    "columnIndex": 9,
                                },
                                "widthPixels": 600,
                                "heightPixels": 400,
                            }
                        },
                    }
                }
            })

            # Pie chart (donut) for category distribution on hashtag sheet
            # Category summary data is written at J16, so data starts at row 16 (index 16)
            category_count = len(set(h.category for h in result.top_hashtags))
            requests.append({
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "카테고리별 분포",
                            "pieChart": {
                                "legendPosition": "RIGHT_LEGEND",
                                "pieHole": 0.4,
                                "domain": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": hashtag_sheet_id,
                                            "startRowIndex": 16,
                                            "endRowIndex": 17 + category_count,
                                            "startColumnIndex": 9,
                                            "endColumnIndex": 10,
                                        }]
                                    }
                                },
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": hashtag_sheet_id,
                                            "startRowIndex": 16,
                                            "endRowIndex": 17 + category_count,
                                            "startColumnIndex": 10,
                                            "endColumnIndex": 11,
                                        }]
                                    }
                                },
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": hashtag_sheet_id,
                                    "rowIndex": 17,
                                    "columnIndex": 9,
                                },
                                "widthPixels": 500,
                                "heightPixels": 400,
                            }
                        },
                    }
                }
            })

        # Column chart for viral content on viral sheet
        if viral_sheet_id is not None:
            viral_row_count = len(result.top_viral) + 1
            requests.append({
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "바이럴 콘텐츠 비교 (좋아요/댓글/조회수)",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "계정"},
                                    {"position": "LEFT_AXIS", "title": "수치"},
                                ],
                                "domains": [{
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": viral_sheet_id,
                                                "startRowIndex": 1,
                                                "endRowIndex": viral_row_count,
                                                "startColumnIndex": 1,
                                                "endColumnIndex": 2,
                                            }]
                                        }
                                    }
                                }],
                                "series": [
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [{
                                                    "sheetId": viral_sheet_id,
                                                    "startRowIndex": 1,
                                                    "endRowIndex": viral_row_count,
                                                    "startColumnIndex": 3,
                                                    "endColumnIndex": 4,
                                                }]
                                            }
                                        },
                                        "color": SHEETS_TAB_COLORS["hashtag"],
                                    },
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [{
                                                    "sheetId": viral_sheet_id,
                                                    "startRowIndex": 1,
                                                    "endRowIndex": viral_row_count,
                                                    "startColumnIndex": 4,
                                                    "endColumnIndex": 5,
                                                }]
                                            }
                                        },
                                        "color": SHEETS_TAB_COLORS["viral"],
                                    },
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [{
                                                    "sheetId": viral_sheet_id,
                                                    "startRowIndex": 1,
                                                    "endRowIndex": viral_row_count,
                                                    "startColumnIndex": 5,
                                                    "endColumnIndex": 6,
                                                }]
                                            }
                                        },
                                        "color": SHEETS_TAB_COLORS["insight"],
                                    },
                                ],
                                "headerCount": 1,
                            },
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": viral_sheet_id,
                                    "rowIndex": 11,
                                    "columnIndex": 0,
                                },
                                "widthPixels": 800,
                                "heightPixels": 400,
                            }
                        },
                    }
                }
            })

        return requests

    def generate_report(self, result: AnalysisResult) -> Dict[str, str]:
        """리포트 생성 및 반환"""
        # Set dynamic tab names based on actual data counts
        self._hashtag_tab = f"Top{len(result.top_hashtags)}_해시태그"
        self._viral_tab = f"Top{len(result.top_viral)}_바이럴콘텐츠"

        # 스프레드시트 생성
        date_str = datetime.now().strftime("%Y-%m-%d")
        title = f"인스타그램_트렌드_리포트_{date_str}"
        spreadsheet_id = self.create_spreadsheet(title, self._hashtag_tab, self._viral_tab)
        
        # 1. Hashtag sheet (dynamic name based on data count)
        hashtag_data = [["순위", "키워드", "카테고리", "빈도", "평균인게이지먼트", "핫스코어", "등급", "등급근거"]]
        for i, h in enumerate(result.top_hashtags, 1):
            hashtag_data.append([
                i, h.tag, h.category, h.count, h.avg_engagement, h.hot_score, h.grade, h.grade_reason
            ])
        self.write_values(spreadsheet_id, f"{self._hashtag_tab}!A1", hashtag_data)
        print(f"  → {self._hashtag_tab} 시트 작성 완료 ({len(result.top_hashtags)}개)")
        
        # 2. Viral content sheet (dynamic name based on data count)
        viral_data = [["순위", "계정", "주제", "좋아요", "댓글", "조회수", "인게이지먼트", "URL"]]
        for v in result.top_viral:
            viral_data.append([
                v.rank, v.username, v.topic, v.likes, v.comments, v.views, v.engagement,
                f'=HYPERLINK("{v.url}", "View Post")'
            ])
        self.write_values(spreadsheet_id, f"{self._viral_tab}!A1", viral_data)
        print(f"  → {self._viral_tab} 시트 작성 완료 ({len(result.top_viral)}개)")
        
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

        # 6. Write category summary for pie chart
        category_counts = {}
        for h in result.top_hashtags:
            category_counts[h.category] = category_counts.get(h.category, 0) + 1
        summary_data = [["카테고리", "개수"]]
        for cat, cnt in category_counts.items():
            name = CATEGORY_COLORS.get(cat, {}).get("name", cat)
            summary_data.append([name, cnt])
        self.write_values(spreadsheet_id, f"{self._hashtag_tab}!J16", summary_data)

        # 7. Apply all formatting in single batchUpdate
        requests = self._build_formatting_requests(result)
        if requests:
            self._get_service().spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests}
            ).execute()
            print("  → 서식 및 차트 적용 완료")

        # 공개 권한 설정
        self.set_public_permission(spreadsheet_id)
        
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
