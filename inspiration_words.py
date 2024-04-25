import random
import json
from random_word import RandomWords
import requests

# List of simple, third-grade level words
word_data_path = "utils/aggregate_words.json"
with open(word_data_path, "r") as f:
    WORDS = json.load(f)

def get_random_word():
    return random.choice(list(WORDS.keys()))

def get_random_words():
    """Selects two random words from the predefined list."""
    try:
        # selected_words = random.sample(WORDS, 2)
        selected_words = [get_random_word() for i in range(2)]
        print(f"Selected words: {selected_words}")
        return selected_words
    except Exception as e:
        print(f"Error selecting random words: {e}")
        raise