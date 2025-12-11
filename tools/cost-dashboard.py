#!/usr/bin/env python3
"""
cost-dashboard.py - Cost Tracking Dashboard & Reports

Display cost summaries, job costs, and optimization recommendations.

Usage:
    python3 tools/cost-dashboard.py show-monthly         # Monthly summary
    python3 tools/cost-dashboard.py show-job JOB_ID      # Job cost breakdown
    python3 tools/cost-dashboard.py show-budget          # Budget status
    python3 tools/cost-dashboard.py export-report        # Export JSON report

Related: BRD/PRD/TRD-2025-12-10-04-cost-tracking
Status: ✅ Implemented (Phase 6 - Task #21)
"""

# Standard library
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local
from shared.cost_tracker import CostTracker
from shared.logger import get_logger

logger = get_logger(__name__)


def show_monthly_summary(user_id: int = 1) -> None:
    """
    Display monthly cost summary.
    
    Args:
        user_id: User ID to show summary for
    """
    tracker = CostTracker(user_id=user_id)
    summary = tracker.get_monthly_summary(user_id)
    
    print("\n" + "=" * 70)
    print(f"📊 AI Cost Summary - {summary['month']}")
    print("=" * 70)
    
    print(f"\n💰 Total Costs:")
    print(f"   Total spend:        ${summary['total_cost']:.2f}")
    print(f"   Jobs processed:     {summary['unique_jobs']} jobs")
    print(f"   Avg cost per job:   ${summary['avg_cost_per_job']:.2f}")
    print(f"   Total API calls:    {summary['total_calls']}")
    print(f"   Total tokens:       {summary['total_tokens']:,}")
    
    # Budget status
    print(f"\n💳 Budget Status:")
    budget_limit, alert_threshold = tracker._load_user_budget(user_id)
    current_spend = summary['total_cost']
    percent_used = (current_spend / budget_limit * 100) if budget_limit > 0 else 0
    remaining = budget_limit - current_spend
    
    status_icon = "✅" if percent_used < alert_threshold else "⚠️" if percent_used < 100 else "🚨"
    print(f"   {status_icon} Monthly budget:    ${budget_limit:.2f}")
    print(f"   Current spend:      ${current_spend:.2f} ({percent_used:.1f}%)")
    print(f"   Remaining:          ${remaining:.2f}")
    
    # Breakdown by service
    if summary['by_service']:
        print(f"\n📈 Cost by Service:")
        for service, data in sorted(
            summary['by_service'].items(),
            key=lambda x: x[1]['cost'],
            reverse=True
        ):
            percent = (data['cost'] / summary['total_cost'] * 100) if summary['total_cost'] > 0 else 0
            bar = "█" * int(percent / 5)  # 20 chars max
            print(f"   {service:15s} {bar:20s} ${data['cost']:7.2f} ({percent:5.1f}%)")
    
    # Top models
    if summary['by_model']:
        print(f"\n🔝 Top Models:")
        top_models = sorted(
            summary['by_model'].items(),
            key=lambda x: x[1]['cost'],
            reverse=True
        )[:5]  # Top 5
        
        for model, data in top_models:
            print(f"   {model:30s} ${data['cost']:7.2f} ({data['calls']:4d} calls)")
    
    print("\n" + "=" * 70 + "\n")


def show_job_costs(job_id: str, user_id: int = 1) -> None:
    """
    Display cost breakdown for a specific job.
    
    Args:
        job_id: Job ID to show costs for
        user_id: User ID
    """
    # Find job directory
    out_dir = Path.cwd() / "out"
    job_dirs = list(out_dir.rglob(f"*{job_id}*"))
    
    if not job_dirs:
        print(f"❌ Job not found: {job_id}")
        return
    
    job_dir = job_dirs[0]
    tracker = CostTracker(job_dir=job_dir, user_id=user_id)
    
    total_cost = tracker.get_job_cost(job_id)
    stage_costs = tracker.get_stage_costs(job_id)
    
    print("\n" + "=" * 70)
    print(f"💼 Job Cost Report: {job_id}")
    print("=" * 70)
    
    print(f"\n📁 Job Details:")
    print(f"   Job ID:    {job_id}")
    print(f"   Job Dir:   {job_dir}")
    
    print(f"\n💰 Total Cost: ${total_cost:.4f}")
    
    if stage_costs:
        print(f"\n📊 Cost by Stage:")
        for stage, cost in sorted(stage_costs.items()):
            percent = (cost / total_cost * 100) if total_cost > 0 else 0
            print(f"   {stage:25s} ${cost:7.4f} ({percent:5.1f}%)")
    else:
        print("\n   No stage costs recorded for this job.")
    
    # Budget impact
    budget_limit, _ = tracker._load_user_budget(user_id)
    current_spend = tracker.get_monthly_cost(user_id)
    remaining = budget_limit - current_spend
    
    print(f"\n💳 Budget Impact:")
    print(f"   Budget remaining:  ${remaining:.2f}")
    print(f"   % of monthly:      {(total_cost / budget_limit * 100):.1f}%")
    
    print("\n" + "=" * 70 + "\n")


