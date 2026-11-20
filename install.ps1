param(
    [ValidateSet('auto', 'claude', 'trae')]
    [string]$Target = 'auto',
    [switch]$Force,
    [string]$ExpectedChecksum = ''
)

# weak-current-contract-spec-review installer (Windows PowerShell 5.1+)
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target trae
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target claude -Force

$ErrorActionPreference = 'Stop'
$SkillName = 'weak-current-contract-spec-review'
$Source = $PSScriptRoot

$ChecksumFile = Join-Path $Source 'CHECKSUM.txt'
if ([string]::IsNullOrWhiteSpace($ExpectedChecksum) -and (Test-Path $ChecksumFile)) {
    $ExpectedChecksum = (Get-Content $ChecksumFile -TotalCount 1).Trim()
}

if (-not (Test-Path (Join-Path $Source 'SKILL.md'))) {
    throw "SKILL.md not found in $Source. Please run this script from the repository root."
}

if ($Target -eq 'auto') {
    if (Test-Path (Join-Path $HOME '.claude')) {
        $Target = 'claude'
    }
    elseif (Test-Path (Join-Path $HOME '.trae-cn')) {
        $Target = 'trae'
    }
    else {
        throw "No platform detected. Please specify -Target claude or -Target trae."
    }
}

if ($Target -eq 'claude') {
    $SkillsRoot = Join-Path $HOME '.claude\skills'
}
else {
    $SkillsRoot = Join-Path $HOME '.trae-cn\skills'
}

New-Item -ItemType Directory -Path $SkillsRoot -Force | Out-Null
$Dest = Join-Path $SkillsRoot $SkillName

if (Test-Path $Dest) {
    if ($Force) {
        Remove-Item $Dest -Recurse -Force
        Write-Host "Removed existing: $Dest"
    }
    else {
        $Backup = $Dest + '.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
        Rename-Item -Path $Dest -NewName (Split-Path $Backup -Leaf)
        Write-Host "Backup created: $Backup"
    }
}

New-Item -ItemType Directory -Path $Dest -Force | Out-Null
$Exclude = @('.git', '.screenshots', '__pycache__')
Get-ChildItem -Path $Source -Force |
    Where-Object { $Exclude -notcontains $_.Name } |
    ForEach-Object { Copy-Item -Path $_.FullName -Destination $Dest -Recurse -Force }

$Count = (Get-ChildItem -Path $Dest -Recurse -File -Force).Count
Write-Host "Installed to: $Dest"
Write-Host "Files copied: $Count"

$Python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $Python) {
    $Python = Get-Command python3 -ErrorAction SilentlyContinue
}

if ($null -ne $Python) {
    Push-Location $Dest
    try {
        & $Python.Source verify_skill.py
        $VerifyCode = $LASTEXITCODE
        $Sum = ((& $Python.Source verify_skill.py --checksum) -join ' ').Trim()
        Write-Host "Checksum: $Sum"
        if ([string]::IsNullOrWhiteSpace($ExpectedChecksum)) {
            Write-Host "No CHECKSUM.txt found. Skipped checksum comparison."
        }
        elseif ($Sum -match $ExpectedChecksum) {
            Write-Host "Checksum OK"
        }
        else {
            Write-Host "WARNING: checksum mismatch, the rules may have been modified."
        }
        if ($VerifyCode -ne 0) {
            Write-Host "WARNING: verify_skill.py exited with code $VerifyCode"
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "Python not found. Skipped structure verification."
}

Write-Host "Done. Restart Claude Code / Trae to load the skill."
