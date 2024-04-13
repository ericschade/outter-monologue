import random

# List of simple, third-grade level words
WORDS = [
    "happy", "sad", "dog", "cat", "sun", "moon",
    "star", "book", "tree", "cup", "pen", "apple"
]

def get_random_words():
    """Selects two random words from the predefined list."""
    try:
        selected_words = random.sample(WORDS, 2)
        return selected_words
    except Exception as e:
        print(f"Error selecting random words: {e}")
        raise