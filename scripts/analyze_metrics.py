"""
메트릭 분석 스크립트
실험 메트릭을 분석하고 요약 리포트 생성
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def load_metrics(metrics_file: str) -> Dict:
    """메트릭 JSON 파일 로드"""
    with open(metrics_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_duration(seconds: float) -> str:
    """초를 사람이 읽기 쉬운 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def print_summary(metrics: Dict):
    """메트릭 요약 출력"""
    print("="*80)
    print("실험 메트릭 요약")
    print("="*80)

    print(f"\n[기본 정보]")
    print(f"  실험 ID: {metrics['experiment_id']}")
    print(f"  PDF 이름: {metrics['pdf_name']}")
    print(f"  시작 시간: {metrics['start_time']}")
    print(f"  종료 시간: {metrics['end_time']}")
    print(f"  총 실행 시간: {format_duration(metrics['total_duration_seconds'])}")
    print(f"  상태: {metrics['status']}")

    print(f"\n[LLM 정보]")
    print(f"  제공자: {metrics['llm_provider']}")
    print(f"  모델: {metrics['llm_model']}")

    print(f"\n[토큰 사용량]")
    print(f"  입력 토큰: {metrics['total_input_tokens']:,}")
    print(f"  출력 토큰: {metrics['total_output_tokens']:,}")
    print(f"  총 토큰: {metrics['total_tokens']:,}")

    print(f"\n[예상 비용]")
    print(f"  USD: ${metrics['total_cost']:.4f}")
    print(f"  KRW (환율 1,300원): {metrics['total_cost'] * 1300:.0f}원")

    print(f"\n[Step별 실행 시간]")
    print(f"  {'Step':<40} {'시간':<15} {'상태':<10}")
    print(f"  {'-'*65}")

    for step in metrics['steps']:
        duration_str = format_duration(step['duration_seconds'])
        print(f"  {step['step_name']:<40} {duration_str:<15} {step['status']:<10}")

    print(f"\n[Step별 LLM 사용량]")
    print(f"  {'Step':<40} {'호출':<8} {'입력':<12} {'출력':<12} {'비용 (USD)':<12}")
    print(f"  {'-'*84}")

    for step in metrics['steps']:
        if step['total_tokens'] > 0:
            print(f"  {step['step_name']:<40} "
                  f"{len(step['llm_calls']):<8} "
                  f"{step['total_input_tokens']:>11,} "
                  f"{step['total_output_tokens']:>11,} "
                  f"${step['total_cost']:>10.4f}")

    print("\n" + "="*80)


