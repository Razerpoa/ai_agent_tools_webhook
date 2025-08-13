
import json
import os
import logging
from datetime import datetime

# Get the logger instance
logger = logging.getLogger(__name__)

# Define the project's root directory by going up two levels from the current file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
JSON_FILE = os.path.join(DATA_DIR, 'songs_data.json')

def save_song_history_from_webhook(payload):
    """
    Saves song history from a webhook payload to the songs_data.json file.
    The JSON file will have a top-level 'last_updated' timestamp and a 'users' object.

    Args:
        payload (dict): A dictionary of users and their songs.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    logger.info("Attempting to save song history from webhook.")
    logger.info(f"Received payload: {payload}")
    
    try:
        if not os.path.exists(DATA_DIR):
            logger.info(f"Data directory not found. Creating directory: {DATA_DIR}")
            os.makedirs(DATA_DIR)

        if os.path.exists(JSON_FILE):
            logger.info(f"Loading existing data from {JSON_FILE}")
            with open(JSON_FILE, 'r') as f:
                try:
                    file_data = json.load(f)
                    user_data = file_data.get('users', {})
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from {JSON_FILE}. Starting with an empty structure.")
                    user_data = {}
        else:
            logger.info(f"JSON file not found at {JSON_FILE}. Starting with an empty structure.")
            user_data = {}

        if not payload or not isinstance(payload, dict):
            logger.error("Payload is empty or not a dictionary.")
            return False

        for username, songs in payload.items():
            logger.info(f"Processing user: {username}")
            if username not in user_data:
                user_data[username] = {
                    "songs-played": [],
                    "current-played": "",
                    "note": "",
                    "notes": []
                }

            for song_item in songs:
                song_string = f"{song_item['song']} by {song_item['artist']}"
                if "songs-played" not in user_data[username]:
                    user_data[username]["songs-played"] = []
                
                if song_string not in user_data[username]["songs-played"]:
                    logger.info(f"Adding new song for {username}: {song_string}")
                    user_data[username]["songs-played"].append(song_string)
                else:
                    logger.info(f"Song already exists for {username}, skipping: {song_string}")

                user_data[username]["current-played"] = song_string
                note = song_item.get("note", "")
                user_data[username]["note"] = note

                if "notes" not in user_data[username]:
                    user_data[username]["notes"] = []
                
                if note and note not in user_data[username]["notes"]:
                    logger.info(f"Adding new note for {username}: {note}")
                    user_data[username]["notes"].append(note)
                elif note:
                    logger.info(f"Note already exists for {username}, skipping: {note}")

        # Prepare the final data structure with a top-level timestamp
        output_data = {
            "last_updated": datetime.now().isoformat(),
            "users": user_data
        }

        logger.info(f"Writing updated data to {JSON_FILE}")
        with open(JSON_FILE, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        logger.info("Successfully saved song history.")
        return True
        
    except Exception as e:
        logger.error(f"An error occurred while saving song history: {e}", exc_info=True)
        return False
