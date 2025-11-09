#!/usr/bin/env python3
"""
Patch pyannote.audio to work with torchaudio 2.8 + numpy 2.x

This script adds `from __future__ import annotations` to io.py
to defer type annotation evaluation, preventing import-time issues.
"""

import sys
from pathlib import Path

def patch_pyannote_io():
    """Patch pyannote.audio io.py to use deferred annotations"""
    
    # Find the io.py file
    import pyannote.audio
    pyannote_path = Path(pyannote.audio.__file__).parent
    io_file = pyannote_path / "core" / "io.py"
    
    if not io_file.exists():
        print(f"Error: {io_file} not found")
        return False
    
    # Read the file
    with open(io_file, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'from __future__ import annotations' in content:
        print("✓ pyannote.audio already patched")
        return True
    
    # Add the future import after the license header (before the docstring)
    lines = content.split('\n')
    
    # Find where to insert (after license, before docstring)
    insert_idx = 0
    in_license = False
    for i, line in enumerate(lines):
        if line.startswith('# MIT License') or line.startswith('# Copyright'):
            in_license = True
        elif in_license and (line.startswith('"""') or line.startswith('import') or (line and not line.startswith('#'))):
            insert_idx = i
            break
    
    # Insert the future import
    if insert_idx > 0:
        lines.insert(insert_idx, 'from __future__ import annotations')
        lines.insert(insert_idx + 1, '')
        
        # Write back
        new_content = '\n'.join(lines)
        with open(io_file, 'w') as f:
            f.write(new_content)
        
        print(f"✓ Patched {io_file}")
        print("  Added: from __future__ import annotations")
        return True
    else:
        print(f"Error: Could not find insertion point in {io_file}")
        return False

if __name__ == '__main__':
    try:
        success = patch_pyannote_io()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
