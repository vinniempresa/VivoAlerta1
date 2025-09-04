import logging
from app import app

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Garantir que o app esteja acessível para o gunicorn
# Mesmo que não seja executado como __main__

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
