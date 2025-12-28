"""  
Ship Database Manager

SQLite-based storage with:
- Instant ship queries (<50ms)
- Background sync with configurable interval
- Full change tracking and audit log
- Smart sync (only new/changed ships)
"""
import sqlite3
import json
import logging
import threading
import time
import html
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

# Faction display name mapping
FACTION_DISPLAY_NAMES = {
    "Romulan Republic": "Romulan",
    "Klingon Empire": "Klingon",
    # Keep others as-is
}

def normalize_faction_name(faction: str) -> str:
    """Normalize faction names for display"""
    return FACTION_DISPLAY_NAMES.get(faction, faction)


class ShipDatabase:
    """