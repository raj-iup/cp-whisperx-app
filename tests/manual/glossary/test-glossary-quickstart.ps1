# ============================================================================
# CP-WhisperX-App Glossary Quick Test (Windows/PowerShell)
# ============================================================================
# Version: 1.0.0
# Date: 2025-12-03
#
# Quick test script for glossary stage functionality
# PowerShell equivalent of test-glossary-quickstart.sh for Windows environments
# ============================================================================

#Requires -Version 5.1

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$GLOSSARY_DIR = Join-Path $PROJECT_ROOT "glossary"
$SCRIPTS_DIR = Join-Path $PROJECT_ROOT "scripts"
$COMMON_VENV = Join-Path $PROJECT_ROOT "venv\common"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "GLOSSARY STAGE QUICK TEST" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

# Check if common venv exists
if (-not (Test-Path $COMMON_VENV)) {
    Write-Host "[ERROR] Environment not found: $COMMON_VENV" -ForegroundColor Red
    Write-Host "Run bootstrap first: .\bootstrap.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if glossary directory exists
if (-not (Test-Path $GLOSSARY_DIR)) {
    Write-Host "[INFO] Creating glossary directory: $GLOSSARY_DIR" -ForegroundColor Blue
    New-Item -ItemType Directory -Path $GLOSSARY_DIR -Force | Out-Null
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST DATA SETUP
# ═══════════════════════════════════════════════════════════════════════════

Write-Host "[INFO] Setting up test data..." -ForegroundColor Blue

# Create test glossary files
$testGlossaries = @{
    "names_hi.csv" = @"
original,replacement,language,category,confidence
राम,Ram,hi,name,1.0
सीता,Sita,hi,name,1.0
लक्ष्मण,Lakshmana,hi,name,1.0
"@
    "places_hi.csv" = @"
original,replacement,language,category,confidence
अयोध्या,Ayodhya,hi,place,1.0
मुंबई,Mumbai,hi,place,1.0
दिल्ली,Delhi,hi,place,1.0
"@
    "terms_hi.csv" = @"
original,replacement,language,category,confidence
धन्यवाद,thank you,hi,term,0.9
नमस्ते,hello,hi,term,0.9
"@
}

foreach ($filename in $testGlossaries.Keys) {
    $filepath = Join-Path $GLOSSARY_DIR $filename
    $testGlossaries[$filename] | Out-File -FilePath $filepath -Encoding UTF8
    Write-Host "✓ Created: $filename" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "[INFO] Testing glossary loading..." -ForegroundColor Blue

# Set environment variables
$env:VIRTUAL_ENV = $COMMON_VENV
$env:PATH = "$COMMON_VENV\Scripts;$env:PATH"
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$PROJECT_ROOT;$env:PYTHONPATH" } else { $PROJECT_ROOT }

# Run Python test
$pythonExe = Join-Path $COMMON_VENV "Scripts\python.exe"

$testCode = @"
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, r'$PROJECT_ROOT')

from shared.logger import get_logger
logger = get_logger('glossary_test')

# Test imports
try:
    from scripts.glossary_loader import load_glossaries
    logger.info('✓ Glossary loader imported successfully')
except ImportError as e:
    logger.error(f'Failed to import glossary_loader: {e}')
    sys.exit(1)

# Test loading
glossary_dir = Path(r'$GLOSSARY_DIR')
logger.info(f'Loading glossaries from: {glossary_dir}')

try:
    glossaries = load_glossaries(glossary_dir, language='hi')
    logger.info(f'✓ Loaded {len(glossaries)} glossary entries')
    
    # Show some entries
    for i, entry in enumerate(list(glossaries.items())[:5]):
        original, replacement = entry
        logger.info(f'  {i+1}. "{original}" → "{replacement}"')
    
    logger.info('━' * 60)
    logger.info('✓ GLOSSARY TEST PASSED')
    logger.info('━' * 60)
    sys.exit(0)
    
except Exception as e:
    logger.error(f'✗ GLOSSARY TEST FAILED: {e}', exc_info=True)
    sys.exit(1)
"@

try {
    $testCode | & $pythonExe -
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host "✓ GLOSSARY QUICK TEST COMPLETE" -ForegroundColor Green
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
        Write-Host ""
        Write-Host "Test glossary files created in: $GLOSSARY_DIR" -ForegroundColor Blue
        Write-Host ""
        exit 0
    } else {
        Write-Host ""
        Write-Host "✗ Glossary test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host ""
    Write-Host "[CRITICAL] Failed to run glossary test: $_" -ForegroundColor Red
    exit 1
}
