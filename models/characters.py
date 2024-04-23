from pydantic import BaseModel
from bson import ObjectId
from db import get_database
from typing import List

class Character(BaseModel):
    """
    A non-narrator character in a story.

    Attributes:
    - name: The name of the character.
    - relationship: A description of the character in relation to the narrator of a story, written in a third person perspective without explicitly mentioning the narrator. For example: "Best Friend", or "deceased grandmother"
    - description: A short, accurate description of the character from the perspective of the narrator of the story, written in a third person perspective.
    - user_id: The ID of the user associated with the character.
    - thoughts: A list of thought IDs associated with the character.

    """
    name: str
    relationship: str
    description: str
    user_id: str
    thoughts: List[str]

def update_character(user_id: str, name: str, relationship: str, description: str, thought_id: str) -> ObjectId:
    if not user_id:
        raise ValueError("user_id cannot be empty.")
    if not name:
        raise ValueError("name cannot be empty.")
    
    db = get_database()
    character_id = db.characters.update_one(
        {'user_id': user_id, 'name': name},
        {'$set': {'relationship': relationship, 'description': description}, '$push': {'thoughts': thought_id}},
        upsert=True
    ).upserted_id
    return character_id

def character_str(character: Character) -> str:
    return f"Name: {character.name} \n Relationship to you: {character.relationship} \n Description: {character.description}"
    return f"Character(name={character.name}, relationship={character.relationship}, description={character.description}, user_id={character.user_id}, thoughts={character.thoughts})"