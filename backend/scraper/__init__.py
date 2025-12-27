"""Web scraping functionality."""
from .sto_wiki_scraper import STOWikiScraper
from .parsers import ShipPageParser, ShipListParser

__all__ = ["STOWikiScraper", "ShipPageParser", "ShipListParser"]