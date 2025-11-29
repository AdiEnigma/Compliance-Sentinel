"""
Document parsers for PDF, DOCX, and OCR for images.
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pypdf not available, PDF parsing disabled")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, DOCX parsing disabled")

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("easyocr not available, OCR disabled")


@dataclass
class TextBlock:
    """Represents a block of text with metadata."""
    page: int
    block_id: str
    text: str
    bbox: Optional[Dict[str, float]] = None
    block_type: str = "paragraph"  # paragraph, header, footer, table


def parse_pdf(file_path: str) -> List[TextBlock]:
    """Parse PDF file and extract text blocks."""
    if not PDF_AVAILABLE:
        raise RuntimeError("PDF parsing not available. Install pypdf.")
    
    blocks = []
    reader = PdfReader(file_path)
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text.strip():
            # Split by paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for idx, para in enumerate(paragraphs):
                blocks.append(TextBlock(
                    page=page_num,
                    block_id=f"page_{page_num}_block_{idx}",
                    text=para,
                    block_type="paragraph"
                ))
    
    return blocks


def parse_docx(file_path: str) -> List[TextBlock]:
    """Parse DOCX file and extract text blocks."""
    if not DOCX_AVAILABLE:
        raise RuntimeError("DOCX parsing not available. Install python-docx.")
    
    blocks = []
    doc = Document(file_path)
    
    for para_idx, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text:
            block_type = "header" if paragraph.style.name.startswith("Heading") else "paragraph"
            blocks.append(TextBlock(
                page=1,  # DOCX doesn't have explicit pages
                block_id=f"para_{para_idx}",
                text=text,
                block_type=block_type
            ))
    
    return blocks


def parse_image_ocr(file_path: str, languages: List[str] = ['en']) -> List[TextBlock]:
    """Parse image using OCR."""
    if not OCR_AVAILABLE:
        raise RuntimeError("OCR not available. Install easyocr.")
    
    reader = easyocr.Reader(languages)
    results = reader.readtext(file_path)
    
    blocks = []
    for idx, (bbox, text, confidence) in enumerate(results):
        if confidence > 0.5:  # Filter low-confidence detections
            blocks.append(TextBlock(
                page=1,
                block_id=f"ocr_block_{idx}",
                text=text,
                bbox={
                    "x1": bbox[0][0],
                    "y1": bbox[0][1],
                    "x2": bbox[2][0],
                    "y2": bbox[2][1]
                },
                block_type="paragraph"
            ))
    
    return blocks


def parse_document(file_path: str) -> Dict[str, Any]:
    """
    Parse a document (PDF, DOCX, or image) and return structured text blocks.
    
    Returns:
        {
            "text_blocks": [TextBlock],
            "metadata": {
                "file_type": str,
                "total_pages": int,
                "headers": List[str],
                "footers": List[str],
                "tables": List[Dict]
            },
            "full_text": str
        }
    """
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        blocks = parse_pdf(file_path)
        file_type = "pdf"
    elif file_ext in ['.docx', '.doc']:
        blocks = parse_docx(file_path)
        file_type = "docx"
    elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
        blocks = parse_image_ocr(file_path)
        file_type = "image"
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    # Extract headers and footers (heuristic)
    headers = [b.text for b in blocks if b.block_type == "header"][:5]
    footers = []
    
    # Combine all text
    full_text = "\n\n".join([b.text for b in blocks])
    
    return {
        "text_blocks": blocks,
        "metadata": {
            "file_type": file_type,
            "total_pages": max([b.page for b in blocks], default=1),
            "headers": headers,
            "footers": footers,
            "tables": []  # TODO: implement table extraction
        },
        "full_text": full_text
    }

