"""  
Ship Database Manager

SQLite-based storage with:
- Instant ship queries (<50ms)
- Background sync with configurable interval
- Full change tracking and audit log
- Smart sync (only new/changed ships)
"""
import sqlite3
import re
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


class ShipDatabase:
    """
    SQLite database for ship data with change tracking
    
    Features:
    - Sub-50ms query performance
    - Automatic background sync (configurable interval)
    - Full audit log of all changes
    - Smart sync (only updates changed ships)
    """
    
    def __init__(self, db_path: str = "ships.db", sync_interval_hours: int = 12):
        """
        Initialize database
        
        Args:
            db_path: Path to SQLite database file
            sync_interval_hours: Hours between automatic syncs (default 8)
        """
        self.db_path = db_path
        self.sync_interval_hours = sync_interval_hours
        self._sync_thread = None
        self._stop_sync = threading.Event()
        
        self.init_db()
        logger.info(f"Database initialized: {db_path} (sync interval: {sync_interval_hours}h)")
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name_raw TEXT,
                
                -- Faction
                faction TEXT,  -- JSON array
                factionlede TEXT,
                
                -- Basic Info
                tier INTEGER,
                type TEXT,  -- JSON array
                rank TEXT,
                cost TEXT,
                
                -- Display
                displayprefix TEXT,
                displayclass TEXT,
                displaytype TEXT,
                
                -- Stats
                hull INTEGER,
                hullmod REAL,
                shieldmod REAL,
                turnrate REAL,
                impulse REAL,
                inertia REAL,
                
                -- Weapons
                fore INTEGER,
                aft INTEGER,
                equipcannons TEXT,
                
                -- Consoles
                consolestac INTEGER,
                consoleseng INTEGER,
                consolessci INTEGER,
                consolesuni INTEGER,
                
                -- Equipment
                hangars INTEGER,
                -- Media / metadata
                image TEXT,
                image2 TEXT,
                released TEXT,
                internalname TEXT,
                fc TEXT,
                facsort TEXT,

                -- Bridge Officers
                boffs TEXT,
                
                -- Abilities
                abilities TEXT,
                
                -- Admiralty
                admiraltyeng INTEGER,
                admiraltytac INTEGER,
                admiraltysci INTEGER,
                
                -- Links
                wiki_url TEXT,
                
                -- Metadata
                data_hash TEXT,  -- Hash of all data for change detection
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes for fast queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_faction ON ships(faction)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier ON ships(tier)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON ships(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_updated ON ships(updated_at)")
        
        # Change log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ship_name TEXT NOT NULL,
                change_type TEXT NOT NULL,  -- 'created', 'updated', 'deleted'
                changed_fields TEXT,  -- JSON array of changed field names
                old_values TEXT,  -- JSON object with old values
                new_values TEXT,  -- JSON object with new values
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (ship_name) REFERENCES ships(name) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_change_timestamp ON change_log(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_change_ship ON change_log(ship_name)")
        
        # Sync status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_full_sync TIMESTAMP,
                last_partial_sync TIMESTAMP,
                is_syncing BOOLEAN DEFAULT 0,
                total_ships INTEGER DEFAULT 0,
                sync_interval_hours INTEGER DEFAULT 8,
                ships_added INTEGER DEFAULT 0,
                ships_updated INTEGER DEFAULT 0,
                ships_deleted INTEGER DEFAULT 0,
                last_sync_duration_seconds INTEGER DEFAULT 0
            )
        """)
        
        # Initialize sync status if not exists
        cursor.execute("""
                INSERT OR IGNORE INTO sync_status (id, sync_interval_hours) 
            VALUES (1, ?)
        """, (self.sync_interval_hours,))
        
        conn.commit()
        conn.close()
        
        logger.info("Database schema initialized")

        # Ensure new columns exist in older databases by attempting to add them
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            extra_columns = [
                ("display_name_raw", "TEXT"),
                ("ranklevel", "INTEGER"),
                ("upgradecost", "TEXT"),
                ("powerall", "REAL"),
                ("powerweapons", "REAL"),
                ("powershields", "REAL"),
                ("powerengines", "REAL"),
                ("powerauxiliary", "REAL"),
                ("powerboost", "REAL"),
                ("devices", "TEXT"),
                ("uniconsole", "INTEGER"),
                ("t5uconsole", "INTEGER"),
                ("experimental", "TEXT"),
                ("secdeflector", "TEXT"),
                ("image", "TEXT"),
                ("image2", "TEXT"),
                ("released", "TEXT"),
                ("internalname", "TEXT"),
                ("fc", "TEXT"),
                ("facsort", "TEXT"),
            ]

            for col, coltype in extra_columns:
                try:
                    cursor.execute(f"ALTER TABLE ships ADD COLUMN {col} {coltype}")
                except Exception:
                    # ignore if column already exists or cannot be added
                    pass

            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def _hash_ship_data(self, ship: Dict) -> str:
        """Generate hash of ship data for change detection"""
        # Remove metadata fields
        data = {k: v for k, v in ship.items() 
                if k not in ['created_at', 'updated_at', 'data_hash', 'id']}
        
        # Sort keys for consistent hashing
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _detect_changes(self, old_ship: Dict, new_ship: Dict) -> tuple[List[str], Dict, Dict]:
        """Detect which fields changed"""
        changed_fields = []
        old_values = {}
        new_values = {}
        
        for key in new_ship.keys():
            if key in ['created_at', 'updated_at', 'data_hash', 'id']:
                continue
            
            old_val = old_ship.get(key)
            new_val = new_ship.get(key)
            
            if old_val != new_val:
                changed_fields.append(key)
                old_values[key] = old_val
                new_values[key] = new_val
        
        return changed_fields, old_values, new_values
    
    def _log_change(self, ship_name: str, change_type: str, 
                    changed_fields: List[str] = None, 
                    old_values: Dict = None, 
                    new_values: Dict = None):
        """Log a change to the audit log"""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            INSERT INTO change_log (ship_name, change_type, changed_fields, old_values, new_values)
            VALUES (?, ?, ?, ?, ?)
        """, (
            ship_name,
            change_type,
            json.dumps(changed_fields) if changed_fields else None,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Change logged: {change_type} - {ship_name}")
    
    def get_ships(self, faction: Optional[str] = None, 
                  tier: Optional[int] = None, 
                  limit: Optional[int] = None) -> List[Dict]:
        """
        Get ships from database (instant response)
        
        Args:
            faction: Filter by faction key (e.g., 'federation', 'klingon')
            tier: Filter by tier
            limit: Maximum results (None = all ships)
        
        Returns:
            List of ship dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM ships WHERE 1=1"
        params = []
        
        # Filter by faction in SQL using LIKE on JSON array
        if faction:
            faction_map = {
                "federation": ["Federation"],
                "klingon": ["Klingon", "Klingon Empire"],
                "romulan": ["Romulan Republic", "Romulan"],
                "dominion": ["Dominion"],
                "cross-faction": ["Cross-Faction"]
            }
            
            target_factions = faction_map.get(faction.lower(), [])
            
            # Build OR conditions for all target faction names
            if target_factions:
                faction_conditions = []
                for faction_name in target_factions:
                    faction_conditions.append("faction LIKE ?")
                    params.append(f'%"{faction_name}"%')
                
                query += f" AND ({' OR '.join(faction_conditions)})"
        
        # Filter by tier
        if tier:
            query += " AND tier = ?"
            params.append(tier)
        
        query += " ORDER BY name"
        
        # Add limit only if specified
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = conn.execute(query, params)
        ships = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse JSON fields and add computed properties
        for ship in ships:
            # Parse type
            if ship.get('type'):
                ship['type'] = json.loads(ship['type'])
            else:
                ship['type'] = []

            # Parse devices (may be stored as JSON list or comma-separated string)
            if ship.get('devices'):
                try:
                    dev = json.loads(ship['devices'])
                    ship['devices'] = dev if isinstance(dev, list) else [dev]
                except Exception:
                    # fallback: split on commas/semicolons
                    ship['devices'] = [d.strip() for d in re.split(r'[,;]', ship['devices']) if d.strip()]
            else:
                ship['devices'] = []
            
            # Parse faction
            if ship.get('faction'):
                try:
                    faction_data = json.loads(ship['faction'])
                    if isinstance(faction_data, list):
                        ship['faction'] = faction_data
                    else:
                        ship['faction'] = [faction_data]
                except:
                    ship['faction'] = [ship['faction']] if ship['faction'] else []
            else:
                ship['faction'] = []
            
            # Set factionlede from first faction for display
            if ship['faction']:
                ship['factionlede'] = ship['faction'][0]
            elif ship.get('factionlede'):
                # Keep existing factionlede if present
                pass
            else:
                ship['factionlede'] = None
            
            # Add computed fields
            ship['can_use_cannons'] = ship.get('equipcannons') == 'yes'
            ship['total_consoles'] = (
                (ship.get('consolestac') or 0) +
                (ship.get('consoleseng') or 0) +
                (ship.get('consolessci') or 0) +
                (ship.get('consolesuni') or 0)
            )
            ship['total_weapons'] = (ship.get('fore') or 0) + (ship.get('aft') or 0)
            ship['has_hangar'] = (ship.get('hangars') or 0) > 0
            ship['is_carrier'] = (ship.get('hangars') or 0) >= 2
            ship['has_experimental_weapon'] = False  # TODO: Add to schema
            ship['has_secondary_deflector'] = False  # TODO: Add to schema
            
            # Build display_name
            parts = []
            if ship.get('displayprefix'):
                parts.append(ship['displayprefix'])
            if ship.get('displayclass'):
                parts.append(ship['displayclass'])
            if ship.get('displaytype'):
                parts.append(ship['displaytype'])
            ship['display_name'] = ' '.join(parts) if parts else ship['name']

            # Normalize new bulk fields to ensure API consistency
            # Images / metadata
            ship['image'] = ship.get('image')
            ship['image2'] = ship.get('image2')
            ship['released'] = ship.get('released')
            ship['internalname'] = ship.get('internalname')
            ship['fc'] = ship.get('fc')
            ship['facsort'] = ship.get('facsort')

            # Power stats (ensure floats or None)
            for p in ('powerall', 'powerweapons', 'powershields', 'powerengines', 'powerauxiliary', 'powerboost'):
                val = ship.get(p)
                try:
                    ship[p] = float(val) if val is not None and val != '' else None
                except Exception:
                    ship[p] = None

            # Rank / upgrade
            try:
                ship['ranklevel'] = int(ship['ranklevel']) if ship.get('ranklevel') not in (None, '') else None
            except Exception:
                ship['ranklevel'] = None
            ship['upgradecost'] = ship.get('upgradecost')

            # Devices (ensure list)
            if 'devices' in ship and ship['devices'] is not None:
                if isinstance(ship['devices'], str):
                    try:
                        ship['devices'] = json.loads(ship['devices'])
                    except Exception:
                        ship['devices'] = [d.strip() for d in re.split(r'[,;]', ship['devices']) if d.strip()]
                elif not isinstance(ship['devices'], list):
                    ship['devices'] = [ship['devices']]
            else:
                ship['devices'] = []

            # Flags / extra fields
            ship['uniconsole'] = ship.get('uniconsole')
            ship['t5uconsole'] = ship.get('t5uconsole')
            ship['experimental'] = ship.get('experimental')
            ship['secdeflector'] = ship.get('secdeflector')
        
        return ships
    
    def get_ship_by_name(self, name: str) -> Optional[Dict]:
        """Get single ship by name"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("SELECT * FROM ships WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            ship = dict(row)
            ship['type'] = json.loads(ship['type']) if ship['type'] else []
            ship['faction'] = json.loads(ship['faction']) if ship['faction'] else []

            # Normalize additional fields similar to get_ships
            ship['image'] = ship.get('image')
            ship['image2'] = ship.get('image2')
            ship['released'] = ship.get('released')
            ship['internalname'] = ship.get('internalname')
            ship['fc'] = ship.get('fc')
            ship['facsort'] = ship.get('facsort')

            for p in ('powerall', 'powerweapons', 'powershields', 'powerengines', 'powerauxiliary', 'powerboost'):
                val = ship.get(p)
                try:
                    ship[p] = float(val) if val is not None and val != '' else None
                except Exception:
                    ship[p] = None

            try:
                ship['ranklevel'] = int(ship['ranklevel']) if ship.get('ranklevel') not in (None, '') else None
            except Exception:
                ship['ranklevel'] = None
            ship['upgradecost'] = ship.get('upgradecost')

            if 'devices' in ship and ship['devices'] is not None:
                if isinstance(ship['devices'], str):
                    try:
                        ship['devices'] = json.loads(ship['devices'])
                    except Exception:
                        ship['devices'] = [d.strip() for d in re.split(r'[,;]', ship['devices']) if d.strip()]
                elif not isinstance(ship['devices'], list):
                    ship['devices'] = [ship['devices']]
            else:
                ship['devices'] = []

            ship['uniconsole'] = ship.get('uniconsole')
            ship['t5uconsole'] = ship.get('t5uconsole')
            ship['experimental'] = ship.get('experimental')
            ship['secdeflector'] = ship.get('secdeflector')

            return ship
        
        return None
    
    def upsert_ship(self, ship_data: Dict) -> str:
        """
        Insert or update a ship, tracking changes
        
        Args:
            ship_data: Ship data dictionary
        
        Returns:
            Change type: 'created', 'updated', or 'unchanged'
        """
        name = ship_data['name']
        
        # Prepare data for database and restrict to existing table columns
        db_data = ship_data.copy()
        
        # Convert lists to JSON
        if 'type' in db_data:
            db_data['type'] = json.dumps(db_data['type'])
        if 'faction' in db_data:
            db_data['faction'] = json.dumps(db_data['faction'])
        # Devices may be a comma-separated string or a list; store as JSON if list
        if 'devices' in db_data and isinstance(db_data['devices'], (list, tuple)):
            db_data['devices'] = json.dumps(list(db_data['devices']))
        
        # Generate hash
        data_hash = self._hash_ship_data(db_data)
        db_data['data_hash'] = data_hash
        
        # Check if ship exists
        existing = self.get_ship_by_name(name)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get existing ship table columns and restrict db_data to those
        cursor.execute("PRAGMA table_info(ships)")
        cols = [r[1] for r in cursor.fetchall()]

        # Ensure we always include 'name' and 'data_hash'
        allowed = set(cols)
        filtered_db_data = {k: v for k, v in db_data.items() if k in allowed}

        if not existing:
            # Insert new ship (only allowed columns)
            fields = list(filtered_db_data.keys())
            placeholders = ','.join(['?' for _ in fields])

            cursor.execute(f"INSERT INTO ships ({','.join(fields)}) VALUES ({placeholders})",
                           [filtered_db_data[f] for f in fields])
            conn.commit()
            conn.close()

            # Log creation
            self._log_change(name, 'created', new_values=filtered_db_data)

            return 'created'

        else:
            # If hash unchanged, skip
            if existing.get('data_hash') == data_hash:
                conn.close()
                return 'unchanged'

            # Detect changes against existing data (use keys present in existing record)
            changed_fields, old_values, new_values = self._detect_changes(existing, filtered_db_data)

            # Update ship (only allowed columns)
            filtered_db_data['updated_at'] = datetime.now().isoformat()

            set_clause = ','.join([f"{f} = ?" for f in filtered_db_data.keys()])

            cursor.execute(f"UPDATE ships SET {set_clause} WHERE name = ?",
                           [filtered_db_data[f] for f in filtered_db_data.keys()] + [name])

            conn.commit()
            conn.close()

            # Log update
            self._log_change(name, 'updated', changed_fields, old_values, new_values)

            return 'updated'
    
    def delete_ship(self, name: str):
        """Delete a ship and log it"""
        ship = self.get_ship_by_name(name)
        if not ship:
            return
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM ships WHERE name = ?", (name,))
        conn.commit()
        conn.close()
        
        # Log deletion
        self._log_change(name, 'deleted', old_values=ship)
        
        logger.info(f"Ship deleted: {name}")
    
    def get_all_ship_names(self) -> List[str]:
        """Get list of all ship names in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT name FROM ships ORDER BY name")
        names = [row[0] for row in cursor.fetchall()]
        conn.close()
        return names
    
    def get_faction_summary(self) -> List[Dict]:
        """Get ship counts per faction by parsing faction JSON field"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT faction FROM ships WHERE faction IS NOT NULL")
        
        # Count ships per faction
        faction_counts = {}
        for row in cursor.fetchall():
            try:
                faction_data = json.loads(row[0])
                if isinstance(faction_data, list):
                    factions = faction_data
                else:
                    factions = [faction_data]
                
                for faction in factions:
                    if faction:
                        faction_counts[faction] = faction_counts.get(faction, 0) + 1
            except:
                pass
        
        conn.close()
        
        # Map faction names to keys and normalize display names
        faction_map = {
            "Federation": ("federation", "Federation"),
            "Klingon": ("klingon", "Klingon"),
            "Klingon Empire": ("klingon", "Klingon"),
            "Romulan Republic": ("romulan", "Romulan"),
            "Romulan": ("romulan", "Romulan"),
            "Dominion": ("dominion", "Dominion"),
            "Cross-Faction": ("cross-faction", "Cross-Faction")
        }
        
        # Merge counts for same faction keys
        merged_counts = {}
        for name, count in faction_counts.items():
            mapping = faction_map.get(name)
            if mapping:
                key, display_name = mapping
            else:
                key = name.lower().replace(' ', '-')
                display_name = name
            
            if key in merged_counts:
                merged_counts[key]['count'] += count
            else:
                merged_counts[key] = {
                    'name': display_name,
                    'key': key,
                    'count': count
                }
        
        # Build faction list sorted by count
        factions = sorted(merged_counts.values(), key=lambda x: -x['count'])
        
        return factions
    
    def get_change_history(self, limit: int = 100, ship_name: Optional[str] = None) -> List[Dict]:
        """
        Get change history
        
        Args:
            limit: Maximum number of changes to return
            ship_name: Optional filter by ship name
        
        Returns:
            List of change records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        if ship_name:
            query = "SELECT * FROM change_log WHERE ship_name = ? ORDER BY timestamp DESC LIMIT ?"
            params = (ship_name, limit)
        else:
            query = "SELECT * FROM change_log ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)
        
        cursor = conn.execute(query, params)
        changes = []
        
        for row in cursor.fetchall():
            change = dict(row)
            
            # Parse JSON fields
            if change['changed_fields']:
                change['changed_fields'] = json.loads(change['changed_fields'])
            if change['old_values']:
                change['old_values'] = json.loads(change['old_values'])
            if change['new_values']:
                change['new_values'] = json.loads(change['new_values'])
            
            changes.append(change)
        
        conn.close()
        return changes
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("SELECT * FROM sync_status WHERE id = 1")
        row = cursor.fetchone()
        
        if row:
            status = dict(row)
        else:
            status = {
                "last_full_sync": None,
                "is_syncing": False,
                "total_ships": 0,
                "sync_interval_hours": self.sync_interval_hours
            }
        
        # Calculate next sync time
        if status['last_full_sync']:
            last_sync = datetime.fromisoformat(status['last_full_sync'])
            next_sync = last_sync + timedelta(hours=status['sync_interval_hours'])
            status['next_sync'] = next_sync.isoformat()
            status['needs_sync'] = datetime.now() >= next_sync
        else:
            status['next_sync'] = None
            status['needs_sync'] = True
        
        # Get total ship count
        cursor = conn.execute("SELECT COUNT(*) FROM ships")
        status['total_ships'] = cursor.fetchone()[0]
        
        conn.close()
        return status
    
    def update_sync_status(self, **kwargs):
        """Update sync status"""
        conn = sqlite3.connect(self.db_path)
        
        set_parts = []
        values = []
        
        for key, value in kwargs.items():
            set_parts.append(f"{key} = ?")
            values.append(value)
        
        if set_parts:
            query = f"UPDATE sync_status SET {', '.join(set_parts)} WHERE id = 1"
            conn.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def needs_sync(self) -> bool:
        """Check if database needs syncing"""
        status = self.get_sync_status()
        return status.get('needs_sync', True)
    
    def start_background_sync(self, scraper):
        """Start background sync thread"""
        if self._sync_thread and self._sync_thread.is_alive():
            logger.warning("Background sync already running")
            return
        
        self._stop_sync.clear()
        self._sync_thread = threading.Thread(
            target=self._background_sync_worker,
            args=(scraper,),
            daemon=True
        )
        self._sync_thread.start()
        logger.info(f"Background sync started (interval: {self.sync_interval_hours}h)")
    
    def stop_background_sync(self):
        """Stop background sync thread"""
        self._stop_sync.set()
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        logger.info("Background sync stopped")
    
    def _background_sync_worker(self, scraper):
        """Background sync worker thread"""
        while not self._stop_sync.is_set():
            try:
                if self.needs_sync():
                    logger.info("Starting automatic background sync...")
                    # Use incremental bulk sync to apply only changed/new ships
                    self.incremental_sync(scraper)
            except Exception as e:
                logger.error(f"Background sync failed: {e}", exc_info=True)
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.sync_interval_hours * 3600):
                if self._stop_sync.is_set():
                    break
                time.sleep(1)
    
    def smart_sync(self, scraper):
        """
        Smart sync: Only update new/changed ships
        
        This is much faster than full sync!
        """
        start_time = time.time()
        
        # Mark as syncing
        self.update_sync_status(is_syncing=True)
        
        stats = {
            'added': 0,
            'updated': 0,
            'deleted': 0,
            'unchanged': 0
        }
        
        try:
            # Get all ship names from wiki (via Cargo API)
            logger.info("Fetching ship list from wiki...")
            wiki_ships = set(scraper.get_category_members(limit=1000))
            
            logger.info(f"Found {len(wiki_ships)} ships on wiki")
            
            # Get current database ships
            db_ships = set(self.get_all_ship_names())
            logger.info(f"Found {len(db_ships)} ships in database")
            
            # Find new ships
            new_ships = wiki_ships - db_ships
            if new_ships:
                logger.info(f"Found {len(new_ships)} new ships to add")
                for ship_name in new_ships:
                    try:
                        data = scraper.parse_ship_page(ship_name)
                        if data:
                            result = self.upsert_ship(data)
                            if result == 'created':
                                stats['added'] += 1
                    except Exception as e:
                        logger.error(f"Failed to add ship {ship_name}: {e}")
            
            # Check existing ships for updates (sample 10% for quick sync)
            import random
            sample_size = max(10, len(db_ships) // 10)
            sample_ships = random.sample(list(db_ships & wiki_ships), min(sample_size, len(db_ships & wiki_ships)))
            
            logger.info(f"Checking {len(sample_ships)} existing ships for updates...")
            for ship_name in sample_ships:
                try:
                    data = scraper.parse_ship_page(ship_name)
                    if data:
                        result = self.upsert_ship(data)
                        if result == 'updated':
                            stats['updated'] += 1
                        elif result == 'unchanged':
                            stats['unchanged'] += 1
                except Exception as e:
                    logger.error(f"Failed to update ship {ship_name}: {e}")
            
            # Find deleted ships
            deleted_ships = db_ships - wiki_ships
            if deleted_ships:
                logger.info(f"Found {len(deleted_ships)} ships to delete")
                for ship_name in deleted_ships:
                    try:
                        self.delete_ship(ship_name)
                        stats['deleted'] += 1
                    except Exception as e:
                        logger.error(f"Failed to delete ship {ship_name}: {e}")
            
            duration = int(time.time() - start_time)
            
            # Update sync status
            self.update_sync_status(
                last_full_sync=datetime.now().isoformat(),
                is_syncing=False,
                ships_added=stats['added'],
                ships_updated=stats['updated'],
                ships_deleted=stats['deleted'],
                last_sync_duration_seconds=duration
            )
            
            logger.info(f"Smart sync completed in {duration}s: "
                       f"{stats['added']} added, {stats['updated']} updated, "
                       f"{stats['deleted']} deleted, {stats['unchanged']} unchanged")
            
        except Exception as e:
            logger.error(f"Smart sync failed: {e}", exc_info=True)
            self.update_sync_status(is_syncing=False)
            raise
    
    def full_sync(self, scraper, use_bulk: bool = True):
        """
        Full sync: Parse all ships from wiki Cargo database
        
        Use this for initial setup or complete refresh.
        
        Strategy:
        1. Get ALL ship names from Cargo (fast, ~1-2 seconds)
        2. Parse each ship's data individually from Cargo
        """
        start_time = time.time()
        
        self.update_sync_status(is_syncing=True)
        
        stats = {'added': 0, 'updated': 0, 'unchanged': 0}
        
        try:
            if use_bulk and hasattr(scraper, 'get_all_ships_bulk'):
                try:
                    logger.info("Attempting bulk fetch of all ships from Cargo...")
                    all_ships = scraper.get_all_ships_bulk(limit=10000)

                    logger.info(f"Bulk fetch returned {len(all_ships)} ships")

                    # Upsert all ships
                    for i, ship_data in enumerate(all_ships, 1):
                        try:
                            logger.info(f"Upserting ship {i}/{len(all_ships)}: {ship_data.get('name')}")
                            result = self.upsert_ship(ship_data)
                            if result == 'created':
                                stats['added'] += 1
                            elif result == 'updated':
                                stats['updated'] += 1
                            elif result == 'unchanged':
                                stats['unchanged'] += 1
                        except Exception as e:
                            logger.error(f"Failed to upsert ship {ship_data.get('name')}: {e}", exc_info=True)

                    duration = int(time.time() - start_time)

                    self.update_sync_status(
                        last_full_sync=datetime.now().isoformat(),
                        is_syncing=False,
                        ships_added=stats['added'],
                        ships_updated=stats['updated'],
                        last_sync_duration_seconds=duration
                    )

                    logger.info(f"Bulk full sync completed in {duration}s: "
                               f"{stats['added']} added, {stats['updated']} updated, "
                               f"{stats['unchanged']} unchanged")
                    return
                except Exception as e:
                    logger.warning(f"Bulk fetch failed, falling back to per-ship parsing: {e}")

            # Fallback: original per-ship parsing flow
            logger.info("Fetching all ship names from Cargo (fallback path)...")
            all_ship_names = scraper.get_category_members(limit=1000)

            logger.info(f"Found {len(all_ship_names)} ships on wiki")

            # Get current database ship names for comparison
            db_ships = set(self.get_all_ship_names())
            logger.info(f"Found {len(db_ships)} ships in database")

            # Determine which ships are new
            new_ships = set(all_ship_names) - db_ships
            logger.info(f"Found {len(new_ships)} new ships to add")

            # Parse each ship from Cargo
            for i, ship_name in enumerate(all_ship_names, 1):
                try:
                    logger.info(f"Parsing ship {i}/{len(all_ship_names)}: {ship_name}")

                    ship_data = scraper.parse_ship_page(ship_name)

                    if ship_data:
                        result = self.upsert_ship(ship_data)

                        if result == 'created':
                            stats['added'] += 1
                        elif result == 'updated':
                            stats['updated'] += 1
                        elif result == 'unchanged':
                            stats['unchanged'] += 1
                    else:
                        logger.warning(f"No data returned for ship: {ship_name}")

                except Exception as e:
                    logger.error(f"Failed to sync ship {ship_name}: {e}", exc_info=True)

                # Small delay to avoid hammering the API
                time.sleep(0.05)
            
            duration = int(time.time() - start_time)
            
            self.update_sync_status(
                last_full_sync=datetime.now().isoformat(),
                is_syncing=False,
                ships_added=stats['added'],
                ships_updated=stats['updated'],
                last_sync_duration_seconds=duration
            )
            
            logger.info(f"Full sync completed in {duration}s: "
                       f"{stats['added']} added, {stats['updated']} updated, "
                       f"{stats['unchanged']} unchanged")
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}", exc_info=True)
            self.update_sync_status(is_syncing=False)
            raise

    def incremental_sync(self, scraper, use_bulk: bool = True, limit: int = 10000):
        """
        Incremental bulk sync: fetch bulk ship records and apply only changes.

        - Uses `scraper.get_all_ships_bulk()` when available to retrieve
          a compact representation of all ships.
        - Compares a deterministic data hash per-ship against the DB's
          `data_hash` and upserts only new/changed ships.
        - Removes ships that no longer appear in the bulk result.
        """
        start_time = time.time()

        # Mark as syncing
        self.update_sync_status(is_syncing=True)

        stats = {'added': 0, 'updated': 0, 'deleted': 0, 'unchanged': 0}

        try:
            if not use_bulk or not hasattr(scraper, 'get_all_ships_bulk'):
                logger.info("Bulk API unavailable; falling back to full sync")
                return self.full_sync(scraper, use_bulk=use_bulk)

            logger.info("Starting incremental bulk sync...")

            # Fetch bulk records
            bulk_ships = scraper.get_all_ships_bulk(limit=limit)
            logger.info(f"Bulk sync fetched {len(bulk_ships)} ships")

            # Load existing name->hash map
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT name, data_hash FROM ships")
            existing_hash = {row['name']: row['data_hash'] for row in cursor.fetchall()}
            conn.close()

            seen_names = set()

            for ship in bulk_ships:
                name = ship.get('name')
                if not name:
                    continue
                seen_names.add(name)

                # Prepare a shallow copy for hashing that matches upsert behavior
                temp = ship.copy()
                if 'type' in temp and isinstance(temp['type'], list):
                    temp['type'] = json.dumps(temp['type'])
                if 'faction' in temp and isinstance(temp['faction'], list):
                    temp['faction'] = json.dumps(temp['faction'])
                if 'devices' in temp and isinstance(temp['devices'], list):
                    temp['devices'] = json.dumps(temp['devices'])

                candidate_hash = self._hash_ship_data(temp)

                # If unchanged, skip upsert
                if existing_hash.get(name) == candidate_hash:
                    stats['unchanged'] += 1
                    continue

                # Otherwise upsert using the bulk record (will compute and store new hash)
                try:
                    res = self.upsert_ship(ship)
                    if res == 'created':
                        stats['added'] += 1
                    elif res == 'updated':
                        stats['updated'] += 1
                    elif res == 'unchanged':
                        stats['unchanged'] += 1
                except Exception as e:
                    logger.error(f"Failed to upsert ship {name} during incremental sync: {e}", exc_info=True)

            # Detect deletions: ships present in DB but not in bulk
            db_names = set(existing_hash.keys())
            deleted = db_names - seen_names
            for name in deleted:
                try:
                    self.delete_ship(name)
                    stats['deleted'] += 1
                except Exception as e:
                    logger.error(f"Failed to delete ship {name} during incremental sync: {e}", exc_info=True)

            duration = int(time.time() - start_time)

            # Update sync status (partial)
            self.update_sync_status(
                last_partial_sync=datetime.now().isoformat(),
                is_syncing=False,
                ships_added=stats['added'],
                ships_updated=stats['updated'],
                ships_deleted=stats['deleted'],
                last_sync_duration_seconds=duration
            )

            logger.info(f"Incremental sync completed in {duration}s: "
                        f"{stats['added']} added, {stats['updated']} updated, {stats['deleted']} deleted, {stats['unchanged']} unchanged")
            return

        except Exception as e:
            logger.error(f"Incremental sync failed: {e}", exc_info=True)
            self.update_sync_status(is_syncing=False)
            raise
    
    def close(self):
        """Close database and stop sync thread"""
        self.stop_background_sync()
        logger.info("Database closed")
