# Running on Windows

This guide provides Windows-specific instructions for running the New Relic ProcessSample Optimization Lab.

## Prerequisites

- **Windows 10/11** with Docker Desktop installed
- **Docker Desktop** set to use WSL2 backend (recommended)
- **Windows Terminal** (optional but recommended)
- **Git Bash**, WSL, or PowerShell
- **New Relic account** with license key, API key, and account ID

## Setup Process

### 1. Clone the Repository

Using Git Bash or PowerShell:
```bash
git clone https://github.com/your-org/newrelic-process-lab.git
cd newrelic-process-lab
```

### 2. Configure Environment Variables

Copy the example .env file:
```bash
cp .env.example .env
```

Edit the .env file with a text editor (e.g., Notepad, VS Code) and add your New Relic credentials:
```
NEW_RELIC_LICENSE_KEY=your_license_key
NEW_RELIC_API_KEY=your_api_key
NR_ACCOUNT_ID=your_account_id
```

### 3. Running Lab Scenarios on Windows

#### Standard Lab (Default)

Using PowerShell:
```powershell
docker-compose up -d
```

Or using Command Prompt:
```cmd
docker-compose up -d
```

#### Running with Overrides

Due to path separator differences on Windows, you'll need to use the `-f` flag instead of `COMPOSE_FILE` environment variable:

```powershell
# Minimal Mounts mode
docker-compose -f docker-compose.yml -f overrides/min-mounts.yml up -d

# Seccomp Disabled mode
docker-compose -f docker-compose.yml -f overrides/seccomp-disabled.yml up -d

# Docker Stats mode
docker-compose -f docker-compose.yml -f overrides/docker-stats.yml up -d
```

### 4. Viewing Logs

```powershell
docker-compose logs
```

To follow logs:
```powershell
docker-compose logs -f
```

### 5. Validation on Windows

For Windows, use the dedicated Windows validation script:

```powershell
# Using PowerShell
.\scripts\validate_ingest_windows.ps1
```

### 6. Windows-Specific Troubleshooting

#### Docker Socket Issues

If you're having issues with Docker socket access:

1. Ensure Docker Desktop is running with Linux containers mode (not Windows containers)
2. Check Docker Desktop settings to allow volume mounting for the drive

#### Path Formatting Issues

Windows uses backslashes (`\`) while Docker expects forward slashes (`/`). For configuration files, ensure paths use the correct format:

```yaml
# In YAML configs, always use forward slashes
volumes:
  - /path/to/source:/container/path
```