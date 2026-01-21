# Integ - AI Coding Agent Instructions

## Project Overview

**Integ** is a Linux-native desktop application for unified GOG & Steam game management on RPM-based distributions (Fedora, RHEL, CentOS). Strategic goal: drive RPM adoption through gaming ecosystem by providing a seamless, unified gaming platform.

**Core Architecture**: 
- **Frontend**: PyQt6 desktop client (thin client, runs on user machine in Flatpak)
- **Backend**: FastAPI REST API (cloud-hosted, stateless, horizontally scalable)
- **Runtime**: Proton/Wine containers for game execution
- **Package**: Flatpak for distribution, RPM spec file for native installation

---

## Critical Architecture Decisions

### 1. **Backend-First, Stateless Design**
- **Why**: Backend must be horizontally scalable for thousands of concurrent users
- **Pattern**: All authentication, game metadata, user data lives on backend (PostgreSQL + Redis)
- **Frontend**: Read-mostly thin client; local game launching only
- **Session**: OAuth2 → JWT token stored in Redis (30-minute TTL), NOT on disk
- **Key file**: [backend/main.py](backend/main.py)

### 2. **Local Save Games, Cloud Everything Else**
- **Save games**: Stored locally in `~/.local/share/integ/games/` (never synced to cloud)
- **Profiles, preferences, library**: All cloud-backed in PostgreSQL
- **Sync strategy**: Frontend caches game list locally, polls backend for library updates
- **Benefit**: No data loss risk, GDPR-friendly, works offline after initial sync

### 3. **Proton Version Management**
- **No bundled Proton**: Download specific versions on-demand from GitHub releases
- **Caching**: Store in `~/.cache/integ/proton/`, symlink latest used version
- **Fallback**: If Proton version missing, use user's system Steam Proton (if available)
- **Per-game**: Game metadata specifies required Proton version (e.g., "ge-8.26")
- **File**: [backend/services/proton_manager.py](backend/services/proton_manager.py) (TODO)

### 4. **Multi-Provider OAuth2 Plugin Architecture**
- **Providers**: Steam OpenID, GOG OAuth2, future (Epic, itch.io)
- **Interface**: Abstract `GameProvider` base class, concrete implementations per provider
- **Registration**: Registry pattern in `backend/auth/oauth2.py` for adding new providers
- **Flow**: Provider login → OAuth callback → JWT token → Backend validates → Response

### 5. **Async Everything**
- **Frontend**: PyQt signals for non-blocking API calls
- **Backend**: FastAPI async endpoints, Celery for long-running tasks (library syncs, downloads)
- **Database**: Connection pooling via SQLAlchemy, async sessions
- **Pattern**: `await` on all I/O (database, HTTP, file operations)

---

## Developer Workflows

### **Quick Dev Setup** (5 minutes)

**Option A: With Docker (Recommended)**
```bash
cd ~/Masaüstü/Projects/integ
cp .env.example .env

# Start services (PostgreSQL, Redis, Backend)
docker-compose up -d

# Install dependencies
pip install -e ".[dev]"

# Verify backend at http://localhost:8000/docs
```

**Option B: Without Docker (Local PostgreSQL/Redis)**
```bash
cd ~/Masaüstü/Projects/integ
cp .env.example .env

# Install PostgreSQL and Redis (Fedora)
sudo dnf install postgresql-server redis

# Start services
sudo systemctl start postgresql redis

# Create database
createdb integ_db
psql integ_db -c "CREATE USER integ_user WITH PASSWORD 'integ_password';"
psql integ_db -c "ALTER ROLE integ_user CREATEDB;"

# Install dependencies
pip install -e ".[dev]"

# Update .env with local database URL
# DATABASE_URL=postgresql://integ_user:integ_password@localhost:5432/integ_db
# REDIS_URL=redis://localhost:6379/0

# Verify backend at http://localhost:8000/docs
```

### **Run Backend Locally**

```bash
export PYTHONPATH=/home/longstone/Masaüstü/Projects/integ
export DATABASE_URL=postgresql://integ_user:integ_password@localhost:5432/integ_db
export REDIS_URL=redis://localhost:6379/0

uvicorn backend.main:app --reload --log-level debug
# API at http://localhost:8000
# Auto-reload on file changes
```

### **Run Frontend Locally**

```bash
cd frontend
python main.py --dev
# Connects to backend at http://localhost:8000 (from .env BACKEND_URL)
```

### **Database Migrations** (SQLAlchemy + Alembic)

```bash
# After modifying backend/models/
alembic revision --autogenerate -m "Add ProtonVersion table"
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### **Testing**

```bash
# All tests
pytest -v --cov=backend --cov=frontend

# Backend only
pytest backend/tests/ -v

# Frontend only
pytest frontend/tests/ -v

