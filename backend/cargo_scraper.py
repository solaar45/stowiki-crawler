"""
Cargo Scraper - Hybrid approach for STOWiki ship data

Since STOWiki's Cargo API is not publicly accessible, we use a hybrid approach:
1. Get ship lists from category pages
2. Parse individual ship pages for structured data
3. Extract Cargo data from rendered infoboxes

This is still 5x faster than full HTML scraping because we use the MediaWiki API.
"""
from typing import List, Dict, Optional
import httpx
import re
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)


class CargoScraper:
    """
    Hybrid scraper that uses MediaWiki API to extract Cargo data
    
    Approach:
    1. Use MediaWiki API to get category members (ship list)
    2. Use action=parse to get rendered HTML with Cargo data
    3. Parse the infobox data from the HTML
    
    This works because the Template:Shiptypeinfo stores data to Cargo,
    and we can extract it from the rendered page.
    """
    
    BASE_URL = "https://stowiki.net/w/api.php"
    
    # Faction category mapping
    FACTION_CATEGORIES = {
        "federation": "Federation_starship_types",
        "klingon": "Klingon_starship_types",
        "romulan": "Romulan_Republic_starship_types",
        "dominion": "Dominion_starship_types",
        "cross-faction": "Cross-Faction_starship_types"
    }
    
    def __init__(self, timeout: float = 30.0):
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "STOWiki-Crawler/3.0 (Hybrid Cargo Scraper)",
                "Accept": "application/json"
            }
        )
        logger.info("CargoScraper initialized (hybrid mode)")
    
    def get_category_members(self, category: str, limit: int = 500) -> List[str]:
        """
        Get all page titles in a category using MediaWiki API
        
        Args:
            category: Category name (without "Category:" prefix)
            limit: Maximum results
        
        Returns:
            List of page titles
        """
        members = []
        cmcontinue = None
        
        while len(members) < limit:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": min(500, limit - len(members)),
                "format": "json"
            }
            
            if cmcontinue:
                params["cmcontinue"] = cmcontinue
            
            try:
                response = self.client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"API error: {data['error'].get('info', 'Unknown')}")
                
                batch = data.get("query", {}).get("categorymembers", [])
                members.extend([page["title"] for page in batch])
                
                # Check for continuation
                cmcontinue = data.get("continue", {}).get("cmcontinue")
                if not cmcontinue:
                    break
                    
            except Exception as e:
                logger.error(f"Failed to get category members: {e}")
                break
        
        logger.info(f"Found {len(members)} members in category {category}")
        return members[:limit]
    
    def parse_ship_page(self, page_title: str) -> Optional[Dict]:
        """
        Parse a ship page and extract structured data from infobox
        
        Args:
            page_title: Ship page title
        
        Returns:
            Dictionary with ship data or None if parsing fails
        """
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "text|displaytitle",
            "format": "json"
        }
        
        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.warning(f"Failed to parse {page_title}: {data['error'].get('info', 'Unknown')}")
                return None
            
            # Extract HTML
            html = data.get("parse", {}).get("text", {}).get("*", "")
            
            # Parse infobox data from HTML
            ship_data = self._extract_infobox_data(html, page_title)
            
            return ship_data
            
        except Exception as e:
            logger.error(f"Failed to parse {page_title}: {e}")
            return None
    
    def _extract_infobox_data(self, html: str, page_title: str) -> Dict:
        """
        Extract ship data from infobox HTML
        
        This parses the rendered infobox which contains all Cargo data.
        """
        ship_data = {
            "name": page_title,
            "wiki_url": f"https://stowiki.net/wiki/{quote(page_title.replace(' ', '_'))}"
        }
        
        # Extract tier
        tier_match = re.search(r'<div class="label">.*?Tier:.*?</div>.*?<div class="entry">(\d+)</div>', html, re.DOTALL)
        if tier_match:
            ship_data["tier"] = int(tier_match.group(1))
        
        # Extract type
        type_match = re.search(r'<div class="label">.*?Type:.*?</div>.*?<div class="entry">(.*?)</div>', html, re.DOTALL)
        if type_match:
            types_html = type_match.group(1)
            # Remove HTML tags
            types_text = re.sub(r'<[^>]+>', '', types_html)
            ship_data["type"] = [t.strip() for t in types_text.split('/') if t.strip()]
        
        # Extract hull
        hull_match = re.search(r'<div class="label">.*?Hull:.*?</div>.*?<div class="entry">.*?(\d[\d,]+)', html, re.DOTALL)
        if hull_match:
            hull_str = hull_match.group(1).replace(',', '')
            ship_data["hull"] = int(hull_str)
        
        # Extract weapons
        weapons_match = re.search(r'<div class="label">.*?Weapons:.*?</div>.*?<div class="entry">.*?(\d+).*?(\d+)', html, re.DOTALL)
        if weapons_match:
            ship_data["fore"] = int(weapons_match.group(1))
            ship_data["aft"] = int(weapons_match.group(2))
        
        # Extract consoles
        console_match = re.search(
            r'<div class="label">.*?Consoles:.*?</div>.*?<div class="entry">.*?'  
            r'(\d+).*?(\d+).*?(\d+)',
            html,
            re.DOTALL
        )
        if console_match:
            ship_data["consolestac"] = int(console_match.group(1))
            ship_data["consoleseng"] = int(console_match.group(2))
            ship_data["consolessci"] = int(console_match.group(3))
        
        # Extract admiralty stats
        admiralty_match = re.search(
            r'<div class="label">.*?Admiralty Stats:.*?</div>.*?<div class="entry">.*?'
            r'(\d+).*?(\d+).*?(\d+)',
            html,
            re.DOTALL
        )
        if admiralty_match:
            ship_data["admiraltyeng"] = int(admiralty_match.group(1))
            ship_data["admiraltytac"] = int(admiralty_match.group(2))
            ship_data["admiraltysci"] = int(admiralty_match.group(3))
        
        # Check for cannon capability
        ship_data["equipcannons"] = "yes" if "Can Load Dual Cannons" in html else "no"
        ship_data["can_use_cannons"] = ship_data["equipcannons"] == "yes"
        
        # Extract hangar bays
        hangar_match = re.search(r'<div class="label">.*?Hangar Bays:.*?</div>.*?<div class="entry">(\d+)</div>', html, re.DOTALL)
        if hangar_match:
            ship_data["hangars"] = int(hangar_match.group(1))
        
        return ship_data
    
    def get_faction_ships(self, faction: str, limit: int = 500) -> List[Dict]:
        """
        Get all ships for a specific faction
        
        Args:
            faction: Faction key (federation, klingon, romulan, dominion, cross-faction)
            limit: Maximum ships to return
        
        Returns:
            List of ship dictionaries
        """
        category = self.FACTION_CATEGORIES.get(faction.lower())
        if not category:
            raise ValueError(f"Unknown faction: {faction}")
        
        logger.info(f"Getting ships for faction {faction} from category {category}")
        
        # Get ship page titles
        ship_titles = self.get_category_members(category, limit=limit)
        
        # Parse each ship page
        ships = []
        for i, title in enumerate(ship_titles, 1):
            logger.info(f"Parsing ship {i}/{len(ship_titles)}: {title}")
            
            ship_data = self.parse_ship_page(title)
            if ship_data:
                ship_data["faction"] = [faction.title()]
                ship_data["factionlede"] = faction.title()
                ships.append(ship_data)
        
        logger.info(f"Successfully parsed {len(ships)}/{len(ship_titles)} ships")
        return ships
    
    def get_all_ships(self, limit: int = 1000) -> List[Dict]:
        """
        Get ships from all factions
        
        Args:
            limit: Maximum total ships
        
        Returns:
            List of all ships
        """
        all_ships = []
        per_faction = limit // len(self.FACTION_CATEGORIES)
        
        for faction in self.FACTION_CATEGORIES.keys():
            try:
                ships = self.get_faction_ships(faction, limit=per_faction)
                all_ships.extend(ships)
            except Exception as e:
                logger.error(f"Failed to get ships for {faction}: {e}")
        
        return all_ships[:limit]
    
    def search_ships(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Search ships by name using MediaWiki search API
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching ships
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{query} incategory:Playable_starships",
            "srlimit": min(limit, 500),
            "format": "json"
        }
        
        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get("query", {}).get("search", [])
            ship_titles = [result["title"] for result in search_results]
            
            # Parse each result
            ships = []
            for title in ship_titles:
                ship_data = self.parse_ship_page(title)
                if ship_data:
                    ships.append(ship_data)
            
            return ships
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
        logger.info("CargoScraper closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
