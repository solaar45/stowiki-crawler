"""Async web scraper for STO Wiki ship data."""
import asyncio
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import settings
from logger import setup_logger
from cache_manager import CacheManager

logger = setup_logger(__name__)


class STOWikiScraper:
    """Async scraper for Star Trek Online Wiki."""

    def __init__(self, base_url: str = None):
        """Initialize scraper.

        Args:
            base_url: Base URL for the wiki (default from settings)
        """
        self.base_url = base_url or settings.base_url
        self.timeout = settings.request_timeout
        self.max_concurrent = settings.max_concurrent_requests
        self.delay = settings.request_delay
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.cache = CacheManager()

        logger.info(
            f"Scraper initialized: {self.base_url} (concurrent={self.max_concurrent}, delay={self.delay}s, cache={self.cache.enabled})"
        )

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
        ),
    )
    async def _fetch_url(self, url: str, client: httpx.AsyncClient) -> str:
        """Fetch URL with retry logic and rate limiting.

        Args:
            url: URL to fetch
            client: HTTP client instance

        Returns:
            HTML content as string
        """
        # Check cache first
        cached_content = await self.cache.get(url)
        if cached_content is not None:
            return cached_content

        async with self.semaphore:
            logger.debug(f"Fetching: {url}")
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Rate limiting
            await asyncio.sleep(self.delay)

            content = response.text
            
            # Cache the content
            await self.cache.set(url, content)
            
            return content

    async def scrape_ship_list_page(self, url: str) -> List[str]:
        """Scrape ship list page and extract individual ship URLs.

        Args:
            url: URL of the faction ship list page

        Returns:
            List of ship detail page URLs
        """
        try:
            async with httpx.AsyncClient() as client:
                html = await self._fetch_url(url, client)

            soup = BeautifulSoup(html, "lxml")
            ship_urls = []

            # Find all sortable tables
            tables = soup.find_all("table", class_="sortable")

            for table in tables:
                rows = table.find_all("tr")[1:]  # Skip header row

                for row in rows:
                    columns = row.find_all("td")
                    if len(columns) >= 2:
                        # Second column contains ship link
                        link = columns[1].find("a")
                        if link and link.get("href"):
                            full_url = urljoin(self.base_url, link["href"])
                            ship_urls.append(full_url)

            logger.info(f"Found {len(ship_urls)} ships in {url}")
            return ship_urls

        except Exception as e:
            logger.error(f"Failed to scrape ship list from {url}: {e}")
            return []

    async def scrape_ship_details(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual ship detail page.

        Args:
            url: Ship detail page URL

        Returns:
            Dictionary with ship data or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                html = await self._fetch_url(url, client)

            soup = BeautifulSoup(html, "lxml")
            ship_data = {"Link": url}

            # Extract ship name
            mission_name_div = soup.find("div", class_="missionname")
            if mission_name_div:
                ship_data["Ship"] = mission_name_div.get_text().strip()
            else:
                logger.warning(f"No ship name found for {url}")
                return None

            # Extract data from label/entry pairs
            label_divs = soup.find_all("div", class_="label")
            entry_divs = soup.find_all("div", class_="entry")

            for label_div, entry_div in zip(label_divs, entry_divs):
                label = label_div.get_text().strip()
                entry = self._extract_entry_content(entry_div)

                if label in ship_data:
                    ship_data[label] += " " + entry
                else:
                    ship_data[label] = entry

            return ship_data

        except Exception as e:
            logger.error(f"Failed to scrape ship details from {url}: {e}")
            return None

    def _extract_entry_content(self, entry_div) -> str:
        """Extract content from entry div.

        Args:
            entry_div: BeautifulSoup div element

        Returns:
            Extracted text content
        """
        content = []
        for element in entry_div.descendants:
            if element.name == "img":
                content.append(element.get("alt", element.get("src", "")))
            elif element.name not in ["small", "span", "i", "a", "td"] and element.string:
                content.append(element.string.strip())

        return " ".join(filter(None, content))

    async def scrape_all_ships(self, ship_urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape all ships concurrently.

        Args:
            ship_urls: List of ship detail page URLs

        Returns:
            List of ship data dictionaries
        """
        logger.info(f"Starting concurrent scrape of {len(ship_urls)} ships")

        tasks = [self.scrape_ship_details(url) for url in ship_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        ships = []
        for result in results:
            if isinstance(result, dict):
                ships.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Ship scrape failed with exception: {result}")

        logger.info(f"Successfully scraped {len(ships)}/{len(ship_urls)} ships")
        return ships
    
    async def clear_cache(self) -> int:
        """Clear scraper cache.
        
        Returns:
            Number of cache files cleared
        """
        return await self.cache.clear_all()
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        return await self.cache.get_cache_stats()