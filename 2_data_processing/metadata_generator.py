"""
Metadata Generator for KGiSL Chatbot
Adds JSON metadata to each chunk for better retrieval and context
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any
import logging
import re

logger = logging.getLogger(__name__)

class MetadataGenerator:
    def __init__(self):
        self.content_categories = {
            'about': ['about', 'company', 'history', 'mission', 'vision', 'values'],
            'services': ['service', 'product', 'solution', 'offering', 'technology'],
            'careers': ['career', 'job', 'position', 'employment', 'hiring', 'opportunity'],
            'contact': ['contact', 'address', 'phone', 'email', 'location', 'office'],
            'technical': ['technical', 'technology', 'development', 'software', 'programming'],
            'education': ['training', 'course', 'education', 'learning', 'curriculum']
        }
        
        # Keywords for importance scoring
        self.important_keywords = [
            'kgisl', 'coimbatore', 'software', 'development', 'technology',
            'training', 'education', 'career', 'service', 'solution'
        ]
    
    def generate_chunk_id(self, chunk_text: str, source: str) -> str:
        """Generate unique ID for chunk"""
        content_hash = hashlib.md5(chunk_text.encode('utf-8')).hexdigest()[:8]
        source_hash = hashlib.md5(source.encode('utf-8')).hexdigest()[:4]
        return f"{source_hash}_{content_hash}"
    
    def categorize_content(self, text: str) -> List[str]:
        """Categorize content based on keywords"""
        text_lower = text.lower()
        categories = []
        
        for category, keywords in self.content_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        return categories if categories else ['general']
    
    def calculate_importance_score(self, text: str) -> float:
        """Calculate importance score based on keywords and content quality"""
        text_lower = text.lower()
        score = 0.0
        
        # Keyword-based scoring
        for keyword in self.important_keywords:
            count = text_lower.count(keyword)
            score += count * 0.1
        
        # Content quality indicators
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        
        # Longer, well-structured content gets higher score
        if words > 50:
            score += 0.2
        if sentences > 3:
            score += 0.1
        
        # Penalize very short or very long chunks
        if words < 20:
            score -= 0.3
        elif words > 800:
            score -= 0.1
        
        return min(max(score, 0.0), 1.0)  # Normalize to 0-1 range
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities like emails, phones, URLs (simple regex-based)"""
        entities = {
            'emails': [],
            'phones': [],
            'urls': [],
            'locations': []
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Phone pattern (Indian format)
        phone_pattern = r'(\+91\s?)?[6-9]\d{9}|\d{3}-\d{3}-\d{4}|\(\d{3}\)\s?\d{3}-\d{4}'
        entities['phones'] = re.findall(phone_pattern, text)
        
        # URL pattern
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Common location indicators
        location_keywords = ['coimbatore', 'tamil nadu', 'india', 'office', 'campus', 'address']
        for keyword in location_keywords:
            if keyword.lower() in text.lower():
                entities['locations'].append(keyword)
        
        # Remove empty lists
        return {k: v for k, v in entities.items() if v}
    
    def generate_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction - could be improved with NLP libraries
        text_lower = text.lower()
        
        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        
        # Filter stopwords and count frequency
        word_freq = {}
        for word in words:
            if word not in stopwords and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def add_metadata_to_chunk(self, chunk: Dict) -> Dict:
        """Add comprehensive metadata to a chunk"""
        text = chunk.get('text', '')
        source = chunk.get('source_file', chunk.get('source_url', 'unknown'))
        
        # Generate metadata
        metadata = {
            'chunk_id': self.generate_chunk_id(text, source),
            'categories': self.categorize_content(text),
            'importance_score': self.calculate_importance_score(text),
            'keywords': self.generate_keywords(text),
            'entities': self.extract_entities(text),
            'processed_at': datetime.now().isoformat(),
            'language': 'en',  # Assuming English content
            'content_type': 'text'
        }
        
        # Add text statistics
        words = text.split()
        sentences = len(re.findall(r'[.!?]+', text))
        
        metadata['statistics'] = {
            'word_count': len(words),
            'char_count': len(text),
            'sentence_count': sentences,
            'avg_words_per_sentence': len(words) / max(sentences, 1)
        }
        
        # Merge with existing chunk data
        enhanced_chunk = chunk.copy()
        enhanced_chunk['metadata'] = metadata
        
        return enhanced_chunk
    
    def process_chunks_file(self, input_file: str, output_file: str) -> int:
        """Process a JSONL file of chunks and add metadata"""
        try:
            processed_count = 0
            
            with open(input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8') as outfile:
                
                for line in infile:
                    if line.strip():
                        chunk = json.loads(line)
                        enhanced_chunk = self.add_metadata_to_chunk(chunk)
                        outfile.write(json.dumps(enhanced_chunk, ensure_ascii=False) + '\n')
                        processed_count += 1
            
            logger.info(f"Added metadata to {processed_count} chunks in {output_file}")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")
            return 0
    
    def process_directory(self, input_dir: str, output_dir: str) -> int:
        """Process all chunk files in directory"""
        os.makedirs(output_dir, exist_ok=True)
        
        total_processed = 0
        
        for filename in os.listdir(input_dir):
            if filename.endswith('.jsonl') and filename.startswith('chunks_'):
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(output_dir, f"enhanced_{filename}")
                
                count = self.process_chunks_file(input_file, output_file)
                total_processed += count
        
        logger.info(f"Total chunks processed: {total_processed}")
        return total_processed
    
    def generate_collection_metadata(self, chunks_dir: str) -> Dict:
        """Generate metadata for the entire collection"""
        collection_stats = {
            'total_chunks': 0,
            'categories': {},
            'total_words': 0,
            'avg_importance_score': 0.0,
            'sources': set(),
            'created_at': datetime.now().isoformat()
        }
        
        importance_scores = []
        
        for filename in os.listdir(chunks_dir):
            if filename.endswith('.jsonl') and filename.startswith('enhanced_'):
                filepath = os.path.join(chunks_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            chunk = json.loads(line)
                            collection_stats['total_chunks'] += 1
                            
                            # Update statistics
                            metadata = chunk.get('metadata', {})
                            stats = metadata.get('statistics', {})
                            
                            collection_stats['total_words'] += stats.get('word_count', 0)
                            importance_scores.append(metadata.get('importance_score', 0.0))
                            
                            # Count categories
                            for category in metadata.get('categories', []):
                                collection_stats['categories'][category] = collection_stats['categories'].get(category, 0) + 1
                            
                            # Track sources
                            source = chunk.get('source_file', chunk.get('source_url', ''))
                            if source:
                                collection_stats['sources'].add(source)
        
        # Convert sources set to list
        collection_stats['sources'] = list(collection_stats['sources'])
        
        # Calculate averages
        if importance_scores:
            collection_stats['avg_importance_score'] = sum(importance_scores) / len(importance_scores)
        
        if collection_stats['total_chunks'] > 0:
            collection_stats['avg_words_per_chunk'] = collection_stats['total_words'] / collection_stats['total_chunks']
        
        return collection_stats

def main():
    """Example usage"""
    generator = MetadataGenerator()
    
    input_directory = "processed_data/chunks"
    output_directory = "processed_data/enhanced_chunks"
    
    if os.path.exists(input_directory):
        count = generator.process_directory(input_directory, output_directory)
        print(f"Enhanced {count} chunks with metadata")
        
        # Generate collection metadata
        collection_meta = generator.generate_collection_metadata(output_directory)
        
        # Save collection metadata
        with open(os.path.join(output_directory, 'collection_metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(collection_meta, f, indent=2, ensure_ascii=False)
        
        print(f"Collection stats: {collection_meta['total_chunks']} chunks from {len(collection_meta['sources'])} sources")
    else:
        print(f"Input directory {input_directory} not found")

if __name__ == "__main__":
    main()