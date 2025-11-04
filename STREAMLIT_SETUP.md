# Streamlit Yönetim Paneli - Kurulum ve Kullanım

## 🚀 Hızlı Başlangıç

### **Yöntem 1: Tek Dosya (Tabs)**
```bash
cd d:\ZgrSam
streamlit run streamlit_app.py
```

### **Yöntem 2: Multi-Page (Pages)**
```bash
cd d:\ZgrSam
streamlit run streamlit_pages/1_🏆_Ana_Sayfa.py
```

## 📁 Dosya Yapısı

```
d:\ZgrSam\
├── streamlit_app.py              # Ana uygulama (tabs yapısı)
├── streamlit_pages/
│   ├── 1_🏆_Ana_Sayfa.py          # Dashboard
│   ├── 2_🔍_İlan_Analizi.py       # Opportunity analysis
│   ├── 3_🧠_Hybrid_RAG_Sorgu.py   # RAG search
│   └── 4_🤖_LLM_Ajani.py          # Chat interface
└── streamlit_opportunity_analysis.py  # Eski versiyon (backup)
```

## ⚙️ Yapılandırma

### **Environment Variables:**
```bash
# RAG API URL
export RAG_API_URL="http://localhost:8001"

# Database DSN
export DB_DSN="dbname=ZGR_AI user=postgres password=sarlio41 host=localhost port=5432"
```

### **Windows PowerShell:**
```powershell
$env:RAG_API_URL="http://localhost:8001"
$env:DB_DSN="dbname=ZGR_AI user=postgres password=sarlio41 host=localhost port=5432"
```

## 📊 Özellikler

### **1. Ana Sayfa / Dashboard**
- ✅ Platform istatistikleri
- ✅ Chunk dağılımı grafikleri
- ✅ Hızlı erişim linkleri

### **2. İlan Analizi**
- ✅ SAM.gov notice ID ile analiz
- ✅ Metadata çekme
- ✅ Doküman indirme
- ✅ Gereksinim çıkarımı
- ✅ SOW analizi
- ✅ Veritabanı kaydı

### **3. Hybrid RAG Sorgu**
- ✅ 172,402 chunk'ta semantic search
- ✅ Hybrid alpha ayarı (0.0-1.0)
- ✅ Kalite skoru filtresi
- ✅ Top-K chunk seçimi

### **4. LLM Ajanı (Chat)**
- ✅ AutoGen tabanlı sohbet
- ✅ Teklif taslağı oluşturma
- ✅ Stratejik analiz
- ✅ Kaynak referansları

## 🔧 Bağımlılıklar

```bash
pip install streamlit pandas requests psycopg2-binary
```

## 🎨 Tasarım Özellikleri

- **Wide Layout:** Geniş ekran optimizasyonu
- **Modern UI:** Custom CSS ve metric cards
- **Performance:** `@st.cache_data` ve `@st.cache_resource` ile optimizasyon
- **Responsive:** Column-based responsive layout

## 🔗 API Entegrasyonları

### **RAG API Endpoints:**
- `POST /api/rag/hybrid_search` - Hybrid search
- `POST /api/rag/generate_proposal` - Proposal generation

### **Database:**
- `ZGR_AI` PostgreSQL database
- `sam_chunks` table
- `hotel_opportunities_new` table
- `sow_analysis` table

## 🐛 Sorun Giderme

### **RAG API Bağlantı Hatası:**
```python
# streamlit_app.py içinde RAG_API_URL'i kontrol edin
RAG_API_URL = "http://localhost:8001"  # FastAPI URL'iniz
```

### **Database Bağlantı Hatası:**
```python
# DB_DSN environment variable'ı ayarlayın
export DB_DSN="dbname=ZGR_AI user=postgres password=YOUR_PASSWORD host=localhost port=5432"
```

### **Import Hataları:**
```bash
# analyze_opportunity_workflow.py'nin aynı dizinde olduğundan emin olun
cd d:\ZgrSam
python -c "import analyze_opportunity_workflow; print('OK')"
```

## 📈 Performans Optimizasyonları

1. **Cache Decorators:**
   - `@st.cache_data` - Platform stats (300s TTL)
   - `@st.cache_resource` - RAG client

2. **Lazy Loading:**
   - İlk kullanımda yükleme
   - Session state kullanımı

3. **Batch Processing:**
   - Top-K limit ile sınırlı sonuçlar
   - Pagination (ileride)

