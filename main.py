from app import app, db # Added db import
from bot import start_bot
import threading
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Initialize database once before starting services
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")

        # Start the Discord bot in a separate thread
        logger.info("Starting Discord bot...")
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()

        # Start the Flask web server
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise