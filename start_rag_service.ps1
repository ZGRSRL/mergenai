# RAG API Servisi Başlatma Scripti (PowerShell)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "RAG API Servisi Baslatiliyor..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# 1. Environment dosyasını kontrol et
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] .env dosyasi bulunamadi!" -ForegroundColor Yellow
    Write-Host "env.example dosyasini .env olarak kopyalayin" -ForegroundColor Yellow
}

# 2. Docker Compose ile servisi başlat
Write-Host "`n[1] Docker Compose ile rag_api servisi baslatiliyor..." -ForegroundColor Green

try {
    docker-compose up -d rag_api
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Servis baslatildi" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Servis baslatilamadi!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Docker Compose hatasi: $_" -ForegroundColor Red
    exit 1
}

# 3. Servisin durumunu kontrol et
Write-Host "`n[2] Servis durumu kontrol ediliyor..." -ForegroundColor Green
Start-Sleep -Seconds 3

$status = docker-compose ps rag_api 2>&1
Write-Host $status

# 4. Health check
Write-Host "`n[3] Health check yapiliyor..." -ForegroundColor Green
Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] RAG API calisiyor!" -ForegroundColor Green
        Write-Host "API URL: http://localhost:8001" -ForegroundColor Cyan
        Write-Host "Docs: http://localhost:8001/docs" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[WARN] Health check basarisiz, servis henuz hazir olmayabilir" -ForegroundColor Yellow
    Write-Host "Lutfen loglari kontrol edin: docker-compose logs -f rag_api" -ForegroundColor Yellow
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Firsat icin RAG calistirmak icin:" -ForegroundColor Cyan
Write-Host "  python run_rag_for_opportunity.py" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan

