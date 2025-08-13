import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote
from typing import Optional, Dict, Any
import logging
from fake_useragent import UserAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LyricsScraper:
    def __init__(self, timeout: int = 10, delay: float = 1.5):
        """
        Initialize the lyrics scraper.
        
        Args:
            timeout: Request timeout in seconds
            delay: Delay between requests to be respectful
        """
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': UserAgent.random
        })
    
    def _clean_text_for_url(self, text: str) -> str:
        """Clean and format text for use in URLs."""
        # Remove special characters and replace spaces with hyphens
        cleaned = re.sub(r'[^\w\s-]', '', text.lower())
        cleaned = re.sub(r'\s+', '-', cleaned.strip())
        # Remove multiple consecutive hyphens
        cleaned = re.sub(r'-+', '-', cleaned)
        return cleaned.strip('-')
    
    def _extract_lyrics_content(self, lyrics_container) -> str:
        """Extract lyrics content from a container element, properly handling nested elements."""
        lyrics_parts = []
        
        def process_element(element):
            """Recursively process elements to handle nested structures."""
            if isinstance(element, str):
                text = element.strip()
                if text:
                    lyrics_parts.append(text)
            elif hasattr(element, 'name'):
                if element.name == 'br':
                    lyrics_parts.append('\n')
                elif element.name in ['span', 'div', 'p', 'a']:
                    # Process children recursively for nested elements
                    for child in element.contents:
                        process_element(child)
                else:
                    # For other elements, process their children
                    for child in element.contents:
                        process_element(child)
        
        # Process all contents recursively
        for element in lyrics_container.contents:
            process_element(element)
        
        return ''.join(lyrics_parts)
    
    def _clean_lyrics(self, raw_lyrics: str) -> str:
        """Clean the extracted lyrics text."""
        if not raw_lyrics:
            return ""
        
        # Remove content within brackets (like [Verse 1], [Chorus], etc.)
        cleaned = re.sub(r'\[.*?\]', '', raw_lyrics)
        
        # Remove extra whitespace and normalize line breaks
        lines = [line.strip() for line in cleaned.split('\n')]
        non_empty_lines = [line for line in lines if line]
        
        return '\n'.join(non_empty_lines)
    
    def get_lyrics_from_url(self, url: str) -> Optional[str]:
        """
        Extract lyrics from a given Genius URL.
        
        Args:
            url: The Genius URL to scrape
            
        Returns:
            The lyrics text or None if not found
        """
        try:
            logger.info(f"Fetching lyrics from: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple selectors as Genius may change their structure
            selectors = [
                "div[data-lyrics-container='true']",
                "div[class*='lyrics']",
                "div[class*='Lyrics']"
            ]
            
            lyrics_containers = []
            for selector in selectors:
                lyrics_containers = soup.select(selector)
                if lyrics_containers:
                    break
            
            if not lyrics_containers:
                logger.warning("No lyrics containers found on the page")
                return None
            
            # Extract and combine lyrics from all containers
            all_lyrics = []
            for container in lyrics_containers:
                lyrics_content = self._extract_lyrics_content(container)
                if lyrics_content:
                    all_lyrics.append(lyrics_content)
            
            if not all_lyrics:
                logger.warning("No lyrics content found in containers")
                return None
            
            combined_lyrics = '\n'.join(all_lyrics)
            cleaned_lyrics = self._clean_lyrics(combined_lyrics)
            
            if cleaned_lyrics:
                logger.info("Successfully extracted lyrics")
                return cleaned_lyrics
            else:
                logger.warning("Lyrics were empty after cleaning")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def get_lyrics(self, artist: str, song_name: str) -> Dict[str, Any]:
        """
        Get lyrics for a song by artist and song name.
        
        Args:
            artist: The artist name
            song_name: The song name
            
        Returns:
            Dictionary with either 'lyrics' or 'error' key
        """
        if not artist or not song_name:
            return {"error": "Artist and song name are required"}
        
        # Clean and format the artist and song name for the URL
        clean_artist = self._clean_text_for_url(artist)
        clean_song = self._clean_text_for_url(song_name)
        
        if not clean_artist or not clean_song:
            return {"error": "Unable to format artist or song name for URL"}
        
        # Construct the Genius URL
        url = f"https://genius.com/{clean_artist}-{clean_song}-lyrics"
        
        # Add delay to be respectful to the server
        time.sleep(self.delay)
        
        lyrics = self.get_lyrics_from_url(url)
        
        if lyrics:
            return {
                "lyrics": lyrics,
                "artist": artist,
                "song": song_name,
                "url": url
            }
        else:
            # Try alternative URL format if the first one fails
            alt_url = f"https://genius.com/{quote(artist.lower())}-{quote(song_name.lower())}-lyrics"
            logger.info(f"Trying alternative URL format: {alt_url}")
            
            time.sleep(self.delay)
            lyrics = self.get_lyrics_from_url(alt_url)
            
            if lyrics:
                return {
                    "lyrics": lyrics,
                    "artist": artist,
                    "song": song_name,
                    "url": alt_url
                }
            
            return {
                "error": f"Could not find lyrics for '{song_name}' by '{artist}'. Tried URLs: {url}, {alt_url}"
            }
    
    def close(self):
        """Close the session."""
        self.session.close()

# Convenience functions for backward compatibility
def get_lyrics_from_url(url: str) -> Optional[str]:
    """Legacy function for backward compatibility."""
    scraper = LyricsScraper()
    try:
        return scraper.get_lyrics_from_url(url)
    finally:
        scraper.close()

def get_lyrics(artist: str, song_name: str) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    scraper = LyricsScraper()
    try:
        return scraper.get_lyrics(artist, song_name)
    finally:
        scraper.close()

# Example usage
if __name__ == "__main__":
    scraper = LyricsScraper()
    
    try:
        # Example usage
        result = scraper.get_lyrics("The Beatles", "Hey Jude")
        
        if "lyrics" in result:
            print(f"Lyrics for '{result['song']}' by '{result['artist']}':")
            print("-" * 50)
            print(result["lyrics"])
        else:
            print(f"Error: {result['error']}")
    
    finally:
        scraper.close()