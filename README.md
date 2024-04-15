# Outter-Monologue

Outter-Monologue is an innovative app designed to store and process user memories over time. Inspired by daily random words, users can input their thoughts through voice or text, which are then converted, processed, and stored for future reflection.

## Overview

The app is built using Python Flask for the backend, MongoDB as the database, and Streamlit for an interactive frontend. The architecture supports user authentication, thought inspiration through random word generation, and input processing including voice-to-text conversion and semantic analysis.

### Project Structure

- Flask app (`app.py`) for handling backend logic and routing.
- MongoDB for storing user data and thoughts.
- Streamlit (`streamlit.cmd`) for frontend interaction.
- Semantic vector embedding using Hugging Face transformers for thought analysis.

## Features

- Daily thought inspiration through two random words.
- Voice or text input for capturing thoughts.
- Semantic analysis of thoughts for deeper insights.
- History browsing and thought retrieval based on similarity.

## Getting started

### Requirements

- Python 3.10 or newer
- MongoDB
- Dependencies listed in `requirements.txt`

### Quickstart

1. Clone the repository and navigate into the project directory.
    - create a .env file, copying the .env-example and filling in the required keys and uri's
        - user id will be left blank until below
2. Install the required Python dependencies: `pip install -r requirements.txt`
3. Start the Flask app: `flask run -p 8000`
    - Go to the backend url: http://localhost:8000/register
    - create new account
    - go to mongo db(via compass/mongosh/atlas) and retrieve the user id created in the db
    - add the string to your .env file
4. Open a new terminal and launch the Streamlit frontend: `streamlit run streamlit_app.py`

## License

Copyright (c) 2024.