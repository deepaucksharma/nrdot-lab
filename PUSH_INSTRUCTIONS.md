# Push Instructions

Follow these steps to push the ProcessSample Lab code to a repository.

## Preparation Steps

1. **Ensure Template Files Exist**
   - `config/newrelic-infra-template.yml`
   - `config/otel-template.yaml`

2. **Fix Line Endings**
   ```
   # Windows
   .\scripts\fix_line_endings.ps1
   
   # Linux/macOS
   ./scripts/fix_line_endings.sh
   ```

3. **Generate Configurations**
   ```
   # Windows
   .\process-lab.ps1 generate-configs
   
   # Linux/macOS
   make generate-configs
   ```

4. **Verify Setup**
   ```
   # Windows
   .\verify_setup.ps1
   
   # Linux/macOS
   ./scripts/verify_setup.sh
   ```

## Git Commands

```bash
# Stage all changes
git add .

# Commit
git commit -m "ProcessSample Lab with cross-platform support"

# Push to main branch
git push origin main

# OR create and push to a new branch
git checkout -b feature-branch
git add .
git commit -m "ProcessSample Lab with cross-platform support"
git push origin feature-branch
```

## Key Files

- `README.md` - Main documentation
- `docker-compose.yml` - Unified configuration
- `process-lab.ps1` - Windows command interface
- `Makefile` - Linux/macOS command interface
- `.gitattributes` - Line ending configuration
