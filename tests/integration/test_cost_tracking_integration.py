#!/usr/bin/env python3
"""
Integration test for cost tracking in stages.

Tests that cost tracking is properly integrated in:
- Stage 06 (WhisperX ASR)
- Stage 10 (Translation)
- Stage 13 (AI Summarization)
"""

# Standard library
import sys
import json
import tempfile
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local
from shared.cost_tracker import CostTracker

def test_cost_tracker_import():
    """Test that cost tracker can be imported by stages."""
    print("\n🧪 Test 1: Import CostTracker")
    try:
        from shared.cost_tracker import CostTracker
        print("   ✅ CostTracker imported successfully")
        return True
    except ImportError as e:
        print(f"   ❌ Failed to import: {e}")
        return False

def test_stage_06_integration():
    """Test Stage 06 has cost tracking code."""
    print("\n🧪 Test 2: Stage 06 Integration")
    try:
        with open("scripts/06_whisperx_asr.py", 'r') as f:
            content = f.read()
        
        has_import = "from shared.cost_tracker import CostTracker" in content
        has_usage = "tracker.log_usage" in content
        has_cost_display = "Stage cost" in content
        
        if has_import and has_usage and has_cost_display:
            print("   ✅ Stage 06 has cost tracking integrated")
            return True
        else:
            print(f"   ❌ Stage 06 missing cost tracking:")
            print(f"      - Import: {has_import}")
            print(f"      - Usage: {has_usage}")
            print(f"      - Display: {has_cost_display}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_stage_10_integration():
    """Test Stage 10 has cost tracking code."""
    print("\n🧪 Test 3: Stage 10 Integration")
    try:
        with open("scripts/10_translation.py", 'r') as f:
            content = f.read()
        
        has_import = "from shared.cost_tracker import CostTracker" in content
        has_usage = "tracker.log_usage" in content
        has_cost_display = "Stage cost" in content
        
        if has_import and has_usage and has_cost_display:
            print("   ✅ Stage 10 has cost tracking integrated")
            return True
        else:
            print(f"   ❌ Stage 10 missing cost tracking:")
            print(f"      - Import: {has_import}")
            print(f"      - Usage: {has_usage}")
            print(f"      - Display: {has_cost_display}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_stage_13_integration():
    """Test Stage 13 has cost tracking code."""
    print("\n🧪 Test 4: Stage 13 Integration")
    try:
        with open("scripts/13_ai_summarization.py", 'r') as f:
            content = f.read()
        
        has_import = "from shared.cost_tracker import CostTracker" in content
        has_usage = "tracker.log_usage" in content
        has_cost_display = "Stage cost" in content
        has_budget_check = "check_budget_alerts" in content
        
        if has_import and has_usage and has_cost_display and has_budget_check:
            print("   ✅ Stage 13 has cost tracking integrated")
            return True
        else:
            print(f"   ❌ Stage 13 missing cost tracking:")
            print(f"      - Import: {has_import}")
            print(f"      - Usage: {has_usage}")
            print(f"      - Display: {has_cost_display}")
            print(f"      - Budget check: {has_budget_check}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_cost_tracker_basic_functionality():
    """Test basic cost tracker functionality."""
    print("\n🧪 Test 5: Basic Cost Tracker Functionality")
    try:
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())
        job_dir = temp_dir / "test-job"
        job_dir.mkdir()
        
        # Initialize tracker
        tracker = CostTracker(job_dir=job_dir, user_id=1, cost_storage_path=temp_dir)
        
        # Test local model (should cost $0)
        cost = tracker.log_usage(
            service="local",
            model="mlx-whisper",
            tokens_input=0,
            tokens_output=0,
            stage="06_whisperx_asr"
        )
        
        if cost == 0.0:
            print("   ✅ Local model cost tracking works ($0)")
        else:
            print(f"   ❌ Local model cost incorrect: ${cost}")
            return False
        
        # Test OpenAI model
        cost = tracker.log_usage(
            service="openai",
            model="gpt-4o",
            tokens_input=1000,
            tokens_output=200,
            stage="13_ai_summarization"
        )
        
        if cost > 0:
            print(f"   ✅ OpenAI cost tracking works (${cost:.4f})")
        else:
            print("   ❌ OpenAI cost tracking failed")
            return False
        
        # Test job cost retrieval
        job_cost = tracker.get_job_cost(job_dir.name)
        if abs(job_cost - cost) < 0.0001:  # Floating point comparison
            print(f"   ✅ Job cost retrieval works (${job_cost:.4f})")
        else:
            print(f"   ❌ Job cost mismatch: expected ${cost:.4f}, got ${job_cost:.4f}")
            return False
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    print("="*70)
    print("COST TRACKING INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        test_cost_tracker_import,
        test_stage_06_integration,
        test_stage_10_integration,
        test_stage_13_integration,
        test_cost_tracker_basic_functionality,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All integration tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
