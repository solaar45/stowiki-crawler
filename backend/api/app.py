"""Main Flask application."""
import asyncio
import json
from flask import Flask, jsonify, Response
from flask_cors import CORS
from typing import Dict, Any

from config import settings
from logger import setup_logger
from scraper import STOWikiScraper
from transformers import ShipTransformer

logger = setup_logger(__name__)

# Create Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app)


def run_async(coro):
    """Helper to run async functions in Flask routes.
    
    Args:
        coro: Async coroutine to run
        
    Returns:
        Result of the coroutine
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route("/", methods=["GET"])
def index() -> Dict[str, Any]:
    """API root endpoint.
    
    Returns:
        JSON with API information
    """
    return jsonify({
        "name": "STO Wiki Crawler API",
        "version": "2.0.0",
        "endpoints": {
            "/": "API information",
            "/health": "Health check",
            "/scrape/dominion-ships": "Scrape Dominion starships",
            "/scrape/dominion-ships/download": "Download scraped data as JSON"
        }
    })


@app.route("/health", methods=["GET"])
def health() -> Dict[str, str]:
    """Health check endpoint.
    
    Returns:
        JSON with health status
    """
    return jsonify({"status": "healthy"})


@app.route("/scrape/dominion-ships", methods=["GET"])
def scrape_dominion_ships() -> Response:
    """Scrape all Dominion playable starships.
    
    Returns:
        JSON response with ship data
    """
    try:
        logger.info("Starting Dominion ships scrape")
        
        # Run async scraper
        scraper = STOWikiScraper()
        raw_ships = run_async(scraper.scrape_dominion_ships())
        
        # Transform to validated models
        ships = ShipTransformer.transform_ships(raw_ships)
        
        # Convert to dictionaries
        ships_dict = ShipTransformer.ships_to_dict(ships)
        
        logger.info(f"Scrape completed: {len(ships)} ships")
        
        return jsonify({
            "success": True,
            "count": len(ships),
            "ships": ships_dict
        })
        
    except Exception as e:
        logger.error(f"Scrape failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/scrape/dominion-ships/download", methods=["GET"])
def download_dominion_ships() -> Response:
    """Download Dominion ships data as JSON file.
    
    Returns:
        JSON file download
    """
    try:
        logger.info("Starting Dominion ships scrape for download")
        
        # Run async scraper
        scraper = STOWikiScraper()
        raw_ships = run_async(scraper.scrape_dominion_ships())
        
        # Transform to validated models
        ships = ShipTransformer.transform_ships(raw_ships)
        
        # Convert to dictionaries
        ships_dict = ShipTransformer.ships_to_dict(ships)
        
        # Create JSON response
        json_data = json.dumps(ships_dict, indent=2, ensure_ascii=False)
        
        logger.info(f"Download ready: {len(ships)} ships")
        
        return Response(
            json_data,
            mimetype="application/json",
            headers={
                "Content-Disposition": "attachment; filename=dominion_ships.json"
            }
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
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
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.flask_debug
    )