
import logging
import os

def setup_logging():
    """
    Configures logging for the entire application to output to a file.
    """
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Keep logging to console as well
        ]
    )
