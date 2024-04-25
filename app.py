from flask import Flask, session, request, redirect, url_for, render_template, flash, jsonify, g
from flask_session import Session
from flask_cors import CORS  # Added for CORS support
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import speech_recognition as sr
from pydub import AudioSegment
from bson.objectid import ObjectId
import io
# Removed bcrypt import here since hashing and checking are moved to models/user.py
from models.user import hash_password, check_password, create_user, get_user, update_user_inspiration, reset_active_user_inspiration_words
from inspiration_words import get_random_words  # Importing the get_random_words function    
from models.thoughts import create_thought, get_all_thoughts, search_thoughts
from utils.text_embedding import generate_text_embedding
from utils.langchain_controller import thought_cascade, ask_myself_gen_resp, create_analysis
from models.characters import character_str


app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes

load_dotenv()
MONGO_URI = os.getenv('MONGO_URI', os.getenv('MONGO_DB_URI'))

# Session configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'mongodb')
app.config['SESSION_MONGO_URI'] = os.getenv('SESSION_MONGO_URI', f'{MONGO_URI}/sessions')
Session(app)

# MongoDB connection setup
client = MongoClient(MONGO_URI)
db = client['outter_monologue']

@app.route('/')
def hello_world():
    try:
        app.logger.info('Hello World route was called')
        return 'Hello, World!'
    except Exception as e:
        app.logger.error('Error in Hello World route: %s', e)
        return 'An error occurred', 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if get_user(username):
            flash('Username already exists.')
            return redirect(url_for('register'))
        try:
            create_user(username, password)
            app.logger.info('User created successfully')
        except Exception as e:
            flash('An error occurred during registration.')
            app.logger.error('Error creating user: %s', e)
            return redirect(url_for('register'))
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and check_password(password, user['password']):
            session['user_id'] = str(user['_id'])
            app.logger.info('User logged in successfully')
            return redirect(url_for('hello_world'))  # Assuming 'hello_world' is the main page for now
        flash('Invalid username or password')
        app.logger.warning('Invalid login attempt')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    app.logger.info('User logged out successfully')
    return redirect(url_for('login'))

@app.route('/inspiration')
def inspiration():
    if not request.is_json:
        app.logger.error('Invalid request format')
        return jsonify({"error": "Invalid request format"}), 400
    try:
        user_id = ObjectId(session.get('user_id', None))
        user = db.users.find_one({'_id': user_id})
        data = request.get_json()
        if (not user.get('inspiration_words', None)) or (data.get('refresh', False)):
            words = get_random_words()
            update_user_inspiration(user_id, words)
            app.logger.info('Successfully generated new inspiration words')
        else:
            words = user.get('inspiration_words')
            app.logger.info('Successfully fetched inspiration words')
        return jsonify(words=words, user=str(user_id))
    except Exception as e:
        app.logger.error('Error fetching inspiration words: %s', e)
        return jsonify(error="An error occurred while fetching inspiration words"), 500

@app.route('/upload_voice', methods=['POST'])
def upload_voice():
    if 'audio' not in request.files:
        app.logger.error(f'No audio file provided: {request.files}')
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        app.logger.error('No selected file')
        return jsonify({"error": "No selected file"}), 400

    try:
        # Convert audio file to wav format
        audio = AudioSegment.from_file(audio_file)
        audio = audio.set_channels(1).set_frame_rate(16000)  # Ensure proper format for SpeechRecognition
        audio_bytes = io.BytesIO()
        audio.export(audio_bytes, format="wav")
        audio_bytes.seek(0)

        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_bytes) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

        app.logger.info('Voice recording processed successfully')
        return jsonify({"text": text}), 200
    except Exception as e:
        app.logger.error(f"Error processing voice recording: {str(e)}")
        return jsonify({"error": "Error processing the audio file"}), 500

