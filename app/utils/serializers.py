"""
MongoDB document serialization utilities
"""
from typing import Dict, Any, List, Optional
from bson import ObjectId


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Convert ObjectId to string for JSON serialization
    
    Args:
        doc: MongoDB document dictionary
        
    Returns:
        Serialized document with ObjectId converted to string, or None if input is None
    """
    if doc is None:
        return None
    
    # Create a copy to avoid modifying the original document
    serialized_doc = doc.copy()
    
    # Convert ObjectId to string for JSON serialization
    if "_id" in serialized_doc and isinstance(serialized_doc["_id"], ObjectId):
        serialized_doc["_id"] = str(serialized_doc["_id"])
    
    return serialized_doc


def serialize_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize a list of MongoDB documents
    
    Args:
        docs: List of MongoDB document dictionaries
        
    Returns:
        List of serialized documents
    """
    return [serialize_doc(doc) for doc in docs if doc is not None]


def convert_object_ids(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert ObjectId instances to strings in a document
    Useful for nested documents or complex structures
    
    Args:
        doc: Document that may contain ObjectIds at any level
        
    Returns:
        Document with all ObjectIds converted to strings
    """
    if isinstance(doc, dict):
        return {
            key: convert_object_ids(value) if isinstance(value, (dict, list)) 
                  else str(value) if isinstance(value, ObjectId) 
                  else value
            for key, value in doc.items()
        }
    elif isinstance(doc, list):
        return [convert_object_ids(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc