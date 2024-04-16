from langchain_core.tools import tool
from models.thoughts import create_thought
from typing import List
from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import JsonOutputToolsParser
from langchain.prompts import PromptTemplate
from models.characters import Character, update_character
from db import get_database
from flask import session
import numpy as np

character_model = ChatOpenAI(model="gpt-3.5-turbo-1106")
character_model.temperature = 0.0

analysis_model = ChatOpenAI(model="gpt-3.5-turbo-1106")

# maybe convert to generalized 'entities' later on
character_extraction_prompt = PromptTemplate.from_template(
    template="""
    You are provided with a story or thought from the perspective of a narrator.
    Describe the non-narrator characters in the story or thought.

    Use only information provided in the story or thought to describe the characters. Do not make any assumptions about the characters' personalities or add any additional information about the characters not explicitly mentioned in the thought.
    Write any descriptions from a third-person perspective.
    
    Story:
    {thought}
    """
)

@tool
def update_character_tool(user_id: str, name: str, relationship: str, thought_id: str) -> None:
    """
    Updates a character entity in the database.
    """
    try:
        update_character(user_id, name, relationship, thought_id)
    except Exception as e:
        print(f"Error updating character: {e}")

@tool
def agent_create_thought(user_id: str, inspiration_words: List[str], raw_text: str, semantic_vector: np.array):
    """
    Create a new thought in the database.
    """
    create_thought(user_id, inspiration_words, raw_text, semantic_vector)

@tool
def analyze_thought(user_id: str, thought_id: str) -> None:
    """
    Analyze a thought in the database.
    """
    try:
        db = get_database()
        thought = db.thoughts.find_one({'_id': ObjectId(thought_id)})
        if thought:
            thought['semantic_vector'] = np.array(thought['semantic_vector'])
            thought['thought_embedding'] = generate_text_embedding(thought['raw_text'])
            db.thoughts.update_one({'_id': ObjectId(thought_id)}, {'$set': thought})
            print("Thought analyzed successfully.")
        else:
            print("No thought found.")
    except Exception as e:
        print(f"Error analyzing thought: {e}")


character_model_with_extraction_tool = character_model.bind_tools([Character])

character_model_with_update_tool = character_model.bind_tools([update_character])

character_chain = character_extraction_prompt | character_model_with_extraction_tool | JsonOutputToolsParser()

def thought_cascade(user_id: str, thought_id: str, thought_text: str) -> None:
    """
    Extracts character entities from a given thought and updates the database with the extracted entities.
    """
    db = get_database()
    try:
        character_entities = character_chain.invoke({"thought": thought_text})
        print("found characters: ", character_entities)
        for entity in character_entities:
            args = entity['args']
            # agentify this interaction to update based on previous stories as well
            update_character(user_id, args['name'], args['relationship'], args['description'], thought_id)
    except Exception as e:
        print(f"Error extracting character entities: {e}")