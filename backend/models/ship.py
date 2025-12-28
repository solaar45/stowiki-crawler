"""
Ship data model - Direct Cargo field mapping

This model matches the Cargo Ships table schema exactly.
No complex transformations needed!
"""
from typing import Optional, List
from pydantic import BaseModel, Field, computed_field
from datetime import date


class Ship(BaseModel):
    """
    Ship model - 1:1 mapping to Cargo Ships table
    
    All fields match the Cargo database schema directly.
    This eliminates the need for complex data transformation.
    
    Cargo Arrays:
    - faction: List of factions that can use this ship
    - type: List of ship types (e.g. ["Cruiser"] or ["Science Vessel", "Carrier"])
    
    Example:
        ship = Ship(
            name="Jem'Hadar Strike Ship",
            faction=["Dominion"],
            factionlede="Dominion",
            tier=5,
            type=["Escort"],
            hull=39000,
            fore=4,
            aft=3
        )
    """
    
    # ========== Basic Info ==========
    name: str = Field(description="Ship name")
    image: Optional[str] = Field(None, description="Image filename")
    image2: Optional[str] = Field(None, description="Secondary image filename")
    released: Optional[str] = Field(None, description="Release date")
    internalname: Optional[str] = Field(None, description="Internal game name")
    
    # ========== Faction ==========
    faction: List[str] = Field(default_factory=list, description="Factions that can use this ship")
    factionlede: Optional[str] = Field(None, description="Primary faction")
    facsort: Optional[str] = Field(None, description="Faction sort code")
    
    # ========== Tier & Rank ==========
    tier: Optional[int] = Field(None, ge=1, le=6, description="Ship tier")
    rank: Optional[str] = Field(None, description="Required rank")
    ranklevel: Optional[int] = Field(None, description="Rank level number")
    upgradecost: Optional[str] = Field(None, description="T5-U upgrade cost")
    
    # ========== Ship Type ==========
    type: List[str] = Field(default_factory=list, description="Ship types")
    displayprefix: Optional[str] = Field(None, description="Display prefix (e.g. 'Fleet', 'Mirror')")
    displayclass: Optional[str] = Field(None, description="Display class name")
    displaytype: Optional[str] = Field(None, description="Display type")
    
    # ========== Stats ==========
    hull: Optional[int] = Field(None, ge=0, description="Base hull points")
    hullmod: Optional[float] = Field(None, description="Hull modifier")
    shieldmod: Optional[float] = Field(None, description="Shield modifier")
    turnrate: Optional[float] = Field(None, description="Turn rate (degrees/sec)")
    impulse: Optional[float] = Field(None, description="Impulse modifier")
    inertia: Optional[float] = Field(None, description="Inertia rating")
    
    # ========== Power ==========
    powerall: Optional[int] = Field(None, description="Bonus to all power levels")
    powerweapons: Optional[int] = Field(None, description="Bonus weapons power")
    powershields: Optional[int] = Field(None, description="Bonus shields power")
    powerengines: Optional[int] = Field(None, description="Bonus engines power")
    powerauxiliary: Optional[int] = Field(None, description="Bonus auxiliary power")
    powerboost: Optional[int] = Field(None, description="Total power boost")
    
    # ========== Bridge Officers ==========
    boffs: Optional[str] = Field(None, description="Bridge officer configuration (comma-separated)")
    
    # ========== Weapons ==========
    fore: Optional[int] = Field(None, ge=0, description="Fore weapon slots")
    aft: Optional[int] = Field(None, ge=0, description="Aft weapon slots")
    equipcannons: Optional[str] = Field(None, description="Can equip dual cannons (yes/no)")
    
    # ========== Equipment ==========
    devices: Optional[int] = Field(None, ge=0, description="Device slots")
    consolestac: Optional[int] = Field(None, ge=0, description="Tactical console slots")
    consoleseng: Optional[int] = Field(None, ge=0, description="Engineering console slots")
    consolessci: Optional[int] = Field(None, ge=0, description="Science console slots")
    consolesuni: Optional[int] = Field(None, ge=0, description="Universal console slots")
    uniconsole: Optional[str] = Field(None, description="Unique console name")
    t5uconsole: Optional[str] = Field(None, description="T5-U console type")
    experimental: Optional[int] = Field(None, description="Has experimental weapon slot (0/1)")
    secdeflector: Optional[int] = Field(None, description="Has secondary deflector (0/1)")
    hangars: Optional[int] = Field(None, ge=0, description="Hangar bay slots")
    
    # ========== Cost & Abilities ==========
    cost: Optional[str] = Field(None, description="Acquisition cost")
    abilities: Optional[str] = Field(None, description="Ship abilities (comma-separated)")
    
    # ========== Admiralty ==========
    admiraltyeng: Optional[int] = Field(None, ge=0, description="Admiralty ENG stat")
    admiraltytac: Optional[int] = Field(None, ge=0, description="Admiralty TAC stat")
    admiraltysci: Optional[int] = Field(None, ge=0, description="Admiralty SCI stat")
    
    # ========== Internal ==========
    fc: Optional[int] = Field(None, description="Fleet credits flag")
    
    # ========== Computed Properties ==========
    
    @computed_field
    @property
    def wiki_url(self) -> str:
        """Generate STOWiki URL"""
        return f"https://stowiki.net/wiki/{self.name.replace(' ', '_')}"
    
    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        """Generate image URL if image exists"""
        if self.image:
            return f"https://stowiki.net/wiki/Special:Redirect/file/{self.image}"
        return None
    
    @computed_field
    @property
    def can_use_cannons(self) -> bool:
        """Check if ship can equip dual cannons"""
        return self.equipcannons == "yes"
    
    @computed_field
    @property
    def total_consoles(self) -> int:
        """Calculate total console slots"""
        return (
            (self.consolestac or 0) +
            (self.consoleseng or 0) +
            (self.consolessci or 0) +
            (self.consolesuni or 0)
        )
    
    @computed_field
    @property
    def total_weapons(self) -> int:
        """Calculate total weapon slots"""
        return (self.fore or 0) + (self.aft or 0)
    
    @computed_field
    @property
    def has_hangar(self) -> bool:
        """Check if ship has hangar bays"""
        return (self.hangars or 0) > 0
    
    @computed_field
    @property
    def has_experimental_weapon(self) -> bool:
        """Check if ship has experimental weapon slot"""
        return self.experimental == 1
    
    @computed_field
    @property
    def has_secondary_deflector(self) -> bool:
        """Check if ship has secondary deflector"""
        return self.secdeflector == 1
    
    @computed_field
    @property
    def is_carrier(self) -> bool:
        """Check if ship is a carrier (has 2+ hangars)"""
        return (self.hangars or 0) >= 2
    
    @computed_field
    @property
    def display_name(self) -> str:
        """
        Generate formatted display name
        
        Example: "Fleet Jem'Hadar Strike Ship" 
        """
        parts = []
        if self.displayprefix:
            parts.append(self.displayprefix)
        if self.displayclass:
            parts.append(f"{self.displayclass}-class")
        if self.displaytype:
            parts.append(self.displaytype)
        
        return " ".join(parts) if parts else self.name
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jem'Hadar Strike Ship",
                "faction": ["Dominion"],
                "factionlede": "Dominion",
                "tier": 5,
                "type": ["Escort"],
                "hull": 39000,
                "hullmod": 1.3,
                "shieldmod": 1.0,
                "turnrate": 15.0,
                "fore": 4,
                "aft": 3,
                "equipcannons": "yes",
                "consolestac": 4,
                "consoleseng": 3,
                "consolessci": 3,
                "admiraltyeng": 28,
                "admiraltytac": 54,
                "admiraltysci": 18
            }
        }


class ShipSummary(BaseModel):
    """
    Lightweight ship summary for list views
    
    Contains only essential fields to reduce payload size.
    """
    name: str
    faction: List[str]
    factionlede: Optional[str] = None
    tier: Optional[int] = None
    type: List[str]
    hull: Optional[int] = None
    fore: Optional[int] = None
    aft: Optional[int] = None
    
    @computed_field
    @property
    def wiki_url(self) -> str:
        return f"https://stowiki.net/wiki/{self.name.replace(' ', '_')}"
