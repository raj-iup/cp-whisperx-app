#!/usr/bin/env python3
"""
Automated compliance checker for DEVELOPER_STANDARDS.md
Validates Python files against project coding standards.

Usage:
    ./scripts/validate-compliance.py <file.py>
    ./scripts/validate-compliance.py scripts/*.py
    ./scripts/validate-compliance.py --strict scripts/*.py  # Exit 1 on violations
    ./scripts/validate-compliance.py --staged  # Check staged files only
"""

# Standard library
import argparse
import ast
import hashlib
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Local
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.logger import get_logger
from shared.config import load_config

# Initialize logger and config
logger = get_logger(__name__)
config = load_config()

# Colors for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ComplianceViolation:
    """Represents a compliance violation."""
    
    def __init__(self, rule: str, severity: str, line: int, message: str, section: str) -> None:
        """Initialize a compliance violation.
        
        Args:
            rule: The rule that was violated
            severity: Severity level ('critical', 'error', 'warning')
            line: Line number of violation
            message: Violation description
            section: Section reference (e.g., '§ 2.3')
        """
        self.rule = rule
        self.severity = severity  # 'critical', 'error', 'warning'
        self.line = line
        self.message = message
        self.section = section  # § reference
    
    def __str__(self) -> str:
        """Format violation as colored string for terminal output."""
        color = RED if self.severity == 'critical' else YELLOW if self.severity == 'warning' else RED
        return f"{color}Line {self.line}: [{self.severity.upper()}] {self.rule}{RESET}\n  {self.message} (See {self.section})"


