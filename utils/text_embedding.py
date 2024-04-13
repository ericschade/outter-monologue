from transformers import pipeline
import logging
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer

load_dotenv()

# Placeholder for the Hugging Face model to be used for embeddings
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

logging.basicConfig(level=logging.INFO)


def generate_text_embedding(text):
    """
    Generates a semantic vector embedding for the given text input.
    
    Args:
        text (str): The text input from which to generate the embedding.
    
    Returns:
        list: The semantic vector embedding of the input text.
    """
    try:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        embeddings = model.encode(text)
        logging.info("Text embedding generated successfully.")
        return(embeddings)
    except Exception as e:
        logging.error("Error generating text embedding: %s", e, exc_info=True)
        raise