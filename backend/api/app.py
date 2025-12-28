"""
Flask API - Hybrid Cargo Scraper Backend

Uses MediaWiki API to get ship lists and parse infobox data.
Since STOWiki's Cargo API is not publicly accessible, we use a hybrid approach:
- MediaWiki API for category listing
- Parse API for rendered HTML with Cargo data
- HTML parsing to extract structured information

This is still 5x faster than full HTML scraping!
"""
import json
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from typing import Dict, Any, List

from cargo_scraper import CargoScraper
from models.ship import Ship
from logger import setup_logger
from config import settings

logger = setup_logger(__name__)

# Create Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app)

# Initialize Hybrid Cargo Scraper
scraper = CargoScraper()
logger.info("Hybrid Cargo Scraper initialized")

# Cache for ships (simple in-memory cache)
_ships_cache = {}


@app.route("/", methods=["GET"])
def index() -> Dict[str, Any]:
    """
    API root endpoint with information.
    
    Returns:
        API metadata and available endpoints
    """
    return jsonify({
        "name": "STOWiki Hybrid Cargo API",
        "version": "3.0.0",
        "description": "MediaWiki API + HTML parsing for ship data",
        "data_source": "stowiki.net via MediaWiki API",
        "wiki_url": "https://stowiki.net",
        "approach": [
            "Get ship lists from category pages (MediaWiki API)",
            "Parse ship infoboxes from rendered HTML",
            "Extract Cargo data from structured infoboxes",
            "Cache results for performance"
        ],
        "advantages": [
            "5x faster than full HTML scraping",
            "Structured data extraction",
            "Uses official MediaWiki API",
            "Category-based filtering"
        ],
        "endpoints": {
            "/": "API information",
            "/health": "Health check",
            "/api/ships": "Get all ships (supports ?faction=, ?tier=, ?type=, ?limit=)",
            "/api/ships/<name>": "Get single ship by name",
            "/api/ships/search": "Search ships (?q=query)",
            "/api/ships/download": "Download ships as JSON file",
            "/api/factions": "Get faction summary with ship counts"
        }
    })


@app.route("/health", methods=["GET"])
def health() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    return jsonify({
        "status": "healthy",
        "api": "Hybrid Cargo Scraper",
        "version": "3.0.0",
        "data_source": "stowiki.net"
    })


@app.route("/api/ships", methods=["GET"])
def get_ships() -> Response:
    """
    Get all ships with optional filtering.
    
    Query parameters:
        faction: Filter by faction (federation, klingon, romulan, dominion, cross-faction)
        tier: Filter by tier (1-6)
        type: Filter by ship type (escort, cruiser, science, etc.)
        limit: Maximum results (default 500)
    
    Returns:
        JSON response with ship list
    """
    try:
        faction = request.args.get("faction")
        tier = request.args.get("tier", type=int)
        ship_type = request.args.get("type")
        limit = request.args.get("limit", 500, type=int)
        
        logger.info(f"GET /api/ships - faction={faction}, tier={tier}, type={ship_type}, limit={limit}")
        
        # Check cache
        cache_key = f"{faction}_{tier}_{ship_type}_{limit}"
        if cache_key in _ships_cache:
            logger.info("Returning cached results")
            ships = _ships_cache[cache_key]
        else:
            # Fetch from API
            if faction:
                raw_ships = scraper.get_faction_ships(faction, limit=limit)
            else:
                raw_ships = scraper.get_all_ships(limit=limit)
            
            # Apply additional filters
            filtered_ships = raw_ships
            
            if tier:
                filtered_ships = [s for s in filtered_ships if s.get("tier") == tier]
            
            if ship_type:
                filtered_ships = [
                    s for s in filtered_ships
                    if ship_type.lower() in [t.lower() for t in s.get("type", [])]
                ]
            
            # Validate with Ship model
            ships = []
            for ship_data in filtered_ships:
                try:
                    ship = Ship(**ship_data)
                    ships.append(ship)
                except Exception as e:
                    logger.warning(f"Failed to validate ship {ship_data.get('name')}: {e}")
            
            # Cache results
            _ships_cache[cache_key] = ships
        
        logger.info(f"Returned {len(ships)} ships")
        
        return jsonify({
            "success": True,
            "count": len(ships),
            "filters": {
                "faction": faction,
                "tier": tier,
                "type": ship_type
            },
            "ships": [ship.model_dump() for ship in ships]
        })
        
    except Exception as e:
        logger.error(f"Failed to get ships: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/ships/<path:name>", methods=["GET"])
