# PowerShell script to setup Windows development environment for Attendance System
# Run this script as Administrator

Write-Host "Setting up Windows development environment..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges. Please run as Administrator." -ForegroundColor Red
    exit 1
}

# Install Chocolatey if not present
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Install required software
Write-Host "Installing required software..." -ForegroundColor Yellow

# Python 3.10+
choco install python311 -y

# Git
choco install git -y

# Inno Setup 6
choco install innosetup -y

# Visual Studio Build Tools (for some Python packages)
choco install visualstudio2022buildtools -y

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "Software installation completed!" -ForegroundColor Green

# Create .env file from template
if (Test-Path "env.example") {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item "env.example" ".env"
    Write-Host "Please edit .env file with your specific settings" -ForegroundColor Cyan
}

Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your settings" -ForegroundColor White
Write-Host "2. Run: pip install -r requirements.txt" -ForegroundColor White
Write-Host "3. Run: python deploy/build_all.py --create-env" -ForegroundColor White

