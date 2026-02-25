import fitz
import re
from typing import List, Dict, Tuple
from pathlib import Path


class PDFProcessor:
    """Handles PDF parsing and text extraction with section detection."""
    
    def __init__(self):
        self.section_patterns = [
            r'^(\d+\.?\s+[A-Z][A-Za-z\s]+)$',
            r'^([A-Z][A-Z\s]+)$',
            r'^(Abstract|Introduction|Conclusion|References|Methodology|Results|Discussion)',
        ]
    
    def extract_text_with_metadata(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF with page numbers and section information.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing text, page number, and section
        """
        pages_data = []
        current_section = "Unknown"
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("blocks")
                
                page_text = ""
                for block in blocks:
                    text = block[4].strip()
                    if not text:
                        continue
                    
                    detected_section = self._detect_section(text)
                    if detected_section:
                        current_section = detected_section
                    
                    page_text += text + "\n"
                
                if page_text.strip():
                    pages_data.append({
                        "text": page_text.strip(),
                        "page": page_num + 1,
                        "section": current_section
                    })
            
            doc.close()
            
        except Exception as e:
            raise ValueError(f"Failed to process PDF: {str(e)}")
        
        return pages_data
    
    def _detect_section(self, text: str) -> str | None:
        """
        Detect if a line of text is a section heading.
        
        Args:
            text: Line of text to check
            
        Returns:
            Section name if detected, None otherwise
        """
        text = text.strip()
        
        if len(text) > 100 or len(text) < 3:
            return None
        
        for pattern in self.section_patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return text.title() if text.isupper() else text
        
        return None
    
    def validate_pdf(self, file_path: str, max_size_mb: int = 20) -> Tuple[bool, str]:
        """
        Validate PDF file size and format.
        
        Args:
            file_path: Path to the PDF file
            max_size_mb: Maximum allowed file size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)
        
        if not path.exists():
            return False, "File does not exist"
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        
        try:
            doc = fitz.open(file_path)
            doc.close()
        except Exception as e:
            return False, f"Invalid or corrupted PDF: {str(e)}"
        
        return True, ""
