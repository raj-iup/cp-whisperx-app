#!/usr/bin/env python3
"""
Model Usage Statistics Tracker

Track AI model usage and costs over time.
Run: ./tools/model-usage-stats.py [--month YYYY-MM] [--report]

Compliance: § 16.7 (DEVELOPER_STANDARDS.md)
"""

# Standard library
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure simple logging
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ModelUsageTracker:
    """Track and report on AI model usage and costs."""
    
    def __init__(self, log_dir: Path = Path("logs/model-usage")):
        """
        Initialize usage tracker.
        
        Args:
            log_dir: Directory for usage logs
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model registry for costs
        self.model_registry = self._load_model_registry()
    
    def _load_model_registry(self) -> Dict:
        """Load model registry for cost information."""
        try:
            with open("config/ai_models.json") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Model registry not found, costs unavailable")
            return {"models": {}}
    
    def get_month_stats(self, month: str) -> Dict:
        """
        Get usage statistics for a specific month.
        
        Args:
            month: Month in YYYY-MM format
            
        Returns:
            Dict with usage statistics
        """
        log_file = self.log_dir / f"{month}.json"
        
        if not log_file.exists():
            logger.info(f"No usage data for {month}")
            return {
                "month": month,
                "models": {},
                "total_tokens": 0,
                "total_cost": 0.0
            }
        
        try:
            with open(log_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {log_file}", exc_info=True)
            return {"month": month, "models": {}, "total_tokens": 0, "total_cost": 0.0}
    
    def generate_report(self, month: str) -> str:
        """
        Generate human-readable usage report.
        
        Args:
            month: Month in YYYY-MM format
            
        Returns:
            Formatted report string
        """
        stats = self.get_month_stats(month)
        
        if not stats.get("models"):
            return f"No usage data for {month}\n"
        
        report = []
        report.append(f"AI Model Usage Report - {month}")
        report.append("=" * 60)
        report.append("")
        
        # Sort models by cost (descending)
        models = sorted(
            stats["models"].items(),
            key=lambda x: x[1].get("cost", 0),
            reverse=True
        )
        
        for model_id, model_stats in models:
            tokens = model_stats.get("tokens", 0)
            cost = model_stats.get("cost", 0.0)
            calls = model_stats.get("calls", 0)
            
            report.append(f"Model: {model_id}")
            report.append(f"  Tokens: {tokens:,}")
            report.append(f"  Cost: ${cost:.2f}")
            report.append(f"  API Calls: {calls}")
            report.append(f"  Avg tokens/call: {tokens/calls if calls > 0 else 0:.0f}")
            report.append("")
        
        report.append("-" * 60)
        report.append(f"Total Tokens: {stats['total_tokens']:,}")
        report.append(f"Total Cost: ${stats['total_cost']:.2f}")
        report.append("")
        
        # Check against limits
        cost_limits = self.model_registry.get("cost_targets", {})
        monthly_max = cost_limits.get("monthly_max", 500)
        alert_threshold = cost_limits.get("alert_threshold", 0.8)
        
        usage_percent = (stats['total_cost'] / monthly_max) * 100
        
        report.append(f"Monthly Limit: ${monthly_max}")
        report.append(f"Usage: {usage_percent:.1f}%")
        
        if stats['total_cost'] >= monthly_max:
            report.append("⚠️  WARNING: Monthly limit exceeded!")
        elif stats['total_cost'] >= (monthly_max * alert_threshold):
            report.append(f"⚠️  ALERT: {alert_threshold*100:.0f}% threshold reached!")
        else:
            report.append("✅ Within budget")
        
        report.append("")
        
        return "\n".join(report)
    
    def log_usage(
        self,
        model_id: str,
        tokens: int,
        cost: Optional[float] = None
    ) -> None:
        """
        Log model usage.
        
        Args:
            model_id: Model identifier
            tokens: Number of tokens used
            cost: Cost in USD (calculated if not provided)
        """
        # Get current month
        month = datetime.now().strftime("%Y-%m")
        log_file = self.log_dir / f"{month}.json"
        
        # Load existing data
        if log_file.exists():
            with open(log_file) as f:
                data = json.load(f)
        else:
            data = {
                "month": month,
                "models": {},
                "total_tokens": 0,
                "total_cost": 0.0
            }
        
        # Calculate cost if not provided
        if cost is None:
            cost = self._calculate_cost(model_id, tokens)
        
        # Update model stats
        if model_id not in data["models"]:
            data["models"][model_id] = {
                "tokens": 0,
                "cost": 0.0,
                "calls": 0
            }
        
        data["models"][model_id]["tokens"] += tokens
        data["models"][model_id]["cost"] += cost
        data["models"][model_id]["calls"] += 1
        
        # Update totals
        data["total_tokens"] += tokens
        data["total_cost"] += cost
        
        # Save
        with open(log_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Logged: {model_id} - {tokens} tokens (${cost:.4f})")
    
    def _calculate_cost(self, model_id: str, tokens: int) -> float:
        """
        Calculate cost for tokens.
        
        Args:
            model_id: Model identifier
            tokens: Number of tokens
            
        Returns:
            Cost in USD
        """
        models = self.model_registry.get("models", {})
        
        if model_id not in models:
            logger.warning(f"Unknown model: {model_id}, assuming $0.01/1K")
            return (tokens / 1000) * 0.01
        
        # Use input token cost (conservative estimate)
        cost_per_1k = models[model_id]["cost_per_1k_tokens"]["input"]
        return (tokens / 1000) * cost_per_1k


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Track and report AI model usage statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View current month stats
  ./tools/model-usage-stats.py
  
  # View specific month
  ./tools/model-usage-stats.py --month 2025-12
  
  # Generate detailed report
  ./tools/model-usage-stats.py --month 2025-12 --report
  
  # Log manual usage
  ./tools/model-usage-stats.py --log gpt-4o --tokens 5000
        """
    )
    parser.add_argument(
        "--month",
        help="Month to report on (YYYY-MM format, default: current)",
        default=datetime.now().strftime("%Y-%m")
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed report"
    )
    parser.add_argument(
        "--log",
        metavar="MODEL",
        help="Log usage for a model (requires --tokens)"
    )
    parser.add_argument(
        "--tokens",
        type=int,
        help="Number of tokens to log"
    )
    parser.add_argument(
        "--cost",
        type=float,
        help="Cost to log (optional, calculated if not provided)"
    )
    
    args = parser.parse_args()
    
    tracker = ModelUsageTracker()
    
    # Log usage if requested
    if args.log:
        if not args.tokens:
            logger.error("--tokens required when using --log")
            return 1
        
        tracker.log_usage(args.log, args.tokens, args.cost)
        return 0
    
    # Generate report
    if args.report:
        report = tracker.generate_report(args.month)
        logger.info(f"\n{report}")
    else:
        # Quick summary
        stats = tracker.get_month_stats(args.month)
        logger.info(f"\nAI Model Usage - {args.month}")
        logger.info(f"Total Tokens: {stats['total_tokens']:,}")
        logger.info(f"Total Cost: ${stats['total_cost']:.2f}")
        logger.info(f"\nUse --report for detailed breakdown")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