def show_budget_status(user_id: int = 1) -> None:
    """
    Display current budget status.
    
    Args:
        user_id: User ID
    """
    tracker = CostTracker(user_id=user_id)
    
    budget_limit, alert_threshold = tracker._load_user_budget(user_id)
    current_spend = tracker.get_monthly_cost(user_id)
    percent_used = (current_spend / budget_limit * 100) if budget_limit > 0 else 0
    remaining = budget_limit - current_spend
    
    # Calculate daily average and projection
    current_day = datetime.now(timezone.utc).day
    daily_avg = current_spend / current_day if current_day > 0 else 0
    days_in_month = 30  # Approximate
    days_remaining = days_in_month - current_day
    projected_total = current_spend + (daily_avg * days_remaining)
    projected_overage = max(0, projected_total - budget_limit)
    
    print("\n" + "=" * 70)
    print(f"💳 Budget Status Report")
    print("=" * 70)
    
    print(f"\n📊 Current Status:")
    status_icon = "✅" if percent_used < alert_threshold else "⚠️" if percent_used < 100 else "🚨"
    print(f"   {status_icon} Monthly budget:    ${budget_limit:.2f}")
    print(f"   Current spend:      ${current_spend:.2f} ({percent_used:.1f}%)")
    print(f"   Remaining:          ${remaining:.2f}")
    print(f"   Alert threshold:    {alert_threshold:.0f}%")
    
    # Visual progress bar
    bar_length = 50
    filled = int(bar_length * percent_used / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n   [{bar}] {percent_used:.1f}%")
    
    # Projection
    print(f"\n📈 Projection:")
    print(f"   Current day:        {current_day}")
    print(f"   Days remaining:     {days_remaining}")
    print(f"   Daily average:      ${daily_avg:.2f}")
    print(f"   Projected total:    ${projected_total:.2f}")
    
    if projected_overage > 0:
        print(f"   ⚠️  Projected overage: ${projected_overage:.2f}")
        # Suggest reduction
        reduction_needed = (projected_overage / days_remaining) if days_remaining > 0 else 0
        print(f"   💡 Reduce daily spend by ${reduction_needed:.2f} to stay in budget")
    else:
        print(f"   ✅ On track to stay within budget")
    
    # Alerts
    alerts = tracker.check_budget_alerts(user_id)
    if alerts:
        print(f"\n🔔 Active Alerts:")
        for alert in alerts:
            print(f"   {alert}")
    
    print("\n" + "=" * 70 + "\n")


def show_optimization_recommendations(user_id: int = 1) -> None:
    """
    Display cost optimization recommendations.
    
    Args:
        user_id: User ID
    """
    tracker = CostTracker(user_id=user_id)
    summary = tracker.get_monthly_summary(user_id)
    
    print("\n" + "=" * 70)
    print(f"💡 Cost Optimization Recommendations")
    print("=" * 70)
    
    recommendations = []
    
    # Check if using expensive models
    if "openai" in summary['by_service']:
        openai_cost = summary['by_service']['openai']['cost']
        if openai_cost > 5.0:  # Significant OpenAI usage
            # Check for GPT-4 usage
            gpt4_models = [m for m in summary['by_model'] if 'gpt-4' in m.lower() and 'gpt-4o' not in m.lower()]
            if gpt4_models:
                gpt4_cost = sum(summary['by_model'][m]['cost'] for m in gpt4_models)
                savings = gpt4_cost * 0.30  # ~30% savings with GPT-4o
                recommendations.append({
                    "priority": 1,
                    "title": "Switch from GPT-4 to GPT-4o",
                    "savings": savings,
                    "impact": "30% cost reduction, minimal quality difference",
                    "action": "Update config/.env.pipeline: AI_MODEL_PRIMARY=gpt-4o"
                })
    
    # Check for Gemini opportunity
    if "openai" in summary['by_service'] and "gemini" not in summary['by_service']:
        openai_cost = summary['by_service']['openai']['cost']
        if openai_cost > 10.0:
            savings = openai_cost * 0.50  # ~50% savings with Gemini
            recommendations.append({
                "priority": 1,
                "title": "Try Google Gemini for some tasks",
                "savings": savings,
                "impact": "50% cost reduction for suitable tasks",
                "action": "Update config/.env.pipeline: AI_PROVIDER=gemini for summarization"
            })
    
    # Check for local model opportunities
    if "whisperx" in summary['by_service']:
        whisperx_cost = summary['by_service']['whisperx']['cost']
        if whisperx_cost > 5.0:
            savings = whisperx_cost * 0.90  # 90% savings with local MLX
            recommendations.append({
                "priority": 2,
                "title": "Use local MLX Whisper instead of API",
                "savings": savings,
                "impact": "90% cost reduction, 8-9x faster on Apple Silicon",
                "action": "Update config/.env.pipeline: WHISPER_BACKEND=mlx"
            })
    
    # General recommendation: enable caching
    if summary['unique_jobs'] > 5:
        estimated_savings = summary['total_cost'] * 0.15  # 15% savings estimate
        recommendations.append({
            "priority": 3,
            "title": "Enable caching for repeated content",
            "savings": estimated_savings,
            "impact": "15-30% cost reduction on similar content",
            "action": "Update config/.env.pipeline: ENABLE_CACHING=true"
        })
    
    # Display recommendations
    if recommendations:
        total_savings = sum(r['savings'] for r in recommendations)
        print(f"\n✨ Found {len(recommendations)} optimization opportunities")
        print(f"💰 Total potential savings: ${total_savings:.2f}/month ({(total_savings/summary['total_cost']*100):.0f}%)\n")
        
        for i, rec in enumerate(sorted(recommendations, key=lambda x: x['priority']), 1):
            print(f"{i}. {rec['title']}")
            print(f"   💰 Savings: ${rec['savings']:.2f}/month")
            print(f"   📊 Impact: {rec['impact']}")
            print(f"   🔧 Action: {rec['action']}")
            print()
    else:
        print("\n✅ No significant optimization opportunities found.")
        print("Your cost configuration is already efficient!\n")
    
    print("=" * 70 + "\n")


def export_report(
    user_id: int = 1,
    format: str = "json",
    output_file: Optional[Path] = None
) -> None:
    """
    Export cost report to file.
    
    Args:
        user_id: User ID
        format: Output format (json, csv)
        output_file: Output file path (default: cost_report_YYYY-MM.{format})
    """
    tracker = CostTracker(user_id=user_id)
    summary = tracker.get_monthly_summary(user_id)
    
    if output_file is None:
        month = summary['month']
        output_file = Path(f"cost_report_{month}.{format}")
    else:
        output_file = Path(output_file)
    
    if format == "json":
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Exported JSON report: {output_file}")
    
    elif format == "csv":
        import csv
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Service/Model', 'Cost (USD)', 'Tokens', 'Calls'])
            for model, data in sorted(
                summary['by_model'].items(),
                key=lambda x: x[1]['cost'],
                reverse=True
            ):
                writer.writerow([
                    model,
                    f"{data['cost']:.2f}",
                    data['tokens'],
                    data['calls']
                ])
        print(f"✅ Exported CSV report: {output_file}")
    
    else:
        print(f"❌ Unsupported format: {format}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cost Tracking Dashboard & Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/cost-dashboard.py show-monthly
  python3 tools/cost-dashboard.py show-job job-20251210-rpatel-0001
  python3 tools/cost-dashboard.py show-budget
  python3 tools/cost-dashboard.py show-optimization
  python3 tools/cost-dashboard.py export-report --format json
        """
    )
    
    parser.add_argument(
        'command',
        choices=['show-monthly', 'show-job', 'show-budget', 'show-optimization', 'export-report'],
        help='Command to execute'
    )
    parser.add_argument(
        'job_id',
        nargs='?',
        help='Job ID (required for show-job command)'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        default=1,
        help='User ID (default: 1)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'csv'],
        default='json',
        help='Export format (default: json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'show-monthly':
            show_monthly_summary(args.user_id)
        
        elif args.command == 'show-job':
            if not args.job_id:
                print("❌ Error: job_id required for show-job command")
                parser.print_help()
                sys.exit(1)
            show_job_costs(args.job_id, args.user_id)
        
        elif args.command == 'show-budget':
            show_budget_status(args.user_id)
        
        elif args.command == 'show-optimization':
            show_optimization_recommendations(args.user_id)
        
        elif args.command == 'export-report':
            export_report(args.user_id, args.format, args.output)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
