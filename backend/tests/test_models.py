"""Tests for pydantic models."""
import pytest
from pydantic import ValidationError
from datetime import date

from models.ship import Ship, ShipWeapons, ShipStats


class TestShipWeapons:
    """Tests for ShipWeapons model."""
    
    def test_valid_weapons(self):
        """Test creating valid weapons config."""
        weapons = ShipWeapons(
            fore=4,
            aft=3,
            can_equip_dual_cannons=True
        )
        
        assert weapons.fore == 4
        assert weapons.aft == 3
        assert weapons.can_equip_dual_cannons is True
    
    def test_weapons_defaults(self):
        """Test default values."""
        weapons = ShipWeapons(fore=4, aft=3)
        
        assert weapons.can_equip_dual_cannons is False
    
    def test_weapons_validation_error(self):
        """Test validation with invalid values."""
        with pytest.raises(ValidationError):
            ShipWeapons(fore=-1, aft=3)  # Negative not allowed


class TestShipStats:
    """Tests for ShipStats model."""
    
    def test_valid_stats(self):
        """Test creating valid stats."""
        stats = ShipStats(
            max_hull=45000,
            hull_modifier=1.2,
            turn_rate=15.0
        )
        
        assert stats.max_hull == 45000
        assert stats.hull_modifier == 1.2
        assert stats.turn_rate == 15.0
    
    def test_stats_optional_fields(self):
        """Test that fields are optional."""
        stats = ShipStats()
        
        assert stats.max_hull is None
        assert stats.turn_rate is None


class TestShip:
    """Tests for Ship model."""
    
    def test_valid_ship(self):
        """Test creating a valid ship."""
        ship = Ship(
            name="Test Ship",
            link="https://sto.fandom.com/wiki/Test",
            tier=5
        )
        
        assert ship.name == "Test Ship"
        assert str(ship.link) == "https://sto.fandom.com/wiki/Test"
        assert ship.tier == 5
    
    def test_ship_with_nested_models(self):
        """Test ship with weapons and stats."""
        ship = Ship(
            name="Test Ship",
            link="https://sto.fandom.com/wiki/Test",
            weapons=ShipWeapons(fore=4, aft=3),
            stats=ShipStats(max_hull=45000)
        )
        
        assert ship.weapons.fore == 4
        assert ship.stats.max_hull == 45000
    
    def test_ship_validation_error(self):
        """Test validation with invalid data."""
        with pytest.raises(ValidationError):
            Ship(
                name="",  # Empty name not allowed
                link="invalid-url"
            )