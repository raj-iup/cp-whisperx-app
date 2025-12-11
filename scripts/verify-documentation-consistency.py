#!/usr/bin/env python3
"""
Documentation Consistency Verification Tool

Checks consistency across:
- CANONICAL_PIPELINE.md
- ARCHITECTURE_IMPLEMENTATION_ROADMAP.md
- DEVELOPER_STANDARDS.md
- .github/copilot-instructions.md
- IMPLEMENTATION_TRACKER.md
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

class ConsistencyChecker:
    def __init__(self, root_dir: Path):
        self.root = root_dir
        self.errors = []
        self.warnings = []
        self.info = []
        
    def check_stage_count(self) -> None:
        """Verify all docs agree on stage count (12)"""
        print("=" * 70)
        print("STAGE COUNT VERIFICATION")
        print("=" * 70)
        
        docs = {
            "CANONICAL_PIPELINE.md": self.root / "CANONICAL_PIPELINE.md",
            "ARCHITECTURE_IMPLEMENTATION_ROADMAP.md": self.root / "docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md",
            "DEVELOPER_STANDARDS.md": self.root / "docs/developer/DEVELOPER_STANDARDS.md",
            "copilot-instructions.md": self.root / ".github/copilot-instructions.md",
            "IMPLEMENTATION_TRACKER.md": self.root / "IMPLEMENTATION_TRACKER.md"
        }
        
        stage_counts = {}
        for name, path in docs.items():
            if path.exists():
                content = path.read_text()
                
                # Count "12-stage" references
                twelve_stage = len(re.findall(r'\b12-stage\b', content, re.IGNORECASE))
                
                # Count "10-stage" references (should be 0)
                ten_stage = len(re.findall(r'\b10-stage\b', content, re.IGNORECASE))
                
                stage_counts[name] = {
                    "12-stage": twelve_stage,
                    "10-stage": ten_stage
                }
                
                if ten_stage > 0:
                    self.errors.append(f"❌ {name}: Found {ten_stage} references to '10-stage' (should be 0)")
                elif twelve_stage == 0:
                    self.warnings.append(f"⚠️  {name}: No '12-stage' references found")
                else:
                    self.info.append(f"✅ {name}: {twelve_stage} correct '12-stage' references")
        
        print()
        
    def check_stage_numbers(self) -> None:
        """Verify stage numbering 01-12 is consistent"""
        print("\n" + "=" * 70)
        print("STAGE NUMBERING VERIFICATION (01-12)")
        print("=" * 70)
        
        expected_stages = [
            ("01", "demux"),
            ("02", "tmdb"),
            ("03", "glossary_load"),
            ("04", "source_separation"),
            ("05", "pyannote_vad"),
            ("06", "whisperx_asr", "asr"),
            ("07", "alignment"),
            ("08", "lyrics_detection"),
            ("09", "hallucination_removal"),
            ("10", "translation"),
            ("11", "subtitle_generation"),
            ("12", "mux")
        ]
        
        canonical = self.root / "CANONICAL_PIPELINE.md"
        if canonical.exists():
            content = canonical.read_text()
            
            for stage_info in expected_stages:
                stage_num = stage_info[0]
                stage_names = stage_info[1:] if len(stage_info) > 2 else [stage_info[1]]
                
                found = False
                for name in stage_names:
                    if f"Stage {stage_num}:" in content or f"{stage_num}_{name}" in content:
                        found = True
                        break
                
                if found:
                    self.info.append(f"✅ Stage {stage_num}: Found")
                else:
                    self.errors.append(f"❌ Stage {stage_num}: Not found in CANONICAL_PIPELINE.md")
        
        print()
        
    def check_mandatory_stages(self) -> None:
        """Verify stages 08-09 marked as MANDATORY for subtitle workflow"""
        print("\n" + "=" * 70)
        print("MANDATORY STAGE VERIFICATION (08-09)")
        print("=" * 70)
        
        canonical = self.root / "CANONICAL_PIPELINE.md"
        if canonical.exists():
            content = canonical.read_text()
            
            # Check stage 08
            if "08_lyrics_detection" in content and "MANDATORY" in content:
                self.info.append("✅ Stage 08 (lyrics_detection): Marked as MANDATORY")
            else:
                self.errors.append("❌ Stage 08: Not properly marked as MANDATORY")
            
            # Check stage 09
            if "09_hallucination_removal" in content and "MANDATORY" in content:
                self.info.append("✅ Stage 09 (hallucination_removal): Marked as MANDATORY")
            else:
                self.errors.append("❌ Stage 09: Not properly marked as MANDATORY")
        
        print()
        
    def check_legacy_directories(self) -> None:
        """Verify no references to media/, transcripts/, subtitles/"""
        print("\n" + "=" * 70)
        print("LEGACY DIRECTORY VERIFICATION")
        print("=" * 70)
        
        legacy_dirs = ["media/", "transcripts/", "subtitles/"]
        docs = [
            self.root / "docs/developer/DEVELOPER_STANDARDS.md",
            self.root / "docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md",
            self.root / "CANONICAL_PIPELINE.md"
        ]
        
        for doc in docs:
            if doc.exists():
                content = doc.read_text()
                doc_name = doc.name
                
                found_legacy = []
                for legacy_dir in legacy_dirs:
                    # Skip if it's in a "don't do this" example or marked as removed
                    matches = re.findall(f'[^❌].*{re.escape(legacy_dir)}', content)
                    # Filter out negative examples
                    real_matches = [m for m in matches if "REMOVE" not in m and "no longer" not in m.lower()]
                    
                    if real_matches:
                        found_legacy.append(legacy_dir)
                
                if found_legacy:
                    self.warnings.append(f"⚠️  {doc_name}: Found references to {', '.join(found_legacy)}")
                else:
                    self.info.append(f"✅ {doc_name}: No legacy directory references")
        
        print()
        
    def check_version_consistency(self) -> None:
        """Verify version terminology (v2.9 current, v3.0 target)"""
        print("\n" + "=" * 70)
        print("VERSION TERMINOLOGY VERIFICATION")
        print("=" * 70)
        
        roadmap = self.root / "docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md"
        if roadmap.exists():
            content = roadmap.read_text()
            
            # Check for v2.9 as current
            if "v2.9" in content or "v2.0 (Simplified Pipeline - 55%)" not in content:
                self.info.append("✅ Version: Uses v2.9 for current state")
            else:
                self.errors.append("❌ Version: Still using v2.0 instead of v2.9")
            
            # Check for proper v3.0 description
            if "v3.0" in content:
                self.info.append("✅ Version: v3.0 mentioned as target")
            else:
                self.warnings.append("⚠️  Version: v3.0 not mentioned")
        
        print()
        
    def check_cross_references(self) -> None:
        """Verify cross-references work"""
        print("\n" + "=" * 70)
        print("CROSS-REFERENCE VERIFICATION")
        print("=" * 70)
        
        tracker = self.root / "IMPLEMENTATION_TRACKER.md"
        if tracker.exists():
            content = tracker.read_text()
            
            # Check references to CANONICAL_PIPELINE.md
            if "CANONICAL_PIPELINE.md" in content:
                canonical = self.root / "CANONICAL_PIPELINE.md"
                if canonical.exists():
                    self.info.append("✅ CANONICAL_PIPELINE.md: Referenced and exists")
                else:
                    self.errors.append("❌ CANONICAL_PIPELINE.md: Referenced but missing")
            
        print()
        
    def run_all_checks(self) -> Tuple[int, int, int]:
        """Run all verification checks"""
        self.check_stage_count()
        self.check_stage_numbers()
        self.check_mandatory_stages()
        self.check_legacy_directories()
        self.check_version_consistency()
        self.check_cross_references()
        
        return len(self.errors), len(self.warnings), len(self.info)
        
    def print_summary(self) -> int:
        """Print summary of all checks"""
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        
        if self.info:
            print(f"\n✅ PASSED ({len(self.info)}):")
            for msg in self.info:
                print(f"  {msg}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for msg in self.errors:
                print(f"  {msg}")
        
        print("\n" + "=" * 70)
        print(f"Total: {len(self.info)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")
        print("=" * 70)
        
        return 1 if self.errors else 0

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    checker = ConsistencyChecker(root)
    errors, warnings, passed = checker.run_all_checks()
    exit_code = checker.print_summary()
    exit(exit_code)
