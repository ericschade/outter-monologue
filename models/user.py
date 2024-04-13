import os
from db import get_database
from bcrypt import hashpw, gensalt, checkpw

def hash_password(password):
    """
    Hashes a password using bcrypt.
    """
    try:
        hashed = hashpw(password.encode('utf8'), gensalt())
        return hashed
    except Exception as e:
        print(f"Error hashing password: {e}")
        return None

def check_password(password, hashed):
    """
    Checks a password against a hashed password.
    """
    try:
        return checkpw(password.encode('utf8'), hashed)
    except Exception as e:
        print(f"Error checking password: {e}")
        return False

def create_user(username, password):
    """
    Creates a new user with a hashed password.
    """
    try:
        db = get_database()
        hashed_password = hash_password(password)
        if hashed_password:
            db.users.insert_one({'username': username, 'password': hashed_password})
            print("User created successfully.")
        else:
            print("Failed to create user due to password hashing issue.")
    except Exception as e:
        print(f"Error creating user: {e}")

def get_user(username):
    """
    Retrieves a user by username.
    """
    try:
        db = get_database()
        user = db.users.find_one({'username': username})
        return user
    except Exception as e:
        print(f"Error retrieving user: {e}")
        return None