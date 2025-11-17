#!/usr/bin/env python3
"""
Glossary Validation Tool - Phase 4 Quality

Validates unified glossary for:
- Format consistency
- Duplicate terms
- Empty translations
- Invalid confidence values
- Data integrity
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_format(df: pd.DataFrame) -> tuple:
    """Validate glossary format"""
    issues = []
    
    # Required columns
    required_cols = ['term', 'english', 'alternatives', 'context', 'confidence', 'source']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        issues.append(('CRITICAL', f"Missing required columns: {missing_cols}"))
    
    return issues


def validate_data_integrity(df: pd.DataFrame) -> tuple:
    """Validate data integrity"""
    issues = []
    
    # Empty terms
    empty_terms = df[df['term'].isna() | (df['term'] == '')].shape[0]
    if empty_terms > 0:
        issues.append(('ERROR', f"{empty_terms} empty terms"))
    
    # Empty translations
    empty_english = df[df['english'].isna() | (df['english'] == '')].shape[0]
    if empty_english > 0:
        issues.append(('ERROR', f"{empty_english} empty translations"))
    
    # Invalid confidence
    invalid_conf = df[(df['confidence'] < 0) | (df['confidence'] > 1)].shape[0]
    if invalid_conf > 0:
        issues.append(('ERROR', f"{invalid_conf} invalid confidence values (must be 0-1)"))
    
    # Missing source
    empty_source = df[df['source'].isna() | (df['source'] == '')].shape[0]
    if empty_source > 0:
        issues.append(('WARNING', f"{empty_source} terms missing source"))
    
    return issues


def validate_duplicates(df: pd.DataFrame) -> tuple:
    """Check for duplicate terms"""
    issues = []
    
    # Find duplicates
    duplicates = df[df.duplicated('term', keep=False)]
    
    if len(duplicates) > 0:
        dup_terms = duplicates['term'].unique()
        issues.append(('WARNING', f"{len(dup_terms)} duplicate terms: {list(dup_terms)[:5]}..."))
    
    return issues


def validate_quality(df: pd.DataFrame) -> tuple:
    """Check data quality"""
    issues = []
    
    # Low confidence terms
    low_conf = df[df['confidence'] < 0.6].shape[0]
    if low_conf > 0:
        issues.append(('INFO', f"{low_conf} terms with confidence < 0.6 (may need review)"))
    
    # Terms without alternatives
    no_alts = df[df['alternatives'].isna() | (df['alternatives'] == '')].shape[0]
    if no_alts > 10:
        issues.append(('INFO', f"{no_alts} terms without alternatives"))
    
    # Terms without context
    no_context = df[df['context'].isna() | (df['context'] == '')].shape[0]
    if no_context > 5:
        issues.append(('WARNING', f"{no_context} terms without context"))
    
    return issues


def print_statistics(df: pd.DataFrame):
    """Print glossary statistics"""
    print("\n" + "=" * 60)
    print("GLOSSARY STATISTICS")
    print("=" * 60)
    
    print(f"\nTotal terms: {len(df)}")
    
    # By source
    print("\nBy source:")
    for source, count in df['source'].value_counts().head(10).items():
        print(f"  {source}: {count}")
    
    # By context
    print("\nBy context:")
    for context, count in df['context'].value_counts().head(10).items():
        print(f"  {context}: {count}")
    
    # Confidence distribution
    print(f"\nConfidence:")
    print(f"  High (>0.9): {df[df['confidence'] > 0.9].shape[0]}")
    print(f"  Medium (0.7-0.9): {df[(df['confidence'] >= 0.7) & (df['confidence'] <= 0.9)].shape[0]}")
    print(f"  Low (<0.7): {df[df['confidence'] < 0.7].shape[0]}")
    
    # Frequency stats
    if 'frequency' in df.columns:
        print(f"\nUsage frequency:")
        print(f"  Total uses: {df['frequency'].sum()}")
        print(f"  Average: {df['frequency'].mean():.1f}")
        print(f"  Most used:")
        for _, row in df.nlargest(5, 'frequency')[['term', 'frequency']].iterrows():
            print(f"    {row['term']}: {row['frequency']}x")


def main():
    """Main validation"""
    print("\n" + "=" * 60)
    print("GLOSSARY VALIDATION TOOL")
    print("=" * 60)
    
    # Load glossary
    glossary_path = PROJECT_ROOT / "glossary" / "unified_glossary.tsv"
    
    if not glossary_path.exists():
        print(f"\n❌ ERROR: Glossary not found at {glossary_path}")
        return 1
    
    print(f"\nValidating: {glossary_path}")
    
    try:
        df = pd.read_csv(glossary_path, sep='\t')
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load glossary: {e}")
        return 1
    
    print(f"Loaded {len(df)} terms")
    
    # Run validations
    all_issues = []
    
    print("\n" + "-" * 60)
    print("Running validations...")
    print("-" * 60)
    
    validations = [
        ("Format", validate_format),
        ("Data Integrity", validate_data_integrity),
        ("Duplicates", validate_duplicates),
        ("Quality", validate_quality),
    ]
    
    for name, validate_func in validations:
        issues = validate_func(df)
        if issues:
            all_issues.extend(issues)
        print(f"\n{name}: {len(issues)} issue(s)")
        for severity, message in issues:
            icon = {
                'CRITICAL': '🔴',
                'ERROR': '❌',
                'WARNING': '⚠️',
                'INFO': 'ℹ️'
            }.get(severity, '•')
            print(f"  {icon} {severity}: {message}")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    critical = sum(1 for s, _ in all_issues if s == 'CRITICAL')
    errors = sum(1 for s, _ in all_issues if s == 'ERROR')
    warnings = sum(1 for s, _ in all_issues if s == 'WARNING')
    info = sum(1 for s, _ in all_issues if s == 'INFO')
    
    print(f"\nTotal issues: {len(all_issues)}")
    print(f"  Critical: {critical}")
    print(f"  Errors: {errors}")
    print(f"  Warnings: {warnings}")
    print(f"  Info: {info}")
    
    # Print statistics
    print_statistics(df)
    
    # Final verdict
    print("\n" + "=" * 60)
    if critical > 0:
        print("❌ VALIDATION FAILED - Critical issues found")
        return 1
    elif errors > 0:
        print("⚠️  VALIDATION WARNING - Errors found")
        return 0  # Don't fail on errors
    elif warnings > 0:
        print("✅ VALIDATION PASSED - With warnings")
        return 0
    else:
        print("✅ VALIDATION PASSED - No issues found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
