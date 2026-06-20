# Publishing to GitHub

The repo is committed locally; these are the exact steps to put it on your GitHub. Pick ONE route.
Replace `ali-altaher` with your GitHub username and `projectsf` with whatever repo name you want.

## Route A — GitHub CLI (easiest, if you install `gh`)
1. Install GitHub CLI: https://cli.github.com/  (or `winget install GitHub.cli`)
2. In **PowerShell**, from the repo folder:
```powershell
cd $env:USERPROFILE\projectsf
gh auth login            # one-time: pick GitHub.com -> HTTPS -> login in browser
gh repo create projectsf --public --source . --remote origin --push
```
That creates the repo and pushes in one go.

## Route B — website + git (no extra tools)
1. On github.com click **New repository** → name it `projectsf` → **Public** → **Create** (don't add a README).
2. In **PowerShell**, from the repo folder:
```powershell
cd $env:USERPROFILE\projectsf
git branch -M main
git remote add origin https://github.com/ali-altaher/projectsf.git
git push -u origin main
```
(If it asks for a password, use a Personal Access Token, not your account password:
GitHub → Settings → Developer settings → Personal access tokens → Fine-grained → repo access.)

## After it's up
- **Turn on the tests badge:** the CI workflow at `.github/workflows/tests.yml` runs automatically on
  push. Edit the badge line at the top of `README.md` to your repo path:
  `![tests](https://github.com/<you>/projectsf/actions/workflows/tests.yml/badge.svg)`
- **Check Actions tab** — you should see the `tests` workflow go green (58 tests across 3 projects).
- **Update your CV link** to point at the repo.

## What's already set up for you
- `.github/workflows/tests.yml` — GitHub Actions running pytest on all three projects on every push.
- `.gitignore` — excludes caches and venvs; keeps the committed sample outputs.
- `README.md`, `GUIDE.pdf`, per-project READMEs + THESIS memos, `INVESTMENT_THESIS.md`.

> Tip: a clean public repo with the README screenshots and a green tests badge is worth more to a
> reviewer than any extra feature — this is the step that makes the work visible.
