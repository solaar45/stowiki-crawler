"""JSON file-based storage backend with metadata tracking."""
import json
import aiofiles
from typing import List, Optional
from datetime import datetime

from models.ship import Ship
from logger import setup_logger

logger = setup_logger(__name__)


class JSONStorage:
    """JSON file storage for ships with metadata tracking."""

    def __init__(self, filepath: str = "ships.json"):
        """Initialize JSON storage.

        Args:
            filepath: Path to JSON file
        """
        self.filepath = filepath
        self.metadata_file = filepath.replace('.json', '_metadata.json')
        logger.info(f"JSON storage initialized: {filepath}")

    async def save_ships(self, ships: List[Ship]) -> None:
        """Save ships to JSON file and update metadata.

        Args:
            ships: List of Ship objects
        """
        try:
            # Save ships data
            ships_data = [ship.dict() for ship in ships]
            async with aiofiles.open(self.filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(ships_data, indent=2, ensure_ascii=False))
            
            # Update metadata
            metadata = {
                "last_scraped": datetime.utcnow().isoformat(),
                "ship_count": len(ships),
                "factions_scraped": list(set(ship.faction for ship in ships if ship.faction))
            }
            async with aiofiles.open(self.metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
            
            logger.info(f"Saved {len(ships)} ships to {self.filepath} with metadata")

        except Exception as e:
            logger.error(f"Failed to save ships: {e}")
            raise

    async def get_ships(self, faction: Optional[str] = None) -> List[Ship]:
        """Load ships from JSON file.

        Args:
            faction: Optional faction filter

        Returns:
            List of Ship objects
        """
        try:
            async with aiofiles.open(self.filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                ships_data = json.loads(content)

            ships = [Ship(**data) for data in ships_data]

            if faction:
                ships = [s for s in ships if s.faction and s.faction.lower() == faction.lower()]

            logger.debug(f"Loaded {len(ships)} ships from storage")
            return ships

        except FileNotFoundError:
            logger.warning(f"Ships file not found: {self.filepath}")
            return []
        except Exception as e:
            logger.error(f"Failed to load ships: {e}")
            return []

    async def get_ship_count(self) -> int:
        """Get total number of ships in storage.

        Returns:
            Number of ships
        """
        ships = await self.get_ships()
        return len(ships)
    
    async def get_metadata(self) -> Optional[dict]:
        """Get scraping metadata.
        
        Returns:
            Metadata dict or None if not found
        """
        try:
            async with aiofiles.open(self.metadata_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            logger.debug(f"Metadata file not found: {self.metadata_file}")
            return None
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return None
    
    async def needs_refresh(self, max_age_hours: int = 24) -> bool:
        """Check if data needs refresh based on age.
        
        Args:
            max_age_hours: Maximum age in hours before refresh needed
            
        Returns:
            True if refresh needed, False otherwise
        """
        metadata = await self.get_metadata()
        
        if not metadata:
            logger.info("No metadata found, refresh needed")
            return True
        
        try:
            last_scraped = datetime.fromisoformat(metadata["last_scraped"])
            age = datetime.utcnow() - last_scraped
            age_hours = age.total_seconds() / 3600
            
            needs_refresh = age_hours > max_age_hours
            
            if needs_refresh:
                logger.info(f"Data is {age_hours:.1f}h old (max {max_age_hours}h), refresh needed")
            else:
                logger.debug(f"Data is {age_hours:.1f}h old, still fresh")
            
            return needs_refresh
            
        except Exception as e:
            logger.error(f"Failed to check refresh status: {e}")
            return True  # Refresh on error