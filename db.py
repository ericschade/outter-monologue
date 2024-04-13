import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB connection URI from the environment variables
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/outter_monologue') 

# Create a MongoDB client
client = MongoClient(MONGO_URI)

# Function to get the database connection
def get_database():
    """
    Returns a connection to the database
    """
    try:
        db = client['outter_monologue']  # Database name
        print("Successfully connected to the database.")
        return db
    except Exception as e:
        print(f"Error connecting to the MongoDB database: {e}")
        return None