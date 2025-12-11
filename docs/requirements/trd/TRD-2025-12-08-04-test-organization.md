# TRD: Organized Test Structure

**ID:** TRD-2025-12-08-04  
**Created:** 2025-12-08  
**Status:** Approved  
**Related BRD:** [BRD-2025-12-08-04](../brd/BRD-2025-12-08-04-test-organization.md)

---

## Technical Overview

Reorganize test directory with clear categorization by test type and scope.

---

## Architecture Changes

### New Structure
```
tests/
├── README.md              # Testing guidelines
├── unit/                  # Unit tests (fast, <1s)
│   └── test_*.py
├── integration/           # Integration tests (real dependencies)
│   └── test_*_integration.py
├── functional/            # E2E workflow tests (minutes)
│   ├── README.md
│   └── test_*_workflow.py
├── manual/                # Manual test scripts
│   ├── README.md
│   ├── glossary/
│   │   ├── test-glossary-quickstart.sh
│   │   └── test-glossary-quickstart.ps1
│   ├── source-separation/
│   └── venv/
├── fixtures/              # Test data
│   ├── README.md
│   ├── audio/
│   ├── video/
│   └── expected/
├── helpers/               # Test utilities
└── reports/               # Test output
```

---

## Implementation Requirements

### Migration Steps

**Step 1: Create directories**
```bash
mkdir -p tests/{functional,manual/{glossary,source-separation,venv},fixtures/{audio,video,expected}}
```

**Step 2: Move scripts from root**
```bash
mv test-glossary-quickstart.sh tests/manual/glossary/
mv test-glossary-quickstart.ps1 tests/manual/glossary/
```

**Step 3: Categorize existing tests**
```bash
# Audit 23 test files in tests/
# Move to appropriate category:
# - Fast, isolated → unit/
# - Module interaction → integration/
# - Workflow/E2E → functional/
# - Shell scripts → manual/
```

**Step 4: Create documentation**
```bash
# Create READMEs for each category
```

---

## Testing Requirements

### Verification
```bash
# Verify no test files in root
ls -la *.sh *.ps1 test*.py 2>/dev/null | wc -l  # Should be 0

# Verify tests still run
pytest tests/unit/           # Fast tests
pytest tests/integration/    # Integration tests
pytest tests/functional/     # E2E tests

# Verify manual scripts work
./tests/manual/glossary/test-glossary-quickstart.sh
```

---

## Documentation Updates

- [ ] **tests/README.md** - Testing guidelines
- [ ] **tests/functional/README.md** - Functional test guide
- [ ] **tests/manual/README.md** - Manual script guide
- [ ] **tests/fixtures/README.md** - Test data guide
- [ ] **Copilot Instructions** - Test placement rules (AD-013)
- [ ] **DEVELOPER_STANDARDS.md** - Testing section update

---

## Test Categorization Guidelines

**Unit Tests:**
- Single function/class
- No external dependencies
- Fast (<1s each)
- Mock external services

**Integration Tests:**
- Module interaction
- Real dependencies
- Medium speed (seconds)
- Verify interfaces

**Functional Tests:**
- Complete workflows
- End-to-end scenarios
- Slow (minutes)
- Real data

**Manual Scripts:**
- Developer testing
- Not automated
- Shell/PowerShell
- Interactive

---

## Related Documents

- **BRD:** [BRD-2025-12-08-04-test-organization.md](../brd/BRD-2025-12-08-04-test-organization.md)
- **AD-013:** ARCHITECTURE.md § AD-013

---

**Version:** 1.0 | **Status:** Approved (Pending Implementation)  
**Effort:** 2-3 hours
