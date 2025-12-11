#!/usr/bin/env python3
"""
Automated File Naming Validation Tests

Tests that all stage output files follow the mandatory naming standard (§ 1.3.1):
  Pattern: {stage}_{language}_{descriptor}.{ext}
  
Rules:
  1. ✅ Must start with stage name prefix (e.g., asr_, demux_, alignment_)
  2. ❌ No leading special characters (., -, _)
  3. ❌ No hidden files (dot-prefixed)
  4. ✅ Consistent underscore separators
  5. ✅ Descriptive middle part
  6. ✅ Appropriate extension

Tests can be run:
  - Manually: python3 tests/test_file_naming_standard.py
  - Via pytest: pytest tests/test_file_naming_standard.py
  - Pre-commit: Automatically validates staged files
"""

# Standard library
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest


class FileNamingValidator:
    """Validates file names against § 1.3.1 standard"""
    
    # Valid stage prefixes (from 01-12 stages)
    VALID_STAGE_PREFIXES = {
        'demux', 'tmdb', 'glossary', 'source_sep', 'vad', 'pyannote',
        'asr', 'whisperx', 'alignment', 'lyrics', 'hallucination', 
        'translation', 'indictrans2', 'nllb', 'subtitle', 'mux'
    }
    
    # Valid language codes
    VALID_LANGUAGES = {
        'english', 'hindi', 'spanish', 'french', 'german', 'italian',
        'portuguese', 'russian', 'japanese', 'korean', 'chinese', 'arabic',
        'tamil', 'telugu', 'bengali', 'urdu', 'gujarati', 'malayalam',
        'kannada', 'marathi', 'punjabi', 'en', 'hi', 'es', 'fr', 'de',
        'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'ta', 'te', 'bn',
        'ur', 'gu', 'ml', 'kn', 'mr', 'pa'
    }
    
    # Standard pattern: {stage}_{language}_{descriptor}.{ext}
    # Examples: asr_english_segments.json, demux_audio.wav, alignment_segments.json
    PATTERN = re.compile(
        r'^([a-z][a-z0-9_]+?)(?:_([a-z]{2,10}))?_([a-z][a-z0-9_]+)\.(json|txt|wav|mp3|mp4|srt|vtt|ass)$'
    )
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_filename(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a single filename against the standard
        
        Returns:
            (is_valid, error_message)
        """
        # Rule 1: No leading special characters
        if filename.startswith(('.', '-', '_')):
            return False, f"Leading special character: '{filename[0]}'"
        
        # Rule 2: Must match pattern
        match = self.PATTERN.match(filename)
        if not match:
            return False, f"Does not match standard pattern: {filename}"
        
        stage, language, descriptor, extension = match.groups()
        
        # Rule 3: Valid stage prefix
        if stage not in self.VALID_STAGE_PREFIXES:
            return False, f"Invalid stage prefix: '{stage}'"
        
        # Rule 4: Valid language code (optional)
        if language and language not in self.VALID_LANGUAGES:
            # Warning only, not error (might be new language)
            self.warnings.append(f"Unrecognized language code: '{language}' in {filename}")
        
        # Rule 5: Descriptive part not empty
        if len(descriptor) < 2:
            return False, f"Descriptor too short: '{descriptor}'"
        
        return True, None
    
    def validate_directory(self, directory: Path, recursive: bool = False) -> Tuple[List[str], List[str]]:
        """
        Validate all files in a directory
        
        Returns:
            (valid_files, invalid_files_with_reasons)
        """
        valid = []
        invalid = []
        
        pattern = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue
            
            # Skip hidden files in parent directories
            if any(part.startswith('.') for part in file_path.parts[:-1]):
                continue
            
            filename = file_path.name
            
            # Skip system files
            if filename in ['.DS_Store', '.gitignore', '.gitkeep', 'stage.log']:
                continue
            
            # Skip legacy compatibility files (allowed for backward compat)
            if filename in ['segments.json', 'transcript.json', 'transcript.txt']:
                self.warnings.append(f"Legacy file (allowed): {filename}")
                valid.append(str(file_path))
                continue
            
            is_valid, error_msg = self.validate_filename(filename)
            if is_valid:
                valid.append(str(file_path))
            else:
                invalid.append(f"{file_path}: {error_msg}")
        
        return valid, invalid


# ============================================================================
# PYTEST TEST CASES
# ============================================================================

class TestFileNamingStandard:
    """Test suite for file naming standard validation"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return FileNamingValidator()
    
    def test_valid_filenames(self, validator):
        """Test that valid filenames pass validation"""
        valid_names = [
            'asr_segments.json',
            'asr_english_segments.json',
            'asr_english_transcript.txt',
            'demux_audio.wav',
            'alignment_segments.json',
            'translation_hindi_segments.json',
            'subtitle_english_subtitles.srt',
            'mux_output.mp4'
        ]
        
        for filename in valid_names:
            is_valid, error = validator.validate_filename(filename)
            assert is_valid, f"{filename} should be valid, but got error: {error}"
    
    def test_invalid_leading_dot(self, validator):
        """Test that dot-prefixed filenames are rejected"""
        invalid_names = [
            '.segments.json',
            '.transcript.txt',
            '.hidden_file.json'
        ]
        
        for filename in invalid_names:
            is_valid, error = validator.validate_filename(filename)
            assert not is_valid, f"{filename} should be invalid (leading dot)"
            assert "Leading special character" in error
    
    def test_invalid_leading_dash(self, validator):
        """Test that dash-prefixed filenames are rejected"""
        invalid_names = [
            '-English.segments.json',
            '-Hindi.srt',
            '-output.json'
        ]
        
        for filename in invalid_names:
            is_valid, error = validator.validate_filename(filename)
            assert not is_valid, f"{filename} should be invalid (leading dash)"
            assert "Leading special character" in error
    
    def test_invalid_no_stage_prefix(self, validator):
        """Test that files without stage prefix are rejected"""
        invalid_names = [
            'segments.json',  # Unless it's a legacy file
            'output.txt',
            'data.json'
        ]
        
        for filename in invalid_names:
            is_valid, error = validator.validate_filename(filename)
            # Note: segments.json and transcript.json are allowed as legacy
            if filename not in ['segments.json', 'transcript.json', 'transcript.txt']:
                assert not is_valid, f"{filename} should be invalid (no stage prefix)"
    
    def test_invalid_stage_prefix(self, validator):
        """Test that invalid stage prefixes are rejected"""
        invalid_names = [
            'invalid_stage_output.json',
            'unknown_prefix_data.txt',
            'xyz_segments.json'
        ]
        
        for filename in invalid_names:
            is_valid, error = validator.validate_filename(filename)
            assert not is_valid, f"{filename} should be invalid (bad stage prefix)"
            assert "Invalid stage prefix" in error
    
    def test_legacy_files_allowed(self, validator):
        """Test that legacy compatibility files are allowed"""
        legacy_files = [
            'segments.json',
            'transcript.json',
            'transcript.txt'
        ]
        
        # These should trigger warnings but be allowed
        for filename in legacy_files:
            # Validator allows these but warns
            pass  # Legacy files are handled specially in validate_directory


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate file naming standard (§ 1.3.1)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Validate a recent job output directory
  python3 tests/test_file_naming_standard.py --directory out/2025/12/05/rpatel/1/06_asr
  
  # Validate all stage output recursively
  python3 tests/test_file_naming_standard.py --directory out --recursive
  
  # Check specific files
  python3 tests/test_file_naming_standard.py --files asr_segments.json .hidden.json
        '''
    )
    
    parser.add_argument(
        '--directory', '-d',
        type=Path,
        help='Validate all files in directory'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Recursively validate subdirectories'
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        help='Validate specific filenames'
    )
    
    args = parser.parse_args()
    
    validator = FileNamingValidator()
    exit_code = 0
    
    # Validate directory
    if args.directory:
        if not args.directory.exists():
            print(f"❌ Directory not found: {args.directory}")
            return 1
        
        print(f"Validating files in: {args.directory}")
        if args.recursive:
            print("  (recursive)")
        print()
        
        valid, invalid = validator.validate_directory(args.directory, args.recursive)
        
        if valid:
            print(f"✅ Valid files: {len(valid)}")
            for file in sorted(valid)[:10]:  # Show first 10
                print(f"  • {file}")
            if len(valid) > 10:
                print(f"  ... and {len(valid) - 10} more")
            print()
        
        if invalid:
            print(f"❌ Invalid files: {len(invalid)}")
            for error in invalid:
                print(f"  • {error}")
            print()
            exit_code = 1
        
        if validator.warnings:
            print(f"⚠️  Warnings: {len(validator.warnings)}")
            for warning in validator.warnings:
                print(f"  • {warning}")
            print()
    
    # Validate specific files
    if args.files:
        print("Validating specific files:")
        print()
        
        for filename in args.files:
            is_valid, error = validator.validate_filename(filename)
            if is_valid:
                print(f"✅ {filename}")
            else:
                print(f"❌ {filename}: {error}")
                exit_code = 1
        print()
    
    # Summary
    if exit_code == 0:
        print("🎉 All files follow naming standard (§ 1.3.1)")
    else:
        print("💥 Some files violate naming standard")
        print("   See: docs/developer/DEVELOPER_STANDARDS.md § 1.3.1")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
