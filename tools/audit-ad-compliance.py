#!/usr/bin/env python3
"""
AD-006 and AD-007 Compliance Audit Tool

Audits all stages and scripts for compliance with:
- AD-006: Job-specific parameters override system defaults
- AD-007: Consistent shared/ import paths

Usage:
    python3 tools/audit-ad-compliance.py [--fix] [--stage STAGE] [--script SCRIPT]
    
Options:
    --fix           Apply automatic fixes where possible
    --stage STAGE   Audit only specific stage (e.g., 06_whisperx_asr.py)
    --script SCRIPT Audit only specific script
    --verbose       Show detailed analysis
"""

# Standard library
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@dataclass
class ComplianceIssue:
    """Represents a compliance violation"""
    file: Path
    line_number: int
    issue_type: str  # "AD-006" or "AD-007"
    severity: str  # "ERROR", "WARNING", "INFO"
    description: str
    fix_suggestion: str = ""
    auto_fixable: bool = False

class ADComplianceAuditor:
    """Audits code for AD-006 and AD-007 compliance"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[ComplianceIssue] = []
        
    def audit_ad006_stage(self, stage_file: Path) -> List[ComplianceIssue]:
        """
        Audit a stage file for AD-006 compliance.
        
        AD-006: Job-specific parameters override system defaults
        
        Checks for:
        1. job.json reading
        2. Parameter override logic
        3. Logging of parameter source
        """
        issues = []
        
        with open(stage_file, 'r') as f:
            lines = f.readlines()
        
        # Check if stage reads job.json
        has_job_json_read = False
        has_override_logic = False
        has_source_logging = False
        
        for i, line in enumerate(lines, 1):
            # Check for job.json reading
            if 'job.json' in line and ('open' in line or 'Path' in line):
                has_job_json_read = True
            
            # Check for override pattern
            if 'job_data' in line and ('get' in line or '[' in line):
                has_override_logic = True
            
            # Check for source logging (logging where param came from)
            if 'from job' in line.lower() or 'from config' in line.lower():
                has_source_logging = True
        
        # Report issues
        if not has_job_json_read:
            issues.append(ComplianceIssue(
                file=stage_file,
                line_number=1,
                issue_type="AD-006",
                severity="ERROR",
                description="Stage does not read job.json for parameter overrides",
                fix_suggestion="Add job.json reading logic (see whisperx_integration.py lines 1415-1433)",
                auto_fixable=False
            ))
        
        if has_job_json_read and not has_override_logic:
            issues.append(ComplianceIssue(
                file=stage_file,
                line_number=1,
                issue_type="AD-006",
                severity="WARNING",
                description="job.json is read but no override logic found",
                fix_suggestion="Implement parameter override pattern",
                auto_fixable=False
            ))
        
        if not has_source_logging:
            issues.append(ComplianceIssue(
                file=stage_file,
                line_number=1,
                issue_type="AD-006",
                severity="INFO",
                description="Consider logging parameter source (job.json vs system config)",
                fix_suggestion="Add logging: logger.info(f'Using param: {value} (from job.json)')",
                auto_fixable=False
            ))
        
        return issues
    
    def audit_ad007_script(self, script_file: Path) -> List[ComplianceIssue]:
        """
        Audit a script file for AD-007 compliance.
        
        AD-007: Consistent shared/ import paths
        
        Checks for:
        1. Missing "shared." prefix in imports from shared/
        2. Inconsistent import patterns
        """
        issues = []
        
        with open(script_file, 'r') as f:
            lines = f.readlines()
        
        # Pattern for incorrect imports (missing shared. prefix)
        incorrect_patterns = [
            r'^from ([a-z_]+(?:_[a-z]+)*) import',  # from module_name import
            r'^import ([a-z_]+(?:_[a-z]+)*)$',      # import module_name
        ]
        
        # Known shared modules
        shared_modules = {
            'config_loader', 'logger', 'stage_utils', 'manifest',
            'bias_window_generator', 'mps_utils', 'asr_chunker',
            'tmdb_client', 'device_selector', 'stage_order'
        }
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            # Check for incorrect imports
            for pattern in incorrect_patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    module_name = match.group(1)
                    
                    # Check if this is a shared module without prefix
                    if module_name in shared_modules:
                        issues.append(ComplianceIssue(
                            file=script_file,
                            line_number=i,
                            issue_type="AD-007",
                            severity="ERROR",
                            description=f"Import from shared/ missing 'shared.' prefix: {line_stripped}",
                            fix_suggestion=f"Change to: from shared.{module_name} import ...",
                            auto_fixable=True
                        ))
        
        return issues
    
    def audit_all_stages(self) -> None:
        """Audit all stage files for AD-006 compliance"""
        scripts_dir = self.project_root / "scripts"
        stage_files = sorted(scripts_dir.glob("[0-9][0-9]_*.py"))
        
        print(f"\n{'='*80}")
        print(f"AD-006 COMPLIANCE AUDIT: Job-Specific Parameter Overrides")
        print(f"{'='*80}\n")
        
        for stage_file in stage_files:
            print(f"Auditing {stage_file.name}...")
            issues = self.audit_ad006_stage(stage_file)
            self.issues.extend(issues)
            
            if not issues:
                print(f"  ✅ COMPLIANT\n")
            else:
                for issue in issues:
                    print(f"  {issue.severity}: {issue.description}")
                print()
    
    def audit_all_scripts(self) -> None:
        """Audit all scripts for AD-007 compliance"""
        scripts_dir = self.project_root / "scripts"
        script_files = sorted(scripts_dir.glob("*.py"))
        
        print(f"\n{'='*80}")
        print(f"AD-007 COMPLIANCE AUDIT: Consistent shared/ Import Paths")
        print(f"{'='*80}\n")
        
        for script_file in script_files:
            print(f"Auditing {script_file.name}...")
            issues = self.audit_ad007_script(script_file)
            self.issues.extend(issues)
            
            if not issues:
                print(f"  ✅ COMPLIANT\n")
            else:
                for issue in issues:
                    print(f"  Line {issue.line_number}: {issue.severity}: {issue.description}")
                    if issue.fix_suggestion:
                        print(f"    Fix: {issue.fix_suggestion}")
                print()
    
    def generate_report(self) -> Dict[str, any]:
        """Generate compliance report"""
        total_issues = len(self.issues)
        by_severity = {
            'ERROR': [i for i in self.issues if i.severity == 'ERROR'],
            'WARNING': [i for i in self.issues if i.severity == 'WARNING'],
            'INFO': [i for i in self.issues if i.severity == 'INFO']
        }
        by_type = {
            'AD-006': [i for i in self.issues if i.issue_type == 'AD-006'],
            'AD-007': [i for i in self.issues if i.issue_type == 'AD-007']
        }
        
        print(f"\n{'='*80}")
        print(f"COMPLIANCE REPORT")
        print(f"{'='*80}\n")
        
        print(f"Total Issues: {total_issues}")
        print(f"  - ERRORS: {len(by_severity['ERROR'])}")
        print(f"  - WARNINGS: {len(by_severity['WARNING'])}")
        print(f"  - INFO: {len(by_severity['INFO'])}")
        print()
        print(f"By Type:")
        print(f"  - AD-006 (Job Parameters): {len(by_type['AD-006'])}")
        print(f"  - AD-007 (Import Paths): {len(by_type['AD-007'])}")
        print()
        
        # Files with issues
        files_with_issues = {}
        for issue in self.issues:
            file_name = issue.file.name
            if file_name not in files_with_issues:
                files_with_issues[file_name] = []
            files_with_issues[file_name].append(issue)
        
        print(f"Files with Issues ({len(files_with_issues)}):")
        for file_name in sorted(files_with_issues.keys()):
            issues = files_with_issues[file_name]
            error_count = len([i for i in issues if i.severity == 'ERROR'])
            warning_count = len([i for i in issues if i.severity == 'WARNING'])
            print(f"  - {file_name}: {error_count} errors, {warning_count} warnings")
        
        return {
            'total': total_issues,
            'by_severity': {k: len(v) for k, v in by_severity.items()},
            'by_type': {k: len(v) for k, v in by_type.items()},
            'files': files_with_issues
        }
    
    def apply_fixes(self) -> int:
        """Apply automatic fixes where possible"""
        fixes_applied = 0
        
        print(f"\n{'='*80}")
        print(f"APPLYING AUTOMATIC FIXES")
        print(f"{'='*80}\n")
        
        # Group issues by file
        by_file = {}
        for issue in self.issues:
            if issue.auto_fixable:
                if issue.file not in by_file:
                    by_file[issue.file] = []
                by_file[issue.file].append(issue)
        
        for file_path, file_issues in by_file.items():
            print(f"Fixing {file_path.name}...")
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Apply fixes (in reverse line order to preserve line numbers)
            file_issues_sorted = sorted(file_issues, key=lambda x: x.line_number, reverse=True)
            
            for issue in file_issues_sorted:
                if issue.issue_type == 'AD-007':
                    # Fix missing shared. prefix
                    line = lines[issue.line_number - 1]
                    # Extract module name
                    match = re.search(r'from ([a-z_]+(?:_[a-z]+)*) import', line)
                    if match:
                        module_name = match.group(1)
                        fixed_line = line.replace(f'from {module_name} import', f'from shared.{module_name} import')
                        lines[issue.line_number - 1] = fixed_line
                        print(f"  Line {issue.line_number}: Added 'shared.' prefix to {module_name}")
                        fixes_applied += 1
            
            # Write back
            if fixes_applied > 0:
                with open(file_path, 'w') as f:
                    f.writelines(lines)
        
        print(f"\n✅ Applied {fixes_applied} automatic fixes")
        return fixes_applied


def main():
    parser = argparse.ArgumentParser(description='Audit AD-006 and AD-007 compliance')
    parser.add_argument('--fix', action='store_true', help='Apply automatic fixes')
    parser.add_argument('--stage', type=str, help='Audit only specific stage')
    parser.add_argument('--script', type=str, help='Audit only specific script')
    parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    parser.add_argument('--ad006-only', action='store_true', help='Audit only AD-006')
    parser.add_argument('--ad007-only', action='store_true', help='Audit only AD-007')
    
    args = parser.parse_args()
    
    auditor = ADComplianceAuditor(PROJECT_ROOT)
    
    # Run audits
    if not args.ad007_only:
        if args.stage:
            stage_file = PROJECT_ROOT / "scripts" / args.stage
            if stage_file.exists():
                issues = auditor.audit_ad006_stage(stage_file)
                auditor.issues.extend(issues)
            else:
                print(f"ERROR: Stage file not found: {stage_file}")
                return 1
        else:
            auditor.audit_all_stages()
    
    if not args.ad006_only:
        if args.script:
            script_file = PROJECT_ROOT / "scripts" / args.script
            if script_file.exists():
                issues = auditor.audit_ad007_script(script_file)
                auditor.issues.extend(issues)
            else:
                print(f"ERROR: Script file not found: {script_file}")
                return 1
        else:
            auditor.audit_all_scripts()
    
    # Generate report
    report = auditor.generate_report()
    
    # Apply fixes if requested
    if args.fix:
        fixes_applied = auditor.apply_fixes()
        if fixes_applied > 0:
            print(f"\n⚠️  Please review changes and test before committing!")
    
    # Exit code based on errors
    error_count = report['by_severity']['ERROR']
    if error_count > 0:
        print(f"\n❌ FAILED: {error_count} errors found")
        return 1
    else:
        print(f"\n✅ PASSED: No errors found")
        return 0


if __name__ == '__main__':
    sys.exit(main())
