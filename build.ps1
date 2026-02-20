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
    Write-Host "PyInstaller Build successful!" -ForegroundColor Green
    
    # Check for Inno Setup compiler
    $iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $iscc)) {
        # Try to find ISCC in PATH or alternative location if needed
        $iscc = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    }

    if ($iscc -and (Test-Path $iscc)) {
        Write-Host "Building Installer with Inno Setup..." -ForegroundColor Cyan
        $env:VERSION = $git_tag
        & $iscc "Setup.iss" /Q
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installer Build successful!" -ForegroundColor Green
        } else {
            Write-Host "Installer Build failed!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Inno Setup compiler (ISCC.exe) not found. Skipping installer build." -ForegroundColor Yellow
        Write-Host "Please install Inno Setup 6 to build the installer."
    }
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
