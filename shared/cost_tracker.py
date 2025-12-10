#!/usr/bin/env python3
"""
cost_tracker.py - AI Service Cost Tracking & Budget Management

Tracks costs for all AI services (OpenAI, Gemini, WhisperX, IndicTrans2) with:
- Real-time cost tracking per API call
- Budget management with 80%/100% alerts
- Monthly cost aggregation and reporting
- Job-level cost tracking

Related: BRD/PRD/TRD-2025-12-10-04-cost-tracking
Status: ✅ Implemented (Phase 6 - Task #21)
"""

# Standard library
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Local
from shared.logger import get_logger

logger = get_logger(__name__)

# ════════════════════════════════════════════════════════════════
# PRICING DATABASE
# ════════════════════════════════════════════════════════════════
# Updated: 2025-12-10 | Source: Official API pricing pages

PRICING_DATABASE = {
    "openai": {
        "gpt-4": {
            "input_per_1k": 0.03,   # $0.03 per 1K input tokens
            "output_per_1k": 0.06,  # $0.06 per 1K output tokens
        },
        "gpt-4o": {
            "input_per_1k": 0.0025,   # $0.0025 per 1K input tokens
            "output_per_1k": 0.01,    # $0.01 per 1K output tokens
        },
        "gpt-4-turbo": {
            "input_per_1k": 0.01,
            "output_per_1k": 0.03,
        },
        "gpt-3.5-turbo": {
            "input_per_1k": 0.0005,
            "output_per_1k": 0.0015,
        },
    },
    "gemini": {
        "gemini-1.5-pro": {
            "input_per_1k": 0.00025,   # $0.00025 per 1K tokens (combined)
            "output_per_1k": 0.00025,
        },
        "gemini-1.5-flash": {
            "input_per_1k": 0.000075,
            "output_per_1k": 0.000075,
        },
        "gemini-pro": {
            "input_per_1k": 0.00025,
            "output_per_1k": 0.00025,
        },
    },
    "azure": {
        "gpt-4": {
            "input_per_1k": 0.03,
            "output_per_1k": 0.06,
        },
        "gpt-4o": {
            "input_per_1k": 0.0025,
            "output_per_1k": 0.01,
        },
        "gpt-35-turbo": {
            "input_per_1k": 0.0005,
            "output_per_1k": 0.0015,
        },
    },
    "whisperx": {
        "large-v3": {
            "input_per_1k": 0.006,   # $0.006 per minute (approx 1K tokens)
            "output_per_1k": 0.0,
        },
        "large-v2": {
            "input_per_1k": 0.006,
            "output_per_1k": 0.0,
        },
        "medium": {
            "input_per_1k": 0.004,
            "output_per_1k": 0.0,
        },
    },
    "indictrans2": {
        "api": {
            "input_per_1k": 0.001,   # Estimated API cost
            "output_per_1k": 0.001,
        },
    },
    "local": {
        "mlx-whisper": {
            "input_per_1k": 0.0,   # Local processing - no API cost
            "output_per_1k": 0.0,
        },
        "indictrans2-local": {
            "input_per_1k": 0.0,
            "output_per_1k": 0.0,
        },
        "pyannote": {
            "input_per_1k": 0.0,
            "output_per_1k": 0.0,
        },
    },
}


