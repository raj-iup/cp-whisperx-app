# TRD: User Profile Management System

**ID:** TRD-2025-12-10-05  
**Created:** 2025-12-10  
**Status:** Draft  
**Priority:** High  
**Target Release:** v3.2  
**Related Documents:**
- BRD-2025-12-10-05-user-profile-management.md
- PRD-2025-12-10-05-user-profile-management.md

---

## Technical Overview

### System Architecture

**New Components:**

```
cp-whisperx-app/
├── shared/
│   └── user_profile.py          # User profile management module (NEW)
├── tools/
│   └── migrate-to-user-profile.py  # Migration script (NEW)
├── tests/
│   ├── unit/
│   │   ├── test_user_profile.py     # Unit tests (NEW)
│   │   └── test_user_profile_migration.py  # Migration tests (NEW)
│   └── integration/
│       └── test_user_profile_integration.py  # Integration tests (NEW)
└── ~/.cp-whisperx/
    └── user.profile             # User-specific profile (NEW LOCATION)
```

**Modified Components:**
- `bootstrap.sh` - Add profile creation prompts
- `bootstrap.ps1` - Add profile creation prompts (Windows)
- `scripts/02_tmdb_enrichment.py` - Use user profile API
- `scripts/05_pyannote_vad.py` - Use user profile API
- `scripts/06_whisperx_asr.py` - Use user profile API
- `scripts/13_ai_summarization.py` - Use user profile API

**Data Flow:**
```
┌─────────────────────────────────────────────────┐
│ User runs bootstrap.sh                          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ Check for ~/.cp-whisperx/user.profile           │
│ - If exists: Load and validate                  │
│ - If missing: Check config/secrets.json         │
│   - If found: Offer migration                   │
│   - If not: Create new profile (interactive)    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ User runs prepare-job.sh                        │
│ → Load user profile                             │
│ → Validate required credentials for workflow    │
│ → Store profile path in job.json                │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ Pipeline runs (run-pipeline.sh)                 │
│ → Each stage loads profile                      │
│ → Get credentials via UserProfile API           │
│ → Execute stage logic                           │
└─────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. User Profile Module (`shared/user_profile.py`)

**File Size:** 400-500 lines  
**Dependencies:** pathlib, json, os, logging  
**Complexity:** Medium

#### Class: UserProfile

**Attributes:**
```python
class UserProfile:
    def __init__(self, data: dict, location: Path):
        self.version: str = data.get('version', '1.0')
        self.user: dict = data.get('user', {})
        self.credentials: dict = data.get('credentials', {})
        self.online_services: dict = data.get('online_services', {})
        self.preferences: dict = data.get('preferences', {})
        self.location: Path = location
        self._data: dict = data  # Raw data for save()
