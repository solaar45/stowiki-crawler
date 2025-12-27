"""Tests for data transformers."""
import pytest
from transformers.ship_transformer import ShipTransformer
from models.ship import Ship


class TestShipTransformer:
    """Tests for ShipTransformer."""
    
    def test_transform_ship_success(self, sample_raw_ship_data):
        """Test successful ship transformation."""
        ship = ShipTransformer.transform_ship(sample_raw_ship_data)
        
        assert ship is not None
        assert isinstance(ship, Ship)
        assert ship.name == "Test Strike Ship"
        assert ship.tier == 5
        assert ship.weapons.fore == 4
        assert ship.weapons.aft == 3
        assert ship.weapons.can_equip_dual_cannons is True
        assert ship.stats.max_hull == 45000
        assert ship.stats.turn_rate == 15.0
    
    def test_transform_ship_minimal_data(self):
        """Test transformation with minimal data."""
        minimal_data = {
            "name": "Minimal Ship",
            "link": "https://sto.fandom.com/wiki/Minimal"
        }
        
        ship = ShipTransformer.transform_ship(minimal_data)
        
        assert ship is not None
        assert ship.name == "Minimal Ship"
        assert ship.weapons is None
        assert ship.tier is None
    
    def test_transform_ships_list(self, sample_raw_ship_data):
        """Test transforming multiple ships."""
        raw_list = [sample_raw_ship_data, sample_raw_ship_data]
        
        ships = ShipTransformer.transform_ships(raw_list)
        
        assert len(ships) == 2
        assert all(isinstance(ship, Ship) for ship in ships)
    
    def test_ships_to_dict(self, sample_raw_ship_data):
        """Test converting ships to dictionaries."""
        ship = ShipTransformer.transform_ship(sample_raw_ship_data)
        ships_list = [ship]
        
        result = ShipTransformer.ships_to_dict(ships_list)
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["name"] == "Test Strike Ship"