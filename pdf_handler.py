"""
PDF Handler for Second Brain Food
==================================
Server-side PDF text extraction when browser capture fails.
"""

import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional
import requests

try:
    import pdfplumber
except ImportError:
    pdfplumber = None
    print("Warning: pdfplumber not installed. Run: py -m pip install pdfplumber")


def is_pdf_url(url: str) -> bool:
    """Check if URL points to a PDF"""
    parsed = urlparse(url.lower())
    path = parsed.path
    
    # Direct .pdf extension
    if path.endswith('.pdf'):
        return True
    
    # arXiv abstract pages -> convert to PDF
    if 'arxiv.org' in parsed.netloc and '/abs/' in path:
        return True
    
    # arXiv PDF links
    if 'arxiv.org' in parsed.netloc and '/pdf/' in path:
        return True
    
    return False


def get_pdf_url(url: str) -> str:
    """Convert abstract URLs to direct PDF URLs where possible"""
    # arXiv: /abs/1234.5678 -> /pdf/1234.5678.pdf
    if 'arxiv.org' in url and '/abs/' in url:
        return url.replace('/abs/', '/pdf/') + '.pdf'
    return url


def fetch_pdf_content(url: str) -> Optional[dict]:
    """
    Download and extract text from a PDF URL.
    
    Returns dict with: title, content, page_count
    Or None if extraction failed.
    """
    if pdfplumber is None:
        return None
    
    if not is_pdf_url(url):
        return None
    
    pdf_url = get_pdf_url(url)
    
    try:
        # Download PDF to temp file
        response = requests.get(
            pdf_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
            timeout=60
        )
        response.raise_for_status()
        
        # Verify it's actually a PDF
        if not response.content[:4] == b'%PDF':
            return None
        
        # Write to temp file and extract
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        try:
            text_parts = []
            title = None
            
            with pdfplumber.open(tmp_path) as pdf:
                page_count = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    
                    # Try to get title from first page
                    if i == 0 and page_text:
                        lines = page_text.strip().split('\n')
                        if lines:
                            # First substantial line is often title
                            for line in lines[:5]:
                                if len(line.strip()) > 10 and len(line.strip()) < 200:
                                    title = line.strip()
                                    break
            
            content = '\n\n'.join(text_parts)
            
            if len(content.strip()) < 100:
                return None
            
            return {
                "success": True,
                "content": content,
                "title": title,
                "page_count": page_count,
                "source_url": url,
                "pdf_url": pdf_url
            }
            
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
            
    except requests.RequestException as e:
        print(f"  PDF download failed: {e}")
        return None
    except Exception as e:
        print(f"  PDF extraction failed: {e}")
        return None


# Integration helper
def get_content(url: str) -> Optional[str]:
    """
    Drop-in helper: returns markdown-formatted content or None
    """
    result = fetch_pdf_content(url)
    if result:
        header = f"# {result['title'] or 'PDF Document'}\n\n"
        header += f"**Pages:** {result['page_count']}\n"
        header += f"**Source:** {url}\n\n---\n\n"
        return header + result['content']
    return None


# Test
if __name__ == "__main__":
    test_urls = [
        "https://arxiv.org/abs/1606.06565",
        "https://arxiv.org/pdf/1606.06565.pdf",
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = fetch_pdf_content(url)
        if result:
            print(f"  ✓ {result.get('title', 'No title')}")
            print(f"    {result['page_count']} pages, {len(result['content'])} chars")
        else:
            print(f"  ✗ Failed")
