"""
Vector Database Integration for KGiSL Chatbot
Supports FAISS and Chroma for efficient similarity search
"""

import json
import os
import numpy as np
from typing import List, Dict, Optional, Union
import logging
import pickle
from pathlib import Path

# Vector database imports
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available. Install with: pip install faiss-cpu")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB not available. Install with: pip install chromadb")

logger = logging.getLogger(__name__)

class FAISSVectorDB:
    """FAISS-based vector database for fast similarity search"""
    
    def __init__(self, embedding_dim: int, index_type: str = "IVF"):
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is not available. Install with: pip install faiss-cpu")
        
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.chunks = []
        self.chunk_ids = []
        
    def create_index(self, embeddings: np.ndarray, chunks: List[Dict]):
        """Create FAISS index from embeddings"""
        try:
            n_vectors = embeddings.shape[0]
            
            if self.index_type == "Flat":
                # Exact search - good for small datasets
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product
            elif self.index_type == "IVF":
                # Approximate search with clustering - good for large datasets
                nlist = min(100, max(1, n_vectors // 10))  # Number of clusters
                quantizer = faiss.IndexFlatIP(self.embedding_dim)
                self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
            else:
                raise ValueError(f"Unsupported index type: {self.index_type}")
            
            # Normalize embeddings for cosine similarity
            embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Train index if necessary
            if hasattr(self.index, 'train'):
                self.index.train(embeddings_normalized.astype(np.float32))
            
            # Add vectors to index
            self.index.add(embeddings_normalized.astype(np.float32))
            
            # Store chunks and metadata
            self.chunks = chunks
            self.chunk_ids = [chunk.get('metadata', {}).get('chunk_id', str(i)) for i, chunk in enumerate(chunks)]
            
            logger.info(f"Created FAISS index with {n_vectors} vectors using {self.index_type}")
            
        except Exception as e:
            logger.error(f"Error creating FAISS index: {str(e)}")
            raise
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Search for similar vectors"""
        try:
            if self.index is None:
                raise ValueError("Index not created. Call create_index first.")
            
            # Normalize query embedding
            query_normalized = query_embedding / np.linalg.norm(query_embedding)
            query_normalized = query_normalized.reshape(1, -1).astype(np.float32)
            
            # Search
            scores, indices = self.index.search(query_normalized, top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.chunks):  # Valid index
                    chunk = self.chunks[idx].copy()
                    chunk['similarity_score'] = float(score)
                    results.append(chunk)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {str(e)}")
            return []
    
    def save_index(self, index_path: str):
        """Save FAISS index to disk"""
        try:
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, f"{index_path}.faiss")
            
            # Save metadata
            metadata = {
                'chunks': self.chunks,
                'chunk_ids': self.chunk_ids,
                'embedding_dim': self.embedding_dim,
                'index_type': self.index_type
            }
            with open(f"{index_path}_metadata.pkl", 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Saved FAISS index to {index_path}")
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
    
    def load_index(self, index_path: str):
        """Load FAISS index from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(f"{index_path}.faiss")
            
            # Load metadata
            with open(f"{index_path}_metadata.pkl", 'rb') as f:
                metadata = pickle.load(f)
            
            self.chunks = metadata['chunks']
            self.chunk_ids = metadata['chunk_ids']
            self.embedding_dim = metadata['embedding_dim']
            self.index_type = metadata['index_type']
            
            logger.info(f"Loaded FAISS index from {index_path}")
            
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")

class ChromaVectorDB:
    """ChromaDB-based vector database"""
    
    def __init__(self, collection_name: str = "kgisl_chunks", persist_directory: str = "chroma_db"):
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB is not available. Install with: pip install chromadb")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Loaded existing ChromaDB collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "KGiSL chatbot knowledge base"}
            )
            logger.info(f"Created new ChromaDB collection: {collection_name}")
    
    def add_chunks(self, chunks: List[Dict], embeddings: np.ndarray):
        """Add chunks with embeddings to ChromaDB"""
        try:
            documents = []
            metadatas = []
            ids = []
            embeddings_list = []
            
            for i, chunk in enumerate(chunks):
                # Prepare document text
                documents.append(chunk.get('text', ''))
                
                # Prepare metadata (ChromaDB doesn't support nested objects)
                metadata = {
                    'source_url': chunk.get('source_url', ''),
                    'source_file': chunk.get('source_file', ''),
                    'title': chunk.get('title', ''),
                    'chunk_id': chunk.get('metadata', {}).get('chunk_id', str(i)),
                    'word_count': chunk.get('metadata', {}).get('statistics', {}).get('word_count', 0),
                    'importance_score': chunk.get('metadata', {}).get('importance_score', 0.0),
                    'categories': ','.join(chunk.get('metadata', {}).get('categories', [])),
                }
                metadatas.append(metadata)
                
                # Use chunk_id or index as ID
                chunk_id = chunk.get('metadata', {}).get('chunk_id', f"chunk_{i}")
                ids.append(chunk_id)
                
                # Add embedding
                embeddings_list.append(embeddings[i].tolist())
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings_list
            )
            
            logger.info(f"Added {len(chunks)} chunks to ChromaDB")
            
        except Exception as e:
            logger.error(f"Error adding chunks to ChromaDB: {str(e)}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """Search for similar chunks in ChromaDB"""
        try:
            # Prepare query
            query_embeddings = [query_embedding.tolist()]
            
            # Search
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k,
                where=filter_metadata,  # Optional metadata filtering
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            
            if results['documents'][0]:  # Check if we have results
                for i in range(len(results['documents'][0])):
                    result = {
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                        'chunk_id': results['metadatas'][0][i].get('chunk_id', ''),
                        'source_url': results['metadatas'][0][i].get('source_url', ''),
                        'title': results['metadatas'][0][i].get('title', ''),
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []
    
    def delete_collection(self):
        """Delete the collection"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")

class VectorDBManager:
    """Unified interface for different vector databases"""
    
    def __init__(self, db_type: str = "faiss", **kwargs):
        self.db_type = db_type.lower()
        
        if self.db_type == "faiss":
            embedding_dim = kwargs.get('embedding_dim', 384)
            index_type = kwargs.get('index_type', 'IVF')
            self.db = FAISSVectorDB(embedding_dim, index_type)
        elif self.db_type == "chroma":
            collection_name = kwargs.get('collection_name', 'kgisl_chunks')
            persist_directory = kwargs.get('persist_directory', 'chroma_db')
            self.db = ChromaVectorDB(collection_name, persist_directory)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def create_and_populate(self, embeddings: np.ndarray, chunks: List[Dict]):
        """Create database and populate with embeddings"""
        if self.db_type == "faiss":
            self.db.create_index(embeddings, chunks)
        elif self.db_type == "chroma":
            self.db.add_chunks(chunks, embeddings)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5, **kwargs) -> List[Dict]:
        """Search for similar chunks"""
        return self.db.search(query_embedding, top_k, **kwargs)
    
    def save(self, path: str):
        """Save database to disk"""
        if self.db_type == "faiss":
            self.db.save_index(path)
        # ChromaDB auto-persists
    
    def load(self, path: str):
        """Load database from disk"""
        if self.db_type == "faiss":
            self.db.load_index(path)
        # ChromaDB auto-loads

def main():
    """Example usage"""
    # This would typically be called after generating embeddings
    print("Vector database classes initialized")
    print(f"FAISS available: {FAISS_AVAILABLE}")
    print(f"ChromaDB available: {CHROMA_AVAILABLE}")

if __name__ == "__main__":
    main()