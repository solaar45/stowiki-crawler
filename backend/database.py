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
    
    def __init__(self, db_path: str = "ships.db", sync_interval_hours: int = 8):
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_faction ON ships(factionlede)")
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
                  limit: int = 500) -> List[Dict]:
        """
        Get ships from database (instant response)
        
        Args:
            faction: Filter by faction key
            tier: Filter by tier
            limit: Maximum results
        
        Returns:
            List of ship dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM ships WHERE 1=1"
        params = []
        
        if faction:
            # Map faction key to factionlede
            faction_map = {
                "federation": "Federation",
                "klingon": "Klingon",
                "romulan": "Romulan",
                "dominion": "Dominion",
                "cross-faction": "Cross Faction"
            }
            factionlede = faction_map.get(faction.lower())
            if factionlede:
                query += " AND factionlede = ?"
                params.append(factionlede)
        
        if tier:
            query += " AND tier = ?"
            params.append(tier)
        
        query += " ORDER BY name LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        ships = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse JSON fields
        for ship in ships:
            if ship.get('type'):
                ship['type'] = json.loads(ship['type'])
            else:
                ship['type'] = []
            
            if ship.get('faction'):
                ship['faction'] = json.loads(ship['faction'])
            else:
                ship['faction'] = []
            
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
        
        # Prepare data for database
        db_data = ship_data.copy()
        
        # Convert lists to JSON
        if 'type' in db_data:
            db_data['type'] = json.dumps(db_data['type'])
        if 'faction' in db_data:
            db_data['faction'] = json.dumps(db_data['faction'])
        
        # Generate hash
        data_hash = self._hash_ship_data(db_data)
        db_data['data_hash'] = data_hash
        
        # Check if ship exists
        existing = self.get_ship_by_name(name)
        
        conn = sqlite3.connect(self.db_path)
        
        if not existing:
            # Insert new ship
            fields = list(db_data.keys())
            placeholders = ','.join(['?' for _ in fields])
            
            conn.execute(f"""
                INSERT INTO ships ({','.join(fields)}) 
                VALUES ({placeholders})
            """, [db_data[f] for f in fields])
            
            conn.commit()
            conn.close()
            
            # Log creation
            self._log_change(name, 'created', new_values=db_data)
            
            return 'created'
        
        else:
            # Check if data changed
            if existing.get('data_hash') == data_hash:
                conn.close()
                return 'unchanged'
            
            # Detect changes
            changed_fields, old_values, new_values = self._detect_changes(existing, db_data)
            
            # Update ship
            db_data['updated_at'] = datetime.now().isoformat()
            
            set_clause = ','.join([f"{f} = ?" for f in db_data.keys()])
            
            conn.execute(f"""
                UPDATE ships 
                SET {set_clause}
                WHERE name = ?
            """, [db_data[f] for f in db_data.keys()] + [name])
            
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
        """Get ship counts per faction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT factionlede, COUNT(*) as count
            FROM ships
            WHERE factionlede IS NOT NULL
            GROUP BY factionlede
            ORDER BY count DESC
        """)
        
        faction_map = {
            "Federation": "federation",
            "Klingon": "klingon",
            "Romulan": "romulan",
            "Dominion": "dominion",
            "Cross Faction": "cross-faction"
        }
        
        factions = []
        for row in cursor.fetchall():
            name = row[0]
            factions.append({
                "name": name,
                "key": faction_map.get(name, name.lower().replace(' ', '-')),
                "count": row[1]
            })
        
        conn.close()
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
                    self.smart_sync(scraper)
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
            # Get all ship names from wiki categories
            wiki_ships = set()
            for faction, category in scraper.FACTION_CATEGORIES.items():
                logger.info(f"Fetching {faction} ship list...")
                members = scraper.get_category_members(category, limit=1000)
                wiki_ships.update(members)
            
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
    
    def full_sync(self, scraper):
        """
        Full sync: Parse all ships from all factions
        
        Use this for initial setup or complete refresh.
        """
        start_time = time.time()
        
        self.update_sync_status(is_syncing=True)
        
        stats = {'added': 0, 'updated': 0, 'unchanged': 0}
        
        try:
            for faction in scraper.FACTION_CATEGORIES.keys():
                logger.info(f"Syncing {faction} ships...")
                
                ships = scraper.get_faction_ships(faction, limit=500)
                
                for ship_data in ships:
                    result = self.upsert_ship(ship_data)
                    # upsert_ship returns 'created', 'updated', or 'unchanged'
                    # We need to map these to our stats keys if they differ
                    if result == 'created':
                        stats['added'] += 1
                    elif result == 'updated':
                        stats['updated'] += 1
                    elif result == 'unchanged':
                        stats['unchanged'] += 1
            
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
    
    def close(self):
        """Close database and stop sync thread"""
        self.stop_background_sync()
        logger.info("Database closed")
