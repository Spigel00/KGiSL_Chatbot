"""
Unit tests for the data scraping modules
Tests HTML scraper, PDF scraper, and crawler utilities
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, Mock, MagicMock
import sys

# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from bs4 import BeautifulSoup

class TestHTMLScraper(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.Session.get')
    def test_get_page_content_success(self, mock_get):
        """Test successful page content extraction"""
        # Mock HTML content
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Heading</h1>
                <p>Test paragraph content.</p>
                <script>console.log('test');</script>
                <style>body { margin: 0; }</style>
            </body>
        </html>
        """
        
        # Mock response
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Import here to avoid issues with missing modules during test discovery
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from scrape_html import HTMLScraper
        
        scraper = HTMLScraper(output_dir=self.temp_dir)
        result = scraper.get_page_content('https://test.com')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['url'], 'https://test.com')
        self.assertEqual(result['title'], 'Test Page')
        self.assertIn('Test Heading', result['content'])
        self.assertIn('Test paragraph content', result['content'])
        # Script and style content should be removed
        self.assertNotIn('console.log', result['content'])
        self.assertNotIn('margin: 0', result['content'])
    
    @patch('requests.Session.get')
    def test_get_page_content_failure(self, mock_get):
        """Test handling of HTTP errors"""
        # Mock HTTP error
        mock_get.side_effect = Exception("Connection error")
        
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from scrape_html import HTMLScraper
        
        scraper = HTMLScraper(output_dir=self.temp_dir)
        result = scraper.get_page_content('https://invalid-url.com')
        
        # Should return None on error
        self.assertIsNone(result)
    
    def test_scrape_page_creates_file(self):
        """Test that scraping creates the expected file"""
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from scrape_html import HTMLScraper
        
        with patch.object(HTMLScraper, 'get_page_content') as mock_get_content:
            mock_get_content.return_value = {
                'url': 'https://test.com/page',
                'title': 'Test Page',
                'content': 'Test content',
                'scraped_at': '2024-01-01 12:00:00'
            }
            
            scraper = HTMLScraper(output_dir=self.temp_dir)
            scraper.scrape_page('https://test.com/page')
            
            # Check if file was created
            files = os.listdir(self.temp_dir)
            self.assertEqual(len(files), 1)
            
            # Check file content
            with open(os.path.join(self.temp_dir, files[0]), 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertEqual(data['url'], 'https://test.com/page')
                self.assertEqual(data['title'], 'Test Page')

class TestCrawlerUtils(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://test.com"
    
    def test_is_valid_url(self):
        """Test URL validation logic"""
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from crawler_utils import CrawlerUtils
        
        crawler = CrawlerUtils(self.base_url)
        
        # Valid URLs
        self.assertTrue(crawler.is_valid_url("https://test.com/page"))
        self.assertTrue(crawler.is_valid_url("https://test.com/about"))
        
        # Invalid URLs (different domain)
        self.assertFalse(crawler.is_valid_url("https://other.com/page"))
        
        # Invalid URLs (non-content)
        self.assertFalse(crawler.is_valid_url("https://test.com/image.jpg"))
        self.assertFalse(crawler.is_valid_url("https://test.com/style.css"))
        self.assertFalse(crawler.is_valid_url("https://test.com/script.js"))
    
    @patch('requests.Session.get')
    def test_extract_links_from_page(self, mock_get):
        """Test link extraction from HTML page"""
        html_content = """
        <html>
            <body>
                <a href="/about">About</a>
                <a href="https://test.com/services">Services</a>
                <a href="https://external.com/page">External</a>
                <a href="image.jpg">Image</a>
                <a href="#section">Fragment</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from crawler_utils import CrawlerUtils
        
        crawler = CrawlerUtils(self.base_url)
        links = crawler.extract_links_from_page("https://test.com")
        
        # Should extract valid internal links only
        self.assertIn("https://test.com/about", links)
        self.assertIn("https://test.com/services", links)
        # Should not include external links, images, or fragments
        self.assertNotIn("https://external.com/page", links)
        self.assertNotIn("https://test.com/image.jpg", links)

class TestPDFScraper(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_text_from_nonexistent_pdf(self):
        """Test handling of non-existent PDF files"""
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from scrape_pdf import PDFScraper
        
        scraper = PDFScraper(output_dir=self.temp_dir)
        result = scraper.extract_text_from_pdf("nonexistent.pdf")
        
        # Should return None for non-existent files
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_download_pdf_success(self, mock_get):
        """Test successful PDF download"""
        # Mock PDF content
        mock_response = Mock()
        mock_response.content = b"Mock PDF content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from scrape_pdf import PDFScraper
        
        scraper = PDFScraper(output_dir=self.temp_dir)
        result = scraper.download_pdf("https://test.com/document.pdf")
        
        # Check if file was downloaded
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Check file content
        with open(result, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b"Mock PDF content")
    
    @patch('requests.get')
    def test_download_pdf_failure(self, mock_get):
        """Test handling of download failures"""
        mock_get.side_effect = Exception("Download failed")
        
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from scrape_pdf import PDFScraper
        
        scraper = PDFScraper(output_dir=self.temp_dir)
        result = scraper.download_pdf("https://invalid-url.com/document.pdf")
        
        # Should return None on failure
        self.assertIsNone(result)

class TestDataScrapingIntegration(unittest.TestCase):
    """Integration tests for data scraping modules"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scraper_file_naming(self):
        """Test that scrapers create files with expected naming convention"""
        import sys
        import os
        scraping_path = os.path.join(os.path.dirname(__file__), '..', '1_data_scraping')
        sys.path.insert(0, scraping_path)
        from scrape_html import HTMLScraper
        
        with patch.object(HTMLScraper, 'get_page_content') as mock_get_content:
            mock_get_content.return_value = {
                'url': 'https://test.com/about/company',
                'title': 'About Us',
                'content': 'Company information',
                'scraped_at': '2024-01-01 12:00:00'
            }
            
            scraper = HTMLScraper(output_dir=self.temp_dir)
            scraper.scrape_page('https://test.com/about/company')
            
            # Check file naming
            files = os.listdir(self.temp_dir)
            self.assertEqual(len(files), 1)
            filename = files[0]
            
            # Should contain domain and path information
            self.assertIn('test.com', filename)
            self.assertTrue(filename.endswith('.json'))

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)