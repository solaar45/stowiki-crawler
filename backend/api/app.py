"""Main Flask application with MediaWiki API support."""
import asyncio
import json
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from typing import Dict, Any

from config import settings
from logger import setup_logger
from mediawiki_scraper import MediaWikiScraper  # NEW: MediaWiki API scraper
from scraper import STOWikiScraper  # Keep old scraper for reference
from transformers import ShipTransformer
from models.faction import Faction
from storage.json_storage import JSONStorage
from storage.database_storage import DatabaseStorage

logger = setup_logger(__name__)

# Create Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app)

# Initialize storage backend
if settings.database_url and settings.database_url != "sqlite:///ships.db":
    storage = DatabaseStorage(settings.database_url)
    logger.info(f"Using database storage: {settings.database_url}")
else:
    storage = JSONStorage("ships.json")
    logger.info("Using JSON file storage")

# Initialize MediaWiki API scraper
scraper = MediaWikiScraper()
logger.info("Using MediaWiki API scraper (10-15x faster!)")


def run_async(coro):
    """Helper to run async functions in Flask routes."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route("/", methods=["GET"])
def index() -> Dict[str, Any]:
    """API root endpoint with information."""
    return jsonify({
        "name": "STO Wiki Crawler API",
        "version": "2.1.0",
        "scraper": "MediaWiki API (10-15x faster!)",
        "wiki_source": "stowiki.net",
        "storage": "database" if isinstance(storage, DatabaseStorage) else "json",
        "cache_enabled": settings.enable_cache,
        "endpoints": {
            "/": "API information",
            "/health": "Health check",
            "/factions": "List all available factions",
            "/scrape/all": "Scrape all factions (MediaWiki API)",
            "/scrape/{faction}": "Scrape specific faction",
            "/ships": "Get all ships (optional ?faction= filter)",
            "/ships/download": "Download all ships as JSON",
            "/ships/count": "Get total ship count",
            "/cache/stats": "Get cache statistics",
            "/cache/clear": "Clear all cached data",
        }
    })


@app.route("/health", methods=["GET"])
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "scraper": "MediaWiki API",
        "storage": type(storage).__name__,
        "cache_enabled": settings.enable_cache,
        "wiki_source": settings.base_url
    })


@app.route("/factions", methods=["GET"])
def list_factions() -> Response:
    """List all available factions."""
    factions = [
        {
            "name": faction.value,
            "key": faction.name.lower(),
            "url": Faction.get_wiki_url(faction)
        }
        for faction in Faction
    ]
    
    return jsonify({
        "success": True,
        "count": len(factions),
        "factions": factions
    })


@app.route("/scrape/all", methods=["GET"])
def scrape_all_factions() -> Response:
    """Scrape all faction ships using MediaWiki API."""
    try:
        logger.info("Starting MediaWiki API scrape of all factions")
        
        all_ships = []
        
        for faction in Faction:
            logger.info(f"Scraping {faction.value} ships via MediaWiki API")
            url = Faction.get_wiki_url(faction)
            
            # Get ship page titles from list page
            ship_titles = run_async(scraper.get_pages_in_category_by_url(url))
            
            # Scrape all ships via API
            raw_ships = run_async(scraper.scrape_all_ships(ship_titles))
            
            # Add faction to raw data
            for ship_data in raw_ships:
                ship_data["Faction"] = faction.value
            
            all_ships.extend(raw_ships)
        
        # Transform to validated models
        ships = ShipTransformer.transform_ships(all_ships)
        
        # Save to storage
        run_async(storage.save_ships(ships))
        
        # Convert to dictionaries
        ships_dict = ShipTransformer.ships_to_dict(ships)
        
        logger.info(f"MediaWiki API scrape completed: {len(ships)} total ships")
        
        return jsonify({
            "success": True,
            "total_count": len(ships),
            "scraper": "MediaWiki API",
            "by_faction": {
                faction.value: len([s for s in ships if s.faction == faction.value])
                for faction in Faction
            },
            "ships": ships_dict
        })
        
    except Exception as e:
        logger.error(f"MediaWiki API scrape failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/scrape/<faction_key>", methods=["GET"])
def scrape_faction(faction_key: str) -> Response:
    """Scrape ships for a specific faction using MediaWiki API."""
    try:
        faction_key_upper = faction_key.upper().replace("-", "_")
        
        try:
            faction = Faction[faction_key_upper]
        except KeyError:
            return jsonify({
                "success": False,
                "error": f"Invalid faction: {faction_key}",
                "valid_factions": [f.name.lower() for f in Faction]
            }), 400
        
        logger.info(f"Starting MediaWiki API scrape of {faction.value} ships")
        
        url = Faction.get_wiki_url(faction)
        
        # Get ship page titles
        ship_titles = run_async(scraper.get_pages_in_category_by_url(url))
        
        # Scrape all ships
        raw_ships = run_async(scraper.scrape_all_ships(ship_titles))
        
        # Add faction
        for ship_data in raw_ships:
            ship_data["Faction"] = faction.value
        
        # Transform
        ships = ShipTransformer.transform_ships(raw_ships)
        
        # Save
        run_async(storage.save_ships(ships))
        
        # Convert
        ships_dict = ShipTransformer.ships_to_dict(ships)
        
        logger.info(f"MediaWiki API scrape completed: {len(ships)} {faction.value} ships")
        
        return jsonify({
            "success": True,
            "faction": faction.value,
            "count": len(ships),
            "scraper": "MediaWiki API",
            "ships": ships_dict
        })
        
    except Exception as e:
        logger.error(f"MediaWiki API scrape failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ships", methods=["GET"])
def get_ships() -> Response:
    """Get ships from storage with optional faction filter."""
    try:
        faction = request.args.get("faction")
        ships = run_async(storage.get_ships(faction=faction))
        ships_dict = ShipTransformer.ships_to_dict(ships)
        
        return jsonify({
            "success": True,
            "count": len(ships),
            "faction_filter": faction,
            "ships": ships_dict
        })
        
    except Exception as e:
        logger.error(f"Failed to get ships: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ships/download", methods=["GET"])
def download_ships() -> Response:
    """Download ships data as JSON file."""
    try:
        faction = request.args.get("faction")
        ships = run_async(storage.get_ships(faction=faction))
        ships_dict = ShipTransformer.ships_to_dict(ships)
        
        json_data = json.dumps(ships_dict, indent=2, ensure_ascii=False)
        
        filename = f"{faction.lower()}_ships.json" if faction else "all_ships.json"
        
        return Response(
            json_data,
            mimetype="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/ships/count", methods=["GET"])
def get_ship_count() -> Response:
    """Get total ship count from storage."""
    try:
        count = run_async(storage.get_ship_count())
        return jsonify({
            "success": True,
            "count": count
        })
    except Exception as e:
        logger.error(f"Failed to get ship count: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/cache/stats", methods=["GET"])
def get_cache_stats() -> Response:
    """Get cache statistics."""
    try:
        stats = run_async(scraper.get_cache_stats())
        return jsonify({
            "success": True,
            "cache": stats
        })
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/cache/clear", methods=["POST"])
def clear_cache() -> Response:
    """Clear all cached data."""
    try:
        count = run_async(scraper.clear_cache())
        return jsonify({
            "success": True,
            "message": f"Cleared {count} cache files",
            "files_cleared": count
        })
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error) -> tuple:
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error) -> tuple:
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Initialize database if using DB storage
    if isinstance(storage, DatabaseStorage):
        run_async(storage.init_db())
    
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.flask_debug
    )