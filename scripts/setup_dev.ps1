# PowerShell Bootstrap Script for GQT Student Portal
Write-Host ">>> Initializing GQT Student Portal Development Environment..." -ForegroundColor Cyan

# 1. Check Root .env
if (-not (Test-Path ".env")) {
    Write-Host "Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 2. Check Backend .env
if (-not (Test-Path "backend\.env")) {
    Write-Host "Copying backend\.env.example to backend\.env..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
}

# 3. Check Frontend .env
if (-not (Test-Path "frontend\.env")) {
    Write-Host "Copying frontend\.env.example to frontend\.env..." -ForegroundColor Yellow
    Copy-Item "frontend\.env.example" "frontend\.env"
}

Write-Host ">>> Checking Docker status..." -ForegroundColor Cyan
docker compose -f infrastructure/docker-compose.dev.yml up -d postgres redis

Write-Host ">>> Backing services started (PostgreSQL & Redis)." -ForegroundColor Green
Write-Host ">>> Run backend migrations and frontend dev server to proceed." -ForegroundColor Green
