# STO Wiki Ship Database

> **Star Trek Online** ship database with instant queries, automatic updates, and full change tracking.

## ✨ Features

### **v2.0 - SQLite Database Backend**

- ⚡ **Sub-50ms Response Time** - Instant ship queries from SQLite
- 🔄 **Automatic Sync** - Configurable background updates (default 8h)
- 📝 **Change Tracking** - Full audit log of all ship data changes
- 🧠 **Smart Sync** - Only updates new/changed ships (fast!)
- 📈 **History API** - Track when ships are added, updated, or deleted
- 🎯 **Persistent Data** - No re-scraping on server restart

### **Core Features**

- 🚀 **808+ Ships** - Complete database from STOWiki
- 🏴 **Faction Filtering** - Federation, Klingon, Romulan, Dominion, Cross-Faction
- 🔢 **Tier Filtering** - Filter by ship tier (1-6)
- 🔍 **Full-Text Search** - Fast ship name search
- 📥 **JSON Export** - Download filtered ship data
- 📊 **Real-time Stats** - Live faction summaries and counts

---

## 🚀 Quick Start

### **Backend**

```bash
cd backend
pip install -r requirements.txt

# Start API server
python -m api.app

# Server runs on http://localhost:5000
```

**Environment Variables:**

```bash
PORT=5000                    # API port (default: 5000)
DB_PATH=ships.db             # Database path (default: ships.db)
SYNC_INTERVAL_HOURS=8        # Auto-sync interval (default: 8)
DEBUG=false                  # Debug mode
```

### **Frontend**

```bash
cd frontend
npm install

# Start dev server
npm run dev

# App runs on http://localhost:3000
```

---

## 📡 API Endpoints

### **Ship Data**

#### `GET /api/ships`

Get ships from database (instant response)

**Query Parameters:**

- `faction` - Filter by faction key (`federation`, `klingon`, `romulan`, `dominion`, `cross-faction`)
- `tier` - Filter by tier (1-6)
- `limit` - Max results (default: 500, max: 1000)

**Example:**

```bash
curl "http://localhost:5000/api/ships?faction=dominion&tier=6&limit=50"
```

**Response:**

```json
{
  "success": true,
  "count": 24,
  "ships": [...],
  "filters": {
    "faction": "dominion",
    "tier": 6
  },
  "source": "database",
  "response_time_ms": 18
}
```

#### `GET /api/factions`

Get faction summary with ship counts

**Example:**

```bash
curl "http://localhost:5000/api/factions"
```

**Response:**

```json
{
  "success": true,
  "total": 808,
  "factions": [
    {"name": "Federation", "key": "federation", "count": 323},
    {"name": "Klingon", "key": "klingon", "count": 159},
    {"name": "Romulan", "key": "romulan", "count": 113},
    {"name": "Dominion", "key": "dominion", "count": 24},
    {"name": "Cross Faction", "key": "cross-faction", "count": 189}
  ]
}
```

#### `GET /api/ships/search`

Search ships by name

**Query Parameters:**

- `q` - Search query (required)
- `limit` - Max results (default: 50)

**Example:**

```bash
curl "http://localhost:5000/api/ships/search?q=Defiant&limit=10"
```

#### `GET /api/ships/download`

Download ships as JSON file

**Query Parameters:**

- `faction` - Optional faction filter

**Example:**

```bash
curl "http://localhost:5000/api/ships/download?faction=federation" -o ships.json
```

---

### **Change History**

#### `GET /api/history`

Get change history (all ships)

**Query Parameters:**

- `limit` - Max results (default: 100)
- `ship` - Optional filter by ship name

**Example:**

```bash
curl "http://localhost:5000/api/history?limit=50"
```

**Response:**

```json
{
  "success": true,
  "count": 50,
  "changes": [
    {
      "id": 1234,
      "ship_name": "Fleet Defiant Tactical Escort Retrofit",
      "change_type": "updated",
      "changed_fields": ["hull", "shieldmod"],
      "old_values": {"hull": 33000, "shieldmod": 0.9},
      "new_values": {"hull": 35000, "shieldmod": 1.0},
      "timestamp": "2025-12-28T10:30:00"
    }
  ]
}
```

#### `GET /api/history/<ship_name>`

Get change history for specific ship

**Example:**

```bash
curl "http://localhost:5000/api/history/Defiant%20Tactical%20Escort"
```

---

### **Sync Management**

#### `GET /api/sync/status`

Get current sync status

**Example:**

```bash
curl "http://localhost:5000/api/sync/status"
```

**Response:**

