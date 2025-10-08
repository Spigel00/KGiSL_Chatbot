"""
Text Chunking Module for KGiSL Chatbot
Splits cleaned text into smaller, manageable chunks for embeddings and retrieval
"""

import json
import os
import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, min_chunk_size: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Sentence boundary patterns
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\s*\n')
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = self.sentence_endings.split(text)
        return [sent.strip() for sent in sentences if sent.strip()]
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = self.paragraph_breaks.split(text)
        return [para.strip() for para in paragraphs if para.strip()]
    
    def create_overlapping_chunks(self, text: str) -> List[Dict]:
        """Create overlapping text chunks"""
        if len(text) <= self.chunk_size:
            return [{
                'text': text,
                'start_pos': 0,
                'end_pos': len(text),
                'chunk_id': 0
            }]
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            
            # Try to find a good breaking point (sentence or paragraph end)
            if end < len(text):
                # Look for sentence ending within the last 100 characters
                search_start = max(start, end - 100)
                search_text = text[search_start:end + 50]
                
                sentence_match = None
                for match in self.sentence_endings.finditer(search_text):
                    sentence_match = match
                
                if sentence_match:
                    end = search_start + sentence_match.end()
            
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    'text': chunk_text,
                    'start_pos': start,
                    'end_pos': end,
                    'chunk_id': chunk_id,
                    'word_count': len(chunk_text.split()),
                    'char_count': len(chunk_text)
                })
                chunk_id += 1
            
            # Calculate next start position with overlap
            start = max(start + 1, end - self.chunk_overlap)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def create_semantic_chunks(self, text: str) -> List[Dict]:
        """Create chunks based on semantic boundaries (paragraphs, sections)"""
        # First, try to split by paragraphs
        paragraphs = self.split_by_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for para in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                # Save current chunk
                if len(current_chunk.strip()) >= self.min_chunk_size:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'chunk_id': chunk_id,
                        'word_count': len(current_chunk.split()),
                        'char_count': len(current_chunk),
                        'type': 'semantic'
                    })
                    chunk_id += 1
                
                current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add final chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_id': chunk_id,
                'word_count': len(current_chunk.split()),
                'char_count': len(current_chunk),
                'type': 'semantic'
            })
        
        return chunks
    
    def chunk_document(self, document: Dict, method: str = 'overlapping') -> List[Dict]:
        """Chunk a document using specified method"""
        content = document.get('content', '')
        
        if not content:
            return []
        
        if method == 'overlapping':
            chunks = self.create_overlapping_chunks(content)
        elif method == 'semantic':
            chunks = self.create_semantic_chunks(content)
        else:
            raise ValueError(f"Unknown chunking method: {method}")
        
        # Add document metadata to each chunk
        for chunk in chunks:
            chunk.update({
                'source_url': document.get('url', ''),
                'source_file': document.get('source_file', ''),
                'title': document.get('title', ''),
                'scraped_at': document.get('scraped_at', ''),
                'total_chunks': len(chunks)
            })
        
        return chunks
    
    def chunk_pdf_document(self, document: Dict) -> List[Dict]:
        """Special handling for PDF documents with page structure"""
        if 'pages' not in document:
            return self.chunk_document(document)
        
        all_chunks = []
        chunk_id = 0
        
        for page_data in document['pages']:
            page_content = page_data.get('content', '')
            page_num = page_data.get('page', 0)
            
            if not page_content:
                continue
            
            # Create chunks for this page
            page_chunks = self.create_overlapping_chunks(page_content)
            
            for chunk in page_chunks:
                chunk.update({
                    'chunk_id': chunk_id,
                    'page_number': page_num,
                    'source_file': document.get('source_file', ''),
                    'source_url': document.get('source_url', ''),
                    'extracted_at': document.get('extracted_at', ''),
                    'total_pages': document.get('total_pages', 0)
                })
                all_chunks.append(chunk)
                chunk_id += 1
        
        return all_chunks
    
    def process_file(self, input_file: str, output_file: str, method: str = 'overlapping') -> int:
        """Process a single file and create chunks"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                document = json.load(f)
            
            # Determine if it's a PDF document
            if 'pages' in document:
                chunks = self.chunk_pdf_document(document)
            else:
                chunks = self.chunk_document(document, method)
            
            # Save chunks to JSONL format
            with open(output_file, 'w', encoding='utf-8') as f:
                for chunk in chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
            
            logger.info(f"Created {len(chunks)} chunks from {input_file}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")
            return 0
    
    def process_directory(self, input_dir: str, output_dir: str, method: str = 'overlapping') -> Tuple[int, int]:
        """Process all files in directory"""
        os.makedirs(output_dir, exist_ok=True)
        
        total_files = 0
        total_chunks = 0
        
        for filename in os.listdir(input_dir):
            if filename.endswith('.json'):
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(output_dir, f"chunks_{filename.replace('.json', '.jsonl')}")
                
                chunk_count = self.process_file(input_file, output_file, method)
                if chunk_count > 0:
                    total_files += 1
                    total_chunks += chunk_count
        
        logger.info(f"Processed {total_files} files, created {total_chunks} chunks")
        return total_files, total_chunks
    
    def get_chunk_statistics(self, chunks: List[Dict]) -> Dict:
        """Calculate statistics for chunks"""
        if not chunks:
            return {}
        
        word_counts = [chunk.get('word_count', 0) for chunk in chunks]
        char_counts = [chunk.get('char_count', 0) for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_words': sum(word_counts) / len(word_counts),
            'min_words': min(word_counts),
            'max_words': max(word_counts),
            'avg_chars': sum(char_counts) / len(char_counts),
            'min_chars': min(char_counts),
            'max_chars': max(char_counts)
        }

def main():
    """Example usage"""
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    
    input_directory = "2_data_processing/processed_data"
    output_directory = "2_data_processing/processed_data/chunks"
    
    if os.path.exists(input_directory):
        files, chunks = chunker.process_directory(input_directory, output_directory)
        print(f"Processed {files} files, created {chunks} chunks")
    else:
        print(f"Input directory {input_directory} not found")

if __name__ == "__main__":
    main()