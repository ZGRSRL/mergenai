# RAG Servisi Başlatma Kılavuzu

Bu fırsat için RAG servisini çalıştırmak için önce servisi başlatmanız gerekiyor.

## Adım 1: RAG API Servisini Başlatın

```bash
# Docker Compose ile RAG API servisini başlat
docker-compose up -d rag_api

# Servisin durumunu kontrol et
docker-compose ps rag_api

# Logları izle
docker-compose logs -f rag_api
```

## Adım 2: Servisi Test Edin

```bash
# Sağlık kontrolü
curl http://localhost:8001/api/health

# API dokümantasyonu (tarayıcıda açın)
# http://localhost:8001/docs
```

## Adım 3: Fırsat İçin RAG Çalıştırın

```bash
python run_rag_for_opportunity.py
```

## Sorun Giderme

### Servis başlamıyorsa:

1. **Environment değişkenlerini kontrol edin:**
   - `.env` dosyasında gerekli değişkenler var mı?
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` ayarlı mı?

2. **Database bağlantısını kontrol edin:**
   ```bash
   docker-compose up -d db
   docker-compose ps db
   ```

3. **Port çakışması var mı kontrol edin:**
   - Port 8001 kullanımda mı? `netstat -ano | findstr :8001`

### Servis çalışıyor ama bağlanamıyorsanız:

- Docker içinden: `http://rag_api:8000`
- Host makineden: `http://localhost:8001`

```bash
# Environment değişkenini kontrol et
echo $RAG_API_URL

# Veya .env dosyasında:
# RAG_API_URL=http://localhost:8001
```

