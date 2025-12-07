#!/bin/bash
# Archive historical documentation
# Usage: ./tools/archive-historical-docs.sh
# Generated: 2025-12-07

set -e

echo "📦 Archiving historical documentation..."

# Project root
ROOT="/Users/rpatel/Projects/Active/cp-whisperx-app"
cd "$ROOT"

# Create archive directories
echo "Creating archive directories..."
mkdir -p archive/{completion-reports,test-reports,ad-documents,phase-reports,plans,fixes,status,analysis}

# Track stats
MOVED=0
FAILED=0

# Function to move file
move_file() {
    local file="$1"
    local dest="$2"
    
    if [ -f "$file" ]; then
        mv "$file" "archive/$dest/" 2>/dev/null && {
            echo "  ✓ $file → archive/$dest/"
            ((MOVED++))
        } || {
            echo "  ✗ Failed: $file"
            ((FAILED++))
        }
    fi
}

# Completion Reports (27 files)
echo ""
echo "📦 Moving completion reports..."
move_file "AD-006_IMPLEMENTATION_COMPLETE.md" "completion-reports"
move_file "AD-006_PRECOMMIT_HOOK_COMPLETE.md" "completion-reports"
move_file "AD-006_VALIDATION_COMPLETE.md" "completion-reports"
move_file "AD-010_IMPLEMENTATION_COMPLETE.md" "completion-reports"
move_file "ALIGNMENT_LANGUAGE_FIX_COMPLETE.md" "completion-reports"
move_file "ALL_HIGH_PRIORITY_FIXES_COMPLETE_2025-12-05.md" "completion-reports"
move_file "ASR_PHASE4_COMPLETION_SUMMARY.md" "completion-reports"
move_file "ASR_PHASE5_COMPLETION_SUMMARY.md" "completion-reports"
move_file "ASR_PHASE7_COMPLETION_SUMMARY.md" "completion-reports"
move_file "ASR_TASK_MODE_FIX_COMPLETE.md" "completion-reports"
move_file "CLEANUP_PROGRESS_REPORT.md" "completion-reports"
move_file "COMPLIANCE_AUDIT_2025-12-04.md" "completion-reports"
move_file "DOCUMENTATION_CONSISTENCY_COMPLETE.md" "completion-reports"
move_file "HIGH_PRIORITY_FIXES_COMPLETE_2025-12-05.md" "completion-reports"
move_file "HYBRID_ARCHITECTURE_IMPLEMENTATION_COMPLETE.md" "completion-reports"
move_file "IMPLEMENTATION_COMPLETE_2025-12-04.md" "completion-reports"
move_file "M-001_COMPLETION_SUMMARY.md" "completion-reports"
move_file "NEXT_STEPS_COMPLETE_2025-12-05.md" "completion-reports"
move_file "OPTIONAL_WORK_COMPLETE_2025-12-05.md" "completion-reports"
move_file "OUTPUT_DIRECTORY_RESTRUCTURE_SUMMARY.md" "completion-reports"
move_file "PHASE1_COMPLETION_REPORT.md" "completion-reports"
move_file "PHASE2_COMPLETION_REPORT.md" "completion-reports"
move_file "PHASE4_COMPLETION_SUMMARY.md" "completion-reports"
move_file "PHASE4_FINAL_REPORT.md" "completion-reports"
move_file "SUBTITLE_WORKFLOW_INTEGRATION_COMPLETION_REPORT.md" "completion-reports"
move_file "TASK_10_OUTPUT_DIRECTORY_CLEANUP_COMPLETE.md" "completion-reports"
move_file "TEST_3_SUBTITLE_WORKFLOW_SUCCESS.md" "completion-reports"

# Test Reports (10 files)
echo ""
echo "📦 Moving test reports..."
move_file "E2E_TESTING_SESSION_2025-12-04.md" "test-reports"
move_file "E2E_TEST_ANALYSIS_2025-12-05.md" "test-reports"
move_file "E2E_TEST_EXECUTION_PLAN.md" "test-reports"
move_file "E2E_TEST_SESSION_2025-12-05.md" "test-reports"
move_file "E2E_TEST_SUCCESS_2025-12-05.md" "test-reports"
move_file "JOB_13_FAILURE_ANALYSIS.md" "test-reports"
move_file "TEST_1_FINAL_VALIDATION.md" "test-reports"
move_file "TEST_2A_SPANISH_TRANSLATION_SUMMARY.md" "test-reports"
move_file "TEST_2_ANALYSIS_2025-12-05.md" "test-reports"
move_file "TEST_2_EXECUTION_SUMMARY_2025-12-05.md" "test-reports"
move_file "TEST_2_FINAL_VALIDATION.md" "test-reports"
move_file "TEST_3_SUBTITLE_WORKFLOW_SUMMARY.md" "test-reports"
move_file "TEST1_RERUN_SUCCESS.md" "test-reports"
move_file "test1_summary.md" "test-reports"

