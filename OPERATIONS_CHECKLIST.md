# 🚀 Production Operations Checklist

## ✅ Completed Improvements

### 1. 📊 Log & İzleme
- **AgentLogManager rotasyonu**: 30 gün saklama politikası ✅
- **Log alanları**: notice_id, agent, duration_ms, status, error_type, schema_version ✅
- **STOP. yakalama metrikleri**: termination_reason, turn_count ✅

### 2. 🔄 Watcher Sağlamlaştırma
- **run_workflow_for_notice() status map**: UI'da tablo (success/failed + hata nedeni) ✅
- **Rate limit guard**: Exponential backoff + jitter (global limiter) ✅
- **Duplicate guard**: Aynı notice_id + source_hash için idempotent skip ✅

### 3. 🔒 Güvenlik / Anahtar Yönetimi
- **.env → .env.example ayrımı**: Gerçek anahtar yok ✅
- **SAM, SMTP, OpenAI anahtarları**: Process-level mask (loglara düşmesin) ✅
- **İndirme klasöründe zararlı içerik koruması**: MIME doğrulama + boyut sınırı ⏳

### 4. 🧪 CI & Test
- **smoke_test_suite.py**: Comprehensive test suite ✅
  - Yeni Fırsatlar: arama → ilk notice indir/analiz → DB kayıt doğrula
  - Comparison Agent: iki notice delta
  - Email Reporter: dry-run + SMTP bağlantı testi
  - Mini load test: 5 notice ardışık (rate-limit toleransı ölç)

### 5. 🚨 Alarmlar (Ops)
- **Success rate < %80**: E-posta uyarı ✅
- **Ortalama süre > 15s**: Uyarı ✅
- **500/401/403 artışı**: Ayrı alarm (SAM API health) ✅

## 🔧 Yararlı Komutlar / Kod Parçaları

### JSONB Index (Örnek)
```sql
CREATE INDEX IF NOT EXISTS idx_sow_gen_capacity
ON sow_analysis ((sow_payload #>> '{function_space,general_session,capacity}'));

CREATE INDEX IF NOT EXISTS idx_sow_period_start
ON sow_analysis ((sow_payload #>> '{period_of_performance,start}'));

CREATE INDEX IF NOT EXISTS idx_sow_period_end
ON sow_analysis ((sow_payload #>> '{period_of_performance,end}'));
```

### İdempotent Upsert (Örnek, notice+version)
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_sow_notice_version
ON sow_analysis (notice_id, template_version);
```

### Rate-limit Guard (Python İskeleti)
```python
import time, random
def backoff_sleep(attempt, base=1.0, cap=32):
    time.sleep(min(cap, base * (2 ** attempt)) + random.uniform(0, 0.5))
```

## 📋 Production Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured (.env)
- [ ] Database schema created (sow_analysis table)
- [ ] SMTP credentials configured
- [ ] SAM API key configured
- [ ] Log directories created
- [ ] Security masks tested

### Deployment
- [ ] Code deployed to production
- [ ] Database migrations run
- [ ] Environment variables loaded
- [ ] Services started
- [ ] Health checks passing

### Post-Deployment
- [ ] Smoke tests run successfully
- [ ] Monitoring alerts configured
- [ ] Log rotation working
- [ ] Rate limiting active
- [ ] Duplicate guard enabled

## 🎯 Performance Targets

### SLO (Service Level Objectives)
- **P95 Processing Time**: < 10 seconds
- **Success Rate**: > 95%
- **Availability**: > 99.9%
- **Error Rate**: < 1%

### Monitoring Metrics
- **Agent Performance**: Success rate, processing time
- **API Health**: Error rates, response times
- **System Resources**: CPU, memory, disk usage
- **Business Metrics**: Notices processed, analysis completed

## 🚨 Alert Thresholds

### Critical Alerts
- Success rate < 80%
- Processing time > 15s average
- API error rate > 10%
- System down

### Warning Alerts
- Success rate < 90%
- Processing time > 10s average
- API error rate > 5%
- High resource usage

## 🔄 Maintenance Tasks

### Daily
- [ ] Check system health
- [ ] Review error logs
- [ ] Monitor performance metrics
- [ ] Verify backups

### Weekly
- [ ] Review alert patterns
- [ ] Analyze performance trends
- [ ] Update documentation
- [ ] Security audit

### Monthly
- [ ] Rotate API keys
- [ ] Update dependencies
- [ ] Performance optimization
- [ ] Capacity planning

## 📊 Monitoring Dashboard

### Key Metrics to Track
1. **System Health**
   - Service status
   - Error rates
   - Response times

2. **Agent Performance**
   - Success rates by agent
   - Processing times
   - Termination metrics

3. **Business Metrics**
   - Notices processed
   - Analysis completed
   - User activity

4. **Infrastructure**
   - Database performance
   - API rate limits
   - Storage usage

## 🛠️ Troubleshooting Guide

### Common Issues
1. **Database Connection Errors**
   - Check connection string
   - Verify database is running
   - Check network connectivity

2. **API Rate Limiting**
   - Check rate limit configuration
   - Verify backoff settings
   - Monitor API usage

3. **Agent Failures**
   - Check agent logs
   - Verify input data
   - Check termination conditions

4. **Performance Issues**
   - Check system resources
   - Review processing times
   - Analyze bottlenecks

## 📈 Future Enhancements

### Short Term
- [ ] Database schema optimization
- [ ] Enhanced error handling
- [ ] Performance monitoring
- [ ] Automated testing

### Long Term
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] Advanced analytics
- [ ] Machine learning integration

## 📞 Support Contacts

### Development Team
- Lead Developer: [Name]
- DevOps Engineer: [Name]
- Database Admin: [Name]

### Operations Team
- On-call Engineer: [Name]
- System Admin: [Name]
- Security Officer: [Name]

## 📚 Documentation Links

- [API Documentation](docs/api.md)
- [Database Schema](docs/database.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

---

**Last Updated**: 2025-10-18
**Version**: 1.0.0
**Status**: Production Ready ✅