@app.route('/thoughts', methods=['GET', 'POST'])
def thoughts():
    user_id = ObjectId(session.get('user_id', None))
    if request.method == 'GET':
        try:
            thoughts = get_all_thoughts(str(user_id))
            thought_list = []
            for thought in thoughts:
                thought_list.append({
                    'inspiration_words': thought['inspiration_words'],
                    'raw_text': thought['raw_text'],
                    'thought_embedding': thought['semantic_vector']
                })
            app.logger.info('Retrieved all thoughts from the database')
            return jsonify(thoughts=thought_list), 200
        except Exception as e:
            app.logger.error(f"Error retrieving thoughts: {str(e)}", exc_info=True)
            return jsonify({"error": "Error retrieving thoughts"}), 500

    if not request.is_json:
        app.logger.error('Invalid request format')
        return jsonify({"error": "Invalid request format"}), 400

    data = request.get_json()
    inspiration_words = data.get('inspiration_words')
    raw_text = data.get('raw_text')

    if not inspiration_words or not raw_text:
        app.logger.error('Missing required fields')
        return jsonify({"error": "Missing required fields"}), 400

    try:
        thought_embedding = generate_text_embedding(raw_text)
        thought_id = create_thought(str(user_id), inspiration_words, raw_text, thought_embedding)
        thought_cascade(str(user_id), thought_id, raw_text)
        reset_active_user_inspiration_words(user_id=user_id)
        app.logger.info('Thought saved successfully')
        return jsonify({"message": "Thought saved successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error saving thought: {str(e)}", exc_info=True)
        return jsonify({"error": "Error saving thought"}), 500

@app.route('/search_thoughts', methods=['POST'])
def search_thoughts_route():
    user_id = ObjectId(session.get('user_id', None))
    if not request.is_json:
        app.logger.error('Invalid request format')
        return jsonify({"error": "Invalid request format"}), 400

    data = request.get_json()
    query_text = data.get('query')

    if not query_text:
        app.logger.error('No query provided')
        return jsonify({"error": "No query provided"}), 400

    try:
        query_embedding = generate_text_embedding(query_text)
        similar_thoughts = search_thoughts(str(user_id), query_embedding, top_n=5)
        similar_thoughts_formatted = [
            {
                'id': str(thought['_id']),
                'inspiration_words': thought['inspiration_words'],
                'raw_text': thought['raw_text']
            } for thought in similar_thoughts
        ]
        app.logger.info('Search query processed successfully')
        return jsonify(similar_thoughts=similar_thoughts_formatted), 200
    except Exception as e:
        app.logger.error(f"Error processing search query: {str(e)}", exc_info=True)
        return jsonify({"error": "Error processing search query"}), 500

@app.route('/similar_analysis', methods=['POST'])
def similar_analysis():
    user_id = ObjectId(session.get('user_id', None))
    if not request.is_json:
        app.logger.error('Invalid request format')
        return jsonify({"error": "Invalid request format"}), 400

    data = request.get_json()
    query_text = data.get('query_text')

    if not query_text:
        app.logger.error('No query provided')
        return jsonify({"error": "No thought embedding provided"}), 400

    query_embedding = generate_text_embedding(query_text)

    try:
        similar_thoughts = search_thoughts(str(user_id), query_embedding, top_n=5, field="analysis_embedding")
        similar_thoughts_formatted = [
            {
                'id': str(thought['_id']),
                'inspiration_words': thought['inspiration_words'],
                'analysis': thought['analysis']
            } for thought in similar_thoughts
        ]
        app.logger.info('Similar thoughts retrieved successfully')
        return jsonify(similar_thoughts=similar_thoughts_formatted), 200
    except Exception as e:
        app.logger.error(f"Error retrieving similar thoughts: {str(e)}", exc_info=True)
        return jsonify({"error": "Error retrieving similar thoughts"}), 500

@app.route('/ask_myself', methods=['POST'])
def ask_myself():
    user_id = ObjectId(session.get('user_id', None))
    if not request.is_json:
        app.logger.error('Invalid request format')
        return jsonify({"error": "Invalid request format"}), 400

    data = request.get_json()
    query_text = data.get('query')

    # first, get the 5 most similar thoughts to the query
    query_embedding = generate_text_embedding(query_text)
    similar_thoughts = search_thoughts(str(user_id), query_embedding, top_n=5)
    similar_analysis = search_thoughts(str(user_id), query_embedding, top_n=5, field="analysis_embedding")
    characters = db.characters.find({'thoughts': {"$in": [thought['_id'] for thought in similar_thoughts]}})
    
    if not similar_thoughts or not similar_analysis:
        app.logger.error('Missing required fields')
        return jsonify({"error": "Missing required fields"}), 400

        # feed the query and similar thoughts to langchain
    try:
        response = ask_myself_gen_resp(query_text, similar_thoughts, similar_analysis, characters)
        app.logger.info('Response generated successfully')
        return jsonify({"response": response}), 200
    except Exception as e:
        app.logger.error(f"Error asking yourself: {str(e)}", exc_info=True)
        return jsonify({"error": "Error generating response"}), 500

@app.before_request
def before_request():
    # set the current user in the global namespace because streamlit doesnt have auth features
    # without this, requests from streamlit will not have a user_id
    session['user_id'] = os.getenv('USER_ID', None)
    
def update_inspiration_words():
    """
    Updates the inspiration words for all users every 24 hours.
    """
    try:
        users = db.users.find({})
        for user in users:
            words = get_random_words()
            update_user_inspiration(user['_id'], words)
        app.logger.info('Successfully updated inspiration words for all users')
    except Exception as e:
        app.logger.error(f"Error updating inspiration words: {str(e)}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=update_inspiration_words, trigger="interval", days=1)
scheduler.start()


if __name__ == '__main__':
    app.logger.info('Starting the Flask application on port 8000')
    app.run(port=8000)