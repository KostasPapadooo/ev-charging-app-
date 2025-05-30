from typing import TypeVar, Generic, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseRepository(Generic[ModelType], ABC):
    def __init__(self, collection: AsyncIOMotorCollection, model_class: type[ModelType]):
        self.collection = collection
        self.model_class = model_class
    
    async def create(self, obj: ModelType) -> ModelType:
        """Create a new document"""
        try:
            obj_dict = obj.dict(by_alias=True, exclude_unset=False)
            if "_id" in obj_dict and obj_dict["_id"] is None:
                del obj_dict["_id"]
            
            result = await self.collection.insert_one(obj_dict)
            obj_dict["_id"] = result.inserted_id
            
            return self.model_class(**obj_dict)
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    async def get_by_id(self, id: str | ObjectId) -> Optional[ModelType]:
        """Get document by ID"""
        try:
            if isinstance(id, str):
                id = ObjectId(id)
            
            doc = await self.collection.find_one({"_id": id})
            if doc:
                return self.model_class(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting document by ID {id}: {e}")
            raise
    
    async def get_many(
        self, 
        filter_dict: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "_id",
        sort_order: int = ASCENDING
    ) -> List[ModelType]:
        """Get multiple documents with pagination"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict)
            
            if sort_by:
                cursor = cursor.sort(sort_by, sort_order)
            
            cursor = cursor.skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            return [self.model_class(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            raise
    
    async def update_by_id(self, id: str | ObjectId, update_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update document by ID"""
        try:
            if isinstance(id, str):
                id = ObjectId(id)
            
            result = await self.collection.find_one_and_update(
                {"_id": id},
                {"$set": update_data},
                return_document=True
            )
            
            if result:
                return self.model_class(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating document {id}: {e}")
            raise
    
    async def delete_by_id(self, id: str | ObjectId) -> bool:
        """Delete document by ID"""
        try:
            if isinstance(id, str):
                id = ObjectId(id)
            
            result = await self.collection.delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document {id}: {e}")
            raise
    
    async def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents matching filter"""
        try:
            filter_dict = filter_dict or {}
            return await self.collection.count_documents(filter_dict)
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            raise
    
    async def exists(self, filter_dict: Dict[str, Any]) -> bool:
        """Check if document exists"""
        try:
            doc = await self.collection.find_one(filter_dict, {"_id": 1})
            return doc is not None
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            raise 