class ComplianceChecker:
    """Checks Python files for compliance with DEVELOPER_STANDARDS.md"""
    
    # Files that have acceptable exceptions to rules
    EXCEPTIONS = {
        'shared/config.py': {
            'Config Access': 'Core config module must use os.getenv() - circular dependency'
        },
        'scripts/validate-compliance.py': {
            'Config Access': 'Validator checks for os.getenv/os.environ patterns in code',
            'Logger Usage': 'Validator uses print() in docstrings as examples'
        }
    }
    
    def __init__(self, file_path: Path) -> None:
        """Initialize compliance checker for a file.
        
        Args:
            file_path: Path to Python file to check
        """
        self.file_path = file_path
        self.violations: List[ComplianceViolation] = []
        self.content = ""
        self.lines = []
        self.tree = None
        
    def load_file(self) -> bool:
        """Load and parse the Python file."""
        try:
            self.content = self.file_path.read_text(encoding='utf-8')
            self.lines = self.content.split('\n')
            self.tree = ast.parse(self.content, filename=str(self.file_path))
            return True
        except SyntaxError as e:
            # CLI output: Must use stdout for user-facing messages
            sys.stdout.write(f"{RED}Syntax error in {self.file_path}: {e}{RESET}\n")
            logger.error(f"Syntax error in {self.file_path}: {e}", exc_info=True)
            return False
        except Exception as e:
            # CLI output: Must use stdout for user-facing messages
            sys.stdout.write(f"{RED}Error loading {self.file_path}: {e}{RESET}\n")
            logger.error(f"Error loading {self.file_path}: {e}", exc_info=True)
            return False
    
    def check_all(self) -> List[ComplianceViolation]:
        """Run all compliance checks."""
        if not self.load_file():
            return []
        
        # Priority 1: Logger usage (60% baseline violation)
        self.check_print_statements()
        self.check_logger_import()
        
        # Priority 2: Import organization (100% baseline violation)
        self.check_import_organization()
        
        # Critical patterns
        self.check_stageio_pattern()
        self.check_config_usage()
        self.check_stage_directory_usage()
        
        # Code quality
        self.check_type_hints()
        self.check_docstrings()
        self.check_error_handling()
        
        return self.violations
    
    def check_print_statements(self) -> None:
        """Check for print() usage instead of logger (§ 2.3)"""
        # Skip if this file has an exception for Logger Usage
        relative_path = str(self.file_path).replace(str(Path.cwd()) + '/', '')
        if relative_path in self.EXCEPTIONS and 'Logger Usage' in self.EXCEPTIONS[relative_path]:
            return
        
        for i, line in enumerate(self.lines, 1):
            # Skip comments and debug statements
            if line.strip().startswith('#'):
                continue
            if '# debug' in line.lower() or '# DEBUG' in line:
                continue
                
            # Check for print() calls
            if re.search(r'\bprint\s*\(', line):
                self.violations.append(ComplianceViolation(
                    rule="Logger Usage",
                    severity="critical",
                    line=i,
                    message="Use logger.info() instead of print() - 60% baseline violation",
                    section="§ 2.3"
                ))
    
    def check_logger_import(self) -> None:
        """Check if logger is imported when needed"""
        has_logging_call = any('logger.' in line for line in self.lines)
        
        # Check for logger import anywhere in the file (simpler and more reliable)
        # This handles organized imports, multi-line docstrings, etc.
        content = '\n'.join(self.lines)
        has_logger_import = (
            'from shared.logger import get_logger' in content or
            'io.get_stage_logger' in content or
            'logger = get_logger' in content
        )
        
        if has_logging_call and not has_logger_import:
            self.violations.append(ComplianceViolation(
                rule="Logger Import",
                severity="error",
                line=1,
                message="Logger used but not imported. Add: from shared.logger import get_logger",
                section="§ 2.3"
            ))
    
    def check_import_organization(self) -> None:
        """Check import organization: Standard/Third-party/Local (§ 6.1)"""
        import_lines = []
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if not stripped.startswith('from __future__'):
                    import_lines.append((i, stripped))
            elif import_lines and stripped and not stripped.startswith('#'):
                break  # Stop at first non-import, non-blank line
        
        if len(import_lines) < 2:
            return  # Not enough imports to check organization
        
        # Check for group separators (blank lines)
        import_text = '\n'.join(self.lines[:max(line[0] for line in import_lines)])
        
        # Look for standard lib, third-party, and local imports
        has_standard = any(
            any(lib in imp[1] for lib in ['import os', 'import sys', 'from pathlib', 'from typing'])
            for imp in import_lines
        )
        has_local = any('from shared.' in imp[1] or 'from scripts.' in imp[1] for imp in import_lines)
        
        # If we have multiple types, we should have blank lines
        if (has_standard and has_local) or len(import_lines) > 5:
            if '\n\n' not in import_text:
                first_import_line = import_lines[0][0]
                self.violations.append(ComplianceViolation(
                    rule="Import Organization",
                    severity="warning",
                    line=first_import_line,
                    message="Imports should be organized: Standard/Third-party/Local with blank lines - 100% baseline violation",
                    section="§ 6.1"
                ))
    
    def check_stageio_pattern(self) -> None:
        """Check StageIO usage in stage files (§ 2.6)"""
        # Check if this looks like a stage file
        is_stage = any('def run_' in line and 'stage' in line.lower() for line in self.lines)
        
        if is_stage:
            has_stageio = any('StageIO' in line for line in self.lines)
            
            if has_stageio:
                # Check for enable_manifest=True
                has_manifest = any('enable_manifest=True' in line for line in self.lines)
                if not has_manifest:
                    for i, line in enumerate(self.lines, 1):
                        if 'StageIO(' in line:
                            self.violations.append(ComplianceViolation(
                                rule="StageIO Manifest",
                                severity="critical",
                                line=i,
                                message="StageIO must include enable_manifest=True",
                                section="§ 2.6"
                            ))
                            break
                
                # Check for io.get_stage_logger()
                has_stage_logger = any('get_stage_logger()' in line for line in self.lines)
                if not has_stage_logger:
                    self.violations.append(ComplianceViolation(
                        rule="Stage Logger",
                        severity="critical",
                        line=1,
                        message="Stage must use io.get_stage_logger() for logging",
                        section="§ 2.3"
                    ))
                
                # Check for manifest.add_input/add_output
                has_add_input = any('manifest.add_input' in line for line in self.lines)
                has_add_output = any('manifest.add_output' in line for line in self.lines)
                
                if not has_add_input:
                    self.violations.append(ComplianceViolation(
                        rule="Manifest Input Tracking",
                        severity="error",
                        line=1,
                        message="Stage should track inputs with io.manifest.add_input()",
                        section="§ 2.5"
                    ))
                
                if not has_add_output:
                    self.violations.append(ComplianceViolation(
                        rule="Manifest Output Tracking",
                        severity="error",
                        line=1,
                        message="Stage should track outputs with io.manifest.add_output()",
                        section="§ 2.5"
                    ))
                
                # Check for finalize_stage_manifest
                has_finalize = any('finalize_stage_manifest' in line for line in self.lines)
                if not has_finalize:
                    self.violations.append(ComplianceViolation(
                        rule="Manifest Finalization",
                        severity="critical",
                        line=1,
                        message="Stage must call io.finalize_stage_manifest()",
                        section="§ 2.6"
                    ))
    
    def check_config_usage(self) -> None:
        """Check for proper config usage (§ 4)"""
        # Skip if this file has an exception for Config Access
        relative_path = str(self.file_path).replace(str(Path.cwd()) + '/', '')
        if relative_path in self.EXCEPTIONS and 'Config Access' in self.EXCEPTIONS[relative_path]:
            return
        
        # Check for direct environment access (reading, not setting)
        for i, line in enumerate(self.lines, 1):
            # Only flag os.getenv() for reading config, not os.environ['X'] = 'Y' for setting
            if 'os.getenv(' in line:
                # This is reading config - should use load_config()
                self.violations.append(ComplianceViolation(
                    rule="Config Access",
                    severity="critical",
                    line=i,
                    message="Use load_config() instead of os.getenv()",
                    section="§ 4.2"
                ))
            elif 'os.environ[' in line and '=' not in line.split('os.environ[')[1].split(']')[0]:
                # Reading from os.environ[] without assignment - should use load_config()
                # Skip lines like: os.environ['X'] = 'Y' (these are settings, not config reading)
                if '] =' not in line and ']=' not in line:
                    self.violations.append(ComplianceViolation(
                        rule="Config Access",
                        severity="critical",
                        line=i,
                        message="Use load_config() instead of os.environ[]",
                        section="§ 4.2"
                    ))
    
    def check_stage_directory_usage(self) -> None:
        """Check for proper stage directory usage (§ 1.1)"""
        for i, line in enumerate(self.lines, 1):
            # Check for output to job_dir instead of stage_dir
            if 'job_dir /' in line and '=' in line and any(
                ext in line for ext in ['.txt', '.json', '.csv', '.wav', '.mp4', '.srt']
            ):
                # Skip common acceptable patterns (reading inputs, checking config)
                acceptable_patterns = [
                    'job_config.json',  # Shared job configuration
                    'job.json',  # Job-level configuration
                    'manifest.json',  # Job-level manifest
                    '.env',  # Environment configuration
                    'transcripts',  # Shared transcripts directory
                    'subtitles',  # Shared subtitles directory
                    'filename_parser',  # Parsing input names
                    'demux',  # Reading demuxed inputs
                    'tmdb',  # Reading TMDB metadata
                    'glossary',  # Reading glossary data
                    'pre_ner', 'post_ner',  # Reading NER data
                    'asr',  # Reading ASR results
                ]
                
                # Skip if any acceptable pattern is in the line
                if any(pattern in line for pattern in acceptable_patterns):
                    continue
                
                # Skip if explicitly checking existence or reading
                next_few_lines = '\n'.join(self.lines[max(0, i-1):min(i+3, len(self.lines))])
                if '.exists()' in next_few_lines or '.read_text()' in next_few_lines:
                    continue
                
                # If it's not an acceptable pattern and not clearly a read, flag it
                self.violations.append(ComplianceViolation(
                    rule="Stage Directory Containment",
                    severity="critical",
                    line=i,
                    message="Write outputs to io.stage_dir, not job_dir",
                    section="§ 1.1"
                ))
    
    def check_type_hints(self) -> None:
        """Check for type hints on functions (§ 6.2)"""
        if not self.tree:
            return
            
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                # Check if function has return type annotation
                if node.returns is None and node.name != '__init__':
                    self.violations.append(ComplianceViolation(
                        rule="Type Hints",
                        severity="warning",
                        line=node.lineno,
                        message=f"Function '{node.name}' missing return type hint",
                        section="§ 6.2"
                    ))
                
                # Check if parameters have type hints
                missing_params = []
                for arg in node.args.args:
                    if arg.arg != 'self' and arg.annotation is None:
                        missing_params.append(arg.arg)
                
                if missing_params and len(missing_params) > 0:
                    self.violations.append(ComplianceViolation(
                        rule="Type Hints",
                        severity="warning",
                        line=node.lineno,
                        message=f"Function '{node.name}' parameters missing type hints: {', '.join(missing_params)}",
                        section="§ 6.2"
                    ))
    
    def check_docstrings(self) -> None:
        """Check for docstrings on public functions (§ 6.3)"""
        if not self.tree:
            return
            
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                # Check if function has docstring
                docstring = ast.get_docstring(node)
                if not docstring:
                    self.violations.append(ComplianceViolation(
                        rule="Docstrings",
                        severity="warning",
                        line=node.lineno,
                        message=f"Public function '{node.name}' missing docstring",
                        section="§ 6.3"
                    ))
    
    def check_error_handling(self) -> None:
        """Check for error handling with logging (§ 5)"""
        if not self.tree:
            return
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ExceptHandler):
                # Check if exception handler has logger.error with exc_info
                has_logger_error = False
                has_exc_info = False
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, 'attr') and child.func.attr == 'error':
                            has_logger_error = True
                            # Check for exc_info=True
                            for keyword in child.keywords:
                                if keyword.arg == 'exc_info':
                                    has_exc_info = True
                
                if has_logger_error and not has_exc_info:
                    self.violations.append(ComplianceViolation(
                        rule="Error Logging",
                        severity="warning",
                        line=node.lineno,
                        message="logger.error() should include exc_info=True for traceback",
                        section="§ 5"
                    ))


