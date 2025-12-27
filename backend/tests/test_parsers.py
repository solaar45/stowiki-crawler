"""Tests for HTML parsers."""
import pytest
from bs4 import BeautifulSoup

from scraper.parsers import ShipListParser, ShipPageParser


class TestShipListParser:
    """Tests for ShipListParser."""
    
    def test_extract_ship_urls(self, sample_ship_list_html):
        """Test extracting ship URLs from list page."""
        soup = BeautifulSoup(sample_ship_list_html, "lxml")
        parser = ShipListParser(soup, "https://sto.fandom.com")
        
        urls = parser.extract_ship_urls()
        
        assert len(urls) == 1
        assert urls[0] == "https://sto.fandom.com/wiki/Test_Ship"
    
    def test_extract_ship_urls_empty_table(self):
        """Test with empty table."""
        html = '<table class="sortable"><tr><th>Header</th></tr></table>'
        soup = BeautifulSoup(html, "lxml")
        parser = ShipListParser(soup, "https://sto.fandom.com")
        
        urls = parser.extract_ship_urls()
        
        assert len(urls) == 0


class TestShipPageParser:
    """Tests for ShipPageParser."""
    
    def test_extract_ship_name(self, sample_ship_detail_html):
        """Test extracting ship name."""
        soup = BeautifulSoup(sample_ship_detail_html, "lxml")
        parser = ShipPageParser(soup, "https://sto.fandom.com/wiki/Test_Ship")
        
        name = parser._extract_ship_name()
        
        assert name == "Test Strike Ship"
    
    def test_extract_ship_name_missing(self):
        """Test with missing ship name."""
        soup = BeautifulSoup("<div></div>", "lxml")
        parser = ShipPageParser(soup, "https://sto.fandom.com/wiki/Test")
        
        name = parser._extract_ship_name()
        
        assert name == "Unknown"
    
    def test_extract_ship_data(self, sample_ship_detail_html):
        """Test extracting complete ship data."""
        soup = BeautifulSoup(sample_ship_detail_html, "lxml")
        parser = ShipPageParser(soup, "https://sto.fandom.com/wiki/Test_Ship")
        
        data = parser.extract_ship_data()
        
        assert data["name"] == "Test Strike Ship"
        assert data["link"] == "https://sto.fandom.com/wiki/Test_Ship"
        assert data["Tier"] == 5
        assert data["Faction"] == "Dominion"
        assert data["Max Hull"] == 45000
        assert data["Fore Weapons"] == 4
        assert data["Aft Weapons"] == 3
        assert data["Dual Cannons"] == "yes"
        assert data["Turn rate"] == 15.0
        assert data["Released"] == "2023-06-03"
    
    def test_parse_weapons(self):
        """Test parsing weapons configuration."""
        soup = BeautifulSoup("<div></div>", "lxml")
        parser = ShipPageParser(soup, "https://test.com")
        
        result = parser._parse_weapons("Fore 4 Aft 3 Can equip dual cannons.")
        
        assert result["Fore Weapons"] == 4
        assert result["Aft Weapons"] == 3
        assert result["Dual Cannons"] == "yes"
    
    def test_parse_weapons_no_dual_cannons(self):
        """Test parsing weapons without dual cannons."""
        soup = BeautifulSoup("<div></div>", "lxml")
        parser = ShipPageParser(soup, "https://test.com")
        
        result = parser._parse_weapons("Fore 3 Aft 3")
        
        assert result["Fore Weapons"] == 3
        assert result["Aft Weapons"] == 3
        assert result["Dual Cannons"] == "no"
    
    def test_parse_date_valid(self):
        """Test parsing valid date."""
        soup = BeautifulSoup("<div></div>", "lxml")
        parser = ShipPageParser(soup, "https://test.com")
        
        result = parser._parse_date("June 3, 2023")
        
        assert result == "2023-06-03"
    
    def test_parse_date_invalid(self):
        """Test parsing invalid date."""
        soup = BeautifulSoup("<div></div>", "lxml")
        parser = ShipPageParser(soup, "https://test.com")
        
        result = parser._parse_date("Invalid Date")
        
        assert result is None