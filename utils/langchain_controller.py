from langchain_core.tools import tool
from models.thoughts import create_thought, thought_str
from models.characters import character_str
from typing import List, Dict
from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import JsonOutputToolsParser
from langchain.prompts import PromptTemplate
from models.characters import Character, update_character
from db import get_database
from flask import session
import numpy as np
from bson.objectid import ObjectId
from utils.text_embedding import generate_text_embedding

character_model = ChatOpenAI(model="gpt-3.5-turbo-1106")
character_model.temperature = 0.0

analysis_model = ChatOpenAI(model="gpt-3.5-turbo-1106")
analysis_model.temperature = 0.6

# maybe convert to generalized 'entities' later on
character_extraction_prompt = PromptTemplate.from_template(
    template="""
    You are provided with a story or thought from the perspective of a narrator.
    Describe the non-narrator, living characters from the story or thought, and 
    describe them as json objects. Only describe living entities, and only if 
    they have a name used in the thought.

    Use only information provided in the story or thought to describe the characters. 
    Do not make any assumptions about the characters' personalities or add any 
    additional information about the characters not explicitly mentioned in the thought.
    Write any descriptions from a third-person perspective.
    
    Story:
    {thought}
    """
)

analysis_prompt = PromptTemplate.from_template(
    template="""
    Overview:
    You are skilled in psychological analysis. A person was given two words as inspiration and provided a thought or 
    memory that was related to the prompt words in their head. You must analyze their response to determine
    their underlying personality traits.
    
    Instructions:
    You must analyze the thought provided below to determine underlying personality trait(s) of the 
    person who is speaking. Explain your analysis in detail, including anything unexpected about 
    which words inspired the person to have this thought

    Label the person's response as one or more of the following: Emotional, Factual, Anecdotal. Do not explain your reasoning.
    
    Respond in the following format:
    - Traits: [LIST_OF_PERSONALITY_TRAITS_HERE]
    - Analysis: YOUR_ANALYSIS_HERE
    - Category: ASSIGNED_THOUGHT_CATEGORY_HERE

    Context:
    Inspiration words:
    [{prompt_word1}, {prompt_word2}]
    
    Person's thought:
    {thought}
    """
)

ask_myself_prompt = PromptTemplate.from_template(
    template="""
    You are a person with the following relevant thoughts, opinions, and stories
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

# @tool
# def agent_create_thought(user_id: str, inspiration_words: List[str], raw_text: str, semantic_vector: np.array):
#     """
#     Create a new thought in the database.
#     """
#     create_thought(user_id, inspiration_words, raw_text, semantic_vector)

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

analysis_chain = analysis_prompt | analysis_model

def thought_cascade(user_id: str, thought_id: str, thought_text: str) -> None:
    """
    Initiates a several step process of handling new thoughts. 
        1. Extracts character entities from a given thought and updates the database with the extracted entities.
        2. Analyzes the thought and updates the database wwith the new analysis.
    """
    db = get_database()
    
    prompt_words = db.users.find_one({'_id': ObjectId(user_id)})['inspiration_words']

    try:
        character_entities = character_chain.invoke({"thought": thought_text})
        print("found characters: ", character_entities)
        for entity in character_entities:
            args = entity['args']
            # TODO: agentify this interaction to update based on previous stories as well
            update_character(user_id, args['name'], args['relationship'], args['description'], thought_id)
    except Exception as e:
        print(f"Error extracting character entities: {e}")

    create_analysis(thought_id, thought_text, prompt_words)

def ask_myself_gen_resp(query: str, thoughts: List[str], analyses: List[Dict], characters: List[Dict]) -> str:
    """
    Generates a response by invoking a langchain chain with the given query, thoughts, and analyses.
    Returns the result of the chain invocation.
    """
    try:
        # Create a prompt template for asking myself
        ask_myself_prompt = PromptTemplate.from_template(
            template="""
            You are a person with the following thoughts: 
        
            Thoughts:
            {thoughts}
            
            You are aware of the following traits and characteristics about yourself:
            
            Analyses:
            {analyses}

            You have the following characters in your life:

            Characters:
            {characters}

            You must respond to the following query, which you have asked of yourself:
            {query}


            Only use the provided context to answer questions personally. Do not make any assumptions about yourself. If you do not know the answer, respond with "I don't know."
            """
        )
        
        # Create the chain with the ask myself prompt
        ask_myself_chain = ask_myself_prompt | analysis_model

        # Invoke the chain with the provided query, thoughts, and analyses
        response = ask_myself_chain.invoke({
            "query": query,
            "thoughts": "\n".join([thought_str(thought) for thought in thoughts]),
            "analyses": "\n".join([analysis["analysis"] for analysis in analyses]),
            "characters": "\n".join([character_str(character) for character in characters])
        })
        
        print(response.json)

        # Return the result of the chain invocation
        return response.content
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return ""


def create_analysis(thought_id: str, thought_text: str, prompt_words: List[str]) -> None:
    """
    Creates an analysis entity in the database.
    """
    try:
        db = get_database()
        # invoke the thought analysis chain
        analysis = analysis_chain.invoke({"thought": thought_text, "prompt_word1": prompt_words[0], "prompt_word2": prompt_words[1]})

        # create an embedding of the analysis
        analysis_embedding = generate_text_embedding(analysis.content)

        # save to the database
        db.thoughts.update_one({'_id': ObjectId(thought_id)}, {'$set': {'analysis': analysis.content, 'analysis_embedding': analysis_embedding.tolist()}})
        print(f"Analysis created successfully for {thought_id}.")
    except Exception as e:
        print(f"Error analyzing thought: {e}")