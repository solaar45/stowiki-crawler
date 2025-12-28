"""
Flask API - Cargo-powered backend

Direct database access via STOWiki's Cargo extension.
No scraping needed - just query the structured database!

This is 10x simpler than the MediaWiki Parse API approach:
- No template parsing
- No complex transformations
- No async/await complexity
- Just clean HTTP → JSON queries
"""
import json
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from typing import Dict, Any, List

from cargo_api import CargoAPIClient
from models.ship import Ship
from logger import setup_logger
from config import settings

logger = setup_logger(__name__)

# Create Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app)

# Initialize Cargo API client
cargo = CargoAPIClient()
logger.info("Cargo API client initialized")


@app.route("/", methods=["GET"])
def index() -> Dict[str, Any]:
    """
    API root endpoint with information.
    
    Returns:
        API metadata and available endpoints
    """
    return jsonify({
        "name": "STOWiki Cargo API",
        "version": "3.0.0",
        "description": "Direct Cargo database access - 10x simpler, 10x faster!",
        "data_source": "stowiki.net Cargo database",
        "wiki_url": "https://stowiki.net",
        "advantages": [
            "No scraping - direct database queries",
            "Structured JSON responses",
            "Instant results (no parsing overhead)",
            "SQL-like filtering support",
            "Bulk queries (all ships in one request)"
        ],
        "endpoints": {
            "/": "API information",
            "/health": "Health check",
            "/api/ships": "Get all ships (supports ?faction=, ?tier=, ?type=, ?limit=)",
            "/api/ships/<name>": "Get single ship by name",
            "/api/ships/search": "Search ships (?q=query)",
            "/api/ships/download": "Download ships as JSON file",
            "/api/factions": "Get faction summary with ship counts",
            "/api/types": "Get all ship types"
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
        "api": "Cargo API",
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
        limit: Maximum results (default 1000)
    
    Returns:
        JSON response with ship list
    
    Examples:
        GET /api/ships
        GET /api/ships?faction=dominion
        GET /api/ships?tier=6&type=escort
        GET /api/ships?faction=federation&limit=50
    """
    try:
        faction = request.args.get("faction")
        tier = request.args.get("tier", type=int)
        ship_type = request.args.get("type")
        limit = request.args.get("limit", 1000, type=int)
        
        logger.info(f"GET /api/ships - faction={faction}, tier={tier}, type={ship_type}, limit={limit}")
        
        # Query Cargo database
        raw_ships = cargo.get_all_ships(
            faction=faction,
            tier=tier,
            ship_type=ship_type,
            limit=limit
        )
        
        # Validate and enrich with Ship model
        ships = [Ship(**ship) for ship in raw_ships]
        
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
    
    Example:
        GET /api/ships/Jem'Hadar Strike Ship
    """
    try:
        logger.info(f"GET /api/ships/{name}")
        
        raw_ship = cargo.get_ship_by_name(name)
        
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
    
    Examples:
        GET /api/ships/search?q=enterprise
        GET /api/ships/search?q=jem'hadar&limit=20
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
        
        raw_results = cargo.search_ships(query, limit=limit)
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
    
    Example:
        GET /api/ships/download
        GET /api/ships/download?faction=dominion
    """
    try:
        faction = request.args.get("faction")
        
        logger.info(f"DOWNLOAD /api/ships/download?faction={faction}")
        
        raw_ships = cargo.get_all_ships(faction=faction)
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
    
    Example:
        GET /api/factions
        
        Response:
        {
            "success": true,
            "total": 850,
            "factions": [
                {"name": "Dominion", "count": 43, "key": "dominion"},
                {"name": "United Federation of Planets", "count": 287, "key": "federation"},
                ...
            ]
        }
    """
    try:
        logger.info("GET /api/factions")
        
        summary = cargo.get_faction_summary()
        
        # Map to user-friendly keys
        faction_map = {
            "United Federation of Planets": "federation",
            "Klingon Empire": "klingon",
            "Romulan Republic": "romulan",
            "Dominion": "dominion",
            "Cross-Faction": "cross-faction"
        }
        
        factions = [
            {
                "name": name,
                "count": count,
                "key": faction_map.get(name, name.lower().replace(" ", "-"))
            }
            for name, count in summary.items()
        ]
        
        total = sum(summary.values())
        
        logger.info(f"Returned {len(factions)} factions, {total} total ships")
        
        return jsonify({
            "success": True,
            "total": total,
            "factions": factions
        })
        
    except Exception as e:
        logger.error(f"Failed to get factions: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/types", methods=["GET"])
def get_ship_types() -> Response:
    """
    Get all unique ship types.
    
    Returns:
        JSON response with ship type list
    
    Example:
        GET /api/types
        
        Response:
        {
            "success": true,
            "count": 15,
            "types": ["Carrier", "Cruiser", "Destroyer", "Escort", ...]
        }
    """
    try:
        logger.info("GET /api/types")
        
        types = cargo.get_ship_types()
        
        logger.info(f"Returned {len(types)} ship types")
        
        return jsonify({
            "success": True,
            "count": len(types),
            "types": types
        })
        
    except Exception as e:
        logger.error(f"Failed to get types: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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
    logger.info("Starting Cargo API server...")
    logger.info(f"Data source: {cargo.BASE_URL}")
    
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.flask_debug
    )
