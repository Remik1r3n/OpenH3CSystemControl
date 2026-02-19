Write-Host "Cleaning up previous builds..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# --- Version generation ---
$git_tag = git describe --tags --always --dirty 2>$null
if (-not $?) { 
    Write-Host "Git describe failed, falling back." -ForegroundColor Yellow
    $git_tag = "x.x.x-unknownbuild"
} else {
    Write-Host "Building version: $git_tag" -ForegroundColor Cyan
}

# Write version to _version.py
Set-Content -Path "_version.py" -Value "__version__ = `"$git_tag`""

Write-Host "Building OpenH3CSystemControl..."
pyinstaller OpenH3CSystemControl.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}
