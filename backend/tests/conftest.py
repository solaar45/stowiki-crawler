"""Pytest configuration and fixtures."""
import pytest
from bs4 import BeautifulSoup


@pytest.fixture
def sample_ship_list_html():
    """Sample HTML for ship list page."""
    return """
    <table class="sortable">
        <tr><th>Name</th><th>Ship</th></tr>
        <tr>
            <td>1</td>
            <td><a href="/wiki/Test_Ship">Test Ship</a></td>
        </tr>
    </table>
    """


@pytest.fixture
def sample_ship_detail_html():
    """Sample HTML for ship detail page."""
    return """
    <div class="missionname">Test Strike Ship</div>
    <div class="label">Tier:</div>
    <div class="entry">5</div>
    <div class="label">Faction:</div>
    <div class="entry">Dominion</div>
    <div class="label">Hull:</div>
    <div class="entry">Lvl 65: 45,000</div>
    <div class="label">Weapons:</div>
    <div class="entry">Fore 4 Aft 3 Can equip dual cannons.</div>
    <div class="label">Turn rate:</div>
    <div class="entry">15.0</div>
    <div class="label">Released:</div>
    <div class="entry">June 3, 2023</div>
    """


@pytest.fixture
def sample_raw_ship_data():
    """Sample raw ship data from scraper."""
    return {
        "name": "Test Strike Ship",
        "link": "https://sto.fandom.com/wiki/Test_Ship",
        "Tier": 5,
        "Faction": "Dominion",
        "Max Hull": 45000,
        "Fore Weapons": 4,
        "Aft Weapons": 3,
        "Dual Cannons": "yes",
        "Turn rate": 15.0,
        "Released": "2023-06-03"
    }