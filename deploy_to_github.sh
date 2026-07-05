#!/usr/bin/env bash
#
# deploy_to_github.sh
# -------------------
# Safe publish of the v1-clinical rebuild of the ABG CDSS.
#
# What it does (in order):
#   1. Backs up your current GitHub state with a tag  (v0-legacy)
#   2. Creates a NEW branch  (v1-clinical)  -- main is NOT touched
#   3. Copies the new files in, commits, and pushes the branch
#
# You then open a Pull Request and we review before merging to main.
#
# HOW TO USE:
#   1. Put this script + the new files in the SAME folder as your local clone
#      (or run it from inside your cloned repo).
#   2. chmod +x deploy_to_github.sh
#   3. ./deploy_to_github.sh
#
set -e

REPO_DIR="$(pwd)"
echo "==> Working in: $REPO_DIR"

# ---- 0. sanity: are we in a git repo? --------------------------------------
if [ ! -d .git ]; then
  echo "ERROR: this folder is not a git repo."
  echo "Run:  git clone https://github.com/Fnaloufi/ABG-Clinical-Decision-Support.git"
  echo "then copy the new files + this script inside it and re-run."
  exit 1
fi

# ---- 1. backup current state with a tag ------------------------------------
echo "==> Backing up current main as tag 'v0-legacy'"
git checkout main 2>/dev/null || git checkout master
git pull origin "$(git branch --show-current)" || true
git tag -f v0-legacy
git push -f origin v0-legacy
echo "    Backup tag pushed. Your old code is preserved."

# ---- 2. create the clinical branch -----------------------------------------
echo "==> Creating branch 'v1-clinical'"
git checkout -B v1-clinical

# ---- 3. stage the new structure --------------------------------------------
# (Assumes the new files sit in ./abg_cdss/ next to this script, OR already
#  in place. Adjust SRC if needed.)
SRC="./abg_cdss"
if [ -d "$SRC" ]; then
  echo "==> Copying new files from $SRC"
  cp -r "$SRC"/* .
  rm -rf "$SRC"
fi

git add abg_engine.py validation.py constants.py cli.py \
        tests/test_engine.py README.md CHANGELOG.md requirements.txt LICENSE 2>/dev/null || git add .

# ---- 4. commit + push ------------------------------------------------------
echo "==> Committing"
git commit -m "v1.0.0: clinical safety rebuild

- Anion gap (+albumin correction), delta ratio, HAGMA/NAGMA
- Full compensation for all four primary disorders (acute/chronic resp)
- IBW + lung-protective TV check, RSBI weaning index
- Physiological input validation + Henderson-Hasselbalch check
- Modular architecture (engine/validation/constants/cli)
- 31 clinical test cases, all passing
- Bilingual README with clinical references"

echo "==> Pushing branch 'v1-clinical'"
git push -u origin v1-clinical

echo ""
echo "============================================================"
echo "  DONE."
echo "  1. Old code preserved at tag: v0-legacy"
echo "  2. New code on branch:        v1-clinical"
echo "  3. Open a Pull Request on GitHub, then we review before"
echo "     merging into main."
echo "============================================================"
