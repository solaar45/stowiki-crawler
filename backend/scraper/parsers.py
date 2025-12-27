"""HTML parsers for extracting ship data from wiki pages."""
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from datetime import datetime
import re

from logger import setup_logger

logger = setup_logger(__name__)


class ShipListParser:
    """Parser for ship list pages."""
    
    def __init__(self, soup: BeautifulSoup, base_url: str):
        self.soup = soup
        self.base_url = base_url
    
    def extract_ship_urls(self) -> List[str]:
        """Extract ship detail page URLs from a sortable table.
        
        Returns:
            List of absolute URLs to ship detail pages
        """
        ship_urls = []
        
        # Find all sortable tables (ship lists)
        tables = self.soup.find_all("table", class_="sortable")
        
        for table in tables:
            rows = table.find_all("tr")
            
            # Skip header row
            for row in rows[1:]:
                columns = row.find_all("td")
                
                # Ship name is typically in the second column
                if len(columns) >= 2:
                    link_tag = columns[1].find("a")
                    if link_tag and link_tag.get("href"):
                        relative_url = link_tag["href"]
                        absolute_url = self.base_url + relative_url
                        ship_urls.append(absolute_url)
        
        return ship_urls


class ShipPageParser:
    """Parser for individual ship detail pages."""
    
    def __init__(self, soup: BeautifulSoup, url: str):
        self.soup = soup
        self.url = url
    
    def extract_ship_data(self) -> Dict[str, Any]:
        """Extract all ship data from the page.
        
        Returns:
            Dictionary with ship data
        """
        data = {
            "link": self.url,
            "name": self._extract_ship_name(),
        }
        
        # Extract data from label-entry pairs
        infobox_data = self._extract_infobox_data()
        data.update(infobox_data)
        
        return data
    
    def _extract_ship_name(self) -> str:
        """Extract ship name from the page.
        
        Returns:
            Ship name or 'Unknown'
        """
        mission_name_div = self.soup.find("div", class_="missionname")
        if mission_name_div:
            return mission_name_div.get_text().strip()
        return "Unknown"
    
    def _extract_infobox_data(self) -> Dict[str, Any]:
        """Extract data from infobox label-entry pairs.
        
        Returns:
            Dictionary with extracted data
        """
        data = {}
        
        # Find all label-entry pairs
        label_divs = self.soup.find_all("div", class_="label")
        entry_divs = self.soup.find_all("div", class_="entry")
        
        # Match labels with entries
        for i, label_div in enumerate(label_divs):
            if i >= len(entry_divs):
                break
                
            label = label_div.get_text().strip()
            entry_div = entry_divs[i]
            
            # Extract entry content
            entry_content = self._extract_entry_content(entry_div)
            
            if label and entry_content:
                # Remove trailing colon from label
                clean_label = label.rstrip(":")
                data[clean_label] = entry_content
        
        # Post-process the data
        return self._postprocess_data(data)
    
    def _extract_entry_content(self, entry_div: Tag) -> str:
        """Extract text content from an entry div.
        
        Args:
            entry_div: BeautifulSoup Tag for entry div
            
        Returns:
            Cleaned text content
        """
        content = []
        
        for element in entry_div.descendants:
            if element.name == "img":
                # Extract alt text from images
                if element.get("alt"):
                    content.append(element["alt"])
            elif element.name not in ["small", "span", "i", "a", "td"] and element.string:
                text = element.string.strip()
                if text:
                    content.append(text)
        
        # Join and clean
        text = " ".join(content)
        text = text.replace("\n", " ").replace("\u00a0", " ")
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        
        return text.strip()
    
    def _postprocess_data(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Post-process extracted data for consistency.
        
        Args:
            data: Raw extracted data
            
        Returns:
            Processed data with type conversions
        """
        processed = {}
        
        for key, value in data.items():
            # Skip certain fields
            if key in ["Rank", "Console (T5-U)"]:
                continue
            
            # Process specific fields
            if key == "Hull":
                processed["Max Hull"] = self._extract_max_hull(value)
            elif key == "Weapons":
                weapons_data = self._parse_weapons(value)
                processed.update(weapons_data)
            elif key == "Released":
                processed[key] = self._parse_date(value)
            elif key == "Tier":
                processed[key] = self._parse_int(value)
            elif key in ["Inertia rating", "Device slots"]:
                processed[key] = self._parse_int(value)
            elif key in ["Hull modifier", "Shield modifier", "Impulse modifier", "Turn rate"]:
                processed[key] = self._parse_float(value)
            else:
                processed[key] = value
        
        return processed
    
    def _extract_max_hull(self, hull_text: str) -> Optional[int]:
        """Extract maximum hull value from hull text.
        
        Args:
            hull_text: Raw hull text from wiki
            
        Returns:
            Maximum hull value or None
        """
        # Look for level 65 values
        patterns = [
            r"Lvl 65 ?:?\s*([\d,]+)",
            r"Lvl 65 T5U ?:?\s*([\d,]+)",
            r"Level 50\+ ?:?\s*([\d,]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, hull_text)
            if match:
                hull_str = match.group(1).replace(",", "")
                return self._parse_int(hull_str)
        
        # Fallback: try to extract any number
        numbers = re.findall(r"[\d,]+", hull_text)
        if numbers:
            hull_str = numbers[-1].replace(",", "")
            return self._parse_int(hull_str)
        
        return None
    
    def _parse_weapons(self, weapons_text: str) -> Dict[str, Any]:
        """Parse weapons configuration.
        
        Args:
            weapons_text: Raw weapons text
            
        Returns:
            Dictionary with fore, aft, and dual cannons info
        """
        # Remove common prefixes
        text = weapons_text.replace("Fore ", "").replace("Aft ", "")
        
        # Extract fore and aft numbers
        parts = text.split()
        fore = None
        aft = None
        
        for i, part in enumerate(parts):
            if fore is None and part.isdigit():
                fore = int(part)
            elif fore is not None and aft is None and part.isdigit():
                aft = int(part)
                break
        
        # Check for dual cannons
        can_equip_dual = "dual cannons" in weapons_text.lower()
        
        return {
            "Fore Weapons": fore,
            "Aft Weapons": aft,
            "Dual Cannons": "yes" if can_equip_dual else "no"
        }
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date string to ISO format.
        
        Args:
            date_text: Date in format like 'June 3, 2023'
            
        Returns:
            ISO formatted date string or None
        """
        try:
            date_obj = datetime.strptime(date_text, "%B %d, %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"Failed to parse date: {date_text}")
            return None
    
    def _parse_int(self, value: str) -> Optional[int]:
        """Safely parse integer value.
        
        Args:
            value: String to parse
            
        Returns:
            Integer value or None
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value: str) -> Optional[float]:
        """Safely parse float value.
        
        Args:
            value: String to parse
            
        Returns:
            Float value or None
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return None