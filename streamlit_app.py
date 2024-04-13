import streamlit as st
import requests

# Function to fetch inspiration words from Flask backend
def fetch_inspiration_words():
    try:
        response = requests.get("http://localhost:8000/inspiration")
        if response.status_code == 200:
            return response.json()["words"]
        else:
            st.error("Failed to fetch inspiration words")
            return [], []
    except Exception as e:
        st.error(f"An error occurred while fetching inspiration words: {str(e)}")
        st.error(f"Error details: {e}")
        return [], []

# Function to send user's thought to the backend
def submit_thought(inspiration_words, raw_text):
    data = {
        "inspiration_words": inspiration_words,
        "raw_text": raw_text
    }
    try:
        response = requests.post("http://localhost:8000/thoughts", json=data)
        if response.status_code == 200:
            st.success("Your thought has been successfully saved!")
        else:
            st.error("Failed to save your thought")
    except Exception as e:
        st.error(f"An error occurred while submitting your thought: {str(e)}")
        st.error(f"Error details: {e}")

# New function to fetch all thoughts
def fetch_all_thoughts():
    try:
        response = requests.get("http://localhost:8000/thoughts")
        if response.status_code == 200:
            return response.json()["thoughts"]
        else:
            st.error("Failed to fetch thoughts")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching thoughts: {str(e)}")
        return []

# Function to send a search query to the backend and receive similar thoughts
def send_search_query(query):
    try:
        response = requests.post("http://localhost:8000/search_thoughts", json={"query": query})
        if response.status_code == 200:
            return response.json()["similar_thoughts"]
        else:
            st.error("Failed to retrieve search results")
            return []
    except Exception as e:
        st.error(f"An error occurred while retrieving search results: {str(e)}")
        return []

# Modify the Streamlit UI to include the thought retrieval page
def display_thoughts_page():
    st.title('Retrieve Your Thoughts')
    thoughts = fetch_all_thoughts()
    if thoughts:
        for thought in thoughts:
            with st.expander(f"Inspired by: {', '.join(thought['inspiration_words'])}"):
                st.write(thought["raw_text"])
    else:
        st.write("No thoughts available to display.")

# Modify the Streamlit UI to include the search functionality
def display_search_page():
    st.title('Search Your Thoughts')
    query = st.text_input("Enter your search query:", "")
    search_button = st.button("Search")

    if search_button and query:
        similar_thoughts = send_search_query(query)
        if similar_thoughts:
            for thought in similar_thoughts:
                with st.expander(f"Inspired by: {', '.join(thought['inspiration_words'])}"):
                    st.write(thought["raw_text"])
        else:
            st.write("No similar thoughts found.")

# Conditional rendering based on user navigation
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Submit Thought", "Retrieve Thoughts", "Search Thoughts"])

    if page == "Submit Thought":
        st.title('Outter-Monologue')
        # Fetch and display inspiration words
        inspiration_words = fetch_inspiration_words()
        if inspiration_words:
            st.write(f"Today's inspiration words are: {', '.join(inspiration_words)}")
        else:
            st.write("No inspiration words available today.")
        # User input for thoughts
        user_thought = st.text_area("What are your thoughts?", "")
        submit_button = st.button("Submit")
        # Process submission
        if submit_button and user_thought:
            submit_thought(inspiration_words, user_thought)
    elif page == "Retrieve Thoughts":
        display_thoughts_page()
    elif page == "Search Thoughts":
        display_search_page()

if __name__ == "__main__":
    main()