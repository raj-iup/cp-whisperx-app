#!/usr/bin/env python3
"""
Unit tests for cost tracking module.

Tests:
- Cost computation accuracy
- Token counting logic
- Budget threshold detection
- Monthly aggregation
- Job cost tracking

Coverage target: ≥80%
Related: TRD-2025-12-10-04-cost-tracking
"""

# Standard library
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# Third-party
import pytest

# Local
from shared.cost_tracker import CostTracker, PRICING_DATABASE


class TestCostTracker:
    """Test CostTracker class."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary cost storage directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_job_dir(self):
        """Create temporary job directory."""
        temp_dir = Path(tempfile.mkdtemp())
        job_dir = temp_dir / "job-20251210-test-0001"
        job_dir.mkdir()
        yield job_dir
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_init_with_job_dir(self, temp_job_dir, temp_storage):
        """Test initialization with job directory."""
        tracker = CostTracker(
            job_dir=temp_job_dir,
            user_id=1,
            cost_storage_path=temp_storage
        )
        assert tracker.job_dir == temp_job_dir
        assert tracker.user_id == 1
        assert tracker.cost_storage_path == temp_storage
        assert temp_storage.exists()
    
    def test_init_without_job_dir(self, temp_storage):
        """Test initialization without job directory."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        assert tracker.job_dir is None
        assert tracker.user_id == 1
    
    def test_compute_cost_openai_gpt4o(self, temp_storage):
        """Test OpenAI GPT-4o cost computation."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # GPT-4o: $0.0025/1K input, $0.01/1K output
        cost = tracker._compute_cost("openai", "gpt-4o", 1000, 200)
        
        expected = (1000/1000 * 0.0025) + (200/1000 * 0.01)
        assert abs(cost - expected) < 0.0001
        assert abs(cost - 0.0045) < 0.0001
    
    def test_compute_cost_openai_gpt4(self, temp_storage):
        """Test OpenAI GPT-4 cost computation."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # GPT-4: $0.03/1K input, $0.06/1K output
        cost = tracker._compute_cost("openai", "gpt-4", 1000, 200)
        
        expected = (1000/1000 * 0.03) + (200/1000 * 0.06)
        assert abs(cost - expected) < 0.0001
        assert abs(cost - 0.042) < 0.0001
    
    def test_compute_cost_gemini(self, temp_storage):
        """Test Gemini cost computation."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # Gemini: $0.00025/1K tokens (combined)
        cost = tracker._compute_cost("gemini", "gemini-1.5-pro", 1000, 200)
        
        expected = (1000 + 200) / 1000 * 0.00025
        assert abs(cost - expected) < 0.00001
        assert abs(cost - 0.0003) < 0.00001
    
    def test_compute_cost_local_model_zero_cost(self, temp_storage):
        """Test local processing (MLX, IndicTrans2) has zero cost."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        cost_mlx = tracker._compute_cost("local", "mlx-whisper", 0, 0)
        assert cost_mlx == 0.0
        
        cost_indic = tracker._compute_cost("local", "indictrans2-local", 0, 0)
        assert cost_indic == 0.0
    
    def test_compute_cost_unknown_service(self, temp_storage):
        """Test unknown service returns zero cost."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        cost = tracker._compute_cost("unknown", "model", 1000, 200)
        assert cost == 0.0
    
    def test_log_usage_creates_entry(self, temp_job_dir, temp_storage):
        """Test logging usage creates log entry."""
        tracker = CostTracker(
            job_dir=temp_job_dir,
            user_id=1,
            cost_storage_path=temp_storage
        )
        
        cost = tracker.log_usage(
            service="openai",
            model="gpt-4o",
            tokens_input=1000,
            tokens_output=200,
            stage="13_ai_summarization"
        )
        
        assert cost > 0
        assert tracker.monthly_log_file.exists()
        
        # Verify log entry
        with open(tracker.monthly_log_file, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data["entries"]) == 1
        entry = log_data["entries"][0]
        assert entry["service"] == "openai"
        assert entry["model"] == "gpt-4o"
        assert entry["tokens_input"] == 1000
        assert entry["tokens_output"] == 200
        assert entry["tokens_total"] == 1200
        assert entry["stage"] == "13_ai_summarization"
        assert entry["user_id"] == 1
        assert entry["job_id"] == temp_job_dir.name
    
    def test_log_usage_multiple_entries(self, temp_job_dir, temp_storage):
        """Test logging multiple usage entries."""
        tracker = CostTracker(
            job_dir=temp_job_dir,
            user_id=1,
            cost_storage_path=temp_storage
        )
        
        # Log multiple entries
        tracker.log_usage("openai", "gpt-4o", 1000, 200)
        tracker.log_usage("gemini", "gemini-1.5-pro", 500, 100)
        tracker.log_usage("local", "mlx-whisper", 0, 0)
        
        # Verify all entries logged
        with open(tracker.monthly_log_file, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data["entries"]) == 3
    
    def test_get_job_cost(self, temp_job_dir, temp_storage):
        """Test job cost aggregation."""
        tracker = CostTracker(
            job_dir=temp_job_dir,
            user_id=1,
            cost_storage_path=temp_storage
        )
        
        # Log multiple entries for same job
        cost1 = tracker.log_usage("openai", "gpt-4o", 1000, 200)
        cost2 = tracker.log_usage("gemini", "gemini-1.5-pro", 500, 100)
        
        total = tracker.get_job_cost(temp_job_dir.name)
        expected = cost1 + cost2
        assert abs(total - expected) < 0.0001
    
    def test_get_job_cost_no_logs(self, temp_job_dir, temp_storage):
        """Test get_job_cost returns 0 when no logs exist."""
        tracker = CostTracker(
            job_dir=temp_job_dir,
            user_id=1,
            cost_storage_path=temp_storage
        )
        
        total = tracker.get_job_cost(temp_job_dir.name)
        assert total == 0.0
    
    def test_get_monthly_cost(self, temp_storage):
        """Test monthly cost aggregation."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # Log multiple entries
        cost1 = tracker.log_usage("openai", "gpt-4o", 1000, 200)
        cost2 = tracker.log_usage("gemini", "gemini-1.5-pro", 500, 100)
        cost3 = tracker.log_usage("openai", "gpt-4", 500, 100)
        
        monthly = tracker.get_monthly_cost(user_id=1)
        expected = cost1 + cost2 + cost3
        assert abs(monthly - expected) < 0.0001
    
    def test_get_monthly_cost_multiple_users(self, temp_storage):
        """Test monthly cost per user (isolation)."""
        tracker1 = CostTracker(user_id=1, cost_storage_path=temp_storage)
        tracker2 = CostTracker(user_id=2, cost_storage_path=temp_storage)
        
        # User 1 usage
        cost1 = tracker1.log_usage("openai", "gpt-4o", 1000, 200)
        cost2 = tracker1.log_usage("gemini", "gemini-1.5-pro", 500, 100)
        
        # User 2 usage
        cost3 = tracker2.log_usage("openai", "gpt-4", 500, 100)
        
        # Verify user isolation
        user1_total = tracker1.get_monthly_cost(user_id=1)
        user2_total = tracker2.get_monthly_cost(user_id=2)
        
        assert abs(user1_total - (cost1 + cost2)) < 0.0001
        assert abs(user2_total - cost3) < 0.0001
    
    def test_get_stage_costs(self, temp_job_dir, temp_storage):
        """Test stage cost breakdown."""
        tracker = CostTracker(
            job_dir=temp_job_dir,
            user_id=1,
            cost_storage_path=temp_storage
        )
        
        # Log costs for different stages
        cost1 = tracker.log_usage(
            "openai", "gpt-4o", 1000, 200,
            stage="06_whisperx_asr"
        )
        cost2 = tracker.log_usage(
            "gemini", "gemini-1.5-pro", 500, 100,
            stage="13_ai_summarization"
        )
        cost3 = tracker.log_usage(
            "openai", "gpt-4o", 500, 100,
            stage="13_ai_summarization"
        )
        
        stage_costs = tracker.get_stage_costs(temp_job_dir.name)
        
        assert "06_whisperx_asr" in stage_costs
        assert "13_ai_summarization" in stage_costs
        assert abs(stage_costs["06_whisperx_asr"] - cost1) < 0.0001
        assert abs(stage_costs["13_ai_summarization"] - (cost2 + cost3)) < 0.0001
    
    def test_budget_alert_80_percent(self, temp_storage):
        """Test budget alert at 80% threshold."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # Directly create log with $40 usage (80% of $50 budget)
        log_data = {
            "entries": [{
                "timestamp": datetime.now().isoformat(),
                "user_id": 1,
                "job_id": None,
                "service": "openai",
                "model": "gpt-4o",
                "tokens_input": 1000,
                "tokens_output": 200,
                "tokens_total": 1200,
                "cost_usd": 40.0,  # Exactly 80% of $50
                "stage": None,
            }],
            "metadata": {"month": datetime.now().strftime("%Y-%m")}
        }
        
        with open(tracker.monthly_log_file, 'w') as f:
            json.dump(log_data, f)
        
        alerts = tracker.check_budget_alerts(user_id=1)
        assert len(alerts) >= 1
        assert "WARNING" in alerts[0] or "80" in alerts[0]
    
    def test_budget_alert_100_percent(self, temp_storage):
        """Test budget alert at 100% threshold."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # Directly create log with $50 usage (100% of $50 budget)
        log_data = {
            "entries": [{
                "timestamp": datetime.now().isoformat(),
                "user_id": 1,
                "job_id": None,
                "service": "openai",
                "model": "gpt-4o",
                "tokens_input": 1000,
                "tokens_output": 200,
                "tokens_total": 1200,
                "cost_usd": 50.0,  # Exactly 100% of $50
                "stage": None,
            }],
            "metadata": {"month": datetime.now().strftime("%Y-%m")}
        }
        
        with open(tracker.monthly_log_file, 'w') as f:
            json.dump(log_data, f)
        
        alerts = tracker.check_budget_alerts(user_id=1)
        assert len(alerts) >= 1
        # Should have critical alert
        assert any("CRITICAL" in alert or "100" in alert for alert in alerts)
    
    def test_is_over_budget(self, temp_storage):
        """Test is_over_budget check."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # Start under budget
        assert not tracker.is_over_budget(user_id=1)
        
        # Create log with over $50 usage
        log_data = {
            "entries": [{
                "timestamp": datetime.now().isoformat(),
                "user_id": 1,
                "job_id": None,
                "service": "openai",
                "model": "gpt-4o",
                "tokens_input": 1000,
                "tokens_output": 200,
                "tokens_total": 1200,
                "cost_usd": 51.0,  # Over budget
                "stage": None,
            }],
            "metadata": {"month": datetime.now().strftime("%Y-%m")}
        }
        
        with open(tracker.monthly_log_file, 'w') as f:
            json.dump(log_data, f)
        
        assert tracker.is_over_budget(user_id=1)
    
    def test_estimate_cost(self, temp_storage):
        """Test cost estimation."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # Estimate GPT-4o cost
        estimate = tracker.estimate_cost("openai", "gpt-4o", 1200)
        
        # Average rate: (0.0025 + 0.01) / 2 = 0.00625 per 1K
        expected = (1200 / 1000) * 0.00625
        assert abs(estimate - expected) < 0.0001
    
    def test_get_monthly_summary(self, temp_storage):
        """Test monthly summary generation."""
        job_dir = temp_storage / "job-test"
        job_dir.mkdir()
        tracker = CostTracker(job_dir=job_dir, user_id=1, cost_storage_path=temp_storage)
        
        # Log some usage
        cost1 = tracker.log_usage("openai", "gpt-4o", 1000, 200, stage="06_whisperx_asr")
        cost2 = tracker.log_usage("gemini", "gemini-1.5-pro", 500, 100, stage="13_ai_summarization")
        
        summary = tracker.get_monthly_summary(user_id=1)
        
        assert summary["user_id"] == 1
        # Verify costs were actually computed
        assert cost1 > 0
        assert cost2 > 0
        # Summary should reflect logged costs
        expected_total = round(cost1 + cost2, 2)
        assert summary["total_cost"] == expected_total, f"Expected {expected_total}, got {summary['total_cost']}"
        assert summary["total_tokens"] == 1800
        assert summary["total_calls"] == 2
        assert summary["unique_jobs"] == 1
        assert "openai" in summary["by_service"]
        assert "gemini" in summary["by_service"]
        assert "openai/gpt-4o" in summary["by_model"]
        assert "gemini/gemini-1.5-pro" in summary["by_model"]
    
    def test_log_usage_with_metadata(self, temp_job_dir, temp_storage):
        """Test logging usage with custom metadata."""
        tracker = CostTracker(
            job_dir=temp_job_dir,
            user_id=1,
            cost_storage_path=temp_storage
        )
        
        metadata = {
            "workflow": "subtitle",
            "media_duration": 7200,
            "quality": "high"
        }
        
        tracker.log_usage(
            "openai", "gpt-4o", 1000, 200,
            metadata=metadata
        )
        
        # Verify metadata stored
        with open(tracker.monthly_log_file, 'r') as f:
            log_data = json.load(f)
        
        entry = log_data["entries"][0]
        assert "metadata" in entry
        assert entry["metadata"] == metadata
    
    def test_pricing_database_completeness(self):
        """Test pricing database has all required services."""
        assert "openai" in PRICING_DATABASE
        assert "gemini" in PRICING_DATABASE
        assert "azure" in PRICING_DATABASE
        assert "whisperx" in PRICING_DATABASE
        assert "indictrans2" in PRICING_DATABASE
        assert "local" in PRICING_DATABASE
        
        # Check OpenAI models
        assert "gpt-4" in PRICING_DATABASE["openai"]
        assert "gpt-4o" in PRICING_DATABASE["openai"]
        assert "gpt-4-turbo" in PRICING_DATABASE["openai"]
        assert "gpt-3.5-turbo" in PRICING_DATABASE["openai"]
    
    def test_atomic_log_writes(self, temp_storage):
        """Test log writes are atomic (write-then-rename)."""
        tracker = CostTracker(user_id=1, cost_storage_path=temp_storage)
        
        # Log usage
        tracker.log_usage("openai", "gpt-4o", 1000, 200)
        
        # Verify no .tmp files left behind
        tmp_files = list(temp_storage.glob("*.tmp"))
        assert len(tmp_files) == 0
        
        # Verify JSON file exists and is valid
        assert tracker.monthly_log_file.exists()
        with open(tracker.monthly_log_file, 'r') as f:
            data = json.load(f)  # Should not raise JSONDecodeError


class TestCostTrackerIntegration:
    """Integration tests for cost tracking."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary cost storage directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_multi_job_cost_tracking(self, temp_storage):
        """Test tracking costs across multiple jobs."""
        job1_dir = temp_storage / "job-001"
        job2_dir = temp_storage / "job-002"
        job1_dir.mkdir()
        job2_dir.mkdir()
        
        tracker1 = CostTracker(job_dir=job1_dir, user_id=1, cost_storage_path=temp_storage)
        tracker2 = CostTracker(job_dir=job2_dir, user_id=1, cost_storage_path=temp_storage)
        
        # Job 1 costs
        cost1 = tracker1.log_usage("openai", "gpt-4o", 1000, 200)
        
        # Job 2 costs
        cost2 = tracker2.log_usage("gemini", "gemini-1.5-pro", 500, 100)
        
        # Verify job isolation
        assert abs(tracker1.get_job_cost("job-001") - cost1) < 0.0001
        assert abs(tracker2.get_job_cost("job-002") - cost2) < 0.0001
        
        # Verify monthly aggregate
        monthly = tracker1.get_monthly_cost(user_id=1)
        assert abs(monthly - (cost1 + cost2)) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
