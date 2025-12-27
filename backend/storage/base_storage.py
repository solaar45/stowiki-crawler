"""Abstract base class for storage backends."""
from abc import ABC, abstractmethod
from typing import List, Optional
from models.ship import Ship


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    async def save_ships(self, ships: List[Ship]) -> bool:
        """Save ships to storage.
        
        Args:
            ships: List of Ship instances to save
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_ships(self, faction: Optional[str] = None) -> List[Ship]:
        """Retrieve ships from storage.
        
        Args:
            faction: Optional faction filter
            
        Returns:
            List of Ship instances
        """
        pass
    
    @abstractmethod
    async def delete_all_ships(self) -> bool:
        """Delete all ships from storage.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_ship_count(self) -> int:
        """Get total number of ships in storage.
        
        Returns:
            Total ship count
        """
        pass