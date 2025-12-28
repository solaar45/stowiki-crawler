"""
Cargo Ship Scraper

Scrapes ship data from STOWiki's Cargo database using MediaWiki Cargo API.
Optimized for database sync operations.
"""
import httpx
import logging
import re
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class CargoShipScraper:
    """
    Scraper for STOWiki ship data using Cargo API
    """
    
    BASE_URL = "https://stowiki.net/api.php"
    
    # Faction filters for Cargo queries
    FACTION_FILTERS = {
        "federation": "Ships.faction HOLDS 'Federation'",
        "klingon": "Ships.faction HOLDS 'Klingon'",
        "romulan": "Ships.faction HOLDS 'Romulan'",
        "dominion": "Ships.faction HOLDS 'Dominion'",
        "cross-faction": "Ships.factionlede='Cross Faction'"
    }
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        logger.info("CargoShipScraper initialized")
    
    def get_all_ships(self, limit: int = 1000) -> List[Dict]:
        """
        Get all ships from Cargo database
        
        Args:
            limit: Maximum ships to fetch
        
        Returns:
            List of ship data dictionaries
        """
        ships = []
        offset = 0
        batch_size = 500  # Cargo max limit
        
        while len(ships) < limit:
            params = {
                "action": "cargoquery",
                "tables": "Ships",
                "fields": self._get_field_list(),
                "limit": min(batch_size, limit - len(ships)),
                "offset": offset,
                "format": "json"
            }
            
            try:
                response = self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "cargoquery" in data:
                    results = data["cargoquery"]
                    
                    if not results:
                        break  # No more results
                    
                    for item in results:
                        ship = self._parse_cargo_result(item["title"])
                        if ship:
                            ships.append(ship)
                    
                    logger.info(f"Fetched {len(results)} ships (total: {len(ships)})")
                    
                    if len(results) < batch_size:
                        break  # Last page
                    
                    offset += batch_size
                else:
                    logger.warning("No cargoquery in response")
                    break
            
            except Exception as e:
                logger.error(f"Error fetching ships: {e}", exc_info=True)
                break
            
            # Rate limiting
            time.sleep(0.1)
        
        logger.info(f"Fetched total of {len(ships)} ships")
        return ships
    
    def get_faction_ships(self, faction: str, limit: int = 500) -> List[Dict]:
        """
        Get all ships for a specific faction
        
        Args:
            faction: Faction key (federation, klingon, etc.)
            limit: Maximum ships to fetch
        
        Returns:
            List of ship data dictionaries
        """
        where_clause = self.FACTION_FILTERS.get(faction.lower())
        
        if not where_clause:
            logger.error(f"Unknown faction: {faction}")
            return []
        
        ships = []
        offset = 0
        batch_size = 500
        
        while len(ships) < limit:
            params = {
                "action": "cargoquery",
                "tables": "Ships",
                "fields": self._get_field_list(),
                "where": where_clause,
                "limit": min(batch_size, limit - len(ships)),
                "offset": offset,
                "format": "json"
            }
            
            try:
                response = self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "cargoquery" in data:
                    results = data["cargoquery"]
                    
                    if not results:
                        break
                    
                    for item in results:
                        ship = self._parse_cargo_result(item["title"])
                        if ship:
                            ships.append(ship)
                    
                    logger.info(f"Fetched {len(results)} {faction} ships (total: {len(ships)})")
                    
                    if len(results) < batch_size:
                        break
                    
                    offset += batch_size
                else:
                    break
            
            except Exception as e:
                logger.error(f"Error fetching {faction} ships: {e}", exc_info=True)
                break
            
            time.sleep(0.1)
        
        logger.info(f"Fetched {len(ships)} ships for {faction}")
        return ships
    
    def get_category_members(self, category: str = None, limit: int = 1000) -> List[str]:
        """
        Get all ship names from Cargo database
        
        This is used for sync operations to get a list of all ships.
        
        Args:
            category: Ignored (for compatibility)
            limit: Maximum ship names to fetch
        
        Returns:
            List of ship names
        """
        ship_names = []
        offset = 0
        batch_size = 500
        
        while len(ship_names) < limit:
            params = {
                "action": "cargoquery",
                "tables": "Ships",
                "fields": "_pageName",
                "limit": min(batch_size, limit - len(ship_names)),
                "offset": offset,
                "format": "json"
            }
            
            try:
                response = self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "cargoquery" in data:
                    results = data["cargoquery"]
                    
                    if not results:
                        break
                    
                    for item in results:
                        name = item["title"].get("pageName")
                        if name:
                            ship_names.append(name)
                    
                    if len(results) < batch_size:
                        break
                    
                    offset += batch_size
                else:
                    break
            
            except Exception as e:
                logger.error(f"Error fetching ship names: {e}", exc_info=True)
                break
        
        logger.info(f"Found {len(ship_names)} ship names")
        return ship_names
    
    def parse_ship_page(self, page_title: str) -> Optional[Dict]:
        """
        Parse a single ship by querying Cargo for its data
        
        Args:
            page_title: Ship name
        
        Returns:
            Ship data dictionary or None if not found
        """
        params = {
            "action": "cargoquery",
            "tables": "Ships",
            "fields": self._get_field_list(),
            "where": f"_pageName='{page_title}'",
            "limit": 1,
            "format": "json"
        }
        
        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "cargoquery" in data and data["cargoquery"]:
                ship = self._parse_cargo_result(data["cargoquery"][0]["title"])
                return ship
            
            logger.warning(f"No data found for {page_title}")
            return None
        
        except Exception as e:
            logger.error(f"Error parsing {page_title}: {e}", exc_info=True)
            return None
    
    def _get_field_list(self) -> str:
        """Get list of fields to query from Cargo"""
        fields = [
            "_pageName",
            "faction",
            "factionlede",
            "tier",
            "type",
            "rank",
            "cost",
            "displayprefix",
            "displayclass",
            "displaytype",
            "hull",
            "hullmod",
            "shieldmod",
            "turnrate",
            "impulse",
            "inertia",
            "fore",
            "aft",
            "equipcannons",
            "consolestac",
            "consoleseng",
            "consolessci",
            "consolesuni",
            "hangars",
            "boffs",
            "abilities",
            "admiraltyeng",
            "admiraltytac",
            "admiraltysci"
        ]
        return ",".join(fields)
    
    def _parse_cargo_result(self, cargo_data: Dict) -> Optional[Dict]:
        """
        Parse ship data from Cargo query result
        
        Args:
            cargo_data: Raw Cargo result
        
        Returns:
            Parsed ship data dictionary
        """
        try:
            ship_data = {}
            
            # Basic info
            ship_data['name'] = cargo_data.get('pageName', '')
            ship_data['faction'] = self._parse_list(cargo_data.get('faction', ''))
            ship_data['factionlede'] = cargo_data.get('factionlede')
            ship_data['tier'] = self._parse_int(cargo_data.get('tier'))
            ship_data['type'] = self._parse_list(cargo_data.get('type', ''))
            ship_data['rank'] = cargo_data.get('rank')
            ship_data['cost'] = cargo_data.get('cost')
            
            # Display
            ship_data['displayprefix'] = cargo_data.get('displayprefix')
            ship_data['displayclass'] = cargo_data.get('displayclass')
            ship_data['displaytype'] = cargo_data.get('displaytype')
            
            # Stats
            ship_data['hull'] = self._parse_int(cargo_data.get('hull'))
            ship_data['hullmod'] = self._parse_float(cargo_data.get('hullmod'))
            ship_data['shieldmod'] = self._parse_float(cargo_data.get('shieldmod'))
            ship_data['turnrate'] = self._parse_float(cargo_data.get('turnrate'))
            ship_data['impulse'] = self._parse_float(cargo_data.get('impulse'))
            ship_data['inertia'] = self._parse_float(cargo_data.get('inertia'))
            
            # Weapons
            ship_data['fore'] = self._parse_int(cargo_data.get('fore'))
            ship_data['aft'] = self._parse_int(cargo_data.get('aft'))
            ship_data['equipcannons'] = cargo_data.get('equipcannons', 'no')
            
            # Consoles
            ship_data['consolestac'] = self._parse_int(cargo_data.get('consolestac'))
            ship_data['consoleseng'] = self._parse_int(cargo_data.get('consoleseng'))
            ship_data['consolessci'] = self._parse_int(cargo_data.get('consolessci'))
            ship_data['consolesuni'] = self._parse_int(cargo_data.get('consolesuni'))
            
            # Equipment
            ship_data['hangars'] = self._parse_int(cargo_data.get('hangars'))
            ship_data['boffs'] = cargo_data.get('boffs')
            ship_data['abilities'] = cargo_data.get('abilities')
            
            # Admiralty
            ship_data['admiraltyeng'] = self._parse_int(cargo_data.get('admiraltyeng'))
            ship_data['admiraltytac'] = self._parse_int(cargo_data.get('admiraltytac'))
            ship_data['admiraltysci'] = self._parse_int(cargo_data.get('admiraltysci'))
            
            # Wiki URL
            ship_data['wiki_url'] = f"https://stowiki.net/wiki/{ship_data['name'].replace(' ', '_')}"
            
            return ship_data
        
        except Exception as e:
            logger.error(f"Error parsing cargo data: {e}", exc_info=True)
            return None
    
    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Parse integer from string"""
        if not value or value in ('?', '', 'None'):
            return None
        try:
            clean = re.sub(r'[^0-9-]', '', str(value))
            return int(clean) if clean and clean != '-' else None
        except:
            return None
    
    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse float from string"""
        if not value or value in ('?', '', 'None'):
            return None
        try:
            clean = re.sub(r'[^0-9.-]', '', str(value))
            return float(clean) if clean and clean not in ('-', '.') else None
        except:
            return None
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated list"""
        if not value or value in ('?', '', 'None'):
            return []
        # Split by comma or semicolon
        items = re.split(r'[,;]', value)
        return [item.strip() for item in items if item.strip()]
    
    # Keep compatibility with old interface
    FACTION_CATEGORIES = {
        "federation": "Federation",
        "klingon": "Klingon",
        "romulan": "Romulan",
        "dominion": "Dominion",
        "cross-faction": "Cross Faction"
    }
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
        logger.info("CargoShipScraper closed")