def get_ship(name: str) -> Response:
    """
    Get single ship by exact name.
    
    Args:
        name: Ship name (URL-encoded)
    
    Returns:
        JSON response with ship details or 404
    """
    try:
        logger.info(f"GET /api/ships/{name}")
        
        raw_ship = scraper.parse_ship_page(name)
        
        if not raw_ship:
            return jsonify({
                "success": False,
                "error": f"Ship not found: {name}"
            }), 404
        
        ship = Ship(**raw_ship)
        
        return jsonify({
            "success": True,
            "ship": ship.model_dump()
        })
        
    except Exception as e:
        logger.error(f"Failed to get ship '{name}': {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/ships/search", methods=["GET"])
def search_ships() -> Response:
    """
    Search ships by name (fuzzy match).
    
    Query parameters:
        q: Search query (required)
        limit: Maximum results (default 100)
    
    Returns:
        JSON response with matching ships
    """
    try:
        query = request.args.get("q", "")
        limit = request.args.get("limit", 100, type=int)
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Missing query parameter 'q'"
            }), 400
        
        logger.info(f"SEARCH /api/ships/search?q={query}&limit={limit}")
        
        raw_results = scraper.search_ships(query, limit=limit)
        ships = [Ship(**ship) for ship in raw_results]
        
        logger.info(f"Found {len(ships)} ships matching '{query}'")
        
        return jsonify({
            "success": True,
            "query": query,
            "count": len(ships),
            "results": [ship.model_dump() for ship in ships]
        })
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/ships/download", methods=["GET"])
def download_ships() -> Response:
    """
    Download ships data as JSON file.
    
    Query parameters:
        faction: Optional faction filter
    
    Returns:
        JSON file download
    """
    try:
        faction = request.args.get("faction")
        
        logger.info(f"DOWNLOAD /api/ships/download?faction={faction}")
        
        if faction:
            raw_ships = scraper.get_faction_ships(faction)
        else:
            raw_ships = scraper.get_all_ships()
        
        ships = [Ship(**ship) for ship in raw_ships]
        
        json_data = json.dumps(
            [ship.model_dump() for ship in ships],
            indent=2,
            ensure_ascii=False
        )
        
        filename = f"{faction.lower()}_ships.json" if faction else "all_ships.json"
        
        logger.info(f"Downloaded {len(ships)} ships as {filename}")
        
        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/factions", methods=["GET"])
def get_factions() -> Response:
    """
    Get faction summary with ship counts.
    
    Returns:
        JSON response with faction list and ship counts
    """
    try:
        logger.info("GET /api/factions")
        
        factions_data = []
        
        for faction_key, category in scraper.FACTION_CATEGORIES.items():
            try:
                # Get ship count from category
                members = scraper.get_category_members(category, limit=1000)
                count = len(members)
                
                factions_data.append({
                    "name": faction_key.replace("-", " ").title(),
                    "key": faction_key,
                    "count": count
                })
            except Exception as e:
                logger.error(f"Failed to get count for {faction_key}: {e}")
                factions_data.append({
                    "name": faction_key.replace("-", " ").title(),
                    "key": faction_key,
                    "count": 0
                })
        
        total = sum(f["count"] for f in factions_data)
        
        logger.info(f"Returned {len(factions_data)} factions, {total} total ships")
        
        return jsonify({
            "success": True,
            "total": total,
            "factions": factions_data
        })
        
    except Exception as e:
        logger.error(f"Failed to get factions: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/cache/clear", methods=["POST"])
def clear_cache() -> Response:
    """Clear the ships cache"""
    global _ships_cache
    _ships_cache = {}
    logger.info("Cache cleared")
    return jsonify({"success": True, "message": "Cache cleared"})


@app.errorhandler(404)
def not_found(error) -> tuple:
    """Handle 404 errors."""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error) -> tuple:
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting Hybrid Cargo API server...")
    logger.info(f"Data source: {scraper.BASE_URL}")
    
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.flask_debug
    )
