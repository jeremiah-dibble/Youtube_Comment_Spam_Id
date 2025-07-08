import logging
from app.ban_db import init_db
from app import create_app

app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)