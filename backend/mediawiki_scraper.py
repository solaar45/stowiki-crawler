"""MediaWiki API-based scraper for STO Wiki."""
import asyncio
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote

import httpx
import mwparserfromhell
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


class MediaWikiScraper:
    """MediaWiki API-based scraper for Star Trek Online Wiki."""

    def __init__(self, base_url: str = None):
        """Initialize MediaWiki scraper.

        Args:
            base_url: Base URL for the wiki (default from settings)
        """
        self.base_url = base_url or settings.base_url
        self.api_url = f"{self.base_url}/w/api.php"
        self.timeout = settings.request_timeout
        self.max_concurrent = settings.max_concurrent_requests
        self.delay = settings.request_delay
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.cache = CacheManager()

        logger.info(
            f"MediaWiki scraper initialized: {self.api_url} (concurrent={self.max_concurrent}, cache={self.cache.enabled})"
        )

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
        ),
    )
    async def _api_request(
        self, client: httpx.AsyncClient, params: Dict[str, Any], cache_key: str = None
    ) -> Dict[str, Any]:
        """Make MediaWiki API request with retry and rate limiting.

        Args:
            client: HTTP client instance
            params: API parameters
            cache_key: Optional cache key

        Returns:
            API response as dict
        """
        # Check cache first
        if cache_key:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        async with self.semaphore:
            logger.debug(f"API request: {params.get('action')} - {params.get('titles', params.get('page', ''))}")
            
            response = await client.get(self.api_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            # Rate limiting
            await asyncio.sleep(self.delay)

            data = response.json()
            
            # Cache the response
            if cache_key:
                await self.cache.set(cache_key, data)
            
            return data

    async def get_category_members(
        self, category: str, limit: int = 500
    ) -> List[str]:
        """Get all page titles in a category.

        Args:
            category: Category name (e.g., 'Playable_starships')
            limit: Maximum number of results

        Returns:
            List of page titles
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "action": "query",
                    "list": "categorymembers",
                    "cmtitle": f"Category:{category}",
                    "cmlimit": limit,
                    "format": "json",
                }

                cache_key = f"category_{category}"
                data = await self._api_request(client, params, cache_key)

                members = data.get("query", {}).get("categorymembers", [])
                titles = [member["title"] for member in members]

                logger.info(f"Found {len(titles)} pages in category {category}")
                return titles

        except Exception as e:
            logger.error(f"Failed to get category members: {e}")
            return []

    async def get_pages_in_category_by_url(self, url: str) -> List[str]:
        """Get ship page titles from faction list page URL.
        
        Args:
            url: URL of faction ship list page
            
        Returns:
            List of ship page titles
        """
        try:
            # Extract page name from URL
            # https://stowiki.net/wiki/Federation_playable_starship -> Federation_playable_starship
            page_name = url.split("/wiki/")[-1]
            
            async with httpx.AsyncClient() as client:
                # Get the wikitext of the list page
                params = {
                    "action": "parse",
                    "page": page_name,
                    "prop": "wikitext",
                    "format": "json",
                }
                
                cache_key = f"page_links_{page_name}"
                data = await self._api_request(client, params, cache_key)
                
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                
                # Parse wikitext to find ship links
                ship_titles = self._extract_ship_links(wikitext)
                
                logger.info(f"Found {len(ship_titles)} ships in {page_name}")
                return ship_titles
                
        except Exception as e:
            logger.error(f"Failed to get pages from {url}: {e}")
            return []

    def _extract_ship_links(self, wikitext: str) -> List[str]:
        """Extract ship page titles from wikitext.
        
        Args:
            wikitext: MediaWiki wikitext content
            
        Returns:
            List of ship page titles
        """
        wikicode = mwparserfromhell.parse(wikitext)
        ship_titles = []
        
        # Find all wikilinks in tables
        for wikilink in wikicode.filter_wikilinks():
            title = str(wikilink.title).strip()
            
            # Filter for ship pages (they typically don't contain 'Category:', 'File:', etc.)
            if not any(prefix in title for prefix in ["Category:", "File:", "Template:", "Help:"]):
                # Only add if it looks like a ship name (contains letters and possibly spaces)
                if re.match(r"^[A-Za-z0-9_ \-\(\)]+$", title):
                    ship_titles.append(title)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(ship_titles))

    async def get_page_wikitext(self, page_title: str) -> Optional[str]:
        """Get raw wikitext for a page.

        Args:
            page_title: Page title

        Returns:
            Wikitext content or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "action": "parse",
                    "page": page_title,
                    "prop": "wikitext",
                    "format": "json",
                }

                cache_key = f"wikitext_{page_title}"
                data = await self._api_request(client, params, cache_key)

                wikitext = data.get("parse", {}).get("wikitext", {}).get("*")
                return wikitext

        except Exception as e:
            logger.error(f"Failed to get wikitext for {page_title}: {e}")
            return None

    def parse_ship_infobox(self, wikitext: str, page_title: str) -> Dict[str, Any]:
        """Parse ship infobox from wikitext.

        Args:
            wikitext: Page wikitext content
            page_title: Page title for ship name

        Returns:
            Dictionary with ship data
        """
        try:
            wikicode = mwparserfromhell.parse(wikitext)
            templates = wikicode.filter_templates()

            ship_data = {
                "Ship": page_title.replace("_", " "),
                "Link": f"{self.base_url}/wiki/{quote(page_title)}",
            }

            # Find infobox template (could be "Infobox ship" or similar)
            infobox = None
            for template in templates:
                template_name = str(template.name).strip().lower()
                if "infobox" in template_name or "ship" in template_name:
                    infobox = template
                    break

            if not infobox:
                logger.warning(f"No infobox found for {page_title}")
                return ship_data

            # Extract all parameters from infobox
            for param in infobox.params:
                param_name = str(param.name).strip()
                param_value = str(param.value).strip()

                # Clean up value (remove wiki markup)
                param_value = self._clean_wikitext(param_value)

                if param_value:
                    ship_data[param_name] = param_value

            return ship_data

        except Exception as e:
            logger.error(f"Failed to parse infobox for {page_title}: {e}")
            return {"Ship": page_title, "Link": f"{self.base_url}/wiki/{quote(page_title)}"}

    def _clean_wikitext(self, text: str) -> str:
        """Clean wikitext markup from text.

        Args:
            text: Text with wiki markup

        Returns:
            Cleaned text
        """
        # Parse and strip all wiki markup
        wikicode = mwparserfromhell.parse(text)
        
        # Convert wikilinks to plain text
        for wikilink in wikicode.filter_wikilinks():
            if wikilink.text:
                wikicode.replace(wikilink, str(wikilink.text))
            else:
                wikicode.replace(wikilink, str(wikilink.title))
        
        # Remove templates but keep their content if visible
        for template in wikicode.filter_templates():
            template_name = str(template.name).strip().lower()
            # Keep icon names or similar
            if "icon" in template_name or "image" in template_name:
                wikicode.replace(template, str(template.name))
            else:
                wikicode.remove(template)
        
        # Strip remaining markup
        text = wikicode.strip_code()
        
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        
        return text

    async def scrape_ship_details(self, page_title: str) -> Optional[Dict[str, Any]]:
        """Scrape ship details via MediaWiki API.

        Args:
            page_title: Ship page title

        Returns:
            Dictionary with ship data or None if failed
        """
        wikitext = await self.get_page_wikitext(page_title)
        if not wikitext:
            return None

        ship_data = self.parse_ship_infobox(wikitext, page_title)
        return ship_data

    async def scrape_all_ships(self, page_titles: List[str]) -> List[Dict[str, Any]]:
        """Scrape all ships concurrently via MediaWiki API.

        Args:
            page_titles: List of ship page titles

        Returns:
            List of ship data dictionaries
        """
        logger.info(f"Starting MediaWiki API scrape of {len(page_titles)} ships")

        tasks = [self.scrape_ship_details(title) for title in page_titles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        ships = []
        for result in results:
            if isinstance(result, dict):
                ships.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Ship scrape failed with exception: {result}")

        logger.info(f"Successfully scraped {len(ships)}/{len(page_titles)} ships")
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