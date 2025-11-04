# RAG API Bağlantı Sorunu - Düzeltme

## Sorun
Streamlit uygulaması `rag_api:8000` adresine bağlanmaya çalışıyordu, ancak bu Docker içi adres. Host makineden `localhost:8001` kullanılmalı.

## Çözüm
`streamlit_app.py` dosyasında RAG_API_URL otomatik olarak düzeltiliyor:

```python
# Docker içi adres (rag_api:8000) tespit edilip localhost:8001'e çevriliyor
env_url = os.getenv("RAG_API_URL", "http://localhost:8001")
if "rag_api:8000" in env_url or ("rag_api" in env_url and "localhost" not in env_url):
    RAG_API_URL = "http://localhost:8001"
else:
    RAG_API_URL = env_url
```

## RAG API Servisini Başlatma

### Yöntem 1: Docker Compose
```bash
cd d:\ZgrSam
docker-compose up -d rag_api
```

### Yöntem 2: Manuel (FastAPI)
```bash
cd d:\ZgrSam\api
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Test
```bash
# Health check
curl http://localhost:8001/api/health

# API docs
# Tarayıcıda: http://localhost:8001/docs
```

## Environment Variable
`.env` dosyasında:
```bash
RAG_API_URL=http://localhost:8001
```

Veya Docker içinden çalışıyorsanız:
```bash
RAG_API_URL=http://rag_api:8000
```

Streamlit host makineden çalıştığı için otomatik olarak `localhost:8001` kullanılacak.