# Specific test
pytest backend/tests/test_auth.py::test_steam_oauth -v
```

### **Code Quality (Before commit)**

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 backend/ frontend/ --max-line-length=100 --ignore=E501,W503

# Type check
mypy backend/ --strict

# All-in-one
make lint  # If Makefile exists, otherwise run above sequentially
```

### **Git Workflow**

```bash
# Create feature branch
git checkout -b feature/steam-library

# Make changes, test
pytest

# Commit
git add .
git commit -m "feat: add Steam library sync endpoint"

# Push
git push origin feature/steam-library

# Create PR on GitHub
```

---

## Project Structure & File Purposes

```
integ/
├── frontend/                    # PyQt6 desktop application
│   ├── main.py                 # Entry point (initialize QApplication)
│   ├── api_client.py           # HTTP client for backend API
│   └── ui/                     # UI components (TODO)
│       ├── main_window.py      # Main window (tabs: Steam, GOG, Library)
│       ├── steam_tab.py        # Steam games view
│       ├── gog_tab.py          # GOG games view
│       └── library_tab.py      # User's installed games
│
├── backend/                     # FastAPI REST API
│   ├── main.py                 # FastAPI app initialization + CORS
│   ├── auth/                   # OAuth2, JWT, security
│   │   ├── oauth2.py           # OAuth2 provider interface + implementations
│   │   ├── jwt.py              # JWT token generation/validation
│   │   └── session.py          # Redis session management
│   ├── api/                    # HTTP endpoints
│   │   ├── games.py            # GET /games/steam, /games/gog
│   │   ├── auth.py             # POST /auth/{provider}/login
│   │   ├── users.py            # GET /users/me, PATCH /users/preferences
│   │   └── proton.py           # GET /proton/versions, POST /proton/install
│   ├── services/               # Business logic
│   │   ├── steam_service.py    # Steam Steamworks API wrapper
│   │   ├── gog_service.py      # GOG Galaxy API wrapper
│   │   ├── proton_manager.py   # Download, cache, manage Proton versions
│   │   └── game_launcher.py    # Execute game with Proton (TODO)
│   └── models/                 # SQLAlchemy ORM
│       ├── user.py             # User model (id, email, profiles, preferences)
│       ├── game.py             # Game model (id, title, provider, metadata)
│       ├── library.py          # Library model (user_id, game_id, timestamp)
│       └── proton.py           # ProtonVersion model (version, cached_path)
│
├── tests/                       # Test suite
│   ├── backend/
│   │   ├── test_auth.py        # OAuth2 flow tests
│   │   ├── test_games.py       # Game library endpoint tests
│   │   └── test_services.py    # Steam/GOG API wrapper tests
│   └── frontend/
│       └── test_ui.py          # PyQt component tests (TODO)
│
├── flatpak/                     # Flatpak manifest
│   └── org.example.IntegProgram.yaml  # Flatpak build configuration
│
├── rpm/                         # RPM packaging
│   └── integ.spec              # RPM spec file for Fedora/RHEL
│
├── docker-compose.yml           # Dev environment (PostgreSQL, Redis, Backend)
├── Dockerfile.backend           # Backend container image
├── pyproject.toml               # Project metadata + dependencies
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore patterns (Python, IDE, etc.)
├── .github/copilot-instructions.md  # THIS FILE - AI agent instructions
├── LICENSE                      # GPL-3.0 license
└── README.md                    # Project documentation
```

---

## Coding Patterns & Conventions

### **Naming**

- **Models** (backend/models/): `CamelCase` (User, Game, ProtonVersion, SteamProfile)
- **Services** (backend/services/): `snake_case` functions, `PascalCase` classes with `Service` or `Manager` suffix (SteamService, ProtonManager)
- **API endpoints** (backend/api/): `/resource-type/{id}/action`, RESTful conventions
  - `GET /games` - List all games
  - `GET /games/{game_id}` - Get specific game
  - `POST /games/{game_id}/download` - Initiate download
  - `GET /auth/{provider}/login` - OAuth login flow
- **Frontend components** (frontend/ui/): `CamelCase` + descriptive (MainWindow, SteamTab, GameCardWidget)
- **Database tables**: `snake_case` (users, games, proton_versions)

### **Async Pattern**

All I/O operations must be async:

```python
# ✅ CORRECT
async def get_steam_library(user_id: int) -> List[Game]:
    async with db.session() as session:
        user = await session.get(User, user_id)
        return await session.execute(select(Game).where(Game.user_id == user_id))

# ❌ WRONG
def get_steam_library(user_id: int):  # No async!
    user = db.query(User).get(user_id)  # Blocking!
```

### **Error Handling**

Create custom exceptions in `backend/exceptions.py`:

```python
# backend/exceptions.py
class IntegError(Exception):
    """Base exception for all Integ errors."""

class GameNotFoundError(IntegError):
    """Game not found in library."""

class AuthenticationError(IntegError):
    """OAuth2 authentication failed."""

# Usage
@app.get("/games/{game_id}")
async def get_game(game_id: int):
    game = await db.get_game(game_id)
    if not game:
        raise GameNotFoundError(f"Game {game_id} not found")
    return game
```

