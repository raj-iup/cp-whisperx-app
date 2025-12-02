#!/usr/bin/env bash
set -euo pipefail

# Minimal git commit & push helper script:
# - Runs basic checks (shellcheck & pytest) if available
# - Adds all changes, commits, pushes to a remote branch
# - Optional: create a tag, or use no-push mode for local commit only

# Usage:
#   ./scripts/git-commit-push.sh -m "Your message" [-b branch] [--no-push] [--force] [--tag v1.2.3] [--skip-checks]

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${WORKDIR}"

# Defaults:
GIT_REMOTE="${GIT_REMOTE:-origin}"
BRANCH="${BRANCH:-}"
COMMIT_MSG=""
NO_PUSH=false
FORCE_PUSH=false
TAG=""
SKIP_CHECKS=false

usage() {
  cat <<EOF
Usage: $(basename "$0") -m "commit message" [options]
Options:
  -m|--message      Commit message (required)
  -b|--branch       Branch to push to (default: current branch)
  --no-push         Do not push to remote (local commit only)
  -f|--force        Force push to remote
  -t|--tag          Create & push tag after push (e.g., v1.2.3)
  --skip-checks     Skip lint/test checks
  -h|--help         Show help
EOF
  exit 1
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--message)
      COMMIT_MSG="$2"; shift 2;;
    -b|--branch)
      BRANCH="$2"; shift 2;;
    -f|--force)
      FORCE_PUSH=true; shift;;
    --no-push)
      NO_PUSH=true; shift;;
    -t|--tag)
      TAG="$2"; shift 2;;
    --skip-checks)
      SKIP_CHECKS=true; shift;;
    -h|--help)
      usage;;
    *)
      echo "Unknown option: $1"
      usage;;
  esac
done

if [[ -z "$COMMIT_MSG" ]]; then
  echo "Commit message is required."
  usage
fi

# Determine current branch if not provided
if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
fi

echo "[info] Repo root: ${WORKDIR}"
echo "[info] Target branch: ${BRANCH}"
echo "[info] Remote: ${GIT_REMOTE}"

# Basic checks: lint & tests
if [[ "${SKIP_CHECKS}" != "true" ]]; then
  # Shellcheck if available
  if command -v shellcheck >/dev/null 2>&1; then
    echo "[info] Running shellcheck on scripts/*.sh"
    shellcheck scripts/*.sh || true
  else
    echo "[info] shellcheck not found; skipping shell lint"
  fi

  # Python tests if pytest is installed
  if command -v pytest >/dev/null 2>&1; then
    echo "[info] Running pytest -q tests"
    pytest -q tests || (echo "[error] tests failed; aborting commit" && exit 1)
  else
    echo "[info] pytest not found; skipping Python tests"
  fi
else
  echo "[info] Skipping checks per --skip-checks"
fi

# Stage changes
git add -A

# Only commit if there are staged changes
if git diff --staged --quiet; then
  echo "[info] No staged changes to commit (no files changed)."
else
  git commit -m "${COMMIT_MSG}"
fi

# Push to remote unless NO_PUSH flagged
if [[ "${NO_PUSH}" = true ]]; then
  echo "[info] NO_PUSH set; not pushing changes to remote."
  exit 0
fi

# Ensure remote branch exists for push; create if needed
if ! git ls-remote --exit-code "${GIT_REMOTE}" "refs/heads/${BRANCH}" >/dev/null 2>&1; then
  echo "[info] Remote branch ${BRANCH} does not exist; pushing new branch to ${GIT_REMOTE}"
fi

if [[ "${FORCE_PUSH}" = true ]]; then
  git push --force "${GIT_REMOTE}" "${BRANCH}"
else
  git push "${GIT_REMOTE}" "${BRANCH}"
fi

# Create & push tag if requested
if [[ -n "${TAG}" ]]; then
  git tag -a "${TAG}" -m "${COMMIT_MSG}"
  git push "${GIT_REMOTE}" "${TAG}"
  echo "[info] Pushed tag ${TAG}"
fi

echo "[info] Push complete to ${GIT_REMOTE}/${BRANCH}"
if command -v gh >/dev/null 2>&1; then
  echo "[info] GitHub CLI detected; to create PR run:"
  echo "  gh pr create --fill --base main --head ${BRANCH}"
fi
