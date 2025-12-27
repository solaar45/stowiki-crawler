# 🚀 STO Wiki Crawler

A modern, high-performance Star Trek Online ship data scraper with a sleek TypeScript + React frontend.

## ✨ Features

### Backend
- **Async Scraping**: Concurrent ship data extraction using `httpx` and `asyncio`
- **Multi-Faction Support**: Federation, Klingon, Romulan, Dominion, Cross-Faction
- **Flexible Storage**: JSON file or database (SQLite, PostgreSQL, MySQL)
- **Type-Safe**: Full Pydantic validation for all ship data
- **Robust Error Handling**: Automatic retries with exponential backoff
- **RESTful API**: Clean Flask endpoints for all operations

### Frontend
- **Modern Stack**: TypeScript + React 18 + Vite
- **Performant UI**: TanStack Table with virtualization
- **Real-time Updates**: React Query for smart caching
- **Dark Mode**: Beautiful Tailwind CSS dark theme
- **Responsive Design**: Mobile-first approach
- **Type Safety**: Full TypeScript coverage

## 🏗️ Architecture

```
stowiki-crawler/
├── backend/
│   ├── api/              # Flask REST API
│   ├── models/           # Pydantic data models
│   ├── storage/          # Storage backends (JSON, DB)
│   ├── scraper.py        # Async web scraping
│   ├── transformers.py   # Data transformation
│   └── config.py         # Configuration
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── lib/          # API client & utilities
│   │   └── types/        # TypeScript types
│   └── vite.config.ts    # Vite configuration
└── docker-compose.yml    # Container orchestration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional)
cp .env.example .env
# Edit .env for database settings

# Run server
python -m api.app
```

Server runs at `http://localhost:5000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at `http://localhost:3000`

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📡 API Endpoints

### Information
- `GET /` - API information
- `GET /health` - Health check
- `GET /factions` - List all factions

### Scraping
- `GET /scrape/all` - Scrape all faction ships
- `GET /scrape/{faction}` - Scrape specific faction
  - Valid factions: `federation`, `klingon`, `romulan`, `dominion`, `cross-faction`

### Data Access
- `GET /ships` - Get all ships (optional `?faction=` filter)
- `GET /ships/download` - Download ships as JSON
- `GET /ships/count` - Get total ship count

### Example Usage

```bash
# Scrape all Federation ships
curl http://localhost:5000/scrape/federation

# Get all ships
curl http://localhost:5000/ships

# Filter by faction
curl http://localhost:5000/ships?faction=Klingon

# Download as JSON
curl http://localhost:5000/ships/download -o ships.json
```

## ⚙️ Configuration

Create a `.env` file in the backend directory:

```env
# Flask
FLASK_ENV=production
FLASK_DEBUG=false

# Scraper
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=0.5
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# Storage
STORAGE_TYPE=json  # or "database"
DATABASE_URL=sqlite:///ships.db
# DATABASE_URL=postgresql://user:pass@localhost/stowiki
# DATABASE_URL=mysql://user:pass@localhost/stowiki

# API
HOST=0.0.0.0
PORT=5000

# Logging
LOG_LEVEL=INFO
```

## 🗄️ Database Support

The application supports multiple database backends:

### SQLite (Default)
```env
STORAGE_TYPE=database
DATABASE_URL=sqlite:///ships.db
```

### PostgreSQL
```env
STORAGE_TYPE=database
DATABASE_URL=postgresql://user:password@localhost:5432/stowiki
```

### MySQL
```env
STORAGE_TYPE=database
DATABASE_URL=mysql://user:password@localhost:3306/stowiki
```

## 🎨 Frontend Features

### Ship Table
- **Sorting**: Click column headers to sort
- **Search**: Global search across all fields
- **Filtering**: Filter by faction
- **Pagination**: Navigate large datasets
- **Links**: External links to wiki pages

### Actions
- **Scrape**: Fetch latest data from wiki
- **Download**: Export ships as JSON
- **Dark Mode**: Toggle dark/light theme

## 🔧 Development

### Backend Tests
```bash
cd backend
pytest
pytest --cov=. --cov-report=html
```

### Frontend Build
```bash
cd frontend
npm run build
npm run preview
```

### Type Checking
```bash
cd frontend
npx tsc --noEmit
```

## 📦 Production Deployment

### Using Docker
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

**Backend:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 api.app:app
```

**Frontend:**
```bash
npm run build
# Serve dist/ with nginx or any static server
```

## 🆕 What's New in v2.0

### Backend Improvements
- ✅ **Async Scraping**: 5x faster data extraction
- ✅ **Multi-Faction Support**: All 5 factions supported
- ✅ **Database Storage**: Optional DB persistence
- ✅ **Type Safety**: Full Pydantic validation
- ✅ **Better Error Handling**: Retries + detailed logging
- ✅ **Clean Architecture**: Separated concerns

### Frontend Rewrite
- ✅ **TypeScript**: Complete type safety
- ✅ **Modern Stack**: Vite + React 18
- ✅ **TanStack Table**: Powerful data table
- ✅ **React Query**: Smart data fetching
- ✅ **Tailwind CSS**: Utility-first styling
- ✅ **Dark Mode**: Beautiful dark theme
- ✅ **Single Dependency**: Only necessary packages

### Removed
- ❌ Multiple UI libraries (Ant Design, Material-UI, Semantic UI)
- ❌ String-based icon replacement
- ❌ Class components
- ❌ Hardcoded backend URLs

## 📝 License

MIT License - feel free to use this project for any purpose.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Known Issues

- Wiki structure changes may break scraping
- Large datasets (>1000 ships) may cause memory issues

## 🔮 Roadmap

- [ ] Ship comparison feature
- [ ] Advanced filtering (by stats, weapons, etc.)
- [ ] Export to CSV/Excel
- [ ] Ship recommendations
- [ ] User accounts & favorites
- [ ] Real-time scraping status
- [ ] GraphQL API

## 💬 Support

For issues, questions, or suggestions, please open a GitHub issue.

---

**Built with ❤️ for Star Trek Online players**
