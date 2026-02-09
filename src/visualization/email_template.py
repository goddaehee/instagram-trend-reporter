"""이메일 HTML 템플릿 생성 모듈"""
from typing import Dict

from ..analyzer import AnalysisResult
from .colors import GRADE_COLORS, CATEGORY_COLORS, INSTAGRAM_COLORS


def create_html_email(result: AnalysisResult, sheets_info: Dict[str, str], has_charts: bool = True) -> str:
    """
    HTML 이메일 본문 생성

    Args:
        result: 분석 결과
        sheets_info: Google Sheets 정보 (url 포함)
        has_charts: 차트 이미지 포함 여부

    Returns:
        완성된 HTML 문자열
    """
    # 지표 데이터
    total_posts = result.total_posts
    top_hashtags_count = len(result.top_hashtags)
    viral_count = len(result.top_viral)

    # 해시태그 태그 클라우드 HTML
    hashtag_pills = ""
    for h in result.top_hashtags[:10]:
        # 등급별 배경색
        if "Hot" in h.grade:
            bg_color = GRADE_COLORS["hot"]["hex"]
        elif "Rising" in h.grade:
            bg_color = GRADE_COLORS["rising"]["hex"]
        else:
            bg_color = GRADE_COLORS["stable"]["hex"]

        hashtag_pills += f'''
            <span style="display: inline-block; background-color: {bg_color}; color: #ffffff;
                         padding: 6px 12px; margin: 4px; border-radius: 16px; font-size: 13px;
                         font-weight: 500;">
                {h.tag} <span style="opacity: 0.8; font-size: 11px;">({h.hot_score:.1f})</span>
            </span>'''

    # 바이럴 콘텐츠 테이블 행
    viral_rows = ""
    for i, v in enumerate(result.top_viral[:7]):
        bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
        viral_rows += f'''
            <tr style="background-color: {bg};">
                <td style="padding: 10px 8px; border-bottom: 1px solid #eeeeee; text-align: center; font-weight: bold; color: {INSTAGRAM_COLORS['pink']};">{v.rank}</td>
                <td style="padding: 10px 8px; border-bottom: 1px solid #eeeeee; font-weight: 500;">{v.username}</td>
                <td style="padding: 10px 8px; border-bottom: 1px solid #eeeeee;">{v.topic[:30]}</td>
                <td style="padding: 10px 8px; border-bottom: 1px solid #eeeeee; text-align: right;">{v.views:,}</td>
                <td style="padding: 10px 8px; border-bottom: 1px solid #eeeeee; text-align: right;">{v.likes:,}</td>
            </tr>'''

    # 인사이트 카드
    insight_cards = ""
    for ins in result.insights:
        insight_cards += f'''
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 4px solid {INSTAGRAM_COLORS['orange']};">
                <div style="font-weight: bold; color: #333333; font-size: 14px; margin-bottom: 6px;">
                    {ins.number}. {ins.title}
                </div>
                <div style="color: #666666; font-size: 13px; line-height: 1.5;">
                    {ins.description}
                </div>
            </div>'''

    # 차트 이미지 섹션
    chart_section = ""
    if has_charts:
        chart_section = f'''
            <tr>
                <td style="padding: 20px 30px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td style="text-align: center; padding-bottom: 15px;">
                                <img src="cid:hashtag_chart" alt="해시태그 차트" style="max-width: 100%; height: auto; border-radius: 8px;" />
                            </td>
                        </tr>
                        <tr>
                            <td style="text-align: center;">
                                <img src="cid:category_chart" alt="카테고리 분포" style="max-width: 100%; height: auto; border-radius: 8px;" />
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>'''

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>인스타그램 주간 트렌드 리포트</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 20px;">
                <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

                    <!-- Header with Instagram Gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {INSTAGRAM_COLORS['pink']} 0%, {INSTAGRAM_COLORS['orange']} 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: bold;">
                                인스타그램 주간 트렌드 리포트
                            </h1>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">
                                {result.analysis_period}
                            </p>
                        </td>
                    </tr>

                    <!-- Metric Cards Row -->
                    <tr>
                        <td style="padding: 25px 30px;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td width="33%" style="text-align: center; padding: 15px 10px; background-color: #fef0f5; border-radius: 8px;">
                                        <div style="font-size: 28px; font-weight: bold; color: {INSTAGRAM_COLORS['pink']};">{total_posts:,}</div>
                                        <div style="font-size: 12px; color: #666666; margin-top: 4px;">분석 포스트 수</div>
                                    </td>
                                    <td width="4%"></td>
                                    <td width="33%" style="text-align: center; padding: 15px 10px; background-color: #fff5ef; border-radius: 8px;">
                                        <div style="font-size: 28px; font-weight: bold; color: {INSTAGRAM_COLORS['orange']};">{top_hashtags_count}</div>
                                        <div style="font-size: 12px; color: #666666; margin-top: 4px;">Top 해시태그 수</div>
                                    </td>
                                    <td width="4%"></td>
                                    <td width="33%" style="text-align: center; padding: 15px 10px; background-color: #f5f0ff; border-radius: 8px;">
                                        <div style="font-size: 28px; font-weight: bold; color: {INSTAGRAM_COLORS['purple']};">{viral_count}</div>
                                        <div style="font-size: 12px; color: #666666; margin-top: 4px;">바이럴 콘텐츠 수</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Charts Section -->
                    {chart_section}

                    <!-- Top Hashtags Tag Cloud -->
                    <tr>
                        <td style="padding: 20px 30px;">
                            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333333; border-bottom: 2px solid {INSTAGRAM_COLORS['pink']}; padding-bottom: 8px;">
                                Top 해시태그
                            </h2>
                            <div style="line-height: 2.2;">
                                {hashtag_pills}
                            </div>
                        </td>
                    </tr>

                    <!-- Viral Content Table -->
                    <tr>
                        <td style="padding: 20px 30px;">
                            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333333; border-bottom: 2px solid {INSTAGRAM_COLORS['orange']}; padding-bottom: 8px;">
                                바이럴 콘텐츠 Top 7
                            </h2>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse;">
                                <tr style="background-color: #333333;">
                                    <th style="padding: 10px 8px; color: #ffffff; font-size: 12px; text-align: center; width: 40px;">순위</th>
                                    <th style="padding: 10px 8px; color: #ffffff; font-size: 12px; text-align: left;">계정</th>
                                    <th style="padding: 10px 8px; color: #ffffff; font-size: 12px; text-align: left;">주제</th>
                                    <th style="padding: 10px 8px; color: #ffffff; font-size: 12px; text-align: right;">조회수</th>
                                    <th style="padding: 10px 8px; color: #ffffff; font-size: 12px; text-align: right;">좋아요</th>
                                </tr>
                                {viral_rows}
                            </table>
                        </td>
                    </tr>

                    <!-- Insights Section -->
                    <tr>
                        <td style="padding: 20px 30px;">
                            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333333; border-bottom: 2px solid {INSTAGRAM_COLORS['yellow']}; padding-bottom: 8px;">
                                인사이트
                            </h2>
                            {insight_cards}
                        </td>
                    </tr>

                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 20px 30px; text-align: center;">
                            <a href="{sheets_info.get('url', '#')}" target="_blank"
                               style="display: inline-block; background-color: {INSTAGRAM_COLORS['pink']}; color: #ffffff;
                                      text-decoration: none; padding: 14px 32px; border-radius: 25px; font-size: 15px;
                                      font-weight: bold; box-shadow: 0 4px 12px rgba(225, 48, 108, 0.3);">
                                Google Sheets에서 전체 리포트 보기
                            </a>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 25px 30px; text-align: center; background-color: #f8f9fa; border-top: 1px solid #eeeeee;">
                            <p style="margin: 0; color: #999999; font-size: 13px;">
                                갓댐봇
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    return html
