"""
STO Wiki API Server

Features:
- Instant ship queries from SQLite (<50ms)
- Background sync (configurable interval)
- Change history tracking
- Real-time sync status
"""
import os
import sys
import logging
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import io

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import ShipDatabase
from scraper.cargo_scraper import CargoShipScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize database and scraper
SYNC_INTERVAL_HOURS = int(os.getenv('SYNC_INTERVAL_HOURS', 8))
DB_PATH = os.getenv('DB_PATH', 'ships.db')

db = ShipDatabase(db_path=DB_PATH, sync_interval_hours=SYNC_INTERVAL_HOURS)
scraper = CargoShipScraper()

logger.info(f"API initialized (DB: {DB_PATH}, Sync Interval: {SYNC_INTERVAL_HOURS}h)")


@app.route("/", methods=["GET"])
def index():
    """API info"""
    status = db.get_sync_status()
    
    return jsonify({
        "name": "STO Wiki Ship Database API",
        "version": "2.0.0",
        "description": "SQLite-backed ship database with automatic sync",
        "features": [
            "Sub-50ms query performance",
            f"Background sync every {SYNC_INTERVAL_HOURS}h",
            "Full change tracking",
            "Smart sync (only new/changed ships)"
        ],
        "endpoints": [
            "/api/ships - Get ships (with filters)",
            "/api/factions - Get faction summary",
            "/api/ships/search - Search ships",
            "/api/ships/download - Download all ships",
            "/api/history - Get change history",
            "/api/history/<ship_name> - Get ship change history",
            "/api/sync/status - Get sync status",
            "/api/sync/trigger - Trigger manual sync",
            "/api/sync/config - Get/update sync config"
        ],
        "status": {
            "total_ships": status['total_ships'],
            "last_sync": status['last_full_sync'],
            "next_sync": status.get('next_sync'),
            "is_syncing": status['is_syncing']
        }
    })


@app.route("/api/ships", methods=["GET"])
def get_ships():
    """
    Get ships from database (instant response)
    
    Query params:
    - faction: Filter by faction key (federation, klingon, etc.)
    - tier: Filter by tier (1-6)
    - limit: Max results (default 500)
    """
    start_time = datetime.now()
    
    faction = request.args.get('faction')
    tier = request.args.get('tier', type=int)
    limit = request.args.get('limit', 500, type=int)
    
    # Limit max results
    limit = min(limit, 1000)
    
    try:
        ships = db.get_ships(faction=faction, tier=tier, limit=limit)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return jsonify({
            "success": True,
            "count": len(ships),
            "ships": ships,
            "filters": {
                "faction": faction,
                "tier": tier
            },
            "source": "database",
            "response_time_ms": duration_ms
        })
    
    except Exception as e:
        logger.error(f"Error getting ships: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/factions", methods=["GET"])
def get_factions():
    """Get faction summary"""
    try:
        factions = db.get_faction_summary()
        total = sum(f['count'] for f in factions)
        
        return jsonify({
            "success": True,
            "total": total,
            "factions": factions
        })
    
    except Exception as e:
        logger.error(f"Error getting factions: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/ships/search", methods=["GET"])
