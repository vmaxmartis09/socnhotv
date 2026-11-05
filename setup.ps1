# ==============================================================================
# SCRIPT TỰ ĐỘNG CÀI ĐẶT & CHẠY DỰ ÁN CHO MÁY MỚI (SocNhoTV Studio)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   BẮT ĐẦU CÀI ĐẶT TỰ ĐỘNG SOCNHOTV STUDIO TRÊN MÁY MỚI    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoRoot = $PSScriptRoot
Set-Location $RepoRoot

# 1. Kiểm tra Python
Write-Host "`n[1/4] Kiểm tra môi trường Python..." -ForegroundColor Yellow
$PythonCmd = ""
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py -3.12"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} else {
    Write-Error "Không tìm thấy Python trên máy. Vui lòng cài đặt Python >= 3.11 từ python.org"
    exit 1
}

# 2. Tạo .venv và cài đặt Backend dependencies
Write-Host "`n[2/4] Thiết lập môi trường ảo Python và cài đặt Backend..." -ForegroundColor Yellow
$VenvDir = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Đang tạo virtualenv tại .venv ..."
    Invoke-Expression "$PythonCmd -m venv .venv"
}

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$VenvPip = Join-Path $RepoRoot ".venv\Scripts\pip.exe"

& $VenvPip install --upgrade pip
& $VenvPip install -e .
& $VenvPip install uvicorn fastapi pydantic python-multipart jinja2 requests

# 3. Cài đặt Node dependencies cho Web Dashboard
Write-Host "`n[3/4] Cài đặt Node.js dependencies cho Dashboard..." -ForegroundColor Yellow
$DashboardDir = Join-Path $RepoRoot "tool\dashboard"
Set-Location $DashboardDir
npm install
Set-Location $RepoRoot

# 4. Hoàn tất và khởi chạy
Write-Host "`n[4/4] Cài đặt hoàn tất! Đang khởi động hệ thống..." -ForegroundColor Green
& (Join-Path $RepoRoot "scripts\start-local.ps1")