def check_file(file_path: Path, strict: bool = False) -> Tuple[int, int, int]:
    """
    Check a single file for compliance.
    
    Returns:
        Tuple of (critical_count, error_count, warning_count)
    """
    checker = ComplianceChecker(file_path)
    violations = checker.check_all()
    
    if not violations:
        # CLI output: Must use stdout for user-facing messages
        sys.stdout.write(f"{GREEN}✓{RESET} {file_path}: All checks passed\n")
        logger.debug(f"File {file_path} passed all compliance checks")
        return (0, 0, 0)
    
    # CLI output: Must use stdout for user-facing messages
    sys.stdout.write(f"\n{BLUE}{'=' * 70}{RESET}\n")
    sys.stdout.write(f"{BLUE}File: {file_path}{RESET}\n")
    sys.stdout.write(f"{BLUE}{'=' * 70}{RESET}\n")
    
    critical = sum(1 for v in violations if v.severity == 'critical')
    errors = sum(1 for v in violations if v.severity == 'error')
    warnings = sum(1 for v in violations if v.severity == 'warning')
    
    logger.info(f"Found {critical} critical, {errors} errors, {warnings} warnings in {file_path}")
    
    for violation in violations:
        # CLI output: Must use stdout for user-facing messages
        sys.stdout.write(f"\n{violation}\n")
    
    # CLI output: Must use stdout for user-facing messages
    sys.stdout.write(f"\n{BLUE}{'=' * 70}{RESET}\n")
    sys.stdout.write(f"Summary: {RED}{critical} critical{RESET}, {RED}{errors} errors{RESET}, {YELLOW}{warnings} warnings{RESET}\n")
    sys.stdout.write(f"{BLUE}{'=' * 70}{RESET}\n\n")
    
    return (critical, errors, warnings)


