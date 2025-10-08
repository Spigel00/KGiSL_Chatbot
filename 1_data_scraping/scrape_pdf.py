"""
PDF Scraper and Text Extractor for KGiSL Documents
Extracts text content from PDF files for chatbot training
"""

import PyPDF2
import requests
import json
import os
from urllib.parse import urlparse
import time
import logging
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFScraper:
    def __init__(self, output_dir="raw_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download_pdf(self, pdf_url, filename=None):
        """Download PDF from URL"""
        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            if not filename:
                parsed_url = urlparse(pdf_url)
                filename = os.path.basename(parsed_url.path)
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
            
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded PDF: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text content from PDF file"""
        try:
            text_content = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            text_content.append({
                                'page': page_num + 1,
                                'content': text.strip()
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {str(e)}")
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return None
    
    def process_pdf_url(self, pdf_url):
        """Download PDF from URL and extract text"""
        # Download PDF
        pdf_path = self.download_pdf(pdf_url)
        if not pdf_path:
            return None
        
        # Extract text
        text_content = self.extract_text_from_pdf(pdf_path)
        if not text_content:
            return None
        
        # Create JSON output
        output_data = {
            'source_url': pdf_url,
            'source_file': os.path.basename(pdf_path),
            'total_pages': len(text_content),
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages': text_content
        }
        
        # Save extracted text to JSON
        json_filename = os.path.basename(pdf_path).replace('.pdf', '_extracted.json')
        json_filepath = os.path.join(self.output_dir, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Extracted text saved: {json_filepath}")
        return output_data
    
    def process_local_pdf(self, pdf_path):
        """Process a local PDF file"""
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        text_content = self.extract_text_from_pdf(pdf_path)
        if not text_content:
            return None
        
        output_data = {
            'source_file': os.path.basename(pdf_path),
            'total_pages': len(text_content),
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages': text_content
        }
        
        # Save extracted text to JSON
        json_filename = os.path.basename(pdf_path).replace('.pdf', '_extracted.json')
        json_filepath = os.path.join(self.output_dir, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Extracted text saved: {json_filepath}")
        return output_data
    
    def process_multiple_pdfs(self, pdf_sources):
        """Process multiple PDFs (URLs or local paths)"""
        results = []
        
        for source in tqdm(pdf_sources, desc="Processing PDFs"):
            if source.startswith(('http://', 'https://')):
                result = self.process_pdf_url(source)
            else:
                result = self.process_local_pdf(source)
            
            if result:
                results.append(result)
            
            time.sleep(1)  # Be respectful to servers
        
        return results

def main():
    scraper = PDFScraper()
    
    # Example PDF sources (URLs or local paths)
    pdf_sources = [
        # Add PDF URLs or local file paths here
        # "https://example.com/sample.pdf",
        # "/path/to/local/file.pdf"
    ]
    
    if pdf_sources:
        scraper.process_multiple_pdfs(pdf_sources)
    else:
        logger.info("No PDF sources provided. Add URLs or file paths to process.")

if __name__ == "__main__":
    main()