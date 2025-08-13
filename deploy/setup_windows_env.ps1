Param(
  [Parameter(Mandatory=$false)][string]$DatabaseUrl = "",
  [Parameter(Mandatory=$false)][string]$ThemeDir = "assets/themes"
)

Write-Host "[1/3] Creating virtualenv and installing requirements..."
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

if ($DatabaseUrl -ne "") {
  $env:DATABASE_URL = $DatabaseUrl
}
$env:THEME_DIR = $ThemeDir

Write-Host "[2/3] Checking PostgreSQL client (optional)..."
python - << 'PY'
try:
    import psycopg2
    print('psycopg2 OK')
except Exception as e:
    print('psycopg2 not available (install if using PostgreSQL):', e)
PY

Write-Host "[3/3] Launching desktop app..."
python -m app.main

