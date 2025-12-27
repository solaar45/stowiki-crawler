"""Faction enumeration for ship categorization."""
from enum import Enum


class Faction(str, Enum):
    """Ship faction types."""
    FEDERATION = "Federation"
    KLINGON = "Klingon"
    ROMULAN = "Romulan"
    DOMINION = "Dominion"
    CROSS_FACTION = "Cross-Faction"
    
    @classmethod
    def get_wiki_url(cls, faction: "Faction") -> str:
        """Get wiki URL for a specific faction.
        
        Args:
            faction: Faction enum value
            
        Returns:
            Full wiki URL for the faction's ship list
        """
        base_url = "https://stowiki.net/wiki"  # Updated from sto.fandom.com
        
        urls = {
            cls.FEDERATION: f"{base_url}/Federation_playable_starship",
            cls.KLINGON: f"{base_url}/Klingon_playable_starship",
            cls.ROMULAN: f"{base_url}/Romulan_playable_starship",
            cls.DOMINION: f"{base_url}/Dominion_playable_starship",
            cls.CROSS_FACTION: f"{base_url}/Cross-Faction_playable_starship",
        }
        
        return urls[faction]
    
    @classmethod
    def all_urls(cls) -> list[str]:
        """Get all faction wiki URLs.
        
        Returns:
            List of all faction wiki URLs
        """
        return [cls.get_wiki_url(faction) for faction in cls]