"""전체 파이프라인 오케스트레이션 모듈"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict

from .config import get_config, Config
from .fetcher import fetch_instagram_data
from .analyzer import analyze_instagram_data, AnalysisResult
from .sheets import create_sheets_report
from .mailer import send_report_email


class InstagramTrendReporter:
    """인스타그램 트렌드 리포트 생성기"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.output_dir = Path.home() / "instagram-research"
    
    def run(
        self,
        save_raw: bool = True,
        send_email: bool = True,
        recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        run_start = datetime.now()
        run_id = run_start.strftime("%Y-%m-%d_%H%M%S")
        run_dir = self.output_dir / run_id
        
        print("=" * 50)
        print("🚀 인스타그램 트렌드 리포트 생성 시작")
        print("=" * 50)
        print(f"실행 ID: {run_id}")
        print(f"분석 기간: 최근 {self.config.analysis.days}일")
        print(f"분석 계정: {len(self.config.accounts)}개")
        print()
        
        # 1. 데이터 수집
        print("[1/4] 📥 인스타그램 데이터 수집")
        data = fetch_instagram_data(self.config)
        
        if save_raw:
            run_dir.mkdir(parents=True, exist_ok=True)
            raw_path = run_dir / "raw.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(data["posts"], f, ensure_ascii=False, indent=2)
            print(f"  → 원본 데이터 저장: {raw_path}")
        print()
        
        # 2. 데이터 분석
        print("[2/4] 🔍 데이터 분석")
        result = analyze_instagram_data(data, self.config)
        
        if save_raw:
            analysis_path = run_dir / "analysis.json"
            # dataclass를 dict로 변환
            analysis_dict = {
                "total_posts": result.total_posts,
                "analysis_period": result.analysis_period,
                "accounts": result.accounts,
                "top_hashtags": [
                    {"tag": h.tag, "count": h.count, "avg_engagement": h.avg_engagement,
                     "hot_score": h.hot_score, "category": h.category, "grade": h.grade}
                    for h in result.top_hashtags
                ],
                "top_viral": [
                    {"rank": v.rank, "username": v.username, "topic": v.topic,
                     "likes": v.likes, "comments": v.comments, "views": v.views,
                     "engagement": v.engagement, "url": v.url}
                    for v in result.top_viral
                ],
                "insights": [
                    {"number": i.number, "title": i.title, "description": i.description}
                    for i in result.insights
                ],
                "generated_at": result.generated_at,
            }
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(analysis_dict, f, ensure_ascii=False, indent=2)
            print(f"  → 분석 결과 저장: {analysis_path}")
        print()
        
        # 3. Google Sheets 리포트 생성
        print("[3/4] 📊 Google Sheets 리포트 생성")
        sheets_info = create_sheets_report(result, self.config)
        print(f"  → 리포트 URL: {sheets_info['url']}")
        print()
        
        # 4. 이메일 전송
        email_results = []
        if send_email:
            print("[4/4] 📧 이메일 전송")
            email_results = send_report_email(result, sheets_info, recipients, self.config)
        else:
            print("[4/4] 📧 이메일 전송 (스킵)")
        print()
        
        # 완료
        run_end = datetime.now()
        duration = (run_end - run_start).total_seconds()
        
        print("=" * 50)
        print("✅ 리포트 생성 완료!")
        print("=" * 50)
        print(f"소요 시간: {duration:.1f}초")
        print(f"리포트 URL: {sheets_info['url']}")
        print()
        
        return {
            "run_id": run_id,
            "duration_seconds": duration,
            "total_posts": result.total_posts,
            "top_hashtags_count": len(result.top_hashtags),
            "top_viral_count": len(result.top_viral),
            "insights_count": len(result.insights),
            "sheets": sheets_info,
            "email_results": email_results,
        }


def run_report(
    config_path: Optional[str] = None,
    save_raw: bool = True,
    send_email: bool = True,
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """리포트 생성 실행 (편의 함수)"""
    config = Config.load(config_path) if config_path else get_config()
    reporter = InstagramTrendReporter(config)
    return reporter.run(save_raw=save_raw, send_email=send_email, recipients=recipients)
