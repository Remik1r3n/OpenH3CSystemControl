<#
.SYNOPSIS
    查找指定的 UEFI 启动项并将其移动到 BootOrder 的第一位。

.DESCRIPTION
    此脚本解析 bcdedit /enum firmware 的输出，查找匹配描述的启动项，
    并使用 bcdedit /set {fwbootmgr} displayorder ... /addfirst 将其置顶。

.EXIT CODES
    0 - 成功 (Success)
    1 - 需要管理员权限 (Admin Rights Required)
    2 - 未找到指定名称的启动项 (Target Not Found)
    3 - 设置启动顺序失败 (Failed to Set Order)
    4 - 未知错误 (Unknown Error)
#>

param (
    [string]$TargetDescription = "MegaOS"
)

# --- 1. 检查管理员权限 ---
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "Admin needed"
    exit 1
}

Write-Host "Searching for '$TargetDescription'..." -ForegroundColor Cyan

# --- 2. 获取并解析固件数据 ---
try {
    # Get output as an array of lines
    $bcdOutputLines = bcdedit /enum firmware /v
} catch {
    Write-Error "Can't execute bcdedit!"
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

# --- 3. 验证是否找到 ---
if ([string]::IsNullOrEmpty($targetGuid)) {
    # Debug info: verify we are actually parsing content
    Write-Warning "Parsed $($entries.Count) entries, but '$TargetDescription' was not found."
    Write-Warning "Ensure the description matches exactly (case-insensitive)."
    exit 2
}

Write-Host "Found! GUID: $targetGuid" -ForegroundColor Green

# --- 4. 修改启动顺序 ---
Write-Host "Changing it to first..." -ForegroundColor Cyan

# {fwbootmgr} 代表 UEFI BootOrder
# /addfirst 确保它被移到列表的最顶端
$proc = Start-Process -FilePath "bcdedit.exe" -ArgumentList "/set `"{fwbootmgr}`" displayorder `"$targetGuid`" /addfirst" -PassThru -Wait -NoNewWindow

if ($proc.ExitCode -eq 0) {
    Write-Host "Success! '$TargetDescription' is now first boot entry." -ForegroundColor Green
    [Console]::WriteLine("")
    exit 0
} else {
    Write-Error "ERROR! ExitCode: $($proc.ExitCode)"
    exit 3
}