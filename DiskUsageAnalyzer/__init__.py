import os
import sys

from flask import Flask
from flask_socketio import SocketIO

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(PACKAGE_DIR, "templates"),
    static_folder=os.path.join(PACKAGE_DIR, "static"),
)

if load_dotenv:
    load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

SCAN_RESULTS = {}
SCAN_ERRORS = {}

PROJECT_ROOT = os.path.dirname(PACKAGE_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