```

**Methods:**

##### load() - Load profile from disk
```python
@staticmethod
def load(path: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> UserProfile:
    """
    Load user profile from disk.
    
    Search order:
    1. path parameter (if provided)
    2. ~/.cp-whisperx/user.profile
    3. config/secrets.json (fallback, deprecated)
    
    Args:
        path: Optional explicit path to profile
        logger: Optional logger for warnings
        
    Returns:
        UserProfile object
        
    Raises:
        FileNotFoundError: No profile found in any location
        ValueError: Invalid JSON or schema
        PermissionError: Cannot read profile file
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Try explicit path first
    if path is not None:
        if not path.exists():
            raise FileNotFoundError(f"Profile not found: {path}")
        return UserProfile._load_from_file(path, logger)
    
    # Try user home directory
    user_profile_path = Path.home() / '.cp-whisperx' / 'user.profile'
    if user_profile_path.exists():
        return UserProfile._load_from_file(user_profile_path, logger)
    
    # Fallback to secrets.json (deprecated)
    secrets_path = Path('config') / 'secrets.json'
    if secrets_path.exists():
        logger.warning(
            "Using deprecated config/secrets.json. "
            "Migrate to user profile: ./tools/migrate-to-user-profile.py"
        )
        return UserProfile._load_from_secrets_json(secrets_path, logger)
    
    # No profile found
    raise FileNotFoundError(
        "No user profile found. Create one:\n"
        "1. Run: ./bootstrap.sh\n"
        "2. Or manually create: ~/.cp-whisperx/user.profile"
    )

@staticmethod
def _load_from_file(path: Path, logger: logging.Logger) -> UserProfile:
    """Load profile from JSON file."""
    # Check file permissions (warn if too permissive)
    stat_info = path.stat()
    if stat_info.st_mode & 0o077:  # Others can read/write
        logger.warning(
            f"Profile permissions too permissive: {oct(stat_info.st_mode)[-3:]}. "
            f"Run: chmod 600 {path}"
        )
    
    # Load JSON
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Validate schema
    UserProfile._validate_schema(data)
    
    return UserProfile(data, path)

@staticmethod
def _validate_schema(data: dict) -> None:
    """Validate profile schema."""
    required_fields = ['version', 'credentials']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate version format
    version = data['version']
    if not re.match(r'^\d+\.\d+$', version):
        raise ValueError(f"Invalid version format: {version}")
```

##### get_credential() - Get credential value
```python
def get_credential(self, service: str, key: str) -> Optional[str]:
    """
    Get credential value.
    
    Args:
        service: Service name (e.g., 'tmdb', 'openai', 'youtube')
        key: Credential key (e.g., 'api_key', 'token')
        
    Returns:
        Credential value or None if not found
        
    Example:
        >>> profile = UserProfile.load()
        >>> tmdb_key = profile.get_credential('tmdb', 'api_key')
    """
    # Check credentials section
    if service in self.credentials:
        if key in self.credentials[service]:
            value = self.credentials[service][key]
            return value if value else None
    
    # Check online_services section
    if service in self.online_services:
        if key in self.online_services[service]:
            value = self.online_services[service][key]
            return value if value else None
    
    return None
```

##### set_credential() - Set credential value
```python
def set_credential(self, service: str, key: str, value: str) -> None:
    """
    Set credential value.
    
    Args:
        service: Service name
        key: Credential key
        value: Credential value
        
    Example:
        >>> profile.set_credential('youtube', 'api_key', 'AIzaSy...')
        >>> profile.save()
    """
    # Update in appropriate section
    if service in self.credentials:
        if service not in self.credentials:
            self.credentials[service] = {}
        self.credentials[service][key] = value
    elif service in self.online_services:
        if service not in self.online_services:
            self.online_services[service] = {}
        self.online_services[service][key] = value
    else:
        # Add to online_services by default
        if 'online_services' not in self._data:
            self._data['online_services'] = {}
        self._data['online_services'][service] = {key: value}
        self.online_services[service] = {key: value}
```

##### validate_for_workflow() - Validate required credentials
```python
def validate_for_workflow(self, workflow: str) -> None:
    """
    Validate required credentials for workflow.
    
    Args:
        workflow: Workflow name ('transcribe', 'translate', 'subtitle')
        
    Raises:
        ValueError: Missing required credentials with helpful message
        
    Example:
        >>> profile.validate_for_workflow('subtitle')
        # Raises if TMDB key missing
    """
    # Define required credentials per workflow
    WORKFLOW_REQUIREMENTS = {
        'transcribe': [
            ('huggingface', 'token', 'HuggingFace token (for WhisperX ASR)'),
        ],
        'translate': [
            ('huggingface', 'token', 'HuggingFace token (for WhisperX ASR)'),
        ],
        'subtitle': [
            ('huggingface', 'token', 'HuggingFace token (for WhisperX ASR)'),
            ('tmdb', 'api_key', 'TMDB API key (for character names)'),
        ],
    }
    
    if workflow not in WORKFLOW_REQUIREMENTS:
        raise ValueError(f"Unknown workflow: {workflow}")
    
    missing = []
    for service, key, description in WORKFLOW_REQUIREMENTS[workflow]:
        value = self.get_credential(service, key)
        if not value:
            missing.append((service, key, description))
    
    if missing:
        error_msg = f"❌ {workflow.capitalize()} workflow requires missing credentials:\n\n"
        for service, key, description in missing:
            error_msg += f"  • {description}\n"
            error_msg += f"    Add to: {self.location or '~/.cp-whisperx/user.profile'}\n"
            error_msg += f"    Path: credentials.{service}.{key}\n\n"
        error_msg += "Fix:\n"
        error_msg += f"  1. Edit: {self.location or '~/.cp-whisperx/user.profile'}\n"
        error_msg += f"  2. Add missing credentials\n"
        error_msg += f"  3. Or run migration: ./tools/migrate-to-user-profile.py\n"
        raise ValueError(error_msg)
```

##### save() - Save profile to disk
```python
def save(self, path: Optional[Path] = None) -> None:
    """
    Save profile to disk with secure permissions.
    
    Args:
        path: Optional explicit path (default: self.location)
        
    Example:
        >>> profile.set_credential('youtube', 'api_key', 'AIza...')
        >>> profile.save()
    """
    save_path = path or self.location
    if save_path is None:
        save_path = Path.home() / '.cp-whisperx' / 'user.profile'
    
    # Ensure parent directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Update internal data
    self._data['version'] = self.version
    self._data['user'] = self.user
    self._data['credentials'] = self.credentials
    self._data['online_services'] = self.online_services
    self._data['preferences'] = self.preferences
    
    # Write JSON
    with open(save_path, 'w') as f:
        json.dump(self._data, f, indent=2)
    
    # Set secure permissions (0600)
    os.chmod(save_path, 0o600)
```

##### create_template() - Create new profile from template
```python
@staticmethod
def create_template(path: Optional[Path] = None) -> UserProfile:
    """
    Create new profile from template.
    
    Args:
        path: Optional explicit path (default: ~/.cp-whisperx/user.profile)
        
    Returns:
        UserProfile object with template data
        
    Example:
        >>> profile = UserProfile.create_template()
        >>> profile.set_credential('tmdb', 'api_key', 'your_key')
        >>> profile.save()
    """
    if path is None:
        path = Path.home() / '.cp-whisperx' / 'user.profile'
    
    template = {
        "version": "1.0",
        "user": {
            "name": "",
            "email": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        "credentials": {
            "huggingface": {"token": ""},
            "tmdb": {"api_key": ""},
            "pyannote": {"token": ""},
            "openai": {"api_key": "", "organization_id": ""},
            "anthropic": {"api_key": ""},
            "google": {"api_key": ""}
        },
        "online_services": {
            "youtube": {"api_key": "", "enabled": False},
            "vimeo": {"access_token": "", "enabled": False}
        },
        "preferences": {
            "default_workflow": "transcribe",
            "default_source_language": "en",
            "ai_provider": "openai",
            "enable_cost_tracking": True
        }
    }
    
    profile = UserProfile(template, path)
    profile.save()
    return profile
```

---

### 2. Migration Tool (`tools/migrate-to-user-profile.py`)

**File Size:** 150-200 lines  
**Dependencies:** pathlib, json, argparse, logging  
**Complexity:** Low

**Functionality:**
1. Parse command-line arguments
2. Load existing `config/secrets.json`
3. Map secrets to new profile schema
4. Create `~/.cp-whisperx/user.profile`
5. Backup secrets.json
6. Validate migration
7. Print summary report

**Implementation:**
```python
#!/usr/bin/env python3
"""
Migrate credentials from config/secrets.json to user profile.

Usage:
    ./tools/migrate-to-user-profile.py [options]

Options:
    --dry-run       Show what would be migrated without making changes
    --backup-dir    Directory for secrets.json backup (default: config/)
    --profile-path  Custom user profile path (default: ~/.cp-whisperx/user.profile)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.user_profile import UserProfile
import json
import argparse
import shutil
from datetime import datetime, timezone

# Mapping from secrets.json keys to profile schema
SECRETS_TO_PROFILE_MAP = {
    'hf_token': ('huggingface', 'token'),
    'tmdb_api_key': ('tmdb', 'api_key'),
    'pyannote_token': ('pyannote', 'token'),
    'PYANNOTE_API_TOKEN': ('pyannote', 'token'),  # Alternative key
    'openai_api_key': ('openai', 'api_key'),
    'anthropic_api_key': ('anthropic', 'api_key'),
    'google_api_key': ('google', 'api_key'),
}

def migrate_secrets(secrets_path: Path, profile_path: Path, dry_run: bool = False) -> dict:
    """
    Migrate credentials from secrets.json to user profile.
    
    Args:
        secrets_path: Path to config/secrets.json
        profile_path: Path to user.profile
        dry_run: If True, show changes without applying
        
    Returns:
        Migration summary dict
    """
    # Load existing secrets
    if not secrets_path.exists():
        print(f"❌ secrets.json not found: {secrets_path}")
        return {'status': 'error', 'message': 'secrets.json not found'}
    
    with open(secrets_path) as f:
        secrets = json.load(f)
    
    print(f"✓ Loaded secrets.json: {len(secrets)} credentials found")
    
    # Create or load profile
    if profile_path.exists():
        print(f"✓ Loading existing profile: {profile_path}")
        profile = UserProfile.load(profile_path)
    else:
        print(f"✓ Creating new profile: {profile_path}")
        profile = UserProfile.create_template(profile_path)
    
    # Migrate credentials
    migrated_count = 0
    skipped = []
    
    for old_key, value in secrets.items():
        if old_key in SECRETS_TO_PROFILE_MAP:
            service, key = SECRETS_TO_PROFILE_MAP[old_key]
            
            # Check if already set
            existing = profile.get_credential(service, key)
            if existing and existing != value:
                print(f"⚠️  Skipping {old_key}: Different value already exists")
                skipped.append(old_key)
                continue
            
            # Set credential
            if not dry_run:
                profile.set_credential(service, key, value)
            print(f"✓ Migrated: {old_key} → credentials.{service}.{key}")
            migrated_count += 1
        else:
            print(f"⚠️  Unknown key: {old_key} (skipped)")
            skipped.append(old_key)
    
    # Save profile
    if not dry_run:
        profile.save()
        print(f"\n✓ Profile saved: {profile_path}")
        print(f"✓ File permissions: 0600 (secure)")
    
    return {
        'status': 'success',
        'migrated': migrated_count,
        'skipped': skipped,
        'profile_path': str(profile_path)
    }

def backup_secrets(secrets_path: Path, backup_dir: Path) -> Path:
    """Backup secrets.json with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'secrets.json.backup_{timestamp}'
    shutil.copy2(secrets_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path

def main():
    parser = argparse.ArgumentParser(
        description='Migrate credentials from secrets.json to user profile'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    parser.add_argument(
        '--backup-dir',
        type=Path,
        default=Path('config'),
        help='Directory for secrets.json backup (default: config/)'
    )
    parser.add_argument(
        '--profile-path',
        type=Path,
        default=Path.home() / '.cp-whisperx' / 'user.profile',
        help='User profile path (default: ~/.cp-whisperx/user.profile)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CP-WhisperX User Profile Migration")
    print("=" * 60)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made\n")
    
    # Paths
    secrets_path = Path('config') / 'secrets.json'
    profile_path = args.profile_path
    
    # Migrate
    result = migrate_secrets(secrets_path, profile_path, args.dry_run)
    
    if result['status'] == 'success' and not args.dry_run:
        # Backup secrets.json
        backup_path = backup_secrets(secrets_path, args.backup_dir)
        
        # Print summary
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"✓ Migrated: {result['migrated']} credentials")
        print(f"✓ Skipped: {len(result['skipped'])} credentials")
        print(f"✓ Profile: {result['profile_path']}")
        print(f"✓ Backup: {backup_path}")
        print("\nNext steps:")
        print(f"  1. Verify profile: cat {profile_path}")
        print(f"  2. Test a job: ./prepare-job.sh --media in/test.mp4")
        print(f"  3. If working, you can delete: {secrets_path}")
    
    return 0 if result['status'] == 'success' else 1

if __name__ == '__main__':
    sys.exit(main())
```

---

### 3. Bootstrap Integration

**Files:** `bootstrap.sh`, `bootstrap.ps1`

**Changes to bootstrap.sh:**
```bash
# After environment setup, before model downloads

echo "========================================"
echo "User Profile Setup"
echo "========================================"

USER_PROFILE="$HOME/.cp-whisperx/user.profile"

if [ -f "$USER_PROFILE" ]; then
    echo "✓ User profile found: $USER_PROFILE"
else
    echo "User profile not found. Would you like to create one? (Y/n)"
    read -r CREATE_PROFILE
    
    if [ "$CREATE_PROFILE" != "n" ] && [ "$CREATE_PROFILE" != "N" ]; then
        # Check for existing secrets.json
        if [ -f "config/secrets.json" ]; then
            echo ""
            echo "Found existing config/secrets.json"
            echo "Would you like to migrate to user profile? (Y/n)"
            read -r MIGRATE
            
            if [ "$MIGRATE" != "n" ] && [ "$MIGRATE" != "N" ]; then
                echo "Running migration..."
                python3 ./tools/migrate-to-user-profile.py
                exit 0
            fi
        fi
        
        # Interactive profile creation
        echo ""
        echo "Let's set up your user profile."
        echo "You can skip optional credentials by pressing Enter."
        echo ""
        
        # HuggingFace token (required for ASR)
        echo "Enter HuggingFace token (required for ASR):"
        echo "  Get token: https://huggingface.co/settings/tokens"
        read -r HF_TOKEN
        
        # TMDB API key (optional)
        echo ""
        echo "Enter TMDB API key (optional, for subtitle workflow) [skip]:"
        echo "  Get key: https://www.themoviedb.org/settings/api"
        read -r TMDB_KEY
        
        # OpenAI API key (optional)
        echo ""
        echo "Enter OpenAI API key (optional, for AI summarization) [skip]:"
        echo "  Get key: https://platform.openai.com/api-keys"
        read -r OPENAI_KEY
        
        # Create profile
        mkdir -p "$HOME/.cp-whisperx"
        cat > "$USER_PROFILE" << EOF
{
  "version": "1.0",
  "user": {
    "name": "",
    "email": "",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "credentials": {
    "huggingface": {
      "token": "$HF_TOKEN"
    },
    "tmdb": {
      "api_key": "$TMDB_KEY"
    },
    "pyannote": {
      "token": "$HF_TOKEN"
    },
    "openai": {
      "api_key": "$OPENAI_KEY",
      "organization_id": ""
    },
    "anthropic": {
      "api_key": ""
    },
    "google": {
      "api_key": ""
    }
  },
  "online_services": {
    "youtube": {
      "api_key": "",
      "enabled": false
    },
    "vimeo": {
      "access_token": "",
      "enabled": false
    }
  },
  "preferences": {
    "default_workflow": "transcribe",
    "default_source_language": "en",
    "ai_provider": "openai",
    "enable_cost_tracking": true
  }
}
EOF
        
        # Set secure permissions
        chmod 600 "$USER_PROFILE"
        
        echo ""
        echo "✓ User profile created: $USER_PROFILE"
        echo "✓ File permissions: 0600 (secure)"
        echo ""
        echo "You can edit your profile anytime:"
        echo "  nano $USER_PROFILE"
    fi
fi

echo ""
```

---

### 4. Stage Refactoring Pattern

**Stages to Update:**
- Stage 02 (TMDB): `scripts/02_tmdb_enrichment.py`
- Stage 05 (PyAnnote VAD): `scripts/05_pyannote_vad.py`
- Stage 06 (WhisperX ASR): `scripts/06_whisperx_asr.py`
- Stage 13 (AI Summarization): `scripts/13_ai_summarization.py`

**Refactoring Pattern (Example: Stage 02 TMDB):**

**BEFORE:**
```python
import json

# Load secrets.json
secrets_path = Path(__file__).parent.parent / 'config' / 'secrets.json'
try:
    with open(secrets_path) as f:
        secrets = json.load(f)
        tmdb_api_key = secrets.get('tmdb_api_key')
except FileNotFoundError:
    logger.error(f"secrets.json not found: {secrets_path}")
    return 1
except json.JSONDecodeError:
    logger.error(f"Invalid JSON in secrets.json")
    return 1

if not tmdb_api_key:
    logger.error("TMDB API key not found in secrets.json")
    return 1
```

**AFTER:**
```python
from shared.user_profile import UserProfile

# Load user profile
try:
    profile = UserProfile.load()
    
    # Validate required credentials
    profile.validate_for_workflow('subtitle')
    
    # Get TMDB API key
    tmdb_api_key = profile.get_credential('tmdb', 'api_key')
    
except FileNotFoundError as e:
    logger.error(f"User profile not found: {e}")
    logger.error("Run bootstrap: ./bootstrap.sh")
    return 1
except ValueError as e:
    logger.error(f"Missing credentials: {e}")
    return 1
```

---

## Testing Plan

### Unit Tests (`tests/unit/test_user_profile.py`)

**Test Coverage:** 90%+

**Test Suite:**
```python
class TestUserProfileLoad:
    def test_load_from_user_profile_location(self):
        """Load profile from ~/.cp-whisperx/user.profile"""
        
    def test_load_fallback_to_secrets_json(self):
        """Fallback to config/secrets.json if profile missing"""
        
    def test_load_explicit_path(self):
        """Load profile from explicit path parameter"""
        
    def test_load_missing_profile_raises(self):
        """Raise FileNotFoundError if no profile found"""
        
    def test_load_invalid_json_raises(self):
        """Raise ValueError if JSON invalid"""
        
    def test_load_missing_required_field_raises(self):
        """Raise ValueError if required field missing"""
        
    def test_load_validates_permissions(self):
        """Warn if file permissions too permissive"""


class TestUserProfileCredentials:
    def test_get_credential_existing(self):
        """Get existing credential returns value"""
        
    def test_get_credential_missing_returns_none(self):
        """Get missing credential returns None"""
        
    def test_get_credential_empty_string_returns_none(self):
        """Get credential with empty string returns None"""
        
    def test_set_credential_new(self):
        """Set new credential updates profile"""
        
    def test_set_credential_existing(self):
        """Set existing credential overwrites value"""
        
    def test_set_credential_new_service(self):
        """Set credential for new service creates section"""


class TestUserProfileValidation:
    def test_validate_transcribe_workflow_valid(self):
        """Validate transcribe workflow with HF token passes"""
        
    def test_validate_subtitle_workflow_valid(self):
        """Validate subtitle workflow with HF + TMDB keys passes"""
        
    def test_validate_transcribe_workflow_missing_hf_raises(self):
        """Validate transcribe workflow without HF token raises"""
        
    def test_validate_subtitle_workflow_missing_tmdb_raises(self):
        """Validate subtitle workflow without TMDB key raises"""
        
    def test_validate_unknown_workflow_raises(self):
        """Validate unknown workflow raises ValueError"""


class TestUserProfileSave:
    def test_save_to_default_location(self):
        """Save profile to default location"""
        
    def test_save_to_explicit_path(self):
        """Save profile to explicit path"""
        
    def test_save_sets_permissions_0600(self):
        """Save profile with 0600 permissions"""
        
    def test_save_creates_parent_directory(self):
        """Save profile creates parent directory if missing"""


class TestUserProfileTemplate:
    def test_create_template_default_location(self):
        """Create template profile at default location"""
        
    def test_create_template_explicit_path(self):
        """Create template profile at explicit path"""
        
    def test_create_template_has_all_sections(self):
        """Template profile has all required sections"""
        
    def test_create_template_sets_permissions(self):
        """Template profile has 0600 permissions"""
```

---

### Integration Tests (`tests/integration/test_user_profile_integration.py`)

**Test Coverage:** 80%+

**Test Suite:**
```python
class TestStageIntegration:
    def test_stage02_tmdb_loads_profile(self):
        """Stage 02 (TMDB) successfully loads user profile"""
        
    def test_stage06_asr_loads_hf_token(self):
        """Stage 06 (WhisperX ASR) loads HuggingFace token"""
        
    def test_stage13_ai_summarization_loads_openai_key(self):
        """Stage 13 (AI Summarization) loads OpenAI API key"""


class TestBootstrapIntegration:
    def test_bootstrap_creates_profile(self):
        """bootstrap.sh creates user profile interactively"""
        
    def test_bootstrap_skips_if_exists(self):
        """bootstrap.sh skips profile creation if exists"""
        
    def test_bootstrap_offers_migration(self):
        """bootstrap.sh offers migration from secrets.json"""


class TestMigrationIntegration:
    def test_migrate_all_credentials(self):
        """migrate-to-user-profile.py migrates all credentials"""
        
    def test_migrate_creates_backup(self):
        """Migration creates backup of secrets.json"""
        
    def test_migrate_sets_permissions(self):
        """Migration sets 0600 permissions on profile"""


class TestMultiUserIntegration:
    def test_separate_profiles_per_user(self):
        """Different OS users have separate profiles"""
        
    def test_profile_permissions_prevent_cross_user_read(self):
        """User A cannot read User B's profile"""
```

---

## Security Considerations

### File Permissions

**Implementation:**
```python
import os

def set_secure_permissions(path: Path) -> None:
    """Set secure file permissions (0600)."""
    os.chmod(path, 0o600)  # Owner read/write only

def validate_permissions(path: Path, logger: logging.Logger) -> None:
    """Validate file permissions, warn if too permissive."""
    stat_info = path.stat()
    mode = stat_info.st_mode
    
    # Check if group or others can read
    if mode & 0o077:
        logger.warning(
            f"Profile permissions too permissive: {oct(mode)[-3:]}. "
            f"Run: chmod 600 {path}"
        )
```

### Credential Handling

**Rules:**
1. **Never log credential values** (only presence/absence)
2. **Load credentials on-demand** (not at module import)
3. **Clear from memory after use** (if possible)
4. **Validate format before use** (API key patterns)

**Example:**
```python
# ❌ WRONG - Logs credential value
logger.info(f"Using API key: {api_key}")

# ✅ CORRECT - Logs presence only
logger.info(f"TMDB API key loaded: {'yes' if api_key else 'no'}")
```

---

## Performance Considerations

### Profile Caching

**Strategy:** Load profile once per pipeline run, cache in memory

**Implementation:**
```python
# In run-pipeline.py
class Pipeline:
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir
        self._profile = None  # Lazy load
    
    @property
    def profile(self) -> UserProfile:
        """Lazy load and cache user profile."""
        if self._profile is None:
            self._profile = UserProfile.load()
        return self._profile

# In stages
def run_stage(pipeline: Pipeline, stage_name: str) -> int:
    # Profile loaded once, reused across stages
    api_key = pipeline.profile.get_credential('tmdb', 'api_key')
```

---

## Migration Strategy

### Phase 1: Introduce User Profile (v3.2)
- Add `shared/user_profile.py` module
- Add migration tool
- Update bootstrap scripts
- **Maintain backward compatibility** (fallback to secrets.json)

### Phase 2: Deprecate secrets.json (v3.3)
- Log warnings when using secrets.json
- Force migration during bootstrap
- Update documentation

### Phase 3: Remove secrets.json Support (v3.4)
- Remove fallback logic
- Require user profile for all jobs

---

## Documentation Updates

### User Guide
- `docs/user-guide/user-profile-setup.md` (NEW)
- `docs/user-guide/configuration.md` (UPDATE)
- `docs/user-guide/troubleshooting.md` (UPDATE)

### Developer Guide
- `docs/developer/user-profile-api.md` (NEW)
- `docs/developer/DEVELOPER_STANDARDS.md` (ADD § 22)

---

## Timeline

| Day | Task | Hours |
|-----|------|-------|
| Day 1 | UserProfile module + unit tests | 4-5 hours |
| Day 2 | Migration tool + bootstrap | 3-4 hours |
| Day 3 | Stage refactoring + docs | 3-4 hours |
| **Total** | | **10-13 hours** |

---

## Acceptance Criteria

- [ ] `shared/user_profile.py` implemented (400-500 lines)
- [ ] Migration tool: `tools/migrate-to-user-profile.py`
- [ ] Bootstrap scripts updated (interactive profile creation)
- [ ] All stages (02, 05, 06, 13) use UserProfile API
- [ ] Unit tests: 90%+ coverage
- [ ] Integration tests: 80%+ coverage
- [ ] Documentation: User guide + developer guide
- [ ] Multi-user tested (2+ users on same system)
- [ ] File permissions: 0600 enforced

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-10 | System | Initial draft |
