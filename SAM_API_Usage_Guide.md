# SAM API Kullanım Rehberi

## 🔑 **API Key Ayarlama**

### **PowerShell'de:**
```powershell
# Geçici olarak (sadece bu session için)
$env:SAM_PUBLIC_API_KEY="your_actual_api_key_here"

# Kalıcı olarak (sistem genelinde)
[Environment]::SetEnvironmentVariable("SAM_PUBLIC_API_KEY", "your_actual_api_key_here", "User")
```

### **Command Prompt'da:**
```cmd
set SAM_PUBLIC_API_KEY=your_actual_api_key_here
```

### **Python'da:**
```python
import os
os.environ['SAM_PUBLIC_API_KEY'] = 'your_actual_api_key_here'
```

---

## 🧪 **Test Etme**

### **1. API Key Test:**
```bash
python test_sam_with_key.py
```

### **2. SAM Client Test:**
```bash
python sam_api_client.py
```

### **3. Entegre Workflow Test:**
```bash
python sow_sam_integrated_workflow.py
```

---

## 📋 **API Key Alma**

### **SAM.gov'dan API Key Alma:**
1. [SAM.gov](https://sam.gov) hesabınıza giriş yapın
2. **Account Details** sayfasına gidin
3. **API Key** bölümünden yeni key oluşturun
4. Key'i kopyalayın ve environment variable olarak ayarlayın

### **System Account (FOUO/Sensitive için):**
1. Federal System Account oluşturun
2. Uygun permissions verin (Read Public, Read FOUO, Read Sensitive)
3. API key oluşturun
4. `SAM_SYSTEM_API_KEY` olarak ayarlayın

---

## 🚀 **Kullanım Örnekleri**

### **Temel Kullanım:**
```python
from sam_api_client import SAMAPIClient

# Client oluştur
client = SAMAPICLient(mode="auto")

# Fırsat ara
opportunities = client.search_opportunities(
    notice_id="70LART26QPFB00001",
    posted_from="10/01/2024",
    posted_to="12/01/2024"
)

# Dokümanları indir
files = client.download_all_attachments(
    "70LART26QPFB00001", 
    "downloads/"
)
```

### **Entegre Workflow:**
```python
from sow_sam_integrated_workflow import SOWSAMIntegratedWorkflow

# Workflow oluştur
workflow = SOWSAMIntegratedWorkflow()

# Fırsatı işle
result = workflow.process_opportunity_from_sam(
    "70LART26QPFB00001",
    download_dir="sam_downloads",
    process_attachments=True
)
```

---

## ⚠️ **Önemli Notlar**

### **Rate Limiting:**
- SAM.gov API rate limiting uygular
- Client otomatik olarak 100ms interval kullanır
- Toplu işlemlerde dikkatli olun

### **API Key Güvenliği:**
- API key'leri environment variable olarak saklayın
- Git'e commit etmeyin
- Production'da güvenli key management kullanın

### **Error Handling:**
- 401/403 hatalarında system account'a otomatik geçiş
- Network hatalarında retry mekanizması
- Timeout ayarları (60s default)

---

## 🔧 **Troubleshooting**

### **401 Unauthorized:**
- API key'in doğru olduğunu kontrol edin
- Environment variable'ın ayarlandığını kontrol edin
- SAM.gov hesabınızın aktif olduğunu kontrol edin

### **403 Forbidden:**
- FOUO/Sensitive içerik için system account gerekebilir
- API key'in uygun permissions'ı olduğunu kontrol edin

### **Rate Limit Exceeded:**
- İstekler arasında daha fazla bekleme süresi ekleyin
- Batch processing'i daha küçük gruplara bölün

---

## 📊 **Test Sonuçları Beklentileri**

### **Başarılı Test:**
```
[SUCCESS] API connection working!
[SUCCESS] Opportunity details retrieved!
  - Title: Off-Center Lodging, FLETC Artesia
  - Agency: Department of Homeland Security
  - Posted Date: 2024-10-15
[SUCCESS] Resource links: X found
[SUCCESS] Downloaded: downloads/attachment_1.pdf
```

### **API Key Yok:**
```
[ERROR] API connection failed
401 Client Error: Unauthorized
```

### **Fırsat Bulunamadı:**
```
[WARNING] Opportunity not found
```

---

## 🎯 **Sonraki Adımlar**

1. **API Key Alın:** SAM.gov'dan public API key alın
2. **Environment Variable Ayarlayın:** `SAM_PUBLIC_API_KEY` olarak ayarlayın
3. **Test Edin:** `python test_sam_with_key.py` çalıştırın
4. **Production'a Geçin:** Gerçek API key ile sistemi kullanın

**API key'inizi aldıktan sonra sistemi test edebilirsiniz!** 🚀
