import os
import sys

from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO

app = Flask(
    __name__,
    template_folder="DiskUsageAnalyzer/templates",
    static_folder="DiskUsageAnalyzer/static",
)
load_dotenv()
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

SCAN_RESULTS = {}
SCAN_ERRORS = {}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

