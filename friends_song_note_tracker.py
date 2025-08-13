import logging
import time
import sys
import os
import gc

# Add project root to the Python path to ensure modules are found
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from logging_config import setup_logging
from tools.ig_inbox_song_automate import get_song_data
from tools.simple_song_history import save_song_history_from_webhook

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the song retrieval and saving process in a loop.
    """
    while True:
        try:
            logger.info("Starting song retrieval process...")
            song_data = get_song_data()

            if song_data and "error" not in song_data and "message" not in song_data:
                logger.info("Song data retrieved successfully. Saving to history...")
                success = save_song_history_from_webhook(song_data)
                if success:
                    logger.info("Song history saved successfully.")
                else:
                    logger.error("Failed to save song history.")
            elif "error" in song_data:
                logger.error(f"An error occurred during song retrieval: {song_data['error']}")
            else:
                logger.info("No new song data found or message received.")

        except Exception as e:
            logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)

        # Sleep for 3 hours
        sleep_duration_hours = 3
        sleep_duration_seconds = sleep_duration_hours * 60 * 60
        logger.info(f"Waiting for {sleep_duration_hours} hours before the next run...")
        gc.collect()
        time.sleep(sleep_duration_seconds)

if __name__ == "__main__":
    main()
