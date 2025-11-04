# Fırsat Analiz Merkezi - Kullanım Kılavuzu

## 🎯 Genel Bakış

**Fırsat Analiz Merkezi** (`opportunity_analysis.py`), SAM.gov ilanlarını otomatik olarak analiz eden, AutoGen destekli kapsamlı bir Streamlit uygulamasıdır.

## 📋 Özellikler

### 1. **Yeni İlan Analizi**
- SAM.gov Notice ID ile analiz başlatma
- Metadata çekme (SAM API)
- Doküman indirme ve metin çıkarma
- AutoGen ile gereksinim çıkarımı
- SOW analizi
- Veritabanına kaydetme

### 2. **Doküman Yönetimi**
- İndirilen dokümanları görüntüleme
- Dosya listesi ve detayları
- Dosya önizleme (metin dosyaları için)

### 3. **Analiz Sonuçları**
- Kayıtlı analizleri listeleme
- Detaylı analiz görüntüleme
- JSON formatında tam analiz verisi

### 4. **AutoGen Agent Logs**
- LLM ajanlarının çalışma logları
- Gereksinim çıkarım süreçleri
- Muhakeme adımları

## 🚀 Kullanım

### Başlatma

```bash
cd d:\ZgrSam
streamlit run sam/document_management/opportunity_analysis.py
```

Veya ana Streamlit uygulamasından:

```bash
streamlit run streamlit_app.py
# "🔍 İlan Analizi" sekmesine gidin
```

### Analiz Yapma

1. **Notice ID Girin:** SAM.gov'dan ilan ID'sini girin
2. **Ayarları Yapın:**
   - LLM ile gereksinim çıkarımı (✅/❌)
   - LLM Provider seçimi (OpenAI/Ollama/Auto)
   - Download dizini
3. **Analiz Başlatın:** "🚀 İlanı Analiz Et" butonuna tıklayın
4. **Sonuçları İnceleyin:** 
   - Metadata, Gereksinimler, SOW Analizi
   - İndirilen dosyalar
   - AutoGen logları

## ⚙️ Yapılandırma

### Environment Variables

```bash
# SAM API
SAM_PUBLIC_API_KEY=your_key
SAM_SYSTEM_API_KEY=your_key

# Database
DB_DSN=dbname=ZGR_AI user=postgres password=your_pass host=localhost port=5432

# Download Path
DOWNLOAD_PATH=./downloads

# LLM (Optional)
OPENAI_API_KEY=your_key  # OpenAI için
OLLAMA_HOST=http://localhost:11434  # Ollama için
```

## 🔧 Bağımlılıklar

```bash
pip install streamlit pandas psycopg2-binary python-dotenv
```

## 📊 Veri Akışı

```
SAM.gov İlanı
    ↓
[1] Metadata Çekme (SAM API)
    ↓
[2] Doküman İndirme (SAM API)
    ↓
[3] Metin Çıkarma (unstructured)
    ↓
[4] Gereksinim Çıkarımı (AutoGen)
    ↓
[5] SOW Analizi (Structured JSON)
    ↓
[6] Veritabanına Kaydetme (ZGR_AI)
    ↓
✅ Analiz Tamamlandı
```

## 🎨 Arayüz Özellikleri

- **Modern Tasarım:** Custom CSS ile profesyonel görünüm
- **Real-time Progress:** İlerleme çubuğu ve status mesajları
- **Detaylı Sonuçlar:** JSON viewer ile yapılandırılmış veri
- **Doküman Yönetimi:** Dosya listesi ve önizleme
- **Agent Logs:** AutoGen muhakeme süreçleri

## 🐛 Sorun Giderme

### SAM API Bağlantı Hatası
- API key'lerin doğru olduğundan emin olun
- Network bağlantısını kontrol edin

### Database Bağlantı Hatası
- PostgreSQL servisinin çalıştığını kontrol edin
- DB_DSN ayarlarını doğrulayın

### LLM Hatası
- OpenAI API key'i ayarlı mı?
- Ollama servisi çalışıyor mu?
- `use_llm=False` ile deneyin (fallback mode)

## 📈 Sonraki Adımlar

1. **RAG Entegrasyonu:** Analiz sonuçlarını RAG sistemine besleme
2. **Teklif Oluşturma:** Analiz sonuçlarından teklif taslağı oluşturma
3. **Batch Processing:** Çoklu ilan analizi
4. **Email Notifications:** Analiz tamamlandığında bildirim