def search_ships():
    """
    Search ships by name
    
    Query params:
    - q: Search query (required)
    - limit: Max results (default 50)
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 50, type=int)
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter 'q' is required"
        }), 400
    
    try:
        # Get all ships and filter by name
        all_ships = db.get_ships(limit=1000)
        
        # Case-insensitive search
        query_lower = query.lower()
        results = [
            ship for ship in all_ships
            if query_lower in ship['name'].lower()
        ][:limit]
        
        return jsonify({
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        })
    
    except Exception as e:
        logger.error(f"Error searching ships: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/ships/download", methods=["GET"])
def download_ships():
    """Download all ships as JSON"""
    faction = request.args.get('faction')
    
    try:
        ships = db.get_ships(faction=faction, limit=1000)
        
        # Create JSON file in memory
        json_data = json.dumps(ships, indent=2)
        buffer = io.BytesIO(json_data.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"sto_ships_{faction or 'all'}_{datetime.now().strftime('%Y%m%d')}.json"
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error downloading ships: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """
    Get change history
    
    Query params:
    - limit: Max results (default 100)
    - ship: Optional filter by ship name
    """
    limit = request.args.get('limit', 100, type=int)
    ship_name = request.args.get('ship')
    
    try:
        changes = db.get_change_history(limit=limit, ship_name=ship_name)
        
        return jsonify({
            "success": True,
            "count": len(changes),
            "changes": changes
        })
    
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/history/<ship_name>", methods=["GET"])
def get_ship_history(ship_name):
    """Get change history for specific ship"""
    limit = request.args.get('limit', 50, type=int)
    
    try:
        changes = db.get_change_history(limit=limit, ship_name=ship_name)
        
        return jsonify({
            "success": True,
            "ship_name": ship_name,
            "count": len(changes),
            "changes": changes
        })
    
    except Exception as e:
        logger.error(f"Error getting ship history: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/sync/status", methods=["GET"])
def get_sync_status():
    """Get current sync status"""
    try:
        status = db.get_sync_status()
        
        return jsonify({
            "success": True,
            "status": status
        })
    
    except Exception as e:
        logger.error(f"Error getting sync status: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/sync/trigger", methods=["POST"])
def trigger_sync():
    """
    Trigger manual sync
    
    JSON body:
    - type: 'smart' (default) or 'full'
    """
    data = request.get_json() or {}
    sync_type = data.get('type', 'smart')
    
    status = db.get_sync_status()
    
    if status['is_syncing']:
        return jsonify({
            "success": False,
            "error": "Sync already in progress"
        }), 409
    
    try:
        # Start sync in background thread
        if sync_type == 'full':
            thread = threading.Thread(target=db.full_sync, args=(scraper,), daemon=True)
        else:
            thread = threading.Thread(target=db.smart_sync, args=(scraper,), daemon=True)
        
        thread.start()
        
        return jsonify({
            "success": True,
            "message": f"{sync_type.capitalize()} sync started",
            "type": sync_type
        })
    
    except Exception as e:
        logger.error(f"Error triggering sync: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/sync/config", methods=["GET", "PUT"])
def sync_config():
    """Get or update sync configuration"""
    
    if request.method == "GET":
        status = db.get_sync_status()
        
        return jsonify({
            "success": True,
            "config": {
                "sync_interval_hours": status['sync_interval_hours'],
                "last_sync": status['last_full_sync'],
                "next_sync": status.get('next_sync')
            }
        })
    
    else:  # PUT
        data = request.get_json() or {}
        new_interval = data.get('sync_interval_hours')
        
        if not new_interval or not isinstance(new_interval, int) or new_interval < 1:
            return jsonify({
                "success": False,
                "error": "sync_interval_hours must be a positive integer"
            }), 400
        
        try:
            db.update_sync_status(sync_interval_hours=new_interval)
            db.sync_interval_hours = new_interval
            
            # Restart background sync with new interval
            db.stop_background_sync()
            db.start_background_sync(scraper)
            
            return jsonify({
                "success": True,
                "message": f"Sync interval updated to {new_interval} hours",
                "config": {
                    "sync_interval_hours": new_interval
                }
            })
        
        except Exception as e:
            logger.error(f"Error updating sync config: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """Clear cache (deprecated - kept for compatibility)"""
    return jsonify({
        "success": True,
        "message": "Cache clearing not needed with database backend"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting API server on port {port}")
    
    # Initialize on startup
    logger.info("Checking database status...")
    status = db.get_sync_status()
    
    if status['total_ships'] == 0:
        logger.info("No ships in database - triggering initial full sync")
        thread = threading.Thread(target=db.full_sync, args=(scraper,), daemon=True)
        thread.start()
    else:
        logger.info(f"Database contains {status['total_ships']} ships")
    
    # Start background sync
    db.start_background_sync(scraper)
    
    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=port, debug=debug)
