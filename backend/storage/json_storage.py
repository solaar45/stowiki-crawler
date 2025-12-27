"""JSON file storage backend."""
import json
import aiofiles
from typing import List, Optional
from pathlib import Path

from models.ship import Ship
from storage.base_storage import BaseStorage
from logger import setup_logger

logger = setup_logger(__name__)


class JSONStorage(BaseStorage):
    """JSON file storage implementation."""
    
    def __init__(self, filepath: str = "ships.json"):
        """Initialize JSON storage.
        
        Args:
            filepath: Path to JSON file
        """
        self.filepath = Path(filepath)
    
    async def save_ships(self, ships: List[Ship]) -> bool:
        """Save ships to JSON file.
        
        Args:
            ships: List of Ship instances
            
        Returns:
            True if successful
        """
        try:
            ships_dict = [ship.model_dump(mode="json") for ship in ships]
            
            async with aiofiles.open(self.filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(ships_dict, indent=2, ensure_ascii=False))
            
            logger.info(f"Saved {len(ships)} ships to {self.filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save ships to JSON: {e}")
            return False
    
    async def get_ships(self, faction: Optional[str] = None) -> List[Ship]:
        """Load ships from JSON file.
        
        Args:
            faction: Optional faction filter
            
        Returns:
            List of Ship instances
        """
        try:
            if not self.filepath.exists():
                logger.warning(f"JSON file not found: {self.filepath}")
                return []
            
            async with aiofiles.open(self.filepath, "r", encoding="utf-8") as f:
                content = await f.read()
                ships_dict = json.loads(content)
            
            ships = [Ship(**ship_data) for ship_data in ships_dict]
            
            # Filter by faction if provided
            if faction:
                ships = [ship for ship in ships if ship.faction == faction]
            
            logger.info(f"Loaded {len(ships)} ships from {self.filepath}")
            return ships
            
        except Exception as e:
            logger.error(f"Failed to load ships from JSON: {e}")
            return []
    
    async def delete_all_ships(self) -> bool:
        """Delete JSON file.
        
        Returns:
            True if successful
        """
        try:
            if self.filepath.exists():
                self.filepath.unlink()
                logger.info(f"Deleted {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete JSON file: {e}")
            return False
    
    async def get_ship_count(self) -> int:
        """Get ship count from JSON file.
        
        Returns:
            Total ship count
        """
        ships = await self.get_ships()
        return len(ships)