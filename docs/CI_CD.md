**Overview**
This repository uses GitHub Actions for CI and CD. The CI workflow runs tests on push and pull requests. The CD workflow builds and pushes a Docker image to GitHub Container Registry (GHCR) on pushes to `main` and `finale`.

**Files added/used**
- `.github/workflows/ci.yml` — runs `pytest` across supported Python versions on `push` and `pull_request` to `main`, `finale`, `develop`.
- `.github/workflows/cd.yml` — builds and pushes a Docker image to `ghcr.io` on `push` to `main`/`finale`.

**Repository secrets**
- `GITHUB_TOKEN` (automatically provided by GitHub Actions) — used to authenticate with GHCR for pushes when Actions permissions allow it.
- `DOCKER_REGISTRY_PAT` (optional) — a personal access token with `write:packages` if `GITHUB_TOKEN` cannot push to GHCR due to organization policies.
- `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` (optional) — if you prefer pushing to Docker Hub instead of GHCR.

**Branch protection (recommended)**
- Protect `main` and `finale` with required status checks: enable the `CI` workflow job and require PR reviews before merge.

**How to set repository secrets**
1. Go to repository Settings → Secrets and variables → Actions.
2. Add `DOCKER_REGISTRY_PAT` (if using a PAT) and `DOCKERHUB_TOKEN` (if using Docker Hub).

**Local testing**
- Run tests locally with:
```
python -m pip install -r requirements.txt
pytest -q
```

**Next steps / Recommendations**
- If you want automatic deployments from `finale` or `main`, I can add environment-specific deploy steps (e.g., to Azure/AWS/GCP or a self-hosted server).
- If GHCR push fails due to permissions, we can switch to Docker Hub or configure a `DOCKER_REGISTRY_PAT`.

If you'd like, I can also add richer notifications (Slack, Teams) using dedicated actions, but those are currently removed per request.
