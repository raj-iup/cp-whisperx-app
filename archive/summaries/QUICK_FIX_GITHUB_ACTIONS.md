# Quick Fix - GitHub Actions Permission Error

**TL;DR:** The workflow needs permission to create PRs. Update repository settings.

---

## ⚡ Quick Fix (2 Minutes)

### Step 1: Go to Settings
```
https://github.com/raj-iup/cp-whisperx-app/settings/actions
```

### Step 2: Enable Permissions

Navigate: **Settings → Actions → General → Workflow permissions**

Enable **BOTH** of these:
- ✅ **Read and write permissions** (select this radio button)
- ✅ **Allow GitHub Actions to create and approve pull requests** (check this box)

Click: **Save**

### Step 3: Test Again

```
https://github.com/raj-iup/cp-whisperx-app/actions/workflows/update-model-routing.yml
```

Click: **Run workflow** → Check **force** → **Run workflow** button

---

## 📊 What This Looks Like

**BEFORE (Current - ❌ Won't work):**
```
○ Read repository contents and packages permission
```

**AFTER (Required - ✅ Will work):**
```
● Read and write permissions
☑ Allow GitHub Actions to create and approve pull requests
```

---

## ✅ Success Indicators

After fixing and running workflow:
- ✅ Workflow completes without errors
- ✅ PR created: https://github.com/raj-iup/cp-whisperx-app/pulls
- ✅ PR title: "Auto-update: AI Model Routing"

---

## 🆘 If Still Fails

See full guide: **GITHUB_ACTIONS_FIX.md**

Alternative solutions:
- Option A: Personal Access Token (PAT)
- Option B: GitHub App
- Option C: Direct commit (no PR)

---

**Fixed:** December 3, 2025  
**Next:** Update settings → Test workflow → Merge PR
