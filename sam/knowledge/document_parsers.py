#!/usr/bin/env python3
"""
Document Parsers - Ekleri türüne göre ayrıştır
"""

import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# PyMuPDF import with fallback
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available, using mock PDF parser")

def _pdf_text_pages(path: Path) -> List[str]:
    """PDF'den sayfa sayfa metin çıkar"""
    if not PYMUPDF_AVAILABLE:
        # Mock PDF parser for testing
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # Split into mock pages
            pages = [content[i:i+1000] for i in range(0, len(content), 1000)]
            return pages if pages else [content]
        except Exception as e:
            print(f"Mock PDF parsing error for {path}: {e}")
            return []
    
    try:
        doc = fitz.open(path)
        pages = [page.get_text("text") or "" for page in doc]
        doc.close()
        return pages
    except Exception as e:
        print(f"PDF parsing error for {path}: {e}")
        return []

def _sha256(path: Path) -> str:
    """Dosya SHA256 hash'i hesapla"""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            h.update(f.read())
        return h.hexdigest()
    except Exception as e:
        print(f"SHA256 error for {path}: {e}")
        return ""

class ParsedDoc:
    """Ayrıştırılmış doküman"""
    def __init__(self, filename: str, pages: List[str], sha256: str):
        self.filename = filename
        self.pages = pages
        self.sha256 = sha256
        self.full_text = "\n".join(pages)

def load_attachments(dirpath: Path) -> List[ParsedDoc]:
    """Attachments klasöründen tüm PDF'leri yükle"""
    out = []
    if not dirpath.exists():
        print(f"Attachments directory not found: {dirpath}")
        return out
    
    for p in dirpath.glob("*.pdf"):
        pages = _pdf_text_pages(p)
        if pages:  # Sadece başarılı parse edilenleri ekle
            out.append(ParsedDoc(p.name, pages, _sha256(p)))
    
    return out

# --- Heuristics ---

def parse_fire_safety(p: ParsedDoc) -> Dict[str, Any]:
    """Fire Safety dokümanlarını ayrıştır"""
    text = p.full_text.lower()
    
    # Fire safety keywords
    fire_keywords = ["sprinkler", "smoke detector", "nfpa", "fire safety act", "hotel and motel fire safety"]
    must = any(k in text for k in fire_keywords)
    
    # Sayfa numaralarını bul
    fire_pages = [i+1 for i, page_text in enumerate(p.pages) if any(k in page_text.lower() for k in fire_keywords)]
    
    return {
        "compliance_required": must,
        "citations": [{"file": p.filename, "pages": fire_pages}],
        "rationale": "Hotel must comply with the Hotel and Motel Fire Safety Act of 1990" if must else None
    }

def parse_wage_determination(p: ParsedDoc) -> Dict[str, Any]:
    """Wage Determination dokümanlarını ayrıştır"""
    text = p.full_text
    sca = bool(re.search(r"service contract act|sca", text, re.I))
    
    return {
        "sca_applicable": sca,
        "rationale": "Service Contract Act appears applicable per wage determination attachment" if sca else None
    }

def parse_invoice_template(p: ParsedDoc) -> Dict[str, Any]:
    """Invoice Template dokümanlarını ayrıştır"""
    text = p.full_text
    tax_exempt = bool(re.search(r"tax\s*exempt", text, re.I))
    
    # Invoice fields
    fields = [f for f in ["UEI", "BPA", "UNIT PRICE", "TOTAL", "DATE", "INVOICE NUMBER"] if f in text.upper()]
    
    return {
        "invoice_fields": fields,
        "tax_exempt": tax_exempt,
        "rationale": "Invoice template explicitly indicates TAX EXEMPT; pricing should exclude tax" if tax_exempt else None
    }

def parse_of347(p: ParsedDoc) -> Dict[str, Any]:
    """OF347 form dokümanlarını ayrıştır"""
    text = p.full_text.lower()
    need_of347 = "of 347" in text or "order for supplies or services" in text
    
    return {
        "of347_required": need_of347,
        "rationale": "OF347 form required for supplies/services orders" if need_of347 else None
    }

def parse_summary_sow_like(p: ParsedDoc) -> Dict[str, Any]:
    """SOW benzeri dokümanları ayrıştır"""
    text = p.full_text
    
    # Projector lumens
    lumens_match = re.search(r"(\d{1,2}[, ]?000)\s*lumen", text, re.I)
    lumens = int(lumens_match.group(1).replace(',', '').replace(' ', '')) if lumens_match else None
    
    # Room requirements
    rooms_match = re.search(r"(\d+)\s*room", text, re.I)
    rooms = int(rooms_match.group(1)) if rooms_match else None
    
    # Capacity requirements
    capacity_match = re.search(r"(\d+)\s*(?:person|participant|attendee)", text, re.I)
    capacity = int(capacity_match.group(1)) if capacity_match else None
    
    # Duration
    duration_match = re.search(r"(\d+)\s*(?:day|night)", text, re.I)
    duration = int(duration_match.group(1)) if duration_match else None
    
    # Breakout rooms
    breakout_match = re.search(r"(\d+)\s*breakout", text, re.I)
    breakout_rooms = int(breakout_match.group(1)) if breakout_match else None
    
    result = {}
    if lumens:
        result["projector_lumens_min"] = lumens
    if rooms:
        result["rooms_per_night"] = rooms
    if capacity:
        result["capacity"] = capacity
    if duration:
        result["duration_days"] = duration
    if breakout_rooms:
        result["breakout_rooms"] = breakout_rooms
    
    return result

def parse_accessibility(p: ParsedDoc) -> Dict[str, Any]:
    """Accessibility dokümanlarını ayrıştır"""
    text = p.full_text.lower()
    
    ada_keywords = ["ada", "americans with disabilities act", "accessibility", "wheelchair accessible"]
    ada_required = any(k in text for k in ada_keywords)
    
    return {
        "ada_compliance_required": ada_required,
        "rationale": "ADA compliance required for accessibility" if ada_required else None
    }

def parse_insurance(p: ParsedDoc) -> Dict[str, Any]:
    """Insurance dokümanlarını ayrıştır"""
    text = p.full_text.lower()
    
    # Insurance types
    general_liability = "general liability" in text
    workers_comp = "workers compensation" in text or "workers' compensation" in text
    auto_insurance = "automobile insurance" in text or "auto insurance" in text
    
    # Coverage amounts
    coverage_match = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|m)", text, re.I)
    coverage_amount = coverage_match.group(1) if coverage_match else None
    
    return {
        "general_liability_required": general_liability,
        "workers_comp_required": workers_comp,
        "auto_insurance_required": auto_insurance,
        "coverage_amount": coverage_amount,
        "rationale": "Insurance requirements specified in attachment" if any([general_liability, workers_comp, auto_insurance]) else None
    }
