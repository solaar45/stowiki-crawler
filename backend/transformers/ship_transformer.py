"""Transform raw ship data into validated models."""
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.ship import Ship, ShipWeapons, ShipStats
from logger import setup_logger

logger = setup_logger(__name__)


class ShipTransformer:
    """Transform and validate ship data."""
    
    @staticmethod
    def is_valid_ship(raw_data: Dict[str, Any]) -> bool:
        """Check if raw data represents a valid ship (not a location/concept page).
        
        Args:
            raw_data: Raw data dictionary from scraper
            
        Returns:
            True if this looks like a real ship, False otherwise
        """
        # Must have at least Tier OR Type to be considered a ship
        has_tier = raw_data.get("Tier") is not None
        has_type = raw_data.get("Type") is not None
        
        # Pages with only Ship + Link are likely non-ship pages (no infobox found)
        has_only_basics = len(raw_data) <= 3  # Ship, Link, Faction
        
        return (has_tier or has_type) and not has_only_basics
    
    @staticmethod
    def transform_ship(raw_data: Dict[str, Any]) -> Optional[Ship]:
        """Transform raw scraped data into a validated Ship model.
        
        Args:
            raw_data: Raw data dictionary from scraper
            
        Returns:
            Validated Ship instance or None if validation fails
        """
        try:
            # Skip non-ship pages
            if not ShipTransformer.is_valid_ship(raw_data):
                logger.debug(f"Skipping non-ship page: {raw_data.get('Ship', 'Unknown')}")
                return None
            
            # Build weapons data
            weapons = None
            if "Fore Weapons" in raw_data or "Aft Weapons" in raw_data:
                weapons = ShipWeapons(
                    fore=raw_data.get("Fore Weapons", 0) or 0,
                    aft=raw_data.get("Aft Weapons", 0) or 0,
                    can_equip_dual_cannons=raw_data.get("Dual Cannons") == "yes"
                )
            
            # Build stats data
            stats = ShipStats(
                max_hull=raw_data.get("Max Hull"),
                hull_modifier=raw_data.get("Hull modifier"),
                shield_modifier=raw_data.get("Shield modifier"),
                impulse_modifier=raw_data.get("Impulse modifier"),
                turn_rate=raw_data.get("Turn rate"),
                inertia_rating=raw_data.get("Inertia rating")
            )
            
            # Parse released date
            released = None
            if raw_data.get("Released"):
                try:
                    released = datetime.fromisoformat(raw_data["Released"]).date()
                except (ValueError, TypeError):
                    logger.warning(f"Invalid date format: {raw_data.get('Released')}")
            
            # Create Ship instance - use uppercase fields from scraper
            ship = Ship(
                name=raw_data.get("Ship", "Unknown"),  # Changed from "name" to "Ship"
                link=raw_data["Link"],  # Changed from "link" to "Link"
                tier=raw_data.get("Tier"),
                faction=raw_data.get("Faction"),
                type=raw_data.get("Type"),
                released=released,
                device_slots=raw_data.get("Device slots"),
                weapons=weapons,
                stats=stats,
                bridge_officers=raw_data.get("Bridge officers"),
                console_slots=raw_data.get("Console modifications")
            )
            
            return ship
            
        except Exception as e:
            logger.error(f"Failed to transform ship data: {e}")
            logger.debug(f"Raw data: {raw_data}")
            return None
    
    @staticmethod
    def transform_ships(raw_data_list: List[Dict[str, Any]]) -> List[Ship]:
        """Transform a list of raw ship data.
        
        Args:
            raw_data_list: List of raw data dictionaries
            
        Returns:
            List of validated Ship instances
        """
        ships = []
        skipped = 0
        
        for raw_data in raw_data_list:
            ship = ShipTransformer.transform_ship(raw_data)
            if ship:
                ships.append(ship)
            else:
                skipped += 1
        
        logger.info(f"Successfully transformed {len(ships)}/{len(raw_data_list)} ships (skipped {skipped} non-ships)")
        return ships
    
    @staticmethod
    def ships_to_dict(ships: List[Ship]) -> List[Dict[str, Any]]:
        """Convert Ship models to dictionaries for JSON serialization.
        
        Args:
            ships: List of Ship instances
            
        Returns:
            List of dictionaries
        """
        return [ship.model_dump(mode="json") for ship in ships]
