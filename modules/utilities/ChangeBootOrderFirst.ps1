<#
.SYNOPSIS
    Finds a specified UEFI boot entry and moves it to the first position in BootOrder.

.DESCRIPTION
        This script parses the output of `bcdedit /enum firmware` to find a boot entry
        with a matching description, then uses:
            bcdedit /set {fwbootmgr} displayorder ... /addfirst
        to move it to the top.

.EXIT CODES
    0 - Success
    1 - Admin rights required
    2 - Target not found
    3 - Failed to set boot order
    4 - Unknown error
#>

param (
    [string]$TargetDescription = "MegaOS"
)

# Step 1: Check for admin rights
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "Administrator privileges are required."
    exit 1
}

Write-Host "Searching for '$TargetDescription'..." -ForegroundColor Cyan

# Step 2: Execute bcdedit and parse output
try {
    # Get output as an array of lines
    $bcdOutputLines = bcdedit /enum firmware /v
} catch {
    Write-Error "Failed to execute 'bcdedit'."
    exit 4
}

# Join the array into a single string using NewLines so we can split by blocks
$bcdString = $bcdOutputLines -join "`r`n"

# Split by double newlines to isolate each firmware entry block
$entries = $bcdString -split "(\r?\n){2,}"

$targetGuid = $null

foreach ($entry in $entries) {
    # Check if this block contains the target description
    if ($entry -match "description\s+$([Regex]::Escape($TargetDescription))") {
        
        # Look for the identifier within this specific block
        if ($entry -match "identifier\s+({[a-fA-F0-9\-]+})") {
            $targetGuid = $Matches[1]
            break
        }
    }
}

# Step 3: Check if we found the target entry
if ([string]::IsNullOrEmpty($targetGuid)) {
    # Debug info: verify we are actually parsing content
    Write-Warning "Parsed $($entries.Count) entries, but '$TargetDescription' was not found."
    Write-Warning "Ensure the description matches (case-insensitive)."
    exit 2
}

Write-Host "Found! GUID: $targetGuid" -ForegroundColor Green

# Step 4: Move the target entry to the first position in the firmware boot order
Write-Host "Changing it to first..." -ForegroundColor Cyan

# {fwbootmgr} is UEFI BootOrder
$proc = Start-Process -FilePath "bcdedit.exe" -ArgumentList "/set `"{fwbootmgr}`" displayorder `"$targetGuid`" /addfirst" -PassThru -Wait -NoNewWindow

if ($proc.ExitCode -eq 0) {
    Write-Host "Success! '$TargetDescription' is now first boot entry." -ForegroundColor Green
    [Console]::WriteLine("")
    exit 0
} else {
    Write-Error "Failed. ExitCode: $($proc.ExitCode)"
    exit 3
}