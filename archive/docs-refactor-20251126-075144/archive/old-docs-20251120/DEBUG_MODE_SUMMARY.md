# Bootstrap Debug Mode Summary

## Question: Does the bootstrap script run in debug mode?

**Answer: No** - Debug mode is **OFF by default** and must be explicitly enabled with the `--debug` flag.

## Default Behavior (Normal Mode)

```bash
./bootstrap.sh
# Or
.\bootstrap.ps1
```

**Output:**
- ✅ Clean, concise messages
- ✅ Section headers (CREATING ENVIRONMENTS, etc.)
- ✅ Progress indicators (Creating, Installing, Success)
- ✅ **Quiet pip installs** (`--quiet` flag)
- ✅ Only errors/warnings shown for troubleshooting

**Example output:**
```
━━━ CP-WHISPERX-APP BOOTSTRAP ━━━
  Platform: Darwin (arm64)
  Detected: Apple Silicon (M1/M2/M3) with MPS + MLX
  Python: Python 3.11.5

━━━ CREATING ENVIRONMENTS ━━━

━━━ ENVIRONMENT: common ━━━
  Core utilities: job management, logging, muxing
  Creating virtual environment...
  Upgrading pip...
  Installing from requirements-common.txt...
✓ Dependencies installed
✓ Environment ready: venv/common

...
```

## Debug Mode (Opt-In)

```bash
./bootstrap.sh --debug
# Or
.\bootstrap.ps1 -Debug
```

**Output:**
- ✅ All normal output PLUS:
- ✅ **Verbose pip install output** (no `--quiet`)
- ✅ Package-by-package installation progress
- ✅ Dependency resolution details
- ✅ Useful for troubleshooting installation issues

**Example output:**
```
━━━ CP-WHISPERX-APP BOOTSTRAP ━━━
  Platform: Darwin (arm64)
  ...

━━━ ENVIRONMENT: common ━━━
  Core utilities: job management, logging, muxing
  Creating virtual environment...
  Upgrading pip...
Collecting pip
  Downloading pip-24.0-py3-none-any.whl (2.1 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 5.0 MB/s eta 0:00:00
Collecting setuptools
  Downloading setuptools-69.0.3-py3-none-any.whl (821 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 821/821 kB 10.0 MB/s eta 0:00:00
Successfully installed pip-24.0 setuptools-69.0.3 wheel-0.42.0
  Installing from requirements-common.txt...
Collecting ffmpeg-python>=0.2.0
  Downloading ffmpeg_python-0.2.0-py3-none-any.whl (25 kB)
Collecting python-dotenv>=1.0.0
  ...
✓ Dependencies installed
✓ Environment ready: venv/common

...
```

## Implementation Details

### Bash Script (`scripts/bootstrap.sh`)

```bash
# Parse arguments
DEBUG_MODE=false  # Default: OFF
FORCE_RECREATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug) DEBUG_MODE=true; shift ;;  # User must opt-in
        --force) FORCE_RECREATE=true; shift ;;
        ...
    esac
done

# In create_environment function:
if [ "$DEBUG_MODE" = true ]; then
    python -m pip install -r "$req_file"  # Verbose
else
    python -m pip install --quiet -r "$req_file"  # Quiet
fi
```

### PowerShell Script (`scripts/bootstrap.ps1`)

```powershell
param(
    [switch]$Debug,  # Default: $false
    [switch]$Force,
    [switch]$Help
)

# In Create-Environment function:
if ($Debug) {
    & python -m pip install -r $reqPath  # Verbose
} else {
    & python -m pip install --quiet -r $reqPath  # Quiet
}
```

## When to Use Debug Mode

### Use `--debug` when:
- ❌ Bootstrap fails with unclear error
- ❌ Package installation hangs
- ❌ Dependency conflict suspected
- ❌ Need to see what's being installed
- ❌ Troubleshooting network/proxy issues
- ❌ Contributing to project (development)

### Normal mode is fine when:
- ✅ First-time setup on working system
- ✅ Just want it to work
- ✅ Following quick-start guide
- ✅ Production deployments

## Command Reference

| Command | Mode | Output Level |
|---------|------|--------------|
| `./bootstrap.sh` | Normal | Concise, quiet pip |
| `./bootstrap.sh --debug` | Debug | Verbose, full pip output |
| `./bootstrap.sh --force` | Normal | Recreates envs, quiet |
| `./bootstrap.sh --debug --force` | Debug | Recreates envs, verbose |
| `.\bootstrap.ps1` | Normal | Concise, quiet pip |
| `.\bootstrap.ps1 -Debug` | Debug | Verbose, full pip output |
| `.\bootstrap.ps1 -Force` | Normal | Recreates envs, quiet |
| `.\bootstrap.ps1 -Debug -Force` | Debug | Recreates envs, verbose |

## Example: Troubleshooting a Failure

**Scenario:** Bootstrap fails with "ERROR: No matching distribution found"

**Step 1:** Try with debug to see which package fails
```bash
./bootstrap.sh --debug
```

**Step 2:** Look for the failing package in output
```
Collecting torch>=2.0.0
  ERROR: Could not find a version that satisfies the requirement torch>=2.0.0
  ERROR: No matching distribution found for torch>=2.0.0
```

**Step 3:** Fix (e.g., update Python version, fix network, etc.)

**Step 4:** Retry with force
```bash
./bootstrap.sh --force
```

## Summary

- **Default:** Debug mode is **OFF** (quiet, clean output)
- **Enable:** Use `--debug` flag for verbose pip output
- **When:** Use debug mode only for troubleshooting
- **Updated:** Both Bash and PowerShell scripts now respect debug flag
