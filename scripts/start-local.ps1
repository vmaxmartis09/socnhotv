# Script khởi chạy toàn bộ hệ thống SocNhoTV cục bộ (Backend Core API + Next.js Studio Dashboard)
param(
    [switch]$BackendOnly,
    [switch]$DashboardOnly
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$VenvUvicorn = Join-Path $RepoRoot ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Không tìm thấy môi trường ảo .venv. Hãy chạy: py -3.12 -m venv .venv và cài đặt thư viện."
    exit 1
}

if ($BackendOnly) {
    Write-Host "[Core API] Khởi động tại http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    & $VenvUvicorn socnhotv.core.api.app:app --port 8000 --reload
    exit 0
}

if ($DashboardOnly) {
    Write-Host "[Dashboard] Khởi động tại http://localhost:3000 ..." -ForegroundColor Green
    Set-Location (Join-Path $RepoRoot "tool\dashboard")
    npm run dev
    exit 0
}

Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host "  KHỞI CHẠY SOCNHOTV STUDIO CỤC BỘ" -ForegroundColor Yellow
Write-Host "  - Core Engine: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  - Studio Web:  http://localhost:3000" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Yellow

# Chạy Backend Core trong 1 process mới
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RepoRoot'; Write-Host '[Core API] Đang chạy tại http://127.0.0.1:8000' -ForegroundColor Cyan; & '$VenvUvicorn' socnhotv.core.api.app:app --port 8000 --reload"

# Chạy Dashboard trong cửa sổ hiện tại
Set-Location (Join-Path $RepoRoot "tool\dashboard")
npm run dev
