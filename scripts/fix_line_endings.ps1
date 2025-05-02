#
# Fix Line Endings Script for ProcessSample Optimization Lab
# Converts Windows-style line endings (CRLF) to Unix-style (LF) in shell scripts
#

# Find all shell scripts in the repository
$shellScripts = Get-ChildItem -Path "." -Filter "*.sh" -Recurse
$entrypointScripts = Get-ChildItem -Path "./load-image" -Filter "entrypoint*" -Recurse

Write-Host "Checking line endings in shell scripts..." -ForegroundColor Cyan
$scriptCount = 0
$fixedCount = 0

# Function to fix line endings in a file
function Fix-LineEndings {
    param (
        [string]$FilePath
    )
    
    $content = Get-Content -Path $FilePath -Raw
    if ($content -match "\r\n") {
        Write-Host "  Converting $FilePath to LF line endings" -ForegroundColor Yellow
        $content = $content -replace "\r\n", "`n"
        [System.IO.File]::WriteAllText($FilePath, $content)
        return $true
    }
    
    return $false
}

# Process all shell scripts
foreach ($script in $shellScripts) {
    $scriptCount++
    if (Fix-LineEndings -FilePath $script.FullName) {
        $fixedCount++
    }
}

# Process entrypoint scripts (which may not have a .sh extension)
foreach ($script in $entrypointScripts) {
    $scriptCount++
    if (Fix-LineEndings -FilePath $script.FullName) {
        $fixedCount++
    }
}

# Report results
Write-Host "`nLine ending conversion complete." -ForegroundColor Green
Write-Host "Checked $scriptCount script files." -ForegroundColor Green
Write-Host "Fixed $fixedCount files with Windows-style line endings." -ForegroundColor Green

if ($fixedCount -gt 0) {
    Write-Host "`nIMPORTANT: The files have been converted to Unix-style line endings (LF)." -ForegroundColor Yellow
    Write-Host "This will prevent the 'No such file or directory' errors in Docker containers." -ForegroundColor Yellow
}

Write-Host "`nDone." -ForegroundColor Green
