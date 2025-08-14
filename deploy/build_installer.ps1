Param(
  [string]$VenvPath = "C:\att-venv",
  [string]$AppName = "AttendanceAdmin"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-Step($Desc, $ScriptBlock) {
  Write-Host "[+] $Desc" -ForegroundColor Cyan
  & $ScriptBlock
}

Invoke-Step "Set execution policy (process)" { Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force }

# 1) Create or reuse venv
if (!(Test-Path $VenvPath)) {
  Invoke-Step "Create virtualenv at $VenvPath" { python -m venv $VenvPath }
} else {
  Write-Host "[i] Reusing venv at $VenvPath" -ForegroundColor Yellow
}

$Py = Join-Path $VenvPath "Scripts/python.exe"
if (!(Test-Path $Py)) { throw "Python not found at $Py" }

# 2) Upgrade tooling and install deps
Invoke-Step "Upgrade pip/setuptools/wheel" { & $Py -m pip install --upgrade --no-cache-dir pip "setuptools>=75" wheel }
Invoke-Step "Install project requirements" { & $Py -m pip install --no-cache-dir -r requirements.txt }
Invoke-Step "Install PyInstaller" { & $Py -m pip install --no-cache-dir "pyinstaller>=6.6" }

# 3) Build exe
$IconPath = Join-Path (Resolve-Path ".").Path "assets\icons\rabat-logo.jpg"
$HasIcon = Test-Path $IconPath

$addData = @(
  "assets\themes;assets/themes",
  "assets\icons;assets/icons",
  "translations;translations",
  "templates;templates"
)

$pyArgs = @(
  "-m", "PyInstaller",
  "--noconfirm", "--clean",
  "--name", $AppName,
  "--windowed"
)
# For PyInstaller icon, prefer .ico. If using a non-ico image, skip icon to avoid errors.
if ($HasIcon -and ($IconPath.ToLower().EndsWith('.ico'))) { $pyArgs += @("--icon", $IconPath) }
foreach ($pair in $addData) { $pyArgs += @("--add-data", $pair) }
$pyArgs += @("app\main.py")

Invoke-Step "Build exe with PyInstaller" { & $Py $pyArgs }

$DistDir = Join-Path (Resolve-Path ".").Path "dist\$AppName"
if (!(Test-Path $DistDir)) { throw "Build failed: $DistDir not found" }
Write-Host "[✓] EXE built at: $DistDir\$AppName.exe" -ForegroundColor Green

# 4) Build installer with Inno Setup
$ISCC = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
if (!(Test-Path $ISCC)) { $ISCC = Join-Path ${env:ProgramFiles} "Inno Setup 6\ISCC.exe" }
if (!(Test-Path $ISCC)) { throw "ISCC.exe not found. Install Inno Setup 6 first." }

${IssPath} = (Resolve-Path ".\deploy\installer.iss").Path

# Determine app version to pass to Inno Setup (robust parsing)
$EnvVersion = $env:APP_VERSION
if (-not $EnvVersion -or $EnvVersion -eq '') {
  try {
    $verContent = Get-Content -Raw -Encoding UTF8 ".\app\version.py"
    $m = [regex]::Match($verContent, 'APP_VERSION\s*=\s*"(.*?)"')
    if ($m.Success) { $EnvVersion = $m.Groups[1].Value }
  } catch {}
}
if (-not $EnvVersion -or $EnvVersion -eq '') { $EnvVersion = "1.0.0" }

Invoke-Step "Compile installer (Inno Setup)" { & $ISCC "/DMyAppVersion=$EnvVersion" $IssPath }

$OutInstaller = Join-Path (Resolve-Path ".").Path "deploy\output\AttendanceAdminInstaller.exe"
if (Test-Path $OutInstaller) {
  Write-Host "[✓] Installer generated: $OutInstaller" -ForegroundColor Green
}
if (!(Test-Path $OutInstaller)) {
  Write-Host "[!] Installer output not found in deploy\\output. Check Inno logs." -ForegroundColor Yellow
}

Write-Host "All done." -ForegroundColor Green