class CostTracker:
    """
    Track AI service costs across jobs and stages.
    
    Features:
    - Real-time cost tracking per API call
    - Budget management with 80%/100% alerts
    - Monthly cost aggregation
    - Job-level cost breakdown
    
    Example:
        tracker = CostTracker(job_dir)
        cost = tracker.log_usage(
            service="openai",
            model="gpt-4o",
            tokens_input=1500,
            tokens_output=300,
            stage="13_ai_summarization"
        )
        logger.info(f"Cost: ${cost:.4f}")
    """
    
    def __init__(
        self,
        job_dir: Optional[Path] = None,
        user_id: int = 1,
        cost_storage_path: Optional[Path] = None
    ):
        """
        Initialize cost tracker.
        
        Args:
            job_dir: Path to job directory (optional, for job-level tracking)
            user_id: User ID for per-user cost tracking
            cost_storage_path: Custom cost storage location (default: ~/.cp-whisperx/costs)
        """
        self.job_dir = Path(job_dir) if job_dir else None
        self.user_id = user_id
        
        # Determine cost storage location
        if cost_storage_path:
            self.cost_storage_path = Path(cost_storage_path)
        else:
            # Default: ~/.cp-whisperx/costs
            home = Path.home()
            self.cost_storage_path = home / ".cp-whisperx" / "costs"
        
        # Create storage directory if needed
        self.cost_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Monthly cost log file
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        self.monthly_log_file = self.cost_storage_path / f"{current_month}.json"
        
        # Load pricing database
        self.pricing_db = PRICING_DATABASE
        
        logger.debug(f"CostTracker initialized: user_id={user_id}, storage={self.cost_storage_path}")
    
    def log_usage(
        self,
        service: str,
        model: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        stage: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Log API usage and return computed cost.
        
        Args:
            service: Service name (openai, gemini, whisperx, etc.)
            model: Model name (gpt-4o, gemini-1.5-pro, etc.)
            tokens_input: Input tokens consumed
            tokens_output: Output tokens consumed
            stage: Stage name (for job-level tracking)
            metadata: Additional metadata to store
        
        Returns:
            Cost in USD
        """
        # Compute cost
        cost = self._compute_cost(service, model, tokens_input, tokens_output)
        
        # Create log entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": self.user_id,
            "job_id": self.job_dir.name if self.job_dir else None,
            "service": service,
            "model": model,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_total": tokens_input + tokens_output,
            "cost_usd": round(cost, 6),
            "stage": stage,
        }
        
        # Add metadata if provided
        if metadata:
            entry["metadata"] = metadata
        
        # Append to monthly log
        self._append_log_entry(entry)
        
        # Check budget alerts
        alerts = self.check_budget_alerts()
        if alerts:
            for alert in alerts:
                logger.warning(alert)
        
        logger.debug(f"💰 Logged usage: {service}/{model} = ${cost:.4f}")
        return cost
    
    def _compute_cost(
        self,
        service: str,
        model: str,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """
        Compute cost based on pricing database.
        
        Args:
            service: Service name
            model: Model name
            tokens_input: Input tokens
            tokens_output: Output tokens
        
        Returns:
            Cost in USD
        """
        try:
            pricing = self.pricing_db[service][model]
            cost_input = (tokens_input / 1000) * pricing["input_per_1k"]
            cost_output = (tokens_output / 1000) * pricing["output_per_1k"]
            return cost_input + cost_output
        except KeyError:
            logger.warning(
                f"Unknown service/model: {service}/{model}. Using zero cost. "
                f"Add to PRICING_DATABASE if this is an API service."
            )
            return 0.0
    
    def _append_log_entry(self, entry: Dict[str, Any]) -> None:
        """
        Append log entry to monthly log file.
        
        Args:
            entry: Log entry dictionary
        """
        try:
            # Load existing log
            if self.monthly_log_file.exists():
                with open(self.monthly_log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {"entries": [], "metadata": {"month": entry["timestamp"][:7]}}
            
            # Append entry
            log_data["entries"].append(entry)
            
            # Write atomically (write to temp, then rename)
            temp_file = self.monthly_log_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            temp_file.replace(self.monthly_log_file)
            
        except Exception as e:
            logger.error(f"Failed to append cost log: {e}", exc_info=True)
    
    def get_job_cost(self, job_id: Optional[str] = None) -> float:
        """
        Get total cost for a job.
        
        Args:
            job_id: Job ID (default: current job_dir)
        
        Returns:
            Total cost in USD
        """
        if job_id is None and self.job_dir:
            job_id = self.job_dir.name
        
        if not job_id:
            logger.warning("No job_id provided and no job_dir set")
            return 0.0
        
        try:
            if not self.monthly_log_file.exists():
                return 0.0
            
            with open(self.monthly_log_file, 'r') as f:
                log_data = json.load(f)
            
            total = sum(
                entry["cost_usd"]
                for entry in log_data.get("entries", [])
                if entry.get("job_id") == job_id
            )
            return total
            
        except Exception as e:
            logger.error(f"Failed to get job cost: {e}", exc_info=True)
            return 0.0
    
    def get_monthly_cost(self, user_id: Optional[int] = None) -> float:
        """
        Get total cost for current month.
        
        Args:
            user_id: User ID (default: self.user_id)
        
        Returns:
            Total cost in USD
        """
        if user_id is None:
            user_id = self.user_id
        
        try:
            if not self.monthly_log_file.exists():
                return 0.0
            
            with open(self.monthly_log_file, 'r') as f:
                log_data = json.load(f)
            
            total = sum(
                entry["cost_usd"]
                for entry in log_data.get("entries", [])
                if entry.get("user_id") == user_id
            )
            return total
            
        except Exception as e:
            logger.error(f"Failed to get monthly cost: {e}", exc_info=True)
            return 0.0
    
    def get_stage_costs(self, job_id: Optional[str] = None) -> Dict[str, float]:
        """
        Get cost breakdown by stage for a job.
        
        Args:
            job_id: Job ID (default: current job_dir)
        
        Returns:
            Dictionary of {stage_name: cost_usd}
        """
        if job_id is None and self.job_dir:
            job_id = self.job_dir.name
        
        if not job_id:
            logger.warning("No job_id provided and no job_dir set")
            return {}
        
        try:
            if not self.monthly_log_file.exists():
                return {}
            
            with open(self.monthly_log_file, 'r') as f:
                log_data = json.load(f)
            
            stage_costs = {}
            for entry in log_data.get("entries", []):
                if entry.get("job_id") == job_id and entry.get("stage"):
                    stage = entry["stage"]
                    stage_costs[stage] = stage_costs.get(stage, 0.0) + entry["cost_usd"]
            
            return stage_costs
            
        except Exception as e:
            logger.error(f"Failed to get stage costs: {e}", exc_info=True)
            return {}
    
    def check_budget_alerts(self, user_id: Optional[int] = None) -> List[str]:
        """
        Check budget thresholds and return alerts.
        
        Args:
            user_id: User ID (default: self.user_id)
        
        Returns:
            List of alert messages (empty if no alerts)
        """
        if user_id is None:
            user_id = self.user_id
        
        alerts = []
        
        try:
            # Load user budget from profile
            budget_limit, alert_threshold = self._load_user_budget(user_id)
            if budget_limit <= 0:
                return []  # Budget not configured
            
            # Get current monthly spend
            current_spend = self.get_monthly_cost(user_id)
            percent_used = (current_spend / budget_limit) * 100
            
            # Check thresholds
            if percent_used >= 100:
                alerts.append(
                    f"🚨 CRITICAL: Budget limit reached! "
                    f"${current_spend:.2f} / ${budget_limit:.2f} ({percent_used:.1f}%)"
                )
            elif percent_used >= alert_threshold:
                remaining = budget_limit - current_spend
                alerts.append(
                    f"⚠️  WARNING: Budget threshold reached! "
                    f"${current_spend:.2f} / ${budget_limit:.2f} ({percent_used:.1f}%) "
                    f"| Remaining: ${remaining:.2f}"
                )
            
        except Exception as e:
            logger.error(f"Failed to check budget alerts: {e}", exc_info=True)
        
        return alerts
    
    def is_over_budget(self, user_id: Optional[int] = None) -> bool:
        """
        Check if user is over budget.
        
        Args:
            user_id: User ID (default: self.user_id)
        
        Returns:
            True if over budget (>=100%), False otherwise
        """
        if user_id is None:
            user_id = self.user_id
        
        try:
            budget_limit, _ = self._load_user_budget(user_id)
            if budget_limit <= 0:
                return False  # No budget configured
            
            current_spend = self.get_monthly_cost(user_id)
            return current_spend >= budget_limit
            
        except Exception as e:
            logger.error(f"Failed to check budget: {e}", exc_info=True)
            return False
    
    def _load_user_budget(self, user_id: int) -> Tuple[float, float]:
        """
        Load user budget from profile.
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (budget_limit_usd, alert_threshold_percent)
        """
        try:
            # Load user profile
            from shared.user_profile import UserProfile
            profile = UserProfile.load(user_id)
            
            # Get budget configuration
            budget_data = profile.data.get("budget", {})
            budget_limit = float(budget_data.get("monthly_limit_usd", 50.0))
            alert_threshold = float(budget_data.get("alert_threshold_percent", 80))
            
            return budget_limit, alert_threshold
            
        except Exception as e:
            logger.warning(f"Failed to load user budget, using defaults: {e}")
            # Default budget settings
            return 50.0, 80.0
    
    def estimate_cost(
        self,
        service: str,
        model: str,
        tokens_estimate: int
    ) -> float:
        """
        Estimate cost for planned API call.
        
        Args:
            service: Service name
            model: Model name
            tokens_estimate: Estimated tokens (input + output combined)
        
        Returns:
            Estimated cost in USD
        """
        # Use average of input/output pricing
        try:
            pricing = self.pricing_db[service][model]
            avg_rate = (pricing["input_per_1k"] + pricing["output_per_1k"]) / 2
            return (tokens_estimate / 1000) * avg_rate
        except KeyError:
            logger.warning(f"Unknown service/model: {service}/{model}")
            return 0.0
    
    def get_monthly_summary(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get monthly cost summary with breakdown by service/model.
        
        Args:
            user_id: User ID (default: self.user_id)
        
        Returns:
            Dictionary with summary statistics
        """
        if user_id is None:
            user_id = self.user_id
        
        try:
            if not self.monthly_log_file.exists():
                return self._empty_summary()
            
            with open(self.monthly_log_file, 'r') as f:
                log_data = json.load(f)
            
            # Filter entries for user
            entries = [
                e for e in log_data.get("entries", [])
                if e.get("user_id") == user_id
            ]
            
            if not entries:
                return self._empty_summary()
            
            # Aggregate costs
            total_cost = sum(e["cost_usd"] for e in entries)
            total_tokens = sum(e["tokens_total"] for e in entries)
            
            # Breakdown by service
            by_service = {}
            for entry in entries:
                service = entry["service"]
                if service not in by_service:
                    by_service[service] = {"cost": 0.0, "tokens": 0, "calls": 0}
                by_service[service]["cost"] += entry["cost_usd"]
                by_service[service]["tokens"] += entry["tokens_total"]
                by_service[service]["calls"] += 1
            
            # Breakdown by model
            by_model = {}
            for entry in entries:
                model = f"{entry['service']}/{entry['model']}"
                if model not in by_model:
                    by_model[model] = {"cost": 0.0, "tokens": 0, "calls": 0}
                by_model[model]["cost"] += entry["cost_usd"]
                by_model[model]["tokens"] += entry["tokens_total"]
                by_model[model]["calls"] += 1
            
            # Count jobs
            unique_jobs = len(set(e.get("job_id") for e in entries if e.get("job_id")))
            
            return {
                "month": log_data["metadata"]["month"],
                "user_id": user_id,
                "total_cost": round(total_cost, 2),
                "total_tokens": total_tokens,
                "total_calls": len(entries),
                "unique_jobs": unique_jobs,
                "avg_cost_per_job": round(total_cost / unique_jobs, 2) if unique_jobs > 0 else 0.0,
                "by_service": by_service,
                "by_model": by_model,
            }
            
        except Exception as e:
            logger.error(f"Failed to get monthly summary: {e}", exc_info=True)
            return self._empty_summary()
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure."""
        return {
            "month": datetime.now(timezone.utc).strftime("%Y-%m"),
            "user_id": self.user_id,
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_calls": 0,
            "unique_jobs": 0,
            "avg_cost_per_job": 0.0,
            "by_service": {},
            "by_model": {},
        }


def get_cost_tracker(
    job_dir: Optional[Path] = None,
    user_id: int = 1
) -> CostTracker:
    """
    Factory function to get CostTracker instance.
    
    Args:
        job_dir: Path to job directory (optional)
        user_id: User ID
    
    Returns:
        CostTracker instance
    """
    return CostTracker(job_dir=job_dir, user_id=user_id)
