# Boomi CI/CD — GitHub Actions

GitHub Actions template for Boomi DevOps. Fork this repo, add secrets, run.

## Setup

### 1. Fork this repo

### 2. Add secrets
Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `BOOMI_USERNAME` | API user email |
| `BOOMI_PASSWORD` | `BOOMI_TOKEN.<token>` |
| `BOOMI_ACCOUNT_ID` | `companyname-XXXXXX` — no trailing spaces |
| `BOOMI_FOLDER_NAME` | Top-level AtomSphere folder to scan |
| `BOOMI_ENV_DEV` | Boomi DEV environment name |
| `BOOMI_ENV_STG` | Boomi Stage environment name (optional) |
| `BOOMI_ENV_PROD` | Boomi Prod environment name (optional) |

### 3. Set up GitHub Environments (optional — for approval gates)
Go to **Settings → Environments** and create `dev`, `stg`, `prod`.
Add required reviewers to `stg` and `prod` for approval gates before deployment.

### 4. Run the Release Generator
Go to **Actions → Boomi Release Generator → Run workflow**.
This discovers all deployable components in your Boomi folder and commits `release/release.json`.

### 5. Run the CICD Pipeline
Go to **Actions → Boomi CICD Pipeline → Run workflow**.
Deploys DEV → (approval) → STG → (approval) → PROD.

## Workflows

| Workflow | Trigger | What it does |
|---|---|---|
| `release-generator` | Push to main or manual | Discovers components, updates `release/release.json` |
| `cicd-pipeline` | Manual only | Lint → DEV → STG → PROD with approval gates |

## Deployable Component Types
`process`, `webservice.external`, `webservice.internal`, `flowservice`, `processroute`, `tpgroup`, `customlibrary`, `certificate`

## Optional: SonarQube
Add `SONARQUBE_URL`, `SONARQUBE_PROJECT_KEY`, `SONARQUBE_TOKEN` secrets to enable analysis.
