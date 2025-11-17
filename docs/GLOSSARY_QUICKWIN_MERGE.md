# Glossary Quick Win: Merge Glossaries Script

**Time**: 30 minutes  
**Priority**: HIGH - Do this first  

## What It Does

Merges all existing glossaries into a single unified format:
- Master glossary (55 manual terms)
- Cache glossaries (115+ auto-generated terms)
- Deduplicates and standardizes format
- Tracks source for each term

## Run Now

```bash
cd /Users/rpatel/Projects/cp-whisperx-app
python3 tools/merge_glossaries.py
```

##Implementation

```python
#!/usr/bin/env python3
"""
Merge Glossaries - Consolidate all glossary sources

Combines:
- glossary/hinglish_master.tsv (manual, authoritative)
- glossary/cache/*.tsv (auto-generated per film)

Output:
- glossary/unified_glossary.tsv (single source of truth)
"""

import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_master_glossary():
    """Load manual master glossary"""
    master_path = PROJECT_ROOT / "glossary" / "hinglish_master.tsv"
    
    if not master_path.exists():
        print(f"Warning: Master glossary not found: {master_path}")
        return pd.DataFrame()
    
    df = pd.read_csv(master_path, sep='\t')
    
    # Standardize columns
    df_unified = pd.DataFrame({
        'term': df['source'],
        'english': df['preferred_english'].str.split('|').str[0],  # First option
        'alternatives': df['preferred_english'],  # All options
        'context': df['context'],
        'confidence': 1.0,  # Manual entries are authoritative
        'source': 'manual:master',
        'frequency': 0,
        'notes': df['notes']
    })
    
    print(f"✓ Loaded master glossary: {len(df_unified)} terms")
    return df_unified


def load_cache_glossaries():
    """Load auto-generated cache glossaries"""
    cache_dir = PROJECT_ROOT / "glossary" / "cache"
    
    if not cache_dir.exists():
        print("Warning: Cache directory not found")
        return pd.DataFrame()
    
    cache_files = list(cache_dir.glob("*.tsv"))
    
    if not cache_files:
        print("Warning: No cache files found")
        return pd.DataFrame()
    
    all_cache = []
    
    for cache_file in cache_files:
        try:
            df = pd.read_csv(cache_file, sep='\t')
            
            # Convert to unified format
            df_unified = pd.DataFrame({
                'term': df['term'],
                'english': df['english'],
                'alternatives': df.get('aliases', ''),
                'context': df.get('type', ''),
                'confidence': df.get('confidence', 0.8),
                'source': f"asr:{cache_file.stem}",
                'frequency': 0,
                'notes': ''
            })
            
            all_cache.append(df_unified)
            print(f"  Loaded cache: {cache_file.name} ({len(df_unified)} terms)")
            
        except Exception as e:
            print(f"  Error loading {cache_file.name}: {e}")
    
    if all_cache:
        combined = pd.concat(all_cache, ignore_index=True)
        print(f"✓ Loaded cache glossaries: {len(combined)} terms")
        return combined
    
    return pd.DataFrame()


def merge_glossaries(master, cache):
    """Merge master and cache, master takes precedence"""
    
    if master.empty and cache.empty:
        print("ERROR: No glossaries to merge!")
        return pd.DataFrame()
    
    if master.empty:
        print("Using cache only (no master)")
        return cache
    
    if cache.empty:
        print("Using master only (no cache)")
        return master
    
    # Combine both
    combined = pd.concat([master, cache], ignore_index=True)
    
    # Remove duplicates, keeping master entries (first occurrence)
    merged = combined.drop_duplicates(subset=['term'], keep='first')
    
    duplicates_removed = len(combined) - len(merged)
    print(f"✓ Merged glossaries: {len(merged)} terms ({duplicates_removed} duplicates removed)")
    
    # Sort by term
    merged = merged.sort_values('term').reset_index(drop=True)
    
    return merged


def validate_glossary(df):
    """Validate unified glossary"""
    issues = []
    
    # Check for required columns
    required = ['term', 'english', 'alternatives', 'context', 'confidence', 'source']
    missing = [col for col in required if col not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
    
    # Check for empty terms
    empty_terms = df[df['term'].isna() | (df['term'] == '')].shape[0]
    if empty_terms > 0:
        issues.append(f"{empty_terms} empty terms")
    
    # Check for empty translations
    empty_english = df[df['english'].isna() | (df['english'] == '')].shape[0]
    if empty_english > 0:
        issues.append(f"{empty_english} empty translations")
    
    # Check confidence range
    invalid_conf = df[(df['confidence'] < 0) | (df['confidence'] > 1)].shape[0]
    if invalid_conf > 0:
        issues.append(f"{invalid_conf} invalid confidence values")
    
    if issues:
        print("⚠ Validation warnings:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Validation passed")
    
    return len(issues) == 0


def save_unified_glossary(df, output_path):
    """Save unified glossary"""
    df.to_csv(output_path, sep='\t', index=False)
    print(f"✓ Saved unified glossary: {output_path}")
    print(f"  Total terms: {len(df)}")
    print(f"  Manual terms: {df[df['source'].str.startswith('manual')].shape[0]}")
    print(f"  Auto terms: {df[df['source'].str.startswith('asr')].shape[0]}")


def print_statistics(df):
    """Print glossary statistics"""
    print("\n" + "=" * 60)
    print("UNIFIED GLOSSARY STATISTICS")
    print("=" * 60)
    
    print(f"\nTotal terms: {len(df)}")
    
    # By source
    print("\nBy source:")
    for source in df['source'].value_counts().head(10).items():
        print(f"  {source[0]}: {source[1]}")
    
    # By context
    print("\nBy context:")
    for context in df['context'].value_counts().head(10).items():
        print(f"  {context[0]}: {context[1]}")
    
    # Confidence distribution
    print(f"\nConfidence:")
    print(f"  High (>0.9): {df[df['confidence'] > 0.9].shape[0]}")
    print(f"  Medium (0.7-0.9): {df[(df['confidence'] >= 0.7) & (df['confidence'] <= 0.9)].shape[0]}")
    print(f"  Low (<0.7): {df[df['confidence'] < 0.7].shape[0]}")
    
    # Sample entries
    print("\nSample entries:")
    for _, row in df.head(5).iterrows():
        print(f"  {row['term']} → {row['english']} ({row['source']})")
    
    print("=" * 60)


def main():
    print("\n" + "=" * 60)
    print("GLOSSARY MERGE TOOL")
    print("=" * 60 + "\n")
    
    # Load glossaries
    print("Loading glossaries...")
    master = load_master_glossary()
    cache = load_cache_glossaries()
    
    # Merge
    print("\nMerging...")
    unified = merge_glossaries(master, cache)
    
    if unified.empty:
        print("ERROR: No glossaries loaded!")
        return 1
    
    # Validate
    print("\nValidating...")
    validate_glossary(unified)
    
    # Save
    output_path = PROJECT_ROOT / "glossary" / "unified_glossary.tsv"
    print(f"\nSaving to: {output_path}")
    save_unified_glossary(unified, output_path)
    
    # Statistics
    print_statistics(unified)
    
    print("\n✅ MERGE COMPLETE")
    print(f"Unified glossary: {output_path}")
    print(f"Total terms: {len(unified)}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## After Running

You'll have:
```
glossary/unified_glossary.tsv    # 170+ terms, single format
```

Check it:
```bash
head -20 glossary/unified_glossary.tsv
wc -l glossary/unified_glossary.tsv
```

## Next Steps

1. ✅ Run this script
2. ⏭ Update pipeline to use unified_glossary.tsv
3. ⏭ Create glossary applier stage
4. ⏭ Test end-to-end

**Time Investment**: 30 minutes  
**Impact**: Single source of truth for all glossary data