### **API Response Format**

Consistent response structure:

```python
# Success
{
  "status": "ok",
  "data": {...},
  "timestamp": "2026-01-21T10:00:00Z"
}

# Error
{
  "status": "error",
  "error": "AuthenticationError",
  "message": "OAuth token expired",
  "timestamp": "2026-01-21T10:00:00Z"
}
```

### **Pydantic Models** (Data validation)

```python
from pydantic import BaseModel

class GameResponse(BaseModel):
    id: int
    title: str
    provider: str  # "steam" or "gog"
    icon_url: Optional[str] = None
    
    class Config:
        from_attributes = True  # SQLAlchemy model compatibility
```

---

## Integration Points & External APIs

### **Steam**

- **OpenID Login**: `https://steamcommunity.com/openid/login`
- **Steamworks API**: Game library, achievements, user profile
- **API Key**: Required, set in `.env STEAM_API_KEY`
- **Wrapper**: [backend/services/steam_service.py](backend/services/steam_service.py)

### **GOG**

- **OAuth2 Endpoint**: `https://auth.gog.com/authorize`
- **Galaxy API**: Game metadata, library, downloads
- **Credentials**: `GOG_CLIENT_ID`, `GOG_CLIENT_SECRET` in `.env`
- **Wrapper**: [backend/services/gog_service.py](backend/services/gog_service.py)

### **Proton** (Game Runtime)

- **GitHub Releases**: `https://github.com/GloriousEggroll/proton-ge-custom/releases`
- **Download**: Binary tarball (~1-2GB per version)
- **Cache**: `~/.cache/integ/proton/{version}/`
- **Manager**: [backend/services/proton_manager.py](backend/services/proton_manager.py)

### **System Integration**

- **Flatpak Sandboxing**: Permissions in `flatpak/org.example.IntegProgram.yaml`
- **XDG Directories**: `~/.local/share/integ/`, `~/.config/integ/`, `~/.cache/integ/`
- **systemd** (future): Background service for auto-updates, game notifications

---

## Performance & Scalability Considerations

### **Database Optimization**

- Index on `user_id` for fast library queries
- Index on `provider` for grouping Steam vs GOG games
- Connection pooling: 20-50 connections (adjust based on load)

### **Caching Strategy**

- **Redis TTLs**:
  - OAuth tokens: 30 minutes
  - Game metadata: 1 hour
  - User profile: 5 minutes
- **Frontend**: Cache library locally, poll `/games/sync-status` for updates

### **Async Tasks** (Celery)

For long-running operations (don't block API):
- Download Proton version
- Sync library from Steam/GOG
- Update game metadata

```python
@celery_app.task
def sync_steam_library(user_id: int):
    """Background task - sync user's Steam library."""
    # Fetch from Steam API, update PostgreSQL
    pass
```

### **Frontend Performance**

- Lazy-load game icons (load on scroll)
- Paginate game list (50 items/page)
- Local SQLite cache for offline browsing (TODO)

---

## When Adding a New Feature

1. **Define API contract first** (endpoint, request/response schema)
2. **Implement backend**:
   - Add Pydantic models (request/response)
   - Add database model if needed
   - Add service logic
   - Add API endpoint
   - Add tests
3. **Implement frontend**:
   - Add UI component
   - Connect to API via `api_client.py`
   - Add tests
4. **Update this file** if pattern changes

### **Example: Add Epic Games Integration**

```
1. backend/services/epic_service.py          # New provider
2. backend/auth/oauth2.py                    # Register in OAuth registry
3. backend/api/games.py                      # Add GET /games/epic
4. frontend/ui/epic_tab.py                   # New UI tab
5. Update tests
6. Update this instructions file
```

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| `docker-compose` won't start | `docker-compose down -v && docker-compose up -d` |
| Backend port 8000 already in use | `lsof -i :8000 && kill <pid>` or change port in docker-compose.yml |
| PostgreSQL connection fails | Check `DATABASE_URL` in `.env`, ensure postgres container is healthy |
| Frontend can't connect to backend | Verify `BACKEND_URL` in `.env`, check backend is running on `:8000` |
| Tests fail with "database locked" | SQLite test database issue, delete `.db` files and rerun |
| Import errors in backend | Ensure `PYTHONPATH` includes project root: `export PYTHONPATH=$PWD` |

---

## Useful Commands Reference

```bash
# Environment setup
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Development
docker-compose up -d
uvicorn backend.main:app --reload

# Testing
pytest -v
pytest --cov=backend

# Deployment
docker build -f Dockerfile.backend -t integ-backend .
flatpak-builder --repo=repo --force-clean build-dir flatpak/org.example.IntegProgram.yaml
```

---

**Updated**: 2026-01-21  
**Version**: 0.1.0 (MVP Phase)  
**Maintainer**: rheldev6