def generate_report(metrics: Dict, output_file: str):
    """마크다운 리포트 생성"""
    lines = []

    lines.append(f"# 실험 메트릭 리포트")
    lines.append(f"")
    lines.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"")

    lines.append(f"## 기본 정보")
    lines.append(f"")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 실험 ID | {metrics['experiment_id']} |")
    lines.append(f"| PDF 이름 | {metrics['pdf_name']} |")
    lines.append(f"| 시작 시간 | {metrics['start_time']} |")
    lines.append(f"| 종료 시간 | {metrics['end_time']} |")
    lines.append(f"| 총 실행 시간 | {format_duration(metrics['total_duration_seconds'])} |")
    lines.append(f"| 상태 | {metrics['status']} |")
    lines.append(f"")

    lines.append(f"## LLM 정보")
    lines.append(f"")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 제공자 | {metrics['llm_provider']} |")
    lines.append(f"| 모델 | {metrics['llm_model']} |")
    lines.append(f"")

    lines.append(f"## 토큰 사용량 및 비용")
    lines.append(f"")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 입력 토큰 | {metrics['total_input_tokens']:,} |")
    lines.append(f"| 출력 토큰 | {metrics['total_output_tokens']:,} |")
    lines.append(f"| 총 토큰 | {metrics['total_tokens']:,} |")
    lines.append(f"| 예상 비용 (USD) | ${metrics['total_cost']:.4f} |")
    lines.append(f"| 예상 비용 (KRW, 환율 1,300원) | ₩{metrics['total_cost'] * 1300:.0f} |")
    lines.append(f"")

    lines.append(f"## Step별 실행 시간")
    lines.append(f"")
    lines.append(f"| Step | 실행 시간 | 상태 |")
    lines.append(f"|------|-----------|------|")
    for step in metrics['steps']:
        duration_str = format_duration(step['duration_seconds'])
        lines.append(f"| {step['step_name']} | {duration_str} | {step['status']} |")
    lines.append(f"")

    lines.append(f"## Step별 LLM 사용량")
    lines.append(f"")
    lines.append(f"| Step | API 호출 수 | 입력 토큰 | 출력 토큰 | 비용 (USD) |")
    lines.append(f"|------|------------|----------|----------|-----------|")
    for step in metrics['steps']:
        if step['total_tokens'] > 0:
            lines.append(f"| {step['step_name']} | "
                        f"{len(step['llm_calls'])} | "
                        f"{step['total_input_tokens']:,} | "
                        f"{step['total_output_tokens']:,} | "
                        f"${step['total_cost']:.4f} |")
    lines.append(f"")

    # 상세 LLM 호출 정보
    lines.append(f"## 상세 LLM 호출 내역")
    lines.append(f"")
    for step in metrics['steps']:
        if step['llm_calls']:
            lines.append(f"### {step['step_name']}")
            lines.append(f"")
            lines.append(f"| 호출 시각 | 모델 | 입력 토큰 | 출력 토큰 | 총 토큰 | 비용 (USD) |")
            lines.append(f"|-----------|------|----------|----------|---------|-----------|")
            for call in step['llm_calls']:
                timestamp = call['timestamp'].split('T')[1].split('.')[0]  # HH:MM:SS만 추출
                lines.append(f"| {timestamp} | "
                           f"{call['model']} | "
                           f"{call['input_tokens']:,} | "
                           f"{call['output_tokens']:,} | "
                           f"{call['total_tokens']:,} | "
                           f"${call['cost']:.4f} |")
            lines.append(f"")

    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n리포트 저장: {output_file}")


def compare_experiments(metrics_files: List[str]):
    """여러 실험 메트릭 비교"""
    experiments = []

    for file in metrics_files:
        try:
            metrics = load_metrics(file)
            experiments.append(metrics)
        except Exception as e:
            print(f"[WARNING] {file} 로드 실패: {e}")

    if not experiments:
        print("[ERROR] 로드된 실험이 없습니다.")
        return

    print("="*100)
    print("실험 비교")
    print("="*100)

    print(f"\n{'실험 ID':<25} {'PDF':<20} {'실행시간':<15} {'총 토큰':<15} {'비용 (USD)':<12}")
    print("-"*100)

    for exp in experiments:
        duration_str = format_duration(exp['total_duration_seconds'])
        print(f"{exp['experiment_id']:<25} "
              f"{exp['pdf_name']:<20} "
              f"{duration_str:<15} "
              f"{exp['total_tokens']:>14,} "
              f"${exp['total_cost']:>10.4f}")

    print("="*100)


def main():
    """CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(
        description="실험 메트릭 분석",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "metrics_file",
        type=str,
        nargs='+',
        help="메트릭 JSON 파일 경로 (여러 파일 지정 가능)"
    )

    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="마크다운 리포트 출력 파일 경로"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="여러 실험 비교 모드"
    )

    args = parser.parse_args()

    if args.compare and len(args.metrics_file) > 1:
        # 비교 모드
        compare_experiments(args.metrics_file)
    else:
        # 단일 파일 분석
        metrics_file = args.metrics_file[0]

        if not Path(metrics_file).exists():
            print(f"[ERROR] 파일을 찾을 수 없음: {metrics_file}")
            sys.exit(1)

        metrics = load_metrics(metrics_file)
        print_summary(metrics)

        if args.report:
            generate_report(metrics, args.report)


if __name__ == "__main__":
    main()
