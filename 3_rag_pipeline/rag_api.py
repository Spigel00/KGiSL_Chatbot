"""
RAG API Backend for KGiSL Chatbot
FastAPI backend with retrieval + generation capabilities
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import json
import os
import logging
from datetime import datetime
import asyncio
import uvicorn

# Import our modules
from embeddings import EmbeddingGenerator
from vector_db import VectorDBManager

# OpenAI/LangChain imports
try:
    import openai
    from langchain.llms import OpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI/LangChain not available. Install with: pip install openai langchain")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict]
    confidence: float
    response_time: float

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_categories: Optional[List[str]] = None

class SearchResult(BaseModel):
    chunks: List[Dict]
    total_results: int

# FastAPI app
app = FastAPI(
    title="KGiSL Chatbot API",
    description="RAG-powered chatbot API for KGiSL knowledge base",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
embedding_generator = None
vector_db = None
chat_model = None

class RAGChatbot:
    def __init__(self):
        self.embedding_generator = None
        self.vector_db = None
        self.chat_model = None
        self.system_prompt = """You are a helpful assistant for KGiSL (Kumaraguru Group of Institutions). 
You provide accurate information about KGiSL's services, courses, facilities, and other related topics.
Use the provided context to answer questions. If you don't know something from the context, say so.
Be helpful, professional, and concise in your responses."""
        
    def initialize(self):
        """Initialize the RAG components"""
        try:
            # Initialize embedding generator
            self.embedding_generator = EmbeddingGenerator()
            logger.info("Embedding generator initialized")
            
            # Initialize vector database
            db_type = os.getenv('VECTOR_DB_TYPE', 'faiss')
            if db_type.lower() == 'chroma':
                self.vector_db = VectorDBManager(
                    db_type='chroma',
                    collection_name='kgisl_chunks',
                    persist_directory='chroma_db'
                )
            else:
                self.vector_db = VectorDBManager(
                    db_type='faiss',
                    embedding_dim=self.embedding_generator.embedding_dim
                )
                # Load existing FAISS index if available
                index_path = os.getenv('FAISS_INDEX_PATH', 'faiss_index/kgisl_index')
                if os.path.exists(f"{index_path}.faiss"):
                    self.vector_db.load(index_path)
                    logger.info("Loaded existing FAISS index")
            
            # Initialize chat model
            if OPENAI_AVAILABLE:
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if openai_api_key:
                    self.chat_model = ChatOpenAI(
                        model_name=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                        temperature=0.7,
                        api_key=openai_api_key
                    )
                    logger.info("OpenAI chat model initialized")
                else:
                    logger.warning("OpenAI API key not found")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG components: {str(e)}")
            return False
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant context for the query"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Search vector database
            results = self.vector_db.search(query_embedding, top_k)
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    def generate_response(self, query: str, context: List[Dict]) -> str:
        """Generate response using retrieved context"""
        try:
            if not self.chat_model:
                # Fallback response without LLM
                if context:
                    return f"Based on the available information: {context[0].get('text', '')[:200]}..."
                else:
                    return "I don't have specific information about that topic in my knowledge base."
            
            # Prepare context text
            context_text = "\n\n".join([
                f"Source: {chunk.get('title', 'Unknown')}\n{chunk.get('text', '')}"
                for chunk in context[:3]  # Use top 3 chunks
            ])
            
            # Create messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""Context information:
{context_text}

Question: {query}

Please provide a helpful answer based on the context above.""")
            ]
            
            # Generate response
            response = self.chat_model(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response right now."
    
    def calculate_confidence(self, query: str, context: List[Dict], response: str) -> float:
        """Calculate confidence score for the response"""
        try:
            if not context:
                return 0.1
            
            # Simple confidence calculation based on similarity scores
            avg_similarity = sum(chunk.get('similarity_score', 0) for chunk in context) / len(context)
            
            # Adjust based on response length and context relevance
            if len(response.split()) < 10:
                confidence = avg_similarity * 0.7
            else:
                confidence = avg_similarity * 0.9
            
            return min(max(confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5

# Initialize chatbot
chatbot = RAGChatbot()

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup"""
    logger.info("Starting KGiSL Chatbot API...")
    success = chatbot.initialize()
    if not success:
        logger.error("Failed to initialize RAG system")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "KGiSL Chatbot API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "embedding_generator": chatbot.embedding_generator is not None,
            "vector_db": chatbot.vector_db is not None,
            "chat_model": chatbot.chat_model is not None
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint"""
    try:
        start_time = datetime.now()
        
        # Retrieve relevant context
        context = chatbot.retrieve_context(message.message, top_k=5)
        
        # Generate response
        response_text = chatbot.generate_response(message.message, context)
        
        # Calculate confidence
        confidence = chatbot.calculate_confidence(message.message, context, response_text)
        
        # Prepare sources
        sources = []
        for chunk in context[:3]:  # Return top 3 sources
            sources.append({
                "title": chunk.get('title', 'Unknown'),
                "url": chunk.get('source_url', ''),
                "similarity": chunk.get('similarity_score', 0),
                "snippet": chunk.get('text', '')[:150] + "..."
            })
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        return ChatResponse(
            response=response_text,
            sources=sources,
            confidence=confidence,
            response_time=response_time
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/search", response_model=SearchResult)
async def search(request: SearchRequest):
    """Search endpoint for retrieving relevant chunks"""
    try:
        # Retrieve relevant chunks
        context = chatbot.retrieve_context(request.query, top_k=request.top_k)
        
        # Filter by categories if specified
        if request.filter_categories:
            filtered_context = []
            for chunk in context:
                chunk_categories = chunk.get('metadata', {}).get('categories', [])
                if any(cat in chunk_categories for cat in request.filter_categories):
                    filtered_context.append(chunk)
            context = filtered_context
        
        return SearchResult(
            chunks=context,
            total_results=len(context)
        )
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        # This would return statistics about the knowledge base
        stats = {
            "total_chunks": 0,  # Would be populated from vector DB
            "embedding_model": chatbot.embedding_generator.model_name if chatbot.embedding_generator else None,
            "vector_db_type": "faiss" if chatbot.vector_db else None,
            "chat_model": "gpt-3.5-turbo" if chatbot.chat_model else None
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "rag_api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )