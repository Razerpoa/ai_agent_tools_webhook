from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from logging_config import setup_logging

# Setup logging
setup_logging()

# Load environment variables
load_dotenv()

# Import tools
from tools.duckduckgo_search import search as duckduckgo_search
from tools.ig_inbox_song_automate import get_song_data
from tools.get_lyrics import get_lyrics
from tools.simple_song_history import save_song_history_from_webhook

app = Flask(__name__)

@app.route('/webhook/search', methods=['POST'])
def search_webhook():
    data = request.get_json()
    if not data or 'query' not in data or 'max_results' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400

    query = data['query']
    max_results = data['max_results']
    print(data)
    results = duckduckgo_search(query, int(max_results))
    return jsonify(results)

@app.route('/webhook/instagram', methods=['POST'])
def instagram_webhook():
    data = get_song_data()
    return jsonify(data)

@app.route('/webhook/get_lyrics', methods=['POST'])
def get_lyrics_webhook():
    data = request.get_json()
    if not data or 'artists' not in data or 'song_name' not in data:
        return jsonify({'error': 'Missing artists or song_name parameter'}), 400

    artists = data['artists']
    song_name = data['song_name']
    lyrics = get_lyrics(artists, song_name)
    return jsonify(lyrics)

@app.route('/webhook/song_note', methods=['POST'])
def song_note_webhook():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid payload'}), 400

    success = save_song_history_from_webhook(data)
    if success:
        return jsonify({'status': 'success', 'message': 'Song history saved.'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to save song history.'}), 500
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)