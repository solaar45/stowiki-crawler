"""Ship data models with pydantic validation."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import date


class ShipWeapons(BaseModel):
    """Ship weapons configuration."""
    fore: int = Field(ge=0, le=10, description="Number of fore weapon slots")
    aft: int = Field(ge=0, le=10, description="Number of aft weapon slots")
    can_equip_dual_cannons: bool = Field(default=False, description="Can equip dual cannons")


class ShipStats(BaseModel):
    """Ship statistics and modifiers."""
    max_hull: Optional[int] = Field(None, ge=0, description="Maximum hull points")
    hull_modifier: Optional[float] = Field(None, description="Hull modifier")
    shield_modifier: Optional[float] = Field(None, description="Shield modifier")
    impulse_modifier: Optional[float] = Field(None, description="Impulse modifier")
    turn_rate: Optional[float] = Field(None, ge=0, description="Turn rate in degrees/second")
    inertia_rating: Optional[int] = Field(None, ge=0, description="Inertia rating")


class Ship(BaseModel):
    """Complete ship data model."""
    name: str = Field(min_length=1, description="Ship name")
    link: HttpUrl = Field(description="Wiki page URL")
    tier: Optional[int] = Field(None, ge=1, le=6, description="Ship tier")
    faction: Optional[str] = Field(None, description="Ship faction")
    type: Optional[str] = Field(None, description="Ship type")
    released: Optional[date] = Field(None, description="Release date")
    device_slots: Optional[int] = Field(None, ge=0, description="Number of device slots")
    
    # Nested models
    weapons: Optional[ShipWeapons] = None
    stats: Optional[ShipStats] = None
    
    # Additional fields
    bridge_officers: Optional[str] = Field(None, description="Bridge officer configuration")
    console_slots: Optional[str] = Field(None, description="Console slot configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jem'Hadar Strike Ship",
                "link": "https://sto.fandom.com/wiki/Jem'Hadar_Strike_Ship",
                "tier": 5,
                "faction": "Dominion",
                "weapons": {
                    "fore": 4,
                    "aft": 3,
                    "can_equip_dual_cannons": True
                },
                "stats": {
                    "max_hull": 39000,
                    "turn_rate": 15.0
                }
            }
        }