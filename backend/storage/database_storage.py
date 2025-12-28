"""Database storage backend with metadata tracking."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from models.ship import Ship
from logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


class ShipModel(Base):
    """SQLAlchemy model for ships."""
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    faction = Column(String(50), index=True)
    tier = Column(String(50))
    type = Column(String(100))
    hull = Column(String(50))
    shields = Column(String(50))
    crew = Column(String(50))
    weapons_fore = Column(String(50))
    weapons_aft = Column(String(50))
    device_slots = Column(String(50))
    consoles_tactical = Column(String(50))
    consoles_engineering = Column(String(50))
    consoles_science = Column(String(50))
    turn_rate = Column(String(50))
    impulse_modifier = Column(String(50))
    inertia = Column(String(50))
    warp_core = Column(String(50))
    bonus_power = Column(String(200))
    bridge_officers = Column(Text)
    link = Column(String(500))
    raw_data = Column(Text)  # Store additional data as JSON


class MetadataModel(Base):
    """SQLAlchemy model for metadata."""
    __tablename__ = "metadata"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class DatabaseStorage:
    """Database storage for ships with metadata tracking."""

    def __init__(self, database_url: str):
        """Initialize database storage.

        Args:
            database_url: Database connection URL
        """
        # Convert sync URL to async if needed
        if database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+aiomysql://")

        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        logger.info(f"Database storage initialized: {database_url.split('@')[-1]}")

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")

    async def save_ships(self, ships: List[Ship]) -> None:
        """Save ships to database and update metadata.

        Args:
            ships: List of Ship objects
        """
        try:
            async with self.async_session() as session:
                # Clear existing ships
                await session.execute(ShipModel.__table__.delete())

                # Insert new ships
                for ship in ships:
                    ship_model = ShipModel(
                        name=ship.ship,
                        faction=ship.faction,
                        tier=ship.tier,
                        type=ship.type,
                        hull=ship.hull,
                        shields=ship.shields,
                        crew=ship.crew,
                        weapons_fore=ship.weapons_fore,
                        weapons_aft=ship.weapons_aft,
                        device_slots=ship.device_slots,
                        consoles_tactical=ship.consoles_tactical,
                        consoles_engineering=ship.consoles_engineering,
                        consoles_science=ship.consoles_science,
                        turn_rate=ship.turn_rate,
                        impulse_modifier=ship.impulse_modifier,
                        inertia=ship.inertia,
                        warp_core=ship.warp_core,
                        bonus_power=ship.bonus_power,
                        bridge_officers=ship.bridge_officers,
                        link=ship.link,
                        raw_data=ship.json()
                    )
                    session.add(ship_model)
                
                # Update metadata
                import json
                metadata_value = json.dumps({
                    "last_scraped": datetime.utcnow().isoformat(),
                    "ship_count": len(ships),
                    "factions_scraped": list(set(ship.faction for ship in ships if ship.faction))
                })
                
                # Upsert metadata
                result = await session.execute(
                    select(MetadataModel).where(MetadataModel.key == "scrape_info")
                )
                metadata_obj = result.scalar_one_or_none()
                
                if metadata_obj:
                    metadata_obj.value = metadata_value
                    metadata_obj.updated_at = datetime.utcnow()
                else:
                    metadata_obj = MetadataModel(
                        key="scrape_info",
                        value=metadata_value,
                        updated_at=datetime.utcnow()
                    )
                    session.add(metadata_obj)

                await session.commit()
                logger.info(f"Saved {len(ships)} ships to database with metadata")

        except Exception as e:
            logger.error(f"Failed to save ships: {e}")
            raise

    async def get_ships(self, faction: Optional[str] = None) -> List[Ship]:
        """Load ships from database.

        Args:
            faction: Optional faction filter

        Returns:
            List of Ship objects
        """
        try:
            async with self.async_session() as session:
                stmt = select(ShipModel)
                if faction:
                    stmt = stmt.where(func.lower(ShipModel.faction) == faction.lower())

                result = await session.execute(stmt)
                ship_models = result.scalars().all()

                ships = [
                    Ship(
                        ship=model.name,
                        faction=model.faction,
                        tier=model.tier,
                        type=model.type,
                        hull=model.hull,
                        shields=model.shields,
                        crew=model.crew,
                        weapons_fore=model.weapons_fore,
                        weapons_aft=model.weapons_aft,
                        device_slots=model.device_slots,
                        consoles_tactical=model.consoles_tactical,
                        consoles_engineering=model.consoles_engineering,
                        consoles_science=model.consoles_science,
                        turn_rate=model.turn_rate,
                        impulse_modifier=model.impulse_modifier,
                        inertia=model.inertia,
                        warp_core=model.warp_core,
                        bonus_power=model.bonus_power,
                        bridge_officers=model.bridge_officers,
                        link=model.link,
                    )
                    for model in ship_models
                ]

                logger.debug(f"Loaded {len(ships)} ships from database")
                return ships

        except Exception as e:
            logger.error(f"Failed to load ships: {e}")
            return []

    async def get_ship_count(self) -> int:
        """Get total number of ships in database.

        Returns:
            Number of ships
        """
        try:
            async with self.async_session() as session:
                result = await session.execute(select(func.count(ShipModel.id)))
                count = result.scalar()
                return count or 0
        except Exception as e:
            logger.error(f"Failed to get ship count: {e}")
            return 0
    
    async def get_metadata(self) -> Optional[dict]:
        """Get scraping metadata.
        
        Returns:
            Metadata dict or None if not found
        """
        try:
            import json
            async with self.async_session() as session:
                result = await session.execute(
                    select(MetadataModel).where(MetadataModel.key == "scrape_info")
                )
                metadata_obj = result.scalar_one_or_none()
                
                if metadata_obj:
                    return json.loads(metadata_obj.value)
                return None
                
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return None
    
    async def needs_refresh(self, max_age_hours: int = 24) -> bool:
        """Check if data needs refresh based on age.
        
        Args:
            max_age_hours: Maximum age in hours before refresh needed
            
        Returns:
            True if refresh needed, False otherwise
        """
        metadata = await self.get_metadata()
        
        if not metadata:
            logger.info("No metadata found, refresh needed")
            return True
        
        try:
            last_scraped = datetime.fromisoformat(metadata["last_scraped"])
            age = datetime.utcnow() - last_scraped
            age_hours = age.total_seconds() / 3600
            
            needs_refresh = age_hours > max_age_hours
            
            if needs_refresh:
                logger.info(f"Data is {age_hours:.1f}h old (max {max_age_hours}h), refresh needed")
            else:
                logger.debug(f"Data is {age_hours:.1f}h old, still fresh")
            
            return needs_refresh
            
        except Exception as e:
            logger.error(f"Failed to check refresh status: {e}")
            return True  # Refresh on error