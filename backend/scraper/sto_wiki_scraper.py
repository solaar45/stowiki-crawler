"""Async scraper for Star Trek Online Wiki."""
import asyncio
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import settings
from logger import setup_logger
from .parsers import ShipListParser, ShipPageParser

logger = setup_logger(__name__)


class STOWikiScraper:
    """Async scraper for STO Wiki ship data."""
    
    def __init__(self):
        self.base_url = settings.base_url
        self.max_concurrent = settings.max_concurrent_requests
        self.request_delay = settings.request_delay
        self.timeout = settings.request_timeout
        
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch a single page with retry logic.
        
        Args:
            client: HTTP client instance
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            httpx.HTTPError: On HTTP errors after retries
        """
        logger.debug(f"Fetching URL: {url}")
        await asyncio.sleep(self.request_delay)  # Rate limiting
        
        response = await client.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.text
    
    async def scrape_ship_list_page(self, url: str) -> List[str]:
        """Scrape a ship list page and extract ship detail URLs.
        
        Args:
            url: URL of the ship list page
            
        Returns:
            List of absolute URLs to ship detail pages
        """
        logger.info(f"Scraping ship list from: {url}")
        
        async with httpx.AsyncClient() as client:
            html = await self._fetch_page(client, url)
            
        soup = BeautifulSoup(html, "lxml")
        parser = ShipListParser(soup, self.base_url)
        ship_urls = parser.extract_ship_urls()
        
        logger.info(f"Found {len(ship_urls)} ships in list")
        return ship_urls
    
    async def scrape_ship_detail(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        """Scrape a single ship detail page.
        
        Args:
            client: HTTP client instance
            url: URL of ship detail page
            
        Returns:
            Dictionary with ship data
        """
        try:
            html = await self._fetch_page(client, url)
            soup = BeautifulSoup(html, "lxml")
            
            parser = ShipPageParser(soup, url)
            ship_data = parser.extract_ship_data()
            
            logger.debug(f"Successfully scraped: {ship_data.get('name', 'Unknown')}")
            return ship_data
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return {"link": url, "error": str(e)}
    
    async def scrape_all_ships(self, ship_urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape all ship detail pages concurrently.
        
        Args:
            ship_urls: List of ship detail URLs
            
        Returns:
            List of ship data dictionaries
        """
        logger.info(f"Starting scrape of {len(ship_urls)} ships")
        
        async with httpx.AsyncClient() as client:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def scrape_with_semaphore(url: str):
                async with semaphore:
                    return await self.scrape_ship_detail(client, url)
            
            # Execute all scraping tasks concurrently
            tasks = [scrape_with_semaphore(url) for url in ship_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Filter out exceptions
        ships = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
            elif not result.get("error"):
                ships.append(result)
        
        logger.info(f"Successfully scraped {len(ships)}/{len(ship_urls)} ships")
        return ships
    
    async def scrape_dominion_ships(self) -> List[Dict[str, Any]]:
        """Scrape all Dominion playable starships.
        
        Returns:
            List of ship data dictionaries
        """
        url = f"{self.base_url}/wiki/Dominion_playable_starship"
        ship_urls = await self.scrape_ship_list_page(url)
        return await self.scrape_all_ships(ship_urls)