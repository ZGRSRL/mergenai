# 🚀 Optimizasyon Test Rehberi

## ✅ Test Adımları

### 1. Redis Başlatma
```bash
cd d:\ZgrSam
docker-compose up -d redis
```

### 2. Streamlit Uygulamasını Başlatma
```bash
streamlit run streamlit_app_optimized.py
```

### 3. Test Senaryoları

#### Senaryo 1: Cache HIT Testi
1. **SOW Analizi (LLM Teklif)** sekmesine gidin
2. Bir Notice ID ve query girin
3. **"🚀 RAG ile Teklif Oluştur"** butonuna tıklayın
4. İlk istek: **"💾 Cache SET - Response cached"** görünmeli
5. Aynı query'yi tekrar çalıştırın
6. İkinci istek: **"💰 Cache HIT - Saved LLM API call"** görünmeli

#### Senaryo 2: Health Check Testi
1. **Sidebar**'da **System Status** bölümünü kontrol edin
2. **🟢 RAG API (45ms)** görünmeli
3. **🟢 Redis Cache (Connected)** görünmeli
4. **⚙️ Ayarlar** sekmesine gidin
5. **🔗 API/Files Durumu** bölümünü kontrol edin
6. Detaylı health bilgileri görünmeli

#### Senaryo 3: Cache Management Testi
1. **⚙️ Ayarlar** sekmesine gidin
2. **💾 Redis Cache Yönetimi** bölümünü kontrol edin
3. **Cache Keys**, **Memory Usage** metriklerini görün
4. **"🗑️ Cache'i Temizle"** butonuna tıklayın
5. Cache temizlendiğini doğrulayın

---

## 📊 Beklenen Sonuçlar

### Sidebar'da:
```
🔧 System Status
🟢 RAG API (45ms)
🟢 Redis Cache (Connected)
```

### Ayarlar Sekmesinde:
```
🔗 API/Files Durumu
🟢 RAG API | Response Time: 45ms | Status: Healthy

💾 Redis Cache Durumu
🟢 Connected | Keys: 5 | Memory: 2.1MB

💾 Redis Cache Yönetimi
Cache Keys: 5
Memory Usage: 2.1 MB
Total Redis Keys: 5
```

### Cache Optimizasyonu:
```
💰 Cache HIT - Saved LLM API call
💾 Cache SET - Response cached
```

---

## 🎯 Maliyet Tasarrufu Hesabı

**Öncesi:**
- Her RAG query → LLM API call ($0.01-0.05)
- Tekrarlanan sorgular → Tam maliyet

**Sonrası:**
- İlk query → LLM API call + Cache
- Tekrarlanan sorgular → Cache HIT ($0.00)
- **%70-90 maliyet tasarrufu** (tipik kullanımda)

---

## 🔧 Sorun Giderme

### Redis Bağlantı Hatası
```bash
# Redis'i kontrol et
docker-compose ps redis

# Redis loglarını kontrol et
docker-compose logs redis

# Redis'i yeniden başlat
docker-compose restart redis
```

### RAG API Health Check Hatası
```bash
# RAG API'yi kontrol et
curl http://localhost:8001/health

# RAG API loglarını kontrol et
docker-compose logs rag_api
```

### Cache Çalışmıyor
- Redis'in çalıştığından emin olun
- `.env` dosyasında `REDIS_URL` ayarını kontrol edin
- Streamlit loglarını kontrol edin

---

## 🏆 Başarı Kriterleri

✅ Sidebar'da health status görünüyor
✅ Ayarlar'da detaylı health bilgileri var
✅ Cache HIT/MISS mesajları görünüyor
✅ Cache istatistikleri doğru gösteriliyor
✅ Cache temizleme çalışıyor

---

## 📝 Notlar

- Redis connection: Docker içinde `redis://redis:6379/0`, host makinede `redis://localhost:6379/0`
- Cache TTL: 1 saat (3600 saniye) - Ayarlanabilir
- Health check: Her Streamlit sayfa yüklemesinde otomatik
- Graceful degradation: Redis yoksa cache devre dışı, uygulama çalışmaya devam eder

