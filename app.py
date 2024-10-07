from flask import Flask, request
from telegram import Bot
from telegram.error import TelegramError
import spacy
import requests
import os
from dotenv import load_dotenv
import logging
import asyncio
import aiohttp

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Load Telegram bot token and Google Books API key from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GOOGLE_BOOKS_API_KEY = os.getenv('GOOGLE_BOOKS_API_KEY')

if not TELEGRAM_TOKEN or not GOOGLE_BOOKS_API_KEY:
    logging.error("Missing environment variables for Telegram token or Google Books API key.")
    exit(1)

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)

# Initialize SpaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Google Books API endpoint
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

# Function to query Google Books API with extracted keywords
def get_books(query):
    params = {
        'q': query,
        'maxResults': 10,
        'printType': 'books',
        
        'key': GOOGLE_BOOKS_API_KEY
    }
    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching books: {e}")
        return []

# Asynchronous function to send messages using aiohttp
async def async_send_message(chat_id, text):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage', json={'chat_id': chat_id, 'text': text}) as response:
            if response.status != 200:
                logging.error(f"Failed to send message, status: {response.status}")
            else:
                logging.info(f"Message sent successfully to {chat_id}")

# Function to extract keywords from user input
def extract_keywords(user_text):
    doc = nlp(user_text)
    return [chunk.text for chunk in doc.noun_chunks]

# Telegram webhook endpoint to receive messages
@app.route('/webhook', methods=['POST'])
async def webhook():
    data = request.get_json()
    logging.info("Received data: %s", data)

    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_text = data['message']['text']

        keywords = extract_keywords(user_text)

        if keywords:
            search_query = ' '.join(keywords)
            books = get_books(search_query)

            if books:
                response_text = "Here are top books from the internet:\n"
                for book in books:  # Limit to 5 books
                    title = book['volumeInfo'].get('title', 'No Title')
                    authors = ', '.join(book['volumeInfo'].get('authors', ['Unknown Author']))
                    info_link = book['volumeInfo'].get('infoLink', 'No Link Available')  # Get the link
                    response_text += f"-- {title} by {authors}\nLink({info_link})\n\n"  # Include link
            else:
                response_text = "Sorry, I couldn't find any books on that topic."
        else:
            response_text = "I couldn't extract any topics from your query. Please try again."

        # Send the response message asynchronously
        await async_send_message(chat_id, response_text)

    return "OK", 200

# Main function to run the Flask app
if __name__ == '__main__':
    app.run(port=5000, debug=True)
