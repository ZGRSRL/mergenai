# İlan Analizi Workflow'u - Implementation Summary

**Tarih:** 2025-11-03  
**Modül:** `analyze_opportunity_workflow.py`  
**Durum:** ✅ Oluşturuldu ve Hazır

---

## 🎯 WORKFLOW MİMARİSİ

### **5 Adımlı Tam Otomatik İşlem:**

```
1. fetch_metadata(notice_id)
   ↓
2. download_and_extract_docs(metadata)
   ↓
3. extract_requirements(text_data)
   ↓
4. analyze_sow(requirements)
   ↓
5. save_analysis(results)
```

---

## 📋 ADIM DETAYLARI

### **ADIM 1: Metadata Çekme** ✅
**Fonksiyon:** `fetch_metadata(notice_id)`

**Yapılanlar:**
- SAM.gov API'den ilan detayları çekilir
- Title, agency, deadline, description
- Attachments listesi
- Point of contact bilgileri
- Fallback: Web scraping (gerekirse)

**Bağımlılıklar:**
- `sam_api_client.py` - SAM API client
- Environment variables: `SAM_PUBLIC_API_KEY`, `SAM_SYSTEM_API_KEY`

**Çıktı:**
```python
{
    'notice_id': '086008536ec84226ad9de043dc738d06',
    'title': 'Hotel and Conference Room Services',
    'agency': 'Department of Defense',
    'posted_date': '2025-01-15',
    'response_deadline': '2025-02-01',
    'attachments': [...],
    'url': 'https://sam.gov/...'
}
```

---

### **ADIM 2: Doküman İndirme ve Metin Çıkarma** ✅
**Fonksiyon:** `download_and_extract_docs(metadata)`

**Yapılanlar:**
- Resource links çekilir
- Her attachment indirilir (PDF, DOCX, TXT)
- Metin çıkarılır (unstructured library)
- Dosyalar notice_id klasöründe saklanır

**Bağımlılıklar:**
- `download_sam_docs.py` - Document downloader
- `unstructured` library - Text extraction

**Çıktı:**
- List of downloaded file paths
- Extracted text from documents

---

### **ADIM 3: Gereksinim Çıkarımı** ✅
**Fonksiyon:** `extract_requirements(metadata, downloaded_files)`

**Yapılanlar:**
- LLM ile yapılandırılmış gereksinim çıkarımı
- 6 kategori:
  1. Room Requirements
  2. Conference Requirements
  3. AV Requirements
  4. Catering Requirements
  5. Compliance Requirements
  6. Pricing Requirements

**Bağımlılıklar:**
- Ollama/OpenAI LLM
- Environment: `USE_OLLAMA`, `OLLAMA_URL`, `OLLAMA_MODEL`

**LLM Prompt:**
```python
"Aşağıdaki SAM.gov ilan dokümanını analiz et ve gereksinimleri çıkar.
JSON formatında yanıt ver: {...}"
```

**Fallback:**
- LLM yoksa temel keyword matching kullanılır

**Çıktı:**
```python
{
    'room_requirements': {...},
    'conference_requirements': {...},
    'av_requirements': {...},
    'catering_requirements': {...},
    'compliance_requirements': {...},
    'pricing_requirements': {...},
    'general_requirements': [...]
}
```

---

### **ADIM 4: SOW Analizi** ✅
**Fonksiyon:** `analyze_sow(requirements)`

**Yapılanlar:**
- Requirements'dan SOW yapısı oluşturulur
- Yapılandırılmış SOW payload hazırlanır:
  - period_of_performance
  - room_block
  - function_space
  - av
  - refreshments
  - location
  - pre_con_meeting
  - tax_exemption

**Çıktı:**
```python
{
    'period_of_performance': {...},
    'room_block': {...},
    'function_space': {...},
    'av': {...},
    'refreshments': {...},
    'location': {...},
    'assumptions': [...]
}
```

---

