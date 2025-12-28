"""
Cargo Scraper - Improved template parsing approach

Uses MediaWiki API to get wikitext and parses Template:Shiptypeinfo directly.
This is much more reliable than HTML regex parsing.
"""
from typing import List, Dict, Optional
import httpx
import re
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)


class CargoScraper:
    """
    Scraper that parses ship templates from wikitext
    
    Approach:
    1. Use MediaWiki API to get category members (ship list)
    2. Get wikitext source with action=parse&prop=wikitext
    3. Parse Template:Shiptypeinfo parameters
    
    This is more reliable than HTML parsing!
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
                "User-Agent": "STOWiki-Crawler/3.0 (Wikitext Parser)",
                "Accept": "application/json"
            }
        )
        logger.info("CargoScraper initialized (wikitext mode)")
    
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
        Parse a ship page and extract data from Template:Shiptypeinfo
        
        Args:
            page_title: Ship page title
        
        Returns:
            Dictionary with ship data or None if parsing fails
        """
        params = {
            "action": "query",
            "titles": page_title,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "format": "json"
        }
        
        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.warning(f"Failed to parse {page_title}: {data['error'].get('info', 'Unknown')}")
                return None
            
            # Extract wikitext
            pages = data.get("query", {}).get("pages", {})
            page_data = next(iter(pages.values()))
            
            if "missing" in page_data:
                logger.warning(f"Page not found: {page_title}")
                return None
            
            revisions = page_data.get("revisions", [])
            if not revisions:
                return None
            
            wikitext = revisions[0].get("slots", {}).get("main", {}).get("*", "")
            
            # Parse template parameters
            ship_data = self._parse_template(wikitext, page_title)
            
            return ship_data
            
        except Exception as e:
            logger.error(f"Failed to parse {page_title}: {e}")
            return None
    
    def _parse_template(self, wikitext: str, page_title: str) -> Dict:
        """
        Extract ship data from Template:Shiptypeinfo in wikitext
        
        This parses parameters like:
        {{Shiptypeinfo
        |tier=6
        |type=Destroyer
        |hull=46000
        |fore=5
        |aft=2
        ...
        }}
        """
        ship_data = {
            "name": page_title,
            "wiki_url": f"https://stowiki.net/wiki/{quote(page_title.replace(' ', '_'))}",
            "faction": [],
            "type": []
        }
        
        # Find Template:Shiptypeinfo
        template_match = re.search(
            r'\{\{Shiptypeinfo([^}]+)\}\}',
            wikitext,
            re.DOTALL | re.IGNORECASE
        )
        
        if not template_match:
            logger.warning(f"No Shiptypeinfo template found for {page_title}")
            return ship_data
        
        template_content = template_match.group(1)
        
        # Parse parameters
        def get_param(name: str, default=None):
            pattern = rf'\|\s*{re.escape(name)}\s*=\s*([^|\n]+)'
            match = re.search(pattern, template_content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove HTML comments
                value = re.sub(r'<!--.*?-->', '', value)
                return value if value else default
            return default
        
        def get_int(name: str, default=None) -> Optional[int]:
            value = get_param(name)
            if value:
                try:
                    # Remove commas and extract first number
                    clean_value = re.sub(r'[^0-9]', '', value)
                    if clean_value:
                        return int(clean_value)
                except ValueError:
                    pass
            return default
        
        def get_float(name: str, default=None) -> Optional[float]:
            value = get_param(name)
            if value:
                try:
                    # Extract float (with decimal point)
                    match = re.search(r'([0-9]+\.?[0-9]*)', value)
                    if match:
                        return float(match.group(1))
                except ValueError:
                    pass
            return default
        
        # Extract all fields
        ship_data["tier"] = get_int("tier")
        ship_data["hull"] = get_int("hull")
        ship_data["hullmod"] = get_float("hullmod")
        ship_data["shieldmod"] = get_float("shieldmod")
        ship_data["turnrate"] = get_float("turnrate")
        ship_data["impulse"] = get_float("impulse")
        ship_data["inertia"] = get_float("inertia")
        
        # Weapons
        ship_data["fore"] = get_int("fore")
        ship_data["aft"] = get_int("aft")
        ship_data["equipcannons"] = get_param("equipcannons", "no")
        ship_data["can_use_cannons"] = ship_data["equipcannons"].lower() == "yes"
        
        # Consoles
        ship_data["consolestac"] = get_int("consolestac")
        ship_data["consoleseng"] = get_int("consoleseng")
        ship_data["consolessci"] = get_int("consolessci")
        ship_data["consolesuni"] = get_int("consolesuni")
        
        # Hangars
        ship_data["hangars"] = get_int("hangars")
        
        # Admiralty
        ship_data["admiraltyeng"] = get_int("admiraltyeng")
        ship_data["admiraltytac"] = get_int("admiraltytac")
        ship_data["admiraltysci"] = get_int("admiraltysci")
        
        # Type (can be comma-separated)
        type_value = get_param("type")
        if type_value:
            # Split by comma or slash
            types = re.split(r'[,/]', type_value)
            ship_data["type"] = [t.strip() for t in types if t.strip()]
        
        # Additional fields
        ship_data["rank"] = get_param("rank")
        ship_data["cost"] = get_param("cost")
        ship_data["boffs"] = get_param("boffs")
        ship_data["abilities"] = get_param("abilities")
        
        # Display fields
        ship_data["displayprefix"] = get_param("displayprefix")
        ship_data["displayclass"] = get_param("displayclass")
        ship_data["displaytype"] = get_param("displaytype")
        
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
                # Add faction info
                faction_name = faction.replace("-", " ").title()
                ship_data["faction"] = [faction_name]
                ship_data["factionlede"] = faction_name
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
            "srlimit": min(limit, 50),  # Reduced to avoid too many results
            "format": "json"
        }
        
        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get("query", {}).get("search", [])
            ship_titles = [result["title"] for result in search_results]
            
            logger.info(f"Found {len(ship_titles)} search results for '{query}'")
            
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