```json
{
  "success": true,
  "status": {
    "last_full_sync": "2025-12-28T10:00:00",
    "last_partial_sync": null,
    "is_syncing": false,
    "total_ships": 808,
    "sync_interval_hours": 8,
    "next_sync": "2025-12-28T18:00:00",
    "needs_sync": false,
    "ships_added": 5,
    "ships_updated": 12,
    "ships_deleted": 0,
    "last_sync_duration_seconds": 180
  }
}
```

#### `POST /api/sync/trigger`

Trigger manual sync

**Request Body:**

```json
{
  "type": "smart"  // or "full"
}
```

**Example:**

```bash
curl -X POST "http://localhost:5000/api/sync/trigger" \
  -H "Content-Type: application/json" \
  -d '{"type": "smart"}'
```

**Response:**

```json
{
  "success": true,
  "message": "Smart sync started",
  "type": "smart"
}
```

#### `GET /api/sync/config`

Get sync configuration

#### `PUT /api/sync/config`

Update sync configuration

**Request Body:**

```json
{
  "sync_interval_hours": 12
}
```

**Example:**

```bash
curl -X PUT "http://localhost:5000/api/sync/config" \
  -H "Content-Type: application/json" \
  -d '{"sync_interval_hours": 12}'
```

---

## 💾 Database Schema

### **ships** Table

Stores all ship data with full metadata:

- **Basic Info**: name, faction, tier, type, rank, cost
- **Stats**: hull, shields, turn rate, impulse, inertia
- **Weapons**: fore, aft, can equip cannons
- **Consoles**: tactical, engineering, science, universal
- **Equipment**: hangar bays, bridge officers, abilities
- **Admiralty**: TAC/ENG/SCI stats
- **Metadata**: wiki_url, data_hash, timestamps

### **change_log** Table

Audit log for all changes:

- `ship_name` - Ship that changed
- `change_type` - created, updated, or deleted
- `changed_fields` - Array of field names that changed
- `old_values` - Previous values (JSON)
- `new_values` - New values (JSON)
- `timestamp` - When the change occurred

### **sync_status** Table

Sync configuration and statistics:

- `last_full_sync` - Last full sync timestamp
- `is_syncing` - Currently syncing flag
- `total_ships` - Total ships in database
- `sync_interval_hours` - Auto-sync interval
- `ships_added` - Ships added in last sync
- `ships_updated` - Ships updated in last sync
- `ships_deleted` - Ships deleted in last sync
- `last_sync_duration_seconds` - Last sync duration

---

## 🛠️ Architecture

```
┌───────────────────┐
│  React Frontend   │
│  (Vite + TS)      │
└───────┬───────────┘
        │ HTTP/REST
        │
┌───────┴───────────┐
│   Flask API       │
│   (Python)        │
└─────┬────────┬─────┘
      │          │
      │          │
┌─────┴─────┐  │
│   SQLite    │  │
│ (<50ms)    │  │ Background
│            │  │ Sync Thread
└────────────┘  │
                  │
            ┌─────┴─────┐
            │  STOWiki   │
            │  Cargo API │
            │ (MediaWiki)│
            └────────────┘
```

### **Sync Strategies**

#### **Smart Sync** (Recommended)

1. Fetch category members (fast)
2. Compare with database
3. Parse only new ships
4. Sample 10% of existing ships for updates
5. Remove deleted ships

**Time:** ~2-5 minutes for incremental updates

#### **Full Sync**

1. Parse all ships from all factions
2. Update entire database

**Time:** ~30-60 minutes for complete refresh

---

## 📊 Performance

| Operation | Live Parsing | SQLite Cache |
| --------- | ------------ | ------------ |
| **Get 500 ships** | 30-60s | **<50ms** ⚡ |
| **Filter by faction** | 10-20s | **<20ms** ⚡ |
| **Search by name** | 5-10s | **<10ms** ⚡ |
| **Get faction summary** | 5s | **<5ms** ⚡ |

**Result:** ~1000x faster with SQLite!

---

## 📝 TODO

- [ ] Add experimental weapon detection
- [ ] Add secondary deflector detection
- [ ] Add ship comparison tool
- [ ] Add GraphQL API
- [ ] Add webhook notifications for changes
- [ ] Add data visualization dashboard
- [ ] Add CSV export
- [ ] Add ship images scraping

---

## 👥 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Add tests if applicable
4. Submit a pull request

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🔗 Links

- **STOWiki**: https://stowiki.net/
- **MediaWiki Cargo**: https://www.mediawiki.org/wiki/Extension:Cargo
- **Star Trek Online**: https://www.playstartrekonline.com/

---

**Built with ❤️ for the STO community**
