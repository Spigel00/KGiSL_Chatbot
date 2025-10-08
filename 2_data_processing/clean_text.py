"""
Text Cleaning Module for KGiSL Chatbot
Removes HTML tags, normalizes text, and cleans scraped content
"""

import re
import json
import os
from bs4 import BeautifulSoup
import html
import unicodedata
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    def __init__(self):
        # Common patterns to remove or clean
        self.html_pattern = re.compile(r'<[^>]+>')
        self.extra_whitespace = re.compile(r'\s+')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Common stopwords and noise
        self.noise_patterns = [
            re.compile(r'\b(click here|read more|learn more|contact us|home|about|services)\b', re.IGNORECASE),
            re.compile(r'\b(privacy policy|terms of service|cookie policy)\b', re.IGNORECASE),
            re.compile(r'\b(copyright|all rights reserved|\©|\®)\b', re.IGNORECASE)
        ]
    
    def remove_html_tags(self, text: str) -> str:
        """Remove HTML tags and decode HTML entities"""
        # First, use BeautifulSoup for better HTML parsing
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove any remaining HTML tags
        text = self.html_pattern.sub('', text)
        
        return text
    
    def normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        # Normalize unicode to NFC form
        text = unicodedata.normalize('NFC', text)
        
        # Replace common unicode characters
        replacements = {
            '\u2019': "'",  # Right single quotation mark
            '\u2018': "'",  # Left single quotation mark
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2026': '...',  # Horizontal ellipsis
            '\u00a0': ' ',  # Non-breaking space
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def clean_whitespace(self, text: str) -> str:
        """Clean and normalize whitespace"""
        # Replace multiple whitespaces with single space
        text = self.extra_whitespace.sub(' ', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines and join
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    def remove_urls_and_emails(self, text: str) -> str:
        """Remove URLs and email addresses"""
        text = self.url_pattern.sub('', text)
        text = self.email_pattern.sub('', text)
        return text
    
    def remove_noise(self, text: str) -> str:
        """Remove common noise patterns"""
        for pattern in self.noise_patterns:
            text = pattern.sub('', text)
        return text
    
    def clean_text(self, text: str, remove_urls: bool = True, remove_noise: bool = True) -> str:
        """Main text cleaning function"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = self.remove_html_tags(text)
        
        # Normalize unicode
        text = self.normalize_unicode(text)
        
        # Remove URLs and emails if specified
        if remove_urls:
            text = self.remove_urls_and_emails(text)
        
        # Remove noise patterns if specified
        if remove_noise:
            text = self.remove_noise(text)
        
        # Clean whitespace
        text = self.clean_whitespace(text)
        
        return text.strip()
    
    def clean_json_data(self, data: Dict) -> Dict:
        """Clean text content in JSON data structure"""
        cleaned_data = data.copy()
        
        # Clean main content
        if 'content' in cleaned_data:
            cleaned_data['content'] = self.clean_text(cleaned_data['content'])
        
        # Clean title
        if 'title' in cleaned_data:
            cleaned_data['title'] = self.clean_text(cleaned_data['title'])
        
        # Clean pages (for PDF data)
        if 'pages' in cleaned_data:
            for page in cleaned_data['pages']:
                if 'content' in page:
                    page['content'] = self.clean_text(page['content'])
        
        # Add cleaning metadata
        cleaned_data['cleaned'] = True
        cleaned_data['original_length'] = len(data.get('content', ''))
        cleaned_data['cleaned_length'] = len(cleaned_data.get('content', ''))
        
        return cleaned_data
    
    def process_file(self, input_file: str, output_file: str) -> bool:
        """Process a single JSON file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cleaned_data = self.clean_json_data(data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cleaned {input_file} -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")
            return False
    
    def process_directory(self, input_dir: str, output_dir: str) -> int:
        """Process all JSON files in a directory"""
        os.makedirs(output_dir, exist_ok=True)
        
        processed_count = 0
        
        for filename in os.listdir(input_dir):
            if filename.endswith('.json'):
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(output_dir, f"cleaned_{filename}")
                
                if self.process_file(input_file, output_file):
                    processed_count += 1
        
        logger.info(f"Processed {processed_count} files")
        return processed_count

def main():
    """Example usage"""
    cleaner = TextCleaner()
    
    # Process scraped data
    input_directory = "1_data_scraping/raw_data"
    output_directory = "2_data_processing/processed_data"
    
    if os.path.exists(input_directory):
        count = cleaner.process_directory(input_directory, output_directory)
        print(f"Cleaned {count} files")
    else:
        print(f"Input directory {input_directory} not found")

if __name__ == "__main__":
    main()