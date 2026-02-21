import sys
import os
from pathlib import Path

# Add the project root to sys.path to allow importing 'backend'
# Path(__file__).resolve().parent.parent points to the root directory
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.main import app
