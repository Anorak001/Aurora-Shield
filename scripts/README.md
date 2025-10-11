# Scripts Directory

This directory is reserved for automation scripts for Aurora Shield project management.

## Note

The issue creation system has been moved to the root directory for easier access:

- **`../issues.yaml`** - All 22 issues definitions in YAML format
- **`../create-issues-from-yaml.ps1`** - PowerShell script to create issues using GitHub CLI
- **`../HOW_TO_CREATE_ISSUES.md`** - Complete guide for creating issues

## Quick Start

After pushing to GitHub:

```powershell
# 1. Install GitHub CLI (if needed)
winget install --id GitHub.cli

# 2. Authenticate
gh auth login

# 3. Run the script from repository root
cd ..
.\create-issues-from-yaml.ps1
```

This will automatically create:
- 30+ labels for organization
- 7 milestones for version tracking
- 22 detailed, modular issues

## Future Scripts

This directory will contain:
- Automated testing scripts
- Deployment automation
- Performance benchmarking tools
- Data analysis scripts

For now, see the root directory for issue creation tools.
