# Development Process Guide

**Standard processes for code and architecture changes in CP-WhisperX-App**

---

## 🔄 Process Overview

Every code or architecture change must follow these steps:

1. **Analyze** - Understand the issue/requirement
2. **Plan** - Design the solution
3. **Implement** - Make minimal, surgical changes
4. **Test** - Verify the fix works
5. **Document** - Update relevant documentation
6. **Commit** - Commit with clear message

---

## 📋 Step-by-Step Process

### 1. Analyze the Issue

**Before making any changes:**

- [ ] Read the error logs completely
- [ ] Understand the root cause
- [ ] Check existing documentation
- [ ] Review related code sections

**Key Questions:**
- What is the exact error?
- When does it occur?
- What are the expected vs actual behaviors?
- Are there any side effects?

### 2. Plan the Solution

**Design before coding:**

- [ ] Identify minimal changes needed
- [ ] Check for impacts on other components
- [ ] Review architecture constraints
- [ ] Consider backward compatibility

**Key Principles:**
- **Minimal changes** - Change as few lines as possible
- **Surgical precision** - Target specific issue only
- **No feature creep** - Don't add unrelated improvements
- **Preserve working code** - Don't refactor unnecessarily

### 3. Implement Changes

**Coding standards:**

```bash
# Make targeted edits
- Use edit tool for single-line changes
- Preserve existing formatting
- Add comments only where needed
- Follow existing code style
```

**File Organization:**
- Scripts: `/scripts/`
- Shared utilities: `/shared/`
- Documentation: `/docs/`
- Configuration: `/config/`

### 4. Test the Changes

**Always test before committing:**

```bash
# Test the specific fix
./run-pipeline.sh -j <test-job-id>

# Check logs
tail -f out/<date>/<user>/<job>/logs/*.log

# Verify no regressions
./health-check.sh
```

**Test Checklist:**
- [ ] Error is fixed
- [ ] No new errors introduced
- [ ] Existing functionality works
- [ ] Logs are clear and informative

### 5. Document Changes

**Update documentation immediately:**

#### For Bug Fixes:
- Update troubleshooting guide if user-facing
- Add debug notes in technical docs
- Document workarounds if applicable

#### For Features:
- Update QUICKSTART.md with examples
- Add feature guide in user-guide/features/
- Update architecture docs if needed
- Add to reference/changelog.md

#### For Architecture Changes:
- Update technical/architecture.md
- Update technical/pipeline.md if relevant
- Document in technical/multi-environment.md if env-related
- Create migration guide if breaking change

**Documentation Standards:**
```markdown
# Use clear headings
- Write for the user, not yourself
- Include examples
- Keep technical details in technical/
- Keep user content simple
```

### 6. Commit Changes

**Commit message format:**

```bash
# Format: <type>: <short description>

# Types:
fix: Bug fix
feat: New feature
docs: Documentation only
refactor: Code restructuring
test: Test additions/changes
chore: Build/tooling changes

# Examples:
git commit -m "fix: source_separation stage environment mapping"
git commit -m "docs: reorganize documentation structure"
git commit -m "feat: add anti-hallucination system"
```

---

## 📁 Documentation Organization

**Always maintain this structure:**

```
docs/
├── INDEX.md                 # Master index
├── QUICKSTART.md            # Quick start guide
│
├── user-guide/              # User-facing docs
│   ├── README.md
│   ├── bootstrap.md
│   ├── prepare-job.md
│   ├── workflows.md
│   ├── troubleshooting.md
│   └── features/
│       ├── anti-hallucination.md
│       ├── source-separation.md
│       └── scene-selection.md
│
├── technical/               # Technical docs
│   ├── README.md
│   ├── architecture.md
│   ├── pipeline.md
│   ├── multi-environment.md
│   └── language-support.md
│
├── reference/               # Reference docs
│   ├── README.md
│   ├── citations.md
│   ├── license.md
│   └── changelog.md
│
└── archive/                 # Historical docs
```

---

## 🔍 Code Review Checklist

**Before considering changes complete:**

- [ ] Code follows existing patterns
- [ ] No hardcoded values (use config)
- [ ] Error handling is comprehensive
- [ ] Logging is informative
- [ ] Comments explain "why" not "what"
- [ ] No redundant code
- [ ] No dead code
- [ ] Variable names are clear
- [ ] Functions are focused and small

---

## 🚨 Common Pitfalls to Avoid

### ❌ Don't Do This:

1. **Over-refactoring**
   - Don't restructure working code unnecessarily
   - Don't "clean up" unrelated sections
   
2. **Incomplete fixes**
   - Don't fix symptoms, fix root causes
   - Don't leave debug code in production
   
3. **Poor documentation**
   - Don't skip documentation updates
   - Don't use vague descriptions
   
4. **Breaking changes**
   - Don't change public APIs without migration plan
   - Don't remove features without deprecation notice

### ✅ Do This Instead:

1. **Surgical changes**
   - Target the specific issue
   - Preserve existing working behavior
   
2. **Complete solutions**
   - Fix root cause
   - Clean up debug code
   - Update tests
   
3. **Comprehensive documentation**
   - Update all affected docs
   - Include examples
   - Update changelog
   
4. **Backward compatibility**
   - Provide migration guides
   - Deprecate before removing
   - Version changes appropriately

---

## 📊 Architecture Change Template

**Use this template for significant architecture changes:**

```markdown
## Architecture Change: <Title>

### Problem Statement
- What issue are we solving?
- Why is the current approach insufficient?

### Proposed Solution
- High-level design
- Component changes
- Data flow diagrams

### Impact Analysis
- Affected components
- Breaking changes
- Migration path

### Implementation Plan
1. Phase 1: ...
2. Phase 2: ...
3. Phase 3: ...

### Testing Strategy
- Unit tests
- Integration tests
- Regression tests

### Documentation Updates
- [ ] Architecture diagram
- [ ] API documentation
- [ ] User guides
- [ ] Migration guide

### Rollback Plan
- How to revert if issues arise
- Data backup strategy
```

---

## 🛠️ Emergency Fix Process

**For critical production issues:**

1. **Assess severity** (5 min)
   - Is system down?
   - Data loss risk?
   - User impact scope?

2. **Quick fix** (30 min)
   - Minimal change to restore service
   - Document what was done
   - Log for investigation

3. **Root cause analysis** (2 hours)
   - Find underlying issue
   - Design proper fix
   - Test thoroughly

4. **Permanent fix** (varies)
   - Implement properly
   - Full testing
   - Documentation
   - Deploy

5. **Post-mortem** (1 hour)
   - What happened?
   - Why wasn't it caught?
   - Prevention strategy

---

## 📝 Documentation Maintenance

**Keep docs current:**

### Weekly
- Review and update troubleshooting guide
- Add new common issues
- Update examples

### Per Release
- Update changelog
- Review all docs for accuracy
- Update version numbers
- Check all links

### Per Architecture Change
- Update architecture diagrams
- Update component relationships
- Document new patterns
- Archive old approaches

---

## ✅ Definition of Done

**A change is complete when:**

- [ ] Code is committed
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] No TODO comments left
- [ ] Logs reviewed
- [ ] No warnings in output
- [ ] Peer reviewed (if applicable)

---

## 📞 Getting Help

**If stuck:**

1. Check troubleshooting docs
2. Review similar issues in archive
3. Check git history for context
4. Review logs with DEBUG_MODE=true
5. Ask for help with specific error details

---

**Remember: Good processes prevent bad code. Follow this guide for every change.**
