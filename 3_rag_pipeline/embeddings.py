"""
Embeddings Generation Module for KGiSL Chatbot
Generates vector embeddings for text chunks using sentence transformers
"""

import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging
from tqdm import tqdm
import pickle

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "models"):
        """
        Initialize the embedding generator
        
        Args:
            model_name: Name of the sentence transformer model
            cache_dir: Directory to cache the model
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load the model
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts"""
        try:
            embeddings = self.model.encode(
                texts, 
                batch_size=batch_size,
                convert_to_tensor=False,
                show_progress_bar=True
            )
            return [emb.astype(np.float32) for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return [np.zeros(self.embedding_dim, dtype=np.float32) for _ in texts]
    
    def process_chunk_file(self, input_file: str, output_file: str, batch_size: int = 32) -> int:
        """Process a JSONL file of chunks and add embeddings"""
        try:
            chunks = []
            texts = []
            
            # Read all chunks
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        chunk = json.loads(line)
                        chunks.append(chunk)
                        texts.append(chunk.get('text', ''))
            
            if not texts:
                logger.warning(f"No texts found in {input_file}")
                return 0
            
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            
            # Generate embeddings in batches
            embeddings = self.generate_embeddings_batch(texts, batch_size)
            
            # Add embeddings to chunks and save
            processed_count = 0
            with open(output_file, 'w', encoding='utf-8') as f:
                for chunk, embedding in zip(chunks, embeddings):
                    # Add embedding to chunk metadata
                    if 'metadata' not in chunk:
                        chunk['metadata'] = {}
                    
                    chunk['metadata']['embedding_model'] = self.model_name
                    chunk['metadata']['embedding_dim'] = self.embedding_dim
                    chunk['embedding'] = embedding.tolist()  # Convert to list for JSON serialization
                    
                    f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
                    processed_count += 1
            
            logger.info(f"Generated embeddings for {processed_count} chunks")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")
            return 0
    
    def process_directory(self, input_dir: str, output_dir: str, batch_size: int = 32) -> int:
        """Process all chunk files in directory and generate embeddings"""
        os.makedirs(output_dir, exist_ok=True)
        
        total_processed = 0
        
        for filename in os.listdir(input_dir):
            if filename.endswith('.jsonl'):
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(output_dir, f"embedded_{filename}")
                
                count = self.process_chunk_file(input_file, output_file, batch_size)
                total_processed += count
        
        logger.info(f"Total chunks with embeddings: {total_processed}")
        return total_processed
    
    def create_embedding_index(self, embedded_chunks_dir: str, index_file: str) -> Dict:
        """Create an index of all embeddings for fast retrieval"""
        try:
            all_embeddings = []
            all_chunks = []
            chunk_ids = []
            
            # Collect all embeddings and chunks
            for filename in os.listdir(embedded_chunks_dir):
                if filename.endswith('.jsonl') and filename.startswith('embedded_'):
                    filepath = os.path.join(embedded_chunks_dir, filename)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                chunk = json.loads(line)
                                if 'embedding' in chunk:
                                    all_embeddings.append(np.array(chunk['embedding']))
                                    all_chunks.append(chunk)
                                    chunk_ids.append(chunk.get('metadata', {}).get('chunk_id', ''))
            
            if not all_embeddings:
                logger.warning("No embeddings found to index")
                return {}
            
            # Create numpy array of embeddings
            embeddings_matrix = np.vstack(all_embeddings)
            
            # Create index data structure
            index_data = {
                'embeddings': embeddings_matrix,
                'chunks': all_chunks,
                'chunk_ids': chunk_ids,
                'embedding_dim': self.embedding_dim,
                'model_name': self.model_name,
                'total_chunks': len(all_chunks)
            }
            
            # Save to pickle file
            with open(index_file, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.info(f"Created embedding index with {len(all_chunks)} chunks")
            return {
                'total_chunks': len(all_chunks),
                'embedding_dim': self.embedding_dim,
                'model_name': self.model_name,
                'index_file': index_file
            }
            
        except Exception as e:
            logger.error(f"Error creating embedding index: {str(e)}")
            return {}
    
    def search_similar_chunks(self, query: str, index_file: str, top_k: int = 5) -> List[Dict]:
        """Search for similar chunks using cosine similarity"""
        try:
            # Load index
            with open(index_file, 'rb') as f:
                index_data = pickle.load(f)
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Calculate cosine similarities
            embeddings_matrix = index_data['embeddings']
            
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            embeddings_norm = embeddings_matrix / np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
            
            # Calculate similarities
            similarities = np.dot(embeddings_norm, query_norm)
            
            # Get top-k most similar chunks
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                chunk = index_data['chunks'][idx].copy()
                chunk['similarity_score'] = float(similarities[idx])
                results.append(chunk)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            return []

def main():
    """Example usage"""
    generator = EmbeddingGenerator()
    
    input_directory = "../2_data_processing/processed_data/enhanced_chunks"
    output_directory = "embedded_chunks"
    index_file = "embedding_index.pkl"
    
    if os.path.exists(input_directory):
        # Generate embeddings
        count = generator.process_directory(input_directory, output_directory)
        print(f"Generated embeddings for {count} chunks")
        
        # Create index
        if count > 0:
            index_info = generator.create_embedding_index(output_directory, index_file)
            print(f"Created index: {index_info}")
            
            # Test search
            if index_info:
                test_query = "What services does KGiSL provide?"
                results = generator.search_similar_chunks(test_query, index_file, top_k=3)
                print(f"\nTop 3 results for '{test_query}':")
                for i, result in enumerate(results, 1):
                    print(f"{i}. Score: {result['similarity_score']:.3f}")
                    print(f"   Text: {result['text'][:100]}...")
    else:
        print(f"Input directory {input_directory} not found")

if __name__ == "__main__":
    main()