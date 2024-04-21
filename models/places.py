from pydantic import BaseModel
from typing import List

class Place(BaseModel):
    """
    A location in a story.

    Attributes:
    - name: The name of the place.
    - description: A short, accurate description of the place from the perspective of the narrator of the story, written in a third person perspective.
    - relationship: The relationship of the place to the story.
    - thoughts: A list of thought IDs that take place in the location.
    - user_id: The ID of the user associated with the place.
    """
    name: str
    description: str
    relationship: str
    thoughts: List[str]
    user_id: str