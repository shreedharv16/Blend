"""Vector store service using Qdrant."""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from typing import List, Dict, Any, Optional
import uuid
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorService:
    """Service for interacting with Qdrant vector store."""
    
    def __init__(self):
        """Initialize vector service."""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = settings.QDRANT_COLLECTION
        self._ensure_collection()
        logger.info(f"Initialized Qdrant client for collection: {self.collection_name}")
    
    def _ensure_collection(self):
        """Ensure collection exists with proper indexes."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,  # Gemini embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
                
                # Create payload indexes for filtering
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="file_id",
                        field_schema="keyword"
                    )
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="type",
                        field_schema="keyword"
                    )
                    logger.info(f"Created payload indexes for {self.collection_name}")
                except Exception as idx_error:
                    logger.warning(f"Could not create indexes (may already exist): {idx_error}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    async def store_file_metadata(
        self,
        file_id: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """Store file metadata in vector store."""
        try:
            point_id = str(uuid.uuid4())
            
            # If no embedding provided, use a placeholder
            if embedding is None:
                embedding = [0.0] * 768
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "type": "file_metadata",
                    "file_id": file_id,
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Stored metadata for file: {file_id}")
            return point_id
        
        except Exception as e:
            logger.error(f"Error storing file metadata: {e}")
            raise
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve file metadata by file ID."""
        try:
            # Try with filter first
            try:
                results = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="file_id",
                                match=MatchValue(value=file_id)
                            ),
                            FieldCondition(
                                key="type",
                                match=MatchValue(value="file_metadata")
                            )
                        ]
                    ),
                    limit=1
                )
                
                if results[0]:
                    return results[0][0].payload
                
                return None
            except Exception as filter_error:
                # If filtering fails (missing index), fall back to scanning all
                logger.warning(f"Filter failed, scanning all points: {filter_error}")
                
                # Try to create indexes for future queries
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="file_id",
                        field_schema="keyword"
                    )
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="type",
                        field_schema="keyword"
                    )
                    logger.info("Created missing payload indexes")
                except:
                    pass
                
                # Scan all points and filter manually
                results = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100
                )
                
                for point in results[0]:
                    if point.payload.get("file_id") == file_id and point.payload.get("type") == "file_metadata":
                        return point.payload
                
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving file metadata: {e}")
            return None
    
    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 5,
        file_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar items."""
        try:
            query_filter = None
            if file_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="file_id",
                            match=MatchValue(value=file_id)
                        )
                    ]
                )
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )
            
            return [
                {
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Error searching similar items: {e}")
            return []
    
    async def delete_file_data(self, file_id: str):
        """Delete all data for a file."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="file_id",
                            match=MatchValue(value=file_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted data for file: {file_id}")
        except Exception as e:
            logger.error(f"Error deleting file data: {e}")
            raise


# Global vector service instance
vector_service = VectorService()

