"""Start the app: `make run` or `python -m app`. It serves the three screens at http://127.0.0.1:8765/ (change the port with RIKLR_PORT).

    python -m app            start the server and print the address
    python -m app --open     also open the page in your browser
"""
import sys

from app.ui.server import serve

if __name__ == "__main__":
    serve(open_browser="--open" in sys.argv)
