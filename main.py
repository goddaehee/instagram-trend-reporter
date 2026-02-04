#!/usr/bin/env python3
"""
Instagram Trend Reporter CLI

인스타그램 트렌드 분석 → Google Sheets 리포트 → 이메일 전송

Usage:
    python main.py run                    # 전체 파이프라인 실행
    python main.py run --no-email         # 이메일 전송 제외
    python main.py run --days 14          # 분석 기간 변경
    python main.py run --email a@b.com    # 수신자 지정
"""
import argparse
import sys
from pathlib import Path

# src 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config, get_config
from src.reporter import InstagramTrendReporter


def main():
    parser = argparse.ArgumentParser(
        description="인스타그램 트렌드 리포트 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py run                     전체 파이프라인 실행
  python main.py run --no-email          이메일 전송 제외
  python main.py run --days 14           분석 기간 14일
  python main.py run --email a@b.com     수신자 지정 (여러 개 가능)
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="명령어")
    
    # run 명령어
    run_parser = subparsers.add_parser("run", help="리포트 생성 실행")
    run_parser.add_argument(
        "--config", "-c",
        help="설정 파일 경로 (기본: config/settings.yaml)",
    )
    run_parser.add_argument(
        "--days", "-d",
        type=int,
        help="분석 기간 (일)",
    )
    run_parser.add_argument(
        "--no-email",
        action="store_true",
        help="이메일 전송 제외",
    )
    run_parser.add_argument(
        "--email", "-e",
        action="append",
        help="이메일 수신자 (여러 번 지정 가능)",
    )
    run_parser.add_argument(
        "--no-save",
        action="store_true",
        help="원본 데이터 저장 제외",
    )
    
    # test 명령어 (설정 확인)
    test_parser = subparsers.add_parser("test", help="설정 테스트")
    test_parser.add_argument(
        "--config", "-c",
        help="설정 파일 경로",
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        # 설정 로드
        config = Config.load(args.config) if args.config else get_config()
        
        # 명령줄 옵션으로 설정 오버라이드
        if args.days:
            config.analysis.days = args.days
        
        # 리포터 실행
        reporter = InstagramTrendReporter(config)
        result = reporter.run(
            save_raw=not args.no_save,
            send_email=not args.no_email,
            recipients=args.email,
        )
        
        print("\n📋 실행 결과:")
        print(f"  - 분석 포스트: {result['total_posts']}개")
        print(f"  - Top 해시태그: {result['top_hashtags_count']}개")
        print(f"  - Top 바이럴: {result['top_viral_count']}개")
        print(f"  - 인사이트: {result['insights_count']}개")
        print(f"  - 소요 시간: {result['duration_seconds']:.1f}초")
        print(f"\n📎 리포트: {result['sheets']['url']}")
        
    elif args.command == "test":
        config = Config.load(args.config) if args.config else get_config()
        
        print("📋 설정 확인")
        print("=" * 40)
        print(f"Apify Token: {config.apify_token[:20]}...")
        print(f"분석 기간: {config.analysis.days}일")
        print(f"콘텐츠 유형: {config.analysis.content_type}")
        print(f"Top 해시태그: {config.analysis.top_hashtags}개")
        print(f"Top 바이럴: {config.analysis.top_viral}개")
        print(f"\n계정 ({len(config.accounts)}개):")
        for acc in config.accounts:
            print(f"  - @{acc.username} ({acc.category})")
        print(f"\n이메일 수신자:")
        for email in config.email_recipients:
            print(f"  - {email}")
        print("\n✅ 설정 확인 완료")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
