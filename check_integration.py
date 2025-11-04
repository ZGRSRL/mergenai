#!/usr/bin/env python3
"""
RAG Entegrasyon Kontrol Scripti
"""

import os
import sys

def check_files():
    """Dosya varlık kontrolleri"""
    print("=" * 60)
    print("1. DOSYA KONTROLLERİ")
    print("=" * 60)
    
    files_to_check = {
        'samai_integrator.py': 'SAMAI entegrasyon modülü',
        'api/app/routes/rag.py': 'RAG API routes',
        'docker-compose.yml': 'Docker Compose yapılandırması',
        'RAG_INTEGRATION_README.md': 'Dokümantasyon',
        'env.example': 'Environment örnek dosyası',
        'api/app/main.py': 'FastAPI ana dosyası'
    }
    
    all_ok = True
    for file_path, description in files_to_check.items():
        exists = os.path.exists(file_path)
        status = "[OK]" if exists else "[FAIL]"
        print(f"{status} {file_path}")
        if exists:
            print(f"   -> {description}")
        else:
            print(f"   → EKSİK!")
            all_ok = False
    
    return all_ok


def check_docker_compose():
    """Docker Compose yapılandırma kontrolleri"""
    print("\n" + "=" * 60)
    print("2. DOCKER COMPOSE KONTROLLERİ")
    print("=" * 60)
    
    if not os.path.exists('docker-compose.yml'):
        print("[FAIL] docker-compose.yml bulunamadi")
        return False
    
    with open('docker-compose.yml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'rag_api servisi': 'rag_api:' in content,
        'Port mapping (8001:8000)': '8001:8000' in content,
        'DB bağımlılığı': 'depends_on:' in content and '- db' in content,
        'Environment ayarları': 'DB_HOST: db' in content or 'POSTGRES_HOST:' in content,
    }
    
    all_ok = True
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name}")
        if not result:
            all_ok = False
    
    return all_ok


def check_api_main():
    """API main.py kontrolleri"""
    print("\n" + "=" * 60)
    print("3. API MAIN.PY KONTROLLERİ")
    print("=" * 60)
    
    if not os.path.exists('api/app/main.py'):
        print("[FAIL] api/app/main.py bulunamadi")
        return False
    
    with open('api/app/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'RAG router import': 'from .routes import' in content and 'rag' in content,
        'RAG router eklenmiş': 'app.include_router(rag.router' in content,
        'RAG prefix': '/api/rag' in content,
        'RAG tags': 'tags=["rag"]' in content,
    }
    
    all_ok = True
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name}")
        if not result:
            all_ok = False
    
    return all_ok


def check_rag_routes():
    """RAG routes kontrolleri"""
    print("\n" + "=" * 60)
    print("4. RAG ROUTES KONTROLLERİ")
    print("=" * 60)
    
    if not os.path.exists('api/app/routes/rag.py'):
        print("[FAIL] api/app/routes/rag.py bulunamadi")
        return False
    
    with open('api/app/routes/rag.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'generate_proposal endpoint': '@router.post("/generate_proposal"' in content or 'def generate_proposal' in content,
        'ProposalRequest model': 'class ProposalRequest' in content,
        'ProposalResponse model': 'class ProposalResponse' in content,
        'RAG servis import': 'from ..services.llm.rag import' in content,
        'LLM router import': 'from ..services.llm.router import' in content,
    }
    
    all_ok = True
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name}")
        if not result:
            all_ok = False
    
    return all_ok


def check_samai_integrator():
    """SAMAI integrator kontrolleri"""
    print("\n" + "=" * 60)
    print("5. SAMAI INTEGRATOR KONTROLLERİ")
    print("=" * 60)
    
    if not os.path.exists('samai_integrator.py'):
        print("[FAIL] samai_integrator.py bulunamadi")
        return False
    
    with open('samai_integrator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'call_rag_proposal_service fonksiyonu': 'def call_rag_proposal_service' in content,
        'call_rag_hybrid_search fonksiyonu': 'call_rag_hybrid_search' in content,
        'RAG_API_URL kullanımı': 'RAG_API_URL' in content,
        'requests import': 'import requests' in content,
        'Error handling': 'except' in content,
    }
    
    all_ok = True
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name}")
        if not result:
            all_ok = False
    
    # Import testi
    try:
        sys.path.insert(0, '.')
        from samai_integrator import call_rag_proposal_service, call_rag_hybrid_search
        print("[OK] Import testi basarili")
    except Exception as e:
        print(f"[FAIL] Import testi basarisiz: {e}")
        all_ok = False
    
    return all_ok


def check_streamlit_integration():
    """Streamlit entegrasyon kontrolleri"""
    print("\n" + "=" * 60)
    print("6. STREAMLIT ENTEGRASYON KONTROLLERİ")
    print("=" * 60)
    
    if not os.path.exists('streamlit_app_optimized.py'):
        print("[FAIL] streamlit_app_optimized.py bulunamadi")
        return False
    
    with open('streamlit_app_optimized.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'RAG servisi bölümü': 'RAG Servisi ile Teklif Oluştur' in content,
        'samai_integrator import': 'from samai_integrator import' in content,
        'call_rag_proposal_service kullanımı': 'call_rag_proposal_service(' in content,
        'RAG bilgi kutusu': 'RAG Servisi Özellikleri' in content,
    }
    
    all_ok = True
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name}")
        if not result:
            all_ok = False
    
    return all_ok


def main():
    """Ana kontrol fonksiyonu"""
    print("\n" + "=" * 60)
    print("RAG ENTEGRASYON KONTROL RAPORU")
    print("=" * 60 + "\n")
    
    results = {
        'Dosyalar': check_files(),
        'Docker Compose': check_docker_compose(),
        'API Main': check_api_main(),
        'RAG Routes': check_rag_routes(),
        'SAMAI Integrator': check_samai_integrator(),
        'Streamlit Integration': check_streamlit_integration(),
    }
    
    print("\n" + "=" * 60)
    print("ÖZET")
    print("=" * 60)
    
    all_passed = True
    for category, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {category}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] TUM KONTROLLER BASARILI!")
        print("RAG entegrasyonu hazir.")
    else:
        print("[WARN] BAZI KONTROLLER BASARISIZ")
        print("Lutfen yukaridaki hatalari duzeltin.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

