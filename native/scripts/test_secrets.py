#!/usr/bin/env python3
"""
Test secrets loading for native MPS pipeline.
Verifies that API keys and tokens are properly loaded from config/secrets.json
"""
import sys
from pathlib import Path

sys.path.insert(0, 'native/utils')

from secrets import get_secrets_manager

def main():
    print("=" * 60)
    print("🔑 Secrets Manager Test")
    print("=" * 60)
    print()
    
    # Load secrets
    secrets_manager = get_secrets_manager('config/secrets.json')
    
    # Get summary (masked)
    summary = secrets_manager.summary()
    
    print("Loaded Secrets (masked):")
    print("-" * 40)
    for key, value in summary.items():
        status = "✓" if value != "Not set" else "✗"
        print(f"  {status} {key:20s}: {value}")
    print()
    
    # Check critical secrets
    print("Secret Availability:")
    print("-" * 40)
    
    tmdb_key = secrets_manager.get_tmdb_api_key()
    hf_token = secrets_manager.get_hf_token()
    pyannote_token = secrets_manager.get_pyannote_token()
    
    if tmdb_key:
        print(f"  ✓ TMDB API Key     : Available ({len(tmdb_key)} chars)")
    else:
        print(f"  ✗ TMDB API Key     : Not configured")
    
    if hf_token:
        print(f"  ✓ HuggingFace Token: Available ({len(hf_token)} chars)")
    else:
        print(f"  ✗ HuggingFace Token: Not configured")
    
    if pyannote_token:
        print(f"  ✓ PyAnnote Token   : Available ({len(pyannote_token)} chars)")
    else:
        print(f"  ✗ PyAnnote Token   : Not configured")
    
    print()
    
    # Test export to environment
    print("Testing Export to Environment:")
    print("-" * 40)
    secrets_manager.export_to_env()
    
    import os
    env_keys = ['TMDB_API_KEY', 'HF_TOKEN', 'PYANNOTE_TOKEN']
    for key in env_keys:
        if os.getenv(key):
            print(f"  ✓ {key:20s}: Exported")
        else:
            print(f"  ✗ {key:20s}: Not exported")
    
    print()
    print("=" * 60)
    
    # Summary
    if all([tmdb_key, hf_token, pyannote_token]):
        print("✅ All secrets configured correctly!")
    elif tmdb_key:
        print("⚠️  TMDB API key configured (others optional)")
    else:
        print("❌ No secrets configured")
        print()
        print("To configure secrets:")
        print("  1. Edit config/secrets.json")
        print("  2. Add your API keys and tokens")
        print("  3. Re-run this test")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
