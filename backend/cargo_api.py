""" 
Cargo API Client - Direct access to STOWiki's Cargo database

This replaces the complex MediaWiki Parse API approach with direct
structured database queries via Special:CargoExport.

Performance: 10x faster, 10x simpler!
"""
from typing import List, Dict, Optional
import httpx
from urllib.parse import urlencode, quote
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class CargoQuery(BaseModel):
    """Cargo query parameters for Special:CargoExport"""
    
    tables: str = "Ships"
    fields: str = "*"
    where: Optional[str] = None
    join_on: Optional[str] = Field(None, alias="join on")
    group_by: Optional[str] = Field(None, alias="group by") 
    having: Optional[str] = None
    order_by: Optional[str] = Field(None, alias="order by")
    limit: int = 500
    offset: int = 0
    format: str = "json"


class CargoAPIClient:
    """
    Direct Cargo database access via Special:CargoExport
    
    STOWiki uses the Cargo extension to store structured data.
    This client queries the Ships table directly, bypassing the need
    for template parsing entirely.
    
    Benefits:
    - 10x faster than MediaWiki Parse API
    - Structured JSON responses
    - Flexible SQL-like filtering
    - Bulk queries (all ships in one request)
    - Stable database schema
    
    Example:
        client = CargoAPIClient()
        ships = client.get_all_ships(faction="dominion")
        enterprise = client.get_ship_by_name("USS Enterprise")
    """
    
    BASE_URL = "https://stowiki.net/wiki/Special:CargoExport"
    
    # All available fields in the Ships Cargo table
    ALL_FIELDS = [
        "name", "image", "image2", "released", "fc", "faction", "facsort",
        "rank", "ranklevel", "tier", "upgradecost", "type", "hull", "hullmod",
        "shieldmod", "turnrate", "impulse", "inertia", "powerall", "powerweapons",
        "powershields", "powerengines", "powerauxiliary", "powerboost", "boffs",
        "fore", "aft", "equipcannons", "devices", "consolestac", "consoleseng",
        "consolessci", "consolesuni", "uniconsole", "t5uconsole", "experimental",
        "secdeflector", "hangars", "cost", "abilities", "admiraltyeng",
        "admiraltytac", "admiraltysci", "displayprefix", "displayclass",
        "displaytype", "factionlede", "internalname"
    ]
    
    # Default fields for list queries (reduces payload size)
    DEFAULT_FIELDS = [
        "name", "image", "faction", "factionlede", "tier", "type",
        "hull", "hullmod", "shieldmod", "turnrate", "impulse", "inertia",
        "fore", "aft", "equipcannons", "consolestac", "consoleseng",
        "consolessci", "consolesuni", "hangars", "admiraltyeng",
        "admiraltytac", "admiraltysci", "displayprefix", "displayclass",
        "displaytype"
    ]
    
    def __init__(self, timeout: float = 30.0):
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "STOWiki-Crawler/3.0 (Cargo API)",
                "Accept": "application/json"
            }
        )
        logger.info("CargoAPIClient initialized")
    
    def query(self, query: CargoQuery) -> List[Dict]:
        """
        Execute Cargo query
        
        Args:
            query: CargoQuery object with tables, fields, where clause, etc.
        
        Returns:
            List of result dictionaries
        
        Raises:
            httpx.HTTPError: If request fails
        
        Example:
            query = CargoQuery(
                fields="name,faction,tier,hull",
                where="factionlede='Dominion'",
                order_by="name",
                limit=100
            )
            ships = client.query(query)
        """
        params = query.model_dump(exclude_none=True, by_alias=True)
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        logger.debug(f"Cargo query: {url}")
        
        try:
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Cargo query returned {len(data)} results")
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"Cargo query failed: {e}")
            raise
    
    def get_all_ships(
        self,
        faction: Optional[str] = None,
        tier: Optional[int] = None,
        ship_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get all ships, optionally filtered by faction, tier, or type
        
        Args:
            faction: Filter by faction (federation, klingon, romulan, dominion, cross-faction)
            tier: Filter by tier (1-6)
            ship_type: Filter by type (escort, cruiser, science, etc.)
            limit: Maximum number of results (default 1000)
        
        Returns:
            List of ship dictionaries
        
        Example:
            # Get all Dominion ships
            ships = client.get_all_ships(faction="dominion")
            
            # Get all Tier 6 escorts
            ships = client.get_all_ships(tier=6, ship_type="escort")
        """
        where_clauses = []
        
        # Map user-friendly faction names to Cargo factionlede values
        if faction:
            faction_map = {
                "federation": "United Federation of Planets",
                "klingon": "Klingon Empire",
                "romulan": "Romulan Republic",
                "dominion": "Dominion",
                "cross-faction": "Cross-Faction"
            }
            faction_value = faction_map.get(faction.lower())
            if faction_value:
                # Use HOLDS for array fields like faction
                where_clauses.append(f"faction HOLDS '{faction_value}'")
        
        if tier:
            where_clauses.append(f"tier={tier}")
        
        if ship_type:
            # Use HOLDS for array fields
            where_clauses.append(f"type HOLDS '{ship_type}'")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else None
        
        query = CargoQuery(
            fields=",".join(self.DEFAULT_FIELDS),
            where=where_clause,
            order_by="name",
            limit=limit
        )
        
        return self.query(query)
    
    def get_ship_by_name(self, name: str) -> Optional[Dict]:
        """
        Get single ship by exact name
        
        Args:
            name: Exact ship name (e.g. "USS Enterprise")
        
        Returns:
            Ship dictionary or None if not found
        
        Example:
            ship = client.get_ship_by_name("Jem'Hadar Strike Ship")
        """
        # Escape single quotes in name
        safe_name = name.replace("'", "\\'").replace('"', '\\"')
        
        query = CargoQuery(
            fields=",".join(self.ALL_FIELDS),
            where=f"name='{safe_name}'",
            limit=1
        )
        
        results = self.query(query)
        return results[0] if results else None
    
    def search_ships(self, search_term: str, limit: int = 100) -> List[Dict]:
        """
        Search ships by name (fuzzy match)
        
        Args:
            search_term: Search query (supports wildcards)
            limit: Maximum results (default 100)
        
        Returns:
            List of matching ship dictionaries
        
        Example:
            # Find all ships with "Jem'Hadar" in the name
            ships = client.search_ships("Jem'Hadar")
        """
        # Escape special characters
        safe_term = search_term.replace("'", "\\'").replace('"', '\\"')
        
        query = CargoQuery(
            fields="name,faction,factionlede,tier,type,hull,fore,aft",
            where=f"name LIKE '%{safe_term}%'",
            order_by="name",
            limit=limit
        )
        
        return self.query(query)
    
    def get_faction_summary(self) -> Dict[str, int]:
        """
        Get ship counts per faction
        
        Returns:
            Dictionary mapping faction names to ship counts
        
        Example:
            summary = client.get_faction_summary()
            # {"Dominion": 43, "Federation": 287, ...}
        """
        factions = [
            "United Federation of Planets",
            "Klingon Empire",
            "Romulan Republic",
            "Dominion"
        ]
        
        summary = {}
        
        for faction in factions:
            # Count ships where faction array contains this faction
            query = CargoQuery(
                tables="Ships",
                fields="COUNT(*) as count",
                where=f"faction HOLDS '{faction}'"
            )
            
            try:
                result = self.query(query)
                # Cargo returns count as string
                count = int(result[0].get("count", 0)) if result else 0
                summary[faction] = count
            except (ValueError, IndexError, KeyError):
                summary[faction] = 0
        
        # Add cross-faction count
        try:
            query = CargoQuery(
                tables="Ships",
                fields="COUNT(*) as count",
                where="factionlede='Cross-Faction'"
            )
            result = self.query(query)
            summary["Cross-Faction"] = int(result[0].get("count", 0)) if result else 0
        except (ValueError, IndexError, KeyError):
            summary["Cross-Faction"] = 0
        
        logger.info(f"Faction summary: {summary}")
        return summary
    
    def get_ship_types(self) -> List[str]:
        """
        Get all unique ship types
        
        Returns:
            List of ship type names
        
        Example:
            types = client.get_ship_types()
            # ["Escort", "Cruiser", "Science Vessel", ...]
        """
        query = CargoQuery(
            fields="type",
            group_by="type",
            order_by="type",
            limit=100
        )
        
        results = self.query(query)
        
        # Flatten type arrays and deduplicate
        types = set()
        for result in results:
            ship_types = result.get("type", [])
            if isinstance(ship_types, list):
                types.update(ship_types)
            elif ship_types:  # String
                types.add(ship_types)
        
        return sorted(types)
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.client.close()
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
        logger.info("CargoAPIClient closed")
