from db import get_database
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

def create_thought(user_id: str, inspiration_words, raw_text, semantic_vector: np.array) -> str:
    """
    Creates a new thought in the database.
    """
    db = get_database()
    thoughts_collection = db.thoughts
    try:
        thought_id = thoughts_collection.insert_one({
            "inspiration_words": inspiration_words,
            "raw_text": raw_text,
            "semantic_vector": semantic_vector.tolist(),
            "user_id": user_id
        }).inserted_id
        logging.info(f"Thought created with ID: {thought_id}")
        return str(thought_id)
    except DuplicateKeyError as e:
        logging.error(f"DuplicateKeyError: {e}")
        return None
    except Exception as e:
        logging.error(f"Error creating thought: {e}")
        return None

def get_thought_by_id(thought_id):
    """
    Retrieves a thought by its ID.
    """
    db = get_database()
    thoughts_collection = db.thoughts
    try:
        thought = thoughts_collection.find_one({"_id": ObjectId(thought_id)})
        if thought:
            thought["_id"] = str(thought["_id"])
            logging.info(f"Thought retrieved with ID: {thought_id}")
        else:
            logging.warning(f"No thought found with ID: {thought_id}")
        return thought
    except Exception as e:
        logging.error(f"Error retrieving thought by ID: {e}")
        return None

def get_all_thoughts(user_id: str):
    """
    Retrieves all thoughts from the database.
    """
    db = get_database()
    thoughts_collection = db.thoughts
    try:
        thoughts = list(thoughts_collection.find({"user_id": user_id}))
        logging.info("All thoughts retrieved successfully.")
        return thoughts
    except Exception as e:
        logging.error(f"Error retrieving all thoughts: {e}")
        return []

def search_thoughts(user_id: str, query_vector, top_n=5, field="semantic_vector"):
    """
    Searches thoughts based on cosine similarity with the query vector.
    """
    db = get_database()
    thoughts_collection = db.thoughts
    try:
        thoughts = list(thoughts_collection.find({"user_id": user_id}))
        thought_vectors = np.array([thought[field] for thought in thoughts])
        query_vector = np.array(query_vector).reshape(1, -1)
        similarities = cosine_similarity(thought_vectors, query_vector).flatten()
        sorted_indices = np.argsort(-similarities)[:top_n]
        sorted_indices = sorted_indices[similarities[sorted_indices] > 0.1]
        most_similar_thoughts = [thoughts[index] for index in sorted_indices if similarities[index] > 0]
        logging.info(f"Found {len(most_similar_thoughts)} similar thoughts.")
        logging.info(f"Similarities: {similarities[sorted_indices]}")
        return most_similar_thoughts
    except Exception as e:
        logging.error(f"Error searching thoughts: {e}")
        return []
    
def thought_str(thought):
    """ Returns a string representation of a thought. Format it in a conversational way, explaining that the inspiration words are the words that inspired the thought, and the raw text is the actual thought."""
    return f"The words {thought['inspiration_words']} inspired you to think about: {thought['raw_text']}"