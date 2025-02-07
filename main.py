from app import app
from bot import start_bot
import threading
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Start the Discord bot in a separate thread
        logger.info("Starting Discord bot...")
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()

        # Start the Flask web server
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise