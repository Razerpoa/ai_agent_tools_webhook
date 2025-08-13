from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from dotenv import load_dotenv
from fake_useragent import UserAgent
import os
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
session_id = os.getenv("SESSIONID")

if not session_id or session_id == "your_session_id_here":
    logging.error("Please set your SESSIONID in the .env file.")
    exit()

def get_song_data():
    logging.info("Initializing WebDriver...")
    # Initialize WebDriver
    chrome_options = Options()
    chrome_options.add_argument(f'user-agent={UserAgent.random}')
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    logging.info("WebDriver initialized.")

    try:
        logging.info("Navigating to instagram.com...")
        # Go to instagram.com first
        driver.get("https://www.instagram.com/")
        logging.info("Adding session cookie...")
        # Add sessionid cookie to log in
        driver.add_cookie({
            "name": "sessionid",
            "value": session_id,
            "domain": ".instagram.com",
        })

        logging.info("Navigating to inbox...")
        # Go to the inbox
        driver.get("https://www.instagram.com/direct/inbox/")
        wait = WebDriverWait(driver, 30)

        # Handle "Turn on Notifications" popup
        try:
            not_now_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
            not_now_button.click()
            logging.info("Dismissed notification popup.")
            time.sleep(3) # Wait for inbox to load
        except:
            logging.info("No notification popup found or an error occurred.")


        wait.until(EC.url_contains("inbox"))
        logging.info("Successfully navigated to Instagram inbox.")

        results = []

        logging.info("Searching for song notes...")
        try:
            song_notes = driver.find_elements(By.XPATH, "//li[contains(@class, '_acaz')]")
            logging.info(f"Found {len(song_notes)} potential song notes.")

            for note in song_notes:
                try:
                    # Get user name from img alt text
                    user_img = note.find_element(By.TAG_NAME, "img")
                    alt_text = user_img.get_attribute("alt")
                    # The alt text is usually "USERNAME's profile picture"
                    user_name = alt_text.split("'s profile picture")[0]

                    # Get song and artist
                    song_div = note.find_element(By.XPATH, ".//div[@class='x6s0dn4 x78zum5 x1n2onr6']")
                    song_title = song_div.text.strip()

                    artist_span = note.find_element(By.XPATH, ".//span[@class='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1roi4f4']")
                    artist_name = artist_span.text.strip()

                    # Get note
                    note_text = ""
                    try:
                        # This selector is more flexible and finds spans that HAVE these classes, among others.
                        potential_note_spans = note.find_elements(By.CSS_SELECTOR, "span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6")
                        for span in potential_note_spans:
                            text = span.text.strip()
                            # The artist name is also in a span with similar classes, so we exclude it.
                            if text and text != artist_name:
                                note_text = text
                                break
                    except Exception:
                        note_text = "" # Keep it safe

                    if not song_title or song_title == artist_name:
                        continue

                    result = {"user": user_name, "song": song_title, "artist": artist_name, "note": note_text}
                    results.append(result)
                    logging.info(f"Found song: {song_title} by {artist_name} for user {user_name}")

                except NoSuchElementException:
                    # If an element is not found, it's likely not a song note, so skip it.
                    continue
                except Exception as e:
                    logging.warning(f"Could not process a note: {e}")
                    continue

        except Exception as e:
            logging.error(f"An error occurred while searching for songs: {e}")

        driver.quit()
        logging.info("WebDriver quit.")

        # Process and print results
        if results:
            logging.info(f"Found {len(results)} songs. Grouping by user...")
            grouped_results = {}
            for result in results:
                user = result["user"]
                if user not in grouped_results:
                    grouped_results[user] = []
                grouped_results[user].append(result)

            logging.info("Finished processing all songs.")
            return grouped_results
        else:
            logging.info("No song notes found.")
            return {"message": "No song notes found."}

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return {"error": str(e)}


