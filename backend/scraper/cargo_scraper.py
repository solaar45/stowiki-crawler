"""
Cargo Ship Scraper

Scrapes ship data from STOWiki's Cargo database using MediaWiki API.
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
    Scraper for STOWiki ship data using Cargo API and Wikitext parsing
    """
    
    BASE_URL = "https://stowiki.net/api.php"
    
    FACTION_CATEGORIES = {
        "federation": "Category:Federation playable starships",
        "klingon": "Category:Klingon Defense Force playable starships",
        "romulan": "Category:Romulan Republic playable starships",
        "dominion": "Category:Dominion playable starships",
        "cross-faction": "Category:Cross-faction playable starships"
    }
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        logger.info("CargoShipScraper initialized")
    
    def get_category_members(self, category: str, limit: int = 500) -> List[str]:
        """
        Get all page titles in a category
        
        Args:
            category: Category name (e.g., "Category:Federation playable starships")
            limit: Maximum number of members to fetch
        
        Returns:
            List of page titles
        """
        members = []
        cm_continue = None
        
        while len(members) < limit:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmlimit": min(500, limit - len(members)),
                "format": "json"
            }
            
            if cm_continue:
                params["cmcontinue"] = cm_continue
            
            try:
                response = self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "query" in data and "categorymembers" in data["query"]:
                    batch = [m["title"] for m in data["query"]["categorymembers"]]
                    members.extend(batch)
                    logger.debug(f"Fetched {len(batch)} members from {category}")
                
                # Check for continuation
                if "continue" in data and "cmcontinue" in data["continue"]:
                    cm_continue = data["continue"]["cmcontinue"]
                else:
                    break
            
            except Exception as e:
                logger.error(f"Error fetching category members: {e}")
                break
        
        logger.info(f"Found {len(members)} members in {category}")
        return members
    
    def parse_ship_page(self, page_title: str) -> Optional[Dict]:
        """
        Parse a single ship page and extract data
        
        Args:
            page_title: Wiki page title
        
        Returns:
            Ship data dictionary or None if parsing fails
        """
        try:
            # Get page wikitext
            params = {
                "action": "query",
                "titles": page_title,
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
                "format": "json"
            }
            
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract wikitext
            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))
            
            if "revisions" not in page:
                logger.warning(f"No revisions found for {page_title}")
                return None
            
            wikitext = page["revisions"][0]["slots"]["main"]["*"]
            
            # Parse ship data from wikitext
            ship_data = self._parse_wikitext(wikitext)
            
            if ship_data:
                ship_data["name"] = page_title
                ship_data["wiki_url"] = f"https://stowiki.net/wiki/{page_title.replace(' ', '_')}"
                return ship_data
            
            return None
        
        except Exception as e:
            logger.error(f"Error parsing {page_title}: {e}", exc_info=True)
            return None
    
    def _parse_wikitext(self, wikitext: str) -> Optional[Dict]:
        """
        Parse ship data from wikitext template
        
        Extracts data from {{Shiptypeinfo|...}} template
        """
        # Find Shiptypeinfo template
        template_match = re.search(r'{{Shiptypeinfo\s*\|([^}]+)}}', wikitext, re.DOTALL | re.IGNORECASE)
        
        if not template_match:
            return None
        
        template_content = template_match.group(1)
        
        # Parse template parameters
        params = {}
        
        # Split by | but handle nested templates
        parts = []
        depth = 0
        current = ""
        
        for char in template_content:
            if char == '{' or char == '[':
                depth += 1
            elif char == '}' or char == ']':
                depth -= 1
            elif char == '|' and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
            current += char
        
        if current:
            parts.append(current.strip())
        
        # Parse key=value pairs
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Skip empty values
                if value and value != "?":
                    params[key] = value
        
        # Convert to ship data format
        ship_data = {}
        
        # Basic info
        ship_data['faction'] = self._parse_list(params.get('faction', ''))
        ship_data['factionlede'] = params.get('factionlede')
        ship_data['tier'] = self._parse_int(params.get('tier'))
        ship_data['type'] = self._parse_list(params.get('type', ''))
        ship_data['rank'] = params.get('rank')
        ship_data['cost'] = params.get('cost')
        
        # Display
        ship_data['displayprefix'] = params.get('displayprefix')
        ship_data['displayclass'] = params.get('displayclass')
        ship_data['displaytype'] = params.get('displaytype')
        
        # Stats
        ship_data['hull'] = self._parse_int(params.get('hull'))
        ship_data['hullmod'] = self._parse_float(params.get('hullmod'))
        ship_data['shieldmod'] = self._parse_float(params.get('shieldmod'))
        ship_data['turnrate'] = self._parse_float(params.get('turnrate'))
        ship_data['impulse'] = self._parse_float(params.get('impulse'))
        ship_data['inertia'] = self._parse_float(params.get('inertia'))
        
        # Weapons
        ship_data['fore'] = self._parse_int(params.get('fore'))
        ship_data['aft'] = self._parse_int(params.get('aft'))
        ship_data['equipcannons'] = params.get('equipcannons', 'no')
        
        # Consoles
        ship_data['consolestac'] = self._parse_int(params.get('consolestac'))
        ship_data['consoleseng'] = self._parse_int(params.get('consoleseng'))
        ship_data['consolessci'] = self._parse_int(params.get('consolessci'))
        ship_data['consolesuni'] = self._parse_int(params.get('consolesuni'))
        
        # Equipment
        ship_data['hangars'] = self._parse_int(params.get('hangars'))
        ship_data['boffs'] = params.get('boffs')
        ship_data['abilities'] = params.get('abilities')
        
        # Admiralty
        ship_data['admiraltyeng'] = self._parse_int(params.get('admiraltyeng'))
        ship_data['admiraltytac'] = self._parse_int(params.get('admiraltytac'))
        ship_data['admiraltysci'] = self._parse_int(params.get('admiraltysci'))
        
        return ship_data
    
    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Parse integer from string"""
        if not value or value == "?":
            return None
        try:
            # Remove commas and other non-numeric chars
            clean = re.sub(r'[^0-9-]', '', value)
            return int(clean) if clean else None
        except:
            return None
    
    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse float from string"""
        if not value or value == "?":
            return None
        try:
            # Remove commas and keep decimals
            clean = re.sub(r'[^0-9.-]', '', value)
            return float(clean) if clean else None
        except:
            return None
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated list"""
        if not value or value == "?":
            return []
        # Split by comma or <br>
        items = re.split(r',|<br\s*/?>|;', value)
        return [item.strip() for item in items if item.strip()]
    
    def get_faction_ships(self, faction: str, limit: int = 500) -> List[Dict]:
        """
        Get all ships for a faction
        
        Args:
            faction: Faction key (federation, klingon, etc.)
            limit: Maximum ships to fetch
        
        Returns:
            List of ship data dictionaries
        """
        category = self.FACTION_CATEGORIES.get(faction.lower())
        
        if not category:
            logger.error(f"Unknown faction: {faction}")
            return []
        
        # Get category members
        ship_names = self.get_category_members(category, limit=limit)
        
        # Parse each ship
        ships = []
        for i, name in enumerate(ship_names, 1):
            logger.info(f"Parsing {i}/{len(ship_names)}: {name}")
            
            ship_data = self.parse_ship_page(name)
            if ship_data:
                ships.append(ship_data)
            
            # Rate limiting
            time.sleep(0.1)
        
        logger.info(f"Parsed {len(ships)} ships for {faction}")
        return ships
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
        logger.info("CargoShipScraper closed")
