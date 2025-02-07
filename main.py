from app import app
from bot import start_bot
import threading
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    # Start the Discord bot in a separate thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start the Flask web server
    app.run(host="0.0.0.0", port=5000, debug=True)