### **ADIM 5: Veritabanına Kaydetme** ✅
**Fonksiyon:** `save_analysis(metadata, requirements, sow_analysis)`

**Yapılanlar:**
- Source documents hash hesaplanır
- SOW payload oluşturulur
- `sow_analysis` tablosuna kaydedilir
- Idempotent upsert (ON CONFLICT)

**Bağımlılıklar:**
- `sow_analysis_manager.py`
- Database: `ZGR_AI.sow_analysis`

**Kaydedilen Veriler:**
- notice_id
- template_version ("v1.0")
- sow_payload (JSONB)
- source_docs (JSONB)
- source_hash (idempotency için)

---

## 🚀 KULLANIM

### **Python'dan:**
```python
from analyze_opportunity_workflow import OpportunityAnalysisWorkflow

workflow = OpportunityAnalysisWorkflow(
    download_dir="./downloads",
    use_llm=True
)

result = workflow.run("086008536ec84226ad9de043dc738d06")

if result.success:
    print(f"Analiz ID: {result.analysis_id}")
    print(f"İndirilen dosya: {len(result.downloaded_files)}")
```

### **Command Line:**
```bash
# LLM ile
python analyze_opportunity_workflow.py 086008536ec84226ad9de043dc738d06

# LLM olmadan
python analyze_opportunity_workflow.py 086008536ec84226ad9de043dc738d06 --no-llm

# Özel download dizini
python analyze_opportunity_workflow.py 086008536ec84226ad9de043dc738d06 --download-dir ./custom_downloads
```

---

## 📊 ÇIKTI FORMATI

### **AnalysisWorkflowResult:**
```python
{
    "notice_id": "086008536ec84226ad9de043dc738d06",
    "success": true,
    "metadata": {...},
    "downloaded_files": ["path/to/file1.pdf", ...],
    "extracted_requirements": {...},
    "sow_analysis": {...},
    "analysis_id": "uuid-here",
    "errors": [],
    "timestamp": "2025-11-03T14:30:00"
}
```

---

## 🔧 ENVIRONMENT VARIABLES

```bash
# SAM API
SAM_PUBLIC_API_KEY=your_public_key
SAM_SYSTEM_API_KEY=your_system_key

# LLM
USE_OLLAMA=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Alternatif: OpenAI
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini

# Download Path
DOWNLOAD_PATH=./downloads
```

---

## ✅ TEST DURUMU

### **Test Edilecek:**
- [ ] Metadata çekme (SAM API)
- [ ] Doküman indirme
- [ ] Metin çıkarma
- [ ] LLM gereksinim çıkarımı
- [ ] SOW analizi
- [ ] Veritabanı kaydı

### **Test Komutu:**
```bash
python analyze_opportunity_workflow.py 086008536ec84226ad9de043dc738d06
```

---

## 🔗 ENTEGRASYON NOKTALARI

### **1. Streamlit Entegrasyonu:**
```python
# streamlit sayfasında
if st.button("İlanı Analiz Et"):
    workflow = OpportunityAnalysisWorkflow()
    result = workflow.run(notice_id)
    
    if result.success:
        st.success(f"Analiz tamamlandı: {result.analysis_id}")
        st.json(result.sow_analysis)
```

### **2. RAG Entegrasyonu:**
- İlan analizi tamamlandıktan sonra
- RAG sistemine beslenebilir
- Benzer fırsatlardan öğrenme yapılabilir

### **3. Teklif Oluşturma:**
- SOW analizi + RAG öğrenmesi
- Teklif taslağı oluşturulabilir

---

## 📝 SONRAKI ADIMLAR

1. ✅ **Workflow modülü oluşturuldu**
2. ⏳ **Test edilmeli** (canlı ilan üzerinde)
3. ⏳ **Streamlit sayfasına entegre edilmeli**
4. ⏳ **RAG sistemi ile birleştirilmeli**

---

**Durum:** 🟢 WORKFLOW HAZIR - Test edilmeye hazır!

