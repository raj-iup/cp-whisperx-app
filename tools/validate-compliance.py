#!/usr/bin/env python3
"""
Logging Compliance Validator for CP-WhisperX-App

Validates that all scripts follow the logging standards.

Usage:
    python tools/validate-compliance.py [OPTIONS]
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ComplianceValidator:
    """Validate logging compliance across all scripts"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = defaultdict(list)
        self.total_scripts = 0
        self.compliant_scripts = 0
        
    def validate_bash_script(self, script_path: Path) -> Tuple[bool, List[str]]:
        """Validate bash script compliance"""
        issues = []
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common-logging.sh source
            if 'common-logging.sh' not in content:
                issues.append("Does not source scripts/common-logging.sh")
            
            # Check for proper logging function usage
            if re.search(r'\becho\s+"', content) and 'log_info' not in content:
                issues.append("Uses echo instead of log_info for messages")
            
            # Check for error handling
            if 'set -euo pipefail' not in content and script_path.name not in ['common-logging.sh']:
                issues.append("Missing 'set -euo pipefail' for error handling")
            
            # Check for shebang
            if not content.startswith('#!/usr/bin/env bash') and not content.startswith('#!/bin/bash'):
                issues.append("Missing or incorrect shebang")
                
        except Exception as e:
            issues.append(f"Could not parse script: {e}")
        
        return (len(issues) == 0, issues)
    
    def validate_powershell_script(self, script_path: Path) -> Tuple[bool, List[str]]:
        """Validate PowerShell script compliance"""
        issues = []
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common-logging.ps1 source
            if 'common-logging.ps1' not in content:
                issues.append("Does not source scripts/common-logging.ps1")
            
            # Check for proper logging function usage
            if re.search(r'Write-Host\s+"', content) and 'Write-LogInfo' not in content:
                issues.append("Uses Write-Host instead of Write-LogInfo")
            
            # Check for shebang
            if not content.startswith('#!/usr/bin/env pwsh') and not content.startswith('#Requires -Version'):
                issues.append("Missing PowerShell header")
                
        except Exception as e:
            issues.append(f"Could not parse script: {e}")
        
        return (len(issues) == 0, issues)
    
    def validate_python_script(self, script_path: Path) -> Tuple[bool, List[str]]:
        """Validate Python script compliance"""
        issues = []
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for logger import
            if 'from shared.logger import' not in content and 'shared/logger.py' not in str(script_path):
                # Check if it's a utility that doesn't need logging
                if script_path.name not in ['__init__.py', 'config.py']:
                    issues.append("Does not import from shared.logger")
            
            # Check for shebang
            if not content.startswith('#!/usr/bin/env python'):
                issues.append("Missing Python shebang")
                
        except Exception as e:
            issues.append(f"Could not parse script: {e}")
        
        return (len(issues) == 0, issues)
    
    def validate_all_scripts(self):
        """Validate all scripts in the project"""
        print("Starting compliance validation...")
        print("")
        
        # Find all bash scripts
        bash_scripts = [
            *self.project_root.glob("*.sh"),
            *self.project_root.glob("scripts/*.sh"),
            *self.project_root.glob("tools/*.sh")
        ]
        
        # Find all PowerShell scripts
        ps_scripts = [
            *self.project_root.glob("*.ps1"),
            *self.project_root.glob("scripts/*.ps1"),
            *self.project_root.glob("tools/*.ps1")
        ]
        
        # Find all Python scripts
        py_scripts = [
            *self.project_root.glob("scripts/*.py"),
            *self.project_root.glob("tools/*.py"),
            *self.project_root.glob("shared/*.py")
        ]
        
        # Validate bash scripts
        print("=" * 70)
        print("BASH SCRIPTS")
        print("=" * 70)
        
        for script in bash_scripts:
            self.total_scripts += 1
            compliant, issues = self.validate_bash_script(script)
            
            if compliant:
                self.compliant_scripts += 1
                print(f"✅ {script.name}")
            else:
                print(f"⚠️  {script.name}")
                for issue in issues:
                    print(f"    → {issue}")
                self.results['bash'].append((script.name, issues))
        
        print("")
        
        # Validate PowerShell scripts
        print("=" * 70)
        print("POWERSHELL SCRIPTS")
        print("=" * 70)
        
        for script in ps_scripts:
            self.total_scripts += 1
            compliant, issues = self.validate_powershell_script(script)
            
            if compliant:
                self.compliant_scripts += 1
                print(f"✅ {script.name}")
            else:
                print(f"⚠️  {script.name}")
                for issue in issues:
                    print(f"    → {issue}")
                self.results['powershell'].append((script.name, issues))
        
        print("")
        
        # Validate Python scripts
        print("=" * 70)
        print("PYTHON SCRIPTS")
        print("=" * 70)
        
        for script in py_scripts:
            self.total_scripts += 1
            compliant, issues = self.validate_python_script(script)
            
            if compliant:
                self.compliant_scripts += 1
                print(f"✅ {script.name}")
            else:
                print(f"⚠️  {script.name}")
                for issue in issues:
                    print(f"    → {issue}")
                self.results['python'].append((script.name, issues))
        
        print("")
        
    def generate_report(self) -> str:
        """Generate compliance report"""
        compliance_rate = (self.compliant_scripts / self.total_scripts * 100) if self.total_scripts > 0 else 0
        
        report = []
        report.append("=" * 70)
        report.append("LOGGING COMPLIANCE REPORT")
        report.append("=" * 70)
        report.append(f"Total Scripts: {self.total_scripts}")
        report.append(f"Compliant: {self.compliant_scripts}")
        report.append(f"Non-Compliant: {self.total_scripts - self.compliant_scripts}")
        report.append(f"Compliance Rate: {compliance_rate:.1f}%")
        report.append("")
        
        if self.total_scripts - self.compliant_scripts == 0:
            report.append("🎉 ALL SCRIPTS ARE COMPLIANT!")
        else:
            report.append("NON-COMPLIANT SCRIPTS:")
            report.append("-" * 70)
            
            for lang, scripts in self.results.items():
                if scripts:
                    report.append(f"\n{lang.upper()}:")
                    for script_name, issues in scripts:
                        report.append(f"  • {script_name}")
                        for issue in issues:
                            report.append(f"      - {issue}")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Main entry point"""
    validator = ComplianceValidator(PROJECT_ROOT)
    
    # Validate all scripts
    validator.validate_all_scripts()
    
    # Generate report
    report = validator.generate_report()
    print(report)
    
    # Exit with appropriate code
    if validator.compliant_scripts == validator.total_scripts:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