# AD Documentation (8 files)
echo ""
echo "📦 Moving AD documents..."
move_file "AD-006_IMPLEMENTATION_GUIDE.md" "ad-documents"
move_file "AD-006_IMPLEMENTATION_SESSION_2025-12-04.md" "ad-documents"
move_file "AD-006_IMPLEMENTATION_SUMMARY.md" "ad-documents"
move_file "AD-006_PROGRESS_REPORT_2025-12-04.md" "ad-documents"
move_file "AD-009_DEVELOPMENT_PHILOSOPHY.md" "ad-documents"
move_file "AD-009_DOCUMENTATION_UPDATE.md" "ad-documents"
move_file "BUG_004_AD-007_SUMMARY.md" "ad-documents"
move_file "M-001_ALIGNMENT_AUDIT_2025-12-06.md" "ad-documents"

# Phase Reports (4 files)
echo ""
echo "📦 Moving phase reports..."
move_file "ASR_MODULARIZATION_SESSION_2025-12-05.md" "phase-reports"
move_file "FILE_NAMING_FIX_SESSION_2025-12-05.md" "phase-reports"
move_file "IMPLEMENTATION_SESSION_FINAL_2025-12-04.md" "phase-reports"

# Plans (8 files)
echo ""
echo "📦 Moving implementation plans..."
move_file "ASR_MODULARIZATION_PLAN.md" "plans"
move_file "ASR_STAGE_REFACTORING_PLAN.md" "plans"
move_file "DOCUMENTATION_MAINTENANCE_PLAN.md" "plans"
move_file "E2E_TEST_EXECUTION_PLAN.md" "plans"
move_file "ROADMAP_CORRECTION_SUMMARY.md" "plans"
move_file "ROADMAP_REALITY_CHECK.md" "plans"
move_file "SUBTITLE_WORKFLOW_INTEGRATION_PLAN.md" "plans"
move_file "TASK_10_OUTPUT_DIRECTORY_CLEANUP_PLAN.md" "plans"
move_file "TRANSLATION_STAGE_REFACTORING_PLAN_NUMERIC.md" "plans"

# Fixes (5 files)
echo ""
echo "📦 Moving fix reports..."
move_file "COMPLIANCE_FIX_SUMMARY_2025-12-04.md" "fixes"
move_file "DEMUCS_FIX_PROPER.md" "fixes"
move_file "DOCUMENTATION_FIX_PROGRESS.md" "fixes"
move_file "LOG_FIXES_2025-12-05.md" "fixes"
move_file "SUBTITLE_WORKFLOW_FIXES_SUMMARY.md" "fixes"

# Status Reports (4 files)
echo ""
echo "📦 Moving status reports..."
move_file "AUDIT_SUMMARY_2025-12-05.md" "status"
move_file "QUICK_STATUS_2025-12-04.md" "status"
move_file "QUICK_STATUS_UPDATE_2025-12-04.md" "status"
move_file "SYSTEM_STATUS_REPORT.md" "status"

# Analysis Documents (11 files)
echo ""
echo "📦 Moving analysis documents..."
move_file "BACKEND_INVESTIGATION.md" "analysis"
move_file "CODEBASE_AUDIT_2025-12-05.md" "analysis"
move_file "DOCUMENTATION_ALIGNMENT_ANALYSIS.md" "analysis"
move_file "DOCUMENTATION_ALIGNMENT_SUMMARY.md" "analysis"
move_file "DOCUMENTATION_INCONSISTENCY_ANALYSIS.md" "analysis"
move_file "DOCUMENTATION_STRATEGY.md" "analysis"
move_file "DOCUMENTATION_UPDATES_SUMMARY_2025-12-05.md" "analysis"
move_file "STAGE_COMPLEXITY_ANALYSIS.md" "analysis"
move_file "SUBTITLE_QUALITY_ANALYSIS.md" "analysis"
move_file "HYBRID_TRANSLATOR_IMPLEMENTATION_SUMMARY.md" "analysis"
move_file "TRANSLATION_QUALITY_ISSUES.md" "analysis"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Archiving complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Files moved: $MOVED"
echo "  Failed:      $FAILED"
echo ""
echo "📁 Archive directories created:"
echo "  - archive/completion-reports/"
echo "  - archive/test-reports/"
echo "  - archive/ad-documents/"
echo "  - archive/phase-reports/"
echo "  - archive/plans/"
echo "  - archive/fixes/"
echo "  - archive/status/"
echo "  - archive/analysis/"
echo ""
echo "Next: Run ./tools/create-archive-readme.sh to generate indexes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
