#!/usr/bin/env python3
"""
Load Wheat Rust Knowledge Base to Qdrant Vector Store
Production-ready script using FREE local embeddings (sentence-transformers)
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger_temp = logging.getLogger(__name__)
    logger_temp.info(f"Loaded .env from {env_path}")

# Import chunks
from wheat_rust_chunks import wheat_rust_chunks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
QDRANT_URL = "http://qdrant:6333"
COLLECTION_NAME = "org_2_wheat_kb"
# Using multilingual model that supports Hindi well
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION = 384  # This model outputs 384-dim vectors
BATCH_SIZE = 10


class WheatKBLoader:
    """Load wheat rust knowledge base into Qdrant using local embeddings"""
    
    def __init__(self):
        # Initialize Qdrant client
        self.qdrant = QdrantClient(
            url=QDRANT_URL,
            prefer_grpc=False
        )
        
        # Load local embedding model (multilingual, supports Hindi)
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("✅ Embedding model loaded successfully (FREE, no API key needed!)")

        
    async def create_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if COLLECTION_NAME in collection_names:
                logger.info(f"Collection '{COLLECTION_NAME}' already exists - deleting...")
                self.qdrant.delete_collection(COLLECTION_NAME)
            
            # Create collection
            self.qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection '{COLLECTION_NAME}' created successfully")
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts using local model (synchronous)"""
        try:
            # sentence-transformers encode is synchronous
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {e}")
            raise
    
    def prepare_point(self, chunk: Dict, embedding: List[float], idx: int) -> PointStruct:
        """Prepare a Qdrant point from chunk data"""
        point_id = str(uuid4())
        
        payload = {
            "content": chunk["content"],
            "crop": chunk["crop"],
            "disease_type": chunk["disease_type"],
            "topic": chunk["topic"],
            "source": chunk["source"],
            "chunk_index": idx
        }
        
        return PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
    
    async def load_chunks(self, chunks: List[Dict]):
        """Load all chunks into Qdrant"""
        total_chunks = len(chunks)
        logger.info(f"Loading {total_chunks} chunks into Qdrant...")
        
        # Process in batches
        for batch_start in range(0, total_chunks, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_chunks)
            batch = chunks[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//BATCH_SIZE + 1} "
                       f"(chunks {batch_start+1}-{batch_end})")
            
            try:
                # Extract texts for batch embedding
                texts = [chunk["content"] for chunk in batch]
                
                # Create embeddings in batch (now synchronous, no API calls!)
                embeddings = self.create_embeddings_batch(texts)
                
                # Prepare points
                points = [
                    self.prepare_point(chunk, embedding, batch_start + i)
                    for i, (chunk, embedding) in enumerate(zip(batch, embeddings))
                ]
                
                # Upload to Qdrant
                self.qdrant.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                
                logger.info(f"✅ Batch {batch_start//BATCH_SIZE + 1} uploaded successfully")
                
            except Exception as e:
                logger.error(f"❌ Error processing batch {batch_start//BATCH_SIZE + 1}: {e}")
                raise
        
        logger.info(f"✅ All {total_chunks} chunks loaded successfully!")
    
    async def verify_collection(self):
        """Verify collection contents"""
        try:
            collection_info = self.qdrant.get_collection(COLLECTION_NAME)
            point_count = collection_info.points_count
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Collection Verification:")
            logger.info(f"  Name: {COLLECTION_NAME}")
            logger.info(f"  Points: {point_count}")
            logger.info(f"  Vector Size: {collection_info.config.params.vectors.size}")
            logger.info(f"  Distance: {collection_info.config.params.vectors.distance}")
            logger.info(f"  Model: {EMBEDDING_MODEL} (LOCAL, FREE)")
            logger.info(f"{'='*60}\n")
            
            # Sample a few points
            sample = self.qdrant.scroll(
                collection_name=COLLECTION_NAME,
                limit=3,
                with_payload=True,
                with_vectors=False
            )
            
            if sample[0]:
                logger.info("Sample points:")
                for i, point in enumerate(sample[0], 1):
                    logger.info(f"\n  Point {i}:")
                    logger.info(f"    ID: {point.id}")
                    logger.info(f"    Crop: {point.payload.get('crop')}")
                    logger.info(f"    Disease: {point.payload.get('disease_type')}")
                    logger.info(f"    Topic: {point.payload.get('topic')}")
                    logger.info(f"    Content Preview: {point.payload.get('content')[:100]}...")
            
        except Exception as e:
            logger.error(f"Error verifying collection: {e}")
            raise
    
    async def run(self):
        """Main execution flow"""
        try:
            logger.info("="*60)
            logger.info("Wheat Rust Knowledge Base - Qdrant Loader")
            logger.info("="*60)
            
            # Step 1: Create collection
            logger.info("\n[Step 1/3] Creating Qdrant collection...")
            await self.create_collection()
            
            # Step 2: Load chunks
            logger.info(f"\n[Step 2/3] Loading {len(wheat_rust_chunks)} chunks...")
            await self.load_chunks(wheat_rust_chunks)
            
            # Step 3: Verify
            logger.info("\n[Step 3/3] Verifying collection...")
            await self.verify_collection()
            
            logger.info("\n" + "="*60)
            logger.info("✅ Knowledge base loaded successfully!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"\n❌ Failed to load knowledge base: {e}")
            sys.exit(1)


async def main():
    """Entry point"""
    loader = WheatKBLoader()
    await loader.run()


if __name__ == "__main__":
    asyncio.run(main())
