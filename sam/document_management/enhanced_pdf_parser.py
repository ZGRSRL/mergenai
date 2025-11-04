#!/usr/bin/env python3
"""
Enhanced PDF Parser with OCR fallback for image-only PDFs
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class EnhancedPDFParser:
    """Enhanced PDF parser with OCR fallback"""
    
    def __init__(self):
        self.ocr_available = self._check_ocr_availability()
    
    def _check_ocr_availability(self) -> bool:
        """Check if OCR dependencies are available"""
        try:
            import pytesseract
            from pdf2image import convert_from_path
            return True
        except ImportError:
            logger.warning("OCR dependencies not available. Install: pip install pytesseract pdf2image")
            return False
    
    def extract_text_with_pypdf(self, pdf_path: str) -> str:
        """Extract text using PyPDF (fast method)"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"PyPDF extraction failed for {pdf_path}: {e}")
            return ""
    
    def extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR (fallback for image-only PDFs)"""
        if not self.ocr_available:
            logger.warning("OCR not available, cannot process image-only PDF")
            return ""
        
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            logger.info(f"Starting OCR extraction for {pdf_path}")
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=200)
            
            ocr_text = []
            for i, page in enumerate(pages):
                logger.info(f"Processing page {i+1}/{len(pages)} with OCR")
                page_text = pytesseract.image_to_string(page)
                ocr_text.append(page_text)
            
            full_text = "\n".join(ocr_text)
            logger.info(f"OCR extraction completed. Text length: {len(full_text)}")
            
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {pdf_path}: {e}")
            return ""
    
    def extract_text_enhanced(self, pdf_path: str) -> Dict[str, Any]:
        """
        Enhanced text extraction with fallback methods
        
        Returns:
            Dict with text, method used, and metadata
        """
        result = {
            "pdf_path": pdf_path,
            "text": "",
            "method": "none",
            "text_length": 0,
            "pages_processed": 0,
            "ocr_used": False,
            "success": False,
            "error": None
        }
        
        try:
            # Method 1: Try PyPDF first (fast)
            logger.info(f"Extracting text from {pdf_path} using PyPDF")
            text = self.extract_text_with_pypdf(pdf_path)
            
            if text and len(text.strip()) >= 50:
                # PyPDF worked well
                result["text"] = text
                result["method"] = "pypdf"
                result["text_length"] = len(text)
                result["success"] = True
                logger.info(f"PyPDF extraction successful. Text length: {len(text)}")
                
            elif self.ocr_available:
                # PyPDF didn't work well, try OCR
                logger.info(f"PyPDF extracted minimal text ({len(text)} chars), trying OCR")
                ocr_text = self.extract_text_with_ocr(pdf_path)
                
                if ocr_text and len(ocr_text.strip()) >= 50:
                    result["text"] = ocr_text
                    result["method"] = "ocr"
                    result["text_length"] = len(ocr_text)
                    result["ocr_used"] = True
                    result["success"] = True
                    logger.info(f"OCR extraction successful. Text length: {len(ocr_text)}")
                else:
                    result["error"] = "PDF_EMPTY_AFTER_OCR"
                    logger.warning(f"OCR extraction failed or produced minimal text: {len(ocr_text)} chars")
            else:
                result["error"] = "PDF_EMPTY_NO_OCR"
                logger.warning(f"PyPDF extracted minimal text ({len(text)} chars) and OCR not available")
                
        except Exception as e:
            result["error"] = f"EXTRACTION_ERROR: {str(e)}"
            logger.error(f"Text extraction failed for {pdf_path}: {e}")
        
        return result

class EnhancedRAGProcessor:
    """Enhanced RAG processor with empty corpus protection"""
    
    def __init__(self):
        self.min_chunk_length = 20
        self.min_total_text = 100
    
    def process_opportunity_text(self, opportunity_id: str, text_data: list) -> Dict[str, Any]:
        """
        Process opportunity text with empty corpus protection
        
        Args:
            opportunity_id: The opportunity ID
            text_data: List of text extraction results from attachments
            
        Returns:
            Dict with processing results and corpus status
        """
        result = {
            "opportunity_id": opportunity_id,
            "total_text_length": 0,
            "chunks_created": 0,
            "corpus_status": "empty",
            "analysis_ready": False,
            "warnings": [],
            "chunks": []
        }
        
        try:
            # Combine all text
            all_text = ""
            for text_result in text_data:
                if text_result.get("success") and text_result.get("text"):
                    all_text += text_result["text"] + "\n\n"
            
            result["total_text_length"] = len(all_text)
            
            if len(all_text.strip()) < self.min_total_text:
                result["corpus_status"] = "empty"
                result["warnings"].append(f"Total text length ({len(all_text)}) below minimum ({self.min_total_text})")
                logger.warning(f"Empty corpus for {opportunity_id}: {len(all_text)} chars")
                return result
            
            # Create chunks
            chunks = self._create_chunks(all_text)
            result["chunks"] = chunks
            result["chunks_created"] = len(chunks)
            
            if len(chunks) == 0:
                result["corpus_status"] = "empty"
                result["warnings"].append("No valid chunks created from text")
                logger.warning(f"No chunks created for {opportunity_id}")
            else:
                result["corpus_status"] = "ready"
                result["analysis_ready"] = True
                logger.info(f"Corpus ready for {opportunity_id}: {len(chunks)} chunks")
            
        except Exception as e:
            result["corpus_status"] = "error"
            result["warnings"].append(f"Processing error: {str(e)}")
            logger.error(f"RAG processing failed for {opportunity_id}: {e}")
        
        return result
    
    def _create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Create text chunks for RAG processing"""
        if not text.strip():
            return []
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.strip()) >= self.min_chunk_length:
                chunks.append({
                    "text": chunk.strip(),
                    "start_word": i,
                    "end_word": min(i + chunk_size, len(words)),
                    "length": len(chunk)
                })
        
        return chunks

def test_enhanced_parsing():
    """Test the enhanced parsing functionality"""
    parser = EnhancedPDFParser()
    rag = EnhancedRAGProcessor()
    
    print("Enhanced PDF Parser Test")
    print("=" * 40)
    print(f"OCR Available: {parser.ocr_available}")
    print()
    
    # Test with a sample text (simulating PDF content)
    sample_text = "This is a sample document for testing the enhanced parser functionality."
    
    # Simulate text extraction result
    text_result = {
        "pdf_path": "sample.pdf",
        "text": sample_text,
        "method": "pypdf",
        "text_length": len(sample_text),
        "success": True
    }
    
    # Test RAG processing
    rag_result = rag.process_opportunity_text("TEST-001", [text_result])
    
    print("RAG Processing Result:")
    print(f"  Opportunity ID: {rag_result['opportunity_id']}")
    print(f"  Total Text Length: {rag_result['total_text_length']}")
    print(f"  Chunks Created: {rag_result['chunks_created']}")
    print(f"  Corpus Status: {rag_result['corpus_status']}")
    print(f"  Analysis Ready: {rag_result['analysis_ready']}")
    print(f"  Warnings: {rag_result['warnings']}")
    
    if rag_result['chunks']:
        print(f"  First Chunk: {rag_result['chunks'][0]['text'][:100]}...")

if __name__ == "__main__":
    test_enhanced_parsing()
