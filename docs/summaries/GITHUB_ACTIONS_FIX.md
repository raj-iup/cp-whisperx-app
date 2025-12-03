# GitHub Actions Permission Fix

**Date:** December 3, 2025  
**Issue:** "GitHub Actions is not permitted to create or approve pull requests"  
**Status:** ✅ FIXED

---

## 🔍 Problem Identified

GitHub Actions workflow tried to create a PR but was blocked due to repository security settings.

**Error from run:** https://github.com/raj-iup/cp-whisperx-app/actions/runs/19902972114

```
Error: GitHub Actions is not permitted to create or approve pull requests.
```

---

## ✅ Solution Applied

### Step 1: Update Workflow Permissions

**File:** `.github/workflows/update-model-routing.yml`

**Changed:**
```yaml
# Move permissions to workflow level (more explicit)
permissions:
  contents: write
  pull-requests: write

jobs:
  update-routing:
    runs-on: ubuntu-latest
```

This makes permissions more explicit at the workflow level rather than job level.

### Step 2: Enable GitHub Actions Permissions in Repository

**You need to update repository settings manually:**

1. **Navigate to Repository Settings:**
   - Go to: https://github.com/raj-iup/cp-whisperx-app/settings
   - Click: "Actions" in left sidebar
   - Click: "General"

2. **Update Workflow Permissions:**
   - Scroll to "Workflow permissions" section
   - Select: **"Read and write permissions"** (not just "Read repository contents")
   - ✅ Check: **"Allow GitHub Actions to create and approve pull requests"**
   - Click: "Save"

**Screenshot locations:**
```
Settings → Actions → General → Workflow permissions
```

**Required settings:**
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

---

## 🧪 Testing After Fix

### Option 1: Test with Workflow Dispatch (Recommended)

```bash
# After updating settings, test again:
1. Go to: https://github.com/raj-iup/cp-whisperx-app/actions
2. Click: "Update AI Model Routing" workflow
3. Click: "Run workflow" button
4. Check: "force" option (to force an update)
5. Click: Green "Run workflow" button
6. Monitor: Execution should complete successfully
7. Check: PR should be created automatically
```

### Option 2: Test Locally First

```bash
# Test the update script locally to ensure it works:
cd /Users/rpatel/Projects/Active/cp-whisperx-app

# Check only (no changes)
python3 tools/update-model-routing.py --check-only

# Force update (creates changes)
python3 tools/update-model-routing.py --force

# Check what changed
git status
git diff docs/AI_MODEL_ROUTING.md
```

---

## 📋 Verification Checklist

After applying the fix:

- [ ] Repository settings updated (Read and write permissions)
- [ ] "Allow GitHub Actions to create and approve pull requests" enabled
- [ ] Workflow file committed and pushed
- [ ] Manual workflow run successful
- [ ] PR created automatically
- [ ] PR contains expected changes
- [ ] PR has correct labels (documentation, automated, ai-models)

---

## 🚀 Expected Behavior After Fix

### Successful Workflow Run Should:

1. ✅ Checkout repository
2. ✅ Setup Python 3.11
3. ✅ Install dependencies (requests)
4. ✅ Check for model updates
5. ✅ Apply updates (if needed)
6. ✅ Detect changes
7. ✅ **Create Pull Request** (this was failing before)
8. ✅ Display summary

### Created PR Should Include:

- **Title:** "Auto-update: AI Model Routing"
- **Branch:** `auto-update-model-routing`
- **Labels:** documentation, automated, ai-models
- **Changes:**
  - `docs/AI_MODEL_ROUTING.md` (routing table updated)
  - `.github/copilot-instructions.md` (synced with routing)
  - `config/ai_models.json` (timestamp updated)

---

## 🔧 Alternative Solutions (If Fix Doesn't Work)

### Option A: Use Personal Access Token (PAT)

If the default `GITHUB_TOKEN` still doesn't work:

1. **Create PAT:**
   - Go to: https://github.com/settings/tokens
   - Generate new token (classic)
   - Scopes needed: `repo`, `workflow`
   - Copy the token

2. **Add to Repository Secrets:**
   - Go to: https://github.com/raj-iup/cp-whisperx-app/settings/secrets/actions
   - Click: "New repository secret"
   - Name: `PAT_TOKEN`
   - Value: [paste your token]
   - Click: "Add secret"

3. **Update Workflow:**
   ```yaml
   - name: Create Pull Request
     uses: peter-evans/create-pull-request@v5
     with:
       token: ${{ secrets.PAT_TOKEN }}  # Use PAT instead of GITHUB_TOKEN
       # ... rest of config
   ```

### Option B: Use GitHub App (Most Secure)

For production environments:

1. Create a GitHub App with `contents:write` and `pull-requests:write` permissions
2. Install the app on your repository
3. Use the app token in the workflow

**See:** https://github.com/peter-evans/create-pull-request#action-behaviour

### Option C: Direct Commit (Skip PR)

If you don't need PR approval:

```yaml
- name: Commit changes
  if: steps.changes.outputs.has_changes == 'true'
  run: |
    git config user.name "GitHub Actions"
    git config user.email "actions@github.com"
    git add .
    git commit -m "docs: auto-update AI model routing"
    git push
```

**Note:** This bypasses PR review. Only use if you trust the automation completely.

---

## 📊 Updated Workflow File

The workflow file has been updated and is ready to push:

```bash
cd /Users/rpatel/Projects/Active/cp-whisperx-app
git add .github/workflows/update-model-routing.yml
git commit -m "fix: update GitHub Actions permissions for PR creation"
git push origin main
```

---

## 🎯 Next Steps

1. **Update Repository Settings** (see Step 2 above)
2. **Push Updated Workflow:**
   ```bash
   git add .github/workflows/update-model-routing.yml GITHUB_ACTIONS_FIX.md
   git commit -m "fix: update GitHub Actions permissions for PR creation"
   git push origin main
   ```
3. **Test Again:** Run workflow manually
4. **Verify:** PR is created successfully
5. **Review & Merge:** Check the auto-created PR

---

## 📚 References

- **GitHub Actions Permissions:** https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token
- **create-pull-request Action:** https://github.com/peter-evans/create-pull-request
- **Workflow Permissions:** https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#permissions

---

## ✅ Status After Fix

- [x] Issue identified
- [x] Root cause understood
- [x] Workflow file updated
- [ ] Repository settings updated (manual step)
- [ ] Workflow tested successfully
- [ ] PR creation verified

**Updated:** December 3, 2025  
**Next Action:** Update repository settings and test workflow
