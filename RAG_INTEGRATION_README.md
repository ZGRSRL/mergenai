# SAMAI RAG Servisi Entegrasyonu

Bu dokümantasyon, SAMAI projesinin RAG (Retrieval-Augmented Generation) servisini Docker üzerinden nasıl kullanacağınızı açıklar.

## 📋 İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Mimari](#mimari)
3. [Kurulum](#kurulum)
4. [Kullanım](#kullanım)
5. [API Referansı](#api-referansı)
6. [Sorun Giderme](#sorun-giderme)

## 🎯 Genel Bakış

RAG servisi, SAMAI projesinin geçmiş fırsat ve tekliflerden öğrenerek yeni teklifler oluşturmasını sağlar. Bu servis:

- ✅ Geçmiş fırsatlardan semantic arama yapar
- ✅ LLM ile bağlamsal teklif taslakları oluşturur
- ✅ Kaynak referansları sağlar
- ✅ Docker container olarak çalışır

## 🏗️ Mimari

```
┌─────────────────┐
│  SAMAI App      │
│  (Streamlit)    │
└────────┬────────┘
         │ HTTP
         │
┌────────▼────────┐
│  samai_         │
│  integrator.py  │
└────────┬────────┘
         │
┌────────▼────────┐
│  RAG API        │
│  (rag_api:8000) │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│  DB   │ │ Redis │
│(Postgres)│      │
└────────┘ └──────┘
```

## 🚀 Kurulum

### 1. Docker Compose ile Servisleri Başlatma

```bash
# Tüm servisleri başlat (db, redis, api, rag_api, worker, web)
docker-compose up -d

# Sadece RAG servisini başlat
docker-compose up -d rag_api

# Logları izle
docker-compose logs -f rag_api
```

### 2. Environment Variables

`.env` dosyanızda şu değişkenlerin olması gerekir:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ZGR_AI
POSTGRES_PORT=5432
DB_HOST=db

# RAG API URL (Docker içinden)
RAG_API_URL=http://rag_api:8000

# RAG API URL (Host makineden)
# RAG_API_URL=http://localhost:8001

# Timeout (saniye)
RAG_API_TIMEOUT=300
```

### 3. Servisleri Kontrol Etme

```bash
# RAG API sağlık kontrolü
curl http://localhost:8001/api/health

# RAG API dokümantasyonu
# Tarayıcıda açın: http://localhost:8001/docs
```

## 📖 Kullanım

### Python Kodunda Kullanım

```python
from samai_integrator import call_rag_proposal_service

# Teklif oluştur
result = call_rag_proposal_service(
    user_query="Bu fırsat için ana teknik gereksinimler nelerdir?",
    notice_id="086008536ec84226ad9de043dc738d06",
    agency="Department of Defense"
)

if result.get("status") == "success":
    print("Teklif Taslağı:")
    print(result['result']['proposal_draft'])
    
    print("\nKaynaklar:")
    for source in result.get('sources', []):
        print(f"- Belge {source['document_id']}: {source['similarity']:.2f}")
else:
    print(f"Hata: {result.get('message')}")
```

### Streamlit Uygulamasında Kullanım

Streamlit uygulamasında `SOW Analizi` menüsünde `RAG Servisi ile Teklif Oluştur` bölümünü kullanabilirsiniz.

1. Streamlit uygulamasını başlatın:
```bash
streamlit run streamlit_app_optimized.py
```

2. Tarayıcıda `http://localhost:8501` adresine gidin

3. Menüden `SOW Analizi` seçin

4. `RAG Servisi ile Teklif Oluştur` bölümünde:
   - Opportunity ID girin
   - Agency bilgisini girin (opsiyonel)
   - Soru/talimatınızı yazın
   - "RAG ile Teklif Oluştur" butonuna tıklayın

### REST API Kullanımı

```bash
# Teklif oluşturma isteği
curl -X POST "http://localhost:8001/api/rag/generate_proposal" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bu fırsat için ana teknik gereksinimler nelerdir?",
    "notice_id": "086008536ec84226ad9de043dc738d06",
    "target_agency": "Department of Defense",
    "hybrid_alpha": 0.6,
    "topk": 15
  }'
```

## 📚 API Referansı

### POST `/api/rag/generate_proposal`

Teklif taslağı oluşturur.

**Request Body:**
```json
{
  "query": "string (required)",
  "notice_id": "string (optional)",
  "target_agency": "string (optional)",
  "hybrid_alpha": 0.6,
  "topk": 15
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "proposal_draft": "string",
    "query": "string",
    "target_agency": "string",
    "notice_id": "string",
    "context_used": 15
  },
  "sources": [
    {
      "document_id": 1,
      "chunk_id": 123,
      "similarity": 0.85,
      "text_preview": "string"
    }
  ]
}
```

### POST `/api/rag/hybrid_search`

Hibrit arama yapar (keyword + semantic).

**Query Parameters:**
- `query`: Arama sorgusu
- `alpha`: Hibrit ağırlık (0.0=keyword, 1.0=semantic)
- `topk`: Döndürülecek kayıt sayısı

## 🔧 Sorun Giderme

### RAG API'ye Bağlanamıyor

1. **Docker servislerini kontrol edin:**
```bash
docker-compose ps
```

2. **RAG API loglarını kontrol edin:**
```bash
docker-compose logs rag_api
```

3. **Network bağlantısını kontrol edin:**
```bash
# Docker içinden
docker-compose exec rag_api curl http://db:5432

# Host makineden
curl http://localhost:8001/api/health
```

### Timeout Hatası

- `RAG_API_TIMEOUT` değerini artırın (varsayılan: 300 saniye)
- LLM modelinin yanıt süresini kontrol edin

### Veritabanı Bağlantı Hatası

- `DB_HOST` değişkeninin `db` (Docker servis adı) olduğundan emin olun
- Docker Compose'daki `depends_on` ayarlarını kontrol edin

### LLM Yanıt Vermiyor

- Ollama/OpenAI API ayarlarını kontrol edin (`.env` dosyasında)
- LLM modelinin yüklü olduğundan emin olun
- API key'lerin doğru olduğundan emin olun

## 📝 Örnek Kullanım Senaryoları

### Senaryo 1: Yeni Fırsat İçin Teklif Oluşturma

```python
from samai_integrator import call_rag_proposal_service

result = call_rag_proposal_service(
    user_query="Bu askeri üs için konaklama hizmetleri teklifinde en kritik başarı faktörleri nelerdir?",
    notice_id="70LART26QPFB00001",
    agency="Department of Homeland Security"
)
```

### Senaryo 2: Geçmiş Fırsatlardan Öğrenme

```python
result = call_rag_proposal_service(
    user_query="Benzer geçmiş fırsatlarda hangi teknik yaklaşımlar başarılı oldu?",
    notice_id="70LART26QPFB00001",
    topk=20  # Daha fazla kaynak
)
```

### Senaryo 3: Compliance Kontrolü

```python
result = call_rag_proposal_service(
    user_query="FAR uyumluluğu için bu fırsatta hangi gereksinimler kritiktir?",
    notice_id="70LART26QPFB00001",
    agency="Department of Defense"
)
```

## 🔗 İlgili Dosyalar

- `samai_integrator.py`: SAMAI entegrasyon modülü
- `api/app/routes/rag.py`: RAG API endpoint'leri
- `api/app/services/llm/rag.py`: RAG servis mantığı
- `docker-compose.yml`: Docker Compose konfigürasyonu
- `streamlit_app_optimized.py`: Streamlit UI entegrasyonu

## 📞 Destek

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. Docker container durumunu kontrol edin
3. API dokümantasyonunu inceleyin: `http://localhost:8001/docs`

