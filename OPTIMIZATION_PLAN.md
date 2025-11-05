# Database Performance Optimization Plan

## 🎯 Optimizasyon Hedefleri

### 1. **Veritabanı Birleştirme** ✅ (Zaten Yapılmış)
- **Mevcut Durum**: ZGR_AI veritabanı kullanılıyor
- **Durum**: `sam` DB'si artık kullanılmıyor, tüm veriler ZGR_AI'da
- **Kazanım**: %50 maliyet azalması, yönetim kolaylığı

### 2. **HNSW İndeksine Geçiş** 🔄
- **Mevcut**: IVFFlat indeksi (varsa)
- **Hedef**: HNSW (Hierarchical Navigable Small World)
- **Kazanım**: 
  - %10-20 daha hızlı arama
  - Daha düşük gecikme (latency)
  - Daha doğru sonuçlar
- **Parametreler**: 
  - `m = 16` (her katmanda bağlantı sayısı)
  - `ef_construction = 64` (index oluşturma kalitesi)

### 3. **Chunk Tablolarını Birleştirme** 🔄
- **Mevcut**: 
  - `sam_chunks` (172,402 chunks - hotel data)
  - `vector_chunks` (opsiyonel - eski SAM data)
- **Hedef**: `unified_chunks` tablosu
- **Yeni Kolonlar**:
  - `source_type`: 'hotel_title', 'hotel_description', 'hotel_document', 'sam_document'
  - `source_id`: notice_id, document_id
  - `embedding_vector`: vector(384) - HNSW için
  - `embedding_jsonb`: JSONB - uyumluluk için
- **Kazanım**:
  - Veri bütünlüğü
  - Karmaşık JOIN'lerin ortadan kalkması
  - Tek sorgu ile tüm chunk'lara erişim

## 📊 Mevcut Durum Analizi

### Tablo Yapıları

#### `sam_chunks` (ZGR_AI)
```sql
- chunk_id (PK)
- opportunity_id (VARCHAR)
- content (TEXT)
- embedding (JSONB)
- chunk_type (VARCHAR) - 'title', 'description', 'document'
- created_at (TIMESTAMP)
```

#### `vector_chunks` (ZGR_AI - opsiyonel)
```sql
- id (PK)
- document_id (INTEGER)
- chunk (TEXT)
- embedding (JSONB veya VECTOR)
- chunk_type (VARCHAR)
- page_number (INTEGER)
```

## 🚀 Optimizasyon Adımları

### ADIM 1: HNSW İndeksi Oluşturma
```bash
python optimize_database_performance.py
# Seçenek: "1. Migrate to HNSW" → y
```

**Yapılacaklar**:
1. pgvector extension kontrolü
2. JSONB → VECTOR dönüşümü (gerekirse)
3. IVFFlat indeksi silme (varsa)
4. HNSW indeksi oluşturma

### ADIM 2: Chunk Tablolarını Birleştirme
```bash
python optimize_database_performance.py
# Seçenek: "2. Unify chunk tables" → y
```

**Yapılacaklar**:
1. `unified_chunks` tablosu oluşturma
2. `sam_chunks` → `unified_chunks` migrasyonu
3. `vector_chunks` → `unified_chunks` migrasyonu (varsa)
4. Index'ler oluşturma (HNSW dahil)

### ADIM 3: Uygulama Kodlarını Güncelleme
- `streamlit_app.py`: `sam_chunks` → `unified_chunks`
- RAG API: `sam_chunks` → `unified_chunks`
- Tüm sorgular: `source_type` filtresi ekleme

## ⚠️ Dikkat Edilmesi Gerekenler

1. **Backup**: Optimizasyon öncesi mutlaka backup alın
2. **Downtime**: HNSW indeksi oluşturma sırasında kısa bir downtime olabilir
3. **Test**: Production'a geçmeden önce test ortamında deneyin
4. **Rollback Plan**: Eski tabloları silmeden önce bir süre tutun

## 📈 Beklenen Performans İyileştirmeleri

| Metrik | Önce | Sonra | İyileşme |
|--------|------|-------|----------|
| Arama Hızı | 100ms | 80-90ms | %10-20 |
| Doğruluk | %95 | %98 | +%3 |
| Veri Bütünlüğü | Orta | Yüksek | ✅ |
| Yönetim Kolaylığı | Orta | Yüksek | ✅ |

## 🔄 Rollback Planı

Eğer sorun çıkarsa:
1. `unified_chunks` tablosunu sil
2. `sam_chunks` tablosu korunmuş olacak
3. Eski sorguları kullanmaya devam et

## 📝 Sonraki Adımlar

1. ✅ Optimizasyon scriptini test et
2. ✅ Backup al
3. ✅ Production'da çalıştır
4. ✅ Uygulama kodlarını güncelle
5. ✅ Performans metriklerini izle