def get_staged_files() -> List[Path]:
    """Get list of staged Python files."""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            check=True
        )
        files = [Path(f) for f in result.stdout.strip().split('\n') if f.endswith('.py')]
        logger.debug(f"Found {len(files)} staged Python files")
        return files
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get staged files: {e}", exc_info=True)
        return []


def main() -> int:
    """Main entry point for compliance validation.
    
    Returns:
        Exit code (0 for success, 1 for violations in strict mode)
    """
    parser = argparse.ArgumentParser(
        description="Validate Python files against DEVELOPER_STANDARDS.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s script.py                    # Check single file
  %(prog)s scripts/*.py                 # Check multiple files
  %(prog)s --strict scripts/*.py        # Exit 1 if violations found
  %(prog)s --staged                     # Check staged files only
        """
    )
    parser.add_argument('files', nargs='*', type=Path, help='Python files to check')
    parser.add_argument('--strict', action='store_true', help='Exit with code 1 if violations found')
    parser.add_argument('--staged', action='store_true', help='Check only staged files')
    
    args = parser.parse_args()
    
    logger.info("Starting compliance validation")
    
    # Get files to check
    if args.staged:
        files = get_staged_files()
        if not files:
            # CLI output: Must use stdout for user-facing messages
            sys.stdout.write(f"{YELLOW}No staged Python files found{RESET}\n")
            logger.info("No staged files to check")
            return 0
        # CLI output: Must use stdout for user-facing messages
        sys.stdout.write(f"{BLUE}Checking {len(files)} staged files...{RESET}\n\n")
        logger.info(f"Checking {len(files)} staged files")
    else:
        files = args.files
        if not files:
            parser.print_help()
            logger.warning("No files specified for validation")
            return 1
        logger.info(f"Checking {len(files)} specified files")
    
    # Check each file
    total_critical = 0
    total_errors = 0
    total_warnings = 0
    
    for file_path in files:
        if not file_path.exists():
            # CLI output: Must use stdout for user-facing messages
            sys.stdout.write(f"{RED}File not found: {file_path}{RESET}\n")
            logger.error(f"File not found: {file_path}")
            continue
        
        if not file_path.suffix == '.py':
            # CLI output: Must use stdout for user-facing messages
            sys.stdout.write(f"{YELLOW}Skipping non-Python file: {file_path}{RESET}\n")
            logger.debug(f"Skipping non-Python file: {file_path}")
            continue
        
        critical, errors, warnings = check_file(file_path, args.strict)
        total_critical += critical
        total_errors += errors
        total_warnings += warnings
    
    # Print overall summary
    # CLI output: Must use stdout for user-facing messages
    sys.stdout.write(f"\n{BLUE}{'=' * 70}{RESET}\n")
    sys.stdout.write(f"{BLUE}OVERALL SUMMARY{RESET}\n")
    sys.stdout.write(f"{BLUE}{'=' * 70}{RESET}\n")
    sys.stdout.write(f"Files checked: {len(files)}\n")
    sys.stdout.write(f"Total violations: {RED}{total_critical} critical{RESET}, {RED}{total_errors} errors{RESET}, {YELLOW}{total_warnings} warnings{RESET}\n")
    
    logger.info(f"Validation complete: {len(files)} files, {total_critical} critical, {total_errors} errors, {total_warnings} warnings")
    
    if total_critical == 0 and total_errors == 0 and total_warnings == 0:
        # CLI output: Must use stdout for user-facing messages
        sys.stdout.write(f"\n{GREEN}✓ All files passed compliance checks!{RESET}\n")
        logger.info("All files passed compliance checks")
        return 0
    else:
        # CLI output: Must use stdout for user-facing messages
        sys.stdout.write(f"\n{YELLOW}⚠ Violations found. Review and fix before committing.{RESET}\n")
        sys.stdout.write(f"\n{BLUE}Tip: See docs/developer/DEVELOPER_STANDARDS.md for details on each § section{RESET}\n")
        logger.warning("Violations found in compliance check")
        
        if args.strict and (total_critical > 0 or total_errors > 0):
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(main())
